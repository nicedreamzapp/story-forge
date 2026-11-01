# 04_shots — selects (part 2, 2026-10-31 11:57 AM)
Picked by the builder (delegated, see APPROVED.md) from a 6-frame grid of every take (`/tmp` sheets, one row per take)
plus the VL clip gate (`logs/gate_clips_report.md`, beat_gate, 3 frames voted per take). Rank 1 = in the cut;
rank 2 = runner-up kept as coverage. Full machine list: `selects.json`; exact in/out per cut: `final/edl_final.json`.

| cut(s) | rank 1 (why) | rank 2 | clip gate |
|---|---|---|---|
| c01, c01b asteroids | previs R01: the ship GROWS toward camera (the beat); hq t1 recedes | hq R01 t1 | FAIL both ("stationary") |
| c02a, c02b cockpit/lever | hq R02 t2: lever pull, sparks and lightning burst ~2 s, most adrenaline | hq t1, previs | FAIL ("red light steady") |
| c03, c03b dive | hq R03 t1: ship plunges into the cloud as lightning cracks ~2 s; previs barely moves | previs | FAIL |
| c04 arrival | hq R04 t1: descent, dust wall, camera slides under the lit hull 2.9-4.5 s (the whip-under), holds 4.4 s clean | t2 (shadow sweep reads, but hull leaves frame by 2 s), t3 (hull smears into a dark disk: declined) | FAIL all ("hovering") |
| c05 claws | hq R05 t1: claw plants, glass shards spray outward and hold to 1.4 s | previs (dust bigger but hazes) | FAIL |
| c06 monolith reveal | hq R06 t2: bright lightning strike over the monolith field | t1, t3 (previs grows a crowd of figures in the fog: not used) | FAIL |
| c06b crew walk | hq R07 t1: both walk, faces stable | previs | FAIL ("standing still") |
| c07 handwriting | hq R08 t1: the glow spreads widest and brightest under the still hand | t3 (gate PASS 3/3, dimmer glow), t2 | t1 FAIL (judge said the hand moves; the grid shows it still) |
| c07b captain face | hq R09 t2: push-in to an extreme close-up, eyes wide | t1 | PASS 3/3 |
| c08 lightwave | hq R10 t1: ring ignites then light pillars burst upward ~2.2 s | t3 (ring expands outward, used in the strobe), t2 | FAIL ("static ring") |
| c09 welcome | hq R11 t2: low angle, lightning behind her, frozen | t1 | PASS 3/3 |
| c10, c10b second sun | hq R12 t1: the burst flares and whites out (lens flare) | previs | FAIL ("not clearly a second sun") |
| c11, c11b yanked | hq R13 t1 then t2: flung off his feet, a dark shape above him, gone into the dust by ~1 s | previs | FAIL ("lunging forward, not pulled back") |
| c12, c12b engines | hq R14 t1, then previs: blue fire and sparks erupt | — | FAIL |
| c13, c13b mountain | hq R15 t1 (rises, camera tilts up, teal eye line), t3 (closer) | t2, previs | FAIL ("static") |
| c14, c14c boots | hq R16 t1: glowing cracks race under the boots | previs | FAIL (reads the glass as water) |
| c14b, c15c sprint | hq R17 t2 (gate PASS 3/3), then t1 | — | t2 PASS 3/3, t1 PASS 2/3 |
| c15, c15b grab | hq R18 t2 (lightning crawls over the talons as the ship lifts), t3 (ship tips, yanked) | t1 (used in strobe), previs | FAIL ("static") |
| strobe | previs R19 eyes + R20 scream (PASS 3/3) cut with alternates of R05/R10/R12/R14/R15/R18 | — | — |

## Clip gate result, stated plainly
10 of 44 takes PASS, 34 FAIL. Most failures are the judge reading ONE frame of a motion beat ("rushing", "rising",
"for the whole shot") as "static". Our clip_beats describe motion, which a still frame cannot show (the rule-26
lesson, again). The selected takes are used under a DECLARED gate exception, backed by the builder's frame-grid
look. The real content risks it flagged are listed in stages/07_gates/known_defects.md (R13 direction, R16 glass
reading as water, R12 second sun ambiguous).

Declined this session (frozen rule 13, deleted now): hq R04 t3 (the hull smears into a dark disk).
