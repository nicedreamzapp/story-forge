#!/usr/bin/env python3
"""music_gate_v51.py IN OUT [--att 18] [--pct 5] [--knee 6] [--try]
Per-bin stationary noise-bed gate for the ACE-Step score (the broadband bed ~25 dB under the notes that noisereduce
left untouched). STFT (2048/512 at 48 k); the bed per bin = the PCT-th percentile of that bin's magnitude over time
(it never falls silent, so the percentile IS the bed); gain per bin/frame = smooth soft-knee from 1.0 (magnitude far
above the bed) down to -ATT dB (at or below the bed), smoothed over 3 frames so it does not flutter. Loud notes are
untouched (a bed 25 dB under a note changes it by 0.03 dB); only the gaps drop. Measured before/after: gap floor
(6-16 k), instrument air (HF of the loudest 20% frames), hiss windows. --try prints a grid without writing."""
import sys, numpy as np, soundfile as sf, librosa
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from music_clean_v51 import stats, SR
NF, HOP = 2048, 512
def gate(y, att_db=18.0, pct=5.0, knee_db=6.0):
    out = np.zeros_like(y)
    for c in range(y.shape[1]):
        S = librosa.stft(y[:, c], n_fft=NF, hop_length=HOP); M = np.abs(S) + 1e-12
        bed = np.percentile(M, pct, axis=1, keepdims=True) * 1.2            # a hair above the bed
        r_db = 20 * np.log10(M / bed)                                         # 0 dB = at the bed
        t = np.clip(r_db / knee_db, 0, 1); g_db = -att_db * (1 - t) ** 2      # soft knee: -att at the bed, 0 at +knee dB
        g = 10 ** (g_db / 20)
        g = np.maximum.reduce([np.roll(g, -1, 1), g, np.roll(g, 1, 1)])     # hold gain over 3 frames (no flutter)
        out[:, c] = librosa.istft(S * g, hop_length=HOP, length=len(y))
    return out.astype(np.float32)
if __name__ == "__main__":
    a = sys.argv[1:]; src, dst = a[0], a[1]
    att = float(a[a.index("--att") + 1]) if "--att" in a else 18.0
    pct = float(a[a.index("--pct") + 1]) if "--pct" in a else 5.0
    knee = float(a[a.index("--knee") + 1]) if "--knee" in a else 6.0
    y, _ = librosa.load(src, sr=SR, mono=False); y = y.T if y.ndim > 1 else np.stack([y, y], 1)
    print(f"BEFORE {src}: {stats(y)}")
    if "--try" in a:
        for at, p, k in [(12, 5, 6), (18, 5, 6), (24, 5, 6), (18, 10, 6), (18, 5, 10), (24, 10, 8)]:
            print(f"  att {at} pct {p} knee {k}: {stats(gate(y, at, p, k))}", flush=True)
    else:
        out = gate(y, att, pct, knee); print(f"AFTER  {dst} (att {att} pct {pct} knee {knee}): {stats(out)}")
        sf.write(dst, out, SR, subtype="PCM_24")
