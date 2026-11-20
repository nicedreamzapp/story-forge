#!/usr/bin/env python3
"""click_audit_v52.py FILE... [--cues final/mix_cues_v51.json] [--timeline tools/timeline_v5.json] [--win 0.5]
Static + scratching finder per 0.5 s window (Matt 11/18 1:52 PM). Per window:
  hiss  = 10th-percentile 50 ms HF (6-16 k) floor in dBFS + spectral flatness of those frames (noise-like > 0.35)
  click = count of sample-to-sample jumps > 0.25 full scale that are NOT part of a broadband onset (crackle/clicks)
  flux  = spectral flux spikes (> 6x the window median) not within 80 ms of a placed cue/line onset
  clip  = samples at or beyond 0.999
A window is flagged when hiss floor > -58 dBFS with flatness > 0.35, or click > 0, or clip > 0, or flux spikes > 0.
Prints only flagged windows (plus a summary) so it reads as a spot list; --all prints every window."""
import sys, json, numpy as np, librosa
from scipy.signal import butter, sosfiltfilt
SR = 48000; FR = int(0.05 * SR)
a = sys.argv[1:]
g = lambda k, d: type(d)(a[a.index(k) + 1]) if k in a else d
WIN, CUES, TLF, ALL = g("--win", 0.5), g("--cues", ""), g("--timeline", ""), "--all" in a
skip = {"--win", "--cues", "--timeline"}
files = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] not in skip)]
onsets = []
if CUES:
    d = json.load(open(CUES)); onsets = [p["t"] for p in d["placed"]]
rows = [(r["id"], r["start"], r["start"] + r["dur"]) for r in json.load(open(TLF))["rows"]] if TLF else []
def row_at(t):
    for rid, s, e in rows:
        if s <= t < e: return rid
    return ""
def db(x): return float(20 * np.log10(max(float(x), 1e-9)))
for f in files:
    y, _ = librosa.load(f, sr=SR, mono=True)
    yb = sosfiltfilt(butter(4, [6000, 16000], btype="band", fs=SR, output="sos"), y)
    n = len(y) // FR
    fr_b = np.sqrt((yb[:n * FR].reshape(n, FR) ** 2).mean(1) + 1e-18)
    S = np.abs(librosa.stft(y, n_fft=1024, hop_length=256)); hop_t = 256 / SR
    flux = np.maximum(np.diff(S, axis=1), 0).sum(0); flux = np.concatenate([[0], flux])
    Sb = np.abs(librosa.stft(yb, n_fft=2048, hop_length=FR, center=False)); freqs = librosa.fft_frequencies(sr=SR, n_fft=2048)
    band = (freqs >= 6000) & (freqs <= 16000); flat = librosa.feature.spectral_flatness(S=Sb[band], power=1)[0]
    flat = np.pad(flat, (0, max(0, n - len(flat))), mode="edge")[:n]
    dy = np.abs(np.diff(y)); env = np.abs(y)
    per = int(WIN / 0.05); flagged = []; total = int(np.ceil(n / per))
    for w in range(total):
        sl = slice(w * per, min(n, (w + 1) * per)); a0, a1 = sl.start * FR, sl.stop * FR
        if a1 - a0 < FR: continue
        fb = fr_b[sl]; k = max(1, int(len(fb) * 0.1)); idx = np.argsort(fb)[:k]
        floor = db(np.sqrt((fb[idx] ** 2).mean())); fl = float(np.median(flat[sl][idx]))
        seg = dy[a0:a1 - 1]; big = np.where(seg > 0.25)[0]
        clicks = 0
        for i in big:   # a jump that is NOT inside a loud broadband onset (the 5 ms around it stays quiet)
            j = a0 + i; loc = env[max(0, j - 240):j + 240]
            if np.median(loc) < 0.08: clicks += 1
        clip = int((env[a0:a1] >= 0.999).sum())
        fi0, fi1 = int(a0 / SR / hop_t), int(a1 / SR / hop_t); fx = flux[fi0:fi1]; med = np.median(flux) + 1e-9
        spikes = 0
        for i in np.where(fx > 6 * med)[0]:
            t = (fi0 + i) * hop_t
            if not any(abs(t - o) < 0.08 for o in onsets): spikes += 1
        hiss = floor > -58 and fl > 0.35
        t0 = a0 / SR
        if hiss or clicks or clip or spikes or ALL:
            flagged.append((t0, row_at(t0 + 0.1), floor, fl, clicks, spikes, clip, hiss))
    print(f"\n== {f}  windows {total}  flagged {sum(1 for x in flagged if (x[4] or x[5] or x[6] or x[7]))}")
    print("    t    row            hissfloor flat  clicks fluxspikes clipped  why")
    for t0, row, floor, fl, clicks, spikes, clip, hiss in flagged:
        why = ",".join(w for w, c in (("HISS", hiss), ("CLICK", clicks), ("FLUX", spikes), ("CLIP", clip)) if c)
        print(f"  {t0:5.1f}  {row:14s} {floor:8.1f} {fl:5.2f} {clicks:6d} {spikes:8d} {clip:8d}  {why}")
