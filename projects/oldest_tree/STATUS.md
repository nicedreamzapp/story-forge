# Story Forge status — oldest_tree

_generated 2026-09-30 11:34_

## Last queue

**0 of 1 shots produced a usable judged clip.**

| shot | outcome | detail |
|---|---|---|
| s7_back | STILL_HELD |  |

## What the film still needs

_no spine defined in beats.json — the film has no completeness check_

## Where the time went

| step | runs | minutes | pass rate |
|---|---|---|---|
| judge_still | 2123 | 3555.3 | 28% |
| still | 2130 | 1583.4 | — |
| animate | 270 | 1186.0 | — |
| a2v_ltx25_bf16 | 1 | 4.3 | — |
| i2v_ltx25_distilled_full | 1 | 1.3 | — |
| i2v_ltx25_distilled_lowram | 1 | 1.1 | — |
| a2v_ltx2_mlxvideo | 1 | 0.7 | — |
| **total instrumented** | | **6332** | |

## What it learned

- 81 shot-level lessons across 32 shots in this project
- 30 curated house rules that carry to the next film

## What changed in the pipeline (24h)

- 0c5efb9 The Oldest Tree + story and sound gates that catch what film_qc can't

## Next

- shots reported UNBUILT need a spec or prompt change, not another re-roll at the same settings
- shots with a locked still but a failed clip need a shorter or gentler animation, not a new still
