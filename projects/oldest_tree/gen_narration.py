#!/usr/bin/env python3
"""Nia narration for The Oldest Tree — one ChatterBox load for every line.
Named gen_narration.py on purpose: forge_guard maps that cmdline to the chatterbox-narr lease."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path.home() / "SongForgeM5"))
import mem_client, torch, torchaudio
from chatterbox.tts import ChatterboxTTS
P = Path(__file__).resolve().parent
REF = str(Path.home() / "Desktop/PROJECTS/story-forge/voices/nia.wav")
lines = json.load(open(P / "narration.json"))
with mem_client.reserve("chatterbox-narr oldest_tree", 8):
    m = ChatterboxTTS.from_pretrained(device="mps")
    for ln in lines:
        out = P / "voices" / f"nia_{ln['id']}.wav"
        if out.exists():
            continue
        torch.manual_seed(ln.get("seed", 0))
        wav = m.generate(ln["text"], audio_prompt_path=REF, exaggeration=ln.get("ex", 0.5), cfg_weight=0.4)
        torchaudio.save(str(out), wav.cpu(), m.sr)
        print("done", out.name, flush=True)
