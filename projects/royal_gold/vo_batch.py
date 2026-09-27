#!/usr/bin/env python3
"""Batch-render all Royal Gold narration lines in ONE model load (Matt's cloned voice)."""
from pathlib import Path
import torch, torchaudio
from chatterbox.tts import ChatterboxTTS

REF = str(Path.home() / "Desktop" / "PROJECTS" / "story-forge" / "voices" / "voice2_matt.wav")
OUT = Path.home() / "Desktop/PROJECTS/story-forge/projects/royal_gold/vo"
OUT.mkdir(parents=True, exist_ok=True)

LINES = {
    "L1": "This is Royal Gold.",
    "L2": "Born in the heart of Humboldt, where care for the craft meets a love for the land.",
    "L3": "Every blend begins with sustainably sourced coco fiber. Ground, rinsed, and perfected by hand.",
    "L4": "Premium soil, coco, and fertilizer. For growers who refuse to settle.",
    "L5": "Give your growing the royal treatment, and watch it prosper.",
    "L6": "Crafted our way, in Humboldt. Every single batch.",
    "L7": "Royal Gold. The gold standard in gardening.",
}

dev = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"[vo] loading ChatterBox on {dev} ...", flush=True)
m = ChatterboxTTS.from_pretrained(device=dev)
# measured, confident commercial-narration delivery
EX, CFG = 0.5, 0.5
for tag, line in LINES.items():
    torch.manual_seed(0)
    wav = m.generate(line, exaggeration=EX, cfg_weight=CFG, audio_prompt_path=REF)
    p = OUT / f"{tag}.wav"
    torchaudio.save(str(p), wav.cpu() if hasattr(wav, "cpu") else wav, m.sr)
    print(f"[vo] {tag} -> {p}", flush=True)
print("[vo] DONE", flush=True)
