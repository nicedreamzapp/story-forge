# Story Forge status — oldest_tree

_generated 2026-10-04 00:11_

## Last queue

**1 of 1 shots produced a usable judged clip.**

| shot | outcome | detail |
|---|---|---|
| s6_breath | CLIP_KEPT | 3/5 |

## What the film still needs

_no spine defined in beats.json — the film has no completeness check_

## Where the time went

| step | runs | minutes | pass rate |
|---|---|---|---|
| judge_still | 2144 | 3607.2 | 28% |
| still | 2151 | 1616.6 | — |
| animate | 285 | 1215.9 | — |
| a2v_ltx25_bf16 | 1 | 4.3 | — |
| i2v_ltx25_distilled_full | 1 | 1.3 | — |
| i2v_ltx25_distilled_lowram | 1 | 1.1 | — |
| a2v_ltx2_mlxvideo | 1 | 0.7 | — |
| **total instrumented** | | **6447** | |

## What it learned

- 93 shot-level lessons across 35 shots in this project
- 30 curated house rules that carry to the next film

## What changed in the pipeline (24h)

- 5478037 Merge pull request #14 from nicedreamzapp/oldest-tree-face-check
- 7fa267a Face check: ArcFace identity gate on every still and clip; The Oldest Tree re-cut and published
- d49964a Merge pull request #13 from nicedreamzapp/pull-oldest-tree-video
- e35c646 README: pull The Oldest Tree video while the girl's face drift gets fixed
- 4c98818 Merge pull request #12 from nicedreamzapp/oldest-tree-october-2026
- 0b0530d The Oldest Tree: October 2026 progress film on YouTube, README + project state up to date

## Next

- shots reported UNBUILT need a spec or prompt change, not another re-roll at the same settings
- shots with a locked still but a failed clip need a shorter or gentler animation, not a new still
