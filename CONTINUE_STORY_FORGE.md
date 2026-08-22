# CONTINUE — Story Forge program (handoff 2026-05-25)

You are picking up a long build in a fresh session. Read this, then read the linked docs, then continue.

## What Story Forge is
A robust **100% LOCAL generative VIDEO system** for making video of ANY kind — narrated explainers, ambient pieces, promos, documentary cuts, sagas, and yes cartoons — in any style, from one readable script. It is NOT a cartoon studio. Cartoons are just the case it works decently for right now ("Hank & Doug" was the first proof, because talking characters are the hardest case). The goal is the SYSTEM as a whole: harden it so any video is easy to spin up — drop in stills, cast voices, write a `.sf`, get a finished piece.

## How we build (the ethos)
- Build off what we KNOW works — perfect the proven win and extend from it; never restart from scratch or chase unproven paths.
- This is OUR environment running OUR language (`.sf`) — we don't depend on slow, old, generic systems that don't fit our machines.
- Built FOR our hardware (M5 Max 128GB + mini, Apple-Silicon/MPS-native, 100% local) and squeezing full advantage out of it at all times.

## Status
- We are MANY phases deep (engine, DSL, render-route, distillation, the locked method, first pilot all done) — this is NOT phase 1. What's left is hardening into the general video system.
- **Log everything, never repeat it:** every build and every mistake lives in these docs (this file + SESSION_HANDOFF.md + SCENE_BUILDING_METHOD.md + STORY_FORGE_BUILD.html). Read the hard rules below before acting so we never re-learn anything the hard way.
- ✅ First pilot SHIPPED: `~/Desktop/StoryForge-good-clips/HANK_AND_DOUG__COMPLETE.mp4` (animated logo intro → 3 scenes → one song). Hank & Doug is now PAUSED — do not keep working it unless asked.
- ✅ Engine: 1-step distillation (LPIPS 0.052, merged), `.sf` DSL, render-route (Wan vs LTX), ChatterBox voices, `mouth_sync`.
- ✅ The dialogue scene-building method is LOCKED. Tools committed to GitHub (story-forge PR #3).

## READ THESE FIRST
1. `~/Desktop/PROJECTS/story-forge/SCENE_BUILDING_METHOD.md` — THE locked way to build a talking scene.
2. `~/Desktop/PROJECTS/story-forge/STORY_FORGE_BUILD.html` — current build status + lessons + voice roster.
3. `~/Desktop/PROJECTS/AI/videopipe/CLAUDE.md` — pipeline rules (auto-loads if you start there).
4. `~/Desktop/PROJECTS/story-forge/SESSION_HANDOFF.md` — older deep state.

## Hard rules (do not relearn these the hard way)
- **NEVER repaint mouths** (Wav2Lip/face-models). Dialogue = voice over the untouched animation.
- **One scene at a time → Matt OKs → lock it → never touch it again.** Don't rebuild locked scenes.
- **Agent self-verifies every render** (pull frames; confirm mouths/voices/logo/text) BEFORE Matt sees it. Matt is NEVER the QC tester.
- You **cannot hear audio**; the ChatterBox voice-similarity meter is degenerate. Voice identity = Matt confirms once, then lock.
- **M5 = all heavy work/rendering** (128GB). **Mini = agents only.** 100% local — never cloud inference.
- Match dialogue DENSITY to mouth motion; one talker per beat; `silencedetect` to confirm no cross-scene voice bleed.

## Voices (ChatterBox, ~/chatterbox-env, via bin/character_voice.py)
- Doug = Matt's cloned voice (StoryForge-voices/voice2_matt.wav). Hank = built-in "other male voice" (no clone, seed 44).
- spare_voiceA/B/C = backups for new characters.

## Where to take the SYSTEM next (Matt's direction)
Harden it into a general video system so ANY video is easy (any subject, any format, any style):
1. ✅ DONE (2026-05-25) — `story-new <name> [--style …] [--format …]` scaffolds a runnable project (stills/ + voices/ + starter `.sf` + README) for any project type. `bin/story-new`.
2. ✅ DONE (2026-05-25) — Style + format packs in `story_forge/packs.py` (7 looks: pixar-3d/flat-2d/photoreal/watercolor/anime/claymation/noir; 5 shapes: film/reel/square/narrated-doc/cinematic). Declared as `film` attrs `style=`/`format=`; style rides the Flux prompt, format rides the dimensions. No style/format = byte-identical to before.
3. ✅ DONE (2026-05-25) — Web UI surfacing (port 17600): live Styles & Formats picker via `/api/packs`, plus one-click example scripts `multi_voice.sf`, `sfx_demo.sf`, `styled_reel.sf`. 49 unit tests green; validated with a real 1-scene render.
4. TODO — Update the public page: nicedreamzwholesale.com/software/story-forge.
5. TODO — Render speed: validate mini parallel render, wire LTX into render-route, optional 2-step Wan distill.
6. R&D: render-time "mouths move to the plot" — the real fix that retires manual mouth-matching for the character-dialogue case.

## Key paths
- Pipeline: `~/Desktop/PROJECTS/AI/videopipe/` (bin/character_voice.py, mouth_sync.py, qc_movie.py, render-route, story_forge/ DSL, server.py :17600)
- Distill: `~/AI/distill/render_distill.py` · ComfyUI :8188 (M5) · ChatterBox: `~/chatterbox-env/bin/python`
- Voices: `~/Desktop/StoryForge-voices/` · Good clips: `~/Desktop/StoryForge-good-clips/`
