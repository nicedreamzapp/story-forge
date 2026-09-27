#!/usr/bin/env python3
"""Animation runner — LTX i2v (multi-scale lightricks, 768x512 known-safe) +
ken_burns glides. Sequential, watchdogged, crash-resumable (skips existing clips).
All clips conformed to 1280x720 @ 24fps for uniform assembly."""
import json, subprocess, sys, time, glob, os
from pathlib import Path

HOME = Path.home()
PROJ = HOME / "Desktop/PROJECTS/story-forge/projects/antarctica"
SF = HOME / "Desktop/PROJECTS/story-forge"
LTX = SF / "bin/make-ltx-lightricks"
KB = SF / "bin/ken_burns.py"
LTX_OUT = HOME / "AI/videopipe/outputs"
CLIPS = PROJ / "clips"
TMP = PROJ / "clips/_tmp"
TMP.mkdir(parents=True, exist_ok=True)

KB_MODE = {"in": ("pushin", None), "in_slow": ("pushslow", None),
           "in_fast": ("pushin", 0.22), "left": ("panL", None),
           "right": ("panR", None), "out": ("pullback", None)}

data = json.loads((PROJ / "shots.json").read_text())
shots = data["shots"]
only = set(sys.argv[1:])

def conform(src, dst, dur=None):
    """any input -> 1280x720 24fps h264, optional duration trim"""
    cmd = ["ffmpeg", "-y", "-i", str(src)]
    if dur:
        cmd += ["-t", f"{dur:.2f}"]
    cmd += ["-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720",
            "-r", "24", "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p",
            "-an", str(dst)]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=300).returncode == 0

done = fail = skip = 0
for sh in shots:
    if only and sh["id"] not in only:
        continue
    out = CLIPS / f"{sh['id']}.mp4"
    if out.exists() and not only:
        skip += 1
        continue
    still = PROJ / "stills" / f"{sh['still']}.png"
    if not still.exists():
        print(f"MISSING_STILL {sh['id']} {sh['still']}", flush=True)
        fail += 1
        continue
    t = time.time()
    try:
        if sh["m"] == "kb":
            mode, zoom = KB_MODE[sh["kb"]]
            cmd = ["python3", str(KB), str(still), str(out),
                   "--dur", str(sh["d"]), "--mode", mode]
            if zoom:
                cmd += ["--zoom", str(zoom)]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            ok = r.returncode == 0 and out.exists()
        else:  # ltx
            # LTX wants 768x512 input; downscale the 1152x768 still (same 3:2)
            small = TMP / f"{sh['still']}_768.png"
            if not small.exists():
                subprocess.run(["ffmpeg", "-y", "-i", str(still), "-vf",
                                "scale=768:512", str(small)],
                               capture_output=True, timeout=60)
            before = set(glob.glob(str(LTX_OUT / f"{sh['id']}_ltxL_*.mp4")))
            ltx_py = str(HOME / "AI/ComfyUI/venv/bin/python")
            r = subprocess.run([ltx_py, str(LTX), "--i2v", str(small),
                                "--duration", str(min(sh["d"], 6.0)),
                                "--res", "768x512", "--label", sh["id"], sh["mp"]],
                               capture_output=True, text=True, timeout=1200)
            after = set(glob.glob(str(LTX_OUT / f"{sh['id']}_ltxL_*.mp4")))
            new = sorted(after - before, key=os.path.getmtime)
            ok = bool(new) and conform(new[-1], out)
        if ok:
            done += 1
            print(f"OK {sh['id']} {sh['m']} ({time.time()-t:.0f}s)", flush=True)
        else:
            fail += 1
            err = (r.stderr or "").strip().splitlines()
            print(f"FAIL {sh['id']} {sh['m']}: {err[-1] if err else 'no output'}", flush=True)
    except subprocess.TimeoutExpired:
        fail += 1
        print(f"TIMEOUT {sh['id']}", flush=True)
    time.sleep(3)  # MPS settle

print(f"CLIPS_DONE ok={done} fail={fail} skip={skip}", flush=True)
