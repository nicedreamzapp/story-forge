#!/usr/bin/env python3
"""Process the picked takes (same character processing as v1's voice_fx): Hank -1.5 st + 160 Hz chest shelf; Young Hank =
the Hank take pitched +4 st, softer, no shelf (never a new voice); Doug V.O. gentle 8 kHz low-pass, light gravel, small room.
Writes voices/<line>.wav (48 kHz mono) and voices/alt/ for the alternate take. Run in ~/chatterbox-env."""
import numpy as np, librosa, soundfile as sf, scipy.signal as ss, shutil
from pathlib import Path
P = Path(__file__).resolve().parent.parent; SR = 48000
PICK = {"L1_hank_rolling": ("s101", "s303", "hank"), "L2_doug_longago": ("s303", "s101", "doug_vo"),
        "L3_doug_metone": ("s101", "s303", "doug_vo"), "L4_younghank_hi": ("s303", None, "young"),
        "L5_doug_samenose": ("s303", None, "doug_vo"), "L6_hank_rolling2": ("s303", "s101", "hank"),
        "N1_narrator_heart": ("s10", None, "narr")}
def trim(y):
    yt, _ = librosa.effects.trim(y, top_db=38); return np.concatenate([np.zeros(int(0.03 * SR)), yt, np.zeros(int(0.10 * SR))])
def norm(y, peak=0.89): return y * (peak / (np.abs(y).max() + 1e-9))
def shelf(y, f, db):
    sos = ss.butter(2, f / (SR / 2), btype="low", output="sos"); return y + (10 ** (db / 20) - 1) * ss.sosfiltfilt(sos, y)
def gravel(y, mix):
    d = np.tanh(3.0 * y / (np.abs(y).max() + 1e-9)); d = ss.sosfiltfilt(ss.butter(2, [300 / (SR / 2), 5000 / (SR / 2)], btype="band", output="sos"), d)
    return (1 - mix) * y + mix * d * (np.abs(y).max())
def room(y, sec, wet):
    rng = np.random.default_rng(5); n = int(sec * SR); t = np.arange(n) / SR
    r = ss.lfilter(*ss.butter(2, 2500 / (SR / 2)), rng.normal(0, 1, n)) * np.exp(-6.9 * t / sec); r[:int(0.012 * SR)] = 0
    r /= np.sqrt(np.sum(r ** 2)); wc = np.zeros(len(y) + n); c = ss.fftconvolve(y, r)[:len(y) + n]; wc[:len(c)] = c
    return np.concatenate([y, np.zeros(n)]) + wet * wc * (np.abs(y).max() / (np.abs(wc).max() + 1e-9))
def process(kind, y):
    y = trim(y)
    if kind == "hank": y = librosa.effects.pitch_shift(y, sr=SR, n_steps=-1.5); y = shelf(y, 160, 3)
    elif kind == "young": y = librosa.effects.pitch_shift(y, sr=SR, n_steps=4.0); y = ss.sosfiltfilt(ss.butter(2, 9000 / (SR / 2), output="sos"), y); y = norm(y, 0.6); return y
    elif kind == "doug_vo": y = ss.sosfiltfilt(ss.butter(2, 8000 / (SR / 2), output="sos"), y); y = gravel(y, 0.18); y = room(y, 0.35, 0.08)
    return norm(y)
(P / "voices/alt").mkdir(exist_ok=True)
for line, (pick, alt, kind) in PICK.items():
    for tag, dest in ((pick, P / f"voices/{line}.wav"), (alt, P / f"voices/alt/{line}_alt.wav")):
        if not tag: continue
        src = P / f"voices/raw/{line}_{tag}.wav"
        y, _ = librosa.load(src, sr=SR, mono=True)
        out = process(kind, y)
        sf.write(dest, out.astype(np.float32), SR, subtype="PCM_24")
        f0 = librosa.yin(out, fmin=50, fmax=400, sr=SR)
        print(f"{dest.relative_to(P)} {len(out)/SR:.2f}s median f0 ~{np.median(f0) if len(f0) else 0:.0f} Hz")
shutil.rmtree(P / "voices/raw")
print("raw takes removed (picks + alts kept)")
