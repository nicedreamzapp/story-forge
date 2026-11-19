#!/usr/bin/env python3
"""music_clean_v51.py — clean the ACE-Step score's hiss (the 6-16 kHz noise-like floor in every window of theme_1/theme_2/
breakdown_1). Spectral denoise (noisereduce, stationary, profile = the file's own quietest 6-16 kHz frames) + a gentle
high shelf, then A/B by measurement: gap floor (should drop a lot) vs HF energy of the LOUD frames (the instruments' air;
should stay within a few dB or the result is dull). Usage: music_clean_v51.py IN OUT [--prop 0.9] [--shelf -3] [--try]
--try runs a small grid and prints the numbers without writing OUT."""
import sys, numpy as np, soundfile as sf, librosa, noisereduce as nr
from scipy.signal import butter, sosfiltfilt
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent)); from audio_audit_v51 import audit, bp, db, SR, FR
def hf_loud(y):   # HF (8-20 k) RMS over the loudest 20% of 50 ms frames = the instruments' air
    y = y.mean(1) if y.ndim > 1 else y; yh = bp(y, 8000, 20000); n = len(y) // FR
    e = np.sqrt((y[:n * FR].reshape(n, FR) ** 2).mean(1)); eh = np.sqrt((yh[:n * FR].reshape(n, FR) ** 2).mean(1))
    idx = np.argsort(e)[-max(1, n // 5):]; return db(np.sqrt((eh[idx] ** 2).mean()))
def noise_profile(y):   # the quietest 2 % of 6-16 k frames, stitched: the hiss on its own
    yb = bp(y, 6000, 16000); n = len(y) // FR
    e = np.sqrt((yb[:n * FR].reshape(n, FR, -1) ** 2).mean((1, 2))); idx = np.sort(np.argsort(e)[:max(4, n // 50)])
    return np.concatenate([y[i * FR:(i + 1) * FR] for i in idx])
def shelf(y, gain_db, fc=9000):   # gentle high shelf via band split
    if gain_db == 0: return y
    hi = sosfiltfilt(butter(2, fc, btype="high", fs=SR, output="sos"), y, axis=0)
    return y + hi * (10 ** (gain_db / 20) - 1)
def clean(y, prop, shelf_db):
    prof = noise_profile(y)
    out = np.stack([nr.reduce_noise(y=y[:, c], sr=SR, y_noise=prof[:, c] if prof.ndim > 1 else prof, stationary=True, prop_decrease=prop,
                                    n_fft=2048, freq_mask_smooth_hz=300, time_mask_smooth_ms=40) for c in range(y.shape[1])], 1)
    return np.stack([shelf(out[:, c], shelf_db) for c in range(out.shape[1])], 1).astype(np.float32)
def stats(y):
    m = y.mean(1); r = audit_mono(m); return r
def audit_mono(m):
    import tempfile, os
    t = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name; sf.write(t, m, SR); res = audit(t); os.unlink(t)
    return {"hiss_windows": sum(x["hiss"] for x in res), "worst_floor": max(x["floor"] for x in res),
            "median_floor": float(np.median([x["floor"] for x in res])), "hf_loud": hf_loud(m)}
if __name__ == "__main__":
    a = sys.argv[1:]; src, dst = a[0], a[1]
    prop = float(a[a.index("--prop") + 1]) if "--prop" in a else 0.9
    sh = float(a[a.index("--shelf") + 1]) if "--shelf" in a else -3.0
    y, _ = librosa.load(src, sr=SR, mono=False); y = y.T if y.ndim > 1 else np.stack([y, y], 1)
    base = stats(y); print(f"BEFORE {src}: {base}")
    if "--try" in a:
        for p, s in [(0.7, 0), (0.85, 0), (0.95, 0), (0.85, -3), (0.95, -4), (1.0, -6)]:
            print(f"  prop {p} shelf {s}: {stats(clean(y, p, s))}")
    else:
        out = clean(y, prop, sh); st = stats(out); print(f"AFTER  {dst}: {st}")
        sf.write(dst, out, SR, subtype="PCM_24")
