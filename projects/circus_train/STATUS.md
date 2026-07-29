# Story Forge status — circus_train

_generated 2026-07-28 19:33_

## Last queue

**1 of 3 shots produced a usable judged clip.**

| shot | outcome | detail |
|---|---|---|
| s3_rollout | CLIP_KEPT | 5/5 |
| s4_arrival | STILL_LOCKED |  |
| s8_goodbye | STILL_LOCKED |  |

## What the film still needs

**9 of 9 required beats have footage.**

| required beat | clip | still |
|---|---|---|
| a calm ordinary day is established so the interruption costs | s1_final.mp4 | yes |
| the heroes SEE that something is wrong — the call to adventu | s2_call_final.mp4 | yes |
| they commit and roll out | s2_final.mp4 | yes |
| they arrive at the broken-down train and the trouble is visi | s4_arrival_final.mp4 | yes |
| we SEE who is trapped — the audience gets someone to root fo | ellie_eye_final.mp4 | yes |
| the effort: the door is forced with real physical weight | s6_final_v2.mp4 | yes |
| the bang is felt from inside the dark car | s6_interior_final.mp4 | yes |
| THE PAYOFF: the door opens and the trapped animal is free on | s7_dooropen_final.mp4 | yes |
| the goodbye, with the rescued train alive behind them | s8_goodbye_final.mp4 | yes |

## Where the time went

| step | runs | minutes | pass rate |
|---|---|---|---|
| judge_still | 261 | 379.5 | 48% |
| animate | 25 | 277.9 | — |
| still | 261 | 207.7 | — |
| **total instrumented** | | **865** | |

## What it learned

- 157 shot-level lessons across 10 shots in this project
- 19 curated house rules that carry to the next film

## What changed in the pipeline (24h)

- 2a08279 forge-shot: --stage animate uses the locked still instead of re-rolling it
- 5b478f6 forge-shot: batch by model (--stage), repeatable --only, dry-run stops clobbering results
- 1f1a1a1 forge-shot: bounce ComfyUI before EVERY animate, unconditionally
- 3bc22b6 film_qc: identity must RULE first, and an unanswered question is UNCHECKED
- c08641e film_qc: judge a line at its MOMENT, not wherever similar words first appear
- 53c4f2a assemble the EDIT, not the directory — the cut had a dropped shot and doubled lines
- 8ef3018 film_qc: a lease is protection, not permission
- 96865b5 film_qc: an overridden run shouldn't wait 30min for a denial it will ignore
- 46591c6 gitignore: launcher log is runtime noise
- 321cef8 The dam + spine-coverage fix (authored earlier 2026-07-27), plus the day's metrics
- 09979e5 circus_train: the spine is finally on screen — 9/9 beats, film UNCHECKED
- 578c80f Rules 17-18 and six house lessons, from a 13-hour day that shipped no motion
- 0eab639 film_qc: refuse rather than get killed, and never let a kill read as a pass
- a12a11c Gates: judge the pointer, split the verdicts, stop lying about completion

## Next

- shots reported UNBUILT need a spec or prompt change, not another re-roll at the same settings
- shots with a locked still but a failed clip need a shorter or gentler animation, not a new still
