#!/usr/bin/env python3
"""Voice takes for WILD RESCUE, ChatterBox loaded ONCE. Audition pass: every candidate reference (voices/refs/, Kokoro)
speaks its character's lines, 2 seeds each; tools/voice_fx.py whisper-checks, measures pitch and picks one voice per
character, which is then registered in ~/AI/videopipe/bin/character_voice.py as wr_hank / wr_doug (same ref + settings,
so the picked takes ARE character_voice renders).
  DOUG line 1 "I picked a side."            low, quiet  -> exaggeration 0.3, cfg 0.5
  DOUG line 2 "Then we need a lot of help."  bright      -> exaggeration 0.6, cfg 0.45
  HANK        "Doug... that's a big hole."   slow, warm  -> exaggeration 0.45, cfg 0.3 (lower cfg = slower pacing)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / "SongForgeM5"))
import torch, torchaudio
from chatterbox.tts import ChatterboxTTS
try:
    from mem_client import reserve
except Exception:
    from contextlib import nullcontext; reserve = lambda n, g: nullcontext()
P = Path(__file__).resolve().parent.parent
LINES = {"doug": [("doug1", "I picked a side.", 0.3, 0.5), ("doug2", "Then we need a lot of help.", 0.6, 0.45)],
         "hank": [("hank1", "Doug... that's a big hole.", 0.45, 0.3)]}
with reserve("chatterbox-voices", 8):
    m = ChatterboxTTS.from_pretrained(device="mps" if torch.backends.mps.is_available() else "cpu")
    for ref in sorted((P / "voices/refs").glob("*.wav")):
        who, v = ref.stem.split("_", 1)
        for line_id, text, ex, cfg in LINES[who]:
            for k, seed in enumerate((101, 202), 1):
                out = P / f"voices/raw/{line_id}__{v}__t{k}.wav"
                if out.exists(): continue
                torch.manual_seed(seed)
                wav = m.generate(text, audio_prompt_path=str(ref), exaggeration=ex, cfg_weight=cfg)
                torchaudio.save(str(out), wav.cpu(), m.sr)
                print(out.name, flush=True)
