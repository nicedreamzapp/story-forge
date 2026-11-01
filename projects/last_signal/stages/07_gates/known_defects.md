# Known defects — THE LAST SIGNAL (2026-10-31)

Date: 2026-10-31, 5:38 PM PT
Watched the full cut start to finish on: 2026-10-31 ~4:48 PM and the face-locked shots again ~5:25 PM, final/The_Last_Signal.mp4 (4K, 46.6 s).
How: I can't play video or hear audio. "Watched" means I went through every 4th frame (6 fps) of the whole cut in order, plus every cut's mid-frame, plus per-half-second loudness of the mix against the beat map. Nobody has listened to the sound yet. Matt's ears come first.

## Gate counts (verbatim)
- film_qc: "Checks run: 53 | passed: 51 | failed: 2" (Verdict: FAIL, 2 defects). Exit 1.
- audio_check: "Verdict: FAIL — 1 fail, 2 warn".
- continuity_check: "Verdict: PASS — 0 violation(s)" (209 rule ballots passed, 0 failed).
- face_check: 6 PASS, 4 FAIL, 4 UNCHECKED shots (Verdict: FAIL).
- design_check: not applicable (no real product, no design.json).
- coverage gate: OK (5 lines, 217 s of footage vs 141 s needed, shooting ratio 5.29:1).
- VL clip gate (stage 04): 10 of 44 takes PASS. The cut uses takes it failed, under a declared exception (stages/04_shots/selects.md).

## FAIL
- film_qc artifact@28.5 s and @40.5 s: both frames are the creature itself (the spiky stone giant, and its huge stone face in the strobe). I looked at both. They show the monster as designed, with no morphing or extra limbs. The judge reads a non-human creature as a deformity. I'm leaving them in, so judge them by eye.
- audio_check balance: "music louder than narration". That check is built for films with narration running all the way through. Here the music hits during long stretches with no words, and the three lines sit in quiet gaps by design. All three lines were re-heard at 100%. I added a 7 dB score dip under "Uncharted." and the cockpit alarm 5 dB quieter. The FAIL stays, because the only way to clear it is to make the score quieter than a whisper.
- face_check: the 4 strobe flashes of the screaming crewmate (37.5, 38.8, 40.1, 40.8 s, 4 to 11 frames each) match his canon face at only 0.15-0.23. That face drifts from the crewmate in the walk shot. I tested a face-lock on one flash and it made the glowing eyes flicker, so I left them alone.

## WARN
- audio_check: the score has hard jumps at 7.1 s and 25.4 s. Those are my arrangement joins, placed on the arrival cut and the ramp cut, with designed hits (braam, boom, sub kick) on top. Please listen at those two moments.
- audio_check: music is within 6 dB of a voice in some windows. The demucs "voice" stem picks up SFX in the arrival and the strobe. All three real lines were heard at 100%.

## Seen by eye, no gate checks this
- The captain was a different-looking woman in several shots. The walk, welcome and both sprint shots are now face-locked to her canon face (inswapper). Locked faces are slightly softer than the sharp SeedVR2 detail around them. I saw no pops at 6 fps, but phoneme-level and frame-by-frame smoothness is UNCHECKED. The cockpit shots are profile views, so they couldn't be checked and weren't locked. She may not match there.
- The handwriting beat doesn't read. The carving under her hand is swirls, not visible handwriting. The "it's her own handwriting" chill now rests on "Welcome back, Captain" and "I've never been here".
- c11 yanked: he looks flung sideways rather than clearly dragged backward (a dark shape passes over him). The gate said the same.
- c14 boots: the glowing cracks could read as splashing water.
- c10 second sun: reads as one orange sun plus a white flare. The "second sun" isn't obvious.
- The creature isn't consistent. The rising giant (c13) has a single vertical line of eyes. The strobe close-up (R19) has two big eyes plus the eye line.
- The crewmate's eyes glow teal in the scream shots. That wasn't scripted. It reads as possession.
- c15 grab: the stone "hands" are rock formations. The ship tilting reads as caught, but it's not obviously a giant hand closing.
- Hook: the asteroid ship (previs draft) mostly holds size instead of charging hard at camera. In the dive, the ship is small in frame.
- The monolith reveal is close to a held frame, with fog and lightning but no real "rocket through fog" camera move.
- Resolution: shots held 0.9 s or longer got SeedVR2-3B at 720p (2x real restoration), then lanczos to 4K. Sub-second ramp and strobe cuts are lanczos plus light sharpening only. It's not native 4K detail. True 4K SeedVR2 measured about 6x slower on this M5 (lessons logged).
- The arrival was upscaled in 2 chunks, after a 3-batch run broke twice. There could be a tiny temporal seam at frame 57 of that shot (about 9.2 s into the film). Not visible at 6 fps, UNCHECKED frame by frame.
- Grain uses bin/grade's temporal noise (strength 0.12, light). Frozen rule 12 bans temporal grain on stills. This is moving footage, but check for shimmer in the dark areas.
- RIFE was not used. Every source is native 24 fps and nothing is retimed, so there was nothing for it to fix.
- Voices: the captain is the ruby voice (EARS dataset, CC-NC licence, non-commercial). If the YouTube video is monetized, that reference needs replacing first. The computer (voiceA) and the planet (voiceB) come from the spare pool.
- Scream SFX (MMAudio) under the strobe: pyin found no pitch in it, so it may sound more like a roar than a scream. UNCHECKED by ear.
- 41.0-41.1 s: a -40 dB tail of the strobe hits leaks into the first ~0.1 s of the black. The rest of that second is true silence.

## UNCHECKED
- Everything about how it sounds: mix balance, score choice in context, surround placement (the arrival sweep front to rear, the planet voice from all speakers), LFE weight. Measured only.
- Lip sync: none needed, all three lines are voice-over by design (film_qc skipped all 3, as intended).
- Taste, pacing, whether the trailer lands. Matt's call.
