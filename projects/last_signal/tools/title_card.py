#!/usr/bin/env python3
"""Title slam card for THE LAST SIGNAL, PIL (ffmpeg has no drawtext). 3840x2160, 24 fps, 3.0 s, text inside the
2.39:1 scope area. Slam: white flash decaying over 5 frames, the title lands from 1.07x to 1.0 in 6 frames, an
anamorphic teal streak decays over 20 frames, then a smooth float-coordinate push 1.00 -> 1.025 (AFFINE + BICUBIC,
no whole-pixel steps, frozen rule 12), fade to black over the last 8 frames."""
import subprocess
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
P = Path(__file__).resolve().parent.parent
W, H, FPS, N = 3840, 2160, 24, 72
out = P / "final/title"; (out / "frames").mkdir(parents=True, exist_ok=True)
font = ImageFont.truetype("/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf", 400)
text = "THE LAST SIGNAL"
track = 70
widths = [font.getlength(ch) for ch in text]
total = sum(widths) + track * (len(text) - 1)
txt = Image.new("L", (W, H), 0); d = ImageDraw.Draw(txt)
x = (W - total) / 2; y = H / 2
for ch, w in zip(text, widths):
    d.text((x, y), ch, font=font, fill=255, anchor="lm"); x += w + track
# metallic: vertical gradient warm white -> steel, plus glow
grad = np.linspace(1.0, 0.62, H)[:, None] * np.ones((1, W))
t = np.asarray(txt, np.float32) / 255
base = np.stack([t * grad * 245, t * grad * 238, t * grad * 228], -1)
glow = np.asarray(txt.filter(ImageFilter.GaussianBlur(40)), np.float32) / 255
glow2 = np.asarray(txt.filter(ImageFilter.GaussianBlur(140)), np.float32) / 255
teal = np.array([40, 190, 210], np.float32)
layer = base + glow[..., None] * teal * 0.55 + glow2[..., None] * teal * 0.35
# background: near-black with a faint warm haze low in frame
yy = np.linspace(0, 1, H)[:, None, None]
bg = np.ones((H, W, 3), np.float32) * np.array([6, 7, 9], np.float32) + (yy ** 3) * np.array([38, 18, 6], np.float32)
streak_row = np.exp(-((np.arange(H) - H / 2) / 9.0) ** 2)[:, None]
streak_col = np.exp(-((np.arange(W) - W / 2) / (W * 0.33)) ** 2)[None, :]
streak = (streak_row * streak_col)[..., None] * np.array([120, 230, 255], np.float32)
L = Image.fromarray(np.clip(layer, 0, 255).astype(np.uint8))
for f in range(N):
    s = 1.07 - 0.07 * min(1, f / 6) ** 0.5 if f < 6 else 1.0 + 0.025 * (f - 6) / (N - 6)
    a = 1 / s; cx, cy = W / 2, H / 2
    T = L.transform((W, H), Image.AFFINE, (a, 0, cx - a * cx, 0, a, cy - a * cy), resample=Image.BICUBIC)
    fr = bg + np.asarray(T, np.float32)
    k = max(0.0, 1 - f / 20) ** 2
    fr += streak * k * 1.4
    flash = max(0.0, 1 - f / 5) ** 1.5
    fr = fr * (1 - flash) + 255 * flash
    if f >= N - 8: fr *= (N - 1 - f) / 8
    Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8)).save(out / f"frames/{f:03d}.png")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(out / "frames/%03d.png"),
                "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", str(out / "title_card.mp4")], check=True)
print(out / "title_card.mp4")
