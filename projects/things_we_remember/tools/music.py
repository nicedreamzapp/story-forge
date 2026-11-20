#!/usr/bin/env python3
"""THE THINGS WE REMEMBER teaser score, written in code (numpy). One lullaby; the Rememberer's WRONG NOTE is the
second note (E5 -> Eb5). A different soundtrack per section: music box -> wrong note + wind-down -> drone ->
reversed laughter bed -> pitched-down broken piano + speeding heartbeat -> dead silence -> drone -> title lullaby."""
import json, numpy as np, soundfile as sf
from pathlib import Path
P = Path(__file__).resolve().parent.parent
SR = 48000; TL = json.load(open(P / "timeline.json")); N = int(TL["end"] * SR)
rng = np.random.default_rng(7)
out = np.zeros(N)
def hz(m, cents=0.0): return 440 * 2 ** ((m - 69 + cents / 100) / 12)
def add(sig, t, g=1.0):
    i = int(t * SR); j = min(N, i + len(sig))
    if i < N: out[i:j] += g * sig[: j - i]
def mbox(m, dur=1.6, cents=None):
    c = rng.uniform(-14, 14) if cents is None else cents
    f = hz(m, c); t = np.arange(int(dur * SR)) / SR
    s = sum(a * np.sin(2 * np.pi * f * k * t) * np.exp(-t * d) for k, a, d in [(1, 1, 2.2), (2.0, .25, 5), (4.2, .12, 9), (6.8, .05, 14)])
    return s * np.minimum(1, t / .003)
def piano(m, dur=2.8, cents=0.0):
    f = hz(m, cents); t = np.arange(int(dur * SR)) / SR
    s = sum((1 / k) * np.sin(2 * np.pi * f * k * np.sqrt(1 + .0004 * k * k) * t) * np.exp(-t * (1.1 + .5 * k)) for k in range(1, 8))
    return s * np.minimum(1, t / .005)
def verb(x, sec=2.2, mix=.35):
    ir = rng.standard_normal(int(sec * SR)) * np.exp(-np.arange(int(sec * SR)) / SR * 3.2); ir /= np.abs(ir).sum() ** .5 * 6
    from scipy.signal import fftconvolve
    return (1 - mix) * x + mix * fftconvolve(x, ir)[: len(x)]
G4, A4, C5, D5, E5, Eb5 = 67, 69, 72, 74, 76, 75
P1 = [(G4, 1), (E5, 1), (D5, 1), (C5, 2), (G4, 1), (A4, 1), (C5, 1), (E5, 1), (D5, 3)]
P2 = [(G4, 1), (E5, 1), (D5, 1), (C5, 2), (A4, 1), (G4, 1), (E5, 1), (D5, 1), (C5, 3)]
def play(phrase, t0, beat, inst, wrong=False, g=.5, droop=0.0, slow=1.0):
    t = t0
    for i, (m, b) in enumerate(phrase):
        if wrong and i == 1: m = Eb5
        k = i / max(1, len(phrase) - 1)
        add(inst(m, cents=None if inst is mbox else 0) if droop == 0 else inst(m, cents=-droop * k), t, g)
        t += b * beat * (1 + (slow - 1) * k)
    return t
# A: warm music box, 0.3 -> ~11.1 s
mb = np.zeros(N); out_ref = out
t = play(P1, 0.3, 0.45, mbox); t = play(P2, t, 0.45, mbox)
# B: wrong note lands on Ruth's look, then the box winds down and droops
w = TL["wrong_note"]; play(P1[:6], w - 0.45, 0.45, mbox, wrong=True, droop=90, slow=2.4, g=.55)
# drone 14.5 -> 31.7 and 32.7 -> 42.5
def drone(t0, t1, g):
    n = int((t1 - t0) * SR); t = np.arange(n) / SR
    s = np.sin(2*np.pi*36.7*t) + .8*np.sin(2*np.pi*38.9*t) + .35*np.sin(2*np.pi*73.4*t + np.sin(2*np.pi*.11*t))
    nz = np.convolve(rng.standard_normal(n), np.ones(400) / 400, "same") * 2.5
    env = np.minimum(1, t / 1.5) * np.minimum(1, (t[-1] - t) / .05 + 0)
    add((s + nz) * env, t0, g)
drone(14.5, 31.7, .16); drone(32.7, 42.5, .10)
# D: broken piano, pitched down (an octave and a tritone), detuned, accelerating with the cuts, 24.6 -> 31.7
t = 24.6; beat = .62
for i, (m, b) in enumerate((P1 + P2) * 2):
    if t > 31.5: break
    mm = m - 18 + (rng.choice([0, 0, 0, 1, -1]))
    add(piano(mm, cents=rng.uniform(-45, 45)), t, .22)
    if rng.random() < .25: add(piano(mm + 1, cents=30), t + .03, .12)
    t += b * beat; beat *= .9
# heartbeat 24.8 -> 31.7, 55 -> 150 bpm
def lub(f, d): tt = np.arange(int(d * SR)) / SR; return np.sin(2*np.pi*f*tt*(1 - .3*tt/d)) * np.exp(-tt * 28)
t = 24.8
while t < 31.6:
    bpm = 55 + (150 - 55) * ((t - 24.8) / 6.8) ** 1.6
    add(lub(52, .22), t, .9); add(lub(42, .2), t + .19, .55); t += 60 / bpm
out = verb(out, 2.4, .3)
# E: dead silence 31.7 -> 32.7 (hard)
out[int(31.7 * SR): int(32.7 * SR)] = 0
# G: title lullaby with the wrong note, slow and far away, 38.2 ->
title = np.zeros(N); t0 = 38.2
for i, (m, b) in enumerate(P1):
    if i == 1: m = Eb5
    i0 = int(t0 * SR); s = mbox(m, 2.4); j = min(N, i0 + len(s)); title[i0:j] += .45 * s[: j - i0]; t0 += b * .6
out += verb(title, 3.0, .5)
E = int((TL["end"] - .7) * SR); out[E:] *= np.linspace(1, 0, N - E)
out /= max(1e-9, np.abs(out).max()) / .7
sf.write(str(P / "audio/score.wav"), np.stack([out, out], 1), SR, subtype="PCM_24")
print("score", round(N / SR, 2), "s")
