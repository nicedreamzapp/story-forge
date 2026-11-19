#!/usr/bin/env python3
"""sfx_clean_v5.py — plan_v5 A1 one-pass foley clean-up. For every cue in tools/cues_v5.json:
high-pass 100 Hz + low-pass 9 kHz (4th-order Butterworth, zero phase) and stationary spectral denoise at 50%
(noisereduce, prop_decrease 0.5) over the whole source file (better noise estimate), then a HARD GATE to the action
window (onset - pre .. onset + len, 10 ms fades), optional short reverb tail, peak-normalise to -6 dBFS.
The mix dB from the cue table is applied later by mix_v5.py. Writes sfx/v5/clean/<row>__<sfx>.wav and
sfx/v5/clean/clean.json (file + where the action onset sits inside it).
Run with ~/chatterbox-env/bin/python (has noisereduce + librosa)."""
import json
from pathlib import Path
import numpy as np, soundfile as sf, noisereduce as nr
from scipy.signal import butter, sosfiltfilt

P = Path(__file__).resolve().parent.parent
OUT = P / "sfx/v5/clean"; OUT.mkdir(parents=True, exist_ok=True)
CUES = json.load(open(P / "tools/cues_v5.json"))


def onset_of(y, sr, db=-30.0):
    m = np.abs(y).max(1); thr = 10 ** (db / 20) * (m.max() + 1e-9)
    idx = int(np.argmax(m > thr)); return idx / sr if m[idx] > thr else 0.0


def clean_full(y, sr):
    sos_hp = butter(4, 100, "highpass", fs=sr, output="sos")
    sos_lp = butter(4, 9000, "lowpass", fs=sr, output="sos")
    y = sosfiltfilt(sos_lp, sosfiltfilt(sos_hp, y, axis=0), axis=0)
    return np.stack([nr.reduce_noise(y=y[:, c], sr=sr, stationary=True, prop_decrease=0.5) for c in range(y.shape[1])], -1)


def reverb_tail(y, sr, secs):
    rng = np.random.default_rng(5); n = int(secs * sr)
    ir = rng.standard_normal(n) * np.exp(-np.linspace(0, 6.9, n)); ir /= np.abs(ir).sum()
    pad = np.vstack([y, np.zeros((n, y.shape[1]))])
    wet = np.stack([np.convolve(pad[:, c], ir)[:len(pad)] for c in range(y.shape[1])], -1)
    return pad * 1.0 + wet * 0.35


report = {}
for c in CUES:
    src = P / c["src"]; key = f"{c['row']}__{c['sfx']}"
    if not src.exists():
        report[key] = {"error": f"missing {c['src']}"}; print("MISSING", c["src"]); continue
    y, sr = sf.read(src, always_2d=True); y = y.astype(np.float64)
    on_raw = 0.0 if c.get("from_start") else onset_of(y, sr, c.get("onset_db", -30.0))
    y = clean_full(y, sr)
    pre = 0.0 if c.get("from_start") else c.get("pre", 0.01)
    a = max(0, int((on_raw - pre) * sr)); b = min(len(y), int((on_raw + c["len"]) * sr))
    w = y[a:b].copy(); pre_eff = on_raw - a / sr
    f = int(0.010 * sr); ramp = np.linspace(0, 1, f)[:, None]
    w[:f] *= ramp; w[-f:] *= ramp[::-1]
    if c.get("tail_reverb"): w = reverb_tail(w, sr, c["tail_reverb"])
    w *= 10 ** (-6 / 20) / (np.abs(w).max() + 1e-12)
    out = OUT / f"{key}.wav"; sf.write(out, w.astype(np.float32), sr, subtype="FLOAT")
    report[key] = {"file": str(out.relative_to(P)), "onset_in_file": round(pre_eff, 4), "secs": round(len(w) / sr, 3),
                   "src": c["src"], "window_src": [round(a / sr, 3), round(b / sr, 3)]}
    print(f"{key:36s} window {a/sr:5.2f}-{b/sr:5.2f}s of {c['src']}  -> {len(w)/sr:.2f}s")
json.dump(report, open(OUT / "clean.json", "w"), indent=1)
