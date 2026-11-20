#!/usr/bin/env python3
"""Cut each score candidate to the WILD RESCUE beat map and rank them (run in ~/chatterbox-env: librosa).
Reused from projects/last_signal/tools/score_arrange.py, sections re-mapped to script v3 (final/edl_final.json):
  night   0.00 -> c02a_rails      mysterious, low, few onsets (night forest, Doug's line sits on top of it)
  call    c02a -> c03a_burst      urgency building: rising RMS slope, steady onsets, no dropouts
  theme   c03a -> c05a_hank       must START on the candidate's biggest onset (the brass THEME hit lands on the wagon
                                  burst), then the gallop: loud, dense, no dips; tension carries through the stakes
  STOP    c05a -> c06a_ground     silence (dead stop for Hank's line and Doug's answer)
  ramp    c06a -> c08_black       the swell: rising slope and loudest/densest, no dips
  BLACK   silence; the title hit is designed (title_boom + sub) and the score re-enters for
  button  c10a -> end             a light playful window: moderate level, bright, onsets present, nothing heavy
Best window per section on a 0.05 s grid (no material reused), joined with 12 ms crossfades exactly on the cut frames,
short fade-outs into the STOP and BLACK. Writes music/arranged/score_N_arranged.wav (48 kHz stereo, film length) +
music/arranged/arrangement.json; prints the ranking."""
import json, numpy as np, librosa, soundfile as sf
from pathlib import Path
P = Path(__file__).resolve().parent.parent
e = json.load(open(P / "final/edl_final.json")); cut = {c["id"]: c["start"] for c in e["cuts"]}
DUR = e["duration"]; SR = 48000; HOP = 0.05
secs = [("night", 0.0, cut["c02a_rails"]), ("call", cut["c02a_rails"], cut["c03a_burst"]),
        ("theme", cut["c03a_burst"], cut["c05a_hank"]), ("ramp", cut["c06a_ground"], cut["c08_black"]),
        ("button", cut["c10a_ant_salute"], DUR)]
ORDER = ["theme", "ramp", "call", "button", "night"]
(P / "music/arranged").mkdir(exist_ok=True)
out = {}
for n in (1, 2, 3):
    f = P / f"music/candidates/score_{n}.wav"
    if not f.exists(): continue
    y, _ = librosa.load(f, sr=SR, mono=False)
    m = y.mean(0); hop = int(HOP * SR)
    rms = librosa.feature.rms(y=m, frame_length=4 * hop, hop_length=hop)[0]; rdb = 20 * np.log10(rms + 1e-6)
    on = librosa.onset.onset_strength(y=m, sr=SR, hop_length=hop); on = on / (on.max() + 1e-9)
    cen = librosa.feature.spectral_centroid(y=m, sr=SR, hop_length=hop)[0]
    L = min(len(rdb), len(on), len(cen)); pick = {}; total = 0; used = []
    for name, s0, s1 in sorted(secs, key=lambda x: ORDER.index(x[0])):
        nl = int(round((s1 - s0) / HOP)); best = (-1e9, 0)
        for i in range(0, L - nl):
            if any(i < b and i + nl > a for a, b in used): continue
            w = rdb[i:i + nl]; o = on[i:i + nl]
            if name in ("call", "theme", "ramp") and w.min() < -36: continue
            if name == "night":
                fit = -np.mean(w) / 6 - 3 * o.mean() - np.std(w) / 4 - max(0, w.max() + 18) / 3
            elif name == "call":
                slope = np.polyfit(np.arange(nl), w, 1)[0] * nl
                fit = slope / 4 + np.mean(w) / 10 + 2 * o.mean()
            elif name == "theme":
                fit = 4 * on[i:i + 3].max() + np.mean(w) / 6 + np.min(w) / 10 + 2 * o.mean()
            elif name == "ramp":
                slope = np.polyfit(np.arange(nl), w, 1)[0] * nl
                fit = slope / 5 + np.mean(w) / 5 + np.min(w) / 6 + 5 * o.mean()
            else:   # button: light and bright, moderate level, some plucks
                fit = -abs(np.mean(w) + 24) / 4 + 2 * o.mean() + np.mean(cen[i:i + nl]) / 4000 - max(0, w.max() + 10) / 3
            if fit > best[0]: best = (fit, i)
        pick[name] = round(best[1] * HOP, 2); total += best[0]; used.append((best[1], best[1] + nl))
    outw = np.zeros((2, int(DUR * SR) + SR)); xf = int(0.012 * SR)
    for name, s0, s1 in secs:
        a = int(pick[name] * SR); nl = int((s1 - s0) * SR)
        seg = y[:, a:a + nl + xf].copy()
        if seg.shape[1] < 2 * xf: continue
        ramp = np.ones(seg.shape[1]); ramp[:xf] = np.linspace(0, 1, xf); ramp[-xf:] = np.linspace(1, 0, xf)
        if name == "night": ramp *= np.clip(np.arange(seg.shape[1]) / (1.5 * SR), 0, 1) ** 1.5
        if name in ("theme", "ramp"):   # short tail fade into the STOP / the smash to black
            k = int(0.06 * SR); ramp[-k:] *= np.linspace(1, 0, k)
        if name == "button":            # ease out at the very end
            k = int(0.6 * SR); ramp[-k:] *= np.linspace(1, 0, k) ** 2
        b = int(s0 * SR); outw[:, b:b + seg.shape[1]] += seg * ramp
    outw = outw[:, :int(DUR * SR)]
    sf.write(P / f"music/arranged/score_{n}_arranged.wav", outw.T.astype(np.float32), SR, subtype="PCM_24")
    out[n] = {"windows_in_candidate": pick, "fitness": round(float(total), 2)}
    print(n, out[n], flush=True)
json.dump({"sections": secs, "candidates": out}, open(P / "music/arranged/arrangement.json", "w"), indent=1)
