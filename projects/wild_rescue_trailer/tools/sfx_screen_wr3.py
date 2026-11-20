#!/usr/bin/env python3
"""WR3 (11/1 evening rebuild) SFX screen + manifest. Run in ~/chatterbox-env on the M5 (CPU only).
Inputs: sfx/raw_moss/*.wav (MOSS-SoundEffect v2.0, PC CPU) + tools/sfx_jobs_wr3.py job list + sfx/raw_moss/gen_log.json.
Drop rule (LESSONS 10/31): spectral flatness > 0.30 AND centroid > 6 kHz (hiss), or peak < -40 dBFS (empty).
Kept files are peak-normalized to -1 dBFS into sfx/<name>.wav; failures get our numpy synth where one exists (sfx/synth/)."""
import json, shutil, sys
import numpy as np, soundfile as sf, librosa
from pathlib import Path
P = Path(__file__).resolve().parent.parent; S = P / "sfx"; R = S / "raw_moss"
sys.path.insert(0, str(P / "tools")); from sfx_jobs_wr3 import JOBS
gen = json.load(open(R / "gen_log.json")) if (R / "gen_log.json").exists() else {}
SYNTH = {"rabbit_thump": S / "synth/rabbit_thump_synth.wav"}
man = []
for name, secs, prompt, seed in JOBS:
    f = R / f"{name}.wav"; e = {"name": name, "prompt": prompt, "model": "MOSS-SoundEffect v2.0 (Apache-2.0), PC CPU fp32",
                              "seed": seed, "steps": gen.get(name, {}).get("steps", 16)}
    if not f.exists():
        e.update(status="missing"); man.append(e); print(name, "MISSING"); continue
    y, sr = sf.read(f); m = y.mean(1) if y.ndim > 1 else y
    fl = float(np.median(librosa.feature.spectral_flatness(y=m))); ce = float(np.median(librosa.feature.spectral_centroid(y=m, sr=sr)))
    pk = 20 * np.log10(np.abs(m).max() + 1e-9); rms = 20 * np.log10(np.sqrt(np.mean(m ** 2)) + 1e-9)
    bad = (fl > 0.30 and ce > 6000) or pk < -40
    e.update(seconds=round(len(m) / sr, 2), peak_db=round(pk, 1), rms_db=round(rms, 1), flatness=round(fl, 3), centroid_hz=round(ce))
    if not bad:
        sf.write(S / f"{name}.wav", (m * (10 ** (-1 / 20) / (np.abs(m).max() + 1e-9))).astype(np.float32), sr, subtype="PCM_24")
        e["status"] = "kept"
    elif name in SYNTH and SYNTH[name].exists():
        shutil.copy(SYNTH[name], S / f"{name}.wav"); e.update(status="replaced", replaced_by="numpy synth (tools/synth_sfx.py)")
    else:
        e["status"] = "dropped"
    man.append(e); print(f"{name:18s} flat {fl:.3f} cent {ce:6.0f} peak {pk:6.1f} rms {rms:6.1f} {e['status']}")
for n in ("sub_theme", "sub_rumble", "sub_hits", "title_sub"):
    f = S / f"{n}.wav"
    if f.exists():
        y, sr = sf.read(f); man.append({"name": n, "prompt": None, "model": "numpy synth (tools/synth_sfx.py)", "seconds": round(len(y) / sr, 2),
                                        "peak_db": round(20 * np.log10(np.abs(y).max() + 1e-9), 1), "rms_db": round(20 * np.log10(np.sqrt(np.mean(y ** 2)) + 1e-9), 1), "status": "kept (synth layer)"})
json.dump({"_note": "WR3 SFX, 2026-11-01 evening. MMAudio retired (CC BY-NC). Drop rule: flatness>0.30 & centroid>6 kHz, or peak<-40 dBFS.",
           "files": man}, open(S / "manifest.json", "w"), indent=1)
print("kept", sum(e.get("status") == "kept" for e in man), "replaced", sum(e.get("status") == "replaced" for e in man), "dropped", [e["name"] for e in man if e.get("status") in ("dropped", "missing")])
