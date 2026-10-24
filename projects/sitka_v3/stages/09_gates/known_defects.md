# Known defects — sitka_v3, v4 cut (2026-10-23, 19:50 cut)

v4 = Matt's approved look test 3: realistic MPFB wearer, CMU mocap, relaxed arms, elbow clearance solve,
black exo materials. All 29 v4 shots encoded into footage/ (old v3 files kept in footage_v3/), same EDL.
The old 10/22 film was deleted after this cut passed its gates.

## Gate counts (verbatim)
- promo_gates: `[gates] PASS 9  FAIL 0  WARN 0  UNCHECKED 0`
  words 237/237 matched on the final mix; word timing median 20 ms over 236 words;
  loudness -16.0 LUFS integrated, true peak -1.5 dBFS, LRA 2.7; voice over ducked music 15.4 dB;
  slam +200 ms after "us"; sting -17.6 dBFS; end card on screen; design: all 31 used shots passed.
- cue_check: exit 0. callout_check: 2/2 PASS (lift tendon; one small motor, after re-tracking the tip onto
  the v4 motor cap: the v3 track had drifted onto the housing bezel and FAILED first).
- film_qc: `Checks run: 112 | passed: 109 | failed: 3` (verdict FAIL — 3 defect(s)).
  The 3 fails are artifact@32.5s, @33.5s (lean back, from behind) and @36.5s (stoop lift, from behind).
  Re-asked the same prompt for the full answers: all three say "two arms and two legs, no extra or missing
  limbs, no merged bodies, proportions correct"; they fail only because the answer did not start with
  "clean". The face cannot be judged in those frames (seen from behind) = UNCHECKED.
  11 lipsync checks SKIPPED by design (off-screen narrator; no on-screen speech in a promo).

## Design check overrides (by eye, recorded in manifest.json checks.design_by_eye)
The VL design judge failed 3 v4 selects at 3/3 and again at 5 votes; I checked each by eye at full res:
- n07_run_low ("an orange rod connecting the two legs"): that is the real running band, CAD part
  `running_band` (KINETICS.md T6, shoe-to-shoe interleg band, RUN only). Correct.
- v1_s20_walk_bands and n05_lean_front ("pole in front of the knee or shin"): the strut is folded along the
  outer thigh (walk) / drops from under the hip, outside the leg, to the ground (seated). Correct per design.

## Frame review (every shot at in/mid/out, 102 frames at 640 px + full-res zooms, plus the 26 gate strips)
Not a real-time playback: motion smoothness is covered by the v4 rig gates (foot slide p95 < 1 mm,
0 collision samples on the used shots) and the film_qc 1 s artifact sweep, not by my eyes.
- Hands/elbows: relaxed and clear of the exo in every walk/stand shot. n05_lean_front: hands rest on the
  thigh shells and the rig gate logs arm clearance down to -7.9 mm (fingertips sink a few mm into the shell,
  18 of 67 frames); at film size it reads as a hand resting on the thigh. Minor, left in.
- n06_lift_front end (about 37.3 s): after the lift his right hand goes to the back of his hip, a slightly odd
  mocap carry pose, visible ~0.3 s. Minor.
- Feet: planted on the ground / stairs, no visible slide or sinking; run_low shows flight phase (correct).
- Ghost walk (line 3) is a deliberate x-ray look.
- v1 close-ups (knee macro, clutch walk, knee sit close) still render the wearer's legs in the v4 materials.

## Weak spots (honest)
- The printer shot (n10_print_close) and the parts-list scroll are still the 10/22 v3 files (no v4 version).
- Kinetic slams (STRONG/LIGHT/STAIRS/HILLS) have no hit SFX of their own.
- Music: Body Movin' "Star Jumps Coach" instrumental; Matt has not picked the score by ear yet.
