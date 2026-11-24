## DEFAULT MOVIE-MAKING RULES — GIVENS on every video (Matt, 2026-05-25, never ask)
These are standing direction. Apply them automatically to every film; do not make Matt re-explain.

0. **Real material first, literal shots, no house style (Matt 2026-11-24: "every film looks the same").**
   a. Step one of every film is gathering Matt's REAL footage, screenshots, photos and recordings of the actual
      subject (`MATERIAL.md`), and the shots are built around them. Generated shots only fill what real material
      can not show.
   b. Every shot shows the real subject literally, with people or the subject DOING something. No metaphors
      (glowing cursors as gates, vaults for security, rivers of light) unless Matt asks for one.
   c. There is no shared look. Each film writes its own `LOOK.md` from references Matt gives for that film;
      "35mm, anamorphic, teal and amber, quiet thriller, one light source" is retired and the gate rejects it.
   d. `pipeline-tools/cliche_gate.py projects/<film>` runs before any still and blocks the repeated motifs
      (robots, alarm beacons, corridors, vaults, padlocks/keys/fingerprints, a desk lamp in a dark room, rain on
      windows, mist/haze, dust in light beams, night city from above, server rooms/glowing monitors, silhouettes,
      moonlight, embers, camera-move-only motion, "nobody in the room") and any main scene a past film already
      used (`_shared/used_scenes.jsonl`; a finished film records its scenes with `cliche_gate.py --record`).
      A motif Matt asked for goes in the film's `ALLOW.md` with his words.
   e. Matt's narration voice is LOCKED: `pipeline-tools/matt_voice.py` only (ChatterBox, matt_real_ref.wav,
      exaggeration 0.45, cfg 0.5, temperature 0.75, seed 7, silence trim only, no pitch/EQ/effects/limiter).
      voices/voice2_matt.wav, pitch 0.92 and the warm EQ are retired for him.

1. **Dynamic multi-shot coverage.** Every scene is a SEQUENCE of shots, never one static clip, so it reads as fully animated film — the viewer can't tell it came from stills. Cover each beat with varied framings + camera moves that keep returning to the same scene: wide establish → push-in close-up → side/parallax move → pull back wider → return to the action. Source the shots: (a) CROPS of the locked still into close/medium/wide framings (instant, perfectly consistent), (b) i2v CAMERA MOVES (push-in, pull-back, pan, parallax, gentle orbit), (c) FRESHLY GENERATED stills for true new angles (behind/side/above/low) when a beat needs one — on-model via per-character LoRAs so characters stay identical across angles. Assume MAXIMAL coverage by default.
2. **Prompt the mouth motion to the dialogue.** On any shot with a line, write the i2v motion prompt to make that character's mouth move when we want the line ("Doug's mouth opens and closes as he speaks"). Direct mouth motion on purpose so it lands with the dialogue, then lay voice over the untouched result and density-match. NOT repainting mouths (still banned) — we prompt the motion, then voice it. i2v gives open/close jaw motion, not phonetic lip-sync; time it + density-match rather than expecting perfect sync.
3. **Character consistency via LoRAs.** For true new angles / new poses, generate on-model using per-character LoRAs (Doug, Hank, etc.). Build the LoRA the first time a film needs real new angles; reuse forever after.

4. **Coverage, then cut to the best (2026-10-22).** For every format: >= 3 setups per line/beat from >= 2 sources, acquired seconds >= 3x runtime, alternates kept until the film is approved, selects ranked with a why (frozen rules 13 amended, 29).
5. **Motivated motion, cut to words (2026-10-22).** Every shot names an action or a camera move chosen for it; static is an explicit flag, drift is never a default. Cuts land on word onsets; dissolves only where a cue asks (frozen rules 31, 32).

6. **Motivated, shaped light (2026-11-02, amended 11-24).** Every still and i2v prompt names where its light comes from, matched to THIS film's `LOOK.md` and Matt's references. `_shared/lighting.md` is a craft reference, not a house style: a lone lamp in a dark room, haze and dust in the beam are banned defaults (rule 0).

Full detail: SCENE_BUILDING_METHOD.md.

7. **K6 / image-to-video: people only in WIDE shots (2026-11-21).** No faces large enough to read, no hands swinging tools close up; close-ups only for objects that stay still. Relief and stone prompts always say "no fire, no flames, no glow". Matt 11/21: "massive amounts of hallucinations on faces and tools... the faraway scenes look good".
8. **Every clip is judged, every bed is hiss-gated (2026-11-21).** Each K6/video clip passes `pipeline-tools/clip_judge.py` before it enters a cut (FAIL = one remake on a new seed; a second FAIL is reported to Matt, never cut in silently). Every sound bed comes from `bin/make-sfx`, which rejects hiss itself. Matt 11/21: "static... I keep asking this every video... kill it and bake it in". Gates: `_shared/gates-and-qc.md`.
