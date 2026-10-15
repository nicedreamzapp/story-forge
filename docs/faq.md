---
title: FAQ
description: Common questions about Story Forge, the local AI video pipeline. Does it need the cloud, does it run on NVIDIA or Windows, what does it cost, can I sell what I make, how long does a render take.
---

# FAQ

## Does Story Forge send anything to the cloud?

No. Every model it calls (Flux, Qwen-Image, Wan, LTX, the voices, the score and the judges)
runs on the Mac, through ComfyUI, MLX or local Python environments. The README's stance is
"no upload, no queue, no subscription, no telemetry". Model weights do have to be downloaded
once, from wherever you get them.

One exception sits in the repo: `bin/make-ltx-cloud`, an old standalone script that sends a
single image-to-video job to fal.ai if you set `FAL_KEY`. Nothing in the pipeline calls it.

## Does it run on NVIDIA, Windows or Linux?

Not today. It is Apple Silicon only. In
[issue #7](https://github.com/nicedreamzapp/story-forge/issues/7) the owner explained that the
pipeline targets MPS throughout and the QC judge runs Qwen3-VL through MLX. The underlying
models (Flux, Wan 2.2, LTX, ACE-Step, Piper) do run on NVIDIA, so a port would mostly mean
swapping the MPS device calls and replacing the MLX judge with a torch vision model. A CUDA
port PR would be reviewed, but there is no such path in the repo. The same reply warns that
8 GB of VRAM is tight for Wan 2.2 14B image-to-video on any platform.

## How much memory do I need?

The repo does not state a minimum. Everything is built and tested on an M5 Max with 128GB.
The gated pipeline loads a 32B vision model and video models in turn, and a memory gate
(`bin/mem-gate`) refuses heavy steps when free memory is too low. Minimum specs for smaller
Macs are TODO-VERIFY.

## How long does a render take?

Numbers reported in the repo, all on an M5 Max with 128GB:

- `test_tiny.sf` (one 3 second scene): about 2 minutes, per the comment in the script.
- LTX-2.5 animation: about 69 seconds per shot, against 13 to 16 minutes per shot on Wan.
- *The Oldest Tree* (2:53, 49 shots): about 105 hours of measured compute, including 2,130
  judged stills and 270 animation renders.

## What does it cost?

The software is free (MIT). The README compares the cost of a 4 minute film of about 51 clips
on hosted services (Runway Gen-3 about $204, Pika 2.0 about $102 to $153, Sora or Luma about
$128, Kling about $89) with $0 for Story Forge plus electricity. Those service prices are the
README's own estimates and are TODO-VERIFY against current pricing.

## Can I sell videos I make with it?

The code is MIT, so the code is not the limit. The model weights are. `CREDITS.md` notes that
the Flux path references `flux1-dev`, whose weights are under the FLUX.1 [dev] Non-Commercial
License, so output rendered with them should not be sold. It points to FLUX.1-schnell
(Apache-2.0) for commercial work. Check every other model's license yourself before selling
output. See [Credits](credits.md).

## Can I use the films in the repo?

`saga.mp4` (*The Bear Sister*) is CC BY-NC-SA 4.0, per `LICENSE-ASSETS.md`.

## Is it only for cartoons?

No. It is meant for any kind of video: narrated explainers, ambient pieces, promos,
documentaries and animated films. Talking characters are the hardest case, so that is where
it is tested hardest. Style packs (`pixar-3d`, `flat-2d`, `photoreal`, `watercolor`,
`anime`, `claymation`, `noir`) and format packs (`film`, `reel`, `square`, `narrated-doc`,
`cinematic`) are listed on the
[Configuration](configuration.md#style-and-format-packs) page.

## Do I have to use the `.sf` language?

For the simple path, yes: `bin/sf` renders `.sf` scripts. The gated director pipeline
(`bin/forge`) works from a project folder with `beats.json` and `shots.json` instead. See
[How it works](how-it-works.md).

## Does it add lip sync to cartoon characters?

No. `with lipsync` exists for real human faces only. The README says it never goes on cartoon
characters, because Wav2Lip paints human lips on them. Talking close-ups in the gated pipeline
are generated from the voice recording instead (LTX-2 audio-to-video).

## Why is the "keyframe sandwich" off?

Pinning the last frame as well as the first measured worse on LTX 13B distilled: the figure
smeared at strength 1.0 and blurred at 0.7, while the unanchored shot stayed clean. In the
current code the parser still accepts `end_prompt` and `end_path`, but the lean renderer
(`story_forge/run.py`) no longer passes them on, so they have no effect; see [Troubleshooting](troubleshooting.md#test_keyframespy-fails).

## Where do I report a bug?

[Open an issue](https://github.com/nicedreamzapp/story-forge/issues/new) with your Mac chip,
RAM and the stage that failed, as the README asks.
