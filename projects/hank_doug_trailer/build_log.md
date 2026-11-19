# Build log — Hank & Doug's Wild Rescue trailer (one-canvas v2)
Started 2026-11-17 7:14 PM PST (Matt: "Approve + build"). Target done ~9:15 PM. Builder: Fable.
ETA plan: stills 20 · animated clips 50 · talking 12 · voices 5 · theme 5 · code layers +10 · cut+QC 15.

| Part | Start | End | Min | Note |
|---|---|---|---|---|
| read rules + inputs | 7:14p | 7:24p | 10 | CLAUDE.md, pipeline, _shared/*, script v2, look test |
| theme song (Song Forge, 2 vocal + 1 music box) | 7:18p | 7:20p | 2 | ETA 5 |
| voices (ChatterBox 13 takes + Heart narrator) | 7:19p | 7:21p | 2 | ETA 5; fx + whisper check later |
| stills (Krea 2 Turbo, 19 jobs) | 7:25p | | | ETA 20 |
| stage 02 docs (Sonnet agent: beats/continuity/story_test) | 7:27p | 7:29p | 2 | |
| voice fx + whisper picks (6 picks, 4 alts, 3 duds deleted) | 7:30p | 7:36p | 6 | young Hank = Hank +7 st |
| stills judged so far: A,B unseen; C ok (Doug recolored in code), D camel 2 humps x2 -> retry + clone fix, E ok, F ok, G lantern painted out + recolor, H1 ok, H2 cutout ok, I recolor | 7:28p | 7:37p | | |
| stills main batch (19 jobs) | 7:25p | ~7:42p | 17 | retry batch (D dromedary x2, K asleep x2, chipmunk cutout) follows |
| previs (LTX-2.5: 4 motion + 2 a2v) | queued 7:40p | | | starts when Krea r2 batch ends |
| SFX (MMAudio, 10 cues) | 7:40p | | | runs beside Krea/LTX under the memory broker |
| stills judged: L ok, M ok (bear's paws on the ground, chain from top of frame: defect), N s1101 picked (s1102 frontal = alt) | 7:38p | 7:42p | | |
| D retry (dromedary wording) s1105: two humps AGAIN (3rd time), Doug + elephants missing -> stop retrying; D = s1102 with the rear hump clone-stamped out | 7:43p | 7:44p | | |
| D s1106: two humps, no elephants -> s1102 fix stays | 7:45p | | | |
| K retry s1105: awake again, no chipmunk (3rd time) -> K = s1101 (resting pile, eyes open = known defect); chipmunk = code cutout on the wheel rim | 7:46p | | | |
| stills retry batch | 7:42p | 7:48p | 6 | stills total 7:25-7:48 = 23 min vs ETA 20 |
| beat 4 leading edge dropped (nose at the frame edge in every D render; code device kept on beat 12) | 7:54p | | | |
| previs LTX-2.5: D 120 s, L 206 s, E 105 s, M 91 s, N a2v 501 s | 7:47p | ~8:15p | | K a2v running |
| coverage gate (frozen rule 29): BLOCKED, 5 of 15 beats OK, 10 short, 165 s footage vs 180 s needed; no time to add setups, reported honestly | 8:08p | | | |
| K a2v (6 s) 801 s; previs pass total 7:47-8:18 = 31 min | | 8:18p | 31 | ETA animated 50 + talking 12 |
| v1 cut (previs clips) rendered + mixed + audio gate FIXED | 8:19p | 8:21p | 2 | K6 D still rendering |
| K6 Pro D rollout 5 s: load ~8:19-8:33, 10 steps at ~150 s/step (measured 718 s for 3 s; 5 s is ~2x), done ~9:00 | 8:19p | | | over the 50 min clip ETA |
| audio_check v1: FAIL score vocals (theme is a vocal song by design), FAIL L4 Hi 50%, WARN music near voice at 6/12/18 s, WARN LRA 19 (silent open by design) | 8:41p | | | |
| v2 cut (K6 D) rendered 83 s, mixed, audio gate FIXED -14.5 LUFS | 9:01p | 9:03p | 2 | gates v2 queued behind film_qc v1 |
| audio_check v2: same as v1 (score vocals FAIL by design, L4 Hi 50%, WARN near-voice at 18 s, LRA 19) | 9:06p | | | |
| declined takes deleted same session (frozen rule 13): D s1104/s1105/s1106, K s1105/s1106, C s1102; D_rollout_s1102 (raw) + K s1102 + N s1102 + J raw + A raw stay as listed coverage | 9:10p | | | |

## ETA vs actual (clock times PST)
| Part | ETA min | Actual | Start | End |
|---|---|---|---|---|
| stills (Krea 2 Turbo, 19 + 5 retry jobs, judged by eye, code fixes) | 20 | 23 | 7:25p | 7:48p |
| animated clips (LTX previs 4 clips 9 min; K6 Pro hero D 43 min incl. load, GPU shared with film_qc) | 50 | 52 | 7:47p | 9:01p (previs 7:47-7:57, K6 8:19-9:01) |
| talking clips (LTX a2v N 8.4 min, K 13.4 min) | 12 | 22 | 7:57p | 8:18p |
| voices (ChatterBox + Heart + fx + whisper picks) | 5 | 8 | 7:19p | 7:36p (spread) |
| theme (Song Forge 2 vocal + 1 music box) | 5 | 2 | 7:18p | 7:20p |
| code layers (paintlib + finish.py + previews + fixes) | +10 | ~45 (overlapped with renders) | 7:30p | 8:21p |
| cut + QC (mix, gates, film_qc x2, continuity, watch sheet, notes) | 15 | ~45 (film_qc v2 ran 9:08-~9:25) | 8:19p | ~9:30p |
Wall clock: 7:14p -> ~9:30p (target 9:15p). Over by ~15 min: the K6 hero clip at 5 s took 43 min against the 12 min/3 s measurement, and film_qc had to run twice (v1 while K6 rendered, v2 on the final).
| continuity_check re-run: FAIL 59 pass / 6 violations (Doug colour x4, wagon rolls left, team count 1 ballot) | 9:15p | 9:26p | 11 | |
| DONE: final/hank_doug_wild_rescue_trailer.mp4, gates read, known_defects written, m5-bigjob end | 9:27p | 9:28p | | wall clock 7:14p-9:28p = 134 min vs 120 planned |
| v3 fix pass start (Matt 9:55p yes): 9 LTX i2v clips queued, 4 natural SFX queued | 9:57p | | | |
| alarm sound: SFX tone scan clean on all 10 MMAudio files; the v2 synthesized crickets bed (gated 4.2 kHz pulse, 26% narrow-band frames) and the synth tuba are the suspects; both removed, natural MMAudio beds queued | 9:59p | 10:02p | 3 | |
| v3 clips so far: K 160 s (reject, morph), A 276 s keep, B 194 s keep, C 186 s keep, F 128 s keep, G 162 s (reject: lantern appears, green saddle, slide), H 183 s keep; I, J, K_r2, G_r2 queued | 9:58p | | | |
| v3 clips: I 138 s (reject: tilt + green saddle), J 199 s keep, K_r2 191 s keep, G_r2 ~210 s keep, I_r2 ~180 s keep; 9 planned + 3 retries = 12 LTX renders 9:58p-10:35p | 9:58p | 10:35p | 37 | |
| v3 render (first run died silently at 4.9 s, relaunched) 64 s; mix v3 (theme_2 sung sections, natural beds, ducked); audio gate FIXED -14.5 LUFS; 59.00 s | 10:35p | 10:42p | 7 | gates v3 started 10:42p |
| declined v3 takes deleted (K seed 21, G first, I first; strong-recolor stills); manifest candidates refreshed | 10:45p | | | |

## v3 fix pass — ETA vs actual (Matt approved ~60 min at 9:55 PM; deadline 11:00 PM)
| Part | Start | End | Min |
|---|---|---|---|
| hand-off (m5-bigjob start, watcher, gentle-Doug still, ditch+lantern composite) | 9:56p | 9:58p | 2 |
| 12 LTX-2.5 i2v renders (9 planned + 3 retries, 2-5 min each, judged by grid) | 9:58p | 10:35p | 37 |
| 4 natural SFX (MMAudio) + tone scans; alarm diagnosis | 9:58p | 10:05p | 7 (beside LTX) |
| finish_v3 + mix_v3 written and dry-run | 10:00p | 10:15p | 15 (beside LTX) |
| render (died once silently, relaunched) + mix + mux + audio gate + 2 fps sheet | 10:35p | 10:42p | 7 |
| gates: audio_check, film_qc (6 min), continuity (11 min), notes | 10:42p | 11:00p | 18 |
Wall clock 9:56p -> 11:00p = 64 min vs 60 planned. Hand-back (m5-bigjob end) 11:00p.
| turtle fix: E re-render 99 s, keep; picture re-render, re-mux, audio gate, sheet | 11:01p | 11:06p | 5 | |
| turtle fix: E re-render 99 s keep; picture re-render (foreground run died again, detached run 68 s), re-mux, audio gate, sheet | 11:01p | 11:08p | 7 | |

## v4 build — Matt approved script_v4 at 11:48 PM ("Approve + build"), budget ~65 min, target ~12:55 AM
| Part | Start | End | Min | Note |
|---|---|---|---|---|
| hand-off + launches: voices (10 narrator + Doug), 10 SFX, 5 Krea stills, all in parallel | 11:49p | 11:52p | 3 | |
| v4 voices: 10 narrator (Heart) + Doug 'Huh. That bear is... cool.' (wr3_doug s303, 2.27 s), whisper exact except N05 heard 'let' for 'led' (UNCHECKED by ear); every line fits its slot, N09 moved to 36.2 so Hank's word stays at 38.4 | 11:50p | 11:54p | 4 | |
| v4 stills: 5 Krea + fox retry (r2 picked: fox hanging in the wire, bear's paws on it); lanterns painted out of G_hunt (2) and ROAD_ditch (1) in code (must_not), Doug gentle-recolored on 4 stills | 11:50p | 11:59p | 9 | |
| v4 clips: 5 LTX renders 11:58p-12:13a (124/188/120/216/209 s), all kept, fox trimmed at 4.2 s | 11:58p | 12:13a | 15 | |
| v4 picture 67 s, mix (42 placed, 34 sync cues, 0 over 120 ms), manifest/timeline/sync table, mux, audio gate FIXED, 2 fps sheet watched | 12:13a | 12:16a | 3 | gates v4 (audio_check + film_qc) started 12:16a |
| montage cuts moved to the measured sung word onsets (turtle 46.2->46.6, otters 49.9->50.16); picture re-render + re-mix | 12:16a | | | |
| v4 re-render (cuts on the sung words) 67 s, re-mix, mux, audio gate FIXED, 2 fps sheet; gates v4 (audio_check + film_qc) started on the final file | 12:16a | 12:17a | 1 | |
| gates v4: audio_check + film_qc (7 min), notes | 12:17a | 12:26a | 9 | |
v4 wall clock 11:49p -> 12:27a = 38 min vs 65 planned. Parts: voices 4 (ETA 10), stills 9 (ETA 10), LTX clips 15 (ETA 15), SFX 7 beside them,
cut+mix+sync 3 (+1 re-lay for the sung words), gates 9 (ETA 15). Hand-back 12:27a.
