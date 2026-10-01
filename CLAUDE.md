# Story Forge — local AI generative video system

This directory is the home of **Story Forge**, a robust 100%-local generative VIDEO system — for making video of ANY kind (narrated explainers, ambient pieces, promos, documentary cuts, sagas, cartoons) in any style, from one readable `.sf` script. It is NOT a cartoon studio. Cartoons are just the case it works decently for right now — talking characters are the hardest case, so they're the proving ground, not the limit. When Claude Code starts here, this file auto-loads to bring you up to speed.

## Where to go
| Task | Read |
|---|---|
| Making or continuing a film | `pipeline/CONTEXT.md`, then ONLY the current stage's contract. `bin/film-status projects/<film>` says which stage (`--init` for a new film) |
| The frozen rules 1–27 (code comments cite "CLAUDE.md rule N") | `_shared/frozen-rules.md`, numbers unchanged |
| The rules enforced in code | `RULES.md` (its own numbering) |
| Writing the story before any render | `_shared/script-writing.md` |
| Givens on every video (coverage, mouth motion, LoRAs) | `_shared/movie-making-defaults.md` |
| Talking-character scenes | `_shared/dialogue-scenes.md` |
| Real footage driving a character | `_shared/motion-transfer.md` |
| Story, sound and QC gates before Matt sees a film | `_shared/gates-and-qc.md` |
| Services, ports, the mini, folder layout, narrator voice | `_shared/machines-and-layout.md` |

## Never skip, whatever the task
- Nothing is "checked/verified/done" until the gates in `_shared/gates-and-qc.md` ran and their reports were read.
- Song Forge customer jobs outrank renders; every heavy step passes the memory gate (frozen rules 11, 16).
- Approved work is the only work that survives; declined takes die the same session (frozen rule 13).
- Every rejection becomes a written lesson before the session ends (frozen rule 15).

## How we build (the ethos — apply this to every decision)
- **Build off what we KNOW works.** Perfect the proven win, then extend from it. Never restart from scratch and never chase an unproven path when a working one exists. Every new feature stands on a tested foundation.
- **This is OUR environment, running OUR language (`.sf`).** We do not lean on other people's systems that are slow, old, and not tuned to our machines. The DSL exists so we control the whole stack end-to-end.
- **Built FOR our hardware, taking full advantage at all times.** M5 Max 128GB does the heavy lifting, the mini runs in parallel, everything is Apple-Silicon / MPS-native and 100% local — no cloud inference, ever. We know exactly what we have and make the most of it.
- **The result: faster, fully owned, hardware-matched.** That's the whole point — escape generic, sluggish, mismatched tooling and run a pipeline that fits this hardware perfectly.

**Live products:**
- 🌐 Public site: https://nicedreamzwholesale.com/software/story-forge/
- 🐙 GitHub: https://github.com/nicedreamzapp/story-forge
- 🎬 First film: https://youtu.be/_bFQTl7_vF4 (live, public, made for kids)

**Read this first:**
- `~/Desktop/PROJECTS/story-forge/SESSION_HANDOFF.md` — full session state, what works, what's broken, where to resume the two-week speedup build.

**Quick file map:**
- `story_pipeline.py` — the core pipeline (Flux + Wan + Kokoro Heart narration + ACE-Step + ffmpeg, config-driven)
- `server.py` — Flask UI server on port 17600
- `ui/story.html` — Story Forge web form
- `bin/make-video` — Wan inference CLI (works)
- `bin/make-ltx-video` — LTX-Video fast-mode CLI (BROKEN, see SESSION_HANDOFF "Open problems #1")
- `bin/render-route` — auto-picks Wan vs LTX per scene
- `bin/story-new` — scaffold a new project in one command (`story-new "Name" --style … --format …`)
- `story_forge/packs.py` — style + format packs (the "any style, any format" layer); `/api/packs` serves them to the UI

