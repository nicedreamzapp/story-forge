# film_qc report (jury + spec only) — LAST_SIGNAL_v2c.mp4
**Verdict: FAIL**
Classic checks (lip sync, silence, identity, artifacts, transcript) were NOT run in this mode: they are UNCHECKED, not passed.

## Spec check (no model)
**Spec verdict: FAIL — 3 problem(s)**
- [UNCHECKED] spec-width: 3840 px (no target in manifest spec)
- [UNCHECKED] spec-height: 2160 px (no target in manifest spec)
- [UNCHECKED] spec-fps: 24.000 fps (no target in manifest spec)
- [INFO] spec-duration: 46.625 s
- [FAIL] spec-loudness: -12.2 LUFS integrated (LRA 10.4 LU), target -14.0 +-1.0
- [FAIL] spec-true-peak: -0.8 dBTP, ceiling -1.0
- [FAIL] spec-black-frames: 1 black span(s) >= 0.15s, 1 unintended: 41.00-43.62s
- [PASS] spec-frozen-frames: 1 static span(s) >= 1.0s, 0 unintended

## Harsh jury (two rounds, local Qwen3-VL)
**Jury verdict: FAIL** (needs each dimension >= 6, mean >= 7, no shot under 4) | shots judged: 6 | unchecked: 0 | round 2 ran on 6
Film mean: **6.69**

| dimension | film mean | worst shot |
|---|---|---|
| identity | 8.00 | 7 |
| anatomy | 7.83 | 6 |
| motion | 5.83 | 5 |
| composition | 7.17 | 7 |
| lighting | 6.33 | 6 |
| story | 5.00 | 4 |

Why it failed:
- motion 5.83 < 6
- story 5.00 < 6
- mean 6.69 < 7

### Per shot (final scores; r1 = round 1 where round 2 argued it down)
| shot | t | identity | anatomy | motion | composition | lighting | story | mean |
|---|---|---|---|---|---|---|---|---|
| cockpit | 1.50 | 7 (r1 8) | 6 (r1 7) | 5 (r1 6) | 7 (r1 8) | 6 (r1 7) | 5 (r1 6) | 6.00 |
| crew_walk | 14.25 | 10 | 10 | 7 (r1 8) | 8 (r1 9) | 8 (r1 9) | 7 | 8.33 |
| captain_face | 17.54 | 10 | 10 | 6 | 7 (r1 8) | 6 (r1 7) | 4 (r1 5) | 7.17 |
| welcome | 21.54 | 7 (r1 8) | 7 (r1 8) | 6 (r1 7) | 7 (r1 8) | 6 (r1 7) | 5 (r1 6) | 6.33 |
| yanked | 26.33 | 7 (r1 8) | 7 | 5 (r1 6) | 7 (r1 8) | 6 (r1 7) | 4 (r1 5) | 6.00 |
| sprint | 29.88 | 7 (r1 8) | 7 (r1 8) | 6 (r1 7) | 7 (r1 8) | 6 (r1 7) | 5 (r1 6) | 6.33 |

### Jury reasons (final)
- **cockpit**: identity 7: Captain’s face shows consistent features, but subtle texture aliasing on skin and hair in frame 4 degrades realism; not high-end agency quality. / anatomy 6: Hands grip controls with plausible articulation, but frame 3 shows motion blur on wrist and forearm—reducing anatomical clarity and fidelity. / motion 5: Head and hand movements are jittery between frames; transitions lack smooth interpolation, making motion feel mechanical and unconvincing. / composition 7: Tight cockpit framing is effective, but the repeated identical framing across 4 frames lacks dynamic variation, reducing visual interest and cinematic intent. / lighting 6: Orange rim light from storm is consistent, but frame 4 shows a noticeable color shift in interior glow—indicating unstable lighting keying. / story 5: Context of stress and piloting is implied, but without audio or clear narrative cues, the scene feels detached and lacks emotional or plot-driven clarity.
- **crew_walk**: identity 10: No visible drift or variation in facial features, hair, or costume across all four frames. Consistent with original cast description. / anatomy 10: All limbs, hands, fingers, facial structures, and suit details are correctly proportioned and rendered without warping or AI artifacts. / motion 7: Minimal forward walk with slight head tilt and arm swing; lacks dynamic weight transfer and foot contact variation, appearing stiff and pre-rendered. / composition 8: Strong symmetrical framing and deep field, but obelisk alignment is slightly inconsistent across frames, breaking perfect symmetry and reducing visual cohesion. / lighting 8: Consistent stormy gradient and directional highlights, but subtle shadow falloff on suits varies between frames, suggesting inconsistent light source placement. / story 7: Viewer understands characters exploring alien ruins under threat; context implied by environment and voice-over, but lacks explicit narrative clarity.
- **captain_face**: identity 10: No visible drift or variation in captain’s face, hair, flight suit, or insignia across frames. Perfect consistency. No flaw to downgrade. / anatomy 10: Face, eyes, nose, mouth, and neck are anatomically correct and consistent. No warping or AI artifacts. No flaw to downgrade. / motion 6: Captain’s head and hair show minimal, plausible movement between frames. Slight wind motion in hair is consistent, but no dynamic motion to judge. / composition 7: Tight framing on captain’s face, monoliths create depth, but background elements are slightly soft and lack crispness, reducing high-end polish. / lighting 6: Cool-toned face lighting is consistent, but background fire and lightning cause inconsistent color spill on skin, reducing realism. / story 4: No context, action, or narrative purpose. Captain’s intense focus is isolated; no voice-over or visual cues to ground the moment. Storytelling fails.
- **welcome**: identity 7: Captain’s face shows slight asymmetry in eye alignment and jawline across frames; minor texture flicker in skin pores reduces photorealism. / anatomy 7: Hands not visible, but neck-to-shoulder transition shows subtle warping in one frame; suit seams inconsistently rendered. / motion 6: Minimal head tilt lacks convincing weight; no subtle micro-movements in shoulders or posture to suggest real human presence. / composition 7: Strong leading lines, but monoliths repeat too regularly; lacks natural variation in spacing or erosion, reducing believability. / lighting 6: Teal glow on monoliths is inconsistent in intensity; lightning timing doesn’t sync with ambient light shifts, breaking immersion. / story 5: Alien context is visually opaque; no clear narrative cue beyond storm and monoliths; voice-over essential but not visually supported.
- **yanked**: identity 7: Crewmate is consistent across frames, but facial expression lacks micro-detail and emotional nuance; armor markings are clean but not dynamically lit to feel lived-in. / anatomy 7: Hands and limbs maintain correct structure; fingers slightly blurred in motion, but no warping or AI mush. Armor geometry holds. / motion 5: Lunge lacks physical weight; feet don’t interact with ground, and frame-to-frame transition shows unnatural slide, not grounded momentum. / composition 7: Strong silhouette and depth, but monoliths repeat too regularly, reducing environmental uniqueness; framing feels staged, not discovered. / lighting 6: Directional light on armor is consistent, but bloom and shadow edges vary slightly between frames, suggesting inconsistent render passes. / story 4: No narrative context or emotional anchor; viewer sees a man lunging without purpose, threat, or consequence—pure visual spectacle without meaning.
- **sprint**: identity 7: Captain’s facial expression shifts subtly between frames—frame 1 shows alarm, frame 4 shows panic—lacking consistent emotional continuity for a single sprinting moment. / anatomy 7: Hands and arms show slight positional drift between frames 2 and 3; right hand appears to rotate unnaturally mid-swing, breaking biomechanical plausibility. / motion 6: Arm swing is inconsistent across frames 2-3; left arm appears to lag behind right, disrupting natural running rhythm and suggesting animation keyframe misalignment. / composition 7: Monoliths create strong leading lines, but framing is slightly off-center in frame 4, reducing visual balance and undermining the intended epic scale. / lighting 6: Frame 4 exhibits noticeable bloom around lightning, inconsistent with the rest; suggests post-processing artifact rather than intentional atmospheric effect. / story 5: Fleeting context; no visual cues explain why she’s running or what the monoliths signify. Voice-over is implied but absent, leaving narrative ambiguity unaddressed.

## Jury: three largest defects (machine-readable)
Also written to `/Users/dtribe/Desktop/PROJECTS/story-forge/projects/last_signal/renders_v2_krea_k6/final/LAST_SIGNAL_v2c_jury.defects.json`. Re-render only these shots.

```json
{
 "film": "/Users/dtribe/Desktop/PROJECTS/story-forge/projects/last_signal/renders_v2_krea_k6/final/LAST_SIGNAL_v2c.mp4",
 "defects": [
  {
   "t": 17.719,
   "shot": "captain_face",
   "dimension": "story",
   "score": 4.0,
   "evidence": "cell 1 of 4 in the shot strip (frame @17.72s): Captain stares intensely, no movement, no context, stormy background with monoliths, no narrative cues.",
   "fix": "Add voice-over or subtitle hinting mission urgency; reframe to include hand on weapon or device to imply action."
  },
  {
   "t": 26.448,
   "shot": "yanked",
   "dimension": "story",
   "score": 4.0,
   "evidence": "cell 1 of 4 in the shot strip (frame @26.45s): Man lunges forward in armor on alien landscape, no visible threat, goal, or reaction\u2014pure action without context.",
   "fix": "Add a visible threat (e.g., energy blast, enemy silhouette) in background to ground action in narrative purpose."
  },
  {
   "t": 2.698,
   "shot": "cockpit",
   "dimension": "motion",
   "score": 5.0,
   "evidence": "cell 3 of 4 in the shot strip (frame @2.70s): Head and hand positions shift abruptly; control stick moves unnaturally between frames, creating jerky motion.",
   "fix": "Reframe or re-generate with smoother motion interpolation, ensuring consistent hand and head trajectory across frames."
  }
 ]
}
```

## Poster candidate (last 3 s)
- /Users/dtribe/Desktop/PROJECTS/story-forge/projects/last_signal/renders_v2_krea_k6/final/LAST_SIGNAL_v2c_jury_poster.jpg: @45.88s, judge scored 7/10 of 6, 7, 7, 7, 7, 6