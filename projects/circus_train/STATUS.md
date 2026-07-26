# Story Forge status — circus_train

_generated 2026-07-26 13:09_

## Last queue

**0 of 2 shots produced a usable judged clip.**

| shot | outcome | detail |
|---|---|---|
| s4_arrival_plate | UNBUILT | 0 candidates, none passed |
| s8_goodbye_plate | UNBUILT | 0 candidates, none passed |

## What the film still needs

**6 of 9 required beats have footage.**

| required beat | clip | still |
|---|---|---|
| a calm ordinary day is established so the interruption costs | s1_final.mp4 | yes |
| the heroes SEE that something is wrong — the call to adventu | s2_call_final.mp4 | yes |
| they commit and roll out | s2_final.mp4 | yes |
| they arrive at the broken-down train and the trouble is visi | s4_arrival_raw.mp4 | yes |
| we SEE who is trapped — the audience gets someone to root fo | — | yes |
| the effort: the door is forced with real physical weight | s6_final_v2.mp4 | yes |
| the bang is felt from inside the dark car | s6_interior_final.mp4 | yes |
| THE PAYOFF: the door opens and the trapped animal is free on | — | yes |
| the goodbye, with the rescued train alive behind them | — | yes |

## Where the time went

| step | runs | minutes | pass rate |
|---|---|---|---|
| judge_still | 78 | 94.4 | 12% |
| animate | 6 | 93.0 | — |
| still | 78 | 46.2 | — |
| **total instrumented** | | **234** | |

## What it learned

- 87 shot-level lessons across 10 shots in this project
- 13 curated house rules that carry to the next film

## What changed in the pipeline (24h)

- 433a7c3 forge-animatic: the Leica reel we should have built on day one
- 53418dd spec_lint: refuse to repeat a known mistake, deterministically
- 987bb62 Story Forge.app opens a working session that already knows the film
- 71efaca forge: one command for every film, and every film inherits the same brain
- 2800873 The app now launches the director, and the rules live in the repo as RULES.md
- 134dec7 The director: a pipeline that does not stop until the film is done
- e8e8317 Audit the auditor: calibrate the gate against known human verdicts
- 6e8d313 Learn unprompted (rule 15); plan for closing the gap to frontier video
- be8f6a7 Research: where render time actually goes, and the first house lessons
- eb1e922 README: lead with the review loop; forge-shot learns across films
- 18b37ad Story gate: a shot must PROVE it depicts its beat before it ships
- a580c5e i2v: GGUF is now the default path — fp16 pair OOM-kills renders

## Next

- shots reported UNBUILT need a spec or prompt change, not another re-roll at the same settings
- shots with a locked still but a failed clip need a shorter or gentler animation, not a new still
