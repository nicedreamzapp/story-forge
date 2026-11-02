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
      `clips/previs/`. One model loaded, then unloaded. LTX-2.5 is the fast previs drafter only (plus a2v
      lip-sync close-ups); it is no longer the quality engine.
   b. Cut a rough previs edit (`final/previs_cut.mp4`) against the script timings and
      decide which shots and which seconds actually make the cut.
   c. The quality engine is **Kandinsky 6.0 Pro** (29B, bf16, MIT; `bin/make-k6`, forge-shot's default
      `"engine": "k6"`; Matt 2026-11-01 on its first clip: "That's the best I've ever seen"; details in
      `../../VIDEO-MODEL-2026-11-01.md`). It renders ONLY what makes the cut, at the cut's length plus ~0.5 s
      handles (never a blanket 5 s; 5 s is K6's maximum); 3 takes for hero shots, 1-2 for the rest.
      Measured on the M5: 10 steps, 832x480 x 73 frames (3 s) = ~718 s a clip, peak 68.7 GB, so it runs
      alone (one model loaded, nothing else heavy beside it). Dialogue close-ups that must lip-sync to a
      real voice wav stay on LTX-2.5 a2v (`make-ltx25 --audio`) until a better acting engine is proven.
   d. Render at the 480p-class native size (832x480). Upscaling happens at assembly through
      `bin/upscale-route` (06_assemble step 7): SeedVR2-3B by default, LTX-2.5 Refine for faces and
      close-ups, lanczos for sub-second cuts. Here, set `"face": true` on every beats.json shot whose
      picture is a face or close-up (always for cartoon/animal characters, which the auto face probe
      can't see), `"face": false` to force SeedVR2, or `"upscale": "..."` as a hard override.
   e. Precise motion (ships, vehicles, debris, camera moves) is blocked in Blender first
      and used as the i2v start frames/guide; AI video paints the organic realism on top.

## Outputs
- `projects/<film>/shots.json`, `clips/`, `stages/04_shots/kept_clips_review.md`

## Human check
Each scene is shown to Matt standalone with a descriptive filename. He says yes per
scene. Write `APPROVED.md` listing the approved clips by path.
