---
title: Troubleshooting Story Forge
description: Fixes for common Story Forge problems, built from real GitHub issues and the error messages in the code. ComfyUI not reachable, Flux model names, sf doctor vs sf render paths, memory gate refusals, BLOCKED and UNCHECKED shots.
---

# Troubleshooting

Every message on this page is quoted from the code. File references point at `main` as of
October 2026. If your problem is not here,
[open an issue](https://github.com/nicedreamzapp/story-forge/issues/new) with your Mac chip,
RAM and the stage that failed.

## Setup and `sf`

### `sf doctor` shows `[MISS] comfyui`

`sf doctor` calls `<SF_COMFY_URL>/system_stats` and got no answer within 1.5 seconds. Start
ComfyUI, or set `SF_COMFY_URL` if it runs elsewhere (for example on another Mac on your
network). `tools/flux_t2i.py` gives the same advice when it can't connect:

```text
cannot reach ComfyUI at <url>: ...
start ComfyUI first, or set SF_COMFY_URL.
```

### `no image came back` from the Flux step

Usually ComfyUI rejected a model file name ("value not in list"). The defaults are
`flux/flux1-dev-fp8.safetensors`, `clip_l.safetensors`, `t5xxl_fp16.safetensors` and
`flux/ae.safetensors`. List what your ComfyUI has and set the `SF_FLUX_*` variables to match:

```bash
python3 tools/flux_t2i.py --list-models
export SF_FLUX_UNET="your/unet.safetensors"
```

### `sf doctor` is clean but `sf render` cannot find a tool

This is a known gap in the current code. `sf doctor` checks the paths in
`story_forge/config.py`, but the renderer, `story_forge/run.py`, uses its own fixed paths
(lines 58 to 81):

| What | Path `run.py` uses |
|---|---|
| `render-route` | `~/Desktop/PROJECTS/AI/videopipe/bin/render-route` |
| Flux script | `~/Scripts/flux_t2i.py` |
| Narration voice | `~/.local/bin/kokoro-piper-shim` and `~/Desktop/PROJECTS/Song Forge/piper_voices/en_US-libritts_r-medium.onnx` |
| ChatterBox | `~/chatterbox-env/bin/python` and `~/Desktop/PROJECTS/AI/videopipe/bin/character_voice.py` |
| Avatar pipeline | `~/Desktop/PROJECTS/avatar-pipeline` |
| Full engine | `~/Desktop/PROJECTS/AI/videopipe/story_pipeline.py` |
| Work folder | `~/Desktop/AI Videos/<slug>/` |
| Clip output that `render-route` writes and `run.py` looks in | `~/AI/videopipe/outputs/` |

A fix for this landed in July 2026 (commit `e837143`, which closed
[issue #4](https://github.com/nicedreamzapp/story-forge/issues/4), "flux_t2i.py missing from
repo"), and a later commit (`44e923b`, August 30, 2026) brought the fixed paths back. Until the
renderer reads `config.py` again, either put the tools at those paths (symlinks to your clone
work) or edit the constants at the top of `run.py`. TODO-VERIFY.

### `render-route produced no output for <label>`

The motion step ran but `run.py` found no clip. Run `bin/render-route` by hand with the same
still and prompt to see the engine's own error. Check that the clip landed in
`~/AI/videopipe/outputs/`, which is where `run.py` looks.

### A changed prompt renders the old picture

The lean renderer reuses files already in the work folder: if `still_NN.png`, `raw_NN.mp4` or
`clip_NN.mp4` exists in `~/Desktop/AI Videos/<slug>/`, that step is skipped. Delete the work
folder (or the scene's files) after editing a scene.

### `ParseError` (exit code 2) or `ResolveError` (exit code 3)

| Message | Cause |
|---|---|
| `line N: unterminated string in '...'` | An unclosed quote |
| `bad variable assignment: '...'` | A `$name` line without `= value` |
| `unrecognized line (no colon, no $/@): '...'` | A block or `key: value` line missing its colon |
| `scene needs a name` | `scene:` with no name |
| `undefined variable $name` | `{$name}` used but never defined |

### A traceback that ends in `unknown style` or `unknown format`

`sf` does not catch this error, so it prints a full traceback. The last line names the packs
that exist. Use one of the style packs `pixar-3d`, `flat-2d`, `photoreal`, `watercolor`,
`anime`, `claymation`, `noir`, or one of the format packs `film`, `reel`, `square`,
`narrated-doc`, `cinematic`.

### Scene errors from `sf render`

| Message | Cause |
|---|---|
| `scenes not in plan: [...]` | A name in `--scenes` that the script does not have |
| `scene <name>: still image not found: <path>` | A bad `path:` in `still image:` |
| `scene <name>: needs still.prompt (flux) or still.path (image)` | An empty `still` block |

### No narration in the output

`[narrate] piper or model missing; skipping line` means the narration voice was not found at
the paths in the table above. The render carries on without that line.

### Lip sync messages

All of these fall back to audio without a talking head:

- `[lipsync] driver still missing: <path> — skipping` (set `LIPSYNC_DRIVER_STILL`)
- `[lipsync] LP inference or venv missing under <dir> — skipping`
- `[lipsync] wav2lip checkpoint missing: <path> — falling back to lp`

### `test_keyframes.py` fails

When these docs were built, 50 of the 55 tests in `story_forge/tests/` passed on Python 3.13
in a Linux container. The 5 failures were all in `test_keyframes.py`. Those tests cover the
"keyframe sandwich" (`end_prompt`, `end_path`, passed on to `render-route --last-frame`).
Commit `44e923b` removed that wiring from `run.py`, so the parser still accepts the keys but
nothing uses them. `bin/render-route --last-frame` itself still works when called directly.
TODO-VERIFY whether the feature should be restored or the tests and example retired.

## Motion engines

| Message | What to do |
|---|---|
| `[make-video] WARNING: i2v GGUF weights missing — falling back to fp16, which can OOM at 832x480x81.` | Download the Wan 2.2 Q6_K GGUF weights into ComfyUI, or expect high memory use |
| `--gguf requested but Q6_K weights not downloaded` | Same, for text-to-video |
| `No T2V model ready yet — downloads still in progress.` / `No I2V model ready yet` | Wan weights are not in `~/AI/ComfyUI/models` |
| `[ltxL] Lightricks repo not found at ...` | Clone Lightricks' LTX-Video repo where the message says |
| `[route] --last-frame ignored: wan i2v conditions on the first frame only. Pass --engine ltx to use it.` | Use LTX for first-and-last-frame shots |
| `make-ltx25: no LTX-2.5 pack on disk (dgrauet/ltx-2.5-mlx) and SF_LTX25_PACK unset` | Download the pack or set `SF_LTX25_PACK` |
| `make-ltx25: --res must be multiples of 32` | Pick a size like 832x480 |
| `ComfyUI rejected prompt: {...}` / `Workflow error: {...}` | A node or model name ComfyUI does not have |

`bin/make-ltx-video` is marked broken in the project notes (its single-pass pipeline produces
noise). `render-route` uses `bin/make-ltx-lightricks` instead. Do not re-enable the
`wan_metal_fused` ComfyUI node: the notes record it crashing renders, and its measured speedup
turned out to be a measurement bug.

On Apple Silicon, FP8 (`FP8_E4M3FN`) weights fail on the first sampler step under MPS. Use fp16
or GGUF weights.

## Memory gate

| Message | Meaning |
|---|---|
| `[mem-gate] waiting for memory before '<label>' (...)` | Not enough free memory yet. It retries every 30 seconds. |
| `[mem-gate] low memory before '<label>' (...) and ComfyUI holds NGB of cached models — bouncing it` | It is restarting an idle ComfyUI to release memory. |
| `mem-gate: refusing to start '<label>' — machine still short after 900s (...)` | It gave up. Quit heavy apps or wait for other jobs, then re-run. |
| `mem-gate restarted ComfyUI but it did not come back within 120s` | The restart command did not work on your machine. Set `SF_COMFY_START_CMD`. |
| `[customer] Song Forge has a paying job running — renders hold` | Renders wait for Song Forge jobs by design. Without Song Forge running this check finds nothing and moves on. |

Tune the thresholds with `SF_MEM_GATE_MIN_FREE`, `SF_MEM_GATE_MAX_WAIT` and the other variables
on the [Configuration](configuration.md#memory-gate-and-scheduling-corepy) page.
`SF_MEM_GATE=0` turns the gate off, with the warning `you are on your own`.

## Director, shots and QC

### What the states mean

The gated pipeline never reports a failure as a pass. Three words come up a lot:

- **UNBUILT**: no candidate passed the gates. Nothing was locked.
- **BLOCKED**: the director gave up on a beat and wrote down why (`QUESTIONS.md`,
  `director_state.json`).
- **UNCHECKED**: a check could not run, so the result is unknown, not passed.

### Common director stops

| Message | What to do |
|---|---|
| `no film matches '<words>'. Films I have: ...` | Use words from the project folder name |
| `director already running` | One director at a time. `bin/forge stop` to stop it. |
| `SPEC REJECTED before rendering` | `spec_lint.py` found a known mistake in the shot spec (for example an impact, a rear view, a missing `clip_beat`). Fix the spec. |
| `STOPPING — X/Y beats have footage and N are BLOCKED. This film is NOT complete.` | Read `QUESTIONS.md`, fix or re-conceive the blocked shots, then `bin/unblock <project> <ids>` |
| `STOPPING — nothing has passed the gates in N.Nh.` | The dry-spell stop. It writes `STOP_DIRECTOR`; delete it (or run `bin/forge "<film>"`) to resume |
| `the render backend kept going away — this is a machine problem, not a story problem` | ComfyUI keeps crashing or restarting. Fix that before re-running. |
| `the machine never had room for this shot` | Memory. Close other work or lower the shot's needs. |
| `the still never passed the gates in 2 attempts` | The prompt describes something the model will not draw. Re-write the shot. |
| `no calibration set — gate verdicts are UNVERIFIED this run` | Add `beats_calibration.json` with human verdicts so the judge can be checked |

### `forge-shot` messages

| Message | Meaning |
|---|---|
| `every seed this cycle failed the same way — this is the PREMISE, not the sampling.` | Re-write the shot instead of rolling more seeds |
| `TEXT IN FRAME — rejected` | The still has lettering. Set `allow_text` if that is intended. |
| `identity ...: DRIFT` | The character does not match its master |
| `identity: master missing (...) — UNCHECKED, not a pass` | The character master image is missing |
| `face gate: face_check or its venv missing, UNCHECKED` | Also printed when the project has no `film_shots.json`, which face check needs |
| `animation never holds the beat — clip NOT used` | The clip is kept in `clips/_failed/` for diagnosis; the still stays locked |
| `face drifted off the canon character during animation — clip NOT used` | Face check failed on the clip |

### `build-episode` and `film_qc`

| Message | Meaning |
|---|---|
| `ABORT: the edit and the script disagree about which file is which shot` | The edit list and `beats.json` point at different shots |
| `ABORT: shots that do not depict their beat are in the EDL` | The story gate failed a shot. Reshoot it or drop it. |
| `ABORT: no usable footage at all` | No clips were found. `build-episode` currently has one film's edit list written into it (see [How it works](how-it-works.md#assembly-and-final-qc)). |
| `ASSEMBLED (NOT VERIFIED)` | The cut exists, but QC did not pass or did not run |
| `[film_qc] REFUSING TO START: the memory guard would not grant 26GB for the vision judge ...` | Free memory and re-run. `--allow-critical-memory` overrides. |
| `film_qc was KILLED (exit N) — the film is UNCHECKED, not verified.` | QC died partway. Re-run it. |

## Web UI

- `POST /api/sf_render` passes the wrong structure to the renderer and is likely to fail. The
  `/story` page uses `POST /api/render` with an `sf` field, which goes through `bin/sf`.
  TODO-VERIFY.
- `ui/director.html` exists, but `server.py` never registers the routes from `director.py`, so
  `/director` returns 404. TODO-VERIFY.
- `POST /api/kill_all` runs `pkill -9 -f main.py`, which stops any process whose command line
  contains `main.py`, not just ComfyUI.

## Not on Apple Silicon

Story Forge does not support NVIDIA, Windows or Linux. See
[issue #7](https://github.com/nicedreamzapp/story-forge/issues/7) and the [FAQ](faq.md).
