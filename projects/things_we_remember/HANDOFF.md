# HANDOFF — THE THINGS WE REMEMBER (updated as cuts finish; newest status at the bottom)

## Matt's standing orders (11/14)
- 1:45 AM go: teaser (approved) → 90 s trailer (fast, then best) → 3-min short (fast, then best ~12 heroes) → feature.
- 1:46 AM: the feature is 20 parts of 5 min (PARTS_MAP.md). Part 1 = scenes 1–3 (PART_01.md).
- 2:28 AM: "just keep working and don't stop until I say": after Part 1, Part 2, 3 … 20 in order (write PART_NN.md from
  PARTS_MAP.md, FAST cut, publish link), each part reusing every prior shot that fits and ending on a hook.
- Links: final/link_<name>.txt (link_trailer_90_fast.txt, link_part_01_fast.txt …); a watcher texts Matt, never text him.
- Every cut: film_qc (mandatory) + read-time + continuity; Song Forge first (127.0.0.1:8767 jobs_running==0); METRICS.jsonl.
- Never delete/overwrite approved teaser files (clips/, clips/hq/, final/segs/up/, teaser finals). Rememberer is never clear.

## How a cut is built (all tools in tools/, all reuse the teaser's recipe)
- Stills: `~/AI/krea2/venv/bin/python ../last_signal/tools/zimage_batch.py stills_jobs_X.json` (jobs from tools/<cut>/mkjobs_*.py).
  Pick with a contact sheet; picks go in tools/picks_more.json (teaser picks stay in tools/picks.json).
- Voices: voice/gen_more.py lines_X.json (Qwen3-TTS VoiceDesign, cast in voice/gen_narration_cast.py, incl. tom + lily3),
  then `~/chatterbox-env/bin/python voice/score_more.py lines_X.json` (picks + trims new ids only; teaser picks untouched).
- Clips: tools/<cut>/clips_*.sh (make-ltx25 fast low-ram 1024x576; a2v via tools/trailer/a2vwav.py lead-in 0.35 s).
  pgrep -f can't see the stills process on macOS (long argv); wait on the pid or the log instead.
  A make-ltx25 that dies can leak its mem lease: release with mem_client.release(<id>) from mem_client.state()['leases'].
- Timeline: tools/<cut>/mk_tl*.py → timeline_X.json + texts_X.json (shots, lines, score cues, sfx cues, silence, cold_t).
- Finish: `tools/finish_cut.sh NAME timeline_X.json texts_X.json` = compose2 (cached per-shot segs in final/segs/<cut>/)
  → music2 → mix2 → mux → final_audio_gate → mk_manifest2 (manifest.json/final/timeline.json/texts.json become this cut's;
  teaser originals saved as *_teaser.json) → read-time → film_qc → prints counts. Then continuity_check, then
  `tools/publish.sh NAME` (re-encode >200 MB, scp to VPS /var/www/v, HTTP 200 check, writes final/link_NAME.txt).
- Best pass: K6 needs a 72 GB lease; the guard budget is ~50 GB, so it is refused → LTX-2.5 --hq --low-ram, then
  bin/upscale-route (auto: Refine on faces ~28 min/shot, SeedVR2 ~15 min/shot) into final/segs/up_<cut>/.

## Status (9:35 AM 11/14)
- Trailer 90 s FAST: DONE 3:02 AM → final/link_trailer_90_fast.txt. QC 105 pass / 6 fail / 9 skip (all 6 on approved teaser shots).
- Trailer 90 s BEST: DONE 9:11 AM → final/link_trailer_90_best.txt. Same QC counts; continuity PASS. Kept HQ+SeedVR2 takes:
  final/segs/up_trailer/00_t13.mp4, 01_t18.mp4, 02_t14.mp4 (t01/t04 HQ rejected, fast takes used). Coordinator told.
- SHORT 3 min FAST: IN PROGRESS. Stills, voices (all 8 lines picked + trimmed), picks (tools/picks_more.json, derived stills
  sh14c/sh31c/sh38c with the Rememberer pre-blurred) and tools/short/overrides.json are DONE. tools/short/clips_s.sh is
  RUNNING (started 9:31; 19 i2v + sh32/sh36 a2v; log clips_short.log; ends with CLIPS_DONE ~10:40). Foley: tools/short/sfx_s.sh
  runs at the end of prep_s.sh (drawer, plate, crayon, giggle; check audio/sfx.log for SFX_S_DONE).
  NEXT: grid-check every new clip (tools/grid.py out.jpg clips/X.mp4 …; LTX can't do physical gags: one re-roll max, then
  code), python3 tools/short/mk_tl_s.py, tools/finish_cut.sh short_3min_fast timeline_short.json texts_short.json, read
  qc/film_qc_short_3min_fast.log (expected known flags: s03 photo man x4, s05/s08 "no character"), continuity_check
  (`~/.local/mlx-server/bin/python ../../pipeline-tools/continuity_check.py . FILM`), tools/publish.sh short_3min_fast, append
  known_defects.md, SendMessage main (name, link, length, QC counts verbatim, fallbacks, UNCHECKED).
- SHORT BEST: ~12 heroes (SHORT_3MIN.md list) with LTX --hq --low-ram (K6 refused at 50 GB budget), then upscale-route
  (EDL cuts need a "src" field or it plans 0 segments). Grid-check HQ vs fast and keep the better; lip-sync HQ that fails QC
  keeps the fast take. Same pattern as tools/trailer/best_t.sh + mk_tl_best.py.
- Part 1 (5:00, 74 shots): PART_01.md v1.1, PARTS_MAP.md, tools/p01/{mkjobs_p1.py, prep_p1.sh, clips_p1.sh, sfx_p1.sh,
  mk_tl_p1.py}, voice/lines_p01.json all written; NOTHING rendered. Run prep_p1.sh → contact sheet → picks (+ p15=p13,
  p26=p27, p39=p37, p44=p42 picks) → touch tools/p01/PICKS_READY → clips_p1.sh → mk_tl_p1.py → finish_cut part_01_fast
  timeline_p01.json texts_p01.json → publish part_01_fast (link_part_01_fast.txt).
- Then Parts 2…20 in order from PARTS_MAP.md (Matt 2:28 AM: don't stop until he says), FAST cuts only, each reusing prior shots.

## Known open defects
- s03 blank-faced photo man (approved), flagged 4x by film_qc every cut. s05/s08 judged "no animated character" (by design).
- New VoiceDesign voices (Tom, Lily at 3, all new lines) and every mix are UNCHECKED by ear.
- The cassette brand text in t12 is gibberish ("DOPAMO").

## Lesson (11/14 8:08 AM)
Before any rm/restart of a render step, check METRICS.jsonl and the step's log for a finished run. The trailer upscale had
completed (4543 s) during a ~4 h session stall; the "restart" deleted its good outputs and cost a 45-min re-run.
Destructive commands print what they touch first.

## Status (12:31 PM 11/14) — PAUSED by Matt at 12:20 PM ("Pause movie production"). NOTHING is running, 0 leases held.
Resume only when Matt says. Do NOT run `m5-bigjob end` (Matt's). Since 11:52 the guard budget is ~108 GB (m5-bigjob, M5 Song
Forge OFF on purpose, :8767 doesn't answer and the sfwait loops read that as 0), so K6 (72 GB) is usable for best passes.
- SHORT 3 min FAST: DONE 11:55 AM → final/link_short_3min_fast.txt (3:00.5). QC 199 pass / 8 fail / 12 skip, continuity PASS,
  read-time PASS (MONTHS LATER card 3.9 s in tools/short/mk_tl_s.py). Coordinator told. Logged in known_defects.md.
- SHORT BEST: stopped mid-pass. Driver tools/short/best_s.sh (LTX --hq --low-ram, then upscale-route → final/segs/up_short).
  HQ DONE in clips/hq/: sh06 sh10 sh13 sh14 sh15. NOT done: sh16 (killed at start, no output) sh18 sh21 sh30 sh31 sh34 sh37.
  Resume: `nohup bash tools/short/best_s.sh > best_short.log 2>&1 &`. It skips finished heroes, but line 5 waits for "^QC:" in
  finish_short_fast.log (already there, so it passes at once). Not yet written: tools/short/mk_tl_best_s.py (copy
  tools/trailer/mk_tl_best.py; swap kept up_short takes into timeline_short.json → timeline_short_best.json), then
  finish_cut.sh short_3min_best timeline_short_best.json texts_short.json, continuity, publish short_3min_best.
  Grid-check each HQ take against its fast take and keep the better one. Optionally switch the 7 remaining heroes to K6 now.
  Don't let film_qc (wants a 32 GB lease) overlap a render driver unless the budget clearly fits both.
- PART 1 prep: stopped. tools/p01/prep_p1.sh made 33 of 120 stills (p03..p22 a+b, p24_a). zimage_batch resumes and skips
  existing files. Voices and foley for P1 were NOT started (prep_p1.sh runs them after the stills).
  Resume: `nohup bash tools/p01/prep_p1.sh > prep_p01.log 2>&1 &`. Contact sheets: `python3 /tmp/twr_grid/sheet.py stills
  /tmp/twr_grid/p01` (if /tmp was wiped, rows are one shot with _a and _b side by side). Then add picks to tools/picks_more.json, touch
  tools/p01/PICKS_READY, and run clips_p1.sh, etc. (see the 9:35 status). With 108 GB, clips may drop --low-ram.
