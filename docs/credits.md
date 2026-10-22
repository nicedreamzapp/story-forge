---
title: Credits and licenses
description: The open models and tools Story Forge is built on (FLUX, LTX-Video, Wan, Qwen-Image, Qwen3-VL, Kokoro, ChatterBox, Piper, ACE-Step, Whisper, MLX, ComfyUI, FFmpeg) and their licenses.
---

# Credits

Story Forge is orchestration code. The models that draw, animate, speak, score and judge are
other people's work, and none of it is claimed here. Matt Macosko designed and built the
pipeline code in this repo; the README credits the stories to "Matt Macosko + Claude".

## Listed in CREDITS.md

These come straight from [`CREDITS.md`](https://github.com/nicedreamzapp/story-forge/blob/main/CREDITS.md)
in the repo, with the licenses it states.

| Project | What it does here | By | License (as stated in CREDITS.md) |
|---|---|---|---|
| [FLUX](https://github.com/black-forest-labs/flux) | Stills and keyframes | Black Forest Labs | code Apache-2.0; weights licensed separately (see below) |
| [LTX-Video](https://github.com/Lightricks/LTX-Video) | Image-to-video motion | Lightricks | Apache-2.0 |
| [Wan](https://github.com/Wan-Video/Wan2.2) | The other motion path, and the 1-step distill target | Alibaba's Wan team | Apache-2.0 |
| [Piper](https://github.com/rhasspy/piper) | Narration and character voices | Michael Hansen and the Rhasspy project | MIT |
| [ACE-Step](https://github.com/ace-step/ACE-Step) | Original score | The ACE-Step team | Apache-2.0 |
| [Rhubarb Lip Sync](https://github.com/DanielSWolf/rhubarb-lip-sync) | Mouth shapes from audio | Daniel Wolf | MIT |
| [Compositor](https://github.com/robbietilton/Compositor) | The ideas behind `bin/forge-finish` (bloom with Screen blending, a colour grade, contrast), rebuilt as one ffmpeg pass | Robbie Tilton | MIT (ideas only, no code used) |
| [FFmpeg](https://ffmpeg.org/) | Every cut, mux and grade | The FFmpeg project | LGPL/GPL depending on build |

### The FLUX weights

From `CREDITS.md`: the FLUX code is Apache-2.0, but the pipeline references `flux1-dev`,
whose weights carry the FLUX.1 [dev] Non-Commercial License Agreement. Anything rendered with
those weights should not be sold. For commercial output, CREDITS.md points to
[FLUX.1-schnell](https://huggingface.co/black-forest-labs/FLUX.1-schnell), which is
Apache-2.0.

## Also used by the code

These are named in the README or imported by the code, but are not yet listed in
`CREDITS.md`. Their licenses are not recorded in the repo, so they are marked TODO-VERIFY.

| Project | Where it shows up | License |
|---|---|---|
| [ComfyUI](https://github.com/comfyanonymous/ComfyUI) | Runs Flux and Wan workflows over its HTTP API (`tools/flux_t2i.py`, `core.py`) | TODO-VERIFY |
| Qwen-Image 2.1 (Qwen team, Alibaba) | Stills in the gated pipeline, run through mflux | TODO-VERIFY |
| [mflux](https://github.com/filipstrand/mflux) | Runs Qwen-Image on MLX (`bin/forge-shot`) | TODO-VERIFY |
| LTX-2 / LTX-2.5 (Lightricks) via [ltx-2-mlx](https://github.com/dgrauet/ltx-2-mlx) | Image-to-video and audio-to-video in the gated pipeline (`bin/make-ltx25`) | TODO-VERIFY |
| Qwen3-VL-32B (Qwen team, Alibaba) | The vision judge | TODO-VERIFY |
| [MLX](https://github.com/ml-explore/mlx) and [mlx-vlm](https://github.com/Blaizzy/mlx-vlm) | Run the vision judge on Apple Silicon (`director.py`, `pipeline-tools/film_qc.py`) | TODO-VERIFY |
| Whisper (OpenAI) via [mlx-whisper](https://github.com/ml-explore/mlx-examples) | Checks every line is heard on time (`pipeline-tools/audio_check.py`, `film_qc.py`) | TODO-VERIFY |
| Kokoro-82M ("Heart" voice) | Narrator | TODO-VERIFY |
| ChatterBox (Resemble AI) | Cloned character voices | TODO-VERIFY |
| [insightface](https://github.com/deepinsight/insightface) (ArcFace, inswapper) | Face check and face lock (`pipeline-tools/face_check.py`, `face_lock.py`) | TODO-VERIFY |
| LivePortrait and Wav2Lip | Optional `with lipsync` for real human faces | TODO-VERIFY |
| [ICM (Interpretable Context Methodology)](https://github.com/RinDig/Interpretable-Context-Methodology) | The method behind the numbered `pipeline/` stage folders | TODO-VERIFY |
| [Claude Code](https://claude.com/claude-code) (Anthropic) | `CLAUDE.md` and `bin/forge-session` set up working sessions where Claude Code drives the pipeline | n/a (a tool, not a dependency) |

## Licenses for this repo

- **Code:** MIT. See [`LICENSE`](https://github.com/nicedreamzapp/story-forge/blob/main/LICENSE).
- **Media:** [`LICENSE-ASSETS.md`](https://github.com/nicedreamzapp/story-forge/blob/main/LICENSE-ASSETS.md).
  `saga.mp4` (*The Bear Sister*) is CC BY-NC-SA 4.0. Model weights pulled at runtime carry
  their own upstream licenses and are not redistributed in the repo.

If your work is used here and is missing or described wrongly,
[open an issue](https://github.com/nicedreamzapp/story-forge/issues/new).
