#!/usr/bin/env python3
"""particles.py — animated overlay layer (gold pollen, floral petals, light blooms,
logo shimmer/sparkle). Rendered on BLACK for screen-blend compositing. Real motion
graphics — NOT a shaken still."""
import numpy as np, subprocess, tempfile, math, random
from pathlib import Path
from PIL import Image

W, H, FPS, DUR = 1280, 720, 24, 32.0
N = int(DUR * FPS)
OUT = Path("/Users/dtribe/Desktop/PROJECTS/story-forge/projects/royal_gold/overlay/particles.mov")
OUT.parent.mkdir(parents=True, exist_ok=True)
random.seed(7); np.random.seed(7)
# card animation windows (intro / outro) — extra sparkle + shimmer here
CARDS = [(0.0, 3.0), (28.0, 32.0)]

def radial(size, power=2.2):
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    c = (size - 1) / 2.0
    r = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / c
    g = np.clip(1 - r, 0, 1) ** power
    return g

MOTE = {s: radial(s, 2.4) for s in (12, 18, 26, 36)}
BLOOM = radial(560, 1.6)
def petal_sprite(size=46):
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    cx, cy = (size-1)/2, (size-1)/2
    a, b = size*0.5, size*0.28
    d = ((xx-cx)/a)**2 + ((yy-cy)/b)**2
    return np.clip(1-d, 0, 1) ** 1.3
PETAL = petal_sprite(46)

def add(frame, sprite, cx, cy, color, gain):
    sh, sw = sprite.shape
    x0, y0 = int(cx - sw/2), int(cy - sh/2)
    x1, y1 = x0+sw, y0+sh
    fx0, fy0 = max(0, x0), max(0, y0); fx1, fy1 = min(W, x1), min(H, y1)
    if fx0 >= fx1 or fy0 >= fy1: return
    sx0, sy0 = fx0-x0, fy0-y0
    sub = sprite[sy0:sy0+(fy1-fy0), sx0:sx0+(fx1-fx0)] * gain
    for c in range(3):
        frame[fy0:fy1, fx0:fx1, c] += sub * color[c]

# ---- particle systems ----
GOLD = (255, 214, 138); WARM = (255, 190, 110)
PETAL_COLS = [(255, 226, 180), (255, 200, 170), (255, 232, 150)]
motes = [dict(x=random.uniform(0,W), y=random.uniform(0,H),
             s=random.choice([12,18,26,36]),
             vy=random.uniform(8,26), sway=random.uniform(6,22),
             ph=random.uniform(0,6.28), tw=random.uniform(0.6,1.4),
             b=random.uniform(0.30,0.85), col=GOLD) for _ in range(58)]
petals = [dict(x=random.uniform(0,W), y=random.uniform(-H,H),
              vy=random.uniform(18,40), sway=random.uniform(20,55),
              ph=random.uniform(0,6.28), rot=random.uniform(0,360),
              vr=random.uniform(-40,40), b=random.uniform(0.18,0.40),
              col=random.choice(PETAL_COLS)) for _ in range(11)]
blooms = [dict(x=random.uniform(200,1080), y=random.uniform(150,560),
              vx=random.uniform(-10,10), vy=random.uniform(-6,6),
              ph=random.uniform(0,6.28), b=random.uniform(0.10,0.20)) for _ in range(3)]

def in_card(t):
    for a,b in CARDS:
        if a <= t <= b: return (t-a)/(b-a)
    return None

tmp = Path(tempfile.mkdtemp(prefix="parts_"))
for i in range(N):
    t = i / FPS
    fr = np.zeros((H, W, 3), np.float32)
    # light blooms (drifting, gentle pulse)
    for bl in blooms:
        bx = bl['x'] + bl['vx']*t; by = bl['y'] + bl['vy']*t
        pulse = 0.7 + 0.3*math.sin(t*0.7 + bl['ph'])
        add(fr, BLOOM, bx % W, by % H, WARM, bl['b']*pulse)
    # gold motes drifting up with sway + twinkle
    for m in motes:
        y = (m['y'] - m['vy']*t) % (H+80) - 40
        x = (m['x'] + m['sway']*math.sin(t*0.5 + m['ph'])) % W
        tw = 0.6 + 0.4*math.sin(t*m['tw']*2 + m['ph'])
        add(fr, MOTE[m['s']], x, y, m['col'], m['b']*tw)
    # floral petals falling with rotation
    for p in petals:
        y = (p['y'] + p['vy']*t) % (H+90) - 45
        x = (p['x'] + p['sway']*math.sin(t*0.45 + p['ph'])) % W
        ang = p['rot'] + p['vr']*t
        spr = np.asarray(Image.fromarray((PETAL*255).astype(np.uint8)).rotate(ang, expand=True), np.float32)/255.0
        add(fr, spr, x, y, p['col'], p['b'])
    # card shimmer + sparkle burst (intro/outro only)
    cp = in_card(t)
    if cp is not None:
        # diagonal shimmer bar sweeping across the medallion (center band)
        sweep = -200 + 1700*cp
        bar = np.zeros((H, W), np.float32)
        xs = np.arange(W)
        band = np.exp(-((xs - sweep)/90.0)**2)
        bar[:] = band[None, :]
        diag = np.clip(1 - np.abs((np.arange(H)[:,None]-H/2))/ (H*0.7), 0, 1)
        bar *= diag
        for c in range(3):
            fr[:,:,c] += bar * GOLD[c] * 0.30
        # rising sparkles from the crest center
        ns = 18
        for k in range(ns):
            sp = (cp*1.4 + k*0.07) % 1.0
            sx = W/2 + math.sin(k*2.1)* (60 + 120*sp)
            sy = H/2 - sp*240 + 20
            tw = max(0, math.sin(sp*math.pi))
            add(fr, MOTE[12], sx, sy, GOLD, 0.9*tw)
    rgb = np.clip(fr, 0, 255).astype(np.uint8)
    alpha = np.clip(fr.max(axis=2), 0, 255).astype(np.uint8)  # bright->opaque, black->transparent
    rgba = np.dstack([rgb, alpha])
    Image.fromarray(rgba, "RGBA").save(tmp/f"{i:05d}.png")

# ProRes 4444 carries the alpha channel cleanly for overlay compositing
subprocess.run(["/opt/homebrew/bin/ffmpeg","-y","-hide_banner","-loglevel","error",
    "-framerate",str(FPS),"-i",str(tmp/"%05d.png"),"-frames:v",str(N),
    "-c:v","prores_ks","-profile:v","4444","-pix_fmt","yuva444p10le",str(OUT)],check=True)
for p in tmp.glob("*.png"): p.unlink()
tmp.rmdir()
print("overlay ->", OUT)
