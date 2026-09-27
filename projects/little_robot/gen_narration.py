#!/usr/bin/env python3
"""Narration via Piper — proven story-forge recipe (speaker 0, warm storyteller).
One sentence per file (frozen rule 2), concat with silence gaps, per-scene wavs."""
import re, subprocess, wave, sys
from pathlib import Path

HOME = Path.home()
PROJ = HOME / "Desktop/PROJECTS/story-forge/projects/little_robot"
PIPER = HOME / "Library/Python/3.9/bin/piper"
MODEL = HOME / "Desktop/PROJECTS/Song Forge/piper_voices/en_US-libritts_r-medium.onnx"
AUDIO = PROJ / "audio"
PIECES = AUDIO / "vo_pieces"
PIECES.mkdir(parents=True, exist_ok=True)
GAP = 0.7  # seconds between sentences

scenes = {}
cur = None
for raw in (PROJ / "narration.txt").read_text().splitlines():
    line = raw.strip()
    if not line or line.startswith("#"):
        continue
    m = re.match(r"\[scene(\d+)\]", line)
    if m:
        cur = int(m.group(1)); scenes[cur] = []; continue
    if cur:
        scenes[cur].append(line)

report = []
for sc, lines in sorted(scenes.items()):
    piece_paths = []
    for i, line in enumerate(lines):
        piece = PIECES / f"sc{sc}_{i:02d}.wav"
        if not piece.exists():
            subprocess.run(
                [str(PIPER), "-m", str(MODEL), "-f", str(piece),
                 "--speaker", "0", "--length-scale", "1.18",
                 "--noise-scale", "0.5", "--noise-w-scale", "0.7"],
                input=line, text=True, check=True, capture_output=False)
        piece_paths.append(piece)
    # concat with silence gaps
    out = AUDIO / f"scene{sc}_vo.wav"
    with wave.open(str(piece_paths[0]), "rb") as w0:
        params = w0.getparams()
    silence = b"\x00" * int(GAP * params.framerate) * params.sampwidth * params.nchannels
    with wave.open(str(out), "wb") as wout:
        wout.setparams(params)
        for j, p in enumerate(piece_paths):
            with wave.open(str(p), "rb") as win:
                wout.writeframes(win.readframes(win.getnframes()))
            if j < len(piece_paths) - 1:
                wout.writeframes(silence)
    with wave.open(str(out), "rb") as w:
        dur = w.getnframes() / w.getframerate()
    report.append(f"scene{sc}: {len(lines)} lines, {dur:.1f}s")

print("\n".join(report))
print("NARRATION_DONE")
