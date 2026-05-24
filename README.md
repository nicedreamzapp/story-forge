# Story Forge

> A 4-minute animated film, end-to-end, **on one laptop, no cloud.**

```
   ╔══════════════════════════════════════════════════╗
   ║                                                  ║
   ║    flux  →  wan  →  piper  →  ace-step  →  mux   ║
   ║                                                  ║
   ║                  no cloud.                       ║
   ║                                                  ║
   ╚══════════════════════════════════════════════════╝
```

A local-only generative cinema pipeline. Five open-source models, ffmpeg, and 12 hours of M5 Max compute produced [the saga in this repo](./saga.mp4) — two-act, scored, narrated, color-graded, cross-faded, with title and credits. **Zero cloud calls. Zero API charges. Zero rate limits.**

![the saga, frame 22s](./hero-screenshot.jpg)

---

## The film in this repo

**`saga.mp4`** — *The Bear Sister*, a 4:08 two-act animated short.

- **Act One — The Rescue** *(0:00 → 2:00)* — Studio Ghibli watercolor. A child lost in winter, rescued by a mother bear, hibernates with the bear family, reunited in spring. 17 scenes.
- **Bridge** — Fade to black across the 20-year gap.
- **Act Two — The Return** *(2:00 → 4:00)* — Photoreal cinematic. The grown woman returns to the forest, finds the elder bear, meets the next generation. 26 scenes.
- **Credits** *(4:00 → 4:08)* — All-local production tag.

| | |
|---|---|
| **Runtime** | 4 min 8 sec |
| **Scenes** | 43 distinct |
| **Voices** | 1 Piper female (LibriTTS speaker 0), warm-EQ chain |
| **Music** | 2 ACE-Step instrumentals (Ghibli lullaby + cinematic homecoming) |
| **Compute hours** | ~12 hours total (51 Wan i2v renders @ ~11 min each + parallel everything else) |
| **Wall clock** | ~19 hours (with overnight sleep + iteration) |
| **Hardware** | One MacBook Pro · Apple M5 Max · 128 GB unified memory |
| **Cloud calls** | **0** |

---

## The story

<details open>
<summary><b>Act One — The Rescue</b></summary>

> In the deep pines of winter, a storm came. Wolves howled. Owls flew through the trees.
>
> A little girl wandered too far from home. Her lantern flickered in the swirling snow.
>
> The river was frozen. Silver fish slept beneath the ice. A small white rabbit watched her.
>
> She fell in the drifts. Her lantern dimmed. Foxes crept close. An owl glided overhead.
>
> But the forest knew. A mother bear stirred in her cave, two cubs tumbling at her heels.
>
> She followed the scent through the snow. Her cubs played behind her. Birds burst from the pines.
>
> She found the child, barely awake. The bear lowered her head, breath warm in the cold.
>
> With paws as soft as breath, she lifted the child. The cubs sniffed close, the owl watched.
>
> Into the warm dark of the den, where the fire burned and the mice slept in the moss.
>
> The cubs welcomed her like a sister. The mother stirred honey by the fire.
>
> They shared berries from a wooden bowl. Bats whispered across the cave ceiling.
>
> Winter passed in a single long breath. The stars spun, and the aurora rippled green.
>
> She slept between them, safe in their warmth. Their hearts beat together in the dark.
>
> In her dreams she flew with the spirits. Bears of starlight, salmon leaping through stars.
>
> When the icicles began to weep, spring returned. Flowers pushed through. Butterflies emerged.
>
> They walked into the sun, the cubs tumbling, deer watching, blossoms falling like pink snow.
>
> Her family found her on the path of flowers. But the forest stayed with her, forever.

</details>

<details open>
<summary><b>Act Two — The Return</b> <i>(twenty winters later)</i></summary>

> Twenty winters had passed since she left the forest.
>
> But the call of the pines never left her.
>
> She took down the red hood from where it had hung.
>
> And drove the long road back into the redwoods.
>
> The trailhead waited where it had always been.
>
> She tied the hood at her throat, just as she had as a child.
>
> And the forest watched her come home.
>
> The salmon ran fierce in the stream where she had once dreamed of them.
>
> An owl marked her path. She remembered him.
>
> A fox emerged, and led her deeper.
>
> She found her stone, marked years ago.
>
> And entered the grove where the old ones lived.
>
> A great bear slept in the sun — older now, wiser.
>
> She knelt, and the elder stirred.
>
> They knew each other. Across the years.
>
> The forest sister had come home.
>
> The elder lifted her head. Her daughter came forward.
>
> And behind her came the next generation.
>
> The cubs came close, curious and bold.
>
> Their mother followed, slow and accepting.
>
> And the forest family was whole again.
>
> Together they walked through the deeper grove.
>
> Until they came to the old cave, moss-covered now.
>
> She entered alone, and found what her child-self had left.
>
> The elder pressed her forehead to hers. A goodbye.
>
> And she walked into the sun, the forest with her, forever.

</details>

*Full text also at [STORYBOOK.md](./STORYBOOK.md).*

---

## What runs where

```
       ┌─────────────────────────────────────────────────────────┐
       │                       M5 Max                             │
       │                                                          │
       │   ┌──────────┐    ┌──────────┐    ┌──────────┐           │
       │   │  Flux 1  │───►│ Wan 2.2  │───►│  ffmpeg  │──► saga   │
       │   │ Dev FP8  │    │   i2v    │    │  compose │           │
       │   └──────────┘    └──────────┘    └────▲─────┘           │
       │   text-to-image   image-to-video       │                 │
       │                                        │                 │
       │   ┌──────────┐    ┌──────────┐    ┌────┴─────┐           │
       │   │  Piper   │    │ ACE-Step │    │  Pillow  │           │
       │   │ LibriTTS │    │  music   │    │ title +  │           │
       │   └──────────┘    └──────────┘    │ credits  │           │
       │   narration       instrumental    └──────────┘           │
       │                                                          │
       └─────────────────────────────────────────────────────────┘
```

Every model runs locally. Nothing leaves the machine.

### Component stack

| Stage | Tool | Model | Purpose |
|---|---|---|---|
| Still image per scene | [Flux 1 Dev FP8](https://huggingface.co/black-forest-labs/FLUX.1-dev) | 16 GB | Sets composition + character look |
| Motion per scene | [Wan 2.2 i2v](https://huggingface.co/Wan-AI) | 27 GB + 1 GB lightx2v LoRA | Animates the still into 5-sec native motion |
| Voice narration | [Piper TTS](https://github.com/rhasspy/piper) | LibriTTS_R medium | Storyteller female voice |
| Music | [Song Forge / ACE-Step](https://github.com/ace-step/ACE-Step) | 13 GB | Instrumental scores |
| Compose | [ffmpeg 8.1](https://ffmpeg.org/) | — | xfade, sidechain ducking, fades, mux |
| Title cards | [Pillow](https://pillow.readthedocs.io/) | — | PNG text overlays |

---

## The clever bits (what isn't in the YouTube tutorials)

These are the patterns that took iteration to land. Each one would be a feature if this were a product:

### 1. **Per-sentence Piper + `adelay+amix` for scene-synced narration**

Most pipelines `concat` narration lines into one block at t=0. By scene 4 the audio is two scenes ahead of the visuals.

Instead: each narration line is rendered separately, then placed at its scene's onscreen start time via ffmpeg's `adelay`. All lines are then `amix`'d into a single track padded to the full video duration. The audio and visuals stay in lock-step the whole movie.

### 2. **Warm storyteller EQ chain**

Piper's raw output sounds like a robot. The voice in this saga is the same model with a deliberate signal chain:

```
highpass(80) → +2dB low-shelf @ 250Hz   (chest warmth)
             → -2dB high-shelf @ 7kHz   (soften sibilance)
             → compressor (-18dB threshold, 2.5:1 ratio)
             → aecho(60ms, 0.15)         (intimate room tail)
             → loudnorm I=-16 LUFS        (bedtime story level)
```

The result is a voice that reads as "a person telling you a story," not "an AI generating speech."

### 3. **Music ducks under narration automatically (sidechain compression)**

The instrumental score plays throughout the movie at -22 LUFS bed level. When the narrator speaks, ffmpeg's `sidechaincompress` filter ducks the music down ~10 dB, then releases back. Zero manual mix automation.

### 4. **Native-speed Wan, no slow-motion stretch**

A common pattern in AI-video tutorials: render 5-sec Wan clips, stretch them with `setpts*1.5` to fit longer scene durations. This makes everything look like dreamy slow-motion. Story Forge plays Wan clips at native 5-sec speed and uses more scenes instead — motion reads as real video.

### 5. **xfade-based saga stitching**

Combining two independently-rendered films into one saga uses `xfade=transition=fadeblack` between them (visual time-jump bridge) and `acrossfade` on the audio for smooth music handoff. No editing software needed.

### 6. **Scene-graph composition**

Each scene is a record:
```python
{
    "still": "<Flux prompt>",
    "motion": "<Wan motion prompt>",
    "narration": "<one storyteller line>",
}
```

The pipeline iterates the list. Change one scene, only that scene re-renders. Add a scene, the timing math redistributes itself. Delete one, the saga shortens cleanly.

---

## What's on the build-out roadmap

The current pipeline is the proof. The next pass is what makes it 30× faster:

- **1-step Wan distillation** — Train a LoRA that collapses Wan's 4-step inference into 1. *(4× per scene)*
- **Metal kernels for attention** — Rewrite Wan's attention hot path in Apple Metal Shading Language. *(2.5×)*
- **LTX-Video drop-in for B-roll** — Use Lightricks' 2 B-param LTX-Video for ambient scenes that don't need Wan's 14 B. *(scenes drop from 11 min to ~30 sec)*
- **Two-node parallel render** — Mini becomes a Wan worker, M5 + mini split the queue. *(2× throughput)*
- **Optical-flow warp** — Render keyframes with Wan, interpolate the rest with a tiny flow net. *(5-10×)*
- **Multi-voice + lip-sync** — Multiple Piper speakers + Wav2Lip for actual dialogue scenes.

Stacked: today's 5-hour render becomes ~3 minutes. The trajectory is real — every one of those is sitting in the open, just waiting to be wired up.

---

## Why local

The whole thing is the point. The film you watched played out frame by frame, sentence by sentence, score bar by bar, on **one machine you can carry in your bag**. No upload step. No "your queue position is 47." No "your subscription renewed." No telemetry. The script is local, the model is local, the output is local. The hardware is yours, the time is yours, the work is yours.

The cloud companies will tell you a 4-minute animated film with custom score and synced narration needs a server farm. It doesn't. It needs a MacBook Pro and a Saturday.

---

## Credits

- Story by **Matt Macosko + Claude**
- Animation: Wan 2.2 i2v
- Stills: Flux 1 Dev FP8
- Narration: Piper LibriTTS
- Music: Song Forge / ACE-Step
- Rendered locally on a M5 Max MacBook Pro
- No cloud

*A Story Forge production.*

---

## License

MIT for the pipeline code (once published).
Saga film itself: CC BY-NC-SA 4.0 — share with attribution, don't sell.
