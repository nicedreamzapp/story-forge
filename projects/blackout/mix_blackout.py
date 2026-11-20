#!/usr/bin/env python3
"""BLACKOUT audio: Song Forge score shaped by a gain curve + code-synthesized dial tone / hits / typing ticks / riser,
non-Matt voices on top. Matt's line gets a static gain only (no stretch/pitch/effects).
Run: ~/AI/ComfyUI/venv/bin/python mix_blackout.py  -> final/blackout_mix.wav, final/blackout_events.json"""
import json, subprocess
from pathlib import Path
import numpy as np, soundfile as sf

P = Path(__file__).resolve().parent
SR = 48000
TL = json.load(open(P / "final/timeline.json")); S = {s["name"]: s for s in TL["segments"]}; TOT = TL["duration"]
N = int(TOT * SR) + SR
rng = np.random.default_rng(3)
tr = {k: np.zeros(N, np.float32) for k in ("score", "sfx", "voice")}
EV = []

def rd(path, sr=SR):
    x, r = sf.read(path); x = x.mean(1) if x.ndim > 1 else x
    if r != sr:
        import scipy.signal as sg
        x = sg.resample_poly(x, sr, r)
    return x.astype(np.float32)

def put(track, x, t):
    i = int(t * SR)
    if i < 0: x = x[-i:]; i = 0
    j = min(N, i + len(x)); track[i:j] += x[:j - i]

def rms_db(x): return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
def voice(name, t, target=-19.0):
    x = rd(P / f"voices/{name}.wav" if name != "matt" else P / "voice/matt_line.wav")
    g = 10 ** ((target - rms_db(x[abs(x) > 0.01 * abs(x).max()])) / 20)     # static gain only
    put(tr["voice"], x * g, t); EV.append({"voice": name, "t": round(t, 3), "dur": round(len(x) / SR, 3), "gain_db": round(float(20 * np.log10(g)), 1)})

def env_curve(keys):
    ts = np.arange(N) / SR
    return np.interp(ts, [k[0] for k in keys], [k[1] for k in keys]).astype(np.float32)

def hit(t, power=1.0, f0=48, dur=1.8, noise=0.5):
    n = int(dur * SR); tt = np.arange(n) / SR
    body = np.sin(2 * np.pi * (f0 + 60 * np.exp(-tt * 14)) * tt) * np.exp(-tt * 2.2)
    nz = rng.normal(0, 1, n) * np.exp(-tt * 9) * noise
    import scipy.signal as sg
    b, a = sg.butter(2, 3500 / (SR / 2)); nz = sg.lfilter(b, a, nz)
    x = (body + nz).astype(np.float32) * 0.9 * power
    # cheap tail
    tail = rng.normal(0, 1, n) * np.exp(-tt * 1.6) * 0.04 * power; tail = sg.lfilter(*sg.butter(2, 400 / (SR / 2)), tail)
    put(tr["sfx"], x + tail.astype(np.float32), t); EV.append({"hit": round(t, 3), "power": float(power)})

def tick(t, g=0.07):
    n = int(0.018 * SR); x = rng.normal(0, 1, n) * np.exp(-np.arange(n) / (n / 5)) * g
    put(tr["sfx"], x.astype(np.float32), t)

def typing(start, cps, nchars, g=0.07):
    for k in range(nchars): tick(start + k / cps + rng.uniform(-0.01, 0.01), g * rng.uniform(0.6, 1.1))

# ---- dial tone that dies
n = int(1.7 * SR); tt = np.arange(n) / SR
f = 350 + 0 * tt; dial = (np.sin(2 * np.pi * 350 * tt) + np.sin(2 * np.pi * 440 * tt)) * 0.08
dial *= np.clip(1 - np.maximum(tt - 1.0, 0) / 0.6, 0, 1) ** 2 * np.clip(tt / 0.08, 0, 1)
put(tr["sfx"], dial.astype(np.float32), 0.1); EV.append({"dial_tone": [0.1, 1.8]})
# drone under cards
def drone(t0, t1, f0=55, g=0.05):
    n = int((t1 - t0) * SR); tt = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f0 * tt) + 0.5 * np.sin(2 * np.pi * f0 * 1.5 * tt + 1)) * g
    x *= np.clip(tt / 0.8, 0, 1) * np.clip((t1 - t0 - tt) / 0.8, 0, 1)
    put(tr["sfx"], x.astype(np.float32), t0)
drone(1.2, S["card3"]["end"], 55, 0.06)

# ---- score
sc = rd(P / "music/cand1.wav"); score = np.zeros(N, np.float32); score[:min(N, len(sc))] = sc[:N]
t_ask, t_rep = S["scr_ask"]["start"], S["scr_reply"]["start"]
title0 = S["title"]["start"]; gap0 = S["gap"]["start"]; still0 = S["still"]["start"]
keys = [(0, 0), (1.5, 0), (4.0, 0.22), (S["card3"]["start"], 0.45), (S["card3"]["end"], 0.2), (S["b4a"]["start"], 0.28), (t_ask + 2.2, 0.3),
        (t_rep - 0.9, 0.0), (t_rep - 0.02, 0.0), (t_rep + 0.05, 0.55), (S["a1"]["start"], 0.45), (S["card6"]["start"], 0.35), (S["card6"]["end"], 0.5),
        (S["rt"]["end"] - 0.3, 1.0), (S["b8a"]["start"], 0.35), (S["a2"]["start"] + 2.5, 0.35), (S["b9"]["start"], 0.55), (gap0 - 1.4, 0.9), (gap0 - 0.5, 0.0), (title0 - 0.02, 0.0),
        (title0 + 0.05, 0.6), (title0 + 8.4, 0.35), (still0, 0.25), (still0 + 2.4, 0.15), (TOT - 0.5, 0.0), (TOT + 1, 0)]
# fast-cut ramp
keys = sorted(keys + [(S["u1"]["start"], 0.55), (S["r2"]["start"], 0.75), (S["sf"]["start"], 0.9)], key=lambda k: k[0])
tr["score"] = score * env_curve(keys) * 0.9

# ---- sfx
for nm in ("card1", "card3", "card6"):
    hit(S[nm]["start"] + 0.2, 0.35, 42, 1.4, 0.2)
typing(t_ask + 0.3, 12, 16); typing(t_rep + 0.2, 20, 32); typing(still0 + 0.3, 12, 11)
hit(t_rep + 0.2, 1.0, 40, 2.5, 0.6)                                    # I'm here
hit(S["a1"]["start"] + 0.0, 0.25, 55, 1.2, 0.2)
# fast cuts: a drum on every cut, building
cuts = [S[k]["start"] for k in ("u1", "r1", "r2", "nar", "sf", "rt")]
for i, c in enumerate(cuts): hit(c, 0.35 + 0.1 * i, 60 - 3 * i, 1.0, 0.7)
# extra build hits between
t = S["u1"]["start"]; k = 0
while t < S["rt"]["end"]:
    hit(t + 0.55, 0.2 + 0.015 * k, 70, 0.5, 0.8); t += 0.55; k += 1
# riser into silence before title
n = int(3.0 * SR); tt = np.arange(n) / SR
ns = rng.normal(0, 1, n).astype(np.float32)
import scipy.signal as sg
risr = np.zeros(n, np.float32); step = SR // 50
for a in range(0, n - step, step):
    fc = 300 + 5500 * (a / n) ** 2
    b_, a_ = sg.butter(2, [fc / (SR / 2) * 0.7, min(0.99, fc / (SR / 2) * 1.3)], "band"); risr[a:a + step] = sg.lfilter(b_, a_, ns[a:a + step])
risr *= (tt / 3.0) ** 2 * 0.25
put(tr["sfx"], risr, gap0 - 3.0 + 0.4); EV.append({"riser": [gap0 - 2.6, gap0 - 0.5]})
risr_cut = env_curve([(0, 1), (gap0 - 0.5, 1), (gap0 - 0.45, 0), (TOT + 2, 0)]); tr["sfx"] *= np.where(np.arange(N) / SR > gap0 - 0.45, 1, 1)  # sfx kept; riser trimmed below
hit(title0, 1.2, 38, 3.5, 0.9)                                          # title slam
hit(title0, 0.6, 90, 1.0, 0.9)
drone(still0 - 0.2, TOT, 50, 0.05)
tr["sfx"] = tr["sfx"]

# ---- voices (non-Matt = ChatterBox, Matt = untouched file, static gain only)
voice("news", S["b2a"]["start"] + 0.9, -20)
voice("narr", S["nar"]["start"] + 0.1, -20)
rt = S["rt"]["start"]; voice("rt1", rt + 0.3, -20); voice("rt2", rt + 1.4, -20); voice("rt3", rt + 2.4, -20)
voice("stranger", S["b8a"]["start"] + 0.7, -19)
voice("matt", S["a2"]["start"] + 0.0, -17)

# duck score under voices
vd = np.abs(tr["voice"]); k = int(0.25 * SR); sm = np.convolve(vd, np.ones(k) / k, "same"); duck = 1 - 0.45 * np.clip(sm / 0.03, 0, 1)
tr["score"] *= duck
mix = tr["score"] * 0.55 + tr["sfx"] * 0.9 + tr["voice"]
mix = mix[:int(TOT * SR)]
pk = np.abs(mix).max(); mix = mix * (0.89 / pk) if pk > 0.89 else mix
sf.write(P / "final/blackout_mix.wav", np.stack([mix, mix], 1), SR, subtype="PCM_24")
json.dump(EV, open(P / "final/blackout_events.json", "w"), indent=1)
print("mix ok", round(TOT, 2), "s peak", round(float(pk), 2))
