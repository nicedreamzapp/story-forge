# Known defects — teaser fast cut (2026-11-13 8:47 PM), final/the_things_we_remember_teaser_fast.mp4
Reviewed by frame sheets + gate reports (not a real-time watch with sound).
1. s06 fork never moves. LTX seed 61 left it still; the one re-roll (seed 62) had a family member's hand lift it, so it was rejected. Fallback used: the push-in on the empty chair. Fix in the hybrid pass (K6) or a code-animated fork.
2. s05 the glass never visibly drops, and the "head turns before it lands" beat doesn't read. The figure walked into the light later in the take, so only the first 66 frames are used, slowed to 0.7x. The shatter is off-screen sound at 16.1 s.
3. s03 the man in the photo has a blank, featureless face (an AI artifact kept on purpose because it reads as horror). film_qc flagged it 4 times as an artifact (8.5 to 11.5 s).
4. s11 the reflection man sharpened in LTX; a moving code blur keeps him soft, and only the first 104 frames are used.
5. s09 era photos: same face via inswapper, but faces are ~0.4 s each; photos 3, 5 and 6 show him twice (doppelgänger), kept.
6. Credit card text: 44 characters for ~3.5 s fully visible; just under the 4.4 s read-time rule (text_readtime_check had no texts.json, so it did not check).
UNCHECKED: phoneme-level lip precision on Lily (s07), voice taste/casting (VoiceDesign, new cast), score taste, the mix by ear, face_check (no canon portraits made for a fast cut).

# Best cut v1 (2026-11-14 00:55), final/the_things_we_remember_teaser_best_v1.mp4
Engine: K6 refused by forge_guard at 21:34 -> LTX-2.5 --hq --low-ram 1024x576 on s01 s04 s08 s11 (+ s07 a2v), then SeedVR2 (s01, s08, 720p) / LTX Refine-Details (s04, s07, s11, 1088p), lanczos to 1080p.
s07 uses the FAST a2v take (HQ a2v failed film_qc lip-sync 3/7); the HQ s07 stays as coverage. s05/s06 remain the code builds.
s11 Rememberer: tracked mask (face track, quadratic-smoothed), blur 26 px, x0.35 (~1.5 stops), half desaturated, cooler; checked on crops at 33.2/35.4/37.6 s: face unreadable, Claire untouched.
Identity DRIFT on v2 was the film_qc sheet sampling a photo insert, Lily and the title card (scene midpoints); no shot drifted. face_check against canon stills: s04 0.77, s07 0.67, s11 0.55, all PASS. Identity passed on this cut.

# Trailer 90 s FAST (2026-11-14 ~3:05 AM), final/the_things_we_remember_trailer_90_fast.mp4 — link in final/link_trailer_90_fast.txt
film_qc: 105 pass, 6 fail, 9 skip. All 6 fails are on APPROVED teaser shots: s03 photo man's blank face x4 (kept on purpose,
approved 11/14), s05 doorway figure and s08 boy under the quilt ("no animated character", by design: the Rememberer and Daniel
are never shown clearly). Lip-sync PASS on L01 (s07), L02 (t11, 72%), L03 (t14, 100%). continuity_check PASS (0 violations).
Read-time PASS. Fixed before publish: t03 Lily's body morphed rounding the banister (cut at 1.9 s, then a held empty-stairs frame);
t17 hallway figure blur now tracks the camera creep. t10 quilt pull: first 1.6 s of the take, then the empty-bed still (LTX's
quilt never read as "empty"). t03 re-roll used (seed 1311); first take deleted. t15 whip pan built in code, not LTX.
UNCHECKED: voice taste on the 5 new VoiceDesign lines (Tom and Lily-at-3 are new voices), mix by ear, phoneme precision.

# Trailer 90 s BEST (2026-11-14 9:11 AM), final/the_things_we_remember_trailer_90_best.mp4 — final/link_trailer_90_best.txt
K6 not run: the guard budget is ~50 GB < the 72 GB K6 lease (lease never shrunk). LTX-2.5 --hq --low-ram on 5 heroes; t01 HQ
(car reverses toward camera) and t04 HQ (push ends in a soft blur) REJECTED and deleted, their fast takes stay. Kept HQ:
t13, t18, t14 (a2v, lip-sync 67% PASS), upscaled to 1080p with SeedVR2 (auto-route: no face over 5%).
film_qc: 105 pass, 6 fail, 9 skip — the same 6 approved-teaser-shot flags as the fast cut. continuity PASS, read-time PASS.
Late by ~3 h vs the 6:00 AM target: a ~4 h session stall, then my cleanup deleted a finished upscale (re-run 45 min).

# Short 3 min FAST (2026-11-14 11:55 AM), final/the_things_we_remember_short_3min_fast.mp4 — final/link_short_3min_fast.txt
film_qc: 199 pass, 8 fail, 12 skip. Fails: identity DRIFT (sheet sampling), s03 photo man x4 (approved), t03e stairs still
(doll on the landing chair read as a child; approved trailer still), sh11 drawer photo "worn" (code insert, face-up not face-down),
t20 flash "blurry" (by design). Lip-sync 4/4 Lily lines PASS. continuity PASS. Read-time PASS after MONTHS LATER 3.0 -> 3.9 s.
All 19 new clips first-take. sh31 camera drifts onto Lily (Claire's line is off-camera). UNCHECKED: voices/mix by ear.
Lesson: film_qc wants a 32 GB lease; with the old 50 GB budget it starved behind an LTX --hq render for ~25 min until the
best-pass driver was SIGSTOPped. Never start a render driver that overlaps a cut's film_qc without checking the budget.
