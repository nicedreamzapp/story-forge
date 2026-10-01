---
stage: 01_story
outputs:
  - stages/01_story/premise.md
  - stages/01_story/script.md
gate: approved
---
# 01_story — settle the drama first

One job: turn Matt's idea into an approved premise and a plain screenplay. No render,
no still, no `.sf` yet.

## Inputs
- Working (this film): Matt's idea, in his words, pasted into `premise.md`
- Reference (every film): the `screenwriting` skills, `sw-premise-theme` FIRST, then
  `sw-story-structure`, `sw-character-conflict`, `sw-dialogue`
- Reference (every film): `../../LESSONS.json` (filter by the film's keywords)

Do NOT load: other films' folders, `RULES.md` render rules, any pipeline-tools source.

## Process
1. Fill `premise.md`: controlling idea, who wants what, what stops them, the ending.
2. Write `script.md` in ordinary screenplay terms: scenes, beats, every spoken line.
3. Every plot turn must be something a camera can SHOW. Flashbacks get a spoken time marker.
4. Lines must fit prompted mouth motion: short beats, one talker per beat.

## Outputs
- `projects/<film>/stages/01_story/premise.md`
- `projects/<film>/stages/01_story/script.md`

## Human check
Matt reads the premise and script and says yes. Write `APPROVED.md` with his words.
