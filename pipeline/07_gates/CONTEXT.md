---
stage: 07_gates
outputs:
  - final/*report*.md
  - stages/07_gates/known_defects.md
gate: approved
---
# 07_gates — find the defects before Matt does

One job: run the three mandatory gates, in order, and write down everything still wrong.

## Inputs
- Working (this film): `final/<Film>.mp4`, `final/timeline.json`, `narration.json`,
  `continuity.json`, the score file
- Reference (every film): `../../CLAUDE.md` "MANDATORY STORY + SOUND GATES" and
  "MANDATORY QC STAGE"; `../../RULES.md` rules 21–25

Do NOT load: generation tooling, other films' reports.

## Process
1. `~/chatterbox-env/bin/python pipeline-tools/audio_check.py FILM --score S --timeline final/timeline.json --narration narration.json`
2. `~/.local/mlx-server/bin/python pipeline-tools/continuity_check.py projects/<film>`,
   then read `final/story_sheet.png` + `.md` yourself as a first-time viewer.
3. `~/.local/mlx-server/bin/python pipeline-tools/film_qc.py FILM manifest.json`.
   Exit 2 is NOT a pass.
4. Write `known_defects.md`: every FAIL and WARN, plus what you saw that no gate checks.
   Anything unjudged is listed as UNCHECKED.

## Outputs
- the three reports in `projects/<film>/final/`, `stages/07_gates/known_defects.md`

## Human check
Matt is told the pass/fail counts verbatim and the known defects BEFORE he watches.
He watches and says ship it. Write `APPROVED.md`. A no sends the film back to the
stage that owns the defect.
