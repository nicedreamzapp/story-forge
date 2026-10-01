---
stage: 02_beats
outputs:
  - beats.json
  - continuity.json
  - stages/02_beats/story_test.md
gate: approved
---
# 02_beats — prove the story on paper

One job: convert the approved script into the shot list the gates judge against, and
prove a stranger could follow the film from the shots alone.

## Inputs
- Working (this film): `stages/01_story/script.md`
- Reference (every film): `../../RULES.md` rules 1–2 (a beat is a VISIBLE STATE), 25, 26
- Reference (every film): `../../FILM_BIBLE_SPEC.md`, `../../SCENE_BUILDING_METHOD.md`
- Reference (every film): `../../pipeline-tools/continuity_check.py` docstring (schema)

Do NOT load: `clips/`, `final/`, render tooling, other films.

## Process
1. Write `beats.json`: every shot's `beat` and `must_not`, plus the `spine`. Every spine
   id must have a `shots[]` entry (rule 17). Pulling/carrying geometry is stated (rule 26).
2. Write `continuity.json`: the state facts that must hold across the film.
3. Write `story_test.md`: from the SHOT LIST ALONE, no narration, the paragraph a
   first-time viewer would say the film is about. Compare to the premise; list gaps.
4. A gap means a missing shot. Add it to `beats.json` and redo step 3.

## Outputs
- `projects/<film>/beats.json`, `continuity.json`, `stages/02_beats/story_test.md`

## Human check
Matt reads the story-test paragraph next to the premise. They match, or this stage
goes again. Write `APPROVED.md`.
