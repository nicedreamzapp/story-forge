> **DECISION 2026-11-18 1:57 AM (Matt): ending Option A, NO button.** The title lands on the musical downbeat after the
> stopdown, holds about 2-3 s, then black and the "Here we go!" sting. Dropped for good: the sleeping-pile still/clip
> (K_sleep_red / K_sleep_chip, D7), the chipmunk (squeak and picture) and the old row-17 dusk wagon shot. The timeline
> ends cleanly near 60 s (it may run a little shorter); no frozen still as padding. Approved run: plan steps 1-4 only
> (A1 sound, A2 mirror, A3 timeline/cues, B1 Doug colour gate), then stop for Matt.

# HANK & DOUG'S WILD RESCUE trailer — v5 fix plan ("make it way better")
Written 2026-11-18 (stage 01, plan only; nothing rendered, nothing edited but this file). Matt approves before any part runs.
Script stays script_v4 (same words, same 17 rows, same music map) except the button (row 17) and three sound rows, noted below.

## What we depend on
Nothing outside the M5. Every tool below is installed and local: Krea 2 (stills), FLUX.2 klein 9B via mflux
(`~/mflux-venv/bin/mflux-generate-flux2-edit`, weights in the HF cache at the path in
`projects/circus_train/lora_build2/train_doug_v2.json`), LTX-2.5 (`bin/make-ltx25`; the underlying
`~/Desktop/PROJECTS/ltx-2-mlx` CLI has `keyframe --start --end`), K6 Pro (`bin/make-k6`), MMAudio 44k, noisereduce,
demucs, ffmpeg, Kokoro + the clones. Freesound CC0 is the only outside option and only if MMAudio fails on one clip
(per-clip licence check); it is replaceable by another MMAudio seed.

## The three problems and the one-line fix for each (the rest of the file is the how)
1. Fuzzy static → drop the crickets bed, clean or replace every foley clip, cut the sound count down to 5 hero sounds
   plus a few soft ones, each gated tight to its visible action. No render.
2. Weak ending → the title lands on a stopdown and holds 4.8 s; the button becomes ONE 2.8 s wide shot that the model
   cannot wake up (same sleeping still as first AND last keyframe), chipmunk painted into the still, no cutout, and
   the title-hill team is mirrored so the wagon travels left-to-right.
3. Doug's colour → fixed at the STILL stage with a FLUX.2 klein reference edit against `canon/doug_master.png`, then the
   five tan shots are re-rendered from the fixed stills. Proof on ONE still first. The hue-rotate code path
   (`tools/recolor_doug.py`) is retired for good: it is what went olive in motion.

Why these over the alternatives (research, in the brief):
- Trailer craft: title on a downbeat after a near-silence stopdown, hold 2-3 s+; a button is one wide shot of 2-3 s,
  set up visibly earlier, no VO explanation; the wagon travels left-to-right in every shot; mirroring is a legitimate
  fix once text / markings / light direction are checked.
- Sound: trailers are mostly music; fewer, cleaner sounds; high-pass 80-120 Hz, low-pass 8-10 kHz, hard gate each
  clip to the action, stationary spectral denoise ~50%, replace or drop weak clips, 3-5 hero effects, music-only
  climax and title.
- Consistency: fix colour at the still stage, never after animation; klein reference editing is the best Mac path;
  keep i2v clips short (drift past ~5 s); first AND last frames carry the right red; first+last-frame keyframing is
  how you force a start and end state (used here for "asleep at both ends" and "lit → unlit").
- Lessons already paid for (hard constraints): no code paint effects or cutouts in motion, a still + camera move
  reads as frozen (so the button is a real LTX clip, not a Ken Burns), every sound on a visible action, no tone beds,
  no jittered stills, narrator tells the story (unchanged words).

## Screen direction map (decided, so no shot fights its neighbour)
Night half (the hunt) travels camera-LEFT on purpose: rows 1, 3 Doug tracks left (the wrong road, the regress), row 6
is tail-away toward the bend (allowed exception), row 9 is tail-away up the road. Day half travels camera-RIGHT:
rows 11 (rollout), 16 (title hill) and the button's parked wagon face right. Rows 12-15 have no travel. The turn from
left to right happens at "Then he went back." Research: left-to-right = progress; exceptions only head-on / tail-away.

---

## PART A — no-render fixes first (about 30 min, all code + ears)

### A1. Sound clean-up (about 20 min)
- Delete the crickets bed from the mix (rows 1-9). The music box (`music/breakdown_1.wav`) starts at 0:00 instead of
  0:06, at -30 dB rising to -23 dB by 0:06, so the night is carried by music not static. Nothing else changes in the
  music map. (Research: drop the ambience bed; the trailer is mostly music.)
- Process every kept sfx with one script pass: trim to the action window from `tools/cues_v4.json` (hard gate, 10 ms
  fades), high-pass 100 Hz, low-pass 9 kHz, noisereduce stationary at 50%, peak-normalise to -6 dBFS, then the mix
  dB from the cue table. Run `tools/sfx_tone_check.py` after; any clip with a narrow band over 0.3 s is dropped.
- Hero sounds (5, loud, clean, each on a visible frame): the two-note whistle (row 2 on the flinch, and row 6 on the
  glow surge only if the new lead clip shows the surge, else once), the wire creak-and-twang (row 4 on the pull), the
  splash/slosh (row 7 on the cut, ripples visible from frame 1), the chipmunk squeak (button, on the painted
  chipmunk's head bob), hooves-and-wheels (row 11, from frame 1).
- Soft sounds kept: sniffs (rows 1, 3), fox yips (row 4, on the kicks), barks (row 6, mouth open), paws walking (row 9),
  morning birds (row 10), wing beats (12), water pour (13), kitten mew (14), otter chirps (15), flame hiss (7, on the
  flame dying), one snore (button, on the visible chest rise).
- Dropped outright (hissy, weak, or no visible action): tail_thumps, paws_running, lantern_creak, tuba_note, wind,
  paint_shhk, marmot chirp/whistle, the old lantern_fall tumble-clank.
- Re-rendered with MMAudio 44k (about 20 s each, 5 clips, 2 min): splash-slosh (short, with a ripple tail), flame hiss,
  water pour (the v4 spray is the hissiest clip), snore, chipmunk squeak (new seed, 44k).
- Stopdown before the title: the sung verse row 15 ends at 51.70; from 51.30 to 51.70 the music ducks to -30 dB with a
  120 ms reverb tail on the last otter chirp, then "It's Hank and Doug's Wild Rescue!" hits full at 51.80 on the
  downbeat (theme_2 55.7 in). The sting "Here we go!" stays over black at the end. (Research: stopdown then downbeat.)
- Music-only on the title and the whole button except the squeak, the snore and the sting (research: music-only
  climax). The final mix target stays -14.5 LUFS / -1.9 dBTP (final_audio_gate).

### A2. Title hill mirrored (about 5 min)
`ffmpeg -vf hflip` on `clips/v3/J_title.mp4` → `clips/v5/J_title_flip.mp4`. Checked before use: the clip has no text
(the title is the code layer laid on after the flip), no lettering on the wagon, the lantern point sits on a post
(fine on either side), the sun is behind the silhouettes (symmetric), neighbours are the otters (no travel) and the
button (parked). Title text timing unchanged (paints in 52.0-53.2, readable before "Hank" at ~53.2, holds to 56.8 =
4.8 s; research says 2-3 s minimum). Row 16 now travels left-to-right.

### A3. Timeline bookkeeping (about 5 min)
`tools/timeline_v5.json` copied from v4 with: music start 0.0; the stopdown; row 7 = the new ditch keyframe clip
(no code lantern, no parabola, no painted splash); row 11 = the new rollout; row 17 = the new button (2.8 s, black at
59.2, sting 59.0-60.0); `cues_v5.json` with the new sound list. `write_manifest_v5.py` / `finish_v5.py` are the v4
scripts with the paths swapped (launched detached with nohup, the v4 note).

---

## PART B — the one-still proof that gates every render (about 6 min)

### B1. klein reference edit on the worst Doug still
`mflux-generate-flux2-edit --base-model flux2-klein-9b -q 8 --image-paths stills/G_forest_v3.png canon/doug_master.png
--prompt "Repaint the dog in the first image as the dog in the second image: a solid russet-red bloodhound, the same
red on his back, saddle and ears, no black or tan saddle, same pose, same brushwork, everything else in the first image
unchanged" --steps 4 --output stills/v5/G_forest_red.png` (klein is distilled; 4 steps; ~1-2 min with the load).
Pass test, by eye on a side-by-side and by number: the median hue inside the Doug box lands within 6 degrees of the
master's coat (same measure recolor_doug used), no black saddle, the bear and the log untouched, the brush texture
kept (no smoothing). Two seeds if the first changes the background.
- PASS → Part C runs with klein edits on every Doug still.
- FAIL (identity or brushwork lost) → fallback 1: the same edit with DOUG_LORA_V2 loaded (`--lora-paths
  ~/.hankdoug_seeds/DOUG_LORA_V2.safetensors --lora-scales 0.8`, single LoRA only, frozen rule 24; rule 10 says the
  LoRA locks identity, the prompt carries the colour). Fallback 2 (repair path only, needs an install): masked LAB
  recolor on the finished clip, keep L, transfer a/b from the master, temporal smoothing; SAM 2 is NOT installed, so
  this costs an install and is the last resort.

---

## PART C — fixed stills (about 14 min, after B passes)

C1. klein colour edits, ~1.5 min each, same prompt and settings as the proof (7 edits ≈ 10 min):
- `stills/v4/G_hunt.png` (raw, pre-recolor) → G_hunt_red (row 1; kills the olive drift at its source)
- `stills/G_forest_v3.png` → done in B1 (row 3)
- `stills/I_walkaway_s1101.png` (raw) → I_walkaway_red (row 9)
- `stills/C_bench_v3.png` → C_bench_red (row 10)
- `stills/D_rollout_s1102.png` hflipped FIRST (team faces right; no text on the wagon; the lantern moves to the other
  post, fine), then edited → D_rollout_right_red (row 11)
- `stills/K_sleeping_s1102.png` → K_sleep_red + a second edit on that result: "add a small chipmunk sitting upright on
  the rim of the near wagon wheel, painted in the same brushwork" with `stills/X_chipmunk.png` as the reference →
  K_sleep_chip (row 17; the chipmunk is now paint, not a cutout; all eyes stay shut in the still)
- `stills/H3_ditch_lantern.png` → "the lantern lies in the ditch water with its flame OUT, dark glass, no glow, cold
  moonlight only" → H3_unlit (the END keyframe for row 7)
NEW2 (Doug_close_glow_fix), NEW4 (Doug_watch_fix) and N_hi read russet on the v4 sheet with no drift: kept as they are.

C2. Two new Krea stills (~45 s each + one retry budget ≈ 3 min), style prefix word for word, then a klein edit each
where Doug appears:
- FOX_fence_v5: "an old sagging wire fence on weathered grey wooden posts, a small red fox with a white chest and a
  black-tipped tail hanging head-down from the top wire, ONE hind leg caught in the wire, the other legs kicking, Young
  Hank standing on his hind legs beside the fence reaching both front paws to the wire" must_not: person, hand, gate,
  sign, lantern. (Doug not in frame, no edit.)
- ROAD_lead_v5: "seen from behind: Doug, small in frame, runs AWAY down the dark dirt road toward a bend where the
  road edge drops into a dark reedy ditch, warm amber lantern glow on the trunks behind and to the right of camera"
  must_not: person, hand, boot, lantern object, bear. Then the klein colour edit (tail-away, red still shows).

---

## PART D — renders, in order, cheapest and most certain first (about 80 min of GPU time, sequential)
All LTX-2.5 clips: 24 fps, 1920x1080 as before, 2-5 min each; every prompt names subject + camera + secondary
motion and says "static camera, locked off" (research: name the three, "static" when locked). Each clip is cut on
its first strong motion and kept at 2-5 s. Song Forge health-check and the pause watcher as always.

D1. Row 3 G_forest from G_forest_red, 4 s (4 min). Doug walks camera-left nose down, Young Hank's eyes blink behind
    the log, ferns stir. Static camera.
D2. Row 1 hunt from G_hunt_red, 5 s (5 min). Doug tracks camera-left nose down; the amber glow on the trunks behind
    him sways slowly (named secondary motion; if it renders, the creak comes back as a soft sound, else it stays out).
D3. Row 9 walk-away from I_walkaway_red, 3.7 s (4 min). Tail-away, the pair shrink up the road, moon brightens.
D4. Row 4 fox from FOX_fence_v5, 4.2 s (5 min + 5 min retry budget). "The fox kicks, the bear hooks both paws into the
    wire and pulls it apart, the fox drops, lands and bolts out of frame right. Static camera." Cut before any lunge.
D5. Row 6 lead from ROAD_lead_v5, 4 s (4 min). "Doug runs away from camera toward the bend, barking back over his
    shoulder; the amber glow surges along the trunks after him. Static camera." The second whistle is placed only on a
    visible surge.
D6. Row 7 ditch, LTX-2.5 KEYFRAME, start = H3_ditch_lantern (lit, ripples), end = H3_unlit, 3.4 s (5 min). "The
    lantern lies on its side in the ditch water, ripples settle, the flame flickers, gutters and goes out, the warm
    light leaves the reeds. Static camera." This replaces the parabola cutout and the 4-frame painted splash and the
    grade ramp. The narrator's "right into a ditch" lands on the cut, the slosh sits on the visible ripples at frame 1,
    the hiss on the flame dying. First use of keyframe on LTX-2.5 (it tested worse on old 13B; this is a 5 min test).
    If it fails (lantern morphs, flame won't die): fallback = first-frame-only i2v of H3 lit, 3.4 s, plus the v4 light-out
    ramp, still no cutout.
D7. Row 17 button, LTX-2.5 KEYFRAME, start = end = K_sleep_chip, 2.8 s (5 min + 5 min retry). Same still at both ends
    means the model must return everyone to asleep, so nobody can wake up and stay up. "Golden dusk, everyone asleep
    in a pile on the parked wagon, chests rising slowly, the lantern flame flickers, the chipmunk on the wheel rim bobs
    its head and chatters, one of Doug's long ears lifts and flops back down. Static camera." One wide shot, no words
    (see the decision below). If the keyframe route fails here too: first-frame i2v with the prompt "nobody wakes,
    eyes stay shut" cut at its first clean 2.8 s; if the crew still wakes, the button is cut and the film ends on the
    title + sting (Option A below), which is a finished ending on its own.
D8. Row 10 bench, LTX-2.5 a2v from C_bench_red with `voices/L1_hank_rolling.wav`, 3 s (8-13 min). "Hank in profile on
    the bench says one word, his jaw opens wide on it; Doug's ears flip up and his head turns; static camera." One
    acting beat per character. If the jaw still barely moves, keep the v4 clip (Doug red is still fixed by D8's still
    only if it renders; otherwise row 10 keeps the tan Doug and is listed as a known defect).
D9. Row 11 rollout, K6 Pro from D_rollout_right_red, 5 s (about 20 min at 12 min per 3 s). "Static locked camera, wide
    side profile, the whole team walks camera-RIGHT across the frame, all four animals stay in frame, big spoked
    wheels turning, dust." Fallback if K6 pushes in again or the horse exits: hflip the v4 K6 clip, use 0.0-4.3 s, and
    extend the bench row by 0.7 s (C_bench is 4.04 s long, room exists), with Doug on the bench left tan in that one
    wide shot and listed.

Total GPU in D: 4+5+4+10+4+5+10+13+20 = 75 min, plus loads ≈ 80 min. No new voice lines (all 14 reused), so 0 min voices.

---

## PART E — finish and watch (about 15 min)
Lay `timeline_v5.json`, title layer on the flipped hill clip, mix from `cues_v5.json`, mux, 2 fps contact sheet,
watch all 120 tiles, and the row-by-row sync check by frame (rows 2, 4, 7, 10, 12-15, 16, 17). Then a real listen of
the whole minute with headphones for the static test: with the bed gone, any hiss left in a foley clip is a drop,
not a tweak.

## PART F — gates (about 21 min)
film_qc ~7 min (lipsync will still flag the 11 V.O. lines with no mouth on screen; report counts verbatim),
continuity_check ~11 min (doug_colour at b03/b04/b09/b12/b14 and wagon_rolls_right at b04 are the ones that must flip
to pass), audio_check ~1 min, final_audio_gate ~1 min. Anything a gate cannot judge is reported UNCHECKED.

## Total, honest
A 30 + B 6 + C 14 + D 80 + E 15 + F 21 = about 166 min ≈ 2 h 45 m of which about 80 min is unattended GPU. Order of
spend: A and B first (36 min, nearly free); nothing in C or D starts until B1 passes.

## The one decision for Matt: the button
- Option A: no button. Title hits on the downbeat after the stopdown, holds 4.8 s, cut to black, sting "Here we go!".
  Cleanest, 0 min, nothing can fail.
- Option B (plan default): the sleeping pile, one 2.8 s wide shot, no words: chipmunk chatters on the wheel, Doug's ear
  lifts and flops, snore, sting. Setup is already in the trailer (the crew awake on the same wagon at row 10 and the
  rollout). Research says a button needs no dialogue; this one has none. 10 min.
- Option C: Option B plus Hank's eyes-shut "Rolling." mumble (the v4 callback) on the a2v path: +13 min, and the
  eyes-shut mouth has failed the judge twice; the mumble would be placed only if the jaw visibly moves.

## Known-defects entries this plan expects to close
Static/ambience, hissy foley, title-hill direction, rollout direction + push-in + horse exit, chipmunk cutout, crew
awake, Doug tan/olive in rows 1/3/9/10/11/17, fox by the front paws, Doug toward camera in the lead, lantern cutout +
painted splash, bench mouth (if D8 renders). Still open after v5 by design: elephants carry no barrels; V.O. lipsync
flags; the montage cut-on-word is confirmed by frame in E.

## Run order (prepped 11/18 3 AM)
Steps 4-8 are one push-button script: `tools/run_v5_renders.sh` (`--check` = CPU-only input check, `--from N` = resume).
Every prompt and setting lives in the script's header. Nothing has rendered; the M5's memory is held by the life-model
training until about 8 AM and the script waits for that pid, for Song Forge (`jobs_running` = 0) and for `bin/mem-gate`
before every heavy step; an inline pause watcher SIGSTOPs renders while a customer job runs.
- Step 4: klein 9B bf16 (`--model flux2-klein-9b`, 4 steps, guidance 1.0, seeds 1 then 2, `KLEIN_Q=8` only if bf16
  cannot fit), the still first and `canon/doug_master.png` second. Gate boxes picked by eye (full-res): Doug 640 380
  1240 670, saddle 800 395 1020 470; before = hue 26.0, saddle dark 60%; master 20.0 / 24%. PASS = hue within 6 of 20
  AND saddle dark at or under 30%. Both seeds fail -> fallback 1 (DOUG_LORA_V2 at 0.8) once. The side-by-side
  (`tools/sbs_v5.py`) is scp'd to the VPS `/var/www/v/doug-sbs-v5-<random>.jpg`, the link goes to the trailer chat and
  Matt's phone, then the script waits for `tools/DOUG_APPROVED` (`tools/DOUG_REJECTED` stops it).
- Step 5: klein edits G_hunt, I_walkaway, C_bench, D_rollout (hflipped first, `stills/v5/D_rollout_flip.png` already
  made), H3 lantern unlit (`stills/v5/H3_ditch_lit.png`, the 1344x768 copy, is the START keyframe); Krea 2 stills
  `stills/v5/jobs_v5.json` (seed 1101) + `jobs_v5_alt.json` (seed 1102, 12 steps) for FOX_fence_v5 and ROAD_lead_v5,
  then the klein edit of ROAD_lead_v5. K_sleep / chipmunk edits dropped (ending A).
- Step 6, 832x480 24 fps seed 11, LTX-2.5 distilled i2v with `--static`: G_forest 4 s, G_hunt 5 s (camera-left),
  I_walkaway 3.7 s (tail-away), FOX 4.2 s (fox exits right; retry seed 12), ROAD_lead 4 s (tail-away), ditch KEYFRAME
  3.4 s = 81 frames (`ltx-2-mlx keyframe --start H3_ditch_lit --end H3_unlit --dev-transformer
  transformer-dev.safetensors --cfg-scale 3.0`, the real CLI contract; the distilled LoRA resolves from the pack; on
  failure row 7 falls back to H_ditch + the light-out ramp already in timeline_v5), bench a2v from
  `voices/L1_hank_rolling.wav`, rollout K6 Pro 5 s camera-RIGHT (`--static`). Clip names match `replace_with` in
  `tools/timeline_v5.json`; a 6-frame strip of each lands in `clips/v5/strips/`.
- Step 7: mix_v5 -> finish_v5 (detached) -> mux -> final_audio_gate in place (-14.5 LUFS / -1.9 dBTP) ->
  `write_manifest_v5.py` / `sync_table_v5.py` -> `final/contact_sheet_v5_2fps.jpg`. Step 8: audio_check + film_qc
  (manifest_v5.json) + continuity_check, reports `final/*_v5*`.
- Expected machine time once free: ~4 + 12 + 65 + 5 + 20 = about 1 h 50 min, plus the wait for Matt's OK after step 4.
- Not automated (needs an eye): the cue re-pick for rows 1/3/6/7/9/11 (`cues_v5.json` "recheck" flags) before trusting
  the mix, the pick between the 1101 and 1102 Krea seeds, and the part E watch. Open question: `G_forest_v3` has Doug
  walking camera-RIGHT toward the log; the plan's map says row 3 tracks left. The clip prompt follows the still (no
  flip, so the moonlight key stays upper-left like its neighbours); flip it only if Matt wants the strict map.
