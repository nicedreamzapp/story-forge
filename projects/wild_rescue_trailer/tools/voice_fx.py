#!/usr/bin/env python3
"""Process + whisper-check + pitch-check the WILD RESCUE voice takes (run in ~/chatterbox-env). Picks ONE voice per
character (the candidate whose takes pass every line, then the best fit to the brief), copies the best take per line
to voices/<line>.wav and writes voices/voice_check.json.
Processing (character, not effects for their own sake):
  hank1  big bear: -1.5 st pitch (size), +3 dB low shelf at 160 Hz (chest), trimmed; no reverb (outdoors at the rim)
  doug1  "I picked a side." low and quiet, night forest: gentle 8 kHz low-pass, light gravel (soft tanh drive, 22% mix),
         small dark room 0.35 s at 10% (the forest), mixed later at a lower level
  doug2  bright, outdoors: +2 dB presence shelf at 3 kHz, light gravel 18%
Size/age check: median f0 (pyin). Hank must sit low (<= 115 Hz after processing, adult male bass/baritone);
Doug a bright adult male (115-185 Hz)."""
import json, re, shutil
import numpy as np, librosa, soundfile as sf, scipy.signal as ss
from pathlib import Path
P = Path(__file__).resolve().parent.parent
SR = 48000
TEXT = {"doug1": "I picked a side.", "doug2": "Then we need a lot of help.", "hank1": "Doug... that's a big hole."}
WHO = {"doug1": "doug", "doug2": "doug", "hank1": "hank"}
rng = np.random.default_rng(5)
def trim(y):
    yt, _ = librosa.effects.trim(y, top_db=38); return np.concatenate([np.zeros(int(0.03 * SR)), yt, np.zeros(int(0.08 * SR))])
def norm(y, peak=0.89): return y * (peak / (np.abs(y).max() + 1e-9))
def shelf(y, f, db, kind):
    sos = ss.butter(2, f / (SR / 2), btype="low" if kind == "low" else "high", output="sos")
    return y + (10 ** (db / 20) - 1) * ss.sosfiltfilt(sos, y)
def gravel(y, mix):
    d = np.tanh(3.0 * y / (np.abs(y).max() + 1e-9)); d = ss.sosfiltfilt(ss.butter(2, [300 / (SR / 2), 5000 / (SR / 2)], btype="band", output="sos"), d)
    return (1 - mix) * y + mix * d * (np.abs(y).max())
def room(y, sec, wet):
    n = int(sec * SR); t = np.arange(n) / SR
    r = ss.lfilter(*ss.butter(2, 2500 / (SR / 2)), rng.normal(0, 1, n)) * np.exp(-6.9 * t / sec); r[:int(0.012 * SR)] = 0
    r /= np.sqrt(np.sum(r ** 2)); w = np.zeros(len(y) + n); wc = ss.fftconvolve(y, r)[:len(y) + n]; w[:len(wc)] = wc
    return np.concatenate([y, np.zeros(n)]) + wet * w * (np.abs(y).max() / (np.abs(w).max() + 1e-9))
def process(line, y):
    y = trim(y)
    if line == "hank1":
        y = librosa.effects.pitch_shift(y, sr=SR, n_steps=-1.5); y = shelf(y, 160, 3, "low")
    elif line == "doug1":
        y = ss.sosfiltfilt(ss.butter(2, 8000 / (SR / 2), output="sos"), y); y = gravel(y, 0.22); y = room(y, 0.35, 0.10)
    else:
        y = shelf(y, 3000, 2, "high"); y = gravel(y, 0.18)
    return norm(y)
def f0(y):
    f, v, _ = librosa.pyin(librosa.resample(y, orig_sr=SR, target_sr=16000), fmin=50, fmax=400, sr=16000)
    f = f[~np.isnan(f)]; return float(np.median(f)) if len(f) else 0.0
import mlx_whisper
nt = lambda s: re.sub(r"[^a-z ]", " ", s.lower().replace("'", "")).split()
res = {}
(P / "voices/takes").mkdir(exist_ok=True)
for f in sorted((P / "voices/raw").glob("*.wav")):
    line, voice, k = f.stem.split("__")
    y, _ = librosa.load(f, sr=SR, mono=True)
    out = P / f"voices/takes/{f.stem}.wav"
    yp = process(line, y); sf.write(out, yp.astype(np.float32), SR, subtype="PCM_24")
    r = mlx_whisper.transcribe(str(out), path_or_hf_repo="mlx-community/whisper-large-v3-turbo", language="en", word_timestamps=True)
    heard = r.get("text", "").strip(); ok = nt(heard) == nt(TEXT[line])
    lp = float(np.mean([s.get("avg_logprob", -9) for s in r.get("segments", [])] or [-9]))
    words = [{"w": w["word"], "s": round(w["start"], 3), "e": round(w["end"], 3)} for s in r.get("segments", []) for w in s.get("words", [])]
    pitch = f0(yp)
    res[out.name] = {"line": line, "who": WHO[line], "voice": voice, "heard": heard, "match": ok, "avg_logprob": round(lp, 3),
                     "f0": round(pitch, 1), "dur": round(len(yp) / SR, 2), "words": words}
    print(out.name, ok, round(lp, 2), f"{pitch:.0f}Hz", f"{len(yp)/SR:.2f}s", repr(heard), flush=True)
FIT = {"hank": lambda p: p <= 115, "doug": lambda p: 115 <= p <= 185}
pick = {}
for who in ("hank", "doug"):
    lines = [l for l in TEXT if WHO[l] == who]; best = None
    for v in sorted({r["voice"] for r in res.values() if r["who"] == who}):
        tk = [r for r in res.values() if r["voice"] == v and r["who"] == who]
        if not all(any(r["match"] and r["line"] == l for r in tk) for l in lines): continue
        fit = np.mean([FIT[who](r["f0"]) for r in tk if r["match"]])
        lp = np.mean([max(r["avg_logprob"] for r in tk if r["match"] and r["line"] == l) for l in lines])
        score = 2 * fit + lp
        print(who, v, "fit", fit, "logprob", round(lp, 3), "score", round(score, 3))
        if best is None or score > best[0]: best = (score, v)
    if best: pick[who] = best[1]
best_take = {}
for l in TEXT:
    v = pick.get(WHO[l])
    cands = [(n, r) for n, r in res.items() if r["line"] == l and r["voice"] == v and r["match"]]
    if l == "hank1":   # slow: prefer the longer read among the clean ones
        cands.sort(key=lambda x: (x[1]["avg_logprob"] > -0.5, x[1]["dur"]), reverse=True)
    else:
        cands.sort(key=lambda x: x[1]["avg_logprob"], reverse=True)
    if cands:
        best_take[l] = cands[0][0]; shutil.copy(P / f"voices/takes/{cands[0][0]}", P / f"voices/{l}.wav")
json.dump({"takes": res, "voice_pick": pick, "best": best_take}, open(P / "voices/voice_check.json", "w"), indent=1)
print("voices:", pick, "best:", best_take, "missing:", [l for l in TEXT if l not in best_take])
