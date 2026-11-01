#!/usr/bin/env python3
"""Cut each score candidate to the v3 beat map and rank them (run in ~/chatterbox-env: librosa).
Sections on the film timeline (final/edl_final.json):
  drone   0.00 -> arrival      quiet, few onsets (the beep carries the hook)
  arrival arrival -> claws     must START on the candidate's biggest onset (the BRAAAM lands on the cut)
  build   claws -> welcome     rising energy, no dropouts
  STOP    welcome -> ramp      silence (dead stop for "Welcome back, Captain")
  ramp    ramp -> black        loudest, densest onsets, no dips (min RMS high)
  BLACK   silence; the title hit is designed (final_hit + sub), the score's last hit is not needed
For every candidate the best window per section is searched on a 0.05 s grid (no material reused, no dropouts
inside build/ramp), joined with
12 ms crossfades exactly on the cut frames, and scored. Writes music/arranged/score_N_arranged.wav (48 kHz stereo,
film length) + music/arranged/arrangement.json; prints the ranking."""
import json, numpy as np, librosa, soundfile as sf
from pathlib import Path
P = Path(__file__).resolve().parent.parent
e = json.load(open(P / "final/edl_final.json")); cut = {c["id"]: c["start"] for c in e["cuts"]}
A, C, W, R, B = cut["c04_arrival"], cut["c05_claws"], cut["c09_welcome"], cut["c10_second_sun"], cut["c17_black"]
DUR = e["duration"]; SR = 48000; HOP = 0.05
secs = [("drone", 0.0, A), ("arrival", A, C), ("build", C, W), ("ramp", R, B)]
(P / "music/arranged").mkdir(exist_ok=True)
out = {}
for n in (1, 2, 3):
    y, _ = librosa.load(P / f"music/candidates/score_{n}.wav", sr=SR, mono=False)
    m = y.mean(0)
    hop = int(HOP * SR)
    rms = librosa.feature.rms(y=m, frame_length=4 * hop, hop_length=hop)[0]
    rdb = 20 * np.log10(rms + 1e-6)
    on = librosa.onset.onset_strength(y=m, sr=SR, hop_length=hop); on = on / (on.max() + 1e-9)
    L = len(rdb); pick = {}; total = 0; used = []
    for name, s0, s1 in sorted(secs, key=lambda x: ["arrival", "ramp", "build", "drone"].index(x[0])):
        nl = int(round((s1 - s0) / HOP)); best = (-1e9, 0)
        for i in range(0, L - nl):
            if any(i < b and i + nl > a for a, b in used): continue   # never reuse material (no audible repeats)
            if name in ("build", "ramp") and rdb[i:i + nl].min() < -36: continue   # no dropouts inside a section
            w = rdb[i:i + nl]; o = on[i:i + nl]
            if name == "drone":
                f = -np.mean(w) / 6 - 3 * o.mean() - np.std(w) / 4 - max(0, w.max() + 18) / 3
            elif name == "arrival":
                f = 4 * on[i:i + 3].max() + np.mean(w) / 10
            elif name == "build":
                slope = np.polyfit(np.arange(nl), w, 1)[0] * nl
                f = slope / 4 + np.mean(w) / 8 + np.min(w) / 10
            else:
                f = np.mean(w) / 4 + np.min(w) / 4 + 6 * o.mean()
            if f > best[0]: best = (f, i)
        pick[name] = round(best[1] * HOP, 2); total += best[0]; used.append((best[1], best[1] + nl))
    if n == 1:   # builder's nudge: lands candidate 1's 3.0 s hit exactly on the c02b lever-slam cut (2.5 s)
        pick["drone"] = round(3.0 - cut["c02b_lever"], 2)
    # render
    outw = np.zeros((2, int(DUR * SR) + SR))
    xf = int(0.012 * SR)
    for name, s0, s1 in secs:
        a = int(pick[name] * SR); nl = int((s1 - s0) * SR)
        seg = y[:, a:a + nl + xf].copy()
        ramp = np.ones(seg.shape[1]); ramp[:xf] = np.linspace(0, 1, xf); ramp[-xf:] = np.linspace(1, 0, xf)
        if name == "drone":   # sit under the beep: ease in over 2.5 s
            g = np.clip(np.arange(seg.shape[1]) / (2.5 * SR), 0, 1) ** 1.5; ramp *= g
        b = int(s0 * SR); outw[:, b:b + seg.shape[1]] += seg * ramp
    outw = outw[:, :int(DUR * SR)]
    sf.write(P / f"music/arranged/score_{n}_arranged.wav", outw.T.astype(np.float32), SR, subtype="PCM_24")
    out[n] = {"windows_in_candidate": pick, "fitness": round(float(total), 2)}
    print(n, out[n], flush=True)
json.dump({"sections": secs, "candidates": out}, open(P / "music/arranged/arrangement.json", "w"), indent=1)
