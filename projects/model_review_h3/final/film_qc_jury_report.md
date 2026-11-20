# film_qc report (jury + spec only) — model_review_h3.mp4
**Verdict: FAIL**
Classic checks (lip sync, silence, identity, artifacts, transcript) were NOT run in this mode: they are UNCHECKED, not passed.

## Spec check (no model)
**Spec verdict: PASS**
- [PASS] spec-width: 1920 px, manifest wants 1920
- [PASS] spec-height: 1080 px, manifest wants 1080
- [PASS] spec-fps: 30.000 fps, manifest wants 30
- [INFO] spec-duration: 105.600 s
- [PASS] spec-loudness: -14.0 LUFS integrated (LRA 3.2 LU), target -14 +-1.0
- [PASS] spec-true-peak: -1.5 dBTP, ceiling -1.0
- [PASS] spec-black-frames: 0 black span(s) >= 0.15s, 0 unintended
- [PASS] spec-frozen-frames: 1 static span(s) >= 1.0s, 0 unintended

## Harsh jury (two rounds, local Qwen3-VL)
**Jury verdict: FAIL** (needs each dimension >= 6, mean >= 7, no shot under 4) | shots judged: 1 | unchecked: 25 | round 2 ran on 0
Film mean: **5.75**

| dimension | film mean | worst shot |
|---|---|---|
| identity | n/a | n/a |
| anatomy | n/a | n/a |
| motion | 5.00 | 5 |
| composition | 6.00 | 6 |
| lighting | 7.00 | 7 |
| story | 5.00 | 5 |

Why it failed:
- motion 5.00 < 6
- story 5.00 < 6
- mean 5.75 < 7
- 25 shot(s) UNCHECKED (judge gave no usable answer)

### Per shot (final scores; r1 = round 1 where round 2 argued it down)
| shot | t | identity | anatomy | motion | composition | lighting | story | mean |
|---|---|---|---|---|---|---|---|---|
| l01_manim_a_1 | 0.00 | UNCHECKED: round 1 unparsed |
| l01_manim_b_1 | 2.97 | UNCHECKED: round 1 unparsed |
| l02_manim_a_1 | 7.77 | UNCHECKED: round 1 unparsed |
| l02_manim_b_1 | 9.13 | UNCHECKED: round 1 unparsed |
| l03_manim_a_1 | 15.10 | UNCHECKED: round 1 unparsed |
| l03_manim_b_1 | 20.10 | UNCHECKED: round 1 unparsed |
| l04_manim_a_1 | 25.03 | UNCHECKED: round 1 unparsed |
| l05_manim_a_1 | 29.33 | UNCHECKED: round 1 unparsed |
| l05_manim_b_1 | 32.40 | UNCHECKED: round 1 unparsed |
| l06_manim_a_1 | 36.00 | UNCHECKED: round 1 unparsed |
| l06_manim_b_1 | 38.43 | UNCHECKED: round 1 unparsed |
| l07_manim_a_1 | 41.97 | UNCHECKED: round 1 unparsed |
| l07_manim_b_1 | 49.17 | UNCHECKED: round 1 unparsed |
| l08_manim_a_1 | 50.97 | UNCHECKED: round 1 unparsed |
| l08_manim_b_1 | 52.73 | UNCHECKED: round 1 unparsed |
| l09_manim_a_1 | 57.57 | UNCHECKED: round 1 unparsed |
| l09_manim_b_1 | 61.17 | UNCHECKED: round 1 unparsed |
| l10_manim_a_1 | 63.83 | UNCHECKED: round 1 unparsed |
| l10_manim_b_1 | 65.10 | UNCHECKED: round 1 unparsed |
| l11_manim_a_1 | 74.40 | UNCHECKED: round 1 unparsed |
| l11_manim_b_1 | 77.77 | UNCHECKED: round 1 unparsed |
| l12_manim_a_1 | 81.47 | UNCHECKED: round 1 unparsed |
| l12_manim_b_1 | 84.23 | n/a | n/a | 5 | 6 | 7 | 5 | 5.75 |
| l13_manim_a_1 | 89.53 | UNCHECKED: round 1 unparsed |
| l14_manim_a_1 | 96.03 | UNCHECKED: round 1 unparsed |
| l14_manim_b_1 | 97.53 | UNCHECKED: round 1 unparsed |

### Jury reasons (final)
- **l12_manim_b_1**: identity n/a: No person or creature is visible; identity consistency not applicable. / anatomy n/a: No person or creature is visible; anatomy evaluation not applicable. / motion 5: Checkmarks progress logically over time; motion is implied but not physically rendered—basic animation logic holds. / composition 6: Framing is consistent, centered, and readable; minimal visual clutter; purposeful layout for checklist progression. / lighting 7: Consistent dark background with subtle dot pattern; text and checkmarks evenly lit; no flicker or inconsistency. / story 5: Viewer understands a checklist is being completed; context is clear but lacks emotional or narrative depth.

## Jury: three largest defects (machine-readable)
Also written to `final/film_qc_jury_report.defects.json`. Re-render only these shots.

```json
{
 "film": "final/model_review_h3.mp4",
 "defects": [
  {
   "t": 84.896,
   "shot": "l12_manim_b_1",
   "dimension": "motion",
   "score": 5.0,
   "evidence": "cell 1 of 4 in the shot strip (frame @84.90s): Only 'License' and 'Fit' are checked; 'Compare' and beyond are unchecked, implying incomplete process.",
   "fix": "Update prompt to include all 7 steps in checklist, ensuring sequential completion for logical flow."
  }
 ]
}
```

## Poster candidate (last 3 s)
- final/film_qc_jury_report_poster.jpg: @103.85s, judge scored 1/10 of 1, 1, 1, 1, 1, 1