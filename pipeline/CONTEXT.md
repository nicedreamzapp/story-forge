# Story Forge — the film pipeline

The flow in one line: write it, prove the story on paper, lock the cast, shoot gated
shots, voice and score it, cut it, run the gates, ship it.

This folder is the METHOD (one contract per stage). Each film is an INSTANCE that lives in
`projects/<film>/`. Machine files stay where the tools already read them (`beats.json`,
`canon/`, `clips/`, `final/`); the human-facing artifacts and the approvals live in
`projects/<film>/stages/NN_name/`.

| Stage | Job | Reads | Writes (in `projects/<film>/`) | Human check |
|---|---|---|---|---|
| `01_story` | premise, structure, dialogue | Matt's idea | `stages/01_story/premise.md`, `script.md` | Matt approves the premise and script |
| `02_beats` | script → shot list, story test | 01 | `beats.json`, `continuity.json`, `stages/02_beats/story_test.md` | the story test paragraph matches the premise |
| `03_canon` | one master per character and set | 02 | `canon/` | Matt approves every master |
| `04_shots` | gated stills → locked → animated | 02, 03 | `shots.json`, `clips/`, `stages/04_shots/kept_clips_review.md` | Matt approves each scene standalone |
| `05_sound` | voices, mouth sync, score | 01, 04 | `voices/`, `stages/05_sound/score_pick.md` | Matt picks the score by ear |
| `06_assemble` | EDL → the cut | 04, 05 | `final/*.mp4`, `final/timeline.json` | none, 07 runs straight after |
| `07_gates` | audio, continuity, film_qc | 06 | `final/*report*.md`, `stages/07_gates/known_defects.md` | Matt watches, told the defects first |
| `08_deliver` | publish | 07 | `stages/08_deliver/published.md` | none |

**A stage is DONE** when every output exists, is non-empty, no longer carries the
`TEMPLATE` marker, and (where there is a human check) `stages/NN_name/APPROVED.md` exists.
Write `APPROVED.md` only after Matt says yes: date, what he approved, his words.

**Status is whatever exists on disk:** `bin/film-status projects/<film>` (add `--init` to
stamp a new film from `_templates/film/`). Each stage's `CONTEXT.md` frontmatter is the
one home for its outputs and gate; the script reads it from there.

Factory (stable, every film): `RULES.md`, `SCENE_BUILDING_METHOD.md`, `FILM_BIBLE_SPEC.md`,
`LESSONS.json`, and the frozen rules in the root `CLAUDE.md`.
Product (new every film): `projects/<film>/`.

Sending a film back: delete the later stages' `APPROVED.md` files when an earlier stage
changes. A re-approved script means the shot list gets re-checked, not trusted.
