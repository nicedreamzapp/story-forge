---
stage: 05_sound
outputs:
  - voices/
  - stages/05_sound/score_pick.md
gate: approved
---
# 05_sound — voices and score

One job: voice every line onto the approved clips and get a score Matt picked by ear.

## Inputs
- Working (this film): `stages/01_story/script.md` (the lines), approved `clips/`
- Reference (every film): `../../_shared/dialogue-scenes.md`, frozen rule 9 in `../../_shared/frozen-rules.md`
- Reference (every film): `../../bin/character_voice.py`, `../../RULES.md` rules 22–23

Do NOT load: canon generation tooling, `beats.json` gate history, other films.

## Process
1. Mouth-sync each scene (`bin/mouth_sync.py`), density-match, one talker per beat.
2. Render voices into `voices/`; whisper-check every take for duds.
3. Commission 2–3 score candidates from Song Forge with `"lyrics": "[instrumental]"`.
4. Write `score_pick.md`: the candidates, which one Matt chose, his words.
5. Sound effects (added 2026-10-31): every film gets designed SFX, not just score and voices.
   Use `bin/make-sfx "prompt" --seconds N --out sfx/NAME.wav` (MMAudio, loads,
   generates, exits; it waits on Song Forge jobs and takes a memory lease itself). Batch all
   SFX in one pass so the model loads once. MMAudio (picture-synced foley) layers on top.
   Write each moving sound's path (azimuth keyframes, LFE send) into `sfx/mix_plan.json`
   for stage 06. Schema: docstring of `../../tools/surround_mix.py`.

## Outputs
- `projects/<film>/voices/`, `stages/05_sound/score_pick.md`, `sfx/` + `sfx/mix_plan.json`

## Human check
Matt confirms each character's voice once, and picks the score by ear.
Write `APPROVED.md`.
