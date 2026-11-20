#!/usr/bin/env python3
"""Cue-driven score for every cut after the teaser (same instruments, lullaby and WRONG NOTE as music.py, which stays
the teaser's own). Cues live in the timeline's "score" list:
  mbox {t, phrases:"P1P2", beat, g}     warm music-box lullaby
  wrong {t}                              the wrong note (E5->Eb5) lands at t, box droops and winds down
  drone {t0, t1, g}                      low beating drone
  piano {t0, t1, g}                      pitched-down broken piano, accelerating
  heart {t0, t1, bpm0, bpm1}             heartbeat speeding up
  title {t, g}                           the slow far-away title lullaby with the wrong note
  right {t, g}                           the ending lullaby that finally plays the RIGHT note (only the last shot)
"silence": [[t0,t1],...] are hard zeroes after the reverb.  TWR_TL=timeline_X.json TWR_SCORE=audio/score_X.wav"""
import json, os, numpy as np, soundfile as sf
from pathlib import Path
from scipy.signal import fftconvolve
P = Path(__file__).resolve().parent.parent
SR = 48000; TL = json.load(open(P / os.environ["TWR_TL"])); N = int(TL["end"] * SR)
rng = np.random.default_rng(7); out = np.zeros(N)
def hz(m, cents=0.0): return 440 * 2 ** ((m - 69 + cents / 100) / 12)
def add(sig, t, g=1.0, buf=None):
    b = out if buf is None else buf; i = int(t * SR); j = min(N, i + len(sig))
    if 0 <= i < N: b[i:j] += g * sig[: j - i]
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
    return (1 - mix) * x + mix * fftconvolve(x, ir)[: len(x)]
G4, A4, C5, D5, E5, Eb5 = 67, 69, 72, 74, 76, 75
P1 = [(G4, 1), (E5, 1), (D5, 1), (C5, 2), (G4, 1), (A4, 1), (C5, 1), (E5, 1), (D5, 3)]
P2 = [(G4, 1), (E5, 1), (D5, 1), (C5, 2), (A4, 1), (G4, 1), (E5, 1), (D5, 1), (C5, 3)]
def play(phrase, t0, beat, inst, wrong=False, g=.5, droop=0.0, slow=1.0, until=None):
    t = t0
    for i, (m, b) in enumerate(phrase):
        if until and t > until: break
        if wrong and i == 1: m = Eb5
        k = i / max(1, len(phrase) - 1)
        add(inst(m, cents=None if inst is mbox else 0) if droop == 0 else inst(m, cents=-droop * k), t, g)
        t += b * beat * (1 + (slow - 1) * k)
    return t
def drone(t0, t1, g):
    n = int((t1 - t0) * SR); t = np.arange(n) / SR
    s = np.sin(2*np.pi*36.7*t) + .8*np.sin(2*np.pi*38.9*t) + .35*np.sin(2*np.pi*73.4*t + np.sin(2*np.pi*.11*t))
    nz = np.convolve(rng.standard_normal(n), np.ones(400) / 400, "same") * 2.5
    env = np.minimum(1, t / 1.5) * np.minimum(1, (t[-1] - t) / .05)
    add((s + nz) * env, t0, g)
def lub(f, d): tt = np.arange(int(d * SR)) / SR; return np.sin(2*np.pi*f*tt*(1 - .3*tt/d)) * np.exp(-tt * 28)
title = np.zeros(N)
for c in TL.get("score", []):
    k = c["k"]
    if k == "mbox":
        t = c["t"]; ph = {"P1": P1, "P2": P2}
        for p in [c.get("phrases", "P1P2")[i:i + 2] for i in range(0, len(c.get("phrases", "P1P2")), 2)]:
            t = play(ph[p], t, c.get("beat", .45), mbox, g=c.get("g", .5), until=c.get("until"))
    elif k == "wrong": play(P1[:6], c["t"] - 0.45, 0.45, mbox, wrong=True, droop=90, slow=2.4, g=.55)
    elif k == "drone": drone(c["t0"], c["t1"], c.get("g", .14))
    elif k == "piano":
        t = c["t0"]; beat = c.get("beat", .62)
        for i, (m, b) in enumerate((P1 + P2) * 6):
            if t > c["t1"] - .2: break
            mm = m - 18 + (rng.choice([0, 0, 0, 1, -1]))
            add(piano(mm, cents=rng.uniform(-45, 45)), t, c.get("g", .22))
            if rng.random() < .25: add(piano(mm + 1, cents=30), t + .03, .12)
            t += b * beat; beat = max(.12, beat * c.get("accel", .9))
    elif k == "heart":
        t = c["t0"]; L = c["t1"] - c["t0"]
        while t < c["t1"] - .1:
            bpm = c.get("bpm0", 55) + (c.get("bpm1", 150) - c.get("bpm0", 55)) * ((t - c["t0"]) / L) ** 1.6
            add(lub(52, .22), t, c.get("g", .9)); add(lub(42, .2), t + .19, c.get("g", .9) * .6); t += 60 / bpm
    elif k == "note":
        add(mbox(c.get("m", 75), 2.4, cents=-20), c["t"], c.get("g", .5), buf=title)
    elif k in ("title", "right"):
        t0 = c["t"]
        for i, (m, b) in enumerate(P1):
            if i == 1 and k == "title": m = Eb5
            add(mbox(m, 2.4, cents=0 if k == "right" else None), t0, c.get("g", .45), buf=title); t0 += b * c.get("beat", .6)
out = verb(out, 2.4, .3)
out += verb(title, 3.0, .5)
for a, b in TL.get("silence", []): out[int(a * SR): int(b * SR)] = 0
E = int((TL["end"] - .7) * SR); out[E:] *= np.linspace(1, 0, N - E)
out /= max(1e-9, np.abs(out).max()) / .7
sf.write(str(P / os.environ["TWR_SCORE"]), np.stack([out, out], 1), SR, subtype="PCM_24")
print("score", round(N / SR, 2), "s")
