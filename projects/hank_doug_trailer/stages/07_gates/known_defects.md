# known_defects — Hank & Doug's Wild Rescue trailer (one canvas, v2) — written 2026-11-17 9:16 PM PST by Fable (builder)
Film: final/hank_doug_wild_rescue_trailer.mp4, 1920x1080, 24 fps, 60.01 s, stereo AAC, -14.5 LUFS / -1.3 dBTP (final_audio_gate FIXED).
Watched the full cut start to finish on 2026-11-17: as a 60-tile contact sheet (one frame every second, final/contact_sheet_v2.jpg) plus
1-second previews of every beat during the build. I cannot play video in real time or hear audio: motion between the sampled frames and
everything audible are UNCHECKED by me and left to Matt's eyes and ears.

## film_qc (pipeline-tools/film_qc.py on the final file, in-process Qwen3-VL-32B + mlx-whisper), verbatim counts
Checks run: 79 | passed: 62 | failed: 17   (exit 0 on the chained run; report final/film_qc_report.md)
- lipsync FAILs (7): 12.3 Hank "Rolling." 0/6 (profile still, no mouth clip: script allowed the still); 14.6 narrator 0/6 and 35.2 / 39.4 /
  46.3 Doug 0/6 (all V.O. lines with no on-screen mouth by script; the judge has no V.O. flag); 41.0 Young Hank 0/6 (the a2v jaw opens
  ~41.0-41.7 but the judge did not see it as mouth motion; 1 sample read Doug as the speaker); 58.5 Hank 2/6 (33%, need 50%).
- artifact FAILs (9): 27.5 (the unpainted linen state of the drain grate read as "a sketch-like drawing of vertical bars": that IS the
  effect); 30.5-33.5 (the otter chain: the judge describes stacked otters holding each other and the kitten, no deformity named);
  35.5-38.5 (the old-paint flashback: bear and dog in a forest, painterly; no deformity named). My own look at those seconds: the otters
  are a chain of bodies holding feet as scripted; the flashback frames carry the craquelure and the varnish grade; Doug's shoulder keeps
  a dark patch (partial recolor).
- audio FAIL (1): 'Hi.' at 41.0 NOT HEARD by film_qc's whisper pass. A direct mlx-whisper re-listen of 40.3-42.3 s heard exactly "Hi."
- PASS: identity sheet (5 scenes), silence checks, the other 50 artifact samples (every second 0-60 except the 9 above), 6 of 7 lines heard.
UNCHECKED by film_qc: phoneme-level lip precision, taste, music by ear.

## audio_check (final/audio_check_report.md): FAIL, 2 fail, 3 warn
- FAIL score vocals: the vocal stem sits 3.1 dB under the music (gate wants an instrumental score). By design: Matt approved a sung
  theme (theme_song.md), so this gate's premise does not fit this film. Whether the lead sings "Doug" or "Tug" (whisper wrote "Tug" on
  theme_1) is UNCHECKED (ears only); theme_2 (alternate) was heard as "Doug".
- FAIL line 'Hi.' 50%: one-word line; the direct re-listen heard it exactly (above).
- WARN score repeats (the chorus repeats by design); WARN music within 6 dB of a voice at 18 s (the sung verse vs. the narrator tail);
  WARN LRA 19.1 LU (the first 9 s are wind and animal calls only, then a full band: the dynamic range is the design).

## continuity_check: see the line appended below (first run died on a timeline schema key; re-run on the final file).

## coverage_gate (frozen rule 29): BLOCKED. 5 of 15 beats have >= 3 setups (b01, b03, b04, b10, b14); 10 beats have 1-2;
165 s of footage against 180 s needed. Not fixed: no render time left inside the 2-hour box.

## Seen by eye (every still looked at in full, every clip as a 6-frame strip)
- Doug: Krea painted him caramel with a black saddle on every seed; code recolor fixed C, G, I; on N only the shoulder was treated
  and a dark patch remains lower left; in the K button he is tan with a dark saddle (not recolored: the a2v clip rendered from it).
- Camel: two humps on every Krea seed (6 renders); rear hump clone-stamped out on D and J; the back line is soft where it was.
- Hank's chest fur still reads a little feathery (best of 4 seeds used).
- D rollout (K6 Pro): the camera pushes in instead of tracking; the horse leaves frame left by ~4.5 s; the elephants carry no
  barrels and drop out of frame right early; Doug is small and tan on the bench. Beat 4's "leading edge" device was dropped (the
  horse's nose sits at the frame edge in every D render, so there is no "ahead" inside the frame); the wet edge lives on beat 12.
- E turtle: sits in water rather than sunk in mud ("stuck" is weak); the LTX clip gives one trunk from above, not two from the sides.
- F kitten: mouth closed (the ring still rises from her).
- G forest: Young Hank stands behind the log looking surprised rather than crouched with ears flat; a painted lantern at the right
  edge (must_not) was painted out in code and is also outside the framing.
- K button: nobody is asleep (3 seeds, all awake; eyes open throughout); the marmot is on Hank's head and the lantern is lit; the
  chipmunk is a composited cutout that pops onto the wheel rim at 56.6 s; the a2v camera drifts back/right and the sky warms.
- L airlift: ropes run sideways to the geese (reads as a tow); the platform rises only a little.
- M otters: the chain hangs from the top of frame; Hank's paws rest on the cobbles instead of holding the top otter.
- N "Hi.": jaw opens ~0.4 s after the conditioned word; the line was moved to 41.0 and the bloom to 41.3 to match.
- Beat 1: the marmot is painted hunched; "stands tall" is sold by the ripple arrival only.
- Joins: beat 7-8 is a pale wash, 8-9 a code trunk wipe; both plainer than the script's full-frame passes. The whip-pans show
  replicated-edge streaks for a few frames at their peak (by design hidden in blur; visible on a frame grab).
- Title: 25 characters, fully painted by 50.2 s and held to 53.7 s (3.5 s; needs 3.2 s): PASS by hand; text_readtime_check did not
  pick up texts.json for a film project and reported "no on-screen text declared".
- Stage approvals: no APPROVED.md for stages 02-07 (Matt approves when he watches); stage notes in each stages/NN folder.

## continuity_check (re-run 9:15-9:26 PM on the final file; final/continuity_report.md): FAIL, 59 pass, 6 violations
- doug_colour FAIL at b04 (13 s), b09 (34 s), b12 (46 s), b14 (54 s): the judge does not see "one solid russet-red coat" on Doug in the
  rollout (small tan Doug on the bench), the flashback (varnish grade over the recolor), the walk-away (seen from behind, recolor partial)
  and the button (not recolored at all). Doug's colour drift is the one defect every gate and my eye agree on.
- wagon_rolls_right FAIL at b04: the team walks LEFT in every D render (the still was painted horse-at-left facing left); the script's
  "rolls right" is not met; the pulling geometry (team out in front, wagon behind) holds.
- team_is_four FAIL at b04 (1 of 3 ballots YES): the cow is partly hidden behind the camel in some frames of the K6 clip.
- PASS (59): no visible lantern holder in the flashback, flashback cast only, one wagon everywhere, camel one hump at b04 and b13,
  bench cast only, Hank's colour, the lantern on the post, lit/unlit states, no humans.
Story sheet (final/story_sheet.md + .png) read as a first-time viewer: the picture alone carries "animals in a painted world answer
calls for help; the dog once tracked the bear; a lantern is left behind; they ride into the sunset"; what a stranger would misread:
that the flashback is a different, darker film rather than the past (no spoken time marker reaches the eye; it is in Doug's V.O. only).

# v3 fix pass — 2026-11-17, Matt's notes at 9:55 PM ("frozen frames, not full animation, too much not moving, a swirl at the end with the cart going back, an alarm sound")
Film: final/hank_doug_wild_rescue_trailer_v3.mp4, 1920x1080, 24 fps, 59.00 s (14 straight cuts, two short dissolves: into the forest, out of the ditch),
stereo AAC, -14.5 LUFS / -1.3 dBTP (final_audio_gate FIXED). v2 kept on disk until Matt approves. Contact sheet at 2 fps: final/contact_sheet_v3_2fps.jpg.
What changed: every code paint layer is gone (no linen frames, rings, reveals, whip streaks, crackle, wash, trunk wipe, chipmunk circle, arc ribbons);
every still-only beat is now a real LTX-2.5 i2v clip trimmed to its real length (goat, marmot, bench, kitten, forest, ditch lantern, walk-away,
title hill); the button was re-rendered locked-off (wagon parked, sky still); the K6 rollout, airlift, turtle, otters and the "Hi." a2v clip stay;
Doug on the bench is a gentle hue-only recolor (no saturation boost); the flashback carries a plain cool grade only; the title fades in over the
rolling silhouette. Watched the full v3 cut as the 2 fps sheet (118 tiles) plus a 6-frame grid of every clip; real-time motion and all audio UNCHECKED by me.
The alarm sound: no MMAudio SFX carried a sustained tone (tone scan on all 10, longest narrow band 0.15 s). The v2 synthesized crickets bed
(a 4.2 kHz pulse gated at 14 Hz, 26% of its frames narrow-band) is the likeliest "alarm"; the synthesized tuba (a pure 54 Hz harmonic stack)
second; the filtered-noise wind bed third. All three synthetic beds are gone; wind, crickets and a softer two-note marmot chirp are MMAudio
renders (tone scan clean), every paint_shhk is gone, and the new MMAudio tuba note scanned as a 1.3 s pure 495 Hz tone so it was dropped too.
Theme: the sung sections now come from music/theme_2.wav (whisper heard "Hank and Doug" on it; it heard "Tug" on theme_1); theme_1 is used only
for the 1.1 s "Rollin'! Here we go!" sting. Whether theme_2's phrasing lands as well by ear is UNCHECKED.
Seen by eye in v3 (clip grids):
- Rejected and re-rendered once each: K (marmot vanished, Doug's face morphed), G (a lantern materialised and slid in; Doug's strong recolor went
  green in motion), I (camera tilted to a huge moon, the pair dropped out of frame, green-striped saddle). The retries are clean on those points.
- Still true: Doug is tan with a black saddle in the forest (raw colours used to avoid the green) and the K6 rollout; a slight green tint on his
  saddle in the walk-away retry; the K6 rollout camera pushes in and the horse leaves frame by ~4.5 s; the K button still has everyone awake and a
  slight camera drift; the title-hill team walks left (same direction as the rollout; the script said right); the ditch lantern's flame does not
  visibly go out on its own, so the light-out is a 1 s grade ramp; Hank's bench mouth opens while he turns to camera (the script had him in profile).
- Beat 1 (the ring running down the mountain) and beat 7's "tiniest ring" no longer exist as devices; the story now reads as plain cuts between
  the calls and the rescues. The script's "one unbroken shot" idea is not in v3 by Matt's direction.

## v3 gates (run on final/hank_doug_wild_rescue_trailer_v3.mp4, 10:42-10:59 PM)
film_qc, verbatim: Checks run: 78 | passed: 64 | failed: 14   (exit 0 on the chained run; final/film_qc_v3_report.md)
- lipsync FAILs (6): 10.4 Hank 2/6 (33%, the bench clip's jaw opens while he turns); 13.2 narrator, 34.0 / 38.3 / 45.3 Doug 0/6 (all V.O.,
  no on-screen mouth by script); 40.0 Young Hank 0/6 (the a2v jaw move is small; one ballot read Doug as the speaker).
- artifact FAILs (7): 24.5 (turtle in the pool; judge text descriptive, no deformity named), 26.5 and 27.5 (kitten through the grate; "upon close
  inspection" text truncated by the tool), 29.5-32.5 (otter chain; the judge describes stacked otters holding each other, no deformity named).
  My own look at those seconds on the 2 fps sheet: the turtle clip's water arcs, the kitten mewing, the otters hauling; nothing merged or extra.
- audio FAIL (1): 'Hi.' at 40.0 NOT HEARD by film_qc's whisper pass; a direct mlx-whisper re-listen of 39.4-41.4 s heard 'Hi.'; audio_check's
  per-line re-listen passed every one of the 7 lines on v3.
- PASS: identity sheet, silence checks, the other 52 artifact samples, 6 of 7 lines in the transcript pass.
audio_check v3 (final/audio_check_v3_report.md): FAIL, 2 fail, 3 warn. FAIL score vocals (sung theme by design, gate premise does not fit);
FAIL balance at 10 s (the sung pickup "here we go" lands on Hank's "Rolling." by design) and 56 s (the sting after the word); WARN hard jumps in
the score at 0.8 / 1.6 s (theme_2's own intro), WARN music within 6 dB of a voice at 10-24 s (the sung verse against the narrator tail, demucs
counts sung vocals as voice), WARN LRA 19.0 (the quiet open then the full band, by design). Every line heard in its own window.
continuity_check v3 (final/continuity_report.md): FAIL, 55 pass, 8 violations: doug_colour at b03 (gentle recolor still reads tan to the judge),
b04, b09, b12, b14; young_hank_is_hank at b12 (seen from behind, the judge could not match him); wagon_rolls_right at b04 (team walks left);
team_is_four at b04 (1 of 3 ballots). The lantern, cast-only, one-wagon, one-hump and no-humans rules all pass.
coverage_gate: unchanged (5 of 15 OK; still-only beats now have a still + one or two clips each, 165 s footage).
Watched the full v3 cut start to finish on 2026-11-17 as the 2 fps contact sheet (final/contact_sheet_v3_2fps.jpg) plus every clip's 6-frame grid.
Turtle fix 11:01-11:08 PM (coordinator's catch): the flat blue ribbons were baked into the LTX previs clip, not the still; the beat was re-rendered
from the clean still with translucent splashy water from two trunks (clips/v3/E_turtle_r2.mp4, kept on the first try), swapped into v3, re-muxed,
audio gate re-run (picture-only change); film_qc/continuity were not re-run for this one 4 s clip: its frames are UNCHECKED by the VL judge.
Note for the pipeline: tools/finish_v3.py dies silently when run in the harness foreground (twice); it completes when launched detached with nohup.

# v4 — script_v4 "Doug leaves the hunt", built 2026-11-17 11:49 PM to 2026-11-18 ~12:25 AM (Matt approved script_v4 at 11:48 PM)
Film: final/hank_doug_wild_rescue_trailer_v4.mp4, 1920x1080, 24 fps, 60.01 s, straight cuts, -14.5 LUFS / -1.9 dBTP (final_audio_gate FIXED). v3 kept.
Contact sheet at 2 fps: final/contact_sheet_v4_2fps.jpg (watched every tile, 120 of them). Sync table: final/sync_v4.md (34 cues, 0 over 120 ms by
construction: each sound's measured onset is placed on the action frame I picked from the clip's 2 fps grid; the pick itself is +-250 ms, the grid's
step, and by ear it is UNCHECKED).
Sound first: 10 narrator lines (Kokoro Heart) + Doug's "Huh. That bear is... cool." (wr3_doug) recorded, whisper-checked (all exact except N05 heard
"let" for "led": UNCHECKED by ear), measured; every line fits its slot; N09 moved to 36.2 so Hank's "Rolling." stays on his mouth frame at 38.3.
The timeline was re-laid from the real durations and from the fox clip trim (row 4 = 4.2 s; +0.4 ditch, +0.3 walk-away, +0.1 button).
New footage: 5 Krea stills (+1 fox retry, r2 picked) and 5 LTX i2v clips, all kept on the first render; lanterns Krea painted into G_hunt (two) and
ROAD_ditch were painted out in code (must_not); Doug gently recolored on four stills (hue only).
Seen by eye in v4:
- NEW1 hunt: Doug's saddle carries a faint olive tint in motion (the recolor artifact, milder than v3's green); the glow does not sway, so no lantern-creak cue.
- NEW2 look-back: no visible glow swing; Doug's flinch (head dips, eyes shut at 1.0 s) is the whistle's visible action and the whistle sits 100 ms before it.
- NEW3 fox: the fox hangs in the wire by its front paws rather than one hind leg; from 4.0 s the bear lunges at camera and smears, so the row ends at 4.2 s.
- NEW4 watch: the tail wag is very large (the tail swings up into frame); eyes stay sad rather than soft.
- NEW5 lead: Doug runs TOWARD camera (the script had him running away toward the bend); the ditch is in frame at right; a tiny flame point shows on a
  trunk in a few frames (the glow's source, not a lantern object); the glow does not lurch, so the script's second whistle has no visible action and was not placed.
- Row 7: the lantern tumble is the code cutout on a parabola with the 4-frame painted splash (as script_v4 row 7 specifies); the flame does not go out on its own
  in the clip, the light-out is the grade ramp over the last 0.6 s.
- Row 10 bench: Hank turns to camera while speaking (not profile); Doug's gentle recolor still reads tan to the continuity judge (v3 result).
- Montage: the sung verse words are placed from whisper segment timestamps on theme_2 (word-level timestamps were not present for every word), so the cut-on-word
  claim for rows 12-15 is approximate (UNCHECKED by ear).
- Still true from v3: K6 rollout camera pushes in and the horse leaves frame by ~4.5 s; elephants carry no barrels; the button crew is awake; the title-hill team
  walks left; Doug's colour continuity (tan/black saddle in the forest and rollout clips).
- Not run on v4: continuity_check (not in the v4 gate list); coverage gate unchanged (blocked).

## v4 gates (final file, 12:17-12:25 AM)
film_qc, verbatim: Checks run: 95 | passed: 75 | failed: 20   (exit 0 on the chained run; final/film_qc_v4_report.md)
- lipsync FAILs (13): 11 are narrator or Doug V.O. lines with no on-screen mouth by design (0.2, 4.9, 8.9, 12.9, 17.8 Doug V.O., 21.1, 24.9, 28.3,
  32.5, 35.5, 39.2); 30.6 Young Hank "Hi." 0/6 (the small a2v jaw move, one ballot read Doug); 38.3 Hank bench "Rolling." 0/6 (his mouth opens while
  he turns to camera at clip 2.4; the judge did not read it as speech).
- artifact FAILs (6): 12.5 (G_forest: bear and "basset hound", descriptive, no deformity named), 47.5 (turtle: "elephant-like feet (or po…", the two
  trunks read as feet to the judge), 48.5 / 49.5 (kitten through the grate), 50.5 / 51.5 (otter chain). My 2 fps look: nothing merged or extra.
- audio FAIL (1): 'Hi.' at 30.6 not heard by film_qc's whisper; direct re-listen of 30.0-32.0 heard 'Hi.'.
- PASS: identity sheet, silence checks, the other 54 artifact samples, 13 of 14 lines in the transcript pass.
audio_check v4 (final/audio_check_v4_report.md): FAIL, 2 fail, 2 warn: FAIL score vocals (sung theme by design); FAIL balance at 46 s (the sung
verse vs the narrator average, by design: no narrator speaks there); WARN theme_2's own intro jumps at 0.8/1.6 s; WARN music within 6 dB of a voice at
0-2 s (crickets bed vs the first line; the bed is -26 dB), 10 s, 44-48 s (the sung verse counted as voice). Every spoken line heard in its own window.
final_audio_gate: FIXED (-14.5 LUFS / -1.9 dBTP). Sync table: final/sync_v4.md, 34 cues 0 over 120 ms by construction, plus the montage word rows
(two cuts moved onto the measured sung words). Watched the full v4 cut start to finish on 2026-11-18 as the 2 fps contact sheet (final/contact_sheet_v4_2fps.jpg).

# v5 fix pass, steps 1-4 only — 2026-11-18 1:57-2:05 AM (Matt approved plan_v5 at 1:57 AM, ending A: NO button)
Decision written at the top of stages/01_story/plan_v5.md. Nothing in v3/v4 was edited; all new files are *_v5.
1. Sound (no picture render). Crickets bed gone. 3 clips re-made with MMAudio large 44k (sfx/v5/raw: splash_slosh, flame_hiss,
   water_pour; seeds 511-513; snore + chipmunk not made, ending A). tools/sfx_clean_v5.py: HP 100 / LP 9k / noisereduce stationary 50%
   over the whole source, then hard gate to the cue window (10 ms fades), -6 dBFS peak -> sfx/v5/clean (15 cues, tools/cues_v5.json).
   Energy above 9 kHz fell 9-20 dB per clip; the in-window floor barely moved (the clips are dense). Tone scan (tools/sfx_tone_check_v5.py,
   0.3 s threshold): 0 flagged. Dropped: tail_thumps, paws_running, lantern_creak, lantern_fall, tuba, wind, paint_shhk, marmot x2,
   water_spray, chipmunk, crickets; L6 "Rolling." mumble (tools/lines_v5.json). tools/mix_v5.py -> final/mix_v5.wav: box from 0:00
   (-30 -> -23 dB by 0:06); the box is only 30 s and fades at ~26 s, so it is extended to the bench with ONE beat-aligned 1.5 s crossfade
   (box 20.15 -> 2.41) — a deviation the plan did not name, UNCHECKED by ear. Stopdown 51.30-51.70 to -30 dB, sung title downbeat 51.80,
   music only after 51.45, sting on black 55.95. Mix -14.1 LUFS / -0.5 dBTP before final_audio_gate (not run yet). Whole mix UNCHECKED by ear
   (static test still owed in part E). Near-silence ~20.0-21.2 s (the box's own dip lands on the crossfade): UNCHECKED by ear.
2. clips/v5/J_title_flip.mp4 (hflip, 5.04 s). Checked on a 6-tile strip: no text or lettering, team now travels left-to-right, sun
   diffuse behind (no light-direction clash), cow/zebra markings mirror harmlessly; the camel's blurred hump is a v3 defect, unchanged.
   Title composited after the flip on one test frame: reads correctly.
3. tools/timeline_v5.json (17 rows: row 17 = 1.5 s black for the sting; total 57.40 s, title readable 53.2, holds 2.7 s, black 55.90),
   'replace_with' per row for the part D clips; row 7 has no code lantern/parabola/splash (fallback H_ditch at 0.89x + light-out ramp).
   tools/finish_v5.py written, NOT run. Rows 1/3/6/7/9/11 cues carry a "recheck" flag: action frames must be re-picked from the new clips.
4. Doug colour gate: BLOCKED. The FLUX.2 klein 9B weights are not on the M5 (only HF lock files remain under
   models--AITRADER--FLUX2-klein-9B-mlx-8bit) nor on the mini. Download = 17.9 GB (mlx-8bit) or 52.9 GB gated (bf16 original); not
   started without Matt's go. Measured with tools/doug_hue_v5.py: G_forest_v3 coat median hue 24.0 deg, saddle 68% dark; master 20.0 deg.
   NOTE: the before already passes the plan's "within 6 deg" hue test, so the gate must also require the saddle dark fraction to drop.
- 2:37-3:10 AM, step 4 retry (Matt OK'd the download at 2:37): black-forest-labs/FLUX.2-klein-9B (same repo as the mini's klein9b_dl.log;
  LICENSE = FLUX Non-Commercial) downloaded to the M5 HF cache, diffusers files only, 35 GB in 7 min 51 s (2:39-2:47). The edit then FAILED
  TWICE THE SAME WAY: forge_guard paused and SIGTERM'd it for memory (bf16 2:51-3:07, stuck at 1/4 steps; 8-bit 3:08-3:09). Cause: the
  life-model run ~/life-model/runs/full-20261117-1030/train_full.py holds 58 GB, Song Forge's ACE 23 GB, the token meter 8 GB; the box was
  swapping. Stopped per the two-failures rule; that training run was not touched. No after-image, no side-by-side, nothing published.
  Pass test now: coat hue within 6 deg of the master AND saddle dark fraction well under the before (68%); master coat 20.0 deg.

# v5.2 — 2026-11-18 2:07-3:30 PM (Fable builder; Matt's 1:52-2:07 PM notes: static/scratching, "hodge podge of edits", Hank's two voices, show the owner, fix everything else)
Built as ONE v5.2 from v5.1. Nothing in v5/v5.1 edited; all new files are *_v52 / stills/v52 / clips/v52 / sfx/library.
SOUND (engineered as one mix, tools/mix_v52b.py):
- Music: ONE song, music/anthem_9.wav (Song Forge on the mini, round 3 of 4: anthem_1..12 commissioned; ACE-Step sang bracketed
  stage directions in round 1, ignored [Instrumental] holds in round 2, ran out of time before the chorus at 64 s in 7/8, mumbled at
  78 s in 10-12). anthem_9 (bluegrass-warm explorer ballad, 100 BPM) is the only take where whisper hears the chorus: "Hank and Doug,
  over the hills when the wild things call" 46.7-54.0, "Hank and Doug, Hank and Doug" 56.3-59.0, "Nobody's too big and nobody's too
  small" 59.0-63.3. Hiss: quietest-10%-frames 6-16 kHz floor -80.7 dBFS (old theme_2: -58.0), gap floor -88.9 (old -64.8).
  Ending: ACE faded in its last 0.7 s, so tools/song_end_v52.py sustains the final chord (spectral freeze of 62.7-63.05, 3.6 s
  exponential ring-out, soft-clipped, -47 dB by the end) -> music/anthem_9_end.wav 66.74 s. Film 0 = song 2.4 s (offset, no stretch).
  Under the narrated story the demucs instrumental stem (no_vocals, low-passed 7.5 kHz for the vocal residue) plays at -21 dB; it
  crossfades (2.4 s) into the full mix at the chorus bar (film 44.28 = montage start); gain ramps -21 -> -11 dB from 38.3 to the title
  bar 53.84; -8 dB stopdown on the half-bar before the title bar; sidechain duck up to -7 dB under every voice (40 ms / 500 ms).
  Picture cut to its beats (tools/cut_v52b.py): story rows proportional to v5 up to the chorus bar, the 4 rescues 4 beats each, title
  row on the sung "Hank and Doug, Hank and Doug" (53.84), black at 61.84 under the last line + ring-out, total 64.34 s.
- Effects: 17 real CC0 recordings (Freesound, sfx/library/LICENSES.md + library.json, 128 kbps previews -> 48 kHz), none AI: dirt
  steps (419181) rows 1/9, dog sniff (765984) rows 1/3, whistle (799580) row 2 on the flinch, fence rattle (391762) row 4 struggle + pull,
  fox yip (173208), boots on leaves/stones (530384) row 6, body fall in dirt (210867) + splash (9508) row 7, horse walk (581833) + wood
  wheels on dirt (480020) row 11, wings flapping (395242) row 12, water pouring (700352) row 13, kitten meow (528743) row 14, otters
  (572680) row 15; beds: night forest (719558) rows 1-9 at -38 dB, dawn birds (456122) rows 10-15 at -37 dB (looped with 1 s crossfades).
  Each cue: slice, HP 100-400 Hz, LP 10 kHz, -2 dB shelf above 6 kHz, raised-cosine fades, -6 dBFS peak, placed on the action frame.
  Dropped on measurement: barbed-wire file (332 scratchy jumps), dry-leaf steps (22-433 crunch jumps: Matt's "scratching").
- Voice: Hank's "Hi." re-voiced with the same wr3_hank voice/settings/processing as "Rolling." (voices/L4_hank_hi.wav, seed 303,
  f0 78 Hz vs 71 Hz; the old +pitch "young" take was 122 Hz). Whisper hears "Hi.". Same onset frame (row 2.0).
- Audit (tools/click_audit_v52b.py, 0.5 s windows, every hit traced to its stem): music + sfx stems carry 0 single-sample spikes and
  0 HISS windows; the remaining CLICK/FLUX windows all sit on the voices stem (speech plosives/syllables) — the same windows flag
  on v5.1's narration. The delivered-file numbers are in the v5.2 gates block below.
PICTURE (every new still and clip looked at as a 2 fps strip):
- Rows 6-7 (Matt: "Yes, show him"): Krea stills of the owner from behind (hat, long coat, lantern), klein night grade + Doug russet
  (ROAD_owner_night), klein "back of the head only" (DITCH_owner_night2); LTX-2.5 i2v: row 6 Doug trots ahead, the man walks after
  with the lantern (ROAD_owner_v52); row 7 he totters, slips into the ditch between 1.0-1.5 s, the glow lands in the water and goes
  out by 2.0 s (DITCH_owner_v52). Face never visible in any frame. continuity.json: owner_faceless / one_person_max / lantern_goes_dark.
- Row 4 fox: Krea x2 painted the fox free on the ground; klein tangled it into the wires (FOX_tangle), LTX: struggles, slips free,
  bolts right. Row 11 rollout: Krea seed 2 (team horse/zebra/camel(1 hump)/cow all visible, travels RIGHT, Hank brown); klein full-frame
  "repaint only the dog" turned the COW maroon twice and a region klein doubled the bear -> changed approach: still-stage coat recolour
  inside the bench box only (tools/recolor_box_v52.py, hue 22 -> 18 deg, master 20), then LTX. Row 12 goat: geese lift the goat in a
  sling up off the ledge (no tow read). Row 13 turtle: elephant pours from a wooden barrel, turtle sunk to the shell rim in the mud
  (klein TURTLE_sunk). Row 15 otters: Hank flat on the cobbles reaching into the open drain, otters handing the kitten up (no chain from
  the top of frame). Row 16 title: 8 s LTX shot from the flipped hill still, camel klein'd to one hump, team travels right, lantern lit.
- Rows 6/7/9 run 3-11% slower instead of holding a frozen last frame (beat snap made them 0.14-0.46 s longer than their clips).
LEFT (seen, not fixed this pass): row 11 wagon post carries a bell, not the brass lantern (continuity lantern_on_post will fail on
r11_rollout); Hank reads warm red-brown in the otters still (hank_colour may flag r15); row 13 turtle sits in the mud but never
visibly floats free; row 3/5/8/10 clips unchanged from v5.1 (V.O. lipsync FAILs by design); the 9 s title hold ends 1.5 s over black
with the last sung line.
## v5.2 gates (final/hank_doug_wild_rescue_trailer_v52.mp4, 64.33 s; run 3:16-3:30 PM after the rollout tracking-shot swap)
film_qc, verbatim: Checks run: 97 | passed: 81 | failed: 16 (v5.1: 23). The 16: 12 lipsync (11 narrator/Doug V.O. lines with no
on-screen mouth by design + 30.7 young Hank "Hi." 0/6, the N_hi previs jaw move is small, unchanged since v4); 3 artifact samples
(16.5 fox+fence, 49.5/50.5 kitten behind the grate: descriptive, nothing merged or extra by eye); 1 audio: film_qc's whisper did not
transcribe "Hi." at 30.7 (a direct whisper of 29.8-32.2 s of the delivered audio hears "Hi."; 37.5-39.5 hears "Rolling.").
continuity_check: 76 PASS / 25 FAIL (v5.1: 80 / 21, both with the same misfiring range rules). doug_colour 9 PASS / 0 FAIL (incl. the
new rollout), no_humans 14/14 PASS, owner_faceless 2/2 PASS, hank_colour 3/3, camel_one_hump 2/2, team_is_four PASS, one_wagon 3/3.
Of the 25 FAILs, 20 are the b-id range rules firing on every row (lantern_lit_13_14 x16, lantern_unlit_3_4 x3 incl. the owner's lit
lantern in rows 6-7 and the title lantern, no_text_outside_title on the title card) = harness, not picture; real ones: young_hank_is_hank
r03/r09 (judge does not read the bear as smaller; unchanged clips, same in v5.1), lantern_on_post r11 (bell on the post, 1/3 YES),
wagon_rolls_right r11 (judge NO x3, same in v5.1; the team walks right in every frame of the strip), one_person_max r07 (judge answers
NO on the two frames where nobody is in the picture after the fall).
audio_check: FAIL 3 / WARN 2: score vocals (sung chorus, by design), score drone (a 108 Hz bass note held 29.5-32.0 in the song, music
not a tone bed), balance (the sung chorus over the rescues/title where no narrator speaks, 46-60 s); WARN repeats/jumps (whisper-level),
WARN music within 6 dB of a voice at 6.0 (the whistle effect on the flinch counts as music) and in the sung chorus.
Delivered-audio audit (tools/click_audit_v52b.py, 0.5 s windows, stem-traced): 129 windows, HISS 0, CLIP 0, 0 windows whose hit is not
explained by the voices stem (speech plosives/syllables flag CLICK/FLUX exactly as v5.1's narration does); music + sfx stems: 0
single-sample spikes (the two music "jumps" at 51.1 / 55.9 are drum transients). final_audio_gate: FIXED -14.3 LUFS / -1.0 dBTP.
Watched as the 2 fps sheet (final/contact_sheet_v52_2fps.jpg) after the row-1 start was moved to 0.0 (the first cut had a 0.38 s black
flash from the beat snap) and every new clip as a 2 fps strip (clips/v52/strips).
# v5.3 — 2026-11-18 7:19-7:26 PM (sound-only remix; Matt 7:18 PM "the jingle runs through the whole trailer")
Picture = final/picture_v52.mp4 unchanged. tools/mix_v53.py = mix_v52b + 3 sung hooks from the anthem_9 vocal stem (HP 100 Hz, -15 dB,
raised-cosine fades, instrumental swells +3 dB under each, added after the voice duck), beat-grid aligned (100.45 BPM, film = song - 2.4)
and chroma-checked against the instrumental where they land:
- 11.30-13.05 "Hank and Doug," (song 46.55-48.30, chorus line 1; word on 11.47; chroma 0.78) between N03 (ends 11.09) and N04 (13.24)
- 23.78-24.99 "Hank and Doug" (song 57.84-59.05; word on 23.86; chroma 0.90) between N05 (ends 23.27) and N06 (25.17)
- 36.92-38.13 "Hank and Doug" (same source; word on 37.00; chroma 0.75) between N09 (ends 36.86) and "Rolling." (38.51)
- 44.3 on: the full chorus as in v5.2 (title on "Hank and Doug, Hank and Doug").
Gates: final_audio_gate FIXED -14.3 LUFS / -1.1 dBTP. click_audit_v52b on delivered audio: 129 windows, HISS 0, CLIP 0, non-voice
windows the same 4 as v5.2 (3.0/3.5 sfx flux, 51.0/55.5 drum transients); stems music/voices/sfx/hooks HISS 0, hooks stem 0 clicks.
audio_check: same 3 FAIL/2 WARN as v5.2 (by-design score vocals/drone/balance), no new ones. Whisper of the whole mix: all 13 spoken
lines word-for-word identical to v5.2; hook 3 transcribed "Hank and Doug." at 36.94; hooks 1-2 not transcribed by whisper (sung, ~2 dB
under narration RMS). Published hank-doug-v53-2wp89032s8uz.mp4 (200).
