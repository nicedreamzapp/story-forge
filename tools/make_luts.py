#!/usr/bin/env python3
"""Generate 33-point .cube 3D LUTs (numpy only) into story-forge/luts/. Our own math, no downloads."""
import numpy as np
from pathlib import Path
N = 33
OUT = Path(__file__).resolve().parent.parent / "luts"
LUMA = np.array([0.2126, 0.7152, 0.0722])

def lum(c): return (c * LUMA).sum(-1, keepdims=True)
def sat(c, s): l = lum(c); return l + (c - l) * s
def scurve(x, k):  # smoothstep-blend contrast around 0.5
    s = x * x * (3 - 2 * x); return x + (s - x) * k
def lift_gamma_gain(c, lift=0.0, gamma=1.0, gain=1.0):
    return np.clip(c * gain + lift, 0, 1) ** (1 / gamma)
def split_tone(c, shadow, high, amt=1.0):
    l = np.clip(lum(c), 0, 1)
    w_s, w_h = (1 - l) ** 2, l ** 2
    return c + amt * (w_s * np.array(shadow) + w_h * np.array(high))
def rolloff(x, knee=0.8):
    over = np.clip(x - knee, 0, None); r = 1 - knee
    return np.where(x > knee, knee + r * np.tanh(over / r), x)

def teal_orange_blockbuster(c):
    c = scurve(c, 0.6); c = split_tone(c, (-0.05, 0.02, 0.06), (0.07, 0.02, -0.07), 1.0)
    return sat(c, 1.1)
def bleach_bypass(c):
    l = lum(c); c = sat(c, 0.45); c = c * 0.5 + (l * 0.5 + scurve(c, 1.0) * 0.5) * 0.5 + 0 * c
    return scurve(c, 0.8) * 1.04 - 0.02
def cold_space_teal(c):
    c = sat(c, 0.8); c = c * np.array([0.9, 1.0, 1.1])
    c = split_tone(c, (-0.04, 0.0, 0.05), (-0.02, 0.03, 0.05), 1.0)
    return lift_gamma_gain(scurve(c, 0.4), lift=0.01, gamma=0.95)
def warm_alien_haze(c):
    c = c * np.array([1.08, 0.97, 0.88]); c = split_tone(c, (0.03, 0.0, 0.02), (0.06, 0.03, -0.04), 1.0)
    c = c * 0.88 + 0.07   # lifted milky blacks, hazy
    return sat(c, 1.05)
def kodak_2383_style(c):
    # print-film-like: toe, strong mid contrast, shoulder rolloff, warm highlights, slightly teal shadows
    c = np.clip(c, 0, 1); c = scurve(c, 1.0) ** 1.05
    c = c * 0.94 + 0.02
    c = rolloff(c, 0.82)
    c = split_tone(c, (-0.01, 0.005, 0.015), (0.025, 0.012, -0.02), 1.0)
    return sat(c, 0.95)
def neutral_filmic(c):
    c = scurve(np.clip(c, 0, 1), 0.45); c = rolloff(c, 0.78)
    return c * 0.97 + 0.01

LUTS = dict(teal_orange_blockbuster=teal_orange_blockbuster, bleach_bypass=bleach_bypass,
            cold_space_teal=cold_space_teal, warm_alien_haze=warm_alien_haze,
            kodak_2383_style=kodak_2383_style, neutral_filmic=neutral_filmic)

def write(name, fn):
    g = np.linspace(0, 1, N)
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")   # .cube: red varies fastest
    rgb = np.stack([r, gg, b], -1).reshape(-1, 3)
    out = np.clip(fn(rgb), 0, 1)
    with open(OUT / f"{name}.cube", "w") as f:
        f.write(f'TITLE "{name}"\nLUT_3D_SIZE {N}\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n')
        for v in out: f.write(f"{v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for n, fn in LUTS.items(): write(n, fn); print("wrote", OUT / f"{n}.cube")
