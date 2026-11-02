---
stage: 06_assemble
outputs:
  - final/*.mp4
  - final/timeline.json
gate: none
---
# 06_assemble — cut the film

One job: turn the coverage into selects and cut them to the words. Nothing new is
generated here except title and credit cards.

## Inputs
- Working (this film): `stages/04_shots/APPROVED.md` (approved scenes), `clips/` +
  `clips/alternates/` + `manifest.json` (the coverage), `voices/`, the picked score, `beats.json`
- Reference (every film): `../../bin/build-episode` docstring, frozen rules 17, 29, 32, RULES.md 23, 26, 28

Do NOT load: `_ARCHIVE_UNUSED_not_in_film/`, review folders, declined takes.

## Process
1. The coverage gate must pass first (`bin/film-status` shows it; frozen rule 29).
2. Selects: rank >= 2 takes per beat from the coverage in `manifest.json`, with a why.
   Only takes from approved scenes are eligible; declined takes are already gone.
3. Cut to words: word timings for every line, hard cuts on word onsets, a dissolve only
   where a cue asks for one (frozen rule 32). Never a blanket crossfade.
4. Run `bin/build-episode projects/<film>`. Its preflight cross-checks the EDL against
   `beats.json` and hard-stops on a mismatch; never bypass it.
5. Static gain mix, never loudnorm dynamic.
6. Surround (added 2026-10-31): render the mix with `bin/surround-mix sfx/mix_plan.json
   --out final/mix_51.wav --stereo final/mix_stereo.wav --no-loudnorm` (keep step 5: static
   gain, no dynamic loudnorm), then `--video final/<Film>.mp4 --mux final/<Film>_51.mp4`
   for the 5.1 E-AC3 + stereo AAC deliverable. Dialogue sits in Center.
7. Upscale (added 2026-11-02, Matt's pick after UPSCALE-TEST-2026-11-02.md): never call one upscaler for
   the whole film. Run `bin/upscale-route projects/<film> --edl <edl.json> --segs <segment dir> --dry-run`,
   read the plan, then run it again with `--out <dir>` when the GPU is yours (it refuses while another heavy
   job is alive). Routes: **SeedVR2-3B** (720p restore, then lanczos to 4K) for every shot by default,
   **LTX-2.5 Refine-Details** (`tools/ltx25_refine_tiled.py`, ~2.3x canvas, tiled) for faces and close-ups,
   and lanczos only for cuts under 0.9 s. Matt 11/2 on the captain close-up: SeedVR2's "wrinkles look fake
   and AI", Refine's look "more smoothed out and normal". A face is decided, first match wins, by a manual
   `"upscale": "seedvr2"|"refine"|"lanczos"` on the EDL cut or beats.json shot, then `"face": true|false`
   (set in stage 04), then `framing` close/MCU with a character, then the Apple Vision probe
   (`bin/face_area`, largest face >= 5% of the frame). Cartoon and animal faces are not auto-detected,
   so they need `face: true`. The upscaled files differ in size per route, so the 4K finish scales to the
   delivery canvas.
8. Grade (added 2026-10-31): `bin/grade in.mp4 out.mp4 --lut NAME [--grain 0-1] [--scope]`
   with a LUT from `../../luts/` (teal_orange_blockbuster, bleach_bypass, cold_space_teal,
   warm_alien_haze, kodak_2383_style, neutral_filmic; regenerate with tools/make_luts.py).
   Pick the LUT per film in `final/timeline.json`; `--scope` for 2.39:1 cinema bars.

## Outputs
- `projects/<film>/final/<Film>.mp4`, `final/timeline.json`

## Human check
None here. Stage 07 runs immediately; Matt sees the film only after the gates.
