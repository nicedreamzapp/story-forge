# sync_v5 — action frame vs sound onset (v5 cut), generated 2026-11-18

Action frame = the row-relative time I picked by LOOKING at the clip's 2 fps grid (or the code composite's frame); sound onset = the SFX/voice file's first sample above threshold, placed on that frame. Offset = onset minus action, in ms; flagged over 120 ms.

| cue | row | action frame (s) | sound onset (s) | offset ms | flag | what I saw |
|---|---|---|---|---|---|---|
| line N01 'This is Doug. Doug used to hunt bears.' | r01_hunt | 0.50 | 0.50 | +0 |  | word onset placed on the script time |
| line N02 'Not because he wanted to. His owner made him.' | r02_lookback | 5.20 | 5.20 | +0 |  | word onset placed on the script time |
| line N03 'One night, his nose found a bear.' | r03_found | 9.20 | 9.20 | +0 |  | word onset placed on the script time |
| line N04 'But this bear wasn't hurting anybody. He was saving a fox.' | r04_fox | 13.20 | 13.20 | +0 |  | word onset placed on the script time |
| line D01 'Huh. That bear is... cool.' | r05_watch | 17.80 | 17.80 | +0 |  | word onset placed on the script time |
| line N05 'So Doug led his owner away from the bear...' | r06_lead | 21.40 | 21.40 | +0 |  | word onset placed on the script time |
| line N06 '...right into a ditch.' | r07_ditch | 25.20 | 25.20 | +0 |  | word onset placed on the script time |
| line N07 'Then he went back.' | r08_hi | 28.60 | 28.60 | +0 |  | word onset placed on the script time |
| line L4 'Hi.' | r08_hi | 30.60 | 30.60 | +0 |  | word onset placed on the script time |
| line N08 'That bear was Hank. Doug never hunted again.' | r09_walkaway | 32.80 | 32.80 | +0 |  | word onset placed on the script time |
| line N09 'Now they rescue animals.' | r09_walkaway | 35.80 | 35.80 | +0 |  | word onset placed on the script time |
| line L1 'Rolling.' | r10_bench | 38.30 | 38.30 | +0 |  | word onset placed on the script time |
| line N10 'A fire wagon, and a crew that's all animals.' | r11_rollout | 39.50 | 39.50 | +0 |  | word onset placed on the script time |
| sfx dog_sniffs: nose on the trail from the first frame, dipping at ~0.5/1.5/2.5/3.5 s (NEW1 2 fps grid) | r01_hunt | 0.10 | 0.10 | +0 |  | NEW1_hunt 2 fps grid tiles 1-10: nose down throughout |
| sfx whistle_two_note [HERO]: the owner's two-note whistle: Doug flinches, head dips and eyes close at row 1.0 (NEW2 2 fps grid tile 3), whistle onset 100 ms ahead of the flinch | r02_lookback | 5.90 | 5.90 | +0 |  | NEW2_lookback 2 fps grid tile 3 (1.0 s): head down, eyes shut; tiles 4-8 eyes low |
| sfx dog_sniffs: Doug's nose dips to the trail (G_forest_r2 grid: nose on the ground from the first frame, dipping through 0.3-3.5) | r03_found | 9.30 | 9.30 | +0 |  | G_forest_r2 6-frame grid, nose down at frames 1-6 |
| sfx fox_yips: fox kicking in the wire, mouth open (NEW3 2 fps tiles 1-5, 0-2.0 s) | r04_fox | 13.30 | 13.30 | +0 |  | NEW3_fox 2 fps grid tiles 1-5 |
| sfx wire_twang [HERO]: the bear pulls the wire apart and the fox drops free at 2.5-3.0 (tiles 6-7); creak+twang file placed so the loud twang lands on the drop; v5 keeps 0.5 s of the creak before the twang, on the bear's pull (tiles 5-6) | r04_fox | 15.40 | 15.40 | +0 |  | NEW3_fox 2 fps grid tiles 6-7 (2.5-3.0 s): fox dropping out of the wire |
| sfx dog_barks: mouth opens barking at 2.5-3.0 (tiles 6-7) | r06_lead | 23.60 | 23.60 | +0 |  | NEW5_lead 2 fps grid tiles 6-7: mouth open |
| sfx splash_slosh [HERO]: splash/slosh on the cut: lantern already in the water, ripples visible from frame 1 (the narrator's 'ditch' lands on the cut) | r07_ditch | 25.20 | 25.20 | +0 |  | v4 fallback clip H_ditch lit lantern with ripples; plan D6 keyframe clip replaces it |
| sfx flame_hiss: soft hiss as the flame dies (fallback: light-out ramp 2.8-3.4 of the row) | r07_ditch | 28.00 | 28.00 | +0 |  | fallback ramp start = row dur - 0.6 |
| sfx paws_walking: the pair walking away (I_walkaway_r2 grid: legs moving from frame 1) | r09_walkaway | 32.80 | 32.80 | +0 |  | I_walkaway_r2 grid frames 1-6 walking |
| sfx morning_birds: morning birds on the dawn bench (was a bed in v4; now one soft cue on the row) | r10_bench | 36.30 | 36.30 | +0 |  | C_bench dawn light, oaks in frame |
| sfx hooves_wheels [HERO]: team walking, wheels turning from the first frame (K6 grid) | r11_rollout | 39.30 | 39.30 | +0 |  | D_rollout_k6 grid frames 1-6 |
| sfx wing_beats: geese wings beating (L_airlift grid: wings mid-beat at clip 0.8) | r12_goat | 44.30 | 44.30 | +0 |  | L_airlift grid frame 2 |
| sfx water_pour: two trunks already pouring at clip 0.6 (replaces the hissy v4 water_spray) | r13_turtle | 46.60 | 46.60 | +0 |  | E_turtle_r2 2 fps grid frames 3-7 |
| sfx kitten_mew: kitten's mouth open (F_kitten grid: open at clip 1.5-3.0; row in-point 1.2 -> row 0.3) | r14_kitten | 48.80 | 48.80 | +0 |  | F_kitten grid frames 3-5 |
| sfx otter_chirps: otters hauling, mouths/bodies moving from clip 1.4; v5 ends at 51.30 (stopdown) with a 120 ms reverb tail | r15_otters | 50.16 | 50.16 | +0 |  | M_otters grid frames 3-5 |

Cues: 28; over 120 ms: 0 (none)

Mouth rows checked by frame: 'Hi.' = N_hi jaw 2.0-2.7 of the clip -> word at row 2.0; bench 'Rolling.' = C_bench mouth opens at clip 2.4 (in 0.4) -> row 2.0;
button 'Rolling.' = K_button_r2 mouth opens at clip 2.0 (in 0.6) -> row 1.4; row 7 'ditch' = N06 spoken from row 0.0, 'ditch' ~1.3 s in, splash frame at row 1.2.
Montage cuts: theme_2 verse words measured by whisper word timestamps (music/theme_2_words.json): 'When a goat's' 9.5, 'turtle' ~11.4, 'kitten' ~13.7, 'drain' ~15.1 from the file; the cuts sit on those onsets (rows 12-15 starts).
UNCHECKED: the sung word onsets inside theme_2 are whisper estimates (segment level in the json; word level only where present); by ear is Matt's.