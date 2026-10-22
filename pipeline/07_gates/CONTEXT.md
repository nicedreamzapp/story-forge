---
stage: 07_gates
outputs:
  - final/*report*.md
  - stages/07_gates/known_defects.md
gate: approved
---
# 07_gates — find the defects before Matt does

One job: run the mandatory gates, in order, watch the whole cut, and write down
everything still wrong.

## Inputs
- Working (this film): `final/<Film>.mp4`, `final/timeline.json`, `narration.json`,
  `continuity.json`, the score file
- Reference (every film): `../../_shared/gates-and-qc.md` (story + sound gates and
  the film_qc stage); `../../RULES.md` rules 21–25

Do NOT load: generation tooling, other films' reports.

## Process
1. `~/chatterbox-env/bin/python pipeline-tools/audio_check.py FILM --score S --timeline final/timeline.json --narration narration.json`
2. `~/.local/mlx-server/bin/python pipeline-tools/continuity_check.py projects/<film>`,
   then read `final/story_sheet.png` + `.md` yourself as a first-time viewer.
3. `~/.local/mlx-server/bin/python pipeline-tools/film_qc.py FILM manifest.json`.
   Exit 2 is NOT a pass.
4. `~/.local/mlx-server/bin/python pipeline-tools/design_check.py projects/<film>` when the
   film shows a real object with a `design.json` (RULES.md 29). The coverage gate already
   passed before the cut (frozen rule 29).
5. Watch the full cut start to finish yourself, every second, not a frame grid.
6. Write `known_defects.md`: dated, every FAIL and WARN, what you saw that no gate checks,
   anything unjudged as UNCHECKED, and the line "Watched the full cut start to finish on
   <date>". It must be newer than the newest `final/*.mp4`; a re-cut means a re-watch.
   Until then `bin/film-status` prints `READY FOR MATT: no` (frozen rule 30).

## Outputs
- the three reports in `projects/<film>/final/`, `stages/07_gates/known_defects.md`

## Human check
Only when film-status says `READY FOR MATT: yes`. Matt is told the pass/fail counts
verbatim and the known defects BEFORE he watches.
He watches and says ship it. Write `APPROVED.md`. A no sends the film back to the
stage that owns the defect.
