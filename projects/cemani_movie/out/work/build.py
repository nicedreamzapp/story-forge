#!/usr/bin/env python3
"""Cemani v1 cut: stills (sub-pixel push-ins), clips (blurred fill for vertical), music + sfx bed, EDL."""
import json, os, subprocess, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

ROOT = Path.home() / "Desktop/PROJECTS/story-forge/projects/cemani_movie"
F = ROOT / "footage"; OUT = ROOT / "out"; W = OUT / "work"; SEG = W / "seg"; SEG.mkdir(parents=True, exist_ok=True)
MUS = OUT / "music"; SFX = OUT / "sfx"
REPO = Path.home() / "Desktop/PROJECTS/CemaniHomesteadRobot/docs"
FPS, WW, HH = 30, 1920, 1080
FONT = "/System/Library/Fonts/Helvetica.ttc"
B92, B96, B70, B104 = 60/92*4, 60/96*4, 60/70*4, 60/104*4

P = F / "photos"; R = F / "renders"; V3 = P / "steering_v3_real/v3"; CAD = R / "steering_v3_cad_renders"; PT = CAD / "parts"
def v3(n): return next(V3.glob(f"*IMG_{n}.jpg"))
MOB = F / "repo_clips/robot_finally_mobile.mp4"; FIRE = F / "repo_clips/robot_pulling_cart_firewood.mp4"
NIGHT = F / "repo_clips/6E106B08.mp4"; YT = F / "youtube_demo.mp4"
G4B = F / "gif_clips/build-4ws.mp4"; G4S = F / "gif_clips/steering-4ws.mp4"
WSR = F / "steering_4ws_real_1080p.mp4"; WSN = F / "steering_4ws_normal_1080p.mp4"; TR = F / "steering_turn_radius_720p.mp4"

# shot: (kind, src, dur, opts) ; kind S=still V=video K=black/title
CH = [
 ("Cold open", None, [
   ("K", None, 1.5, {}),
   ("V", MOB, 3.4, {"in": 7.0, "aud": 0.0}),
   ("K", None, 1.6, {}),
   ("K", None, 4.0, {"title": "Built on a Homestead"}),
 ]),
 ("1. Four motors, one brain", "m1_build_sparse", [
   ("S", P / "repo_media_stills/Photoroom_20251025_185931.JPG", 2*B92, {"mode": "in"}),
   ("S", P / "repo_media_stills/Photoroom_20251027_050455.JPG", 1.5*B92, {"mode": "out"}),
   ("S", P / "steering_v3_real/IMG_7735.jpg", 1.5*B92, {"mode": "in"}),
   ("V", NIGHT, 2*B92, {"in": 9.0}),
   ("S", P / "steering_rebuild/IMG_7680.jpeg", B92, {"mode": "in"}),
   ("S", P / "steering_rebuild/IMG_7684.jpeg", B92, {"mode": "panR"}),
   ("S", REPO / "robot-diagram.png", B92, {"mode": "in", "fit": "contain"}),
   ("V", MOB, 2*B92, {"in": 0.5}),
   ("S", P / "steering_rebuild/IMG_7683.jpeg", B92, {"mode": "in"}),
   ("S", P / "steering_v3_real/matt_robot_ref.jpg", 1.5*B92, {"mode": "in"}),
 ]),
 ("2. It rolls", None, [
   ("V", MOB, 4*B92, {"in": 5.5}),
   ("V", MOB, 3*B92, {"in": 17.0}),
   ("V", NIGHT, 3*B92, {"in": 22.0}),
   ("V", MOB, 2*B92, {"in": 25.5}),
 ]),
 ("3. Earning its keep", "m2_full_groove", [
   ("V", FIRE, 6*B96, {"in": 0.2, "aud": 0.5}),
   ("S", REPO / "command-center.png", 1.6*B96, {"mode": "in", "fit": "contain"}),
   ("V", FIRE, 3.6*B96, {"in": 6.5, "aud": 0.5}),
 ]),
 ("4. The shudder", "m3_low_pad", [
   ("V", MOB, 2*B70, {"in": 7.5, "speed": 0.5, "aud": 0.0}),
   ("S", P / "repo_docs_photos/current-front.jpg", B70, {"mode": "in"}),
   ("S", P / "repo_docs_photos/measure-IMG_7729.jpg", B70, {"mode": "in", "label": "4 1/2 in between tires"}),
   ("S", P / "repo_docs_photos/current-corner.jpg", B70, {"mode": "slow"}),
   ("K", None, 2.0, {}),
   ("V", FIRE, 1.2*B70, {"in": 12.0, "speed": 0.5, "aud": 0.0, "grade": "cold"}),
   ("S", P / "repo_docs_photos/current-suspension.jpg", B70, {"mode": "slow", "grade": "cold"}),
 ]),
 ("5. Back to the drawing board", "m4_iteration_build", [
   ("S", R / "new-frame.png", 1.5*B104, {"mode": "in", "fit": "contain"}),
   ("S", R / "how-it-steers.jpg", 1.5*B104, {"mode": "in"}),
   ("S", R / "frame_v2_blender/bare-frame.jpg", 1.5*B104, {"mode": "in", "label": "2020 extrusion"}),
   ("V", G4B, 3*B104, {"in": 1.2}),
   ("S", R / "frame_v2_blender/bare-side.jpg", 1.5*B104, {"mode": "panR", "label": "gusset"}),
   ("S", R / "frame_v2_blender/bare-underneath.jpg", 1.5*B104, {"mode": "in", "label": "cross rail"}),
   ("S", R / "frame_v3_blender/iso.jpg", 1.5*B104, {"mode": "in"}),
   ("V", WSR, 2*B104, {"in": 30.0, "speed": 3.0}),
   ("S", v3(8097), 1.5*B104, {"mode": "in"}),
   ("S", v3(8098), 1.5*B104, {"mode": "panL"}),
   ("S", v3(8116), 1.5*B104, {"mode": "in"}),
 ]),
 ("6. The corner problem", None, [
   ("S", R / "where-the-lazy-susan-goes.jpg", 1.5*B104, {"mode": "in", "label": "6 in lazy susan"}),
   ("S", PT / "ucf204-12_housing_alone.png", 1.5*B104, {"mode": "in", "label": "UCF204-12, 3/4 in bore", "fit": "contain"}),
   ("S", PT / "ucf204-12_insert_alone.png", B104, {"mode": "in", "label": "UCF204 bearing insert", "fit": "contain"}),
   ("V", WSN, 2*B104, {"in": 12.0, "speed": 3.0}),
   ("S", PT / "clamp_collar_3-4_double_split_half_alone.png", B104, {"mode": "in", "label": "3/4 in shaft collar", "fit": "contain"}),
   ("S", PT / "steering_plate_left_alone.png", 1.5*B104, {"mode": "in", "label": "1/4 in steering plate", "fit": "contain"}),
   ("S", PT / "heim_CF5_5-16-24_RH_alone.png", B104, {"mode": "in", "label": "heim joint", "fit": "contain"}),
   ("V", WSN, 2*B104, {"in": 47.0, "speed": 3.0}),
   ("S", PT / "tie_rod_5-16-24_alone.png", B104, {"mode": "in", "label": "5/16 tie rod", "fit": "contain"}),
   ("S", PT / "clevis_pin_3-4x2-1-2_cut_alone.png", B104, {"mode": "in", "label": "clevis pin", "fit": "contain"}),
   ("S", PT / "actuator_LACT4P_body_inplace.png", B104, {"mode": "in", "label": "linear actuator", "fit": "contain"}),
   ("K", None, B104/2, {}),
   ("S", CAD / "exploded_corner.png", 2.5*B104, {"mode": "in", "fit": "contain"}),
   ("S", CAD / "iso.png", 1.5*B104, {"mode": "in", "fit": "contain"}),
 ]),
 ("7. Turn all four", "m5_peak", [
   ("V", TR, 3*B104, {"in": 1.0, "speed": 1.5}),
   ("V", WSR, 2*B104, {"in": 18.0, "speed": 3.0}),
   ("V", WSR, 2*B104, {"in": 40.0, "speed": 3.0}),
   ("V", WSR, 2*B104, {"in": 58.0, "speed": 3.0}),
   ("V", WSR, 2*B104, {"in": 83.0, "speed": 3.0}),
   ("V", G4S, 2*B104, {"in": 0.0}),
   ("S", CAD / "top.png", 1.5*B104, {"mode": "in", "fit": "contain"}),
 ]),
 ("8. Faster every time", "m6_warm_close", [
   ("S", v3(8110), 1.5*B92, {"mode": "in"}),
   ("S", P / "steering_v3_real/v3_frame_34.jpg", 1.5*B92, {"mode": "in"}),
   ("S", CAD / "front.png", 1.5*B92, {"mode": "in", "fit": "contain"}),
   ("V", FIRE, 2.5*B92, {"in": 9.0, "aud": 0.5}),
   ("K", None, 1.5, {}),
   ("K", None, 4.0, {"title": "Cemani", "sub": "github.com/nicedreamzapp/CemaniHomesteadRobot"}),
 ]),
]

def font(sz): return ImageFont.truetype(FONT, sz)

def label_png(text, path):
    f = font(34); pad = 16
    w = int(f.getlength(text)) + 2*pad; h = 34 + 2*pad
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w-1, h-1), radius=12, fill=(10, 12, 16, 190))
    d.text((pad, pad-2), text, font=f, fill=(255, 255, 255, 235))
    im.save(path); return im

def compose(src, fit, scale):
    im = Image.open(src).convert("RGB"); w, h = im.size; CW, CH_ = int(WW*scale), int(HH*scale)
    ar = w/h
    if fit != "contain" and 1.3 <= ar <= 1.9:
        s = max(CW/w, CH_/h); im = im.resize((round(w*s), round(h*s)), Image.LANCZOS)
        x, y = (im.width-CW)//2, (im.height-CH_)//2
        return im.crop((x, y, x+CW, y+CH_))
    # blurred fill background + contained foreground
    s = max(CW/w, CH_/h); bg = im.resize((round(w*s), round(h*s)), Image.BILINEAR)
    x, y = (bg.width-CW)//2, (bg.height-CH_)//2; bg = bg.crop((x, y, x+CW, y+CH_))
    bg = bg.resize((CW//8, CH_//8)).filter(ImageFilter.GaussianBlur(6)).resize((CW, CH_), Image.BILINEAR)
    bg = ImageEnhance.Brightness(bg).enhance(0.45)
    s = min(CW/w, CH_/h) * (0.94 if fit == "contain" else 1.0); fg = im.resize((round(w*s), round(h*s)), Image.LANCZOS)
    bg.paste(fg, ((CW-fg.width)//2, (CH_-fg.height)//2)); return bg

def ease(t): return t*t*(3-2*t)

def render_still(args):
    i, src, dur, o = args
    out = SEG / f"{i:03d}.mp4"
    if out.exists(): return str(out)
    sc = 1.35; base = compose(src, o.get("fit"), sc)
    if o.get("grade") == "cold": base = ImageEnhance.Color(base).enhance(0.45)
    lab = label_png(o["label"], W / f"lab{i}.png") if o.get("label") else None
    n = round(dur*FPS); mode = o.get("mode", "in")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WW}x{HH}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    for k in range(n):
        t = ease(k/max(1, n-1))
        z0, z1, dx = {"in": (1.0, 1.16, 0), "slow": (1.0, 1.10, 0), "out": (1.10, 1.0, 0), "panR": (1.08, 1.08, 1), "panL": (1.08, 1.08, -1)}[mode]
        z = z0 + (z1-z0)*t; s = sc/z
        cx = base.width/2 + dx*(t-0.5)*base.width*0.06; cy = base.height/2
        fr = base.transform((WW, HH), Image.AFFINE, (s, 0, cx-WW/2*s, 0, s, cy-HH/2*s), resample=Image.BICUBIC)
        if lab is not None:
            a = min(1.0, k/(0.3*FPS)); l2 = lab.copy(); l2.putalpha(l2.getchannel("A").point(lambda v: int(v*a)))
            fr.paste(l2, (70, HH-70-lab.height), l2)
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait(); return str(out)

def render_black(args):
    i, dur, o = args
    out = SEG / f"{i:03d}.mp4"
    if out.exists(): return str(out)
    n = round(dur*FPS)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WW}x{HH}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    for k in range(n):
        im = Image.new("RGB", (WW, HH), (0, 0, 0))
        if o.get("title"):
            t = k/FPS; a = min(1, t/0.8, (dur-t)/0.8); a = max(0, a); c = int(235*a)
            d = ImageDraw.Draw(im); f = font(84 if not o.get("sub") else 76)
            tw = f.getlength(o["title"]); d.text(((WW-tw)/2, HH/2-60), o["title"], font=f, fill=(c, c, c))
            if o.get("sub"):
                f2 = font(30); sw = f2.getlength(o["sub"]); cc = int(170*a); d.text(((WW-sw)/2, HH/2+50), o["sub"], font=f2, fill=(cc, cc, cc))
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait(); return str(out)

def probe_vert(src):
    o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(src)], capture_output=True, text=True).stdout.strip().split(",")
    w, h = int(o[0]), int(o[1]); return h > w*0.9

def render_video(args):
    i, src, dur, o = args
    out = SEG / f"{i:03d}.mp4"
    if out.exists(): return str(out)
    sp = o.get("speed", 1.0); grade = ",hue=s=0.45" if o.get("grade") == "cold" else ""
    pre = f"setpts=PTS/{sp}," if sp != 1.0 else ""
    if probe_vert(src):
        vf = (f"[0:v]{pre}fps={FPS},split[a][b];[a]scale={WW}:{HH}:force_original_aspect_ratio=increase,crop={WW}:{HH},scale=240:-2,gblur=sigma=8,scale={WW}:{HH},eq=brightness=-0.18[bg];"
              f"[b]scale=-2:{HH}:flags=lanczos[fg];[bg][fg]overlay=(W-w)/2:0{grade},format=yuv420p[v]")
    else:
        vf = (f"[0:v]{pre}fps={FPS},scale={WW}:{HH}:force_original_aspect_ratio=decrease:flags=lanczos,pad={WW}:{HH}:(ow-iw)/2:(oh-ih)/2:black{grade},format=yuv420p[v]")
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(o.get("in", 0)), "-t", f"{dur*sp+0.5:.3f}", "-i", str(src), "-filter_complex", vf, "-map", "[v]",
           "-frames:v", str(round(dur*FPS)), "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-r", str(FPS), str(out)]
    subprocess.run(cmd, check=True); return str(out)

def main():
    jobs, edl, t, idx = [], [], 0.0, 0
    chapters = []
    for name, cue, shots in CH:
        c0 = t
        for kind, src, dur, o in shots:
            n = round(dur*FPS); d = n/FPS
            jobs.append((kind, (idx, src, d, o) if kind != "K" else (idx, d, o)))
            edl.append({"i": idx, "chapter": name, "in_film": round(t, 3), "out_film": round(t+d, 3), "kind": {"S": "still", "V": "video", "K": "black/title"}[kind],
                        "source": str(src) if src else None, "source_in": o.get("in"), "speed": o.get("speed", 1.0), "label": o.get("label"), "title": o.get("title"),
                        "clip_audio_gain": o.get("aud", 0.0) if kind == "V" else None})
            t += d; idx += 1
        chapters.append({"name": name, "start": round(c0, 3), "end": round(t, 3), "music_cue": cue})
    total = t
    with ProcessPoolExecutor(10) as ex:
        futs = [ex.submit({"S": render_still, "V": render_video, "K": render_black}[k], a) for k, a in jobs]
        segs = [f.result() for f in futs]
    (W / "concat.txt").write_text("".join(f"file '{s}'\n" for s in segs))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(W / "concat.txt"), "-c", "copy", str(W / "picture.mp4")], check=True)

    # ---- audio ----
    ev = []  # (file, at, src_in, dur, gain_db, fin, fout, tempo)
    cue_ch = {}
    for c in chapters:
        if c["music_cue"]: cue_ch.setdefault(c["music_cue"], [c["start"], c["end"]])
        elif cue_ch: list(cue_ch.values())[-1][1] = c["end"]
    # cold open: m1 begins under the title (motif enters on the cut to black)
    co = chapters[0]; m1 = cue_ch["m1_build_sparse"]; m1[0] = edl[2]["in_film"]
    music = []
    for cue, (a, b) in cue_ch.items():
        f = MUS / f"{cue}.wav"
        last = cue == "m6_warm_close"
        d = (b - a) + (0 if last else 1.2)
        fd = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(f)],capture_output=True,text=True).stdout)
        d = min(d, fd)
        music.append({"cue": cue, "file": str(f), "at": round(a, 3), "dur": round(d, 3)})
        ev.append((f, a, 0.0, d, -4.0, 0.4 if cue != "m1_build_sparse" else 2.0, 1.2 if not last else 3.5, 1.0))
    # clip audio (real robot sound) on spine clips
    for e in edl:
        if e["kind"] == "video" and (e["clip_audio_gain"] or 0) > 0:
            ev.append((Path(e["source"]), e["in_film"], e["source_in"], e["out_film"]-e["in_film"], -10.0, 0.15, 0.25, 1.0))
    def sfx(name, at, dur, g, fin=0.05, fout=0.3):
        f = SFX / name
        if f.exists(): ev.append((f, at, 0.0, dur, g, fin, fout, 1.0))
    sfx("whine_scrub.wav", 0.2, 4.7, -6, 1.2, 0.05)          # cold open, cut hard at black
    sfx("whine_scrub.wav", chapters[4]["start"], edl_t(edl, chapters[4]["start"]), -10, 0.3, 0.6)
    corner = next(e for e in edl if e["source"] and "current-corner" in e["source"])
    sfx("clank.wav", corner["in_film"]+0.3, 2.5, -6)
    for e in edl:
        if e["chapter"].startswith("5.") and e["kind"] == "still" and e["i"] % 2 == 0:
            sfx("workshop.wav", e["in_film"], min(3.0, e["out_film"]-e["in_film"]), -16, 0.2, 0.5)
        if e["chapter"].startswith("6.") and e["label"]:
            sfx("seat_click.wav", e["in_film"]+0.05, 1.0, -12, 0.0, 0.3)
    drop = [e for e in edl if e["chapter"].startswith("6.") and e["kind"] == "black/title"]
    for e in drop: sfx("thunk.wav", e["in_film"], 1.2, -10)
    last8 = chapters[-1]
    sfx("outdoor.wav", last8["start"]+3*B92, 8.0, -16, 1.0, 2.0)
    inputs, fl = [], []
    for k, (f, at, si, d, g, fin, fout, tp) in enumerate(ev):
        inputs += ["-i", str(f)]
        fl.append(f"[{k+1}:a]atrim=start={si}:duration={d:.3f},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=stereo,"
                  f"afade=t=in:d={fin},afade=t=out:st={max(0, d-fout):.3f}:d={fout},volume={g}dB,adelay={int(at*1000)}|{int(at*1000)}[a{k}]")
    fl.append("".join(f"[a{k}]" for k in range(len(ev))) + f"amix=inputs={len(ev)}:normalize=0:dropout_transition=0,atrim=duration={total:.3f},"
              f"loudnorm=I=-20:TP=-2:LRA=11[aout]")
    (W / "audio_graph.txt").write_text(";\n".join(fl))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(W / "picture.mp4")] + inputs + ["-filter_complex", ";".join(fl), "-map", "0:v", "-map", "[aout]",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", "-shortest", str(OUT / "cemani_v1.mp4")], check=True)
    json.dump({"film": "out/cemani_v1.mp4", "duration": round(total, 3), "fps": FPS, "size": [WW, HH], "chapters": chapters, "music": music,
               "voice_track": {"status": "pending (Matt's voice memos)", "duck_music_db": -10, "note": "lay memos per chapter; duck music cues listed under 'music' while voice plays"},
               "shots": edl}, open(OUT / "edl.json", "w"), indent=1)
    print("TOTAL", round(total, 2))
    for c in chapters: print(c)

def edl_t(edl, start):
    return 4.0

if __name__ == "__main__":
    main()
