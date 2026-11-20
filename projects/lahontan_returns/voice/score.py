"""Score every take: whisper text match + speaking rate (natural = near the speaker's median). Picks best per line."""
import json, glob, os, re, difflib, numpy as np, soundfile as sf, mlx_whisper
V = os.path.dirname(os.path.abspath(__file__))
LINES = json.load(open(f"{V}/lines.json"))
def trim(y, sr):
    h = int(sr * 0.01); e = np.array([np.sqrt(np.mean(y[k:k+h]**2)) for k in range(0, len(y) - h, h)])
    idx = np.where(e > 0.01)[0]; a = max(0, idx[0] * h - int(0.04 * sr)); b = min(len(y), (idx[-1] + 1) * h + int(0.08 * sr))
    return y[a:b]
norm = lambda s: re.sub(r"[^a-z0-9 ]", "", s.lower().replace("-", " ").replace("3 pm", "three p m").replace("p.m.", "p m")
                        .replace("13,000", "thirteen thousand").replace("400", "four hundred").replace("50", "fifty").replace("30", "thirty")).split()
import sys
IDS = set(sys.argv[1:])
res = json.load(open(f"{V}/scores.json")) if os.path.exists(f"{V}/scores.json") else {}
for f in sorted(glob.glob(f"{V}/pieces/*.wav")):
    n = os.path.basename(f); lid = n.split("_")[0]
    if (IDS and lid not in IDS) or n in res: continue
    y, r = sf.read(f); y = y.mean(1) if y.ndim > 1 else y; y = trim(y, r); t = f.replace("pieces", "trimmed"); sf.write(t, y, r)
    w = mlx_whisper.transcribe(t, path_or_hf_repo="mlx-community/whisper-large-v3-turbo", language="en", word_timestamps=True)
    hyp = norm(w["text"]); ref = norm(LINES[lid][1])
    tm = difflib.SequenceMatcher(None, hyp, ref).ratio()
    words = [x for s in w["segments"] for x in s["words"]]
    gaps = [b["start"] - a["end"] for a, b in zip(words, words[1:])]
    res[n] = {"id": lid, "dur": round(len(y)/r, 2), "wps": round(len(ref)/(len(y)/r), 2), "text": round(tm, 3),
              "maxgap": round(max(gaps) if gaps else 0, 2), "asr": w["text"].strip(), "words": [{"w": x["word"].strip(), "s": round(x["start"], 2), "e": round(x["end"], 2)} for x in words]}
    print(n, res[n]["wps"], res[n]["text"], res[n]["maxgap"], "|", res[n]["asr"], flush=True)
json.dump(res, open(f"{V}/scores.json", "w"), indent=1)
# pick: best text match, then rate closest to speaker median, penalise long internal pauses (except the scripted "just..." pause)
spk = {}
for n, v in res.items(): spk.setdefault(LINES[v["id"]][0], []).append(v["wps"])
med = {k: float(np.median(x)) for k, x in spk.items()}
pick = json.load(open(f"{V}/picks.json")) if os.path.exists(f"{V}/picks.json") else {}
for lid in LINES:
    c = [(n, v) for n, v in res.items() if v["id"] == lid]
    if len(c) < 6 or (IDS and lid not in IDS): continue
    m = med[LINES[lid][0]]
    def sc(nv):
        v = nv[1]; gp = max(0, v["maxgap"] - (1.2 if lid == "H02" else 0.6))
        return v["text"] * 3 - abs(v["wps"] - m) / m - gp
    best = max(c, key=sc); pick[lid] = best[0]
    print("PICK", lid, best[0], best[1]["text"], best[1]["wps"], "med", round(m, 2), "|", best[1]["asr"])
json.dump(pick, open(f"{V}/picks.json", "w"), indent=1)
