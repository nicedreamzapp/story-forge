#!/usr/bin/env python3
"""Hank & Doug trailer voices: ChatterBox loaded once, 2 takes per line (coverage), raw to voices/raw/.
Run in ~/chatterbox-env. Casting from character_voice.py: wr3_hank (bear, bass) / wr3_doug (older warm male).
Young Hank = the Hank voice, pitched a little higher and softer in tools/voices_fx.py (never a new voice)."""
import sys, torch, torchaudio
from pathlib import Path
sys.path.insert(0, str(Path.home() / "AI/videopipe/bin"))
from character_voice import VOICES
from chatterbox.tts import ChatterboxTTS
P = Path(__file__).resolve().parent.parent
RAW = P / "voices/raw"; RAW.mkdir(parents=True, exist_ok=True)
# line id, voice, text, exaggeration, cfg, seeds
LINES = [
 ("L1_hank_rolling",   "wr3_hank", "Rolling.",                                0.35, 0.3,  [101, 303]),
 ("L2_doug_longago",   "wr3_doug", "Long time ago... I hunted bears.",        0.3,  0.5,  [101, 303]),
 ("L3_doug_metone",    "wr3_doug", "Then I met one.",                         0.3,  0.5,  [101, 303]),
 ("L4_younghank_hi",   "wr3_hank", "Hi.",                                     0.6,  0.35, [101, 303, 505]),
 ("L5_doug_samenose",  "wr3_doug", "Same nose. Same light. Different job.",   0.45, 0.45, [101, 303]),
 ("L6_hank_rolling2",  "wr3_hank", "Rolling.",                                0.25, 0.3,  [101, 303]),
]
dev = "mps" if torch.backends.mps.is_available() else "cpu"
m = ChatterboxTTS.from_pretrained(device=dev)
for lid, who, text, ex, cfg, seeds in LINES:
    v = VOICES[who]
    for s in seeds:
        out = RAW / f"{lid}_s{s}.wav"
        if out.exists(): continue
        torch.manual_seed(s)
        wav = m.generate(text, exaggeration=ex, cfg_weight=cfg, audio_prompt_path=v["ref"])
        torchaudio.save(str(out), wav.cpu() if hasattr(wav, "cpu") else wav, m.sr)
        print(f"[voices] {out.name} {wav.shape[-1]/m.sr:.2f}s", flush=True)
print("[voices] done")
