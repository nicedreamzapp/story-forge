#!/usr/bin/env python3
"""paintify.py — turn a real clip (or still) into an oil-painted twin with the SAME motion.

Why (The Heading, 2026-11-07): the film moves between painted, hybrid and real, and the trailer
flickers between them. Asking the image model for a painted twin gave a near copy (t3 window,
t2 bluff), and it can't draw a half-real/half-painted frame at all (LESSONS 11/07). Painting the
animated real clip frame by frame gives a twin whose motion matches exactly, so a cut, flicker,
wipe or dissolve between the two never jumps. Style splits are post work, not prompt work.

  ~/AI/ComfyUI/venv/bin/python pipeline-tools/paintify.py IN.mp4 OUT.mp4 [--style paint|toon] [--size 3] [--strength 1.0]
  (works on .png/.jpg too). Needs opencv-contrib (cv2.xphoto), which the ComfyUI venv has.
"""
import argparse
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

FFMPEG = "/opt/homebrew/bin/ffmpeg"


def paint(img: np.ndarray, size: int, strength: float, canvas: np.ndarray) -> np.ndarray:
    oil = cv2.xphoto.oilPainting(img, size, 1)
    sty = cv2.stylization(img, sigma_s=30, sigma_r=0.25)
    out = cv2.addWeighted(oil, 0.5, sty, 0.5, 0)
    out = cv2.GaussianBlur(out, (0, 0), 0.6)
    # warm, slightly muted palette + canvas weave, like the Qwen painted shots
    out = cv2.addWeighted(out, 0.92, np.full_like(out, (60, 85, 110)), 0.08, 0)
    out = np.clip(out.astype(np.float32) * canvas, 0, 255).astype(np.uint8)
    return cv2.addWeighted(out, strength, img, 1 - strength, 0)


def toon(img: np.ndarray, size: int, strength: float, canvas: np.ndarray) -> np.ndarray:
    """2D cartoon look (The Heading 11/07: Matt wanted the start to read as ANIMATED, not painted):
    flat colour regions + bold ink outlines. BRIGHT scenes only: on a dark night crowd it turns to
    mush (r4_signal, 11/07); for those ask the image model for a cartoon twin via refs instead."""
    flat = cv2.convertScaleAbs(img, alpha=1.15, beta=12)  # lift dark scenes so cels read
    for _ in range(5):
        flat = cv2.bilateralFilter(flat, 9, 75, 9)
    q = (flat // 48) * 48 + 24                      # posterize to flat cel colours
    hsv = cv2.cvtColor(q, cv2.COLOR_BGR2HSV)
    hsv[..., 1] = cv2.convertScaleAbs(hsv[..., 1], alpha=1.25)
    q = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    g = cv2.cvtColor(flat, cv2.COLOR_BGR2GRAY)
    e = cv2.Canny(g, 50, 130)
    e = cv2.dilate(e, np.ones((2, 2), np.uint8))
    edges = cv2.bitwise_not(e)
    out = cv2.bitwise_and(q, q, mask=edges)
    return cv2.addWeighted(out, strength, img, 1 - strength, 0)


def make_canvas(h: int, w: int) -> np.ndarray:
    rng = np.random.default_rng(7)  # seeded: same weave on every frame, no boil
    n = rng.normal(0, 1, (h // 2, w // 2)).astype(np.float32)
    n = cv2.resize(cv2.GaussianBlur(n, (3, 3), 0), (w, h))
    return (1.0 + 0.035 * n)[..., None]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--size", type=int, default=3)
    ap.add_argument("--strength", type=float, default=1.0)
    ap.add_argument("--style", choices=["paint", "toon"], default="paint")
    a = ap.parse_args()
    src, dst = Path(a.src), Path(a.dst)
    fx = toon if a.style == "toon" else paint
    if src.suffix.lower() in (".png", ".jpg", ".jpeg"):
        img = cv2.imread(str(src))
        cv2.imwrite(str(dst), fx(img, a.size, a.strength, make_canvas(*img.shape[:2])))
        return 0
    cap = cv2.VideoCapture(str(src))
    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    canvas = make_canvas(h, w)
    enc = subprocess.Popen([FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                            "-s", f"{w}x{h}", "-r", str(fps), "-i", "-", "-c:v", "libx264",
                            "-crf", "16", "-pix_fmt", "yuv420p", str(dst)], stdin=subprocess.PIPE)
    n = 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        enc.stdin.write(fx(fr, a.size, a.strength, canvas).tobytes())
        n += 1
    enc.stdin.close()
    enc.wait()
    print(f"paintify: {n} frames -> {dst}")
    return 0 if n and enc.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
