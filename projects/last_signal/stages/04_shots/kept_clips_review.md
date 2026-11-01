# 04_shots — kept clips review (part 1, 2026-10-31 ~6:30 AM)
Engine: LTX-2.5 bf16 (MLX). Previs = distilled --low-ram, 5 s, 832x448. Quality pass = --hq two-stage on the used shots only (final_plan.json).
Start stills: Z-Image-Turbo bf16 + Blender (ship). Every still went through beat_gate (logs/gate_stills_report.md, gate_stills2_report.md).

## Stills locked with a declared gate exception (rule 7: nothing silently lowers a bar)
- R03_dive: beat FAIL on both candidates ("ship floating, no motion visible"); a still cannot show the dive. Locked the Blender polish, and the clip is judged instead. The ship is small in frame: WEAK.
- R12_second_sun: beat PASS, set-continuity FAIL (monolith style differs from the plain master). Locked s606, the only frame with two suns.
- R13_crewmate_yanked: beat FAIL on 4 candidates over 2 rounds ("he looks like he is leaping"). Locked s707. The previs clip carries the beat: he is swept into the fog and vanishes by ~1.5 s.
- Beats reworded to visible states (motion lives in clip_beat): R01, R02, R03, R05, R06, R10, R18.

## Previs drafts (clips/previs/<id>_t1.mp4), frame-grid look by the builder (3 frames each)
| render | what I saw | usable window |
|---|---|---|
| R01 asteroids | ship grows toward camera, asteroids streak; coherent | 0-5 s |
| R02 cockpit | Captain works the throttle lever, red lamps, lightning outside | 0-5 s |
| R03 dive | ship small, drifting into orange cloud, lightning | 0-5 s, weak framing |
| R04 arrival | ship over the plain, dust, then the shadow swallows the frame (the shadow sweep reads) | 0-3.5 s |
| R05 claws | claw leg plants, dust and shards burst, then haze | 0-2.5 s |
| R06 monolith reveal | fast push through monoliths, fog rolls in | 0-3 s |
| R07 crew walk | both walk toward camera, faces stable | 0-5 s |
| R08 handwriting | glow spreads under the hand, hand stays still, push in | 0-5 s |
| R09 captain face | teal underlight, eyes widen, push in | 0-5 s |
| R10 lightwave | ring of teal light pulses among the monoliths | 0-5 s |
| R11 welcome | Captain frozen among glowing monoliths, lightning | 0-5 s |
| R12 second sun | rays sweep, ends in a white-out (good for the strobe "light") | 0-5 s |
| R13 yanked | swept into fog, gone by ~1.5 s | 0-1.5 s |
| R14 engines | nozzles erupt in blue fire and sparks | 0-5 s |
| R15 Watcher | rises, spine crown, teal eye line ignites, camera tilts up | 0-5 s |
| R16 boots | cracks race under the boots | 0-5 s |
| R17 sprint | runs at camera between monoliths | 0-5 s |
| R18 grab | ship between the stone talons, then dark rock engulfs the frame | 0-2 s |
| R19 eyes | eye line glows, push in | 0-5 s (kept as-is for the strobe, no hq re-render) |
| R20 scream | screams; his eyes flare teal (unscripted, reads as possession) | 0-5 s (strobe, kept as-is) |

## Quality pass (clips/takes/)
- R01_asteroids_t1 (hq, 528 s render, 3.7 s): plays, coherent, but the ship RECEDES instead of charging at camera. The previs draft is the better take for c01. Keep both as coverage.
- VL clip gate: UNCHECKED so far. Loading the VL judge alongside an LTX render would exceed the memory allowance, so it runs after the queue (tools/gate_file.py clips, then beat_gate).
Extra motion source: Blender ship/renders/anim_04_arrival.mp4 and anim_15_liftoff.mp4 (real camera moves).

## Quality pass verdicts (part 2, 2026-10-31 11:57 AM, builder frame-grid look of every take, 6 frames each)
VL clip gate ran 11:31-11:56 (logs/gate_clips_report.md): 10/44 PASS. Per-take keep/decline and the why: stages/04_shots/selects.md.
- KEEP (in the cut): previs R01; hq R02 t2, R03 t1, R04 t1, R05 t1, R06 t2, R07 t1, R08 t1, R09 t2, R10 t1/t2/t3, R11 t2, R12 t1, R13 t1/t2, R14 t1, R15 t1/t3, R16 t1, R17 t1/t2, R18 t1/t2/t3; previs R05/R12/R14/R15/R18/R19/R20 (strobe).
- KEEP as coverage: hq R01 t1, R02 t1, R04 t2, R06 t1/t3, R08 t2/t3, R09 t1, R11 t1, R15 t2; the other previs drafts.
- DECLINED + deleted: hq R04 t3 (the hull smears into a dark smoky disk, then black).
- Seen by eye, flagged: previs R06 grows a crowd of figures in the fog after ~3 s (never used past 2 s); R13 reads as flung, not clearly pulled backward; R16's glass cracks can read as splashing water.
