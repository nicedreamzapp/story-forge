# THE LAST SIGNAL — production plan (2026-10-31, not built yet)
Goal: feature-film trailer feel, all local on the M5, one model in memory at a time.

Phases run in model order (load, batch everything for that model, unload, next):
1. Ship model: Hunyuan3D draft mesh -> Blender refine -> Cycles hero renders + flythrough camera paths (real scale, consistent ship)
2. Look frames: Qwen-Image 2.1 (bf16) all stills, Flux.1-dev for alternates -> unload
3. Motion: Wan 2.2 A14B (MLX bf16) i2v/t2v, 3+ takes per shot -> unload. LTX 2.5 only for fast previs.
4. Restore: SeedVR2-3B upscale to 4K -> unload; RIFE to 24fps-smooth motion
5. Finish: ffmpeg grade (teal/orange LUT), anamorphic 2.39:1 bars, grain, lens flare plates from Blender
6. Sound FX: MMAudio from picture (synced rumble, metal groan) + layered sub-bass designed in our own numpy synth
7. Score: ACE-Step 1.5 XL turbo, trailer cues (drone, braams, silence, final hit)
8. Voices: Chatterbox (planet voice pitched/layered, captain whisper, ship computer)
9. Mix: our own python panner -> 5.1 (ship sweeps front->rear, LFE on rumble) + stereo downmix
10. QC: film_qc.py (Qwen3-VL + whisper), reports read before Matt sees it

Add-ons proposed: Stable Audio Open (SFX), our own 5.1 panner script, film LUT pack.

## Decisions (2026-10-31)
- 2:35 AM Matt picked the FULL version (~13 hrs, now ~15 with script v3): Wan 2.2 14B bf16 on ~12 hero shots, 3 takes each.
- Tools added + wired into pipeline: bin/make-sfx (MMAudio, not Stable Audio — no sign-ins), bin/grade + luts/, bin/surround-mix (5.1 + stereo).
- YouTube: Nice Dreamz channel, "my first AI sci-fi, local on Mac M5 128GB"; title + making-of still to pick. Post only on Matt's OK.
- Build not started: Matt said "dont build yet" (2:14 AM); start only on his go.
- 2:45 AM Matt heard the MMAudio test rumble on his phone: "Good, use MMAudio". Stable Audio dropped for good.
- 2:52 AM script v3 locked (fast-cut, ~40 cuts, ~50s).
- 3:07 AM Music: ACE-Step instrumental, cut to v3 beats (drone under beep → BRAAAM on arrival → rising strings → dead stop for "Welcome back" → accelerating drums w/ horn hit per cut → silence for whisper → final hit on title). Make 3 candidates DURING the full build, text them to Matt, he picks by ear.
- 3:08 AM Matt: "just get the whole trailer done i will review, we can make this our first sci fi video locally". Mid-build approvals (canon masters, scenes, voices, score pick) are delegated to the builder: pick the best, keep the alternates until Matt approves the final film. Matt reviews only the finished trailer (READY FOR MATT, after the gates).
- 3:25 AM (builder, part 1): Wan 2.2 is NOT on this M5. All four Wan 2.2 14B files + umt5 were deleted 10/25 at Matt's OK when LTX-2.5 was named THE video model ("nothing open beats it on a Mac"); the AITRADER Wan MLX cache folder is empty, and core.py records that the Wan fp16/bf16 i2v pair OOM-kills ComfyUI with Song Forge resident (the only safe Wan path was a Q6 quant, which breaks the bf16 rule). So motion runs on LTX-2.5 bf16 (MLX, bin/make-ltx25 --low-ram, mem-gate + forge_guard lease), same takes plan (3 per hero render, 2 for the rest). Real Blender camera-move animations are the second motion source for the ship shots (rule 29 coverage). FLUX.1-dev was deleted the same night, so alternates are extra Qwen-Image 2.1 seeds. Hunyuan3D weights link is broken, so the ship is modeled procedurally in Blender.
- ~3:45 AM Matt (via coordinator), creature: MattPaint's "The Watcher Beyond the Stones" (canon/creature_layout_guide.png; banner-cropped working copy stills/refs/creature_layout_nobanner.png) is the COMPOSITION/SILHOUETTE guide only for R15 (mountain shape) and R19 (eyes). The photoreal creature comes from Qwen-Image 2.1 bf16 with the guide + plain canon as references: tall thin stone-and-fog giant, long arms, crown of jagged spines, vertical line of teal eyes, tiny human for scale. beats.json R15/R19 wording updated to match.
- PART 2 TODO (from Matt via coordinator): add a glare/bloom pass on the engine nozzles at the grade stage (R14 engines, R03 dive, R18 grab, R01). Arrival shadow sweep: R04 animate prompt now asks for the hull shadow racing across the ground toward and past camera; the Blender anim_04_arrival also carries a shadow sweep. Pick whichever take shows it best.
- 4:43 AM Matt approved the faster motion method (via coordinator), applied here: (1) previs first, one LTX-2.5 distilled --low-ram draft per render into clips/previs/; (2) a rough previs cut against the v3 timings, final/previs_cut.mp4, decides which renders and which seconds are used (written to final_plan.json); (3) the quality pass renders ONLY the used shots, at cut length + ~0.5 s handles, 3 takes for the 6 heroes and 1-2 for the rest, and a previs draft that is already good enough for a strobe cut is kept with no re-render; (4) render at 832x480 (480p class), SeedVR2 upscales in part 2. Builder note: the quality pass engine is LTX-2.5 --hq (dev transformer + CFG two-stage), NOT Wan 2.2. Wan isn't on this machine (deleted 10/25, see the 3:25 AM line) and its bf16 i2v path OOM-kills ComfyUI with Song Forge resident. Re-adding it means a ~68 GB download plus an OOM risk to customer jobs, so that call is Matt's.
- 4:50 AM image phase held by forge_guard: another chat's SFT training run (lfm3-agent-sft, 20 GB lease) left only 23 GB of the 50 GB render budget, and Qwen-Image needs 48 GB. The batch retries every ~17 min (tools/run_qwen_retry.sh) and never overrides the guard.
- 4:50 AM image model switch (coordinator: find an installed bf16 model that fits the guard's allowance and run the whole canon and all start stills on it). Z-Image-Turbo (Tongyi-MAI, 6B, bf16, fully downloaded in the HF cache, top-tier photoreal, 9 steps) runs staged: the text encoder encodes every prompt and is freed, then the transformer and VAE render, with a 20 GB lease that fits the 23 GB allowance. Qwen-Image 2.1 (48 GB) is parked. FLUX.1-dev is gone, so it can't be used. Trade-off: Z-Image has no reference-image input, so the characters are held by a fixed word-for-word description and then face_lock (inswapper) from canon, and the creature guide and Blender ship frames go in through img2img (guide 0.82-0.9, ship polish 0.42, ship-grab 0.6-0.72). The whole look stays on one model.
- 6:25 AM motion status: 20 previs drafts done, 5:45-6:15 AM (~106 s each, no failures). The previs cut (final/previs_cut.mp4, 39 cuts, 39.3 s) set final_plan.json: 18 renders, 35 takes, 105.9 s of footage. R19/R20 keep their previs drafts for the strobe. The quality pass started 6:15 AM. First hq clip: 528 s for a 3.7 s clip (~143 s per second of footage), so the full pass projects to ~4.2 hrs, finishing ~10:30 AM (later if Song Forge jobs pause it).

## Time ledger (actual)
- 3:08-3:20 shot list (12 min)
- 3:20-4:27 Blender ship, 7 stills + 2 animations (67 min, 27 over)
- 4:32-4:48 STALL: memory guard refused Qwen-Image (16 min)
- 4:50-5:45 Z-Image canon + stills + redos + vision gate (55 min)
- 5:46-6:14 LTX previs, 20 drafts + rough cut (28 min)
- 6:15-~11:30 LTX hq quality pass, 35 takes (~5h15, ~1 hr over the 4.2 h projection: ~9.5 min/take vs 8.8 projected)
- Lessons written to LESSONS.json (5) on 10/31.

## Part 2 time ledger (actual, 2026-10-31)
- 11:29-11:31 read the contracts + plan
- 11:31-11:56 04 VL clip gate, 44 takes x 3 frames (25 min); 10 PASS / 34 FAIL, mostly motion beats judged on stills (declared exception, selects.md)
- 11:34-11:35 05 score: 3 ACE-Step candidates (~20 s each, ran alongside the gate on Song Forge's resident engine)
- 11:36-11:57 06 prep on CPU while the gate ran: final EDL (50 cuts, 46.6 s), title card (PIL, 33 s), segments, synth (sub/beep/hits), selects, 04 APPROVED
- 11:57-12:01 05 SFX: MMAudio batch, 25 jobs, one load (4 min)
- 12:02-12:03 05 voices: ChatterBox, 9 takes, one load (1.5 min); 12:03-12:04 voice FX + whisper check, scores whisper-screened clean
- 12:04 music texted to Matt from the mini (text + 3 mp4s, all is_delivered=1)
- 12:05-12:34 STALL: SeedVR2 bring-up (29 min): flash_attn crash (fixed with a wrapper), then 4K direct measured at ~7 min per 21-frame ENCODE (killed), 720p measured at ~13 s/frame; plan changed to SeedVR2 720p on held shots + lanczos to 4K
- 12:13-12:20 06 mix (numpy, CPU, alongside): two bugs found by per-half-second RMS (score clamped at the dead stop; sub-hit tail in the black), fixed
- 12:34-~15:45 SeedVR2-3B 720p, 19 held shots, 866 frames (projected ~3.1 h at 13 s/frame)
- 12:34-15:56 SeedVR2-3B 720p, 19 held shots (~12.7 s/frame; one 30 s wait for a Song Forge customer job ~14:54). 14:20 batch sizing fixed after a 46-frame shot padded to 90 frames (~9 min lost)
- 15:19-16:02 4K finish (bloom + bin/grade per segment) run on CPU alongside SeedVR2
- 15:27-16:45 STALL: the arrival (c04, the only 3-batch shot) came back grey with white smears in batch 2, twice (caught by frame-vs-source check at 15:27 and 16:18); approach changed to 2 single-batch chunks
- 16:42-16:46 4K finish + muxes (scream SFX added, MMAudio one job)
- 16:46-17:08 07 gates round 1: audio_check, continuity (209/209), film_qc 51/53, face_check 7 shot FAILs
- 17:09-17:16 fix: face-locked the captain/crewmate shots that failed face_check (walk, welcome, 2 sprints), re-finished, re-muxed
- 17:16-17:37 07 gates round 2 on the final cut: audio FAIL(balance, structural) 2 WARN, face 6 PASS/4 FAIL/4 UNCHECKED, film_qc 51/53, continuity PASS
- 17:38 known_defects.md written; READY FOR MATT check
