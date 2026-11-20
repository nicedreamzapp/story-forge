#!/usr/bin/env python3
"""Matt avatar story narration, ChatterBox + matt_real_ref.wav, no pitch-down. One load for every line.
Named gen_narration.py on purpose: forge_guard maps that cmdline to the chatterbox-narr lease.
Usage: gen_narration.py [id:seed ...]  (re-roll given ids with new seeds; others skip if present)"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path.home() / "SongForgeM5"))
import mem_client, torch, torchaudio
from chatterbox.tts import ChatterboxTTS
P = Path(__file__).resolve().parent
REF = str(Path.home() / "Desktop/PROJECTS/avatar-assets/matt-inputs/matt_real_ref.wav")
import os
LF = os.environ.get("NARR_LINES", "lines.json"); PD = os.environ.get("NARR_PIECES", "pieces")
lines = json.load(open(P / LF))
reroll = dict(a.split(":") for a in sys.argv[1:])
with mem_client.reserve("chatterbox-narr matt-story", 12, honest=False):
    m = ChatterboxTTS.from_pretrained(device="mps")
    for ln in lines:
        out = P / PD / f"l{ln['id']}.wav"
        if out.exists() and ln["id"] not in reroll:
            continue
        seed = int(reroll.get(ln["id"], 7))
        torch.manual_seed(seed)
        wav = m.generate(ln["text"], audio_prompt_path=REF, exaggeration=ln.get("ex", 0.5),
                         cfg_weight=0.5, temperature=0.75)
        torchaudio.save(str(out), wav.cpu(), m.sr)
        print("done", out.name, "seed", seed, flush=True)
print("GEN_DONE")
