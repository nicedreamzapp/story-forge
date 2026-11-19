#!/usr/bin/env python3
"""voice_hi_v52.py — Matt 11/18 1:52 PM: "the bear's voice is different when it says hi and rolling". Young Hank's "Hi."
was the Hank take pitched +4 st (voices_fx 'young'). v5.2: SAME voice, SAME settings as L1 "Rolling." (wr3_hank,
exaggeration 0.35, cfg 0.3, seeds 101/303) and the SAME 'hank' processing (-1.5 st + 160 Hz shelf). Writes
voices/L4_hank_hi_s{seed}.wav and picks the shortest clean take as voices/L4_hank_hi.wav. Run in ~/chatterbox-env."""
import sys, torch, torchaudio, numpy as np, librosa, soundfile as sf, scipy.signal as ss
from pathlib import Path
sys.path.insert(0, str(Path.home() / "AI/videopipe/bin")); from character_voice import VOICES
from chatterbox.tts import ChatterboxTTS
P = Path(__file__).resolve().parent.parent; SR = 48000
def trim(y):
    yt, _ = librosa.effects.trim(y, top_db=38); return np.concatenate([np.zeros(int(0.03 * SR)), yt, np.zeros(int(0.10 * SR))])
def shelf(y, f, db):
    sos = ss.butter(2, f / (SR / 2), btype="low", output="sos"); return y + (10 ** (db / 20) - 1) * ss.sosfiltfilt(sos, y)
def hank(y): y = trim(y); y = librosa.effects.pitch_shift(y, sr=SR, n_steps=-1.5); y = shelf(y, 160, 3); return y * (0.89 / (np.abs(y).max() + 1e-9))
dev = "mps" if torch.backends.mps.is_available() else "cpu"
m = ChatterboxTTS.from_pretrained(device=dev); v = VOICES["wr3_hank"]; takes = []
for s in (101, 303, 505):
    torch.manual_seed(s); wav = m.generate("Hi.", exaggeration=0.35, cfg_weight=0.3, audio_prompt_path=v["ref"])
    raw = wav.squeeze().cpu().numpy() if hasattr(wav, "cpu") else np.asarray(wav).squeeze()
    y = librosa.resample(raw.astype(np.float32), orig_sr=m.sr, target_sr=SR); out = hank(y)
    f = P / f"voices/L4_hank_hi_s{s}.wav"; sf.write(f, out.astype(np.float32), SR, subtype="PCM_24")
    f0 = librosa.yin(out, fmin=50, fmax=400, sr=SR); takes.append((len(out) / SR, s, f)); print(f"{f.name} {len(out)/SR:.2f}s f0~{np.median(f0):.0f} Hz", flush=True)
good = [t for t in takes if t[0] <= 1.2] or takes
best = min(good)[2]; import shutil; shutil.copy(best, P / "voices/L4_hank_hi.wav"); print("pick:", best.name)
