#!/usr/bin/env python3
"""Process + whisper-check the voice takes (run in ~/chatterbox-env). Writes voices/<who>_t<k>.wav (processed, 48 kHz
mono) and voices/voice_check.json; the best passing take per line is copied to voices/<who>.wav.
  computer: trimmed, band-limited 120 Hz-8 kHz, a 14 ms doubled layer and a small room (0.5 s): a calm ship AI
  planet:   main layer pitched -4 st, an octave-below layer (-16 st) at -5 dB, a faint +7 st air layer at -20 dB,
            then a 4 s cathedral-scale reverb (60% wet): deep, layered, from everywhere (spread 1.0 in the mix)
  captain:  whisperized (STFT magnitude kept, phase randomized = breath instead of voicing) 85% + 15% dry for
            intelligibility, gentle low-pass, no reverb (intimate, close)"""
import json, re, shutil
import numpy as np, librosa, soundfile as sf, scipy.signal as ss
from pathlib import Path
P = Path(__file__).resolve().parent.parent
SR = 48000
TEXT = {"computer": "Uncharted.", "planet": "Welcome back, Captain.", "captain": "I've never been here."}
rng = np.random.default_rng(5)
def trim(y): 
    yt, _ = librosa.effects.trim(y, top_db=38); return yt
def ir(sec, pre=0.02, bright=0.5):
    n = int(sec * SR); t = np.arange(n) / SR
    noise = rng.normal(0, 1, (n,))
    e = np.exp(-6.9 * t / sec)
    b, a = ss.butter(2, 3000 * bright / (SR / 2))
    r = ss.lfilter(b, a, noise) * e
    r[:int(pre * SR)] = 0; r[0] = 0
    return r / np.sqrt(np.sum(r ** 2))
def bp(y, lo, hi):
    sos = ss.butter(4, [lo / (SR / 2), hi / (SR / 2)], btype="band", output="sos"); return ss.sosfiltfilt(sos, y)
def norm(y, peak=0.89): return y * (peak / (np.abs(y).max() + 1e-9))
def process(who, y):
    y = trim(y)
    if who == "computer":
        y = bp(y, 120, 8000)
        d = int(0.014 * SR); dbl = np.concatenate([np.zeros(d), y])[:len(y)]
        y = y + 0.35 * dbl
        n = len(y) + int(0.5 * SR)
        wet = np.zeros(n); w = ss.fftconvolve(y, ir(0.5, bright=0.8))[:n]; wet[:len(w)] = w
        y = np.concatenate([y, np.zeros(int(0.5 * SR))]) + 0.18 * wet
    elif who == "planet":
        main = librosa.effects.pitch_shift(y, sr=SR, n_steps=-4)
        low = librosa.effects.pitch_shift(y, sr=SR, n_steps=-16)
        air = librosa.effects.pitch_shift(y, sr=SR, n_steps=7)
        dry = main + 0.56 * low + 0.1 * air
        tail = int(4.0 * SR)
        n = len(dry) + tail
        wet = np.zeros(n); w = ss.fftconvolve(dry, ir(4.0, pre=0.04, bright=0.35))[:n]; wet[:len(w)] = w
        dry = np.concatenate([dry, np.zeros(tail)])
        y = 0.62 * dry + 0.6 * wet * (np.abs(dry).max() / (np.abs(wet).max() + 1e-9))
    elif who == "captain":
        S = librosa.stft(y, n_fft=1024, hop_length=256)
        ph = np.exp(1j * rng.uniform(-np.pi, np.pi, S.shape))
        wh = librosa.istft(np.abs(S) * ph, hop_length=256, length=len(y))
        y = 0.85 * norm(wh) + 0.15 * norm(y)
        sos = ss.butter(2, 7000 / (SR / 2), output="sos"); y = ss.sosfiltfilt(sos, y)
    return norm(y)
import mlx_whisper
res = {}
for f in sorted((P / "voices/raw").glob("*.wav")):
    who, k = f.stem.rsplit("_t", 1)
    y, _ = librosa.load(f, sr=SR, mono=True)
    out = P / f"voices/{who}_t{k}.wav"
    sf.write(out, process(who, y).astype(np.float32), SR, subtype="PCM_24")
    r = mlx_whisper.transcribe(str(out), path_or_hf_repo="mlx-community/whisper-large-v3-turbo", language="en", word_timestamps=True)
    heard = r.get("text", "").strip()
    norm_t = lambda s: re.sub(r"[^a-z ]", "", s.lower().replace("'", "")).split()
    ok = norm_t(heard) == norm_t(TEXT[who])
    lp = float(np.mean([s.get("avg_logprob", -9) for s in r.get("segments", [])] or [-9]))
    words = [{"w": w["word"], "s": round(w["start"], 3), "e": round(w["end"], 3)} for s in r.get("segments", []) for w in s.get("words", [])]
    res[out.name] = {"who": who, "heard": heard, "match": ok, "avg_logprob": round(lp, 3), "dur": round(len(sf.read(out)[0]) / SR, 2), "words": words}
    print(out.name, ok, round(lp, 2), repr(heard), flush=True)
best = {}
for name, r in res.items():
    if r["match"] and (r["who"] not in best or r["avg_logprob"] > res[best[r["who"]]]["avg_logprob"]):
        best[r["who"]] = name
for who, name in best.items():
    shutil.copy(P / f"voices/{name}", P / f"voices/{who}.wav")
json.dump({"takes": res, "best": best}, open(P / "voices/voice_check.json", "w"), indent=1)
print("best:", best, "missing:", [w for w in TEXT if w not in best])
