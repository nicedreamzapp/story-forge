#!/usr/bin/env python3
"""Screen every generated SFX for noise-like hiss (LESSONS 10/31: MMAudio 'long riser' came back as white noise,
flatness 0.45, centroid 10.7 kHz) and silence. Writes sfx/screen.json {"files": {name: stats}, "drop": [names]}.
Drop rule: spectral flatness > 0.30 AND centroid > 6 kHz (hiss), or peak < -40 dBFS (empty)."""
import json
import numpy as np, soundfile as sf, librosa
from pathlib import Path
P = Path(__file__).resolve().parent.parent; S = P / "sfx"
jobs = json.load(open(S / "jobs.json")); res = {}; drop = []
for j in jobs:
    f = Path(j["out"])
    if not f.exists(): continue
    y, sr = sf.read(f); m = y.mean(1) if y.ndim > 1 else y
    fl = float(np.median(librosa.feature.spectral_flatness(y=m))); ce = float(np.median(librosa.feature.spectral_centroid(y=m, sr=sr)))
    pk = 20 * np.log10(np.abs(m).max() + 1e-9)
    bad = (fl > 0.30 and ce > 6000) or pk < -40
    res[j["name"]] = {"flatness": round(fl, 3), "centroid": round(ce), "peak_db": round(pk, 1), "drop": bool(bad)}
    if bad: drop.append(j["name"])
    print(f"{j['name']:18s} flat {fl:.3f} cent {ce:6.0f} peak {pk:6.1f} {'DROP' if bad else ''}")
json.dump({"files": res, "drop": drop}, open(S / "screen.json", "w"), indent=1)
print("drop:", drop)
