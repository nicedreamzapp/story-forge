# Known defects — sitka_demo (promo-mode test fixture)

Date: 2026-10-22
Cut: final/sitka_demo.mp4, 23.80 s, ffmpeg renderer (the Remotion renderer was also rendered once from the same EDL and checked by frames).

NOT a full watch: the building agent reviewed every frame strip and a 1-frame-per-second sheet of the whole
cut, and relied on whisper for the audio. Nobody has listened to it start to finish, so READY FOR MATT stays no
until someone does and writes that line here.

## Gate counts (verbatim)
promo_gates: PASS 8, FAIL 0, WARN 1, UNCHECKED 0. cue_check: 8 cues hit, 0 structural problems.
callout_check: 1/1 PASS. design_check: 11 pass, 0 fail (l02_bl_sit_push failed twice before the ground fix), 8 unchecked
(macro and parts shots with no person visible; none of them in the cut).

## WARN
- words: whisper's whole-film pass hears "light pull" for "light pole" (line 2); the line's own window of the same
  final mix, the clean VO stem, VO+music and VO+fx all hear "pole". Listen for it.

## Seen in frames, no gate checks this
- The Manim card (6.1–10.7 s) covers the right half of the frame while the seated wearer is centred; the hand-made
  Sitka shots framed the subject left for this. Blender shots meant to carry a card need the subject off-centre.
- selects.json and cues.json are promo_draft DRAFTS (no editorial why), which is fine for a fixture, not for a release.

## UNCHECKED
- The score was not picked by ear (bed_a from the Sitka promo, downbeat set by promo.json music.hit).
