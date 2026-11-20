# sync_v52 — action frame vs sound onset (v5.2 cut), generated 2026-11-18

Action frame = the row-relative time picked by LOOKING at the clip's 2 fps strip; sound onset = the file's first sample above threshold, placed on that frame (onset-aligned in mix_v52b). Offset = onset minus action, in ms; flagged over 120 ms. Every effect is a real CC0 recording from sfx/library (LICENSES.md); no AI-generated sound.

| cue | row | action frame (s) | sound onset (s) | offset ms | flag | what I saw |
|---|---|---|---|---|---|---|
| line N01 'This is Doug. Doug used to hunt bears.' | r01_hunt | 0.50 | 0.50 | +0 |  | word onset placed on the script time (row-relative) |
| line N02 'Not because he wanted to. His owner made him.' | r02_lookback | 5.21 | 5.21 | +0 |  | word onset placed on the script time (row-relative) |
| line N03 'One night, his nose found a bear.' | r03_found | 9.26 | 9.26 | +0 |  | word onset placed on the script time (row-relative) |
| line N04 'But this bear wasn't hurting anybody. He was saving a fox.' | r04_fox | 13.24 | 13.24 | +0 |  | word onset placed on the script time (row-relative) |
| line D01 'Huh. That bear is... cool.' | r05_watch | 18.01 | 18.01 | +0 |  | word onset placed on the script time (row-relative) |
| line N05 'So Doug led his owner away from the bear...' | r06_lead | 21.19 | 21.19 | +0 |  | word onset placed on the script time (row-relative) |
| line N06 '...right into a ditch.' | r07_ditch | 25.17 | 25.17 | +0 |  | word onset placed on the script time (row-relative) |
| line N07 'Then he went back.' | r08_hi | 28.78 | 28.78 | +0 |  | word onset placed on the script time (row-relative) |
| line L4 'Hi.' | r08_hi | 30.78 | 30.78 | +0 |  | word onset placed on the script time (row-relative) |
| line N08 'That bear was Hank. Doug never hunted again.' | r09_walkaway | 32.55 | 32.55 | +0 |  | word onset placed on the script time (row-relative) |
| line N09 'Now they rescue animals.' | r09_walkaway | 35.55 | 35.55 | +0 |  | word onset placed on the script time (row-relative) |
| line L1 'Rolling.' | r10_bench | 38.52 | 38.52 | +0 |  | word onset placed on the script time (row-relative) |
| line N10 'A fire wagon, and a crew that's all animals.' | r11_rollout | 39.71 | 39.71 | +0 |  | word onset placed on the script time (row-relative) |
| sfx dirt_steps: Doug walks the trail nose-down, soft paw steps on the dirt trail from frame 1 | r01_hunt | 0.10 | 0.10 | +0 |  | G_hunt_red_s12 strip: walking from tile 1 |
| sfx dog_sniff: nose dipping on the trail | r01_hunt | 0.60 | 0.60 | +0 |  | G_hunt_red_s12 strip: nose down tiles 2-7 |
| sfx whistle: the owner's whistle: Doug flinches, head dips at row 1.0 (whistle onset 100 ms ahead) | r02_lookback | 5.91 | 5.91 | +0 |  | NEW2_lookback_red strip tile 3: head down, eyes shut |
| sfx dog_sniff: Doug's nose on the ground reaching the clearing | r03_found | 9.36 | 9.36 | +0 |  | G_forest_red strip: nose down tiles 1-5 |
| sfx fence_rattle: the fox kicking in the wire, the fence shaking | r04_fox | 13.24 | 13.24 | +0 |  | fox clip strip: fox struggling tiles 1-4 |
| sfx fox_yip: the fox's mouth open, yipping | r04_fox | 13.54 | 13.54 | +0 |  | fox clip strip tiles 2-3 |
| sfx wire_pull: the bear pulls the strands apart, the fence wire shakes and springs as the fox drops free | r04_fox | 15.45 | 15.45 | +0 |  | fox clip strip tiles 6-7 |
| sfx boots_dirt: the owner's boots on the dirt road, walking after Doug | r06_lead | 21.09 | 21.09 | +0 |  | ROAD_owner_v52 strip: both walking away from tile 1 |
| sfx stumble: the boot slides, he loses his footing | r07_ditch | 25.67 | 25.67 | +0 |  | DITCH_owner_v52 strip tiles 2-3 (0.5-1.0 s): arms out, boot sliding |
| sfx splash: he lands in the ditch water, the lantern goes under | r07_ditch | 26.42 | 26.42 | +0 |  | DITCH_owner_v52 strip: he vanishes into the reeds between tiles 3 and 4 (1.0-1.5 s), glow in the water at 1.5, out by 2.0 |
| sfx dirt_steps: the pair walking away up the road, soft and distant | r09_walkaway | 32.35 | 32.35 | +0 |  | I_walkaway_red strip: legs moving tiles 1-6 |
| sfx hooves: the team walking from frame 1 | r11_rollout | 39.51 | 39.51 | +0 |  | rollout strip: legs moving tiles 1-10 |
| sfx wagon_wheels: the wagon's wooden wheels on the dirt road | r11_rollout | 39.51 | 39.51 | +0 |  | rollout strip: wheels turning |
| sfx wings: the geese beating their wings, lifting the goat | r12_goat | 44.28 | 44.28 | +0 |  | GOAT_airlift_v52 strip: wings beating from tile 1 |
| sfx water_pour: water pouring from the barrel onto the mud | r13_turtle | 46.67 | 46.67 | +0 |  | TURTLE strip: pour from tile 1 |
| sfx kitten_mew: the kitten's mouth opens behind the grate | r14_kitten | 50.96 | 50.96 | +0 |  | F_kitten strip tiles 7-8 (clip 3.0-3.5, in 1.2 -> row 1.8-2.3) |
| sfx otters: the otters chattering as they hand the kitten up | r15_otters | 51.65 | 51.65 | +0 |  | OTTERS strip |

Cues: 30; over 120 ms: 0 by construction (onset-aligned placement).

Beds: bed:birds_dawn dawn birds bed from the bench through the rescues 36.523-55.523 s at -37 dB; bed:night_forest quiet night forest bed under the hunt rows 1-9 0.0-38.0 s at -38 dB
Music: music:music/anthem_9_end.wav continuous from 0 (instrumental stem music/stems/htdemucs/anthem_9/no_vocals.wav until 44.277), bed -22.0 dB -> full -11.0 dB by 53.835, stopdown -8.0 dB on the half-bar before, duck -9.0 dB under voices

Mouth rows checked by frame: 'Hi.' = N_hi jaw opens 1.5-2.0 s of the clip -> word at row 2.0 (same Hank voice as 'Rolling.', voice_hi_v52); bench 'Rolling.' = C_bench_red a2v mouth -> row 2.0.