# Known defects: model_review_h3, cut 3 (calm, conversational), written 2026-11-03 ~7:25 PM PST

Cut: `final/model_review_h3.mp4`, 1920x1080 @30, 105.6 s (VO 99.3 s + 6 s end card), -14 LUFS / TP <= -1 dBTP.
Why cut 3: cut 1 "my voice sounds monotone"; cut 2 "way too much emphasis. Hugging Face was sounding way too much."

Watched the full cut start to finish on: 2026-11-03 7:15 PM PST (every 0.5 s frame, 212 frames, against vo/words.json, plus the frame after each of the 26 cuts measured for content; the only later change was line 10's card title being on screen at the cut)

## Voice
- matt2, exaggeration 0.50, cfg 0.45, no pitch shift, EQ +3 dB @180 Hz. Calm script: no exclamation marks, one question.
- Whole-film F0 std-dev: 1.90 st (cut 1) -> 3.77 st (cut 2) -> 2.64 st (cut 3, target 2.6-3.0). 5-95% range 8.10 st.
- All 14 lines whisper-clean, none auto-reworded.
- Proper-noun stress check (tools/stress_check.py, name vs up to 4 neighbour words; flag > +4 dB or > +3 st):
  0 flagged. Hugging Face line 1 -1.2 dB / +0.9 st, line 8 +0.7 dB / -1.1 st; hottest LTX +3.7 dB / +1.8 st and
  "United Kingdom Korea" +3.5 dB / +1.6 st. MiniMax opening line 13 was +3.7 st -> reworded ("If the license on
  MiniMax H3 ever changes") -> -1.1 dB / -0.4 st. Line 4 "H3" reads -26.6 dB: an alignment glitch (CTC put it in a
  70 ms gap, conf 0.7); the line's energy shows no hot spot, so UNCHECKED by the tool, not stressed.

## Gate results (verbatim)
- promo_gates: PASS 9, FAIL 0, WARN 1, UNCHECKED 0. WARN words: "whole-film pass 278/279 (expected 'it's' heard
  'it'); every line heard word for word in its own window of the final mix".
- cue_check PASS; text_readtime PASS; coverage gate OK; final audio gate PASS; film_qc SPEC: PASS.
- audio_check: Verdict PASS, 0 fail, 1 warn (both runs). WARN "music within 6 dB of the voice while speaking at
  [(62.0, -25.5, -19.7), (98.0, -18.2, -16.7)]": stems show music -41.7 / -41.8 dB vs voice -17.4 / -17.0 dB
  there (separation leakage). Under "build": music -41.1 dB, voice -11.9 dB.
- film_qc: Verdict PASS, "Checks run: 127 | passed: 127 | failed: 0"; 14 lip-sync checks SKIPPED (off-screen narrator).
- film_qc jury: "JURY: FAIL (mean 5.75; identity n/a, anatomy n/a, motion 5.0, composition 6.0, lighting 7.0,
  story 5.0)": only l12_manim_b_1 scored; 25 shots UNCHECKED (round 1 gave no parseable scores).
- face_check / continuity_check / design_check: N/A (no faces, no characters, no product).

## Fixed in cut 3
- promo_gates FAIL on "hugging face" vs whisper's "huggingface" and "comfy ui" vs "comfyui": compare_words now treats a
  joined/split name as one word (still catches "a merge" vs "emerge").
- Line 10 cut on "We use" landed on an empty card for 0.37 s (film_qc spec): title now on screen at the cut.
- Line 10 auto-reword "It's MIT, licensed" (chopped) replaced by "It has an MIT license".

## Still true, for Matt's ears
- Voice warmth/taste UNCHECKED by any tool. Music bed unchanged (one candidate). Script/score not approved. Not uploaded.
