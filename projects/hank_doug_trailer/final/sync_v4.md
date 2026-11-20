# sync_v4 — action frame vs sound onset (v4 cut), generated 2026-11-18

Action frame = the row-relative time I picked by LOOKING at the clip's 2 fps grid (or the code composite's frame); sound onset = the SFX/voice file's first sample above threshold, placed on that frame. Offset = onset minus action, in ms; flagged over 120 ms.

| cue | row | action frame (s) | sound onset (s) | offset ms | flag | what I saw |
|---|---|---|---|---|---|---|
| line N01 'This is Doug. Doug used to hunt bears.' | r01_hunt | 0.50 | 0.50 | +0 |  | word onset placed on the script time; mouth frame checked in sync_v4.md |
| line N02 'Not because he wanted to. His owner made him.' | r02_lookback | 5.20 | 5.20 | +0 |  | word onset placed on the script time; mouth frame checked in sync_v4.md |
| line N03 'One night, his nose found a bear.' | r03_found | 9.20 | 9.20 | +0 |  | word onset placed on the script time; mouth frame checked in sync_v4.md |
| line N04 'But this bear wasn't hurting anybody. He was saving a fox.' | r04_fox | 13.20 | 13.20 | +0 |  | word onset placed on the script time; mouth frame checked in sync_v4.md |
| line D01 'Huh. That bear is... cool.' | r05_watch | 17.80 | 17.80 | +0 |  | word onset placed on the script time; mouth frame checked in sync_v4.md |
| line N05 'So Doug led his owner away from the bear...' | r06_lead | 21.40 | 21.40 | +0 |  | word onset placed on the script time; mouth frame checked in sync_v4.md |
| line N06 '...right into a ditch.' | r07_ditch | 25.20 | 25.20 | +0 |  | word onset placed on the script time; mouth frame checked in sync_v4.md |
| line N07 'Then he went back.' | r08_hi | 28.60 | 28.60 | +0 |  | word onset placed on the script time; mouth frame checked in sync_v4.md |
| line L4 'Hi.' | r08_hi | 30.60 | 30.60 | +0 |  | word onset placed on the script time; mouth frame checked in sync_v4.md |
| line N08 'That bear was Hank. Doug never hunted again.' | r09_walkaway | 32.80 | 32.80 | +0 |  | word onset placed on the script time; mouth frame checked in sync_v4.md |
| line N09 'Now they rescue animals.' | r09_walkaway | 35.80 | 35.80 | +0 |  | word onset placed on the script time; mouth frame checked in sync_v4.md |
| line L1 'Rolling.' | r10_bench | 38.30 | 38.30 | +0 |  | word onset placed on the script time; mouth frame checked in sync_v4.md |
| line N10 'A fire wagon, and a crew that's all animals.' | r11_rollout | 39.50 | 39.50 | +0 |  | word onset placed on the script time; mouth frame checked in sync_v4.md |
| line L6 'Rolling.' | r17_button | 58.10 | 58.10 | +0 |  | word onset placed on the script time; mouth frame checked in sync_v4.md |
| sfx dog_sniffs: Doug's nose dips to the trail (G_forest_r2 grid: nose on the ground from the first frame, dipping through 0.3-3.5) | r03_found | 9.30 | 9.30 | +0 |  | G_forest_r2 6-frame grid, nose down at frames 1-6 |
| sfx lantern_fall: lantern tumbles end over end (code parabola 0.0-1.2 of the row), the clank-tumble part of the file | r07_ditch | 25.40 | 25.40 | +0 |  | code: parabola frames 0.0-1.2, rotation 420 deg |
| sfx lantern_fall: SPLASH on the landing frame (row 1.2 = 27.2, the word 'ditch') | r07_ditch | 26.40 | 26.40 | +0 |  | code: landing frame at row 1.20, 4-frame painted splash 1.2-1.37 |
| sfx lantern_fall: hiss as the flame dies (grade ramp 2.4-3.0) | r07_ditch | 27.60 | 27.60 | +0 |  | code: grade ramp starts row 2.4 |
| sfx paws_walking: the pair walking away (I_walkaway_r2 grid: legs moving from frame 1) | r09_walkaway | 32.80 | 32.80 | +0 |  | I_walkaway_r2 grid frames 1-6 walking |
| sfx hooves_wheels: team walking, wheels turning from the first frame (K6 grid) | r11_rollout | 39.30 | 39.30 | +0 |  | D_rollout_k6 grid frames 1-6 |
| sfx wing_beats: geese wings beating (L_airlift grid: wings mid-beat at clip 0.8) | r12_goat | 44.30 | 44.30 | +0 |  | L_airlift grid frame 2 |
| sfx water_spray: two trunks already pouring at clip 0.6 (E_turtle_r2 grid frame 3 at 1.0 s shows both streams) | r13_turtle | 46.60 | 46.60 | +0 |  | E_turtle_r2 2 fps grid frames 3-7 |
| sfx kitten_mew: kitten's mouth open (F_kitten grid: open at clip 1.5-3.0; row in-point 1.2 -> row 0.3) | r14_kitten | 48.80 | 48.80 | +0 |  | F_kitten grid frames 3-5 |
| sfx otter_chirps: otters hauling, mouths/bodies moving from clip 1.4 | r15_otters | 50.16 | 50.16 | +0 |  | M_otters grid frames 3-5 |
| sfx chipmunk_squeak: chipmunk pops onto the rim (code composite pop 0.4-0.7 of the row; squeak on the top of the pop) | r17_button | 57.15 | 57.15 | +0 |  | code: pop eased 0.4-0.7 |
| sfx tuba_note: one soft tuba note on Hank's 'Rolling.' (mouth opens at clip 2.0 = row 1.4; K_button_r2 grid frame 3) | r17_button | 58.10 | 58.10 | +0 |  | K_button_r2 grid frame 3 at 2.0 s |
| sfx dog_sniffs: nose on the trail from the first frame, dipping at ~0.5/1.5/2.5/3.5 s (NEW1 2 fps grid) | r01_hunt | 0.10 | 0.10 | +0 |  | NEW1_hunt 2 fps grid tiles 1-10: nose down throughout |
| sfx whistle_two_note: the owner's two-note whistle: Doug flinches, head dips and eyes close at row 1.0 (NEW2 2 fps grid tile 3), whistle onset 100 ms ahead of the flinch | r02_lookback | 5.90 | 5.90 | +0 |  | NEW2_lookback 2 fps grid tile 3 (1.0 s): head down, eyes shut; tiles 4-8 eyes low |
| sfx fox_yips: fox kicking in the wire, mouth open (NEW3 2 fps tiles 1-5, 0-2.0 s) | r04_fox | 13.30 | 13.30 | +0 |  | NEW3_fox 2 fps grid tiles 1-5 |
| sfx wire_twang: the bear pulls the wire apart and the fox drops free at 2.5-3.0 (tiles 6-7); creak+twang file placed so the loud twang lands on the drop | r04_fox | 15.40 | 15.40 | +0 |  | NEW3_fox 2 fps grid tiles 6-7 (2.5-3.0 s): fox dropping out of the wire |
| sfx paws_running: the fox bolts right (tile 8 at 3.5 s) | r04_fox | 16.40 | 16.40 | +0 |  | NEW3_fox 2 fps grid tile 8 |
| sfx tail_thumps: Doug's tail rises and wags against the ferns from 1.5 s (NEW4 2 fps tiles 4-8) | r05_watch | 18.70 | 18.70 | +0 |  | NEW4_watch 2 fps grid tiles 4-8: tail up and swinging |
| sfx paws_running: Doug running toward us from the first frame (NEW5 2 fps tiles 1-8) | r06_lead | 21.20 | 21.20 | +0 |  | NEW5_lead 2 fps grid, running throughout |
| sfx dog_barks: mouth opens barking at 2.5-3.0 (tiles 6-7) | r06_lead | 23.60 | 23.60 | +0 |  | NEW5_lead 2 fps grid tiles 6-7: mouth open |

Cues: 34; over 120 ms: 0 (none)

Mouth rows checked by frame: 'Hi.' = N_hi jaw 2.0-2.7 of the clip -> word at row 2.0; bench 'Rolling.' = C_bench mouth opens at clip 2.4 (in 0.4) -> row 2.0;
button 'Rolling.' = K_button_r2 mouth opens at clip 2.0 (in 0.6) -> row 1.4; row 7 'ditch' = N06 spoken from row 0.0, 'ditch' ~1.3 s in, splash frame at row 1.2.
Montage cuts: theme_2 verse words measured by whisper word timestamps (music/theme_2_words.json): 'When a goat's' 9.5, 'turtle' ~11.4, 'kitten' ~13.7, 'drain' ~15.1 from the file; the cuts sit on those onsets (rows 12-15 starts).
UNCHECKED: the sung word onsets inside theme_2 are whisper estimates (segment level in the json; word level only where present); by ear is Matt's.
## Montage cuts vs sung word onsets, measured by whisper (word timestamps) on the v4 film itself
| cut | picture cut (s) | sung word | word onset in film (s) | offset ms | fix |
|---|---|---|---|---|---|
| goat | 44.30 | "When (a goat's stuck high)" | 44.40 | +100 | none needed |
| turtle | 46.20 -> 46.60 | "And (a turtle's stuck low)" | 46.60 | was -400, now 0 | cut moved to the word |
| kitten | 48.50 | "And (a kitten)" | 48.62 | +120 | kept (at the limit) |
| otters | 49.90 -> 50.16 | "stuck (in a drain)" | 50.16 | was -260, now 0 | cut moved to the word |
| title complete | 53.10 | "Hank" sung | 53.70 | title is complete 600 ms before "Hank" | as scripted (title before the name) |
Note: the first measurement heard "a ghost goes high" for "a goat's stuck high" at 45.16-45.98 (whisper mishearing of the sung line; UNCHECKED by ear).
