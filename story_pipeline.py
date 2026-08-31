#!/usr/bin/env python3
"""Story Forge pipeline — config-driven version of the bear-sister flow.

Usage:
    python3 story_pipeline.py < config.json
    python3 story_pipeline.py --config /path/to/config.json

Config JSON schema:
{
  "title": "The Bear Sister",
  "slug": "bear-sister",                     # used for output directory
  "style": "Studio Ghibli watercolor ...",   # style prefix applied to every still
  "character": "a small child in red hood",  # character signature
  "scenes": [                                # one per scene
    {
      "still": "scene 1 still prompt",
      "motion": "scene 1 motion prompt",
      "narration": "scene 1 narration line"   # optional, defaults to ""
    },
    ...
  ],
  "voice": "warm_female_storyteller",        # or "none"
  "overlays": {
    "snow_scenes": [1,2,3,4,5],
    "fireflies_scenes": [8,9,10,11,12],
    "blossom_scenes": [14,15,16],
    "aurora_scenes": [11,13],
    "dust_all": true,
    "film_grain": true,
    "vignette": true,
    "chapter_grades": {"1": "winter", "5": "dawn", "8": "cave", "11": "cosmic", "14": "spring"}
  },
  "scene_duration": 8.5                       # seconds per scene after stretch
}
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HOME = Path.home()
STATUS = Path("/tmp/mks-status.json")
FLUX = HOME / "Scripts" / "flux_t2i.py"
MAKE_VIDEO = HOME / "Desktop" / "PROJECTS" / "AI" / "videopipe" / "bin" / "make-video"
WAN_OUT = HOME / "AI" / "videopipe" / "outputs"
PIPER = HOME / ".local" / "bin" / "kokoro-piper-shim"  # Kokoro-82M af_heart ("Heart") — replaced Piper Ashley 2026-08-07
PIPER_MODEL = HOME / "Desktop" / "PROJECTS" / "Song Forge" / "piper_voices" / "en_US-libritts_r-medium.onnx"


def run(cmd, **kw):
    print(f"$ {' '.join(str(c) for c in cmd)}", flush=True)
    return subprocess.run(cmd, check=True, **kw)


def comfy_clear():
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:8188/queue",
            data=json.dumps({"clear": True}).encode(),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=5).read()
    except Exception:
        pass


def write_status(cfg, t0, work, phase, current=None):
    scenes = cfg["scenes"]
    dur = cfg.get("scene_duration", 8.5)
    payload = {
        "phase": phase,
        "title": cfg.get("title", "Untitled Story"),
        "output": str(work / f"{cfg['slug']}.mp4"),
        "started_at": t0,
        "ts": time.time(),
        "target_video_seconds": len(scenes) * dur,
        "scenes": [
            {"index": i + 1, "kind": "ai_broll", "duration": dur,
             "prompt": s.get("motion", "")}
            for i, s in enumerate(scenes)
        ],
    }
    if current:
        payload["current_scene"] = current
    STATUS.write_text(json.dumps(payload))


# ---------------------------------------------------------------------------
# Overlay procedural generators (same as overlay_pass.py)
# ---------------------------------------------------------------------------
def particle_gens(scene_dur):
    base = f"color=c=black:s=1920x1080:r=30:d={scene_dur + 0.2}"
    return {
        "snow": (f"{base},noise=alls=80:allf=t,format=gray,"
                 "geq='if(gt(lum(X,Y),245),255,0)',boxblur=1:1,"
                 "format=yuva420p,colorchannelmixer=aa=0.4"),
        "fireflies": (f"{base},noise=alls=120:allf=t,format=gray,"
                      "geq='if(gt(lum(X,Y),253),255,0)',boxblur=4:2,"
                      "format=yuva420p,colorchannelmixer=aa=0.6:rr=1.2:gg=1.0:bb=0.4"),
        "blossoms": (f"{base},noise=alls=60:allf=t,format=gray,"
                     "geq='if(gt(lum(X,Y),248),255,0)',boxblur=2:1,"
                     "format=yuva420p,colorchannelmixer=aa=0.45:rr=1.4:gg=0.7:bb=0.9"),
        "dust": (f"{base},noise=alls=30:allf=t,format=gray,"
                 "geq='if(gt(lum(X,Y),250),255,0)',boxblur=3:2,"
                 "format=yuva420p,colorchannelmixer=aa=0.20"),
        "aurora": (f"{base},"
                   "geq='r=if(gt(sin(Y/100+T*0.5)*sin(X/300+T*0.3),0.3),100,0)':"
                   "'g=if(gt(sin(Y/100+T*0.5)*sin(X/300+T*0.3),0.3),200,0)':"
                   "'b=if(gt(sin(Y/100+T*0.5)*sin(X/300+T*0.3),0.3),150,0)',"
                   "boxblur=20:10,format=yuva420p,colorchannelmixer=aa=0.35"),
    }


GRADE_PRESETS = {
    "winter": "curves=preset=increase_contrast,colorbalance=rs=-0.10:gs=-0.05:bs=0.15:rm=-0.10:bm=0.10,eq=saturation=0.85",
    "dawn":   "curves=preset=lighter,colorbalance=rs=0.10:gs=0.05:bs=-0.10,eq=saturation=1.10",
    "cave":   "colorbalance=rs=0.20:gs=0.10:bs=-0.20:rm=0.10:bm=-0.10,eq=saturation=1.15:gamma=0.95",
    "cosmic": "colorbalance=rs=-0.05:gs=-0.10:bs=0.25:rm=0.15:gm=-0.10:bm=0.20,eq=saturation=1.30",
    "spring": "curves=preset=lighter,colorbalance=rs=0.10:gs=0.10:bs=-0.05,eq=saturation=1.20",
    "neutral": "eq=saturation=1.05",
}


def grade_for_scene(idx, chapter_grades):
    # chapter_grades is dict like {"1":"winter","5":"dawn","8":"cave"} meaning grade applies
    # from that scene forward until the next chapter mark.
    sorted_marks = sorted((int(k), v) for k, v in chapter_grades.items())
    active = "neutral"
    for mark_idx, mark_name in sorted_marks:
        if idx >= mark_idx:
            active = mark_name
    return GRADE_PRESETS.get(active, GRADE_PRESETS["neutral"])


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="path to JSON config; reads stdin if omitted")
    args = parser.parse_args()

    if args.config:
        cfg = json.loads(Path(args.config).read_text())
    else:
        cfg = json.loads(sys.stdin.read())

    slug = cfg["slug"]
    title = cfg.get("title", "Untitled")
    scenes = cfg["scenes"]
    scene_dur = float(cfg.get("scene_duration", 8.5))
    work = HOME / "Desktop" / "AI Videos" / slug
    work.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    write_status(cfg, t0, work, "starting")

    # ── 1. Flux stills ─────────────────────────────────────────────────
    print(f"\n=== Generating {len(scenes)} Flux stills ===", flush=True)
    for i, sc in enumerate(scenes, start=1):
        write_status(cfg, t0, work, "rendering_scene", current={
            "index": i, "kind": "ai_image", "duration": scene_dur,
            "prompt": "Flux still: " + sc["still"][:80],
            "started_at": time.time(),
        })
        png = work / f"still_{i:02d}.png"
        if not png.exists():
            run([str(FLUX), sc["still"], "--out", str(png),
                 "--w", "832", "--h", "480", "--seed", str(73 + i * 17)])

    # ── 2. Wan i2v clips ───────────────────────────────────────────────
    print("\n=== Wan 2.2 i2v clips ===", flush=True)
    clips = []
    pts_mult = scene_dur / 5.0
    for i, sc in enumerate(scenes, start=1):
        scene_started = time.time()
        write_status(cfg, t0, work, "rendering_scene", current={
            "index": i, "kind": "ai_broll", "duration": scene_dur,
            "prompt": sc["motion"], "started_at": scene_started,
        })
        raw = work / f"raw_{i:02d}.mp4"
        if not raw.exists():
            comfy_clear()
            run([
                "python3", str(MAKE_VIDEO),
                "--gguf", "--i2v", str(work / f"still_{i:02d}.png"),
                "--duration", "5.0", "--res", "832x480",
                "--label", f"{slug}_{i:02d}",
                sc["motion"],
            ])
            cands = sorted(WAN_OUT.glob(f"{slug}_{i:02d}_*.mp4"),
                           key=lambda p: p.stat().st_mtime, reverse=True)
            if not cands:
                raise RuntimeError(f"no Wan output for scene {i}")
            shutil.copy(cands[0], raw)

        conformed = work / f"clip_{i:02d}.mp4"
        if not conformed.exists():
            run([
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(raw),
                "-vf", (f"setpts=PTS*{pts_mult:.4f},"
                        "scale=1920:1080:force_original_aspect_ratio=increase,"
                        "crop=1920:1080,fps=30"),
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
                "-t", str(scene_dur),
                str(conformed),
            ])
        clips.append(conformed)

    # ── 3. Narration via Piper (warm female storyteller) ───────────────
    voice = cfg.get("voice", "warm_female_storyteller")
    vo = work / "vo.wav"
    if voice == "warm_female_storyteller" and any(s.get("narration") for s in scenes):
        write_status(cfg, t0, work, "narration")
        print("\n=== Warm female narration (scene-synced) ===", flush=True)
        if not vo.exists():
            pieces_dir = work / "vo_pieces"
            pieces_dir.mkdir(exist_ok=True)
            # Render each narration line and track its scene index
            scene_pieces = []  # list of (scene_idx_1based, Path)
            for i, sc in enumerate(scenes, start=1):
                line = sc.get("narration", "").strip()
                if not line:
                    continue
                piece = pieces_dir / f"p_{i:02d}.wav"
                if not piece.exists():
                    subprocess.run(
                        [str(PIPER), "-m", str(PIPER_MODEL), "-f", str(piece),
                         "--speaker", "0",
                         "--length-scale", "1.18",
                         "--noise-scale", "0.5",
                         "--noise-w-scale", "0.7"],
                        input=line, text=True, check=True,
                    )
                scene_pieces.append((i, piece))

            # Build adelay+amix command so each line starts at its scene's onscreen start.
            # Scene N onscreen starts at (N-1) * (scene_dur - xfade) seconds.
            xfade = 0.5
            scene_advance = scene_dur - xfade
            total_audio_dur = (len(scenes) - 1) * scene_advance + scene_dur  # match video duration
            args = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning"]
            fc_parts = []
            mix_labels = []
            for input_idx, (scene_i, piece) in enumerate(scene_pieces):
                args += ["-i", str(piece)]
                delay_ms = int((scene_i - 1) * scene_advance * 1000)
                fc_parts.append(f"[{input_idx}:a]adelay={delay_ms}|{delay_ms}[a{input_idx}]")
                mix_labels.append(f"[a{input_idx}]")
            fc = ";".join(fc_parts) + ";" + "".join(mix_labels) + \
                 f"amix=inputs={len(scene_pieces)}:duration=longest:normalize=0," \
                 f"apad=whole_dur={total_audio_dur}[amixed]"
            vo_raw = work / "vo_raw.wav"
            args += ["-filter_complex", fc, "-map", "[amixed]",
                     "-t", str(total_audio_dur),
                     "-c:a", "pcm_s16le", str(vo_raw)]
            run(args)

            run([
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(vo_raw),
                "-af", ("highpass=f=80,"
                        "equalizer=f=250:t=h:width=200:g=2,"
                        "equalizer=f=7000:t=h:width=2000:g=-2,"
                        "acompressor=threshold=-18dB:ratio=2.5:attack=8:release=180,"
                        "aecho=0.7:0.85:60:0.15,"
                        "loudnorm=I=-16:LRA=11:TP=-1.5"),
                "-ar", "48000", "-ac", "2",
                str(vo),
            ])

    # ── 4. Overlay compositing ─────────────────────────────────────────
    write_status(cfg, t0, work, "overlay")
    print("\n=== Overlay compositing ===", flush=True)
    overlays = cfg.get("overlays", {})
    chapter_grades = overlays.get("chapter_grades", {})
    gens = particle_gens(scene_dur)
    enhanced = work / "enhanced"
    enhanced.mkdir(exist_ok=True)
    enhanced_clips = []
    for i in range(1, len(scenes) + 1):
        base = work / f"clip_{i:02d}.mp4"
        out = enhanced / f"clip_{i:02d}.mp4"
        if not out.exists():
            layers = []
            if i in overlays.get("snow_scenes", []):
                layers.append(gens["snow"])
            if i in overlays.get("fireflies_scenes", []):
                layers.append(gens["fireflies"])
            if i in overlays.get("aurora_scenes", []):
                layers.append(gens["aurora"])
            if i in overlays.get("blossom_scenes", []):
                layers.append(gens["blossoms"])
            if overlays.get("dust_all", False):
                layers.append(gens["dust"])

            grade = grade_for_scene(i, chapter_grades)
            grain = "noise=alls=8:allf=t," if overlays.get("film_grain", True) else ""
            vig = "vignette=PI/4" if overlays.get("vignette", True) else "null"

            fc_parts = []
            fc_parts.append(f"[0:v]{grade},{grain}{vig}[base]")
            last = "[base]"
            for n, gen in enumerate(layers):
                fc_parts.append(f"{gen}[gen{n}]")
                fc_parts.append(f"{last}[gen{n}]overlay=eof_action=pass:format=auto[p{n}]")
                last = f"[p{n}]"

            run([
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
                "-i", str(base),
                "-filter_complex", ";".join(fc_parts),
                "-map", last,
                "-t", str(scene_dur),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "18",
                "-r", "30",
                str(out),
            ])
        enhanced_clips.append(out)

    # ── 5. Stitch with xfade ───────────────────────────────────────────
    write_status(cfg, t0, work, "concatenating")
    print("\n=== Stitch ===", flush=True)
    xfade = 0.5
    visuals = work / "visuals.mp4"
    inputs = []
    for c in enhanced_clips:
        inputs += ["-i", str(c)]
    fc = []
    last = "[0:v]"
    off = scene_dur - xfade
    for i in range(1, len(enhanced_clips)):
        label = f"v{i}"
        fc.append(f"{last}[{i}:v]xfade=transition=fade:duration={xfade}:offset={off:.3f}[{label}]")
        last = f"[{label}]"
        off += scene_dur - xfade
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        *inputs, "-filter_complex", ";".join(fc),
        "-map", last,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "18",
        "-r", "30", "-an", str(visuals),
    ])

    # ── 6. Final mux ──────────────────────────────────────────────────
    print("\n=== Final mux ===", flush=True)
    visuals_dur = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(visuals)],
        text=True,
    ).strip())
    fade_out = visuals_dur - 1.5

    final = work / f"{slug}.mp4"
    if vo.exists():
        run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(visuals), "-i", str(vo),
            "-filter_complex",
            f"[0:v]fade=in:st=0:d=0.8,fade=out:st={fade_out}:d=1.5[v];"
            f"[1:a]volume=1.0,afade=in:st=0:d=0.6,afade=out:st={fade_out}:d=1.5,apad[a]",
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-shortest",
            "-movflags", "+faststart",
            str(final),
        ])
    else:
        run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(visuals),
            "-vf", f"fade=in:st=0:d=0.8,fade=out:st={fade_out}:d=1.5",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "18",
            "-movflags", "+faststart",
            str(final),
        ])

    write_status(cfg, t0, work, "done")
    print(f"\nDONE -> {final}", flush=True)
    subprocess.run(["open", str(final)], check=False)


if __name__ == "__main__":
    main()
