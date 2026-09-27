#!/usr/bin/env python3
"""Royal Gold VO — Piper speaker 0, rendered ONE SENTENCE PER FILE then concatenated
(frozen Story Forge rule). Multi-sentence input made Piper emit a loud static tail."""
import subprocess, wave, re
from pathlib import Path

PIPER = str(Path.home() / "Library/Python/3.9/bin/piper")
MODEL = str(Path.home() / "Desktop/PROJECTS/Song Forge/piper_voices/en_US-libritts_r-medium.onnx")
OUT = Path.home() / "Desktop/PROJECTS/story-forge/projects/royal_gold/vo"
OUT.mkdir(parents=True, exist_ok=True)
SR = 22050
SIL = b"\x00\x00" * int(SR * 0.14)   # 0.14s between sentences

LINES = {
    "1": "This is Royal Gold.",
    "2": "Born in the heart of Humboldt, where care for the craft meets a love for the land.",
    "3": "Every blend begins with sustainably sourced coco fiber, ground, rinsed, and perfected by hand.",
    "4": "Premium soil, coco, and fertilizer, for growers who refuse to settle.",
    "5": "Give your growing the royal treatment, and watch it prosper.",
    "6": "Crafted our way, in Humboldt. Every single batch.",
    "7": "Royal Gold. The gold standard in gardening.",
}

def say(text, path):
    subprocess.run([PIPER, "--model", MODEL, "--speaker", "0", "--length-scale", "1.0",
                    "--noise-scale", "0.4", "--noise-w", "0.55", "--output_file", path],
                   input=text, text=True, check=True, capture_output=True)

for tag, line in LINES.items():
    sents = [s.strip() for s in re.findall(r"[^.]*\.", line) if s.strip()] or [line]
    frames = b""
    for i, s in enumerate(sents):
        tmp = f"/tmp/vo_{tag}_{i}.wav"
        say(s, tmp)
        with wave.open(tmp, "rb") as w:
            fr = w.readframes(w.getnframes())
        if i > 0:
            frames += SIL
        frames += fr
    outp = OUT / f"P{tag}.wav"
    with wave.open(str(outp), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(frames)
    dur = len(frames) / 2 / SR
    print(f"P{tag}.wav  {dur:.3f}s  ({len(sents)} sentence(s))  bytes={44+len(frames)}")
