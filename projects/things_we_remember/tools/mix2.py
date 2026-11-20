#!/usr/bin/env python3
"""Cue-driven mix (teaser's mix.py stays its own): score + foley cues + voice lines -> TWR_MIX (48k stereo).
sfx cues: {f, t, dur, g, fade, off, proc: rev|tape|lp|hp|slow}; lines from timeline "lines" (voice/trimmed/<id>.wav).
Static gains; final level is set by final_audio_gate."""
import json, os, numpy as np, soundfile as sf
from pathlib import Path
from scipy.signal import resample_poly, fftconvolve, butter, sosfilt
P = Path(__file__).resolve().parent.parent; SR = 48000
TL = json.load(open(P / os.environ["TWR_TL"])); N = int(TL["end"] * SR); rng = np.random.default_rng(5)
def load(p):
    y, r = sf.read(str(p)); y = y.mean(1) if y.ndim > 1 else y
    if r != SR: y = resample_poly(y, SR, r)
    return y
mix = np.zeros(N); duck = np.ones(N)
def add(y, t, g, fade=.02):
    i = int(t * SR); j = min(N, i + len(y))
    if i >= N or j <= i: return
    y = y[: j - i].copy(); f = int(fade * SR)
    if len(y) > 2 * f and f > 0: y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    mix[i:j] += g * y
def verb(y, sec, wet):
    ir = rng.standard_normal(int(sec * SR)) * np.exp(-np.arange(int(sec * SR)) / SR * 4); ir /= np.sqrt((ir ** 2).sum()) * 1.4
    w = fftconvolve(y, ir); return (1 - wet) * np.pad(y, (0, len(w) - len(y))) + wet * w
def lp(y, hz): return sosfilt(butter(4, hz, "low", fs=SR, output="sos"), y)
def hp(y, hz): return sosfilt(butter(2, hz, "high", fs=SR, output="sos"), y)
def tape(y):   # old cassette / camcorder: band-limited, wow, a little hiss
    y = hp(lp(y, 3800), 250); n = np.arange(len(y)); idx = n + 40 * np.sin(2 * np.pi * .7 * n / SR)
    y = np.interp(idx, n, y); return y + rng.normal(0, .004, len(y))
fx = P / "audio/sfx"
for c in TL.get("sfx", []):
    y = load(fx / f"{c['f']}.wav")
    for pr in c.get("proc", "").split("|"):
        if pr == "rev": y = y[::-1]
        elif pr == "slow": y = resample_poly(y, 5, 4)
        elif pr == "lp": y = lp(y, 2500)
        elif pr == "hp": y = hp(y, 300)
        elif pr == "tape": y = tape(y)
    o = int(c.get("off", 0) * SR); y = y[o:]
    if "dur" in c:
        need = int(c["dur"] * SR)
        while len(y) < need: y = np.concatenate([y, y])
        y = y[:need]
    add(y, c["t"], c.get("g", .3), c.get("fade", .02))
V = {"claire": (1.0, .10), "ruth": (1.0, .12), "lily": (1.0, .06), "daniel": (1.1, .45), "rememberer": (1.2, .18), "tom": (1.0, .10), "lily3": (1.0, .03)}
for lid, L in TL["lines"].items():
    y = load(P / "voice/trimmed" / f"{L.get('wav', lid)}.wav"); g, wet = V[L["spk"]]
    if L["spk"] == "rememberer": y = lp(y, 7000)
    if L.get("tape"): y = tape(y)
    y = verb(y, 1.6 if L["spk"] == "daniel" else 0.9, wet); add(y, L["t"], g * L.get("g", 1), .01)
    i = int((L["t"] - .15) * SR); j = min(N, i + len(y) + int(.2 * SR)); duck[i:j] = np.minimum(duck[i:j], .45)
duck = np.convolve(duck, np.ones(4800) / 4800, "same")
sc = load(P / os.environ["TWR_SCORE"])[:N]; sc = np.pad(sc, (0, N - len(sc)))
mix = mix + .55 * sc * duck
for a, b in TL.get("silence", []): mix[int(a * SR): int(b * SR)] = 0
mix /= max(1e-9, np.abs(mix).max()) / .8
sf.write(str(P / os.environ["TWR_MIX"]), np.stack([mix, mix], 1), SR, subtype="PCM_24"); print("MIX_DONE")
