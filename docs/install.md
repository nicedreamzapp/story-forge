---
title: Install Story Forge on an Apple Silicon Mac
description: How to install Story Forge, the local AI video pipeline. Requirements (Apple Silicon, Python 3, ffmpeg, ComfyUI with Flux and Wan or LTX), cloning the repo and checking it with sf doctor.
---

# Install

Story Forge is a set of Python and shell scripts. There is no package to `pip install` and no
installer: you clone the repo and point it at the model runtimes you already have.

## What you need

**For the `.sf` script path** (`sf render`, the path covered in the [Quickstart](quickstart.md)):

| Piece | Why | Required |
|---|---|---|
| A Mac with Apple Silicon | Everything is built and tested on Apple Silicon (MPS and MLX). The README says it is built on an M5 Max with 128GB. | yes |
| Python 3 | Runs the CLI. The README says the parser and its tests were run on Python 3.11. The `.sf` parser itself uses only the standard library. | yes |
| `ffmpeg` and `ffprobe` on `PATH` | Assembles scenes into the final cut. | yes |
| [ComfyUI](https://github.com/comfyanonymous/ComfyUI), running | `tools/flux_t2i.py` draws every still through ComfyUI's HTTP API, and the Wan path renders through it too. | yes |
| Flux weights loaded in ComfyUI | The still for each scene. Default file names are in [Configuration](configuration.md#image-stage-flux-through-comfyui). | yes |
| Wan 2.2 and/or LTX-Video | Motion for each scene. `bin/render-route` picks Wan or LTX per scene. | yes |
| `piper` plus a `.onnx` voice | Narration. Only needed if a script has `narrate` lines. | optional |
| ChatterBox in its own Python env | Cloned character voices (`chatterbox/<character>` presets). | optional |
| An avatar pipeline checkout (LivePortrait / Wav2Lip) | Only for `with lipsync` on real human faces. | optional |

**For the gated director pipeline** (`bin/forge`, `forge-director`, `forge-shot`), the README
lists these extra requirements: mflux with Qwen-Image 2.1,
[ltx-2-mlx](https://github.com/dgrauet/ltx-2-mlx), a Qwen3-VL-32B judge on MLX (loaded with
mlx-vlm), and mlx-whisper. Face check and face lock also use insightface. The README is
direct about this part: it still has some paths hard-coded to the machine it was built on,
and it is published so you can read the method and borrow from it.

!!! warning "Not on NVIDIA or Linux today"
    Story Forge is Apple Silicon only. The owner answered this in
    [issue #7](https://github.com/nicedreamzapp/story-forge/issues/7): the pipeline targets MPS
    throughout and the judge runs through MLX. The models it composes (Flux, Wan 2.2, LTX,
    ACE-Step, Piper) do run on NVIDIA, and a CUDA port would be reviewed, but there is no
    such path in the repo.

## Get the code

```bash
git clone https://github.com/nicedreamzapp/story-forge
cd story-forge
```

The clone is large because the repo carries a finished film (`saga.mp4`, about 96 MB) and
hero images.

## Check what is missing

```bash
./bin/sf doctor
```

`sf doctor` checks every external piece a lean render needs and prints one line per piece
(`ok`, `MISS` for a missing required piece, `opt` for a missing optional one). It exits with
code 1 if a required piece is missing. Example output on a machine without ComfyUI running:

```text
story forge doctor

  [ok  ] flux script        /path/to/story-forge/tools/flux_t2i.py
  [ok  ] render-route       /path/to/story-forge/bin/render-route
  [opt ] piper              ~/.local/bin/piper
         SF_PIPER — narration voice
  ...
  [ok  ] ffmpeg             /usr/bin/ffmpeg
  [ok  ] ffprobe            /usr/bin/ffprobe
  [MISS] comfyui            http://127.0.0.1:8188
         SF_COMFY_URL — the flux script renders through it

1 required piece(s) missing. A lean render will fail until those resolve.
```

The ComfyUI check calls `GET <SF_COMFY_URL>/system_stats` with a 1.5 second timeout.

Every path `sf doctor` checks can be moved with an `SF_*` environment variable. See
[Configuration](configuration.md#environment-variables).

## Check your Flux model names

`tools/flux_t2i.py` sends ComfyUI model file names. If they do not match your install, list
what ComfyUI actually has and set the `SF_FLUX_*` variables to match:

```bash
python3 tools/flux_t2i.py --list-models
```

## Optional: run the tests

The DSL has unit tests under `story_forge/tests/`:

```bash
python3 -m pytest -q story_forge/tests
```

!!! note
    In a Linux container used to build these docs, 50 of 55 tests passed and the 5 tests in
    `test_keyframes.py` failed. See [Troubleshooting](troubleshooting.md#test_keyframespy-fails).
