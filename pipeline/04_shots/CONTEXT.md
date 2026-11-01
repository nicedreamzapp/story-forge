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
4. Keep every passing alternate as coverage in `clips/alternates/`, listed in
   `manifest.json`, until the film is approved. Delete DECLINED takes the same session
   (frozen rule 13 as amended). Motion prompts name an action or a motivated camera move;
   static is an explicit `"static": true` (frozen rule 31).

5. Motion order, previs first (Matt 2026-10-31, "scale this differently... bake it in"):
   a. Animate EVERY shot with LTX 2.5 distilled first (~70 s a clip on the M5), into
      `clips/previs/`. One model loaded, then unloaded.
   b. Cut a rough previs edit (`final/previs_cut.mp4`) against the script timings and
      decide which shots and which seconds actually make the cut.
   c. The quality engine (LTX-2.5 `make-ltx25 --hq`, dev transformer + CFG two-stage; Wan 2.2 14B bf16
      only if it is installed and the memory guard allows it) renders ONLY what makes the cut, at the
      cut's length plus ~0.5 s handles (never a blanket 5 s); 3 takes for hero shots, 1-2 for the rest.
      A previs draft that already holds up for a sub-second cut stays and skips the quality pass.
   d. Render at the 480p-class native size (832x480); SeedVR2-3B upscales at assembly (held shots
      >= ~0.9 s at 720p, then lanczos to 4K; sub-second cuts lanczos only; see LESSONS).
   e. Precise motion (ships, vehicles, debris, camera moves) is blocked in Blender first
      and used as the i2v start frames/guide; AI video paints the organic realism on top.

## Outputs
- `projects/<film>/shots.json`, `clips/`, `stages/04_shots/kept_clips_review.md`

## Human check
Each scene is shown to Matt standalone with a descriptive filename. He says yes per
scene. Write `APPROVED.md` listing the approved clips by path.
