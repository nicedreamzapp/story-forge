#!/usr/bin/env python3
"""qc_movie.py — automated lip-match QC gate. Run BEFORE showing Matt anything.

For each scene + character box it:
  1. dumps a tight mouth montage (for fast visual verification)
  2. measures mouth-OPENNESS per frame via local contrast (open mouth = teeth/gap
     contrast; closed muzzle = uniform) — NOT motion (motion is fooled by head turns)
  3. prints each character's open windows

The agent reviews the montages + windows and confirms: right voice on the right
open mouth, no mover left silent, no voice over a closed mouth. Matt never tests.

Usage:
  qc_movie.py --scene "name:clip.mp4" --char "name:x1,y1,x2,y2" [--char ...] [--out DIR]
  (repeat --scene; --char applies to the most recent --scene)
"""
import argparse, sys
from pathlib import Path
import cv2, numpy as np, subprocess


def openness(clip, box):
    x1, y1, x2, y2 = box
    cap = cv2.VideoCapture(clip); fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    vals = []
    while True:
        ok, fr = cap.read()
        if not ok: break
        g = cv2.cvtColor(fr[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
        vals.append(float(g.std()))   # local contrast ~ mouth aperture
    cap.release()
    return np.array(vals), fps


def windows(sig, fps, frac=0.6, min_len=0.15, gap=0.2):
    if sig.size == 0: return []
    m = sig.max() or 1.0
    on = sig > frac * m
    runs = []; s = None
    for i, a in enumerate(on):
        if a and s is None: s = i
        if (not a) and s is not None: runs.append((s, i)); s = None
    if s is not None: runs.append((s, len(on)))
    out = []
    for s, e in runs:
        ts, te = s / fps, e / fps
        if out and ts - out[-1][1] <= gap: out[-1] = (out[-1][0], te)
        else: out.append((ts, te))
    return [(round(s, 2), round(e, 2)) for s, e in out if e - s >= min_len]


def montage(clip, box, out_png):
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", clip,
                    "-vf", f"crop={w}:{h}:{x1}:{y1},select='not(mod(n,12))',"
                           f"scale=150:{int(150*h/w)},tile=5x2",
                    "-frames:v", "1", "-vsync", "0", str(out_png)], check=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", action="append", default=[])
    ap.add_argument("--char", action="append", default=[])
    ap.add_argument("--out", default="/tmp/qc")
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    # group: chars listed after a scene belong to it (simple positional: all chars to all scenes here)
    scenes = [s.split(":", 1) for s in args.scene]
    chars = [(c.split(":")[0], [int(v) for v in c.split(":")[1].split(",")]) for c in args.char]

    for sname, clip in scenes:
        print(f"\n=== SCENE {sname} ({clip}) ===")
        for cname, box in chars:
            sig, fps = openness(clip, box)
            ivs = windows(sig, fps)
            png = out / f"{sname}_{cname}.png"
            montage(clip, box, png)
            print(f"  {cname}: open windows {ivs}  -> montage {png}")


if __name__ == "__main__":
    main()
