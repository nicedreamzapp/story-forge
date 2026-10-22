---
stage: 07_callouts
outputs:
  - callouts.json
gate: none
---
# 07_callouts — point at the parts (optional per film)

One job: arrows and diagrams that land on the real part, on the word that names it.

## Writes
- `callouts.json` (SCHEMAS.md; `tip` keyframes when the part moves) with a `callout` cue per entry in
  cues.json; Manim CE diagrams as alpha clips (`overlays/*.mov`) with `overlay` cues. For a Blender
  shot, read the tip from the object-ID pass (`acquired/blender/<id>/ids_####.png` + `ids.json`).
- A film with no callouts simply has no `callouts.json`; the stage reads as open in film-status
  and make-promo skips callout_check.

## Gate (runs in 09)
`~/.local/mlx-server/bin/python pipeline-tools/callout_check.py projects/<film> --film final/<film>.mp4`
— every tip on its part; UNCHECKED is listed, never counted as a pass.
