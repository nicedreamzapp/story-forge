"""Score + pick + trim only the NEW line ids (teaser picks untouched). Same rule as score.py. Run in chatterbox-env.
score_more.py lines_X.json"""
import json, glob, os, re, sys, difflib, numpy as np, soundfile as sf, mlx_whisper, librosa
V = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, V)
from gen_narration_cast import TARGET
LINES = json.load(open(sys.argv[1])); norm = lambda s: re.sub(r"[^a-z ]", "", s.lower()).split()
allL = json.load(open(f"{V}/lines.json")); allL.update(LINES); json.dump(allL, open(f"{V}/lines.json", "w"), indent=1)
scores = json.load(open(f"{V}/scores.json")); picks = json.load(open(f"{V}/picks.json"))
for lid, (ch, text) in LINES.items():
    c = []
    for f in sorted(glob.glob(f"{V}/pieces/{lid}_s*.wav")):
        n = os.path.basename(f); y, r = sf.read(f); y = y.mean(1) if y.ndim > 1 else y
        w = mlx_whisper.transcribe(f, path_or_hf_repo="mlx-community/whisper-large-v3-turbo", language="en")
        tm = difflib.SequenceMatcher(None, norm(w["text"]), norm(text)).ratio()
        f0, vf, _ = librosa.pyin(y.astype(np.float32), fmin=60, fmax=600, sr=r); f0 = f0[vf] if vf.any() else np.array([0])
        scores[n] = {"id": lid, "dur": round(len(y) / r, 2), "text": round(tm, 3), "f0": round(float(np.nanmedian(f0)), 1), "asr": w["text"].strip()}
        c.append((n, scores[n])); print(n, scores[n], flush=True)
    if lid in picks and os.path.exists(f"{V}/trimmed/{lid}.wav"): continue
    best = max(c, key=lambda nv: nv[1]["text"] * 3 - abs(nv[1]["f0"] - TARGET[ch]) / TARGET[ch])
    picks[lid] = best[0]; print("PICK", lid, best, flush=True)
    y, r = sf.read(f"{V}/pieces/{best[0]}"); _, (a, b) = librosa.effects.trim(y, top_db=38)
    a = max(0, a - int(.04 * r)); b = min(len(y), b + int(.08 * r)); sf.write(f"{V}/trimmed/{lid}.wav", y[a:b], r)
json.dump(scores, open(f"{V}/scores.json", "w"), indent=1); json.dump(picks, open(f"{V}/picks.json", "w"), indent=1)
print("SCORE_DONE")
