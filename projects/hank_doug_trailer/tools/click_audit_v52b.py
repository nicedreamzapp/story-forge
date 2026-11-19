#!/usr/bin/env python3
"""click_audit_v52b.py MIX.wav [--stems a.wav b.wav ...] [--cues final/mix_cues_v52.json] [--timeline tools/timeline_v52.json]
v5.2 static + scratching finder, per 0.5 s window of the DELIVERED mix, each hit traced to the stem that carries it.
  HISS  : the window is quiet (rms < -28 dBFS) AND its 6-16 kHz floor (10th-percentile of 50 ms frames) is above -58 dBFS AND that
          floor is noise-like (spectral flatness > 0.5). Loud passages are not hiss by this test (cymbals/brass ARE 6-16 kHz content);
          the music take's own quiet-frame floor is reported separately (anthem_9: -80.7 dBFS vs the old theme's -58.0).
  CLICK : sample-to-sample jumps > 0.25 FS while the 10 ms around them sits under 0.08 (digital clicks / crackle, not transients
          inside a loud onset).
  FLUX  : spectral-flux spikes > 8x the LOCAL (+-2 s) median that are not within 80 ms of a placed cue/line onset or a row cut.
  CLIP  : samples at/over 0.999 FS.
For every flagged window the same test runs on each stem and the stem(s) that flag are named. Prints flagged windows + a summary."""
import sys, json, numpy as np, librosa
from scipy.signal import butter, sosfiltfilt
SR = 48000; FR = int(0.05 * SR)
a = sys.argv[1:]; g = lambda k, d: type(d)(a[a.index(k) + 1]) if k in a else d
CUES, TLF = g("--cues", ""), g("--timeline", "")
stems = a[a.index("--stems") + 1:] if "--stems" in a else []
stems = [s for s in stems if not s.startswith("--")]
mixf = a[0]
onsets = [p["t"] for p in json.load(open(CUES))["placed"]] if CUES else []
rows = [(r["id"], r["start"], r["start"] + r["dur"]) for r in json.load(open(TLF))["rows"]] if TLF else []
onsets += [s for _, s, _ in rows]
def row_at(t):
    for rid, s, e in rows:
        if s <= t < e: return rid
    return ""
def analyse(f):
    y, _ = librosa.load(f, sr=SR, mono=True)
    yb = sosfiltfilt(butter(4, [6000, 16000], btype="band", fs=SR, output="sos"), y)
    n = len(y) // FR; fr_b = np.sqrt((yb[:n * FR].reshape(n, FR) ** 2).mean(1) + 1e-18); fr_a = np.sqrt((y[:n * FR].reshape(n, FR) ** 2).mean(1) + 1e-18)
    S = np.abs(librosa.stft(y, n_fft=1024, hop_length=256)); hop_t = 256 / SR
    flux = np.concatenate([[0], np.maximum(np.diff(S, axis=1), 0).sum(0)])
    Sb = np.abs(librosa.stft(yb, n_fft=2048, hop_length=FR, center=False)); freqs = librosa.fft_frequencies(sr=SR, n_fft=2048)
    band = (freqs >= 6000) & (freqs <= 16000); flat = librosa.feature.spectral_flatness(S=Sb[band], power=1)[0]
    flat = np.pad(flat, (0, max(0, n - len(flat))), mode="edge")[:n]
    dy = np.abs(np.diff(y)); env = np.abs(y); per = 10; res = {}
    for w in range(int(np.ceil(n / per))):
        sl = slice(w * per, min(n, (w + 1) * per)); a0, a1 = sl.start * FR, sl.stop * FR
        if a1 - a0 < FR: continue
        fb = fr_b[sl]; k = max(1, int(len(fb) * 0.1)); idx = np.argsort(fb)[:k]
        floor = 20 * np.log10(np.sqrt((fb[idx] ** 2).mean())); fl = float(np.median(flat[sl][idx])); rms = 20 * np.log10(np.sqrt((fr_a[sl] ** 2).mean()))
        clicks = 0
        for i in np.where(dy[a0:a1 - 1] > 0.25)[0]:
            j = a0 + i
            if np.median(env[max(0, j - 240):j + 240]) < 0.08: clicks += 1
        clip = int((env[a0:a1] >= 0.999).sum())
        fi0, fi1 = int(a0 / SR / hop_t), int(a1 / SR / hop_t); loc = flux[max(0, fi0 - int(2 / hop_t)):fi1 + int(2 / hop_t)]; med = np.median(loc) + 1e-9
        spikes = sum(1 for i in np.where(flux[fi0:fi1] > 8 * med)[0] if not any(abs((fi0 + i) * hop_t - o) < 0.08 for o in onsets))
        hiss = rms < -28 and floor > -58 and fl > 0.5
        res[round(a0 / SR, 1)] = dict(floor=float(floor), flat=fl, rms=float(rms), clicks=clicks, spikes=spikes, clip=clip, hiss=hiss)
    return res
mix = analyse(mixf); st = {s: analyse(s) for s in stems}
flag = lambda r: r["hiss"] or r["clicks"] or r["clip"] or r["spikes"]
bad = [(t, r) for t, r in mix.items() if flag(r)]
print(f"== {mixf}  windows {len(mix)}  flagged {len(bad)}  (HISS {sum(r['hiss'] for _, r in bad)}, CLICK {sum(1 for _, r in bad if r['clicks'])}, FLUX {sum(1 for _, r in bad if r['spikes'])}, CLIP {sum(1 for _, r in bad if r['clip'])})")
print("    t    row            rms  hissfloor flat  clicks flux clip  why            stem(s)")
for t, r in bad:
    why = ",".join(w for w, c in (("HISS", r["hiss"]), ("CLICK", r["clicks"]), ("FLUX", r["spikes"]), ("CLIP", r["clip"])) if c)
    src = [s.split("/")[-1].replace(".wav", "") for s, sr in st.items() if t in sr and (sr[t]["clicks"] or sr[t]["spikes"] or sr[t]["hiss"] or sr[t]["clip"])]
    print(f"  {t:5.1f}  {row_at(t + 0.1):14s} {r['rms']:6.1f} {r['floor']:8.1f} {r['flat']:5.2f} {r['clicks']:6d} {r['spikes']:4d} {r['clip']:4d}  {why:14s} {' '.join(src)}")
