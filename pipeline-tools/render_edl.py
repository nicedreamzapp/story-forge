#!/usr/bin/env python3
"""render_edl.py — the pluggable promo renderer: edl.json + callouts.json + vo/words.json -> mp4.

WHY THIS EXISTS (promo format, 2026-10-22): the first Sitka promo was assembled by a script
that knew nothing about the words. Every cut was a 0.5 s xfade, narration was laid on top,
and it showed. The cut is now decided ONCE, by edit_to_words.py, in edl.json, and gated by
cue_check.py. A renderer's only job is to play that EDL faithfully, frame-exact:
  * hard cuts wherever the EDL says "cut"; a dissolve ONLY where it says "xfade" (centered
    on the word: the incoming shot is 50% at rec_in, using the head/tail handles)
  * each shot conformed to the EDL frame (1920x1080@30 for the promo pack): scale to fill and
    center-crop (or --fit pad), never a speed change (frozen rule 4)
  * stills only through bin/ken_burns.py (frozen rule 12: no shaking/zoompan stills)
  * vo wavs laid at their rec_in, STATIC gain mix (gates-and-qc: never loudnorm dynamic)
  * "overlays": alpha clips (Manim ProRes 4444 .mov / VP9 WebM) over the shot track, under
    callouts and titles; ffmpeg decodes the alpha (libvpx-vp9 for WebM), Remotion uses
    <OffthreadVideo transparent>
  * callouts (arrow line, dot at the tip, label box; the tip tracks [t,x,y] keyframes) and
    title cards. On the ffmpeg path they are PIL-rendered RGBA overlays, because this
    ffmpeg build has no drawtext.

Two renderers, same interface (SCHEMAS.md "Renderer plug"):
  --renderer ffmpeg    the preview/fallback path, pure ffmpeg + PIL, no node
  --renderer remotion  promo-remotion/ (Remotion v4): springs, tracked SVG arrows, kinetic
                       type. Media is hard-linked (or copied) into
                       promo-remotion/public/media/<film>/ and the three JSONs go in as props.

Usage (run with a python that has PIL, e.g. ~/chatterbox-env/bin/python):
  render_edl.py --renderer ffmpeg|remotion projects/<film> [--out final/<film>.mp4]
                [--fit crop|pad] [--vo-gain 0] [--music score.wav --music-gain -18]
                [--lut grade.cube] [--lower-third]
Exit 0 = rendered and probed (duration matches the EDL within 1 frame + 50 ms);
1 = rendered but the output is wrong (duration/streams); 2 = could not render. NEVER treat 2
as a pass, and a 0 here is NOT film QC: cue_check and the gates in _shared/gates-and-qc.md
still run before anyone calls the film checked.
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SF = Path(__file__).resolve().parent.parent
REMOTION = SF / "promo-remotion"
KEN_BURNS = SF / "bin" / "ken_burns.py"
FONT = "/System/Library/Fonts/Avenir Next.ttc"  # index 2 = Demi Bold, 0 = Bold
TEAL = (45, 212, 191)
AMBER = (251, 191, 36)


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        tail = "\n".join((r.stderr or r.stdout).strip().splitlines()[-12:])
        raise RuntimeError(f"command failed ({cmd[0]} ...):\n{tail}")
    return r


def probe(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
             "-of", "json", str(path)])
    return json.loads(r.stdout)


# ---------------------------------------------------------------- overlays (PIL)
def ease_out_back(x, s=1.4):
    x = min(max(x, 0.0), 1.0) - 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def tip_at(tip, t):
    """tip is [x, y] or a list of [t, x, y] keyframes (final-timeline seconds)."""
    if tip and isinstance(tip[0], (list, tuple)):
        ks = sorted(tip)
        if t <= ks[0][0]:
            return ks[0][1], ks[0][2]
        for a, b in zip(ks, ks[1:]):
            if a[0] <= t <= b[0]:
                u = (t - a[0]) / max(1e-6, b[0] - a[0])
                return a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u
        return ks[-1][1], ks[-1][2]
    return tip[0], tip[1]


def callout_frames(co, W, H, fps, outdir):
    """One RGBA PNG per frame: label pill, arrow line drawn in from the label to the tip,
    dot at the tip. Supersampled 2x for clean edges."""
    from PIL import Image, ImageDraw, ImageFont
    S = 2
    t0, t1 = float(co["rec_in"]), float(co["rec_out"])
    n = max(1, round((t1 - t0) * fps))
    font = ImageFont.truetype(FONT, 44 * S, index=2)
    label = co.get("label", co.get("id", ""))
    tx, ty = co.get("text_at", [0.7, 0.3])
    for k in range(n):
        t = t0 + k / fps
        age = t - t0
        fade = smooth((t1 - t) / 0.25) if t1 - t < 0.25 else 1.0
        im = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        # label pill
        bx, by = tx * W * S, ty * H * S
        l, tp, r, b = d.textbbox((0, 0), label, font=font)
        pw, ph = (r - l) + 56 * S, (b - tp) + 36 * S
        pop = ease_out_back(age / 0.35)
        a_lab = int(255 * smooth(age / 0.2) * fade)
        sc = 0.85 + 0.15 * pop
        x0, y0 = bx - pw * sc / 2, by - ph * sc / 2
        d.rounded_rectangle([x0, y0, x0 + pw * sc, y0 + ph * sc], radius=ph * sc / 2,
                            fill=(12, 18, 28, int(a_lab * 0.82)), outline=TEAL + (a_lab,), width=3 * S)
        if sc > 0.97:
            d.text((bx - (r - l) / 2 - l, by - (b - tp) / 2 - tp), label, font=font, fill=(255, 255, 255, a_lab))
        # arrow: from the pill edge nearest the tip, growing toward the tip
        px, py = tip_at(co["tip"], t)
        ex, ey = px * W * S, py * H * S
        sx = min(max(ex, x0 + 20 * S), x0 + pw * sc - 20 * S)
        sy = y0 + ph * sc if ey > by else y0
        grow = smooth((age - 0.12) / 0.4)
        if grow > 0:
            cx, cy = sx + (ex - sx) * grow, sy + (ey - sy) * grow
            d.line([(sx, sy), (cx, cy)], fill=(255, 255, 255, int(255 * fade)), width=5 * S)
            if grow >= 1:
                rr = (9 + 5 * (1 - smooth((age - 0.52) / 0.2))) * S
                d.ellipse([ex - rr - 4 * S, ey - rr - 4 * S, ex + rr + 4 * S, ey + rr + 4 * S],
                          fill=(255, 255, 255, int(110 * fade)))
                d.ellipse([ex - rr, ey - rr, ex + rr, ey + rr], fill=TEAL + (int(255 * fade),))
        im.resize((W, H), Image.LANCZOS).save(outdir / f"{k:05d}.png")
    return n


def title_frames(tt, W, H, fps, outdir):
    """Kinetic title card: spring scale-in (1.25 -> 1.0) with opacity, fade out at the end."""
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    t0, t1 = float(tt["rec_in"]), float(tt["rec_out"])
    n = max(1, round((t1 - t0) * fps))
    text = tt["text"]
    for k in range(n):
        age = k / fps
        left = (t1 - t0) - age
        alpha = smooth(age / 0.18) * (smooth(left / 0.3) if left < 0.3 else 1.0)
        sc = 1.0 + 0.25 * (1 - ease_out_back(age / 0.45, 1.2))
        size = max(8, int(190 * sc))
        font = ImageFont.truetype(FONT, size, index=8)
        spaced = " ".join(text) if len(text) <= 8 else text
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        l, tp, r, b = d.textbbox((0, 0), spaced, font=font)
        x, y = (W - (r - l)) / 2 - l, (H - (b - tp)) / 2 - tp
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((x, y + 6), spaced, font=font, fill=(0, 0, 0, int(170 * alpha)))
        im = Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), im)
        d = ImageDraw.Draw(im)
        d.text((x, y), spaced, font=font, fill=(255, 255, 255, int(255 * alpha)))
        if age < 0.2:   # the slam: a white flash that decays in ~6 frames (Sitka recipe)
            fl = Image.new("RGBA", (W, H), (255, 255, 255, int(200 * (1 - age / 0.2) ** 2)))
            im = Image.alpha_composite(im, fl)
            d = ImageDraw.Draw(im)
        bar_w = (r - l) * smooth((age - 0.15) / 0.4)
        d.rectangle([W / 2 - bar_w / 2, y + (b - tp) + tp + 28, W / 2 + bar_w / 2, y + (b - tp) + tp + 36],
                    fill=AMBER + (int(255 * alpha),))
        im.save(outdir / f"{k:05d}.png")
    return n


def endcard_frames(ec, W, H, fps, outdir, brand_font_index=8):
    """The end card (Sitka recipe): a flash + the brand SLAMS in on the first frame (the music's
    downbeat and the sting land here, AFTER the last word), the tagline rises in, the URL follows.
    Opaque frames over a dark vignette; the music sting rings out under it."""
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    n = max(1, round((float(ec["rec_out"]) - float(ec["rec_in"])) * fps))
    title, tag, url = ec.get("title", ""), ec.get("tagline", ""), ec.get("url", "")
    bg = Image.new("RGB", (W, H), (6, 8, 12))
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse([-W * 0.2, -H * 0.5, W * 1.2, H * 1.5], fill=60)
    bg = Image.composite(Image.new("RGB", (W, H), (22, 30, 40)), bg, vig.filter(ImageFilter.GaussianBlur(220)))
    f_tag = ImageFont.truetype(FONT, 58, index=2)
    f_url = ImageFont.truetype(FONT, 38, index=2)
    for k in range(n):
        age = k / fps
        im = bg.copy().convert("RGBA")
        d = ImageDraw.Draw(im)
        sc = 1.0 + 0.35 * (1 - ease_out_back(age / 0.32, 1.1))
        font = ImageFont.truetype(FONT, max(8, int(230 * sc)), index=brand_font_index)
        spaced = " ".join(title) if len(title) <= 8 else title
        l, tp, r, b = d.textbbox((0, 0), spaced, font=font)
        x, y = (W - (r - l)) / 2 - l, H * 0.40 - (b - tp) / 2 - tp
        d.text((x, y), spaced, font=font, fill=(255, 255, 255, 255))
        bar = (r - l) * smooth((age - 0.1) / 0.45)
        d.rectangle([W / 2 - bar / 2, y + b + 26, W / 2 + bar / 2, y + b + 34], fill=AMBER + (255,))
        for txt, f_, yy, t0 in ((tag, f_tag, H * 0.64, 0.45), (url, f_url, H * 0.76, 0.85)):
            if not txt:
                continue
            a_ = smooth((age - t0) / 0.4)
            if a_ <= 0:
                continue
            l2, t2, r2, b2 = d.textbbox((0, 0), txt, font=f_)
            d.text(((W - (r2 - l2)) / 2 - l2, yy + 18 * (1 - a_) - t2), txt, font=f_,
                   fill=(255, 255, 255, int(235 * a_)) if f_ is f_tag else TEAL + (int(235 * a_),))
        if age < 0.25:
            im = Image.alpha_composite(im, Image.new("RGBA", (W, H), (255, 255, 255, int(235 * (1 - age / 0.25) ** 2))))
        im.save(outdir / f"{k:05d}.png")
    return n


def bug_png(text, W, H, out):
    """The corner logo bug ("SITKA", top right, 70% white), on screen until the end card."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f_ = ImageFont.truetype(FONT, int(H * 0.034), index=8)
    spaced = " ".join(text) if len(text) <= 8 else text
    l, t, r, b = d.textbbox((0, 0), spaced, font=f_)
    d.text((W - (r - l) - W * 0.035 - l, H * 0.045 - t), spaced, font=f_, fill=(255, 255, 255, 178))
    im.save(out)


def png_seq_to_mov(src_dir, fps, out):
    run(["ffmpeg", "-y", "-v", "error", "-framerate", str(fps), "-i", str(src_dir / "%05d.png"),
         "-c:v", "qtrle", "-pix_fmt", "argb", str(out)])


# ---------------------------------------------------------------- ffmpeg renderer
def render_ffmpeg(film, edl, callouts, out, a):
    W, H, fps = int(edl["w"]), int(edl["h"]), int(edl["fps"])
    work = Path(tempfile.mkdtemp(prefix="render_edl_"))
    segs, seg_frames = [], []
    shots = edl["shots"]
    ec = edl.get("endcard")
    print(f"[render_edl] ffmpeg: {len(shots)} shots -> {W}x{H}@{fps}, work {work}")
    for i, s in enumerate(shots):
        f_in, f_out = round(s["rec_in"] * fps), round(s["rec_out"] * fps)
        hf, tf = round(s.get("head", 0) * fps), round(s.get("tail", 0) * fps)
        nfr = (f_out - f_in) + hf + tf
        seg = work / f"seg{i:03d}.mp4"
        src = film / s["file"]
        if s.get("kind") == "image":
            run([sys.executable, str(KEN_BURNS), str(src), str(seg), "--dur", f"{nfr / fps:.4f}",
                 "--mode", s.get("move", "pushslow"), "--fps", str(fps), "--size", f"{W}x{H}"])
        else:
            start = max(0.0, s["src_in"] - s.get("head", 0))
            if a.fit == "pad":
                vf = f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2"
            else:
                vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
            # tpad only guards a 1-2 frame rounding shortfall at the very end of a clip;
            # edit_to_words already refused any shot that runs past its source.
            vf += f",fps={fps},setsar=1,format=yuv420p,tpad=stop_mode=clone:stop_duration=0.1"
            run(["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.4f}", "-i", str(src), "-frames:v", str(nfr),
                 "-vf", vf, "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "12", str(seg)])
        segs.append(seg)
        seg_frames.append(nfr)

    # alpha clips (Manim etc.) go first so callouts/titles sit on top of them
    alpha = []
    for o in edl.get("overlays", []):
        f = film / o["file"]
        ow = int(round(float(o.get("w", 1.0)) * W / 2)) * 2
        dec = ["-c:v", "libvpx-vp9"] if f.suffix.lower() == ".webm" else []  # VP9 alpha needs libvpx to decode
        alpha.append((dec, f, o, ow))

    # overlays
    ov = []
    for co in callouts:
        d = work / f"co_{co['id']}"
        d.mkdir()
        callout_frames(co, W, H, fps, d)
        mov = work / f"co_{co['id']}.mov"
        png_seq_to_mov(d, fps, mov)
        ov.append((mov, float(co["rec_in"]), float(co["rec_out"])))
    bug = getattr(a, "bug", None)
    if bug:
        bp = work / "bug.png"
        bug_png(bug, W, H, bp)
        bmov = work / "bug.mov"
        run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(fps), "-t",
             f"{(float(ec['rec_in']) if ec else float(edl['dur'])):.4f}", "-i", str(bp), "-c:v", "qtrle",
             "-pix_fmt", "argb", str(bmov)])
        ov.append((bmov, 0.0, float(ec["rec_in"]) if ec else float(edl["dur"])))
    for j, tt in enumerate(edl.get("titles", [])):
        d = work / f"title_{j}"
        d.mkdir()
        title_frames(tt, W, H, fps, d)
        mov = work / f"title_{j}.mov"
        png_seq_to_mov(d, fps, mov)
        ov.append((mov, float(tt["rec_in"]), float(tt["rec_out"])))

    if ec:
        d = work / "endcard"
        d.mkdir()
        endcard_frames(ec, W, H, fps, d)
        mov = work / "endcard.mov"
        png_seq_to_mov(d, fps, mov)
        ov.append((mov, float(ec["rec_in"]), float(ec["rec_out"])))
    inputs, fc = [], []
    for s in segs:
        inputs += ["-i", str(s)]
    for i in range(len(segs)):  # one timebase for concat and xfade
        fc.append(f"[{i}:v]settb=AVTB,setpts=PTS-STARTPTS[s{i}]")
    cur, cur_frames = "[s0]", seg_frames[0]
    for i in range(1, len(segs)):
        s = shots[i]
        lab = f"[v{i}]"
        if s["transition"] == "xfade" and s.get("xfade", 0) > 0:
            dfr = round(s["head"] * fps) + round(shots[i - 1].get("tail", 0) * fps)
            off = (cur_frames - dfr) / fps
            fc.append(f"{cur}[{i}:v]xfade=transition=fade:duration={dfr / fps:.4f}:offset={off:.4f}{lab}".replace(f"[{i}:v]", f"[s{i}]"))
            cur_frames = cur_frames + seg_frames[i] - dfr
        else:
            fc.append(f"{cur}[s{i}]concat=n=2:v=1:a=0{lab}")
            cur_frames += seg_frames[i]
        cur = lab
    if ec:   # the shots stop at the slam; black under the card for its duration
        fc.append(f"{cur}tpad=stop_mode=add:stop_duration={float(ec['rec_out']) - float(ec['rec_in']) + 0.2:.4f}:color=black[padded]")
        cur = "[padded]"
    n_in = len(segs)
    for k, (dec, f, o, ow) in enumerate(alpha):
        inputs += dec + ["-ss", f"{float(o.get('src_in', 0)):.4f}", "-i", str(f)]
        t0, t1 = float(o["rec_in"]), float(o["rec_out"])
        op = float(o.get("opacity", 1.0))
        cxp, cyp = float(o.get("x", 0.5)) * W, float(o.get("y", 0.5)) * H
        fc.append(f"[{n_in + k}:v]format=rgba,scale={ow}:-2,fps={fps},colorchannelmixer=aa={op:.3f},"
                  f"setpts=PTS-STARTPTS+{t0:.4f}/TB[al{k}]")
        fc.append(f"{cur}[al{k}]overlay=x={cxp:.1f}-w/2:y={cyp:.1f}-h/2:eof_action=pass:format=auto:"
                  f"enable='between(t,{t0:.4f},{t1:.4f})'[ac{k}]")
        cur = f"[ac{k}]"
    n_in += len(alpha)
    for k, (mov, t0, t1) in enumerate(ov):
        inputs += ["-i", str(mov)]
        idx = n_in + k
        # start half a frame early: an overlay timed exactly on a frame boundary could miss that
        # frame to PTS rounding (sitka_demo: one BLACK frame at the end-card slam)
        t0 = max(0.0, t0 - 0.5 / fps)
        fc.append(f"[{idx}:v]setpts=PTS-STARTPTS+{t0:.4f}/TB[o{k}]")
        fc.append(f"{cur}[o{k}]overlay=eof_action=pass:enable='between(t,{t0:.4f},{t1:.4f})'[c{k}]")
        cur = f"[c{k}]"
    if a.lut:
        fc.append(f"{cur}lut3d=file='{a.lut}'[graded]")
        cur = "[graded]"
    fc.append(f"{cur}format=yuv420p[vout]")

    # audio: every wav at its rec_in, static gain, no dynamics
    n_v = n_in + len(ov)
    al = []
    auds = [] if getattr(a, "audio", None) else list(edl.get("audio", []))
    if a.music and not getattr(a, "audio", None):
        auds.append({"file": a.music, "rec_in": 0.0, "kind": "music"})
    for k, au in enumerate(auds):
        p = Path(au["file"])
        inputs += ["-i", str(p if p.is_absolute() else film / p)]
        g = a.music_gain if au.get("kind") == "music" else a.vo_gain
        ms = int(round(float(au["rec_in"]) * 1000))
        fc.append(f"[{n_v + k}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}:all=1,volume={g}dB[a{k}]")
        al.append(f"[a{k}]")
    dur = float(edl["dur"])
    if al:
        fc.append(f"{''.join(al)}amix=inputs={len(al)}:normalize=0:dropout_transition=0,apad,atrim=0:{dur:.4f}[aout]")
    fcfile = work / "filter.txt"
    fcfile.write_text(";\n".join(fc))
    cmd = ["ffmpeg", "-y", "-v", "error"] + inputs + ["-filter_complex_script", str(fcfile),
                                                      "-map", "[vout]"]
    if getattr(a, "audio", None):
        cmd[cmd.index("-filter_complex_script"):cmd.index("-filter_complex_script")] = ["-i", str(Path(a.audio).resolve())]
        cmd += ["-map", f"{n_v}:a", "-c:a", "aac", "-b:a", "320k", "-ar", "48000"]
    elif al:
        cmd += ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-r", str(fps), "-frames:v", str(round(dur * fps)), "-c:v", "libx264", "-preset", "medium",
            "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)]
    run(cmd)
    if not a.keep_work:
        shutil.rmtree(work, ignore_errors=True)
    else:
        print(f"[render_edl] work kept: {work}")


# ---------------------------------------------------------------- remotion renderer
def place(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if dst.stat().st_size == src.stat().st_size:
            return
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def render_remotion(film, edl, callouts, words, out, a):
    if not (REMOTION / "node_modules" / "remotion").exists():
        raise RuntimeError(f"{REMOTION}/node_modules missing: run `npm install` in {REMOTION}")
    base = f"media/{film.name}/"
    pub = REMOTION / "public" / "media" / film.name
    files = ({s["file"] for s in edl["shots"]} | {au["file"] for au in edl.get("audio", [])}
             | {o["file"] for o in edl.get("overlays", [])})
    for f in sorted(files):
        place((film / f).resolve(), pub / f)
    music = None
    if a.music:
        mp = Path(a.music).resolve()
        place(mp, pub / "music" / mp.name)
        music = {"file": f"music/{mp.name}", "gain_db": a.music_gain}
    audio_file = None
    if getattr(a, "audio", None):
        ap_ = Path(a.audio).resolve()
        place(ap_, pub / "mix" / ap_.name)
        audio_file = f"mix/{ap_.name}"
    props = {"edl": edl, "callouts": callouts, "words": words, "base": base,
             "voGainDb": a.vo_gain, "music": music, "lowerThird": a.lower_third, "fit": a.fit,
             "audioFile": audio_file, "bug": getattr(a, "bug", None)}
    pf = Path(tempfile.mkstemp(prefix="promo_props_", suffix=".json")[1])
    pf.write_text(json.dumps(props))
    print(f"[render_edl] remotion: {len(files)} media files linked under public/{base}, props {pf}")
    # chrome-for-testing: the default headless shell hangs on this macOS (see remotion.config.ts)
    cmd = ["npx", "remotion", "render", "src/index.ts", "Promo", str(out), f"--props={pf}",
           "--chrome-mode=chrome-for-testing",
           "--codec=h264", "--crf=17", "--log=error"]
    if a.concurrency:
        cmd.append(f"--concurrency={a.concurrency}")
    r = subprocess.run(cmd, cwd=str(REMOTION), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("remotion render failed:\n" + "\n".join((r.stderr + r.stdout).strip().splitlines()[-20:]))
    pf.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("film")
    ap.add_argument("--renderer", choices=["ffmpeg", "remotion"], default="ffmpeg")
    ap.add_argument("--out", default=None, help="default final/<film>.mp4 (suffixed _remotion for remotion)")
    ap.add_argument("--fit", choices=["crop", "pad"], default="crop")
    ap.add_argument("--vo-gain", type=float, default=0.0, help="static VO gain, dB")
    ap.add_argument("--music", default=None)
    ap.add_argument("--audio", default=None, help="a finished mix (promo_mix.py final/mix.wav) used as the whole soundtrack")
    ap.add_argument("--bug", default=None, help="corner logo bug text, on screen until the end card")
    ap.add_argument("--music-gain", type=float, default=-18.0, help="static music gain, dB")
    ap.add_argument("--lut", default=None, help=".cube for lut3d (ffmpeg path)")
    ap.add_argument("--lower-third", action="store_true", help="word-synced lower third (remotion)")
    ap.add_argument("--concurrency", default=None, help="remotion --concurrency")
    ap.add_argument("--keep-work", action="store_true")
    a = ap.parse_args()
    film = Path(a.film).resolve()
    try:
        edl = json.loads((film / "edl.json").read_text())
        cpath = film / edl.get("callouts", "callouts.json")
        callouts = json.loads(cpath.read_text()).get("callouts", []) if cpath.exists() else []
        words = json.loads((film / edl.get("words", "vo/words.json")).read_text())
    except Exception as e:
        print(f"[render_edl] could not read inputs: {e}", file=sys.stderr)
        sys.exit(2)
    out = Path(a.out) if a.out else film / "final" / (
        f"{film.name}.mp4" if a.renderer == "ffmpeg" else f"{film.name}_remotion.mp4")
    if not out.is_absolute():
        out = film / out
    out.parent.mkdir(parents=True, exist_ok=True)

    gate = subprocess.run([str(SF / "bin" / "mem-gate"), f"render_edl {film.name}"])  # frozen rule 11
    if gate.returncode != 0:
        print("[render_edl] memory gate refused; not rendering", file=sys.stderr)
        sys.exit(2)
    try:
        if a.renderer == "ffmpeg":
            render_ffmpeg(film, edl, callouts, out, a)
        else:
            render_remotion(film, edl, callouts, words, out, a)
    except Exception as e:
        print(f"[render_edl] {e}", file=sys.stderr)
        sys.exit(2)

    info = probe(out)
    got = float(info["format"]["duration"])
    kinds = sorted({s["codec_type"] for s in info["streams"]})
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), {})
    want = float(edl["dur"])
    ok = abs(got - want) <= 1.0 / edl["fps"] + 0.05 and "video" in kinds and ("audio" in kinds or not edl.get("audio"))
    ok = ok and v.get("width") == edl["w"] and v.get("height") == edl["h"]
    print(f"[render_edl] {out}  {got:.3f}s (edl {want:.3f}s)  {v.get('width')}x{v.get('height')} "
          f"@{v.get('r_frame_rate')}  streams {kinds}  -> {'OK' if ok else 'WRONG'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
