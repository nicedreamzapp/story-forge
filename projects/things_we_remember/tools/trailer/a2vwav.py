"""a2v driving wavs: 0.35 s lead-in + the picked trimmed line, padded to the shot length + 0.5 s (teaser L01_a2v recipe)."""
import sys, numpy as np, soundfile as sf
from pathlib import Path
V = Path(__file__).resolve().parents[2] / "voice"
for arg in sys.argv[1:]:
    shot, lid, ln = arg.split(":"); y, r = sf.read(str(V / "trimmed" / f"{lid}.wav")); y = y.mean(1) if y.ndim > 1 else y
    n = int((float(ln) + .5) * r); out = np.zeros(max(n, int(.35 * r) + len(y) + int(.2 * r)))
    out[int(.35 * r): int(.35 * r) + len(y)] = y; sf.write(str(V / f"{shot}_a2v.wav"), out, r); print(shot, round(len(out) / r, 2))
