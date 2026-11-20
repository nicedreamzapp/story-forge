#!/usr/bin/env python3
"""Frame-grid sheets for the agent's look (rule 26): one PNG per render, a row per take (hq takes, then the previs
draft), 6 frames evenly over the clip, labelled. Writes REVIEW_grids/<render>.png (review folder, deleted after 04)."""
import json, subprocess, glob
from pathlib import Path
from PIL import Image, ImageDraw
P = Path(__file__).resolve().parent.parent; O = P / "REVIEW_grids"
renders = [r["id"] for r in json.load(open(P / "renders.json"))["renders"]]
TW, TH, N = 300, 168, 6
def dur(f): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]))
for rid in renders:
    files = sorted(glob.glob(str(P / f"clips/takes/{rid}_t*.mp4"))) + sorted(glob.glob(str(P / f"clips/previs/{rid}_t1.mp4")))
    sheet = Image.new("RGB", (TW * N, (TH + 18) * len(files)), (20, 20, 20)); d = ImageDraw.Draw(sheet)
    for row, f in enumerate(files):
        D = dur(f); y = row * (TH + 18)
        d.text((4, y + 2), ("PREVIS " if "previs" in f else "HQ ") + Path(f).stem + f"  {D:.2f}s", fill=(255, 255, 0))
        for k in range(N):
            t = D * (0.04 + 0.92 * k / (N - 1))
            raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", f, "-frames:v", "1", "-vf", f"scale={TW}:{TH}",
                                  "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
            if len(raw) == TW * TH * 3: sheet.paste(Image.frombytes("RGB", (TW, TH), raw), (k * TW, y + 18))
    sheet.save(O / f"{rid}.png")
print("done")
