#!/usr/bin/env python3
"""ken_burns.py — JITTER-FREE camera move on a still (sub-pixel, baked-in standard).

WHY THIS EXISTS (frozen rule, 2026-05-27, Matt): ffmpeg `zoompan` moves the crop
window in WHOLE-PIXEL steps, so a slow push/pan on a still VIBRATES / SHAKES.
That fake shake is BANNED. This renderer samples the source at FLOAT coordinates
with BICUBIC resampling via PIL AFFINE, so motion is perfectly smooth at any speed.
Never fake animation by shaking/jittering a still again.

Usage:
  ken_burns.py SRC OUT --dur 4.5 --mode pushin [--fps 24] [--zoom 0.12]
Modes: pushin | pushslow | pullback | panL | panR | static
"""
import argparse, subprocess, tempfile
from pathlib import Path
from PIL import Image

OUT_W, OUT_H = 1280, 720

def smoothstep(t):  # ease in/out
    return t * t * (3 - 2 * t)

def cover_base(src):
    im = Image.open(src).convert("RGB")
    w, h = im.size
    # center-crop to 16:9
    target = OUT_W / OUT_H
    if w / h > target:
        nw = int(h * target); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w / target); im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    # ensure plenty of headroom for sub-pixel sharp zoom
    if im.size[0] < 2560:
        im = im.resize((2560, 1440), Image.LANCZOS)
    return im

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("out")
    ap.add_argument("--dur", type=float, required=True)
    ap.add_argument("--mode", default="pushin")
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--zoom", type=float, default=None, help="zoom delta (default per mode)")
    a = ap.parse_args()

    base = cover_base(a.src)
    bw, bh = base.size
    N = max(2, int(round(a.dur * a.fps)))
    dz = a.zoom if a.zoom is not None else {
        "pushin": 0.12, "pushslow": 0.07, "pullback": 0.12,
        "panL": 0.0, "panR": 0.0, "static": 0.0,
    }.get(a.mode, 0.10)
    # constant zoom level used during pans (gives slack to move)
    pan_z = 1.10

    tmp = Path(tempfile.mkdtemp(prefix="kb_"))
    for i in range(N):
        s = smoothstep(i / (N - 1)) if N > 1 else 0.0
        if a.mode == "pushin":   z = 1.0 + dz * s
        elif a.mode == "pushslow": z = 1.0 + dz * s
        elif a.mode == "pullback": z = (1.0 + dz) - dz * s
        else: z = pan_z if a.mode in ("panL", "panR") else 1.0
        cw, ch = bw / z, bh / z
        cx, cy = bw / 2.0, bh / 2.0
        if a.mode in ("panL", "panR"):
            slack = (bw - cw) / 2.0
            cx = (bw / 2.0 - slack) + (2 * slack) * (s if a.mode == "panR" else (1 - s))
        # clamp window inside base
        cx = min(max(cx, cw / 2), bw - cw / 2)
        cy = min(max(cy, ch / 2), bh - ch / 2)
        coef = (cw / OUT_W, 0.0, cx - cw / 2.0, 0.0, ch / OUT_H, cy - ch / 2.0)
        frame = base.transform((OUT_W, OUT_H), Image.AFFINE, coef, resample=Image.BICUBIC)
        frame.save(tmp / f"{i:05d}.png")

    subprocess.run([
        "/opt/homebrew/bin/ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-framerate", str(a.fps), "-i", str(tmp / "%05d.png"),
        "-frames:v", str(N), "-c:v", "libx264", "-preset", "medium", "-crf", "17",
        "-pix_fmt", "yuv420p", "-an", a.out,
    ], check=True)
    for p in tmp.glob("*.png"): p.unlink()
    tmp.rmdir()
    print(f"[ken_burns] {a.mode} {a.dur}s -> {a.out}")

if __name__ == "__main__":
    main()
