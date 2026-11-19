#!/usr/bin/env python3
"""finish_v5.py — plan_v5 cut (copied from finish_v4.py; v4 untouched). Straight cuts from tools/timeline_v5.json.
Per row: the plan part D clip in 'replace_with' when that file exists, else 'clip'. No code lantern, no parabola, no
painted splash, no chipmunk cutout, no button (Matt's ending A, 11/18 1:57 AM). Row 7 fallback (H_ditch) plays at
'speed' with the light-out grade ramp over its last 'light_out' s; the D6 keyframe clip plays at 1.0 with no ramp
(the flame goes out in the clip). Row 16 = the hflipped title hill, title painted in AFTER the flip. Row 17 = black.
Run detached (nohup). Not run in steps 1-4.
  finish_v5.py --out final/picture_v5.mp4
"""
from __future__ import annotations
import argparse, json, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
import paintlib as pl
from paintlib import PW, PH, OW, OH, FPS, ease

P = Path(__file__).resolve().parent.parent
TL = json.load(open(P / __import__("os").getenv("TIMELINE", "tools/timeline_v5.json")))   # v5.2: TIMELINE=tools/timeline_v52.json
ROWS = TL["rows"]
FR = {}; USED = {}


def clip_len(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip() or 0)


def pick(r):
    rw = r.get("replace_with")
    return rw if rw and (P / rw).exists() else r["clip"]


def load():
    for r in ROWS:
        c = pick(r); USED[r["id"]] = c
        if c == "black":
            continue
        f = P / c
        if not f.exists():
            sys.exit(f"MISSING {c} for {r['id']}")
        FR[r["id"]] = pl.load_clip(f)
        sp = r.get("speed", 1.0) if c == r["clip"] else 1.0
        need = r["in"] + r["dur"] * sp
        if clip_len(f) + 0.05 < need:
            print(f"  WARNING {r['id']}: clip {clip_len(f):.2f}s shorter than in+dur {need:.2f}s; last frame would hold", flush=True)
        print(f"  {r['id']:14s} <- {c}", flush=True)
    pl.title_layer()


def row_frame(r, tl):
    rid = r["id"]; c = USED[rid]
    if c == "black":
        return np.zeros((PH, PW, 3), np.float32)
    fallback = c == r["clip"]
    sp = r.get("speed", 1.0) if fallback else 1.0
    frs = FR[rid]; k = max(0, min(len(frs) - 1, int(round((r["in"] + tl * sp) * 24))))
    fr = frs[k].astype(np.float32) / 255.0
    if fallback and "light_out" in r:
        u = ease((tl - (r["dur"] - r["light_out"])) / r["light_out"])
        if u > 0:
            fr = np.clip(fr * (1 - 0.4 * u) * np.array([1 - 0.14 * u, 1 - 0.06 * u, 1 + 0.04 * u], np.float32), 0, 1).astype(np.float32)
    if "title_in" in r:
        u = (tl - r["title_in"]) / r["title_dur"]
        if u > 0: fr = pl.title_reveal(fr, min(1.0, u))
    return fr


def render(t):
    for i, r in enumerate(ROWS):
        if r["start"] <= t < r["start"] + r["dur"] or (i == len(ROWS) - 1 and t >= r["start"]):
            return pl.view(row_frame(r, t - r["start"]), PW / 2, PH / 2, 1.0)
    return np.zeros((OH, OW, 3), np.float32)


def frame_u8(i): return (np.clip(render(i / FPS), 0, 1) * 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(P / "final/picture_v5.mp4")); ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args(); load()
    total = TL["total"]; n = int(round(total * FPS)); print(f"cut: {len(ROWS)} rows, {total:.2f} s", flush=True)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", a.out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE); t0 = time.time(); cv2.setNumThreads(2)
    with ThreadPoolExecutor(a.workers) as pool:
        for fr in pool.map(frame_u8, range(n)): ff.stdin.write(fr.tobytes())
    ff.stdin.close(); ff.wait(); print(f"picture -> {a.out} ({total:.2f} s) in {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
