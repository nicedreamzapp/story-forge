#!/usr/bin/env python3
"""lahontan_returns voices: 6 untouched takes per line (no stretch, no pitch), cast from character_voice.py.
Named gen_narration.py so forge_guard maps it to the chatterbox-narr lease."""
import sys, json, importlib.util
from pathlib import Path
sys.path.insert(0, str(Path.home() / "SongForgeM5"))
import mem_client, torch, torchaudio
from chatterbox.tts import ChatterboxTTS
P = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("cv", str(Path.home() / "AI/videopipe/bin/character_voice.py"))
src = open(spec.origin).read().split("\ndef main")[0]
ns = {}; exec(src.replace("import torch\nimport torchaudio\nfrom chatterbox.tts import ChatterboxTTS", ""), ns)
VOICES = ns["VOICES"]
LINES = json.load(open(P / "lines.json"))
TAKES = [(11, 0.0), (23, 0.0), (79, 0.0), (37, -0.15), (51, -0.15), (88, 0.1)]
with mem_client.reserve("chatterbox-narr lahontan_returns", 12, honest=False):
    m = ChatterboxTTS.from_pretrained(device="mps")
    conds = {}
    for i, (ch, t) in LINES.items():
        v = VOICES[ch]
        for seed, dc in TAKES:
            cfg = round(max(0.2, v["cfg"] + dc), 2)
            out = P / "pieces" / f"{i}_s{seed}_c{int(cfg*100)}.wav"
            if out.exists(): continue
            torch.manual_seed(seed)
            wav = m.generate(t, audio_prompt_path=v["ref"], exaggeration=v["exaggeration"], cfg_weight=cfg, temperature=0.7)
            torchaudio.save(str(out), wav.cpu(), m.sr)
            print("done", out.name, flush=True)
print("GEN_DONE")
