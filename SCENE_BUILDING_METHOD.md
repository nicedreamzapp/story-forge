# Story Forge — Dialogue Scene-Building Method (LOCKED 2026-05-25)

Story Forge is a general local video system; this doc covers ONE case within it: scenes where characters talk on screen (the hardest case — cartoons are just where we proved it). Other video types (narrated, ambient, promo) use the same engine without most of these steps.

The hard-won, Matt-approved way to build a talking-character scene. Follow this exactly.
Tools live in `~/Desktop/PROJECTS/AI/videopipe/bin/` (also see that dir's CLAUDE.md).

## Default: dynamic multi-shot coverage (a GIVEN — never ask, always do)
Every scene is built as a SEQUENCE of shots, never a single static clip, so the result reads as fully animated film — the viewer can't tell it was built from stills. This is Matt's standing direction (2026-05-25): assume MAXIMAL dynamic coverage on every video. He never has to request it — it's simply how we make movies.

Cover each beat with varied framings + camera moves that keep returning to the same scene. A typical coverage pass:
- wide establish → push-in to a close-up → a side / parallax move → pull back to a wider angle → return to the action.

Source the shots, in order of preference:
1. **Crops** of the locked still into different framings (close / medium / wide) — instant, perfectly consistent, no new art.
2. **i2v camera moves** (push-in, pull-back, slow pan, parallax, gentle orbit) — adds motion and apparent angle change.
3. **Freshly generated stills** for TRUE new angles (from behind / side / above / low) when a beat needs one — generated on-model via the per-character **LoRAs** so Doug/Hank/etc. stay identical across angles. (LoRA training is the unlock for unlimited consistent angles; build it when a film first needs real new angles.)

The dialogue rules below still apply per shot: voice only over untouched animation, density-matched, one talker per beat.

### Prompt the mouth motion to the dialogue (don't just react to it) — also a GIVEN
For any shot that carries a line, WRITE THE i2v MOTION PROMPT so that character's mouth moves exactly when we want the line — e.g. "Doug's mouth opens and closes as he speaks," "the bear's muzzle moves gently as if talking." Direct the mouth movement on purpose so it lands where the dialogue lands; then lay the voice over those open beats. We are NOT repainting mouths (still banned) — we PROMPT the i2v to generate the mouth motion, then place voice over the untouched result. i2v gives believable open/close jaw motion, not phonetic lip-sync, so density-match the line to that motion (rule 3 below) rather than expecting perfect sync. Standing direction (Matt, 2026-05-25): prompt for mouth motion at the intended dialogue moments on every talking shot, automatically.

## Golden rules
1. **One scene at a time.** Perfect a scene's mouth+voice, get Matt's OK, LOCK it (save the .mp4), then move on. Never build all scenes at once — that is what kept breaking.
2. **Never touch a locked scene.** Once approved it is frozen. Don't regenerate it for "consistency" or anything else.
3. **NEVER repaint mouths.** Wav2Lip / box / face-models paint human mouths onto stylized characters and look horrible. Dialogue is voice ONLY, laid over the untouched animation.
4. **I self-verify before showing Matt.** Pull a frame, confirm the mouths/voices/logo/text are actually right. Matt is NEVER the QC tester.

## Per-scene workflow
1. Pull a CLEAN full frame; locate each character's mouth precisely (crop coords are easy to get wrong — verify against the real frame).
2. Montage each character's mouth across the scene; judge OPEN vs CLOSED **by eye** (motion ≠ open; contrast is fooled by fur/collar — the eye is the reliable judge).
3. Place each character's voice on THEIR open beats, **density-matched**: lots of mouth motion → a full/continuous line; sparse opens → short lines on the opens; closed → silent. **One talker per beat.** Never voice a closed mouth; never leave a moving mouth silent.
4. Keep each scene's dialogue INSIDE its clip with a tail gap; verify with `silencedetect` (bleed/carryover into the next scene is a real bug — and it's the one audio check I can do without ears).
5. Show the scene STANDALONE with a descriptive FILENAME label (the drawtext filter is NOT installed; filenames show in the player title bar). Get Matt's explicit OK → LOCK.

## Voices (ChatterBox — `~/chatterbox-env`, via `bin/character_voice.py`)
- **Doug (dog) = Matt's cloned voice** (`StoryForge-voices/voice2_matt.wav`).
- **Hank (bear) = the "other male voice"** = ChatterBox BUILT-IN voice, NO clone, `torch.manual_seed(44)`. Do NOT clone a synthetic clip for Hank — it drifts toward Matt's voice and collides with Doug.
- **spare_voiceA/B/C = BACKUPS for future characters.** Never use a backup for Hank.
- I cannot hear audio. Voice identity must be confirmed by Matt once; the ChatterBox VoiceEncoder similarity meter is degenerate — don't trust it.

## Assembly
- Build DIALOGUE-ONLY scenes, concat, then lay **ONE continuous song** over the whole episode. Music strings across all scenes and can vary; only mouth+voice need per-scene perfection.
- **Intro** = an LTX-animated (or Ken-Burns-zoomed) scenic title card + PIL text overlays (logo + credits) composited and faded/popped in. Always verify the logo+credits actually render in a frame before showing.

## Why this exists
Reliable per-character mouth attribution in multi-character scenes is fragile (the auto-detectors confound head motion / fur with mouth-opens). Until a render-time "mouths move to the plot" approach exists, the eye-verified, one-scene-at-a-time method above is THE way.
