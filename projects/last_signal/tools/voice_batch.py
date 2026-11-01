#!/usr/bin/env python3
"""Voice takes for THE LAST SIGNAL, ChatterBox loaded ONCE (casting from bin/character_voice.py's VOICES table):
  computer = voiceA (spare pool, f0 ~167 Hz, calm), exaggeration 0.25 for a flat neutral read
  planet   = voiceB (spare pool, f0 ~103 Hz, deep male), later pitched down + octave-stacked + big reverb
  captain  = ruby (woman, 46-55 per EARS metadata, f0 ~177 Hz), soft read, later whisperized
3 takes each (different seeds) into voices/raw/; tools/voice_fx.py processes and whisper-checks them."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path.home() / "AI/videopipe/bin")); sys.path.insert(0, str(Path.home() / "SongForgeM5"))
import torch, torchaudio
from character_voice import VOICES
from chatterbox.tts import ChatterboxTTS
try:
    from mem_client import reserve
except Exception:
    from contextlib import nullcontext; reserve = lambda n, g: nullcontext()
P = Path(__file__).resolve().parent.parent
LINES = [
 ("computer", "voiceA", "Uncharted.", 0.25, 0.5),
 ("planet", "voiceB", "Welcome back, Captain.", 0.45, 0.35),
 ("captain", "ruby", "I've never been here.", 0.3, 0.3),
]
with reserve("chatterbox-voices", 8):
    m = ChatterboxTTS.from_pretrained(device="mps" if torch.backends.mps.is_available() else "cpu")
    for who, voice, line, ex, cfg in LINES:
        for k, seed in enumerate((101, 202, 303), 1):
            out = P / f"voices/raw/{who}_t{k}.wav"
            if out.exists(): continue
            torch.manual_seed(seed)
            wav = m.generate(line, audio_prompt_path=VOICES[voice]["ref"], exaggeration=ex, cfg_weight=cfg)
            torchaudio.save(str(out), wav.cpu(), m.sr)
            print(who, k, out.name, flush=True)
