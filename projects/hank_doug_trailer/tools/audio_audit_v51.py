#!/usr/bin/env python3
"""audio_audit_v51.py — hiss / noise-floor audit per 3 s window (Matt 11/18 1:01 PM: "lame hissing static", "so many bad
audio scenes"). Calibrated dBFS, time domain. For every file: per 3 s window
  rms      = RMS of the window (dBFS)
  hf       = RMS of the 8-20 kHz band (dBFS)
  gapfloor = 10th percentile of 50 ms-frame RMS of the 6-16 kHz band = what you hear between notes/words (dBFS)
  flat     = spectral flatness (6-16 kHz) of those floor frames, 1.0 = pure noise
A window is HISS when gapfloor > FLOOR_DB and flat > FLAT (a steady noise-like floor you can hear in the gaps).
Usage: audio_audit_v51.py [--floor -60] [--flat 0.35] [--json out] [--timeline tools/timeline_v5.json] FILE...
Import: from audio_audit_v51 import audit -> list of window dicts."""
import sys, json, numpy as np, librosa
from scipy.signal import butter, sosfiltfilt
SR = 48000; WIN = 3.0; FR = int(0.05 * SR)
def db(x): return float(20 * np.log10(max(float(x), 1e-9)))
def bp(y, lo, hi): return sosfiltfilt(butter(4, [lo, min(hi, SR / 2 - 1)], btype="band", fs=SR, output="sos"), y, axis=0)
def audit(f, floor_db=-60.0, flat_max=0.35, rows=None):
    y, _ = librosa.load(f, sr=SR, mono=True)
    yb = bp(y, 6000, 16000); yh = bp(y, 8000, 20000)
    n = len(y) // FR
    fr_b = np.sqrt((yb[:n * FR].reshape(n, FR) ** 2).mean(1) + 1e-18)
    S = np.abs(librosa.stft(yb, n_fft=2048, hop_length=FR, center=False))
    freqs = librosa.fft_frequencies(sr=SR, n_fft=2048); band = (freqs >= 6000) & (freqs <= 16000)
    flat = librosa.feature.spectral_flatness(S=S[band], power=1)[0]; flat = np.pad(flat, (0, max(0, n - len(flat))), mode="edge")[:n]
    per = int(WIN / 0.05); res = []
    for w in range(int(np.ceil(n / per))):
        sl = slice(w * per, min(n, (w + 1) * per))
        if sl.stop - sl.start < 10: continue
        a, b = sl.start * FR, sl.stop * FR
        rms = db(np.sqrt((y[a:b] ** 2).mean())); hf = db(np.sqrt((yh[a:b] ** 2).mean()))
        fb = fr_b[sl]; k = max(1, int(len(fb) * 0.1)); idx = np.argsort(fb)[:k]
        floor = db(np.sqrt((fb[idx] ** 2).mean())); fl = float(np.median(flat[sl][idx]))
        t = w * WIN; row = ""
        if rows:
            for rid, ra, rb in rows:
                if ra <= t + 1.0 < rb: row = rid
        hiss = floor > floor_db and fl > flat_max
        res.append({"t": round(t, 1), "row": row, "rms": round(rms, 1), "hf": round(hf, 1), "floor": round(floor, 1), "flat": round(fl, 2), "hiss": bool(hiss)})
    return res
if __name__ == "__main__":
    args = sys.argv[1:]
    g = lambda k, d: type(d)(args[args.index(k) + 1]) if k in args else d
    FLOOR_DB, FLAT, JOUT, TLF = g("--floor", -60.0), g("--flat", 0.35), g("--json", ""), g("--timeline", "")
    skip = {"--floor", "--flat", "--json", "--timeline"}
    files = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] not in skip)]
    rows = [(r["id"], r["start"], r["start"] + r["dur"]) for r in json.load(open(TLF))["rows"]] if TLF else None
    out = {}
    for f in files:
        res = audit(f, FLOOR_DB, FLAT, rows); out[f] = res; bad = sum(r["hiss"] for r in res)
        print(f"\n== {f}  windows {len(res)}  HISS windows {bad}  worst gapfloor {max(r['floor'] for r in res):.1f} dBFS")
        print("   t   row            rms    hf>8k  gapfloor flat")
        for r in res:
            print(f" {r['t']:5.1f} {r['row']:14s} {r['rms']:6.1f} {r['hf']:7.1f} {r['floor']:8.1f} {r['flat']:5.2f} {'HISS' if r['hiss'] else ''}")
    if JOUT: json.dump(out, open(JOUT, "w"), indent=1)
