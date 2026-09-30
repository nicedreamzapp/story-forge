# The Oldest Tree — CURRENT (story locked 2026-09-28 11:35p; scene list pending Matt OK)

Style: photoreal cinematic, 2.39:1 letterbox, one grade + light grain. No on-camera lip-sync:
wides, backs, silhouettes, hands. Narrator = the granddaughter grown up (voice TBD).
Cast: Grandfather (~75), Granddaughter (~10), Grown granddaughter (~35, final scene only).

Premise: love outlasts memory, because the stories we're given carry us home.
Plant/payoff: the fire story ("when the fire came, the animals hid inside the tree and lived")
is the clue that sends her back to the hollow.

## Scene list (~4:00)
1. 0:00-0:25 Opening image: aerial redwood canopy in fog, narrator. Title.
2. 0:25-0:55 Grandfather + girl walk among giants; small signs he's forgetting (calls her by grandma's name).
3. 0:55-1:25 The giant tree: the fire-scarred hollow, old carved initials where he proposed. Seed -> sapling -> centuries.
4. 1:25-1:45 She goes to the creek for water; comes back at dusk, he's gone. Fog rolls in.
5. 1:45-2:45 Search in the dark, flashlight. Intercut tree stories: lightning strike, wall of forest fire + embers, storm + falling giant.
6. 2:45-3:05 All is lost: flashlight dies, black fog, cold. She remembers the fire story.
7. 3:05-3:35 Back to the tree: he's inside the fire scar. She wraps him in her jacket. One moment he knows her.
8. 3:35-4:00 Years later: grown woman + her own child, hand on the scar. Mirror of opening.

## 2026-09-29 1:35a — scene 3 TEST built (awaiting Matt's verdict)
final/oldest_tree_scene3_test.mp4 — 21.5s, 1920x1080 (2.5:1 letterboxed), 6 LTX-2.5 shots from Qwen stills,
graded + grain, Heart narration over Song Forge piano/cello score (ducked). film_qc PASS 22/22; audio transcript
checked by whisper separately (all 5 narration lines heard). Forest ambience NOT in: LTX's generated audio came out
near-silent (-57 dB). Actors: canon/grandpa.png, canon/girl.png (locked).
Pipeline fix made tonight: bin/forge-shot unloads the in-process VL judge before asking for a still lease
(otherwise every shot after the first is HELD — 19GB judge + 45GB still > 50GB budget).

## 2026-09-29 2:15a — FULL FILM building overnight (Matt: "work through the night and finish")
- Matt's notes on the test: seedling read as grandpa planting it -> reordered (tree first, aged seedling, "Two thousand years ago" line);
  wanted more motion, sound effects, music he could hear, lip sync, narrator = Nia.
- Spec: film_shots.json (57 shots, 8 scenes; s2_talk + s7_talk are lip-sync via make_talk.sh = LTX-2 distilled a2v, strength 0.4, audio-cfg 14).
- Voices: narration Nia (voices/nia_n01..n17, all whisper-verified); grandpa = Kokoro am_michael ("warm American", Matt picked 9:15a 9/29). voiceC was rejected as gruff and retired.
- Score: Song Forge 250s instrumental, private/video_only -> score_full.wav. Foley: MMAudio fp32 via ComfyUI (make_sfx.py -> sfx/).
- Pipeline: run_film.sh (masters2 + 51 shots) -> finish_all.sh (talk, sfx, assemble_film.py, film_qc) -> final/The_Oldest_Tree.mp4
- Narrator voice note: nia.wav is an EARS CC-NC reference — fine for personal use, swap before monetizing.
- 9:13a Matt: score had LYRICS (Song Forge writes lyrics when lyrics blank — always send lyrics "[instrumental]") and drowned the narration -> new score v2 + music 0.32 + hard sidechain duck.
- 8:15p 9/29 story-clarity pass (Matt: "I don't know what it's about"): added s4_wander (grandpa walks off into fog), lines nA/nB/n10b/n11b/n12b make memory loss, disappearance and "centuries ago" explicit; cut s5_fallen (read as our tree falling). Music = score 3 (Matt's pick), static-gain mix. Hands = ken_burns stills; s2_hands/s6_hands/s8_childhand cut.
