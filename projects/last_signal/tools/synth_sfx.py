#!/usr/bin/env python3
"""Our own numpy synth layers for THE LAST SIGNAL (no models). 48 kHz mono WAVs in sfx/:
  sub_arrival.wav  25-40 Hz swell under the arrival (starts on the c04 cut, swells 3.4 s, decays)
  beep_track.wav   the radio beep, accelerating like a heartbeat from 0.0 s, stops DEAD at the c09 cut
                   (Welcome back), then one final beep on the title slam; full-film length
  sub_hits.wav     a pitch-dropping sub kick (55->28 Hz) on every ramp/strobe cut; full-film length
  title_sub.wav    the long final sub drop under the title hit"""
import json
import numpy as np, soundfile as sf
from pathlib import Path
P = Path(__file__).resolve().parent.parent
SR = 48000
edl = json.load(open(P / "final/edl_final.json"))
cuts = {c["id"]: c for c in edl["cuts"]}
DUR = edl["duration"] + 1.0
t_arr = cuts["c04_arrival"]["start"]; t_wel = cuts["c09_welcome"]["start"]; t_title = cuts["c18_title"]["start"]

def env(n, a, r):
    e = np.ones(n); ai = int(a * SR); ri = int(r * SR)
    e[:ai] = np.linspace(0, 1, ai) ** 2
    if ri: e[-ri:] *= np.linspace(1, 0, ri) ** 1.5
    return e

# 1. arrival sub swell: 40 -> 25 Hz glide, slow attack, rumble tremolo, soft 2nd harmonic
n = int(6.5 * SR); t = np.arange(n) / SR
f = 40 - 15 * np.clip(t / 5.0, 0, 1)
ph = 2 * np.pi * np.cumsum(f) / SR
amp = np.clip(t / 3.4, 0, 1) ** 1.6 * np.exp(-np.clip(t - 3.6, 0, None) / 1.2)
trem = 1 + 0.18 * np.sin(2 * np.pi * 5.5 * t)
sub = (np.sin(ph) + 0.25 * np.sin(2 * ph)) * amp * trem
sub = np.tanh(1.6 * sub) / np.tanh(1.6)
sf.write(P / "sfx/sub_arrival.wav", (0.9 * sub / np.abs(sub).max()).astype(np.float32), SR, subtype="PCM_24")

# 2. the radio beep: 1.1 kHz carrier with a touch of 3rd harmonic, band-limited 'radio' color, 110 ms
bn = int(0.11 * SR); bt = np.arange(bn) / SR
beep = (np.sin(2 * np.pi * 1100 * bt) + 0.18 * np.sin(2 * np.pi * 3300 * bt)) * env(bn, 0.004, 0.03)
rng = np.random.default_rng(3)
track = np.zeros(int(DUR * SR))
times, tt, gap = [], 0.0, 1.05
while tt + 0.12 < t_wel:
    times.append(tt); tt += 1.1 * (0.28 / 1.1) ** (tt / t_wel)
times.append(t_title)
for b in times:
    i = int(b * SR); seg = track[i:i + bn]; seg += beep[:len(seg)] * (1.0 if b != t_title else 1.3)
track += rng.normal(0, 0.004, len(track)) * (np.arange(len(track)) / SR < t_wel)   # faint radio hiss, dies with the beep
sf.write(P / "sfx/beep_track.wav", (0.7 * track / np.abs(track).max()).astype(np.float32), SR, subtype="PCM_24")

# 3. sub kick on every ramp + strobe cut
kn = int(0.45 * SR); kt = np.arange(kn) / SR
kf = 28 + 27 * np.exp(-kt / 0.06)
kick = np.sin(2 * np.pi * np.cumsum(kf) / SR) * np.exp(-kt / 0.16) * env(kn, 0.002, 0.05)
kick = np.tanh(2.0 * kick)
hits = np.zeros(int(DUR * SR)); hit_times = []
for c in edl["cuts"]:
    if c["section"] in ("ramp", "strobe"):
        i = int(c["start"] * SR); g = 1.0 if c["section"] == "ramp" else 0.75
        seg = hits[i:i + kn]; seg += kick[:len(seg)] * g; hit_times.append(c["start"])
sf.write(P / "sfx/sub_hits.wav", (0.9 * hits / np.abs(hits).max()).astype(np.float32), SR, subtype="PCM_24")

# 4. title sub drop: 60 -> 24 Hz over 2.8 s
n = int(3.0 * SR); t = np.arange(n) / SR
f = 24 + 36 * np.exp(-t / 0.35)
td = np.tanh(1.8 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 1.1)) * env(n, 0.003, 0.4)
sf.write(P / "sfx/title_sub.wav", (0.9 * td / np.abs(td).max()).astype(np.float32), SR, subtype="PCM_24")
json.dump({"beeps": [round(x, 3) for x in times], "hits": hit_times, "arrival": t_arr, "welcome": t_wel, "title": t_title},
          open(P / "sfx/synth_times.json", "w"), indent=1)
print(len(times), "beeps, last pre-stop at", round(times[-2], 2), "; hits", len(hit_times))
