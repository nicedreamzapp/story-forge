#!/usr/bin/env python3
"""Brand-new reference clips for the WILD RESCUE cast (run in ~/kokoro-env). No earlier Hank & Doug voice is reused:
the old cast was ChatterBox's built-in voice (Hank), Matt's clone (Doug), spare voiceA/voiceB (circus_train bird/Ellie).
Kokoro-82M (local, MLX) speaks a ~10 s neutral passage in candidate voices; ChatterBox later clones the chosen one
through character_voice.py entries wr_hank / wr_doug. Candidates by the character brief:
  HANK, a big gentle bear, deep, slow, warm:     am_onyx, am_santa, bm_george  (speed 0.88)
  DOUG, a bloodhound, quick, bright, some gravel: am_puck, am_fenrir, am_echo, am_liam  (speed 1.05)"""
from pathlib import Path
from mlx_audio.tts.utils import load_model
import numpy as np
from scipy.io import wavfile
P = Path(__file__).resolve().parent.parent; O = P / "voices/refs"
TEXT = ("Out here the wind carries everything, the dust, the smell of rain, the sound of somebody who needs a hand. "
        "So you listen close, you keep your nose to the ground, and when the call comes, you go.")
C = {"hank": (["am_onyx", "am_santa", "bm_george"], 0.88), "doug": (["am_puck", "am_fenrir", "am_echo", "am_liam"], 1.05)}
m = load_model("prince-canuma/Kokoro-82M")
for who, (voices, speed) in C.items():
    for v in voices:
        out = O / f"{who}_{v}.wav"
        if out.exists(): continue
        chunks = [np.asarray(r.audio) for r in m.generate(text=TEXT, voice=v, speed=speed, lang_code="b" if v.startswith("b") else "a")]
        y = np.concatenate(chunks).astype(np.float32)
        wavfile.write(out, 24000, (y / (np.abs(y).max() + 1e-9) * 0.9).astype(np.float32))
        print(out.name, round(len(y) / 24000, 1), "s", flush=True)
