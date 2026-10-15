---
title: How Story Forge works - architecture of a local AI film pipeline
description: The architecture of Story Forge, read from the code. The .sf parser, resolver and renderer; the gated director that judges every shot with a local vision model; memory scheduling; the ICM stage folders; and the models used at each step.
---

# How it works

Story Forge has two pipelines that share tools: a simple `.sf` script renderer and a gated
director that keeps working until every story beat has footage that passed its checks. Both
run every model locally and talk to ComfyUI, MLX and ffmpeg.

## The `.sf` path

```text
film.sf ──parse──▶ AST ──resolve──▶ scenes + presets ──emit──▶ film.storyplan.json ──run──▶ film.mp4
         parser.py         resolver.py                  emitter.py + packs.py        run.py
```

| Step | File | What it does |
|---|---|---|
| Parse | `story_forge/parser.py` | A hand-written, standard-library-only, indentation-aware parser. Turns lines into a list of nodes: variables, `@` directives, block heads (`film`, `scene`, `still`, `motion`, `narrate`, `voice`, `music`, `sfx`) and `key: value` pairs. |
| Resolve | `story_forge/resolver.py` | Substitutes `{$variables}`, collects voice, music and sfx presets, groups each scene's blocks, and turns `seed: auto` into a stable hash of slug, scene and role. |
| Emit | `story_forge/emitter.py`, `story_forge/packs.py` | Writes the storyplan JSON (schema version 0.1) and expands `style=` and `format=` into a prompt suffix, a frame size and a frame rate. |
| Run | `story_forge/run.py` | `lean` (default) renders scene by scene. `full` hands the plan to the older `story_pipeline.py`. |

What the lean renderer does for each scene (`run.py`, `render_lean`):

1. **Still.** Copies the image named by `still image:` / `path:`, or shells out to a Flux
   script. The repo's `tools/flux_t2i.py` is a small ComfyUI API client (Flux 1 dev FP8,
   `clip_l` plus `t5xxl_fp16`, 20 steps).
2. **Motion.** Calls `bin/render-route`, which picks an engine:
    - **Wan 2.2** image-to-video through `bin/make-video` and ComfyUI (Q6_K GGUF weights with the
      lightx2v 4-step LoRA, 16 fps; falls back to fp16 with a warning if the GGUF files are
      missing).
    - **LTX-Video 13B 0.9.8 distilled** through `bin/make-ltx-lightricks`, Lightricks' upstream
      multi-scale recipe (7 steps, upscale, 3 steps).
    - With `auto`, motion prompts about faces, talking or actions go to Wan and prompts about
      wind, fog, water or wide shots go to LTX.
3. **Conform.** ffmpeg rescales and crops the clip to the target size and frame rate.
4. **Narration.** One audio file per line. In the current code the narrator is Kokoro-82M
   ("Heart" voice) behind a Piper-compatible shim; `chatterbox/<name>` voices go to ChatterBox.
5. **Optional lip sync.** LivePortrait (plus Wav2Lip if asked) makes a talking head that is
   overlaid in a corner. Real human faces only.
6. **Assemble.** ffmpeg stitches the clips with 0.5 second crossfades, places each narration
   line at its scene's start time (`adelay` plus `amix`), and muxes the final video with fades.

The lean path does not judge anything and does not retry. It does not mix music either; see
[Configuration](configuration.md#presets-voice-music-sfx).

## The gated director pipeline

This is what made *The Oldest Tree*. The README describes its idea in one line: a local vision
model judges every shot against its story beat before it is kept.

```text
bin/forge "<film>"
  └─ bin/forge-keepalive        restarts the director if it dies (up to 10 times)
      └─ bin/forge-director     owns the loop
          ├─ spec_lint.py       refuses a shot spec that repeats a known mistake, before any GPU time
          ├─ bin/forge-shot     still → judge → identity → lock → animate → judge → trim → face lock
          ├─ bin/forge-review   writes STATUS.md
          └─ bin/build-episode  when every beat has footage: score, cards, assembly, film_qc
```

### What the director does each cycle

- Re-reads `shots.json` and its own state from disk, so a spec fixed or a shot unblocked while
  it runs is picked up.
- Finds the next **gap**: a beat on the story spine with no usable clip.
- Lints the spec with `pipeline-tools/spec_lint.py`.
- Runs `forge-shot` on it. If a shot fails, it tries again with a tighter setup: first a
  3 second locked-camera clip on new seeds, then 2 seconds, then 2 seconds at 40 steps.
- Does not count machine trouble as a failed attempt. A missing render backend or a memory
  refusal is a strike, and repeated strikes mark the shot BLOCKED with a reason that says it is
  a machine problem, not a story problem.
- Marks a shot BLOCKED after 4 attempts, or after 2 attempts where the still never passed
  (`SF_MAX_UNBUILT_ATTEMPTS`).
- Stops when every beat has footage (then assembles), when only blocked beats remain, when the
  hour limit is reached, or when nothing has passed for 2 hours (`SF_DRY_HOURS`). It never calls
  a stop with blocked beats "complete".

### What `forge-shot` does for one shot

1. **Still.** Qwen-Image 2.1 (through mflux, or a diffusers reference render when the shot names
   a character master), or a Flux img2img weld for a hand-built plate. It rolls several seeds.
   Lessons from earlier failures on this shot, and matching entries from the repo-wide
   `LESSONS.json`, are folded into the prompt.
2. **Beat gate** (`pipeline-tools/beat_gate.py`). The vision model first describes the frame
   without knowing the beat, then rules PASS or FAIL against it, by majority vote over several
   samples. A FAIL comes back with a one-sentence correction for the next try.
3. **Text check.** Lettering in frame rejects the still unless the shot allows it.
4. **Identity.** The vision model compares the still with the character's master side by side,
   then `pipeline-tools/face_check.py` compares faces with ArcFace embeddings (insightface).
5. **Lock.** The winning still is copied to its lock path and made read-only.
6. **Animate.** The judge is unloaded, ComfyUI is restarted clean, memory is reserved, and the
   still is animated with Wan 2.2 or LTX-2.5 (MLX, through `bin/make-ltx25`).
7. **Judge the clip.** The beat gate runs again on the clip. A pass is kept; otherwise the
   longest stretch that holds the beat (at least 2 seconds by default) is trimmed out; otherwise
   the clip goes to `clips/_failed/`.
8. **Face lock.** For shots without dialogue, `pipeline-tools/face_lock.py` re-renders each face
   with its canon identity (inswapper) while keeping the motion, then face check runs on the
   clip. Talking shots are skipped to protect lip sync.

Each shot ends in a named state, written to `forge_shot_results.json`: `CLIP_KEPT`,
`CLIP_TRIMMED`, `CLIP_FAILED`, `UNBUILT`, `STILL_LOCKED`, `STILL_HELD`, `ANIMATE_HELD`,
`ANIMATE_FAILED`, `CLIP_UNJUDGED`, `PREMISE_FAILED`, `INFRA`, `INIT_MISSING`, `NO_LOCK` or `DRY`.

### Assembly and final QC

`bin/build-episode` runs in stages: `preflight`, `song`, `cards`, `segments`, `assemble`, `qc`.

- **Preflight** checks that the edit list agrees with `beats.json` and runs the story gate. A
  shot that does not show its beat stops the build.
- **Song** asks Song Forge (ACE-Step) for an instrumental score, falling back to a saved bed.
- **Assemble** concatenates the segments and ducks the score under dialogue.
- **QC** runs `pipeline-tools/film_qc.py`: which mouth is open on each line, mouths shut in
  silence, identity across scenes, an artifact sweep every second, and a Whisper transcript
  check that every line is heard within 1.2 seconds of its moment. Only a clean run reports
  `COMPLETE`; anything else is `ASSEMBLED (NOT VERIFIED)`.

!!! note
    In the current code `bin/build-episode` has the edit list, title cards and QC cast of one
    film (*The Circus Train*) written into it. Other films, such as *The Oldest Tree*, use
    their own assembly scripts in their project folders. TODO-VERIFY.

### The project folder

A film lives in `projects/<film>/`. The director reads and writes these files:

| File | Written by | Holds |
|---|---|---|
| `beats.json` | a person | Shots with their beat, clip path, must-not list, identity and set; the `spine` of beats the film cannot skip; set masters |
| `shots.json` | a person | Shot specs for `forge-shot` and a `defaults` block |
| `director_state.json` | `forge-director` | Attempts, blocked shots with reasons, history |
| `shot_lessons.json` | `forge-shot` | Corrections learned per shot |
| `forge_shot_results.json` | `forge-shot` | The last state of each shot |
| `STATUS.md`, `QUESTIONS.md`, `WIP_REEL.mp4` | director tools | What was built, what is blocked and why, a rough reel |
| `ACTIVE_FILM`, `STOP_DIRECTOR` | `forge`, director | Which film is armed; a stand-down flag (delete it to resume) |
| `canon/`, `stills/`, `clips/`, `clips/_failed/` | | Masters, locked stills, kept and failed clips |

Repo-wide, `LESSONS.json` holds lessons from past films and `METRICS.jsonl` holds timing and
verdicts per step.

## Stage folders and `film-status`

The film process is also written down as eight numbered folders under `pipeline/`, following
[ICM](https://github.com/RinDig/Interpretable-Context-Methodology). Each folder's `CONTEXT.md`
says what the stage reads, what it writes, and what a person checks before the next stage.

| Stage | Job | Writes |
|---|---|---|
| `01_story` | premise, structure, dialogue | `premise.md`, `script.md` |
| `02_beats` | script to shot list, story test | `beats.json`, `continuity.json`, `story_test.md` |
| `03_canon` | one master per character and set | `canon/` |
| `04_shots` | gated stills, locked, animated | `shots.json`, `clips/`, `kept_clips_review.md` |
| `05_sound` | voices, mouth sync, score | `voices/`, `score_pick.md` |
| `06_assemble` | edit list to the cut | `final/*.mp4`, `final/timeline.json` |
| `07_gates` | audio, continuity, film QC | `final/*report*.md`, `known_defects.md` |
| `08_deliver` | publish | `published.md` |

`bin/film-status projects/<film>` reads those contracts and the project folder and prints which
stages are done and what is next. A stage is done when every output exists, is not empty, no
longer carries the template marker, and, where the stage has a human check, an `APPROVED.md`
exists. `--init` stamps a new film from `_templates/film/`.

## Memory scheduling

Big local models can't all share the machine at once. `core.py` routes every ComfyUI job
through one function, `queue_prompt`, which:

1. waits while Song Forge has a customer job running,
2. estimates the job's memory need (model size times 1.2, plus 12 GB of headroom) and unloads
   idle models (the ComfyUI cache, a local vision server) to make room,
3. runs the **memory gate**: it passes when macOS reports normal memory pressure and at least
   30% free memory. Otherwise it may restart an idle ComfyUI to release memory, then waits in 30
   second steps for up to 15 minutes before refusing.

`bin/mem-gate` runs the same gate from a shell. `forge-shot`, `film_qc` and `make-ltx25` also
reserve memory per phase (still 48 GB, animate 46 GB, QC 26 GB) from a separate local memory
guard. All the limits are environment variables; see
[Configuration](configuration.md#memory-gate-and-scheduling-corepy). The gate reads
macOS-only tools (`memory_pressure`, `sysctl`).

## The web UI

`server.py` is a Flask app on `http://127.0.0.1:17600`. Its pages:

- `/`: render one Wan clip from a prompt and an optional image.
- `/story`: the `.sf` editor, which runs `bin/sf render` in the background.
- `/story-classic`: the older form for `story_pipeline.py`.
- `/review`: a yes/no review queue for clips.
- `/pulse` and `/short`: live status of the active film.

`bin/story-forge-start` starts ComfyUI, the server and the director for the active film.

## Models at each step

| Step | Model | Where in the code |
|---|---|---|
| `.sf` still | FLUX.1 dev (FP8) through ComfyUI | `tools/flux_t2i.py` |
| `.sf` motion | Wan 2.2 I2V A14B; LTX-Video 13B 0.9.8 distilled | `bin/make-video`, `core.py`; `bin/make-ltx-lightricks` |
| Director still | Qwen-Image 2.1 (mflux); Flux img2img for plates | `bin/forge-shot` |
| Director motion | Wan 2.2 or LTX-2.5 (ltx-2-mlx) | `bin/forge-shot`, `bin/make-ltx25` |
| Talking close-ups | LTX-2 / LTX-2.5 audio-to-video | `bin/make-ltx25 --audio` |
| Vision judge | Qwen3-VL-32B, 4-bit MLX, through mlx-vlm | `pipeline-tools/film_qc.py`, `beat_gate.py` |
| Ears | Whisper large-v3-turbo through mlx-whisper | `pipeline-tools/film_qc.py`, `audio_check.py` |
| Face check and lock | insightface ArcFace (`buffalo_l`), `inswapper_128` | `pipeline-tools/face_check.py`, `face_lock.py` |
| Narrator | Kokoro-82M, "Heart" voice | `story_forge/run.py` |
| Character voices | ChatterBox | `bin/character_voice.py` |
| Score | ACE-Step through Song Forge | `bin/build-episode` |
| Director chat | gemma-3-12b-it 4-bit (MLX) | `director.py` |
