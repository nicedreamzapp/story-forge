#!/usr/bin/env python3
"""KSSN 8 sound, all coded on the film clock (timeline.json): alert beeps + news sting on the cold open, a driving
news bed (pulse, timpani, low brass pads) ducked under every line, water ambience under the field shots, a splash after
"Look at this", whoosh + hit on the map and EVACUATION cards, a low comic "dun dun" on the fish, closing sting on the end
banner. Writes audio/mix.wav (48 kHz stereo, unnormalised; final.sh does the 2-pass loudness)."""
import json
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt
from pathlib import Path

P = Path(__file__).resolve().parent.parent
TL = json.load(open(P / "timeline.json"))
SR = 48000; END = TL["end"]; NS = int(END * SR)
rng = np.random.default_rng(8)
tt = lambda d: np.arange(int(d * SR)) / SR
def lp(x, f, o=2): return sosfilt(butter(o, f, "low", fs=SR, output="sos"), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, "high", fs=SR, output="sos"), x)
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], "band", fs=SR, output="sos"), x)
def noise(d): return rng.standard_normal(int(d * SR))
def env(n, a, d): t = np.arange(n) / SR; return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)
def put(buf, x, t, g=1.0):
    i = int(t * SR)
    if 0 <= i < len(buf): x = x[:len(buf) - i]; buf[i:i + len(x)] += x * g
def saw(f, d):
    t = tt(d); return sum(np.sin(2 * np.pi * f * k * t) / k for k in range(1, 9))
def brass(freqs, d, a=.02, rel=.5):
    x = sum(saw(f * (1 + .002 * j), d) for j, f in enumerate(freqs)); n = len(x)
    e = np.minimum(1, tt(d) / a) * np.minimum(1, (d - tt(d)) / rel)
    return lp(x, 2600) * e / len(freqs)
def timp(f=55, d=1.2): return (np.sin(2 * np.pi * f * tt(d)) + .4 * np.sin(2 * np.pi * f * 1.5 * tt(d))) * env(int(d * SR), .003, .35) + lp(noise(d), 300) * env(int(d * SR), .001, .05) * .6
def whoosh(d=.7): return bp(noise(d), 500, 5000) * np.sin(np.pi * tt(d) / d) ** 2 * .5
def stab(t0, chord, g=1.0):
    put(fx, brass(chord, .9, .01, .6) * .9 * g, t0); put(fx, timp(49, 1.4) * .9 * g, t0); put(fx, hp(noise(.5), 3000) * env(int(.5 * SR), .001, .15) * .25 * g, t0)

mus = np.zeros(NS); fx = np.zeros(NS); amb = np.zeros(NS)
C = TL["gfx"]["cold"]; L = TL["lines"]; SH = TL["shots"]

# ---- cold open: three alert beeps (not the EAS tones), whoosh, sting on the BREAKING slam
for t0 in (0.02, 0.62, 1.22):
    b = np.sin(2 * np.pi * 1050 * tt(.18)) + .3 * np.sin(2 * np.pi * 2100 * tt(.18)); b *= np.minimum(1, tt(.18) / .005) * np.minimum(1, (.18 - tt(.18)) / .01)
    put(fx, b * .16, t0)
put(fx, whoosh(.4), 0.0)
stab(0.15, [146.8, 220.0, 293.7, 349.2])        # Dm
stab(1.75, [130.8, 196.0, 261.6, 329.6], .8)     # C
stab(2.35, [146.8, 220.0, 293.7, 440.0], 1.0)    # Dm resolve into the anchor

# ---- news bed: 120 bpm, 16th pulse on D with a i-VI-VII-i progression, timpani on 1, pads; runs from the cold open to the end
BPM = 120; beat = 60 / BPM; bar = 4 * beat
prog = [[73.4, 146.8, 220.0], [58.3, 116.5, 174.6], [65.4, 130.8, 196.0], [73.4, 146.8, 220.0]]
t0 = C - .05; k = 0
while t0 < END - 1.0:
    ch = prog[k % 4]
    for s in range(16):
        f = ch[1] * (2 if s % 4 == 2 else 1)
        n = np.sin(2 * np.pi * f * tt(.11)) + .5 * np.sin(2 * np.pi * f * 2 * tt(.11))
        put(mus, lp(n, 1800) * env(int(.11 * SR), .003, .05) * .16, t0 + s * beat / 4)
    put(mus, timp(ch[0] if ch[0] > 50 else 55, 1.0) * .35, t0)
    put(mus, brass([c * 2 for c in ch], bar, .4, .6) * .18, t0)
    t0 += bar; k += 1

# ---- water ambience under field / b-roll water shots
WATER = ("lips:REP", "clip:hwy", "clip:reservoir", "clip:sage", "lips:RES", "still:pontoon", "clip:fish", "still:rings")
w = lp(noise(END), 900) * .5 + bp(noise(END), 1500, 5000) * .12
wm = np.zeros(NS)
for s in SH:
    if s["src"] in WATER:
        i0, i1 = int(s["s"] * SR), int(s["e"] * SR); wm[i0:i1] = 1.0 if s["src"] != "still:rings" else .5
wm = lp(lp(wm, 3), 3)
mod = 1 + .3 * np.sin(2 * np.pi * .23 * np.arange(NS) / SR) + .2 * lp(rng.standard_normal(NS), 2) * 20
amb += w * wm * np.clip(mod, .3, 1.8) * .55
for s in SH:   # bubbles/laps on water shots
    if s["src"] in WATER[:7]:
        for x in np.arange(s["s"], s["e"], .35):
            put(amb, np.sin(2 * np.pi * (500 + 600 * rng.random()) * tt(.05)) * env(int(.05 * SR), .002, .015) * .05, x + .2 * rng.random())

# ---- splash after "Look at this."
for s in SH:
    if s.get("mode") == "splash":
        for o, g in ((0.12, 1.0), (0.5, .7)):
            sp = bp(noise(.9), 300, 6000) * env(int(.9 * SR), .004, .18) + lp(noise(.9), 250) * env(int(.9 * SR), .002, .1)
            put(fx, sp * .55 * g, s["s"] + o)

# ---- card hits
for s in SH:
    if s["src"] == "map": put(fx, whoosh(.6) * .6, s["s"] - .35); stab(s["s"], [146.8, 220.0, 293.7], .45)
    if s["src"] == "evac":
        put(fx, whoosh(.6) * .7, s["s"] - .35); stab(s["s"], [116.5, 174.6, 233.1, 293.7], .8)
        for x in np.arange(s["s"] + .8, s["e"], .8):   # sign blink ticks
            put(fx, np.sin(2 * np.pi * 900 * tt(.06)) * env(int(.06 * SR), .002, .02) * .12, x)
    if s["src"] == "clip:fish":   # low comic "dun... dun"
        for o in (0.0, .55):
            put(fx, (np.sin(2 * np.pi * 61.7 * tt(.5)) + .5 * saw(61.7, .5) / 3) * env(int(.5 * SR), .01, .25) * .5, s["s"] + o)

# ---- end banner: closing sting, bed stops
E = TL["gfx"]["end"]
stab(E, [146.8, 220.0, 293.7, 349.2, 440.0], 1.0)
mus[int(E * SR):] = 0
put(mus, brass([73.4, 146.8, 220.0, 293.7], END - E, .05, 1.2) * .25, E)

# ---- dialogue + ducking (bed down ~13 dB while anyone speaks)
dlg, sr0 = sf.read(P / "audio/dlg.wav"); assert sr0 == SR
dlg = np.pad(dlg, (0, max(0, NS - len(dlg))))[:NS]
e = np.sqrt(np.maximum(0, lp(dlg ** 2, 6))); e = np.clip(e / (np.percentile(e[e > 1e-3], 90) + 1e-9), 0, 1)
e = np.maximum(e, np.convolve(e, np.ones(int(.25 * SR)) / int(.25 * SR), "same"))
spm = np.zeros(NS, bool)
for v in L.values(): spm[int(v["s"] * SR):int(v["e"] * SR)] = True
dlg = dlg * 10 ** ((-20.0 - 20 * np.log10(np.sqrt(np.mean(dlg[spm] ** 2)) + 1e-9)) / 20)   # dialogue to -20 dBFS rms while speaking
mix = dlg + mus * .2 * (1 - .8 * np.clip(e * 1.5, 0, 1)) + fx * .33 * (1 - .4 * np.clip(e, 0, 1)) + amb * .45 * (1 - .5 * np.clip(e, 0, 1))
mix[-int(.8 * SR):] *= np.linspace(1, 0, int(.8 * SR)) ** 2
st = np.stack([mix, mix], 1)
sf.write(P / "audio/mix.wav", st, SR, subtype="PCM_24")
print("SOUND_DONE", END)
