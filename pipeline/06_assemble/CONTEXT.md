---
stage: 06_assemble
outputs:
  - final/*.mp4
  - final/timeline.json
gate: none
---
# 06_assemble — cut the film

One job: turn the coverage into selects and cut them to the words. Nothing new is
generated here except title and credit cards.

## Inputs
- Working (this film): `stages/04_shots/APPROVED.md` (approved scenes), `clips/` +
  `clips/alternates/` + `manifest.json` (the coverage), `voices/`, the picked score, `beats.json`
- Reference (every film): `../../bin/build-episode` docstring, frozen rules 17, 29, 32, RULES.md 23, 26, 28

Do NOT load: `_ARCHIVE_UNUSED_not_in_film/`, review folders, declined takes.

## Process
1. The coverage gate must pass first (`bin/film-status` shows it; frozen rule 29).
2. Selects: rank >= 2 takes per beat from the coverage in `manifest.json`, with a why.
   Only takes from approved scenes are eligible; declined takes are already gone.
3. Cut to words: word timings for every line, hard cuts on word onsets, a dissolve only
   where a cue asks for one (frozen rule 32). Never a blanket crossfade.
4. Run `bin/build-episode projects/<film>`. Its preflight cross-checks the EDL against
   `beats.json` and hard-stops on a mismatch; never bypass it.
5. Static gain mix, never loudnorm dynamic.

## Outputs
- `projects/<film>/final/<Film>.mp4`, `final/timeline.json`

## Human check
None here. Stage 07 runs immediately; Matt sees the film only after the gates.
