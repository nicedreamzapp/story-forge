---
stage: 03_coverage
outputs:
  - coverage.json
  - design.json
gate: approved
---
# 03_coverage — plan way more footage than the cut needs

One job: the coverage plan per line, and the physical-accuracy contract for the product.

## Reads
- `script.md`, `stages/01_story/premise.md` (the sentiments), the CAD (GLBs) and any renders on hand,
  `../SCHEMAS.md` (coverage.json, design.json), frozen rules 28, 29, 31.

## Writes
- `coverage.json`: per line its text, sentiment, >= 3 setups from >= 2 sources, and `target_runtime`.
  Every setup names an action or a motivated camera move (frozen rule 31). `blender-render` setups
  name `acquired/blender/<id>/beauty.mp4` and get a matching `promo.json "blender"` shot.
- `design.json`: reference CAD stills per angle, counted facts (`when` for poses), `must_not`, the
  part names, and the `fidelity_clause` every browser prompt carries.

## Command
`python3 pipeline-tools/coverage_lint.py projects/<film>` must pass.

## Done when
coverage_lint passes, both files are real, and Matt confirmed the design facts
(`stages/03_coverage/APPROVED.md`). Only he knows the product; a wrong fact fails every good shot.
