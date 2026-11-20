# Selects: HANK & DOUG'S WILD RESCUE (part 2, 2026-11-01)

Every take got a frame-grid look from the builder (6 frames per take, all takes of a render side by side, plus the
previs draft) and the VL clip gate (beat_gate, Qwen3-VL, 3 frames over 15-85% of the clip, majority rules, against
the render's clip_beat + must_not + house checks: no humans, no trucks/tires, Doug a long-eared bloodhound not a beagle,
dog and bear never merged). Gate verdicts: logs/gate_clips_report.md (summary at the bottom of this file).
The cut uses the best take per cut; rank-2 takes stay as coverage (manifest.json) until Matt approves the film.

| cut | select (in, len) | why this one | runner-up / declined |
|---|---|---|---|
| c01a_hunt | R01 t1 (0.3, 1.5) | nose to the ground the whole time, lantern swinging behind, canon Doug (red, long ears), camera tracks back | t2 (head comes up sooner); previs |
| c01b_bear | R02 t1 (0.7, 1.0) | the warm lantern light sweeps across the frightened bear: the hunt is on him | t2 (no light sweep) |
| c01c_eyes | R03 RE-RENDER (see below) | old still put a tricolor beagle-like hound in Doug's place | R03 t1-t3 DECLINED (Doug off-model) |
| c01d_away | R04 t2 (0.1, 1.0) | Doug turns, glances back, bolts off the trail; clean | t1 (similar, lower energy); previs DECLINED (grew a lantern, noted 1:49 AM) |
| c01e_ditch | R05 t1 (0.45, 1.5) | the lantern tumbles and lands lit in the mud with a reflection; Doug's line sits over it | t3 (lands smaller); t2 (lantern goes dark) |
| c02a_rails | clips/blender/T_rails.mp4 (4 f, 0.8) | BLENDER (Matt 10:45: AI wheels moved unnaturally). Low camera riding alongside the drivers at 11 m/s: wheels turn by distance/R, side rods on the crank pins, motion blur on the spokes | R06 t1 + previs DECLINED for wheels (AI i2v wheels) |
| c02b_ears | R07 previs (0.3, 0.9) | ears up and swivel; the clip blurs only after 2.6 s | (sub-second, previs kept by plan) |
| c02c_thump | R08 previs (0.4, 0.8) | hind foot down, dust puff | |
| c02d_hawk | R09 previs (0.1, 0.8) | wings spread, beak wide open (the cry) before the launch blur | |
| c02e_prairie | R10 previs (1.5, 0.7) | mouth open whistling, paws up | |
| c03a_burst | R11 t1 (0.0, 1.5) | horses out front pulling, wagon behind, giraffes riding tall, barn behind, dust; correct pull geometry | t3 (similar, a horse turns to camera); t2 DECLINED (team geometry breaks, cows loose ahead of the wheels; VL also flagged a human) |
| c03b_wheel | R12 previs (0.6, 0.9) | wooden spokes, brass hub, iron rim, sand spraying; no tire | |
| c03c_team | R13 t1 (0.6, 1.0) | horses, camels and cows in harness ahead of the wagon, galloping | previs (camera swings in front of the team) |
| c03d_crew | R14 t1 (0.3, 1.2) | giraffes on the wagon bed, elephants with barrels alongside | previs |
| c03e_bench | R15 RE-RENDER (see below) | old still: Doug small and beagle-like beside Hank | R15 t1-t3 DECLINED (Doug off-model; t2 jump-zoom, t3 flying brass horns); previs DECLINED (hair-cloud morph) |
| c04a_train | clips/blender/T_wide.mp4 (4 f, 1.5) | BLENDER: the circus train rides the curve at 15 m/s with rigged wheels, slow push in | R16 t1-t3 DECLINED for wheels (AI i2v) |
| c04b_gap | R17 t1 (0.6, 1.5) | rails run to the rim and stop; the gap and far rim read | t2 (used for the rush); t3 DECLINED (a blue truck on the rails) |
| c05a_hank | R18 t1 (0.05, 2.85) | mouth_sync: his mouth opens 0.12-0.38 s and 1.54-2.83 s, exactly the shape of "Doug... that's a big hole." (pause in the middle); scratching his head at the gap | t2 (mouth beats 0.71-1.08 + 2.04-2.67, too short for the line), t3 (0.87 s of mouth motion) |
| c05b_doug | R19 t3 (0.58, 2.0) | mouth_sync: talking 0.62-1.96 s, the cut lands on his first word; canon Doug, talking mouth all through, determined smile, ears stay put | t1 (morph at ~1.5 s), t2 (ears fly out like wings) |
| c06a_ground | R20 t1 (0.3, 1.2) | metal-plated ants step up out of the sand toward camera | previs (a pebble pile grows) |
| c06b_river | R21 t3 (0.5, 1.6) | the glinting river of ants holds for the whole window | t1/t2 (crane away and lose the river) |
| c06c_hero_ant | R22 t1 (0.3, 1.2) | the hero ant marches with the column, plate glinting | t2 (soft, close blur) |
| c07a_bridge | R23 t2 (0.35, 1.2) | pushes in on the living bridge until the linked ants read | t1/t3 (static wide) |
| c07b_giraffes | R24 previs (0.1, 0.8) | two giraffes peer over the gap | |
| c07c_trumpet | R25 t1 (0.05, 0.8) | trunk raised high, water spraying | t2 DECLINED (ears/trunk morph) |
| c07d_whistle | R26 previs (1.0, 0.8) | brass whistle, steam jets | |
| c07e_monkey | R27 t1 (0.3, 0.8) | hands clamped over eyes, cap on, cab rattling | t2 (face smears at 1.2 s) |
| c07f_link | R28 previs (1.8, 0.8) | ants holding on in a line over the drop | R28 t1/t2 DECLINED (the beam becomes a paved road with yellow dashes; t2 morph) |
| c07g_doug | R29 t2 (0.5, 0.8) | eyes widen tracking the train, mouth shut, no morph | t1 (morph at ~0.7 s) |
| c07h_edge | clips/blender/T_edge.mp4 (4 f, 1.2) | BLENDER: static low camera at the rim, the loco rolls in on turning wheels and its lead wheels stop at the last ties | R30 t1-t3 DECLINED for wheels (AI i2v) |
| c07i_rush | R17 t2 (2.2, 0.8) | POV rushes over the rim | |
| c10a_ant_salute | R31 t3 (0.4, 1.8) | the ant snaps the salute and holds it, Doug soft behind, clean | t1 (strong push, ant face stretches), t2 (soft) |
| c10b_doug_salute | R32 t3 (0.6, 2.0) | Doug salutes back with a warm smile, canon look, gentle push | t1 (nose fills frame), t2 |

## Re-render (part 2): R03 + R15
| cut | select | why | declined |
|---|---|---|---|
| c01c_eyes | R03 t4 (0.5, 1.3) | canon Doug (solid red, long ears) all through; the bear turns his head and his eyes land on Doug | t5 kept as coverage (the bear waves a paw instead of looking) |
| c03e_bench | R15 t4 (0.3, 1.4) | canon Doug beside a much bigger Hank, Hank grins, gentle push in; VL 3/3 PASS | t5 DECLINED (Doug merges into Hank at the end) |

## Gate summary and declared exceptions
VL clip gate (logs/gate_clips_report.md): 50/70 PASS; redo pass (logs/gate_clips_redo_report.md) 2/4 PASS.
Selected takes rated FAIL by the gate, kept by the builder with the reason:
- R04 t2 (1/3): "running forward" vs "running away"; the frames show Doug turning and leaving the trail, the beat reads.
- R05 t1 (1/3): judge saw the lantern "lying" not "falling"; the tumble happens between sampled frames (motion beat).
- R06 t1 (0/3): judge calls it a "toy train" with no sparks; it IS a stylized circus loco, and sparks are a sound job now.
- R18 t2 was the gate's problem take, not used; R18 t1 (1/3, "mouth open" judged on frames between words) is the mouth_sync pick.
- R20 t1 (1/3): "beetles resembling ants": the Blender ant plates read shell-like (known since 1:05 AM), no better take.
- R21 t3 (0/3): "stationary ants": a motion word judged on stills; the river holds in frame for the whole window.
- R30 t1 (1/3): judge missed the gap behind the wheel on 2 frames; the edge and falling pebbles are visible by eye.
- R03 t4 (0/3): no fallen log in the new still (the canon plate has none); identity was the bigger failure, fixed.
