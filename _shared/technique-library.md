# Technique library

Tricks collected from outside work (11/02 X posts and repos). Read this when planning any new film,
promo or explainer, and pick what fits; nothing here is mandatory until it becomes a tool or a gate.
Sources: lemo-opuscar, pdoom-video, mg-styles-15, ClaudeAnimationBase (all MIT), a "motion
engineering" article, and an infographic-explainer prompt. Ideas only; never copy their art or prompts.

## Studio shape (plan before rendering)
- Director brief first: one sentence the viewer should remember, audience, length, formats, the real
  assets, Keep/Avoid lists, "never invent product screens or numbers". Facts about the product are
  separate from choices about the film; the model may invent camera moves, never the product.
- Reference breakdown before style: measure palette (actual hex), type, where the eye goes first, average
  shot length, motion feel (snap/glide/overshoot/hold), texture, plus a DO NOT COPY list
  (`reference_analyze.py`).
- Shot list as states, not effects: each beat has an entry state, an exit state and a reason to exist.
  If you can't say why shot 4 exists, cut it. For UI: SEARCH -> RESULT -> DETAIL -> ACTION -> CONFIRM.
- Gates for long runs: references+assets → style guide+shot list → stills → rough cut+contact sheet →
  fix the 3 worst defects → audio/formats/deliverables. A missing real asset is a blocker, not an
  invitation to draw a fake. An unclear reference gets a test frame, not 900 wrong frames.
- Every project keeps brief, style guide, shot list, assets, source, reviews and outputs as files, so the
  next run resumes from a gate instead of a chat.

## Timing and pacing
- Model the viewer: list the reads per shot, one read at a time, hold after fast action (in
  `script-writing.md`, linted by `spec_lint.py`).
- Emotion changes go anticipation → squint → take → overshoot, never a snap.
- Explainer cadence: new scene every 2–4 s, hard cut on every sentence that changes the idea, a fast wipe
  (0.2 s in, 0.2 s out) between big sections, camera always drifting 2–4% or panning, no still frame over 1 s.
- Every cut, sign and gesture starts on a real word (`ctc_align.py` word times). Repeated words are found
  by occurrence number (the third "and"), or cuts land on the wrong line.
- Cut pauses over 0.24 s down to 0.16 s, then atempo to the target length.
- Cuts and story turns snap to the music's beat grid (`audio_analyze.py`, `edit_to_words.py --beat-snap`).
  Watch for half-time tempo reads on fast tracks.
- On-screen text stays up for chars/15 s + 1.5 s; subtitles ≤17 cps (`text_readtime_check.py`).

## Code-rendered motion (titles, explainers, UI, diagrams)
- Every frame is a pure function of time: `seek(t)`, READY, END, and an EV list of sound-event times.
  No hidden clock, no unseeded randomness, so frame 240 renders without playing 0–239 and a fix is one number.
- One timeline drives picture, voice, score, foley and subtitles; sound cues sit on the same timestamps
  as the picture. Test: listen with eyes closed; if it has no shape, the sound isn't done.
- Motion rules per object class: micro UI snaps, panels settle, camera eases slowly, headlines arrive
  fast and hold, mascots play. Not everything springs, or nothing feels precise.
- Things arrive with a spring, a squash or a puff, never a plain fade.
- Typed text: letters arrive about 1.45x big and offset right, settling in ~0.18 s, at 26–34 letters/s.
- A red X drawn in two quick strokes over every wrong idea; date cards for every date.
- Adaptive motion blur: more sub-frames only where tiles move (pdoom `render.ts`); 6 sub-frames over
  half a frame is a good flat default.
- Variable-font width animation for karaoke/lyric text.
- Linework "boil": reseed hand-drawn lines ~12×/s so flat art feels alive.

## Flat character animation without a video model
- Draw characters who gesture a lot WITHOUT ARMS (round shoulder sockets) and draw the arms in code:
  two-bone IK tubes with mitten hands that open, point or make a fist. Gestures are exact and never drift.
- Everyone else is drawn in the exact pose their scene needs (side at a desk, walking, from behind).
- Split heads at the neck, drawing hands, and walkers' legs below the hem; inpaint each hole from the
  body's own colours so a turning part never shows a gap.
- Idle life: blink 0.14 s every 2.7–4.2 s, head nods ±0.035 rad, drawing hands scribble ±8 px.
  No character stands still.
- Walk cycle: thighs ±0.42 rad, knee bend 0.75·cos² on the swing, hips drop so the planted foot stays
  down, body moves 1.5 leg lengths per cycle so feet never slide.
- Empty background plates (no people, blank signs and screens); write text on the plate's own blank
  sign by measuring its rectangle, never on a card floating over the art. Clamp the camera to the plate edges.

## Cutouts on green
- Character sheets on solid #00B140 with nothing green on anyone.
- Key = pixels with G − max(R,B) > 40, within 110 of the median green, AND connected to the border.
  A floating flood fill leaks into dark clothes on outline-free art.
- 2 px soft alpha edge, clamp G to max(R,B)+6 inside it (despill).

## Voice
- Cast by measurement: median pitch (pyin) + MFCC timbre against a clip of the narrator you want
  (candidate upgrade for `character_voice.py`). Voices still must match the character.

## QC and finishing
- Contact sheet before any full render: one frame per beat plus a strip around the fastest transitions.
  Check readable at phone size, safe areas, real assets, consistent type/colour, no ugly mid-transition
  frames, cuts and sound together, a real hook in the first 2 s, a last frame strong enough to be a poster.
- Critic judges only rendered frames, scores harshly (most first renders are 5–7/10), names the 3 biggest
  defects with timestamp + evidence + local fix, then only those shots re-render (`film_qc.py --jury`).
- Scan the render for single-frame jumps and confirm each is a planned cut.
- Colour-match every shot to one reference (`color_match.py`, MKL at 0.6).
- Real footage only: stabilize (`stabilize.py`), cut dead air (`cut_dead_air.py`).
- Final audio: two-pass loudnorm to −14 LUFS, true peak ≤ −1 dBTP, reject truncated audio
  (`final_audio_gate.py`). Music bed sits 10–11 dB under the voice.
- 9:16 and 1:1 are their own compositions from the same story and assets (bigger type, fewer elements,
  vertical hierarchy), never a crop or blurred pad. Each variant gets its own contact sheet.
- Every deliverable ships a poster frame.

## Open-source building blocks worth knowing
PySceneDetect (shots), Auto-Editor (dead air), vid.stab (stabilize), color-matcher, rembg (background
removal), RIFE (slow-mo), Demucs (stems), librosa (beats), MMS_FA/wav2vec2 (forced alignment),
Playwright+Chromium (render HTML/canvas films), Remotion / HyperFrames (HTML video frameworks).
