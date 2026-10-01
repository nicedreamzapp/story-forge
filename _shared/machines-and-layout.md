# Machines, services, layout, narrator voice (moved verbatim from CLAUDE.md, 2026-10-01)

**Active services on this machine:**
- Story Forge UI: `localhost:17600` · `localhost:17600/story` for narrative mode
- ComfyUI: `localhost:8188`
- Song Forge / ACE-Step: `localhost:8767`

**Mac mini (parallel render node):** `~/.local/bin/mini "<cmd>"` is the channel. Mini has Wan i2v models + LoRAs + VAE + Piper + Real-ESRGAN + training stack all installed. Inference path not yet end-to-end validated.

**Two-week speedup build status:** ~40% plumbed, 0% operationally validated. See SESSION_HANDOFF roadmap for the priority order. Next concrete win: validate mini Wan inference end-to-end (lowest risk, halves all future renders if it works).

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

## 🔊 NARRATION VOICE CHANGE — 2026-08-07
Ashley (Piper LibriTTS speaker 0) is RETIRED. The narrator voice is now **Kokoro-82M "Heart" (`af_heart`)** for ALL future videos and narration. `story_pipeline.py` / `story_forge/run.py` `PIPER` constants now point at `~/.local/bin/kokoro-piper-shim` (piper-compatible CLI, renders Kokoro Heart). `speak` / `speak-heart` CLIs also render Heart. Matt's cloned voice is unchanged as the second voice. Do NOT use Piper Ashley in new work.
