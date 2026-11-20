"""Score every take: whisper text match, pitch (yin median on voiced frames), length. Pick best text match, then
pitch nearest the character's target. Writes scores.json + picks.json."""
import json, glob, os, re, difflib, numpy as np, soundfile as sf, mlx_whisper, librosa
V = os.path.dirname(os.path.abspath(__file__)); LINES = json.load(open(f"{V}/lines.json"))
TARGET = {"claire": 200, "ruth": 190, "lily": 290, "daniel": 300, "rememberer": 105}
norm = lambda s: re.sub(r"[^a-z ]", "", s.lower()).split()
res = {}
for f in sorted(glob.glob(f"{V}/pieces/*.wav")):
    n = os.path.basename(f); lid = n.split("_")[0]
    y, r = sf.read(f); y = y.mean(1) if y.ndim > 1 else y
    w = mlx_whisper.transcribe(f, path_or_hf_repo="mlx-community/whisper-large-v3-turbo", language="en", word_timestamps=True)
    tm = difflib.SequenceMatcher(None, norm(w["text"]), norm(LINES[lid][1])).ratio()
    f0, vf, _ = librosa.pyin(y.astype(np.float32), fmin=60, fmax=600, sr=r); f0 = f0[vf] if vf.any() else np.array([0])
    res[n] = {"id": lid, "dur": round(len(y) / r, 2), "text": round(tm, 3), "f0": round(float(np.nanmedian(f0)), 1), "asr": w["text"].strip()}
    print(n, res[n], flush=True)
json.dump(res, open(f"{V}/scores.json", "w"), indent=1)
pick = {}
for lid, (ch, _) in LINES.items():
    c = [(n, v) for n, v in res.items() if v["id"] == lid]
    best = max(c, key=lambda nv: nv[1]["text"] * 3 - abs(nv[1]["f0"] - TARGET[ch]) / TARGET[ch])
    pick[lid] = best[0]; print("PICK", lid, best)
json.dump(pick, open(f"{V}/picks.json", "w"), indent=1)
