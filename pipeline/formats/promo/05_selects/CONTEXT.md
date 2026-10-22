---
stage: 05_selects
outputs:
  - selects.json
gate: none
---
# 05_selects — cut to the best, and say why

One job: rank the takes for every line so the edit has choices.

## Reads
- `manifest.json` (only design `pass`, or `unchecked` written down as such), `coverage.json`,
  `stages/01_story/premise.md` (the sentiment each line must land), `../SCHEMAS.md` (selects.json).

## Writes
- `selects.json`: per line, >= 2 ranked takes with `in`/`out` and a `why` naming the sentiment, the
  action, the geometry. `pipeline-tools/promo_draft.py --selects` writes a `"draft": true` version
  when none exists (design pass first, then source trust, then the plan's order); replace its whys
  with real ones before calling the film done.

## Command
`python3 pipeline-tools/coverage_gate.py projects/<film>` must pass (frozen rule 29).

## Done when
Every line has >= 2 ranked takes with a why, and the coverage gate passes.
