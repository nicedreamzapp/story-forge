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

**Active services on this machine:**
- Story Forge UI: `localhost:17600` · `localhost:17600/story` for narrative mode
- ComfyUI: `localhost:8188`
- Song Forge / ACE-Step: `localhost:8767`

**Mac mini (parallel render node):** `~/.local/bin/mini "<cmd>"` is the channel. Mini has Wan i2v models + LoRAs + VAE + Piper + Real-ESRGAN + training stack all installed. Inference path not yet end-to-end validated.

**Two-week speedup build status:** ~40% plumbed, 0% operationally validated. See SESSION_HANDOFF roadmap for the priority order. Next concrete win: validate mini Wan inference end-to-end (lowest risk, halves all future renders if it works).
