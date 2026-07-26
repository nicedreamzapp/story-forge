# Story Forge — local AI generative video system

This directory is the home of **Story Forge**, a robust 100%-local generative VIDEO system — for making video of ANY kind (narrated explainers, ambient pieces, promos, documentary cuts, sagas, cartoons) in any style, from one readable `.sf` script. It is NOT a cartoon studio. Cartoons are just the case it works decently for right now — talking characters are the hardest case, so they're the proving ground, not the limit. When Claude Code starts here, this file auto-loads to bring you up to speed.

## How we build (the ethos — apply this to every decision)
- **Build off what we KNOW works.** Perfect the proven win, then extend from it. Never restart from scratch and never chase an unproven path when a working one exists. Every new feature stands on a tested foundation.
- **This is OUR environment, running OUR language (`.sf`).** We do not lean on other people's systems that are slow, old, and not tuned to our machines. The DSL exists so we control the whole stack end-to-end.
- **Built FOR our hardware, taking full advantage at all times.** M5 Max 128GB does the heavy lifting, the mini runs in parallel, everything is Apple-Silicon / MPS-native and 100% local — no cloud inference, ever. We know exactly what we have and make the most of it.
- **The result: faster, fully owned, hardware-matched.** That's the whole point — escape generic, sluggish, mismatched tooling and run a pipeline that fits this hardware perfectly.

**Live products:**
- 🌐 Public site: https://nicedreamzwholesale.com/software/story-forge/
- 🐙 GitHub: https://github.com/nicedreamzapp/story-forge
- 🎬 First film: https://youtu.be/_bFQTl7_vF4 (live, public, made for kids)

**Read this first:**
- `~/Desktop/PROJECTS/story-forge/SESSION_HANDOFF.md` — full session state, what works, what's broken, where to resume the two-week speedup build.

**Quick file map:**
- `story_pipeline.py` — the core pipeline (Flux + Wan + Piper + ACE-Step + ffmpeg, config-driven)
- `server.py` — Flask UI server on port 17600
- `ui/story.html` — Story Forge web form
- `bin/make-video` — Wan inference CLI (works)
- `bin/make-ltx-video` — LTX-Video fast-mode CLI (BROKEN, see SESSION_HANDOFF "Open problems #1")
- `bin/render-route` — auto-picks Wan vs LTX per scene
- `bin/story-new` — scaffold a new project in one command (`story-new "Name" --style … --format …`)
- `story_forge/packs.py` — style + format packs (the "any style, any format" layer); `/api/packs` serves them to the UI

**The frozen rules (lessons learned, don't re-derive):**
1. Piper flag is `--noise-w-scale` (NOT `--noise-scale-w` — wrong order gets read aloud)
2. Render each Piper sentence to its own file, concat with silence (Piper `-f` only saves last stdin line)
3. Scene-synced narration via `adelay+amix`, never naive concat at t=0
4. Native 5-sec Wan, never `setpts*1.5` stretch (looks like dreamy slow-mo)
5. QC every audio/video output before showing Matt — use silencedetect, spectrograms, extracted frames. Never trust duration alone.
6. Wan can't do object collisions, physics, lip sync, or coordinated multi-character action. Stay in: ambient motion, camera moves, walking, breathing, atmosphere, particles.
7. Wan struggles with first-person POV — use a reference photo with correct composition
8. NEVER repaint mouths (Wav2Lip/box/face-models paint human mouths on stylized characters = horrible). Dialogue = voice ONLY, over the untouched animation.
9. MANDATORY per-scene step: meticulously analyze EVERY character's mouth in EVERY scene (bin/mouth_sync.py) and match dialogue to it — MATCH THE DENSITY: lots of mouth motion → a full/continuous line; sparse opens → short lines on the opens; no motion → silent. One talker per beat. NEVER leave a moving mouth unvoiced, and never voice a closed mouth. Verify by eye (montage crops) — auto-detect only proposes. Interim until render-time mouth-from-plot is solved.
10. ONE MASTER IMAGE PER CHARACTER — every other view (face, crop, new angle) DERIVES from it via crop/img2img/edit. NEVER independently re-generate a character who has a locked master: LoRAs lock identity but NOT color/texture, so fresh samples drift (Matt rejected drifted Hanks 2026-07-22, "totally different, color and texture"). Dual-LoRA two-shots get color/texture QC against the masters before Matt sees them.
11. MEMORY GATE IS MANDATORY (2026-07-23, after the kernel panic that killed the
   circus_train S6 final mid-render). Every ComfyUI submission auto-passes
   `core.memory_gate()` (wired inside `queue_prompt` — covers make-video, server
   jobs, everything). It blocks on low free / high swap / memory pressure,
   bounces an idle model-cached ComfyUI to reclaim RAM, and REFUSES rather than
   start a shot the machine can't afford. Non-ComfyUI heavy steps (mlx training,
   ffmpeg batches) call `bin/mem-gate "label" || exit 1` first. NEVER set
   SF_MEM_GATE=0. Budget context: Song Forge's resident models own ~45GB of the
   128GB at all times — plan renders inside what's left, prefer --gguf for
   queued/overnight work, and NEVER launch new heavy work (downloads included)
   while a render is swap-grinding (>15 s/step means STOP, not retry).
12. NEVER fake animation by SHAKING / JITTERING / VIBRATING a still. ffmpeg `zoompan` moves the crop window in WHOLE-PIXEL steps, so slow pushes/pans on a still vibrate — that fake shake is BANNED (Matt, 2026-05-27, "hardcode and bake that in"). ALL still-derived camera motion goes through `bin/ken_burns.py` (PIL AFFINE float-coord sampling + BICUBIC) which glides smoothly at any speed. Also NO temporal grain (`noise=allf=t` re-randomizes every frame = shimmer/vibration); use a clean grade + static vignette only. If perfect smoothness can't be guaranteed, hold STATIC or use real i2v. Real animated overlays (drifting particles, petals, light blooms, logo shimmer — see projects/royal_gold/particles.py) are good; shaking a still is not.

13. APPROVED WORK IS THE ONLY WORK THAT SURVIVES (Matt, 2026-07-23). The moment a
   winner is locked (chmod 444 + ledger entry), delete its competing takes,
   drafts, and intermediates THE SAME SESSION — rejected stills, draft clips,
   dud voice takes, review montages, training scraps (keep the recipe dataset +
   the production LoRA copy). A project folder holds locked stills, canon,
   final clips, approved audio, ledger/scripts — nothing else. First sweep of
   circus_train reclaimed 850MB of corpses.

15. LEARN WITHOUT BEING ASKED (Matt, 2026-07-26: "I shouldn't have to tell you
   these special notes to take from here on out"). Every rejection — his, or a gate's —
   becomes a written lesson BEFORE the session ends, not when someone requests it:
   - a shot-level reason goes to the project `shot_lessons.json` (automatic in forge-shot),
   - the generalised version goes to `LESSONS.json` at the repo root with the keywords it
     applies to, so it fires on the next film,
   - a pipeline-level mistake (a gate that lied, a beat written wrong, a scheduling
     bottleneck) goes into THIS file as a numbered rule plus a fix in code,
   - a speed/quality candidate goes into `RENDER_SPEED_RESEARCH.md` with a MEASUREMENT,
     never a vendor claim, and must clear `bin/measure-render` before it ships.
   Standing job, no prompting: hunt for new tools and techniques that streamline renders
   or raise quality, log them the same way, and try them. The bar Matt set is not "it
   renders" — it is a film that survives a public audience. Our AI video posts have been
   downvoted into nothing and removed; assume the audience is hostile to slop and that
   story coherence, clean audio and no morphing are the price of entry.

14. THE PICTURE MUST SHOW THE BEAT — and a machine has to say so, not a human
   eyeball (2026-07-25, the "stick in the door" episode). film_qc checks mouths,
   faces, limb counts and audio timing; ALL of them pass on a shot that depicts
   completely the wrong action. Episode 1 shipped a bear idly poking a plank wall
   with a stick — 91 checks, 86 passed — for the beat "he drives his shoulder
   into a jammed door," and the wrong still had been LOCKED days earlier with a
   ledger note saying it was fine. So:
   - `pipeline-tools/beat_gate.py` is now a MANDATORY gate. It describes each
     frame BLIND (told the intended beat first, a VL model just agrees), then
     rules PASS/FAIL against the beat plus per-shot `must_not` disqualifiers.
     It is wired into `bin/build-episode` preflight as a HARD STOP — a cut is
     never assembled out of shots that don't tell the story.
   - `beats.json` per project carries every shot's intended beat AND a `spine`:
     the beats the film cannot exist without. Per-shot checks cannot catch a beat
     that was never shot at all — Episode 1 had no door ever opening and Ellie
     never on screen, and every shot present passed on its own terms.
   - `bin/forge-shot` builds shots that PROVE themselves: roll seeds → beat gate
     → identity gate vs the character master → lock → animate → re-judge the
     clip → keep only the stretch that holds the beat. A shot that never passes
     is reported UNBUILT, never quietly used.
   - ONE INSTANT IS NOT A VERDICT. The same clip sampled at 1.1s vs 2.7s produced
     opposite rulings — the identical noise that sent seven good lip-sync clips to
     "failed" on 2026-07-23. Every judgement votes over several frames and prints
     each ballot.
   - Sets need canon too. Nothing ever locked the train, so Episode 1 has four
     different ones (sunset steam train, colourful passenger cars, brown plank
     wall, red steel boxcar). beat_gate takes `set_masters` and holds shots to
     them the way rule 10 holds characters.
   - NEVER prompt an impact. "Splinters bursting" became a five-second continuous
     particle spray that reads as drilling, because Wan cannot render collisions
     (rule 6). The bang is felt from inside the dark car — shudder, falling dust,
     a widening crack of light — and never shown.

## MOTION TRANSFER — real footage drives a character (2026-07-25, Matt-approved)

Breaks frozen rule 6's action ceiling. Take ANY video of a real person doing something
physical, trace their skeleton, and render OUR character performing it. Cartwheels,
flips, dances, falls, fights — anything we can find footage of. 100% local, Apple
Silicon, no Blender, no NVIDIA physics sim (NVIDIA's GPC needs rigged 3D + CUDA — wrong
stack for us; evaluated and rejected 2026-07-25).

```bash
# stage 1 — real video → pose track (CPU, seconds). ALWAYS read the QC sheet.
~/AI/ComfyUI/venv/bin/python bin/motion_pose.py source.mp4 pose.mp4 \
    --start 3.3 --dur 8.1 --frames 81
# stage 2 — locked still + pose track → the character doing the move (~14 min)
bin/make-motion-video --ref canon/hank_canon.png --pose pose.mp4 --frames 81 \
    "a cartoon brown bear does a fast athletic cartwheel on green grass"
```

Lessons paid for on the first four takes — do not re-derive:
1. **Q6_K GGUF, never fp16.** The 34GB fp16 Animate weights + Song Forge's resident
   45GB = swap storm at ~110 s/step and macOS kills the render. The 14GB Q6_K quant
   does the same job at ~10 s/step. (Rule 11 memory gate caught the aftermath, not the
   cause.)
2. **Never feed slow-motion at its recorded rate.** A 60fps source resampled 1:1 leaves
   the character hanging inverted; Matt read it as "upside down / backwards."
   `motion_pose.py --frames` resamples the window to natural speed.
3. **Give the move its FULL arc + room.** 49 frames truncated the cartwheel mid-flip —
   "only a half cartwheel, and the clip is so short." 81 frames (5s) covering wind-up →
   apex → landing → recovery is what he approved. Verify the arc on the QC sheet BEFORE
   spending render minutes; the pose sheet is the cheapest gate we have.
4. **Pick LATERAL source motion — the performer must stay at roughly constant
   distance from camera.** Wan scales the character to the skeleton, so a move that
   charges TOWARD camera blows the character up until a shapeless close-up rump fills
   the frame and the action becomes unreadable (action_test shot A, run-and-dive,
   2026-07-25 — dead on arrival). Side-on and stationary is what works: the approved
   cartwheel and the karate strike combo both hold scale across the whole clip. Also
   reject sources with more than one person in frame — the tracker locks onto the
   largest body, which is often a bystander closer to camera.
5. **Identity is NOT locked by this.** The character drifts toward a generic version of
   itself — a per-character video LoRA is the open fix (rule 10 still governs: derive
   from the locked master). Say "Hank-ish, not Hank" out loud; never paper over it.
   Also unfixed: fast-motion smear at draft res, and the face can stay upright while the
   body inverts (`face_video` input unused so far).

**Coverage comes free.** The close-up in the approved action scene is a STATIC ffmpeg
crop of the wide shot, not a second render — the multi-shot rule's crop path (default
rule 1a) applies to motion-transfer clips exactly as it does to stills. Static crops
only; frozen rule 12 still bans zoompan/fake pushes.

**Doug and other quadrupeds cannot take a human skeleton** — they get plain i2v reaction
shots. OPEN BUG (2026-07-25): `make-video --i2v` has no GGUF path, so it loads two 27GB
fp16 MoE stages and killed ComfyUI mid-render during the action scene. Give i2v a GGUF
variant before attempting another quadruped reaction shot.

Approved clips + pose track: `good-clips/motion_transfer_*` (chmod 444) — the bear
cartwheel, the strike combo, and the 3-beat action scene Matt approved 2026-07-25
("yes this really works"). Project scraps in `projects/action_test/`.

## DIALOGUE SCENE-BUILDING WORKFLOW — THE locked way (2026-05-25, Matt-approved)

Build a talking-character scene ONE SCENE AT A TIME. Do NOT do all scenes at once — that is what kept breaking. (Applies to any video with characters speaking on screen, not just cartoons.)

Per scene:
1. Pull a CLEAN full frame, locate each character's mouth precisely (extension crops are easy to get wrong — always verify against the real frame).
2. Montage each character's mouth across the scene; read OPEN vs CLOSED by eye (motion ≠ open; contrast is fooled by fur/collar — the eye is the reliable judge).
3. For each character with mouth motion: place THEIR voice on THEIR open beats, density-matched. One talker per beat — never two voices over one mouth, never a voice over a closed mouth, never a moving mouth left silent.
4. Keep each scene's dialogue INSIDE its clip with a tail gap; verify with `silencedetect` (this is the ONE QC I can do without ears — bleed/carryover into the next scene is a real bug).
5. Show the scene STANDALONE with a descriptive FILENAME label (drawtext filter is NOT installed). Get Matt's explicit OK. LOCK it (save the .mp4). NEVER touch a locked scene again.

Voices (ChatterBox, ~/chatterbox-env, via bin/character_voice.py):
- Doug (dog) = Matt's cloned voice (StoryForge-voices/voice2_matt.wav).
- Hank (bear) = the "other male voice" = ChatterBox BUILT-IN voice, NO clone, torch seed 44. (Cloning a synthetic clip drifts toward Matt's voice — never do it.)
- spare_voiceA/B/C = BACKUPS for FUTURE characters. NEVER use a backup for Hank.
- I cannot hear audio — voice identity must be confirmed by Matt once (or via a working speaker meter); the VoiceEncoder similarity meter is degenerate, don't trust it.

Assembly: build DIALOGUE-ONLY scenes, concat, then lay ONE continuous song over the whole episode (music strings across all scenes; only mouth+voice need per-scene perfection). Intro = LTX-animated scenic title card + PIL text overlays (title + credits) faded in.

## DEFAULT MOVIE-MAKING RULES — GIVENS on every video (Matt, 2026-05-25, never ask)
These are standing direction. Apply them automatically to every film; do not make Matt re-explain.

1. **Dynamic multi-shot coverage.** Every scene is a SEQUENCE of shots, never one static clip, so it reads as fully animated film — the viewer can't tell it came from stills. Cover each beat with varied framings + camera moves that keep returning to the same scene: wide establish → push-in close-up → side/parallax move → pull back wider → return to the action. Source the shots: (a) CROPS of the locked still into close/medium/wide framings (instant, perfectly consistent), (b) i2v CAMERA MOVES (push-in, pull-back, pan, parallax, gentle orbit), (c) FRESHLY GENERATED stills for true new angles (behind/side/above/low) when a beat needs one — on-model via per-character LoRAs so characters stay identical across angles. Assume MAXIMAL coverage by default.
2. **Prompt the mouth motion to the dialogue.** On any shot with a line, write the i2v motion prompt to make that character's mouth move when we want the line ("Doug's mouth opens and closes as he speaks"). Direct mouth motion on purpose so it lands with the dialogue, then lay voice over the untouched result and density-match. NOT repainting mouths (still banned) — we prompt the motion, then voice it. i2v gives open/close jaw motion, not phonetic lip-sync; time it + density-match rather than expecting perfect sync.
3. **Character consistency via LoRAs.** For true new angles / new poses, generate on-model using per-character LoRAs (Doug, Hank, etc.). Build the LoRA the first time a film needs real new angles; reuse forever after.

Full detail: SCENE_BUILDING_METHOD.md.

**Active services on this machine:**
- Story Forge UI: `localhost:17600` · `localhost:17600/story` for narrative mode
- ComfyUI: `localhost:8188`
- Song Forge / ACE-Step: `localhost:8767`

**Mac mini (parallel render node):** `~/.local/bin/mini "<cmd>"` is the channel. Mini has Wan i2v models + LoRAs + VAE + Piper + Real-ESRGAN + training stack all installed. Inference path not yet end-to-end validated.

**Two-week speedup build status:** ~40% plumbed, 0% operationally validated. See SESSION_HANDOFF roadmap for the priority order. Next concrete win: validate mini Wan inference end-to-end (lowest risk, halves all future renders if it works).

## MANDATORY QC STAGE — `pipeline-tools/film_qc.py` (added 2026-07-22, non-negotiable)
No film, scene, or demo is EVER reported to Matt as "checked/verified/done" until this
agent has run and its report is read. Frame-grid spot checks are NOT verification —
that shortcut shipped a broken film on 2026-07-22 ("Every Day" incident).

Run:
```bash
~/.local/mlx-server/bin/python "~/Desktop/PROJECTS/story-forge/pipeline-tools/film_qc.py" FILM.mp4 manifest.json
```
The manifest lists characters, scene time-ranges, and every dialogue line with its
final-timeline timestamp + speaker (schema in the script docstring). The agent uses
**Picture Eyes' Qwen3-VL-32B** (server :8181 if up, else loads in-process) as eyes and
**mlx-whisper** as ears, and checks: (1) correct character's mouth moving at each line,
(2) mouths shut during silence, (3) character identity consistent across scenes,
(4) 1s-interval artifact sweep (morphing/merging/extra limbs), (5) every line audible
at its expected time. Exit 0 = pass, 1 = defects (read the `_qc.md` report), 2 = QC
couldn't run — NEVER treat 2 as a pass.

Report results to Matt as: "film_qc ran N checks: X passed, Y failed — defects: …" and
attach/summarize the report. Anything film_qc cannot judge (phoneme-level lip precision,
taste) is stated as UNCHECKED and left to Matt's eyes — never papered over.

Upgrade path: finish downloading `mlx-community/NVIDIA-Nemotron-3-Nano-Omni-30B-A3B-4bit`
(audio+video jointly) and add a true AV-sync check — the Jul 15 download died at 4KB.

### QC gates — catch failures EARLY, not at the end (added 2026-07-22)
Run QC at three points, cheapest first, so bad work dies before it eats render time:
1. **Input gate (seconds):** before animating, show each still to the VL model (via
   film_qc's vl_ask or Picture Eyes :8181): characters on-model? composition right?
   Whisper-check every voice take for duds. Stills cost ~11s — re-roll freely.
2. **Draft gate (~2-3 min):** before any 15min+ render, generate a cheap draft of the
   same shot (e.g. 97 frames @ 480x256, same prompt/audio) and QC it. Kills bad
   staging/dead mouths/drift at ~1/6 the cost. Imperfect predictor, great filter.
3. **Scene gate (mid-queue):** in multi-scene queues, run film_qc on each scene AS IT
   COMPLETES and STOP the queue on failure — re-roll that scene before rendering the
   next. Never batch-render blind and discover defects at assembly.
Mid-render aborts aren't possible (no intermediate frames exposed); the draft gate is
the substitute.

## Canonical layout (consolidated 2026-07-22 — ONE folder, ONE launcher)
Everything Story Forge lives in THIS folder now. Old scattered paths are symlinks here
(scripts referencing them still work — don't "fix" them back to real folders):
- `voices/`      ← was ~/Desktop/StoryForge-voices (character_voice.py reads via symlink)
- `good-clips/`  ← was ~/Desktop/StoryForge-good-clips
- `fflf-test/`   ← was ~/Desktop/story-forge-fflf-test
- `queue/`       ← was ~/story-forge-queue (divine-tribe-studio config reads via symlink)
- `STORY_FORGE_FORMULA.md` ← was on Desktop
The ONE launcher: **~/Desktop/Story Forge.app** (opens the :17600 web UI). "Divine Tribe
Studio.command" is retired to ~/Desktop/Launchers/Archive. Don't create new Desktop-level
Story Forge folders or launchers.
