# Qwen3.6-35B-A3B-bf16 as QC judge (single still + shot description, thinking off, T1.0/top_p .95/top_k 20)

| image | ground truth | Qwen verdict | reason | match |
|---|---|---|---|---|
| s01_a.png | ACCEPTED (teaser shot 1, approved) | FAIL | FAIL: the dust particles appear digitally rendered and overly sharp against the glass, breaking the illusion of atmospheric depth. | no |
| s07_a.png | ACCEPTED (teaser shot 7 lip-sync, approved) | PASS | PASS, The image accurately depicts the described character and setting without any visible generation artifacts or anatomical errors. | yes |
| s08_a.png | ACCEPTED (teaser shot 8, approved) | PASS | PASS | yes |
| s11_bl.png | ACCEPTED (teaser shot 11, approved; face deliberately soft) | PASS | PASS, the image accurately depicts the described reflection while maintaining natural human anatomy and avoiding digital artifacts. | yes |
| t13_a.png | ACCEPTED (trailer HQ shot t13, kept) | PASS | PASS: The image matches the description with no visible generation artifacts. | yes |
| s03_b.png | FLAGGED (film_qc artifact x4: the man in the photo has a blank, featureless face; kept on purpose) | FAIL | FAIL, The figure standing in the background has a featureless, blank face instead of the described "face in shadow." | yes |
| s05_a.png | FLAGGED (take rejected: figure walked into light, head-turn beat did not read) | FAIL | FAIL, the arm holding the glass appears severed at the wrist, creating a major anatomical and generative artifact. | yes |
| s06_a.png | FLAGGED (take rejected: fork never moved / a family hand lifted it) | FAIL | FAIL, image shows only three people and does not depict the required five plates or animated fork. | yes |
| t01_a.png | REJECTED (HQ video take: car reverses toward camera) | PASS | PASS | no |
| t04_a.png | REJECTED (HQ video take: push ends in a soft blur) | PASS | PASS: The image matches the description with an elderly woman with silver curled hair and a lavender cardigan seen from behind looking out a rain-streaked window, free of visible artifacts. | no |

Score: 7/10 matches ground truth. Judging time 22s.

Caveat: stills cannot show video-only defects (motion, fork, car direction, blur at end of push); the ground truth for those flags comes from the rendered video takes.
