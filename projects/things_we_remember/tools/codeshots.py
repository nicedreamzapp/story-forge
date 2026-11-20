#!/usr/bin/env python3
"""Code-built physical gags (LTX failed both; memory: one re-roll max, then still + code).
s06: the fork at the empty place is cut to its own layer (table inpainted under it) and slides ~4 cm toward the
     empty chair, turning slightly, under a slow push. No hands in frame (crop starts at 1.35x).
s05: the glass is cut from the hand and falls under gravity (~0.4 s to the floor, off the bottom of frame); the figure in
     the doorway has two states (head forward / head turned down toward the floor spot), cross-blended over 6 frames,
     the turn finishing 8 frames BEFORE the glass lands; then a shards insert, then a held, silent master."""
import cv2, numpy as np, subprocess
from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw
P = Path(__file__).resolve().parent.parent; S = P / "stills"; FPS = 24; W, H = 1920, 1080
def ease(k): k = min(1, max(0, k)); return k * k * (3 - 2 * k)
def poly_mask(shape, pts, feather=2):
    m = Image.new("L", (shape[1], shape[0]), 0); ImageDraw.Draw(m).polygon(pts, fill=255)
    return np.asarray(m.filter(ImageFilter.GaussianBlur(feather))).astype(np.float32) / 255
def view(img, cx, cy, z):
    h, w = img.shape[:2]; cw, ch = w / z, h / z
    x0 = min(max(0, cx * w - cw / 2), w - cw); y0 = min(max(0, cy * h - ch / 2), h - ch)
    return np.asarray(Image.fromarray(img).resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch)))
def write(frames, out):
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    for f in frames: ff.stdin.write(np.ascontiguousarray(f).tobytes())
    ff.stdin.close(); ff.wait(); print("wrote", out.name, len(frames))
def layer_over(base, layer, alpha, dx, dy, ang, pivot):
    M = cv2.getRotationMatrix2D(pivot, ang, 1.0); M[0, 2] += dx; M[1, 2] += dy
    h, w = base.shape[:2]
    L = cv2.warpAffine(layer, M, (w, h), flags=cv2.INTER_LINEAR); A = cv2.warpAffine(alpha, M, (w, h), flags=cv2.INTER_LINEAR)[..., None]
    return (base * (1 - A) + L * A).astype(np.uint8)

# ---------------- s06 fork ----------------
im = np.asarray(Image.open(S / "s06_a.png").convert("RGB"))
FORK = [(774, 436), (801, 431), (862, 461), (900, 460), (965, 463), (1049, 476), (1049, 491), (962, 480), (902, 478), (872, 491), (850, 486), (790, 456), (770, 446)]
a = poly_mask(im.shape, FORK, 1.5)
hole = (poly_mask(im.shape, FORK, 0) > .05).astype(np.uint8) * 255; hole = cv2.dilate(hole, np.ones((7, 7), np.uint8))
plate = cv2.inpaint(im, hole, 9, cv2.INPAINT_TELEA)
plate = cv2.GaussianBlur(plate, (0, 0), 1.2) * (hole[..., None] / 255) + plate * (1 - hole[..., None] / 255)
plate = plate.astype(np.uint8)
n = int(3.5 * FPS); fr = []
for i in range(n):
    t = i / FPS; k = ease((t - 1.0) / 1.6)                 # slide 1.0 -> 2.6 s, then hold
    k = k ** 1.4                                            # slow start, as if pulled
    f = layer_over(plate, im, a, -6 * k, 26 * k, 7 * k, (910.0, 470.0))
    z = 1.35 + .22 * ease(i / (n - 1))
    fr.append(view(f, .52, .56, z))
write(fr, P / "clips/s06_code.mp4")

# ---------------- s05 glass + the figure ----------------
im = np.asarray(Image.open(S / "s05_a.png").convert("RGB")).astype(np.uint8)
GLASS = [(400, 462), (486, 486), (453, 613), (374, 601), (371, 584)]
g = poly_mask(im.shape, GLASS, 1.0)
hsv = cv2.cvtColor(im, cv2.COLOR_RGB2HSV).astype(int); r, gg, b = im[..., 0].astype(int), im[..., 1].astype(int), im[..., 2].astype(int)
skin = ((r - b > 28) & (r > 90) & (hsv[..., 1] > 50)).astype(np.float32)
# the hand holds the glass from BEHIND (fingers seen through it), so the whole glass is the falling layer
ghole = (g > .05).astype(np.uint8) * 255; ghole = cv2.dilate(ghole, np.ones((5, 5), np.uint8))
nog = cv2.inpaint(im, ghole, 7, cv2.INPAINT_TELEA)
nog = (nog * (1 - ghole[..., None] / 255 * .35) + cv2.GaussianBlur(nog, (0, 0), 5) * (ghole[..., None] / 255 * .35) * .8).astype(np.uint8)
# figure: soften + dim, then a turned-head state
fig_box = (740, 200, 960, 720)
def soften(x):
    out = x.copy(); x0, y0, x1, y1 = fig_box; reg = out[y0:y1, x0:x1]
    out[y0:y1, x0:x1] = (cv2.GaussianBlur(reg, (0, 0), 2.0) * .85).astype(np.uint8); return out
HEAD = [(820, 218), (875, 218), (878, 262), (868, 292), (832, 292), (818, 262)]
ha = poly_mask(im.shape, HEAD, 2.0)
hhole = (poly_mask(im.shape, HEAD, 0) > .05).astype(np.uint8) * 255; hhole = cv2.dilate(hhole, np.ones((9, 9), np.uint8))
def turned(base):
    bg = cv2.inpaint(base, hhole, 11, cv2.INPAINT_TELEA)
    bg = (bg * (1 - hhole[..., None] / 255) + cv2.GaussianBlur(bg, (0, 0), 4) * (hhole[..., None] / 255)).astype(np.uint8)
    return layer_over(bg, base, ha, -5, 7, 24, (850.0, 292.0))   # head tips down toward the floor spot (screen left, below)
A_fwd = soften(nog); A_turn = soften(turned(nog))
A_fwd_glass = soften(im); A_turn_glass = soften(turned(im))
shards = np.asarray(Image.open(S / "s05_shards.png").convert("RGB"))
n = int(4.0 * FPS); fr = []
T_TURN0 = 24; T_TURN1 = 30          # head turn frames 24-30 (6 frames)
T_DROP = 29; T_LAND = 38            # glass slips at frame 29, lands (off frame) at 38 = 8 frames after the turn ends
T_BACK = 50                          # shards insert 38-50 (0.5 s)
for i in range(n):
    if T_LAND <= i < T_BACK:
        k = (i - T_LAND) / (T_BACK - T_LAND); sh = np.random.default_rng(i).normal(0, 6 * (1 - k), 2)
        f = view(shards, .74 + sh[0] / 1344, .72 + sh[1] / 768, 2.1 + .08 * k); fr.append(f); continue   # shards only, away from the intact glass in the still
    w = ease((i - T_TURN0) / (T_TURN1 - T_TURN0))
    if i < T_DROP:
        base = (A_fwd_glass * (1 - w) + A_turn_glass * w).astype(np.uint8)
    else:
        base = (A_fwd * (1 - w) + A_turn * w).astype(np.uint8)
        dt = (i - T_DROP) / FPS; y = .5 * 2600 * dt * dt * 3.2          # ~330 px in 0.33 s, gone off frame before 0.4 s
        sub = []
        for s in np.linspace(-.5, .5, 5):                                 # motion blur, 5 sub-steps
            dts = max(0, dt + s / FPS); ys = .5 * 2600 * dts * dts * 3.2
            sub.append(layer_over(base, im, g, -8 * dts * 10, ys, -40 * dts, (428.0, 540.0)).astype(np.float32))
        base = np.mean(sub, 0).astype(np.uint8)
    z = 1.0 + .05 * ease(i / (n - 1))
    fr.append(view(base, .52, .5, z))
write(fr, P / "clips/s05_code.mp4")
