#!/usr/bin/env python3
"""Our own numpy sub layer for WILD RESCUE (no models). 48 kHz mono WAVs in sfx/:
  sub_theme.wav    a 45->30 Hz sub punch + 2.5 s tail under the THEME hit (wagon burst)
  sub_rumble.wav   a slow 28-36 Hz ground rumble under the ant reveal (c06a -> c07a), swelling
  sub_hits.wav     a pitch-dropping sub kick (55->28 Hz) on every ramp cut; full-film length, nothing after the black
  title_sub.wav    the long final sub drop under the title slam
Times come from final/edl_final.json; sfx/synth_times.json records them."""
import json
import numpy as np, soundfile as sf
from pathlib import Path
P = Path(__file__).resolve().parent.parent
SR = 48000
edl = json.load(open(P / "final/edl_final.json")); cut = {c["id"]: c for c in edl["cuts"]}
DUR = edl["duration"] + 1.0
def env(n, a, r):
    e = np.ones(n); ai = max(1, int(a * SR)); ri = int(r * SR)
    e[:ai] = np.linspace(0, 1, ai) ** 2
    if ri: e[-ri:] *= np.linspace(1, 0, ri) ** 1.5
    return e
def w(name, y): sf.write(P / f"sfx/{name}.wav", (0.9 * y / (np.abs(y).max() + 1e-9)).astype(np.float32), SR, subtype="PCM_24")
# theme sub punch
n = int(3.0 * SR); t = np.arange(n) / SR
f = 30 + 15 * np.exp(-t / 0.25)
y = np.tanh(1.8 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.9)) * env(n, 0.004, 0.4); w("sub_theme", y)
# ground rumble for the reveal
d = cut["c07a_bridge"]["start"] - cut["c06a_ground"]["start"] + 0.6
n = int(d * SR); t = np.arange(n) / SR
f = 28 + 8 * np.clip(t / d, 0, 1)
rng = np.random.default_rng(4)
am = 1 + 0.25 * np.interp(t, np.linspace(0, d, 40), rng.uniform(-1, 1, 40))
y = (np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(4 * np.pi * np.cumsum(f) / SR)) * am * (np.clip(t / d, 0, 1) ** 1.3) * env(n, 0.3, 0.3)
w("sub_rumble", np.tanh(1.5 * y))
# ramp kicks
kn = int(0.45 * SR); kt = np.arange(kn) / SR
kick = np.tanh(2.0 * np.sin(2 * np.pi * np.cumsum(28 + 27 * np.exp(-kt / 0.06)) / SR) * np.exp(-kt / 0.16)) * env(kn, 0.002, 0.05)
hits = np.zeros(int(DUR * SR)); ht = []
for c in edl["cuts"]:
    if c["section"] == "ramp":
        i = int(c["start"] * SR); seg = hits[i:i + kn]; seg += kick[:len(seg)]; ht.append(c["start"])
blk = int(cut["c08_black"]["start"] * SR); hits[blk:] = 0
w("sub_hits", hits)
# rabbit thump (MMAudio's came back empty, peak -44.7 dB): two soft low thuds in dirt, 0.1 s and 0.42 s into the cut
n = int(0.9 * SR); y = np.zeros(n); rng2 = np.random.default_rng(9)
for t0 in (0.10, 0.42):
    m = int(0.25 * SR); tt = np.arange(m) / SR
    th = np.sin(2 * np.pi * np.cumsum(70 + 60 * np.exp(-tt / 0.02)) / SR) * np.exp(-tt / 0.06)
    dirt = np.convolve(rng2.normal(0, 1, m), np.ones(40) / 40, "same") * np.exp(-tt / 0.03) * 0.5
    i = int(t0 * SR); y[i:i + m] += th + dirt
w("rabbit_thump", y)
# title sub drop
n = int(3.0 * SR); t = np.arange(n) / SR
y = np.tanh(1.8 * np.sin(2 * np.pi * np.cumsum(24 + 36 * np.exp(-t / 0.35)) / SR) * np.exp(-t / 1.1)) * env(n, 0.003, 0.4); w("title_sub", y)
json.dump({"theme": cut["c03a_burst"]["start"], "reveal": cut["c06a_ground"]["start"], "hits": ht,
           "black": cut["c08_black"]["start"], "title": cut["c09_title"]["start"]}, open(P / "sfx/synth_times.json", "w"), indent=1)
print("synth done; ramp hits", len(ht))
