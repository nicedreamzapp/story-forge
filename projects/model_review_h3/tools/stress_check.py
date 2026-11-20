"""Proper-noun stress check (11/03, Matt: "Hugging Face was sounding way too much").
For every run of proper-noun tokens, RMS loudness (dB) and median F0 (semitones) vs the up-to-4 non-proper words on
each side in the same line. FLAG if > +4 dB or > +3 st hotter. Also prints whole-film F0 std-dev.
Usage: ~/chatterbox-env/bin/python tools/stress_check.py [lines...]"""
import json, re, sys
import numpy as np, librosa, soundfile as sf
from pathlib import Path
F = Path(__file__).resolve().parent.parent
W = json.loads((F / "vo/words.json").read_text())
PROPER = {"hugging", "face", "minimax", "h3", "kandinsky", "6", "pro", "ltx", "mlx", "comfy", "ui", "california",
          "european", "union", "united", "kingdom", "korea", "states", "mit", "m5", "max", "apache"}
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
only = {int(x) for x in sys.argv[1:]}
allf0 = []; flags = 0; rows = []
for ln in W["lines"]:
    L = ln["line"]
    y, sr = sf.read(F / ln["wav"]); y = y.mean(1) if y.ndim > 1 else y
    f0, vf, _ = librosa.pyin(y.astype(float), fmin=60, fmax=400, sr=sr, frame_length=2048, hop_length=512)
    t = librosa.times_like(f0, sr=sr, hop_length=512)
    good = vf & ~np.isnan(f0); allf0.append(f0[good])
    ws = [w for w in W["words"] if w["line"] == L]
    off = ln["start"]
    def seg(a, b):
        i, j = int(max(0, a - off) * sr), int(max(0, b - off) * sr); return y[i:j]
    def rms(spans):
        x = np.concatenate([seg(a, b) for a, b in spans]) if spans else np.zeros(1)
        return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
    def f0med(spans):
        m = np.zeros_like(t, bool)
        for a, b in spans: m |= (t >= a - off) & (t <= b - off)
        v = f0[m & good]; return float(np.median(v)) if len(v) else None
    k = 0
    while k < len(ws):
        if norm(ws[k]["word"]) in PROPER:
            j = k
            while j + 1 < len(ws) and norm(ws[j + 1]["word"]) in PROPER: j += 1
            phrase = " ".join(w["word"] for w in ws[k:j + 1])
            ctx = [w for w in ws[max(0, k - 4):k] + ws[j + 1:j + 5] if norm(w["word"]) not in PROPER]
            ps = [(w["start"], w["end"]) for w in ws[k:j + 1]]; cs = [(w["start"], w["end"]) for w in ctx]
            dd = rms(ps) - rms(cs)
            a, b = f0med(ps), f0med(cs)
            dst = 12 * np.log2(a / b) if a and b else float("nan")
            bad = dd > 4 or (dst == dst and dst > 3)
            flags += bad
            if not only or L in only:
                rows.append(f"{'FLAG' if bad else 'ok  '} line {L:2d} {phrase:28s} {dd:+5.1f} dB  {dst:+5.1f} st")
            k = j + 1
        else:
            k += 1
f = np.concatenate(allf0); s = 12 * np.log2(f / np.median(f)); p5, p95 = np.percentile(s, [5, 95])
print("\n".join(rows))
print(f"whole film F0 std {np.std(s):.2f} st, 5-95% range {p95 - p5:.2f} st, median {np.median(f):.0f} Hz; {flags} flagged")
