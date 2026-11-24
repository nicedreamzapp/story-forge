---
stage: 02_voice
outputs:
  - vo/final/part000.wav
  - vo/voice.json
gate: none
---
# 02_voice — the narration, voiced and heard back

One job: every script line in Matt's clone, finished, and transcribed back word for word. Runs on
the M5; Song Forge must be idle (customer jobs first).

## Command
`~/chatterbox-env/bin/python pipeline-tools/promo_voice.py projects/<film>` (`--force`, `--only N`)

## What it does
Matt's LOCKED voice (`pipeline-tools/matt_voice.py`, 11/24: ChatterBox, matt_real_ref.wav, exaggeration 0.45,
cfg 0.5, temperature 0.75, seed 7) → finish = silence trim + 0.25 s pad, 48 kHz mono, NOTHING else (no pitch,
EQ, loudnorm or limiter on his voice; voice2_matt / matt2 / pitch 0.92 / warm EQ are retired) → mlx-whisper with no
script prompt → compare. A miss gets `retakes` more takes; still missing → AUTO-REWORD (`alt:` lines,
then numbers written out, then the misheard word set off by commas). A reworded line is recorded in
`vo/voice.json` "spoken" and every later gate checks against what was spoken. Unchanged lines are
not re-voiced.

## Done when
Exit 0: every line `match: true` in `vo/voice.json`. Exit 1 prints the line, what was expected and
heard; add an `alt:` (or `say:`) under it in script.md and run again.
