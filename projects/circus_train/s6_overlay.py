#!/usr/bin/env python3
"""s6_interior via real motion graphics — the bang is FELT (2026-07-31).

Five Wan i2v attempts across two locked stills all failed the same way: a static
dark interior with one light source is a shot class Wan cannot hold (the light
brightens/opens, hallucinates a person, or fades and fragments). Rule 18: the
remedy is a re-conceived shot. Rule 12 blesses REAL animated overlays (see
projects/royal_gold/particles.py) — actual motion graphics, never a shaken still.

The shot (3s @ 24fps on the gate-passed LOCKED_s6_interior.png):
  0.0-1.2s  quiet hold — dust motes sink slowly through the blade of light
  1.2s      THE BANG — Hank hits the door outside: a decaying sub-pixel frame
            shudder (PIL AFFINE float sampling, ken_burns-style — smooth, never
            zoompan jitter) + a burst of dust knocked loose rains down the beam
            + the seam flares briefly
  1.5-3.0s  the dust settles back to a gentle drift

Output: clips/s6_interior_overlay.mp4 — judged by beat_gate, then Matt's click.
"""
import math
import random
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

PROJ = Path(__file__).resolve().parent
STILL = PROJ / "stills" / "LOCKED_s6_interior.png"
OUT = PROJ / "clips" / "s6_interior_overlay.mp4"
FPS, DUR = 24, 3.0
N = int(FPS * DUR)
BANG_F = int(1.2 * FPS)          # the hit lands here
random.seed(82)                   # the seed that won the still
np.random.seed(82)

base = np.asarray(Image.open(STILL).convert("RGB"), dtype=np.float32)
H, W = base.shape[:2]

# The beam corridor in the locked still: seam top → lit straw at the floor.
TOP = (268.0, 100.0)
BOT = (255.0, 445.0)
W_TOP, W_BOT = 16.0, 170.0

def beam_pos(t: float, lat: float) -> tuple[float, float]:
    """t 0..1 down the beam, lat -1..1 across it."""
    x = TOP[0] + (BOT[0] - TOP[0]) * t + lat * (W_TOP + (W_BOT - W_TOP) * t) / 2
    y = TOP[1] + (BOT[1] - TOP[1]) * t
    return x, y

def radial(size: int, power: float = 2.4) -> np.ndarray:
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    c = (size - 1) / 2.0
    r = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / c
    return np.clip(1 - r, 0, 1) ** power

MOTE = {s: radial(s) for s in (2, 3, 4, 5)}
WARM = (255, 224, 160)

def add_sprite(frame, sprite, cx, cy, gain):
    sh, sw = sprite.shape
    x0, y0 = int(cx - sw / 2), int(cy - sh / 2)
    fx0, fy0 = max(0, x0), max(0, y0)
    fx1, fy1 = min(W, x0 + sw), min(H, y0 + sh)
    if fx0 >= fx1 or fy0 >= fy1:
        return
    sub = sprite[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0] * gain
    for c in range(3):
        frame[fy0:fy1, fx0:fx1, c] += sub * WARM[c]

# ambient motes living in the beam the whole shot
motes = [dict(t=random.random(), lat=random.uniform(-0.9, 0.9),
              vt=random.uniform(0.028, 0.055),          # slow sink, fraction/s
              sway=random.uniform(0.02, 0.07), ph=random.uniform(0, 6.28),
              s=random.choice([2, 3, 4, 5]), b=random.uniform(0.05, 0.16))
         for _ in range(55)]
# dust knocked loose by the bang — spawns at the top, falls fast, fades
burst = [dict(t=random.uniform(0.0, 0.18), lat=random.uniform(-0.95, 0.95),
              vt=random.uniform(0.16, 0.34), sway=random.uniform(0.03, 0.10),
              ph=random.uniform(0, 6.28), s=random.choice([2, 3, 3, 4]),
              b=random.uniform(0.10, 0.30))
         for _ in range(40)]

tmp = Path(tempfile.mkdtemp())
for f in range(N):
    tsec = f / FPS
    frame = base.copy()

    # the seam flares for a few frames as the blow lands
    if 0 <= f - BANG_F < 5:
        flare = 1.0 + 0.10 * math.exp(-(f - BANG_F) / 2.0)
        frame *= 1.0  # base untouched; flare applies to sprites below
    else:
        flare = 1.0

    for m in motes:
        t = (m["t"] + m["vt"] * tsec) % 1.0
        lat = m["lat"] + m["sway"] * math.sin(2.1 * tsec + m["ph"])
        x, y = beam_pos(t, lat)
        tw = 0.75 + 0.25 * math.sin(3.0 * tsec + m["ph"] * 2)
        add_sprite(frame, MOTE[m["s"]], x, y, m["b"] * tw * flare * 255)

    if f >= BANG_F:
        dt = tsec - BANG_F / FPS
        for m in burst:
            t = m["t"] + m["vt"] * dt
            if t > 1.0:
                continue
            lat = m["lat"] + m["sway"] * math.sin(5.0 * dt + m["ph"])
            x, y = beam_pos(t, lat)
            fade = max(0.0, 1.0 - dt / 1.6)
            add_sprite(frame, MOTE[m["s"]], x, y, m["b"] * fade * flare * 255)

    img = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8))

    # THE SHUDDER — 6 frames of decaying sub-pixel offset, float-coord AFFINE
    # (BICUBIC), the ken_burns method rule 12 requires. Never whole-pixel steps.
    k = f - BANG_F
    if 0 <= k < 6:
        amp = 3.2 * math.exp(-k / 1.8)
        dx = amp * math.sin(k * 2.4)
        dy = 0.6 * amp * math.cos(k * 1.9)
        img = img.transform((W, H), Image.AFFINE, (1, 0, dx, 0, 1, dy),
                            resample=Image.BICUBIC, fillcolor=(4, 3, 2))

    img.save(tmp / f"f{f:04d}.png")

OUT.parent.mkdir(exist_ok=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS),
                "-i", str(tmp / "f%04d.png"),
                "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                str(OUT)], check=True)
print(f"wrote {OUT} ({N} frames @ {FPS}fps)")
