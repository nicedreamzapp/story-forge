# Story Forge — local AI generative video system

This directory is the home of **Story Forge**, a robust local-first generative VIDEO system — for making video of ANY kind (narrated explainers, ambient pieces, promos, documentary cuts, sagas, cartoons) in any style, from one readable `.sf` script. It is NOT a cartoon studio. Cartoons are just the case it works decently for right now — talking characters are the hardest case, so they're the proving ground, not the limit. When Claude Code starts here, this file auto-loads to bring you up to speed.

## Where to go
| Task | Read |
|---|---|
| Making or continuing a film | `pipeline/CONTEXT.md`, then ONLY the current stage's contract. `bin/film-status projects/<film>` says which stage (`--init` for a new film) |
| Making a product promo (CAD renders, Matt's voice, cut to words, callouts) | `pipeline/formats/promo/CONTEXT.md` + `SCHEMAS.md`; start with `bin/film-status projects/<film> --init --format promo`, run with `bin/make-promo projects/<film>` (example: `projects/sitka_demo/`) |
| Acquiring browser takes (optional; mini's Brave, never APIs, refs required, never ChatGPT for photoreal product shots) | frozen rule 28, then `bin/browser-acquire projects/<film>/acquire.json` (`--mock` to test, never a live run) |
| The frozen rules 1–32 (code comments cite "CLAUDE.md rule N") | `_shared/frozen-rules.md`, numbers unchanged |
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
- Declined takes die the same session; coverage and alternates (listed in `manifest.json`) survive until the FILM is approved, then die that session (frozen rule 13 as amended).
- Shoot coverage and cut to the best, cut to the words, motivate every move, and never show Matt a film he has not been told is READY (frozen rules 29–32).
- Every rejection becomes a written lesson before the session ends (frozen rule 15).

## How we build (the ethos — apply this to every decision)
- **Build off what we KNOW works.** Perfect the proven win, then extend from it. Never restart from scratch and never chase an unproven path when a working one exists. Every new feature stands on a tested foundation.
- **This is OUR environment, running OUR language (`.sf`).** We do not lean on other people's systems that are slow, old, and not tuned to our machines. The DSL exists so we control the whole stack end-to-end.
- **Built FOR our hardware, taking full advantage at all times.** M5 Max 128GB does the heavy lifting, the mini runs in parallel, everything is Apple-Silicon / MPS-native. Inference stays local by default: everything WE run runs on our hardware, and for a product the primary photoreal source is a Blender Cycles render of the real CAD. ACQUIRED footage is allowed and gated exactly like our own: real footage, CAD renders, and optional browser takes made in Matt's logged-in Brave on the mini via `bin/browser-acquire` (refs required, never through an API, never ChatGPT for photoreal product shots; frozen rule 28). We know exactly what we have and make the most of it.
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
- `bin/film-status` — where a film stands, read from disk (`--format promo` for promos; prints READY FOR MATT)
- `bin/make-promo` — one command, project folder to gated final mp4 + thumbnail + youtube.json (stops at the first failing gate)
- `bin/browser-acquire` — optional browser takes via the broker on the mini (frozen rule 28; `--mock` for tests)
- `pipeline/formats/promo/` — the promo method (stages 01–10, `bin/make-promo` runs them); `promo-remotion/` — the Remotion v4 finish on the M5
- `story_forge/packs.py` — style + format packs (the "any style, any format" layer); `/api/packs` serves them to the UI

