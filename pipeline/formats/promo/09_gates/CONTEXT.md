---
stage: 09_gates
outputs:
  - final/*report*.md
  - stages/09_gates/known_defects.md
gate: approved
---
# 09_gates — every gate, then watch it whole

One job: run every gate on the finished cut, look at the strips, watch it start to finish, write down
what is wrong.

## Commands (inside `bin/make-promo`)
1. `python3 pipeline-tools/cue_check.py projects/<film>` → `final/cue_check_report.md`
2. `~/chatterbox-env/bin/python pipeline-tools/promo_gates.py projects/<film>` → `final/promo_gates_report.md`:
   whisper the FINAL mix vs the script word for word; loudness −16 ± 1 LUFS, TP <= −1 dBFS; voice >= 10 dB
   over the ducked music; slam after the last heard word; last words heard; sting rings; end card on
   screen; every used shot passed design_check; frame strips per line and per event in `final/strips/`.
3. `~/.local/mlx-server/bin/python pipeline-tools/callout_check.py projects/<film> --film final/<film>.mp4`
   when `callouts.json` exists.
4. `~/.local/mlx-server/bin/python pipeline-tools/film_qc.py ...` when people with faces/lips are on screen.
5. Look at EVERY strip, then watch the full cut start to finish. Strips are not verification.

## Writes
`stages/09_gates/known_defects.md`: dated, the gate counts verbatim, every FAIL/WARN/UNCHECKED, what
you saw that no gate checks, and "Watched the full cut start to finish on <date>".

## Done when
`bin/film-status` prints `READY FOR MATT: yes`. Matt hears the counts and the defects first, watches,
and says ship it: write `APPROVED.md`. That session, delete the coverage the cut did not use (frozen
rule 13 as amended).
