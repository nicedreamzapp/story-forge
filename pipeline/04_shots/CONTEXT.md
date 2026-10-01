---
stage: 04_shots
outputs:
  - shots.json
  - clips/
  - stages/04_shots/kept_clips_review.md
gate: approved
---
# 04_shots — shots that prove themselves

One job: build every shot in `beats.json` through the gates. A shot that cannot pass
is reported UNBUILT, never quietly used.

## Inputs
- Working (this film): `beats.json`, `canon/`, `shot_lessons.json` (if present)
- Reference (every film): `../../RULES.md` "What a shot must prove" + "How motion is made"
- Reference (every film): `../../_shared/movie-making-defaults.md`; `../../_shared/motion-transfer.md` only for a stunt driven by real footage
- Reference (every film): frozen rules 6, 11, 12, 14, 16, 18, 19, 27 in `../../_shared/frozen-rules.md`

Do NOT load: `voices/`, score files, `final/`, other films.

## Process
1. Health-check Song Forge (`127.0.0.1:8767/api/status`) before heavy GPU work.
2. Write `shots.json`, then run `bin/forge-director projects/<film>` (or one shot at a
   time: `~/.local/mlx-server/bin/python bin/forge-shot projects/<film>/shots.json --only ID`).
3. Every KEPT clip gets a frame-grid look from the agent (rule 26). Record each verdict
   in `kept_clips_review.md`: shot id, clip path, what you saw, keep or reshoot.
4. Delete declined takes the same session (frozen rule 13).

## Outputs
- `projects/<film>/shots.json`, `clips/`, `stages/04_shots/kept_clips_review.md`

## Human check
Each scene is shown to Matt standalone with a descriptive filename. He says yes per
scene. Write `APPROVED.md` listing the approved clips by path.
