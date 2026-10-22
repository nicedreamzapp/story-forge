---
title: Changelog
description: Story Forge changes by month, taken from the git history of nicedreamzapp/story-forge, from the first commit in May 2026 to October 2026.
---

# Changelog

Story Forge has no version numbers and the repo has no git tags. This page is built from the
commit history on `main` (105 commits at the time of writing), grouped by month. Dates are
commit dates. The one GitHub release is `lucid-engine`, which carries the film file for
*The Lucid Engine*, not a software version.

## October 2026

- **Face lock** (Oct 4, PR #15). `pipeline-tools/face_lock.py` re-renders every face in every
  animated clip with its canon identity (inswapper), keeping the motion. `forge-shot` runs it
  automatically; talk shots are skipped to protect lip sync. *The Oldest Tree* v3 recut with
  both missing scenes, a recast adult and a -16 LUFS mix.
- **Face check** (Oct 3, PR #14). `pipeline-tools/face_check.py` compares every face with the
  cast portraits (insightface ArcFace) on each still before lock and each clip before keep.
- *The Oldest Tree* October 2026 progress film published (Oct 3, PR #12), briefly pulled while
  a face drift was fixed (PR #13), then republished.
- **ICM stage folders** (Oct 1, PR #10). The film pipeline is written down as eight numbered
  folders under `pipeline/`, and `bin/film-status` reports which stage a film is in.
- `CLAUDE.md` becomes a short router; its content moves verbatim to `_shared/` (PR #11).
- README plain intro and requirements (PR #16); local home paths scrubbed from the public repo
  (PR #17); link to claude-code-local (PR #18).

## September 2026

- Story and sound gates that catch what `film_qc` can't, plus *The Oldest Tree* project
  (Sep 30).
- Stills move to **Qwen-Image 2.1** with canon references; Bernini-R measured and deleted;
  `forge-session` opens a terminal session (Sep 22).
- **`bin/forge-finish`**: bloom, colour grade and contrast for stills and clips, with ideas
  credited to Robbie Tilton's Compositor (Sep 19).
- Circus Train: locked stills, beat-gate calibration and QC state (Sep 7).
- Several README rewrites describing the pipeline as it is now (Sep 22 to 27, PR #9, PR #8).

## August 2026

- Circus Train: door payoff, style contract, canon references; LTX 2.5 build tools (Aug 30).
- Main merged into the `story-forge-studio-layer` branch (Aug 22).
- `CREDITS.md` added, naming upstream work and licenses; `LICENSE` made plain MIT with asset
  terms split into `LICENSE-ASSETS.md` (Aug 6).
- Scene-building method and pipeline tools locked (PR #3, Aug 5); Rhubarb no longer vendored.

## July 2026

- A long run of gate fixes (Jul 26 to 29): `spec_lint` refuses to repeat a known mistake,
  `forge-animatic` story reel, set canon enforced, a blocked stop is no longer called
  "FILM COMPLETE", `film_qc` reports UNCHECKED instead of passing when a question goes
  unanswered, assembly follows the edit list rather than the directory, and `forge-shot` gets
  `--stage` and repeatable `--only`.
- Circus Train reaches its first clean `film_qc` verdict: 107 checks, 107 passed (Jul 28).
- **The Director**: chat and storyboard UI, recipe bank and self-fixing QC; `film_qc.py`
  self-QC stage (Jul 22).
- Keyframe sandwich (anchor the last frame too) added, then documented as measuring worse
  than no anchor (Jul 20, PR #6). See the note on the [Configuration](configuration.md) page
  about its current state.
- **A fresh clone can render** (Jul 20, PR #5, closes issue #4): ships `tools/flux_t2i.py`,
  adds `story_forge/config.py` with `SF_*` environment variables, and adds `sf doctor`.
- README "Watch the films" section (Jul 18).

## June 2026

- *The Lucid Engine*, a psychedelic sci-fi short, with its release and YouTube link
  (Jun 30 to Jul 1).

## May 2026

- 1-step Wan distillation experiments with per-checkpoint LPIPS evaluation; best 1-step LPIPS
  0.052 after a 300-step extension (May 24 to 25, PR #1).
- A Metal flash-attention speedup was reported, then corrected the same day as a measurement
  artifact caused by a dispatch bug (May 24).
- **The `.sf` DSL**: parser MVP, multi-voice, SFX and lipsync clauses, and the first
  end-to-end `.sf` to `.mp4` render (May 24).
- New DSL-first web UI (May 24).
- LTX 0.9.8 running on M5 MPS, a measurement harness and Metal toolchain (May 24).
- First commits: README, YouTube metadata and `SESSION_HANDOFF.md` for *The Bear Sister*
  (May 23).
