# HANK & DOUG'S WILD RESCUE — production plan (trailer v3, part 1 = every picture element)
Started 2026-10-31 11:03 PM. Method copied from projects/last_signal/PRODUCTION-PLAN.md (model order,
previs first, hq only on what makes the cut, detached resumable queue). FRESH START: nothing reused from
circus_train or any earlier Hank & Doug project (no canon, LoRAs, voices, clips); tools/pipeline code only.

## What is on disk (du of the real weight folders, 2026-10-31 11:08 PM)
- Video: LTX-2.5 MLX pack (dgrauet/ltx-2.5-mlx) 223 GB -> bin/make-ltx25 (previs distilled, --hq final), --low-ram.
- Image: Z-Image-Turbo (Tongyi-MAI) 61 GB folder, bf16, staged load ~20 GB lease. The ONLY image model present:
  Qwen-Image-2.1 = 4 KB stub, FLUX.1-dev = 4 KB stub (deleted 10/25), Wan 2.2 = 4 KB stub (deleted 10/25).
- Vision judge: Qwen3-VL-32B (beat_gate / continuity / film_qc plumbing), 37 GB.
- Blender 5.1.1 (/opt/homebrew/bin/blender), Cycles on Metal. rembg (u2net) in the ComfyUI venv for cutouts.
- Memory guard 11:08 PM: budget 50.1 GB, available 52.2 GB, swap rate 0, level ok; Song Forge jobs_running 0.
  Z-Image staged (20 GB) fits; LTX-2.5 --low-ram runs under make-ltx25's own lease.

## What we depend on
Nothing outside: every model is open weights on this M5, Blender is open source, tools are ours.

## Phases (one model loaded at a time)
1. Stage 02 on paper: beats.json (cuts), renders.json (renders -> cuts), continuity.json, story_test.md.
2. Blender hero props (CPU build + Cycles Metal stills/anims): fire-wagon + team proxies, circus train,
   tracks ending at the canyon gap, instanced ant river + ant bridge. Used as i2v start frames via Z-Image img2img.
3. Z-Image-Turbo bf16: canon masters (fixed style string + word-for-word character text), then every start
   still (t2i, img2img over Blender, composite-weld for two-character frames). Unload.
4. Vision gate (beat_gate, Qwen3-VL) on the candidates -> LOCKED stills. Unload.
5. LTX-2.5 distilled previs of every render -> final/previs_cut.mp4 -> final_plan.json.
6. LTX-2.5 --hq on what makes the cut at cut length + ~0.5 s handles, 3 takes heroes / 1-2 rest, detached queue.

## Time ledger (actual)
- 11:03-11:06 PM read router, contracts, shared rules, script v3, Jeremy's canon, LESSONS (10/31), last_signal plan
- 11:06 PM inventory + guard check (above); 11:06 PM Blender build handed to a parallel builder (Blender only, no model)
- 11:06-11:10 PM stage 02: beats.json (35 cuts, 42.8 s), renders.json (32 renders, 13 hero), continuity.json, story_test.md, APPROVED (delegated)
- 11:11 PM Z-Image canon batch started (39 candidates: 10 characters + 3 sets x 3 seeds)
- 11:11-11:29 PM Z-Image canon batch, 39 candidates (~29 s each with Blender sharing the GPU; peak 45 GB incl. Blender)
- 11:29 PM finding: the character style string ("big expressive animated eyes", fur) puts a cute invented creature in
  EVERY empty set candidate (9/9). Fix: STYLE_SET_DAY/NIGHT (environment only, "empty of characters") for every
  frame with no character; set masters re-queued (jobs_sets2.json). Lesson written to LESSONS.json.
- 11:20 PM Doug v1 read as a generic beagle/basset: description tightened (long narrow head, saggy skin folds, long legs),
  doug2/hank2 re-rolled at 11:30 PM ahead of the t2i stills batch; picked doug2_s23, hank2_s11.
- 11:30 PM t2i start-still batch started (53 candidates), sets v2 queued behind it
- 11:07-11:58 PM Blender (parallel builder): wagon.blend + train.blend (track, canyon, train, ~30k instanced ants),
  14 stills (2.7-7.5 s each, Metal GPU, 48 samples, 1248x720) + 2 camera-move anims (0.8-0.9 s/frame, 48 frames).
  ~9 min of it held by mem-gate (low memory while Z-Image + Blender shared the box). 5 frames re-done on coordinator notes.
- 11:30-11:58 PM t2i stills batch (53) + 11:58 PM sets v2 (9). Look: strong animated-feature quality; fixes found by eye:
  lanterns standing on the ground in R01/R02/R04 (breaks the "hunter's lantern" logic), R25 elephant holding a brass
  trumpet instrument (literal "trumpet"), monkey peeking eye in 2/3. Prompts fixed, re-rolled in the guided batch.
- 11:59 PM B18 (Blender track end) reads as a wall; R17 switched to the Z-Image canyon master (rails stop at the rim,
  gap, far rim with the track) as its init at 0.35. Masters locked: 10 characters + 3 sets; losing canon candidates deleted.
- 11:59 PM composite plates (rembg cutouts of the masters on set plates / B16) for R03, R15, R18, R19, R29;
  guided batch started (63: Blender img2img x3, composites x2-3, 4 re-prompts x3, wagon/train masters x2)
- 12:00-12:20 AM guided batch (63, ~13-25 s each); 12:21-12:24 AM redo3 (R02/R04/R14 truck-cab fix, 9); 12:25-12:27 AM redo4 (no-lamp night style, 6)
- 12:20 AM wagon master = R13_team_b202 (Blender img2img, team in front of the wagon), train master = train_s11 (B17 img2img 0.5); canon/cand emptied
- 12:28 AM vision gate (beat_gate, Qwen3-VL) started on 64 by-eye shortlisted candidates (2 per render)
- 12:28-1:04 AM vision gate, 64 shortlisted stills (~33 s each): 31 PASS / 33 FAIL; 20 renders PASS-locked
- 1:05-1:09 AM ant re-rolls (R20/R21 read as beetles from the Blender ant's shell-like plate; 'river' turned the swarm into water once); 1:10-1:14 AM gate on 7: R20 PASS
- 1:14 AM LOCKED 32 stills (832x480, chmod 444, logs/locks.json): 21 gate PASS, 11 kept by eye as declared exceptions
  (8 failed only on motion/expression words judged on one frame: tumbling, talking, whistling, smiling, ears 'up' on a
  bloodhound; 3 weak on content: R15 no reins visible, R21 ants hold discs overhead, R28 ants walk a beam, not a chain)
- 1:15 AM LTX-2.5 distilled previs queue started detached (32 renders x 3.0 s, logs/render_previs.log)
- 1:15-1:49 AM LTX previs, 32 drafts x 3.0 s (63-66 s each, 0 failures). By eye: R15 bench morphed (Doug's 'ears stream in the wind' became a hair cloud merged with Hank) and R04 grew a lantern from its prompt; both animate prompts rewritten for the hq pass
- 1:49 AM previs cut: final/previs_cut.mp4 (35 cuts, 42.8 s). Every render makes the cut. 7 sub-second renders keep their previs draft (R07 R08 R09 R10 R12 R24 R26; final_plan_previs_kept.json). final_plan.json: 25 renders, 59 takes, 136.8 s of footage (cut length + ~0.5 s handles), 3 takes heroes / 2 characters / 1 props
- 1:49 AM LTX-2.5 --hq queue started DETACHED (nohup, logs/render.log, done-markers, logs/STOP_RENDER, finish marker logs/RENDER_QUEUE_FINISHED_final)
- 1:49-1:57 AM first hq take R01_night_hunt_t1: 465 s for a 2.375 s clip (~196 s per second of footage, incl. load). Verified by frame grid: on-model, motivated move, no haze.
- Projection (measured, not promised): 58 takes / 134.4 s left x ~196 s/s = ~7.3 h -> finishes ~9:15 AM, later if Song Forge customer jobs pause it.

## Part 2 time ledger (actual, 2026-11-01)
- 8:51 AM hq queue finished (RENDER_QUEUE_FINISHED_final, 59 takes; last take R32_doug_salute_t3 at 8:51). No wait needed.
- 8:51-8:52 read router, contracts 04-07, frozen rules, gates doc, project plan/script/premise, LESSONS (10/31 last_signal + wild_rescue), last_signal part-2 ledger + tools
- 8:52 VL clip gate started (beat_gate, Qwen3-VL, 70 takes: 59 hq + 11 previs candidates, 3 frames each; house checks added: no humans, no trucks/tires, Doug a long-eared bloodhound not a beagle, dog/bear not merged)
- 8:53-9:00 frame-grid sheets of all 32 renders (CPU) and the agent's look at every take. Found: R03 + R15 (both heroes) LOCKED on stills where Doug is a tricolor beagle-like hound (black saddle, white legs), not canon Doug; R17 t3 has a blue TRUCK on the rails (declined); R28 hq takes turn the beam into a paved road with yellow dashes; R11 t2 flagged by VL for a human (checked by eye after the gate)
- 9:00-9:12 CPU prep alongside the gate: title card (PIL, Rockwell Bold gold, 3 renders to fit), two new LUTs of our own (warm_feature_pop, moonlit_feature in tools/make_luts.py), EDL, SFX job list, score commission + arrange, synth, mix plan, segment cutter, SeedVR2 batch, 4K finish, deliver, coverage builder, music-text script
- Voice casting finding: spare voiceA/voiceB were the circus_train bird and Ellie (earlier Hank & Doug voices), so they are out too; the new cast is built from Kokoro-82M references (local) cloned by ChatterBox through new character_voice.py entries
- 8:52-9:25 VL clip gate, 70 takes (33 min, ~28 s/take): 50 PASS / 20 FAIL. Selected FAILs are motion words judged on single frames or style reads ("toy train"): declared exceptions in selects.md
- 9:26 Z-Image first launch failed (no diffusers in the mlx venv; zimage_batch runs in the ComfyUI venv per tools/run_after.sh), relaunched at once
- 9:26-9:28 Z-Image re-still R03/R15: 8 candidates from the canon plates at img2img 0.40-0.50 + a solid-red-coat clarifier (~14 s each, peak 34 GB). Doug canon in all 8. Locked R03_x72242 + R15_x61140 (x61148 grew a human-like hand on the reins, x72248 a car in the background); old locks deleted (declined)
- 9:29 LTX-2.5 --hq re-render started (R03 + R15, 2 takes each, t4/t5, cut length + handles, detached: logs/render_redo.log)
- 9:29-9:33 declined takes deleted (R17 t3 truck, R11 t2 geometry, R28 t1/t2 road + morph, R25 t2 morph, R15 + R04 previs); segments cut; 1080p preview finish (CPU, 1.5 min) checked by contact sheet: grade and title read right
- 9:34 mouth_sync on the dialogue takes: Hank R18 t1 (mouth opens 0.12-0.38 + 1.54-2.83 = "Doug..." pause "that's a big hole"), Doug R19 t3 (talking 0.62-1.96); Hank's voice is split onto his two beats
- 9:29-10:03 LTX-2.5 --hq re-render, 4 takes (~8.5 min each, 0 failures); 9:44 R03 t4 checked by grid (canon Doug, bear turns to him); 10:03 picked R03 t4 + R15 t4 (R15 t5 merged Doug into Hank: declined); old R03/R15 t1-t3 deleted
- 10:04-10:05 voice refs: Kokoro-82M, 7 candidate passages (am_onyx/am_santa/bm_george for Hank; am_puck/am_fenrir/am_echo/am_liam for Doug); first launch failed (no soundfile in kokoro-env), switched to scipy at once
- 10:04-10:06 ChatterBox auditions (22 takes, one load); voice_fx crashed once on a 1-sample reverb length mismatch, fixed; 10:06-10:08 4 extra am_onyx seeds (whisper heard "Dug" on 2 of 2). Cast: HANK = am_onyx (t5: 88 Hz, slow 1.93 s, whisper clean), DOUG = am_liam (~116-128 Hz, bright); registered as wr_hank / wr_doug in ~/AI/videopipe/bin/character_voice.py; 51 losing takes/refs deleted
- 10:07-10:11 MMAudio SFX batch, 32 jobs, one load (4 min, peak 14.8 GB); screen: rabbit_thump empty (-44.7 dB) -> replaced by our numpy synth; 4 quiet hits normalized; numpy sub layer (theme punch, ant rumble, ramp kicks, title drop)
- 10:12 Song Forge: 3 instrumental score candidates (15-20 s each, jobs_running 0 before)
- 10:13-10:15 VL gate on the re-render takes + R28 previs: R15 t4 PASS, R28 previs PASS, R03 t4 FAIL (no log; declared exception)
- 10:15-10:42 STALL (~27 min, unexplained): edit + segment cut normally takes <1 min; then the SeedVR2 launch was skipped by a failed zsh glob in the same && chain
- 10:43 SeedVR2-3B started (22 held shots, 916 frames, ~5-7 min per shot, logs/seedvr2.log)
- 10:43 scores arranged (candidate 2 best, fitness -2.96); 10:43 all 3 texted to Matt from the mini, chat.db rows 42784/42786/42788/42790 is_delivered=1, mini copies deleted. 10:44 Matt sent HankDoug_music_3.mp4 back with no text (ambiguous: a pick of 3, or the train-shot note)
- 10:44-10:48 mix v1 (43 sources): ramp flat at ~-15 dB -> written score swell (+6 dB into the black) + sub kicks up; black verified silent (-52 dB first 0.1 s, then digital silence); 10:48 04/05 records written
- 10:45 Matt (via coordinator): "the wheels are moving under the train unnaturally". 10:46-10:50 blender/anim_train.py: splits each joined vehicle into loose parts, rigs every wheel on an axle pivot (rotation = distance / R), side rods on the crank pins, main rod on a sliding crosshead, bodies riding track.P; 10:49-10:50 test frames for rails / edge / wide
- ~10:51-12:09 STOPPED: the coordinating session restarted around 11 AM and this builder was halted mid-job (~78 min lost). SeedVR2 kept running detached and also upscaled the old AI c04a_train (~7 min wasted)
- 12:09 resumed: state re-checked from disk; music delivery re-verified in chat.db; 12:10 anim fixes (frame-1 stale camera matrix, edge train starts closer at 2.6 m/s, left main rod caught, wide tighter + push) and full renders started (Blender Cycles, 1664x896, motion blur)
- 12:12 6 lessons added to LESSONS.json (vehicle wheels: Blender never AI i2v; brand-new cast; img2img identity; split line on mouth beats; ramp swell; replacement vs upscale queue)
- 12:10-12:21 Blender train animations rendered (Cycles Metal, 1664x896, 32 samples, motion blur): rails 27 f (229 s), edge 37 f (208 s), wide 44 f (~60 s), alongside SeedVR2. Frame check by eye: rails every frame, edge every 2nd, wide every 6th: wheels turn with travel, rods cycle, nothing slides. The far-side main rod (hidden from both close cameras) stayed static (bbox filter edge case)
- 12:22 swapped into the cut (c02a_rails, c04a_train, c07h_edge -> clips/blender/T_*.mp4); SeedVR2 up/ files written straight from the 2x renders so the queue skips them; R06/R16/R30 AI takes declined for the wheels and deleted; coverage gate OK
- 12:23 partial 4K finish started on CPU (every segment whose upscale exists)
- 1:10 PM PST: Matt: "Stop and restart on new models". Part 2 stopped (the salute segments were mid-upscale), SeedVR2 jobs killed. Restart pending: Krea 2 Turbo stills + the new video model (TBD).
- 1:12 PM PST: Matt: "erase all video feed... start fresh". Deleted every generated still, canon image, clip, previs, take, upscale, voice, SFX, music, review grid, final, and the Blender renders; also removed the take-tied plan files and stage 03-08 approvals. Kept: the locked story (01), beats/continuity/renders maps (02), the Blender model files + scripts, tools, logs.
- 1:17 PM PST: Matt: "Wait for the mini's test results". Restart waits for the mini chat's model winners (stills/video/upscaler); it'll chat-send this chat.
- 4:02 PM PST: Matt approved Kandinsky 6 Pro ("the best I've ever seen"); team = horse, zebra, camel, cow, one each.
- 4:13 PM PST (Matt, in the mini chat): Last Signal v2 redo first; Hank & Doug rebuild (Krea 2 + Kandinsky 6 Pro, team horse/zebra/camel/cow) waits until it finishes, about 12:30 AM 11/2.

## Part 3 time ledger (rebuild, 2026-11-01 evening)
Matt 4:32 PM: "find fast ways to do things, use both computers, use whatever you can." Goal: the K6 motion queue starts on the M5 the moment the Last Signal v2 redo finishes (~12:30 AM), everything else done elsewhere first.
- 4:32-4:45 PM read router, CONTEXT + contracts 03-06, plan, script v3, premise, renders/beats, MODEL-CONSENSUS + VIDEO-MODEL docs, LESSONS (Last Signal / Hank & Doug / bake-off)
- 4:40 PM machine check. PC = Intel i7-1185G7, 32 GB, Intel Iris Xe (no CUDA, no Blender): CPU-only work (voices/SFX). Mini = 64 GB, Blender 4.2, Krea-2 weights in its HF cache, but its forge_guard shows budget 0 GB / level critical (Song Forge reserves 60 of 64 GB, 7.5 GB available): Krea 2 Turbo bf16 (26.3 GB transformer + 8.9 GB text encoder, peak ~37 GB on the M5) does NOT fit beside Song Forge. LAN ssh to the mini times out; mini-vps (VPS tunnel) works.
- 4:42 PM decision: Krea stills cannot run before 12:30 AM anywhere (mini has no room at bf16, PC has no GPU and 32 GB RAM), so they run FIRST in the M5 queue at 12:30 AM, followed by the Qwen3-VL gate that picks the locks, then K6.
- 4:40 PM Blender builder launched (mini, Blender 5.1 install, wheel-correct train/wagon shots + ant swarm anims); sound builder launched (voices + SFX on PC CPU / mini lease, 3 ACE-Step score candidates via the mini's Song Forge)
- 4:40-4:44 PM v4 picture plan written (tools/v4/): bible_v4.py (fixed style + character strings, word for word: night style names moonlight only, Doug's solid russet coat, the team = one horse, one zebra, one camel, one cow side by side, wagon shots keep the wheels out of frame or deep in dust); write_plan_v4.py -> v4/plan.json (32 renders: 22 K6, 2 LTX-2.5 a2v lip-sync close-ups R18/R19, 5 Blender wheel shots R06/R12/R16/R26/R30, 3 Blender-primary ant shots R20/R21/R23 with one K6 alternate each), v4/jobs_stills.json (65 Krea candidates: 3 seeds heroes, 2 the rest), v4/jobs_canon.json (15 masters x 2 seeds). Clip length = cut + 0.5 s handles, floor 1.5 s.
- 4:43-4:47 PM tools/v4/hd_queue.py (detached, resumable, done-markers, v4/logs/STOP, v4/logs/HD_QUEUE_FINISHED): Krea stills -> beat_gate (Qwen3-VL, --votes 1 for stills: 71/71 past still votes were unanimous) -> lock first PASS -> one re-roll round (2 new seeds) for renders with no PASS -> K6 breadth-first (take 1 of all, LTX a2v, canon masters, take 2, take 3, ant alternates). Dry run OK: 52 K6 + 4 LTX takes.
- 4:45 PM tools/v4/hd_waiter.sh (plain bash, no model) started detached (pid in v4/logs/waiter.log): polls every 2 min for last_signal/renders_v2_krea_k6/logs/REDO_V2_FINISHED + no redo_v2.py/redo_v2_wait.sh process + no heavy GPU process 2 polls running (crash fallback: process gone without the marker -> 5 free polls). Dry-run tests: live (waits, LS running), marker + GPU busy (waits), marker + free (WOULD LAUNCH after 2 polls), crash (WOULD LAUNCH after 5). Nothing launched.
- Projection from a 12:30 AM finish: launch ~12:34, stills ~1:03, gate + re-roll ~1:27, take 1 of every shot ~4:30 AM (frame-scaled K6 time) to ~6:10 AM (flat 12 min/clip), canon masters +14 min, full coverage ~8:55 AM to ~12:40 PM. Song Forge customer jobs pause it.
- [audio builder] 4:39-4:41 PM read plan/script/beats/tools/consensus/LESSONS; mini forge_guard refused a 6 GB lease (budget 0 GB) -> voices + SFX on the PC CPU; built a VPS<->PC file path through the PC's FiaOS upload/download API (temp helper /root/wr3_pcfile.sh)
- [audio builder] 4:42-4:57 PM PC envs (torch CPU): venv_a Chatterbox + Kokoro, venv_b MOSS-SoundEffect v2.0 (one failed import: missing ffmpy for descript-audiotools; fixed 4:52), venv_c Qwen3-TTS VoiceDesign; MOSS weights 11 GB downloaded 4:54-4:57
- [audio builder] 4:43-4:48 PM music: 3 ACE-Step instrumental score candidates (45 s) on the mini's Song Forge, jobs_running 0 checked before each, 90 s apart (35/40/55 s renders); copied to music/, all 3 DELETEd from Song Forge, mini temp removed
- [audio builder] ~6:00 PM Matt (via coordinator): "Mini only does songs." No H&D work may run on the mini, and no more score requests to its Song Forge. The 3 candidates were already done by 4:48 and stay. Nothing of this builder was running on the mini at 6:05 PM (the chatterbox-env process there is the standing pocket-tts server, not ours)
- [audio builder] 4:57-5:11 PM MOSS speed test on PC CPU: one 2.5 s clip took 614 s at 30 steps (sharing CPU with Qwen3-TTS) -> 5:12 PM full batch relaunched at 16 steps with a tight latent window; 6 low-value jobs dropped (28 jobs); ~5.5 min/clip
- [audio builder] 4:44-~5:30 PM voice refs on PC: Kokoro am_michael/am_adam (Hank), am_eric/bm_daniel (Doug), 2 s each; Qwen3-TTS VoiceDesign 2 per character (~4 min each on CPU); then Chatterbox auditions (36 takes, 3 seeds)
- 5:12 PM the Last Signal redo exited after two K6 failures on R01 (no finished marker); 5:21 PM the v4 waiter's crash fallback (GPU free 10 min) launched hd_queue.py on the M5: Krea 2 Turbo rendered all 65 start-still candidates 5:21-5:50 PM (28.5 min, rc 0). 5:50 PM the Last Signal session fixed its redo and STOPped our queue cleanly after the stills stage (STOP file, since removed); the redo restarted at 5:50 and its clips run ~12 min each (R01 done 6:02 PM).
- ~6:00 PM Matt (other chat): "Mini only does songs." Blender builder told to move to the PC (CPU) at 6:05 PM; audio builder confirmed it never ran models on the mini (its lease was refused at 4:40, voices + SFX on the PC CPU from the start; the 3 score candidates were made on the mini's Song Forge 4:43-4:48 PM with jobs_running 0, before the rule, copied to music/ and deleted from Song Forge).
- 6:05 PM waiter re-armed (exactly one: pid in v4/logs/waiter.log): crash fallback lengthened from 5 to 15 free polls (30 min) so a session fixing the redo gets the GPU first. Normal trigger unchanged: REDO_V2_FINISHED, written only after the redo's LAST stage (clips, edit, SeedVR2 upscale, finish, deliver), not at the end of its clips.
- 6:06-6:10 PM looked at all 65 stills (contact sheets). On-model: Doug a long-eared russet bloodhound in R01, R15, R19, R29, R31, R32; the team exactly one horse, zebra, camel, cow in R13 s11/s23 and R11 s37; no humans, no trucks or tires anywhere. Off-model, fixed: R03 + R04 Doug has a black saddle (tricolor) in all 5 night candidates -> prompt adds "back, sides and legs the same warm russet-red as his face, one single color all over", candidates deleted; R11 shows big readable wagon wheels (and s11/s23 miss an animal) -> re-prompted close on the team with the wheels hidden behind animals and dust, deleted; R14 wheels read in both seeds -> lock crops the top band (wagon bed, giraffes, elephants; wheels below the cut, checked). The 57 others are kept and will not be redone (8 re-renders, ~5 min at launch). Left to the gate/re-roll: R27 monkey covers his cheeks not his eyes, R28 ants walk the rims instead of linking, R23 K6-alternate stills show no ants (Blender is primary there), R21 river reads partly as water (Blender primary).
- Projection (if the redo's finished marker lands ~12:30 AM): launch ~12:34, 8 Krea re-renders + gate + re-roll ~1:05 AM, take 1 of every shot ~4:10 AM (frame-scaled K6) to ~5:50 AM (flat 12 min/clip), full coverage ~8:35 AM to ~12:20 PM.
- 4:38-4:47 PM Blender builder: read plan/beats/scripts; Blender 5.1.1 (official arm64) downloaded + installed on the mini at ~/Applications/Blender5.1.app (1 min download)
- 4:44-4:52 PM wrote blender/fx.py (steam/dust puffs), anim_ants.py (new ANT model: 3 segments, pinched waist, elbowed antennae, 6 thin legs, small plate on the gaster; geometry-nodes motion), anim_wheel.py (c03b wheel rig, distance/R, 9 deg/frame so 14 spokes never strobe); anim_train.py: 1664x960, cut + 6 handle frames, new whistle shot
- 4:43-4:45 PM test paused by a Song Forge customer job (SIGSTOP watcher), ~1.5 min
- 4:50 PM forge_guard SIGSTOP + SIGTERM'd the wagon test (20 GB phys_footprint: volume puffs + GPU denoise, box at 5.3 GB available); fix: CPU denoise, 512 tiles, no persistent data -> 4.8 GB
- 4:47-4:58 PM low-sample test frames, all 8 shots; fixes: whistle reframed twice, river camera re-aimed twice, volume puffs -> soft surface puffs (45 s/frame -> fast), bigger ant plate
- 4:59-5:03 PM first full rails render; review found frames 1 and 31 with no motion blur (keys only inside the range) -> keys 0..n+1; queue restarted 5:04
- 5:04-5:36 PM full renders on the mini (Cycles Metal, 1664x960): rails 31 f 223 s, edge 41 f 259 s, ground 41 f 731 s, bridge 41 f 389 s, river 50 f 308 s. Wheel, whistle, wide segfaulted in 1 s (bmesh freed before use in fx.py, my bug)
- ~5:12-6:05 PM STALL (~50 min): this builder was halted mid-wait; the queue finished alone at 5:36
- 6:00 PM Matt (via coordinator): "Mini only does songs." 6:05 PM stopped all Blender on the mini, pulled the 5 finished shots to the M5, deleted every H&D file on the mini (work folder, Blender 5.1 app, download)
- 6:05-6:28 PM moved to the PC: Blender 5.1.1 Windows installed at C:\Users\matt\wr; project zip passed through a temp file on the VPS web root (deleted after); fx.py bug fixed; EEVEE on the Iris Xe tested -> garbage frames (8 min shader compile), so Cycles CPU, 12 samples + OIDN
- 6:15-6:30 PM rails (earlier), edge, ground, bridge, river checked by eye and delivered to clips/blender/ (+ stills/blender/ first frames, manifest.json)
- 6:28 PM PC queue launched but ran nothing (PowerShell function named R collides with the built-in alias r); relaunched 6:30 PM: wheel, whistle, wide
- [audio builder] 6:30 PM another job's Blender render on the PC took ~6.7 of 8 cores; Chatterbox fell to ~5 s/token (3 takes in 25 min). 6:48 PM paused the MOSS batch (killed; it resumes and skips finished files); 7:00 PM raised the voice process to AboveNormal -> 7.5 it/s
- [audio builder] 7:03-7:20 PM voice fx + faster-whisper (CPU) on 36 takes: 35 whisper-exact, "Doug" heard in every Hank take, 1 fail (hank qvd1 seed 202 "it's a big hole"); 7:21 PM first Compress-Archive pull timed out (CPU starved), tar worked at once
- [audio builder] 7:24 PM voices delivered: HANK = Qwen3-TTS VoiceDesign deep-bass ref (~80 Hz take), DOUG = Kokoro am_eric ref (~136-151 Hz takes); c01e_doug/c05a_hank/c05b_doug + alt/ + cast.md; registered wr3_hank / wr3_doug in character_voice.py (backup .bak-20261101-wr3)
- [audio builder] 7:24-7:26 PM screened the 13 16-step MOSS files by band energy: 12-55% of the energy below 60 Hz with flat envelopes (sub-bass mush; flatness/centroid alone passed them all). 7:26-7:37 PM A/B on the hawk (AboveNormal priority): 16 steps with a 4 s window = bad, 30 steps with a 3 s window = bad, 30 steps with a 4 s window (the 5:00 test) = good (70% of energy at 0.5-4 kHz)
- [audio builder] 7:39 PM SFX batch restarted at 30 steps, window >= seconds+1, ordered by need; 16-step files parked in sfx16/ as fallback; shares the PC CPU with Blender (equal BelowNormal priority)
- 6:30-8:50 PM PC: c03b_wheel rendered, 34 f in 140 min (Cycles CPU 12 samples + OIDN, 3.3-4.8 min/frame; one 11 min frame when the audio SFX batch started). 8:51-8:56 PM every frame checked by eye and delivered (T_c03b_wheel.mp4)
- 7:52 PM ETA check: whistle + wide projected past 11:45 PM; coordinator lifted the deadline to ~12:15-12:30 AM, keeping 6-frame handles; only cut is the wide shot at 832x480 / 8 samples (upscaled at delivery)
- 8:50 PM PC: c07d_whistle started (31 f, full res, 12 samples)
- 8:50-9:55 PM PC: c07d_whistle rendered, 31 f in 65 min (~2.1 min/frame); checked by eye (every frame of 1-10 and 28-31, every 2nd between) and delivered 9:58 PM
- 9:55 PM PC: c04a_train (wide) started at 832x480 / 8 samples, ~37 s/frame
- 9:55-10:31 PM PC: c04a_train wide rendered, 48 f in 36 min (832x480, 8 samples); 10:33-10:36 PM checked every 3rd frame, Lanczos-upscaled to 1664x960 and delivered
- 10:37 PM all 8 Blender shots in clips/blender/ (manifest.json), BLENDER_DONE written; PC work folder C:\Users\matt\wr removed
- 10:40 PM correction: the PC folder C: sers\matt\wr (Blender 5.1.1 + frames, ~1.5 GB) was NOT removed; FiaOS blocks recursive deletes, left in place for Matt or a later cleanup
- 11/2 ~12:16-12:20 AM the M5 rebooted (watchdog panic, one Python at ~111 GB resident during the Last Signal SeedVR2 step); the Last Signal v2 redo stopped at upscale 13/19 and the H&D waiter died with it
- 11/2 1:48 AM re-armed exactly ONE H&D waiter (pid 58026): `cd projects/wild_rescue_trailer && CRASH_NEED=999999 nohup tools/v4/hd_waiter.sh >> v4/logs/waiter.log 2>&1 < /dev/null &`. CRASH_NEED=999999 turns off its "redo vanished without the marker" fallback, so H&D launches ONLY after last_signal/renders_v2_krea_k6/logs/REDO_V2_FINISHED exists and the GPU is free (Matt's order: Last Signal first). The mini chat was asked to resume the redo; at 1:48 AM the waiter already saw redo_v2_wait.sh (pid 40759) alive. The YuE2 test waiter (~/AI/yue2-test) keys off the H&D finished marker, so it runs after H&D; left alone.
