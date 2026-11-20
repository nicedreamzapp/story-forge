#!/usr/bin/env python3
"""Teaser mix: code score + MMAudio foley + VoiceDesign lines on the timeline -> audio/mix.wav (48k stereo).
Static gains only (no dynamic loudnorm); final level is set by final_audio_gate."""
import json, numpy as np, soundfile as sf
from pathlib import Path
from scipy.signal import resample_poly, fftconvolve, butter, sosfilt
P = Path(__file__).resolve().parent.parent; SR = 48000
TL = json.load(open(P / "timeline.json")); N = int(TL["end"] * SR); rng = np.random.default_rng(5)
def load(p):
    y, r = sf.read(str(p)); y = y.mean(1) if y.ndim > 1 else y
    if r != SR: y = resample_poly(y, SR, r)
    return y
mix = np.zeros(N); duck = np.ones(N)
def add(y, t, g, fade=.02):
    i = int(t * SR); j = min(N, i + len(y)); y = y[: j - i].copy(); f = int(fade * SR)
    if len(y) > 2 * f: y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)
    mix[i:j] += g * y
def verb(y, sec, wet):
    ir = rng.standard_normal(int(sec * SR)) * np.exp(-np.arange(int(sec * SR)) / SR * 4); ir /= np.sqrt((ir ** 2).sum()) * 1.4
    w = fftconvolve(y, ir); return (1 - wet) * np.pad(y, (0, len(w) - len(y))) + wet * w
def lp(y, hz): return sosfilt(butter(4, hz, "low", fs=SR, output="sos"), y)
def hp(y, hz): return sosfilt(butter(2, hz, "high", fs=SR, output="sos"), y)
fx = P / "audio/sfx"
# warm world: rain + room tone until the glass
add(load(fx / "rain.wav")[: int(10 * SR)], 0.0, .25, .8); gt = TL.get("glass_t", 16.1); add(load(fx / "rain.wav")[: int((gt - 10.0) * SR)], 10.0, .25, .005)
add(load(fx / "room.wav")[: int((gt - 7.0) * SR)], 7.0, .3, .005)   # room sound cuts dead at the shatter
add(load(fx / "glass.wav"), TL.get("glass_t", 16.1), .9, .005)
# reversed, slowed, muffled family laughter under the dinner
lau = load(fx / "laugh.wav")[::-1]; lau = resample_poly(lau, 5, 4); lau = lp(lau, 2500)
add(lau[: int(6 * SR)], 18.5, .45, .6)
add(hp(load(fx / "fork.wav"), 300)[: int(1.6 * SR)], 19.5, .6, .25)   # the fork slides 1.0-2.6 s into s06
add(load(fx / "creak.wav")[: int(3 * SR)], 24.5, .35, .3)
# voices
V = {"claire": (1.0, .10), "ruth": (1.0, .12), "lily": (1.0, .06), "daniel": (1.1, .45), "rememberer": (1.2, .18)}
for lid, L in TL["lines"].items():
    y = load(P / "voice/trimmed" / f"{lid}.wav"); g, wet = V[L["spk"]]
    if L["spk"] == "rememberer": y = lp(y, 7000)
    y = verb(y, 1.6 if L["spk"] == "daniel" else 0.9, wet); add(y, L["t"], g, .01)
    i = int((L["t"] - .15) * SR); j = min(N, i + len(y) + int(.2 * SR)); duck[i:j] = np.minimum(duck[i:j], .45)
duck = np.convolve(duck, np.ones(4800) / 4800, "same")
sc = load(P / "audio/score.wav")[:N]; sc = np.pad(sc, (0, N - len(sc)))
mix = mix + .55 * sc * duck
mix[int(31.7 * SR): int(32.7 * SR)] = 0                       # dead silence
mix /= max(1e-9, np.abs(mix).max()) / .8
sf.write(str(P / "audio/mix.wav"), np.stack([mix, mix], 1), SR, subtype="PCM_24"); print("MIX_DONE")
