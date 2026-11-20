#!/usr/bin/env python3
"""Title slam for HANK & DOUG'S WILD RESCUE, PIL only (no ffmpeg drawtext). 3840x2160, 24 fps, 3.0 s, full 16:9.
Look: warm animated-feature title. Two lines in Rockwell Bold (slab serif = western adventure): "HANK & DOUG'S"
above, "WILD RESCUE" big below. Gold gradient face, bevel highlight on the top edge, a thick dark-red outline, a deep
brown drop shadow and a warm amber glow, on a deep warm vignette with slow drifting dust motes (real animated overlay,
float coordinates). Slam: lands from 1.22x with an ease-out-back overshoot in 9 frames + a warm flash, a light glint
sweeps across the letters (frames 22-44), then a smooth float-coordinate push 1.00 -> 1.03 (AFFINE + BICUBIC, never
whole-pixel steps, frozen rule 12); fades to black over the last 6 frames."""
import subprocess
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
P = Path(__file__).resolve().parent.parent
W, H, FPS, N = 3840, 2160, 24, 72
out = P / "final/title"; (out / "frames").mkdir(parents=True, exist_ok=True)
FONT = "/System/Library/Fonts/Supplemental/Rockwell.ttc"
def font(sz):
    for idx in (2,):   # Rockwell Bold (upright)
        try:
            f = ImageFont.truetype(FONT, sz, index=idx)
            if "Bold" in " ".join(f.getname()): return f
        except Exception: pass
    return ImageFont.truetype(FONT, sz)
f1, f2 = font(205), font(385)
print("font:", f1.getname(), f2.getname())

mask = Image.new("L", (W, H), 0); d = ImageDraw.Draw(mask)
y1, y2 = H * 0.355, H * 0.585
d.text((W / 2, y1), "HANK & DOUG'S", font=f1, fill=255, anchor="mm")
d.text((W / 2, y2), "WILD RESCUE", font=f2, fill=255, anchor="mm")
m = np.asarray(mask, np.float32) / 255
outline = np.asarray(mask.filter(ImageFilter.MaxFilter(31)), np.float32) / 255
shadow = np.asarray(mask.filter(ImageFilter.MaxFilter(31)).filter(ImageFilter.GaussianBlur(22)), np.float32) / 255
shadow = np.roll(np.roll(shadow, 26, 0), 14, 1)
glow = np.asarray(mask.filter(ImageFilter.GaussianBlur(70)), np.float32) / 255
# bevel: the mask's vertical gradient (top edges light, bottom edges dark)
bl = np.asarray(mask.filter(ImageFilter.GaussianBlur(7)), np.float32) / 255
gy = np.zeros_like(bl); gy[1:-1] = bl[2:] - bl[:-2]
yy = np.linspace(0, 1, H)[:, None]
# gold face: bright cream-gold at each line's top to deep orange-gold at the bottom
def band(c, h):
    return np.clip((yy - (c - h / 2) / H) / (h / H), 0, 1)
t = np.where(yy < (y1 + y2) / 2 / H, band(y1, 230), band(y2, 430))
top, bot = np.array([255, 236, 150], np.float32), np.array([232, 128, 22], np.float32)
face = top * (1 - t[..., None]) + bot * t[..., None]
face = face * (1 + 1.6 * np.clip(gy, 0, None)[..., None]) * (1 - 1.2 * np.clip(-gy, 0, None)[..., None])
red = np.array([118, 22, 12], np.float32)
layer_rgb = np.zeros((H, W, 3), np.float32); alpha = np.zeros((H, W), np.float32)
layer_rgb += red * outline[..., None]; alpha = np.maximum(alpha, outline)
layer_rgb = layer_rgb * (1 - m[..., None]) + face * m[..., None]
L = Image.fromarray(np.clip(layer_rgb, 0, 255).astype(np.uint8)); A = Image.fromarray((alpha * 255).astype(np.uint8))
S = Image.fromarray((np.clip(shadow, 0, 1) * 255).astype(np.uint8)); G = Image.fromarray((np.clip(glow, 0, 1) * 255).astype(np.uint8))
M = mask
# background: deep warm vignette (dark maroon-brown centre glow to near black)
xx = np.linspace(-1, 1, W)[None, :]; yv = np.linspace(-1, 1, H)[:, None]
r = np.sqrt((xx * 0.9) ** 2 + (yv * 1.2) ** 2)
bg = (np.clip(1 - r, 0, 1) ** 1.6)[..., None] * np.array([130, 52, 18], np.float32) + np.array([10, 5, 3], np.float32)
rng = np.random.default_rng(11)
motes = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(2, 7), rng.uniform(-14, 14), rng.uniform(-22, -6), rng.uniform(0.25, 0.8))
         for _ in range(140)]
def ease_back(x, s=1.9):
    x = x - 1; return x * x * ((s + 1) * x + s) + 1
def tf(img, sc, resample=Image.BICUBIC):
    a = 1 / sc; cx, cy = W / 2, H / 2
    return img.transform((W, H), Image.AFFINE, (a, 0, cx - a * cx, 0, a, cy - a * cy), resample=resample)
for f in range(N):
    if f < 9: sc = 1.22 - 0.22 * ease_back(f / 9)
    else: sc = 1.0 + 0.03 * (f - 9) / (N - 9)
    fr = bg.copy()
    # dust motes: soft discs drifting up in float coordinates
    dm = Image.new("L", (W, H), 0); dd = ImageDraw.Draw(dm)
    for x, y, rad, vx, vy, b in motes:
        px, py = (x + vx * f) % W, (y + vy * f) % H
        dd.ellipse((px - rad, py - rad, px + rad, py + rad), fill=int(255 * b))
    dmv = np.asarray(dm.filter(ImageFilter.GaussianBlur(3)), np.float32)[..., None] / 255
    fr += dmv * np.array([255, 190, 110], np.float32) * 0.5
    sh = np.asarray(tf(S, sc), np.float32)[..., None] / 255
    fr = fr * (1 - 0.85 * sh) + np.array([30, 10, 4], np.float32) * 0.85 * sh
    gl = np.asarray(tf(G, sc), np.float32)[..., None] / 255
    fr += gl * np.array([255, 140, 40], np.float32) * (0.55 + 0.6 * max(0.0, 1 - f / 14))
    a = np.asarray(tf(A, sc), np.float32)[..., None] / 255
    fr = fr * (1 - a) + np.asarray(tf(L, sc), np.float32) * a
    if 22 <= f <= 44:   # glint: a soft diagonal light band sweeping left to right across the gold face
        k = (f - 22) / 22
        cxg = -0.3 * W + k * 1.6 * W
        band_ = np.exp(-(((np.arange(W)[None, :] - cxg) + 0.45 * (np.arange(H)[:, None] - H / 2)) / 120.0) ** 2)
        mm = np.asarray(tf(M, sc), np.float32) / 255
        fr += (band_ * mm)[..., None] * np.array([255, 250, 225], np.float32) * 0.55
    flash = max(0.0, 1 - f / 5) ** 2
    fr = fr * (1 - 0.6 * flash) + np.array([255, 220, 160], np.float32) * 0.6 * flash
    if f >= N - 6: fr *= (N - 1 - f) / 6
    Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8)).save(out / f"frames/{f:03d}.png")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(out / "frames/%03d.png"),
                "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", str(out / "title_card.mp4")], check=True)
Image.open(out / "frames/030.png").resize((1280, 720)).save(out / "title_preview.png")
print(out / "title_card.mp4")
