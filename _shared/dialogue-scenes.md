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
