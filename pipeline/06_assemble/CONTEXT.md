---
stage: 06_assemble
outputs:
  - final/*.mp4
  - final/timeline.json
gate: none
---
# 06_assemble — cut the film

One job: assemble exactly the approved clips and audio into the film. Nothing new is
generated here except title and credit cards.

## Inputs
- Working (this film): `stages/04_shots/APPROVED.md` (the only clips allowed in the cut),
  `voices/`, the picked score, `beats.json`
- Reference (every film): `../../bin/build-episode` docstring, frozen rule 17, RULES.md 23

Do NOT load: `_ARCHIVE_UNUSED_not_in_film/`, review folders, declined takes.

## Process
1. The EDL points only at clips named in `stages/04_shots/APPROVED.md`.
2. Run `bin/build-episode projects/<film>`. Its preflight cross-checks the EDL against
   `beats.json` and hard-stops on a mismatch; never bypass it.
3. Static gain mix, never loudnorm dynamic.

## Outputs
- `projects/<film>/final/<Film>.mp4`, `final/timeline.json`

## Human check
None here. Stage 07 runs immediately; Matt sees the film only after the gates.
