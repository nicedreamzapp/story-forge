<div align="center">

# 🎬 Story Forge

### A whole film studio on one laptop. No cloud. No bill. No limits.

![100% local](https://img.shields.io/badge/cloud_calls-0-brightgreen?style=for-the-badge)
![Apple Silicon](https://img.shields.io/badge/runs_on-Apple_Silicon-black?style=for-the-badge&logo=apple)
![Self-reviewing](https://img.shields.io/badge/reviews_its_own_work-yes-blueviolet?style=for-the-badge)
![MIT](https://img.shields.io/badge/code-MIT-orange?style=for-the-badge)

**Pictures ✦ motion ✦ voices ✦ original music ✦ titles ✦ a finished cut**<br>
Any kind of video, any style: explainers, documentaries, promos, music shorts, and fully animated films.

</div>

---

## 🍿 Watch the films

<table>
<tr>
<td width="50%" valign="top">

[![The Bear Sister](./hero-screenshot.jpg)](https://youtu.be/_bFQTl7_vF4)

### 🐻 The Bear Sister
A lost child, a mother bear, and a homecoming twenty winters later. Two acts, two art styles, **4:08**, 43 scenes.

[▶ Watch](https://youtu.be/_bFQTl7_vF4) · [📥 Download](./saga.mp4) · [📖 Read the story](./STORYBOOK.md)

</td>
<td width="50%" valign="top">

[![The Lucid Engine](./lucid-hero.jpg)](https://www.youtube.com/watch?v=31ZeFu-ePcc)

### 🌀 The Lucid Engine
An uploaded mind pieces together how the world ended. Psychedelic sci-fi, five acts, **~4:30**, original score.

[▶ Watch](https://www.youtube.com/watch?v=31ZeFu-ePcc) · [📥 Download](https://github.com/nicedreamzapp/story-forge/releases/tag/lucid-engine)

</td>
</tr>
</table>

> 🕰️ Both were made on the **first** pipeline (May and June 2026). Nearly every stage has been upgraded since. Here's what runs today 👇

---

## 🛠️ What I built

**Matt Macosko** designed and built the pipeline. The models (Qwen-Image, LTX, Wan, Flux, Kokoro, ChatterBox, ACE-Step, Qwen3-VL, Whisper) are upstream open models; the code here is what turns them into a film.

- 📜 **A script language, `.sf`**, with its own parser, resolver and emitter ([`story_forge/`](story_forge/)), a CLI ([`bin/sf`](bin/sf)), style/format packs and tests
- 🎬 **A director that runs until the film is done** ([`bin/forge-director`](bin/forge-director)): finds beats with no passing footage, drives each one, escalates instead of repeating, and marks a shot BLOCKED with its reason
- 🎯 **A shot builder that proves each shot** ([`bin/forge-shot`](bin/forge-shot)): still → judge → identity check → lock → animate → judge the clip → trim to the part that holds
- 👁️ **Vision and audio judges** ([`beat_gate.py`](pipeline-tools/beat_gate.py), [`film_qc.py`](pipeline-tools/film_qc.py)): blind description then verdict, majority vote across frames, set continuity, mouths, identity, every line heard
- 🧱 **A spec linter** ([`spec_lint.py`](pipeline-tools/spec_lint.py)) that blocks a shot spec repeating a known mistake before any GPU time is spent
- 💾 **Memory scheduling** ([`core.py`](core.py), [`bin/mem-gate`](bin/mem-gate)) so heavy local models take turns instead of crashing the machine
- ✂️ **Assembly** ([`bin/build-episode`](bin/build-episode), [`bin/forge-finish`](bin/forge-finish)): preflight checks, score, title cards, ducked mix, finishing grade, final QC
- 🖥️ **A local web UI** ([`server.py`](server.py), [`ui/`](ui/)) for rendering, live status and reviewing clips

---

## ⚡ The pipeline today

<div align="center">

### 📝 ➜ 🎨 ➜ 👁️ ➜ 🎞️ ➜ 👁️ ➜ 🎙️ ➜ ✂️ ➜ 🔍 ➜ 🍿

</div>

| Step | | What happens |
|:---:|:---:|---|
| **1** | 📝 | **Write it.** The story is broken into beats, the moments the film can't skip |
| **2** | 🎨 | **Draw it.** Qwen-Image 2.1 paints each shot, using the locked character designs as reference |
| **3** | 👁️ | **Judge it.** An AI looks at the picture: right moment? right character? If not, it says *why*, and that goes into the next try 🔁 |
| **4** | 🎞️ | **Move it.** LTX-2.5 brings the approved picture to life in about a minute |
| **5** | 👁️ | **Judge it again.** Is the clip still showing the right thing? Only the part that works is kept ✂️ |
| **6** | 🎙️ | **Voice it.** Narrator, character voices, and an original music score |
| **7** | ✂️ | **Cut it.** Every shot goes together in story order, with the music dipping under dialogue |
| **8** | 🔍 | **Final check.** AI eyes and ears watch the whole film: right mouths, clean faces, every line heard |
| **9** | 🍿 | **Film!** |

**How it fits together.** `forge` points the director at a project folder, where the film's state lives: `beats.json` (the story spine), `shots.json` (shot specs), `director_state.json` (attempts and blocks) and `shot_lessons.json`. Each cycle the director re-reads the specs, lints them, picks the next beat with no passing footage and hands it to `forge-shot`. That rolls seeds for a still until the vision judge passes it and the identity check matches the character's master, locks it, animates it, then judges the clip and keeps only the stretch that holds the beat. A failed still or clip comes back with a concrete correction from the judge, and that goes into the next prompt, and after repeated failures the director tightens the attempt (shorter clip, locked camera, new seeds) before marking it BLOCKED. The models never share the machine at once: the in-process judge is unloaded before animation, ComfyUI is restarted clean before each render, a memory gate runs before every heavy step, the still and animate phases hold their memory one at a time, and renders wait for Song Forge's customer jobs. When every spine beat has footage, `build-episode` checks the edit list against the beats, runs the story gate, lays in the score and title cards, assembles the cut and runs `film_qc` over the result.

**Folders are the orchestration.** The film pipeline is also written down as eight numbered stage folders under [`pipeline/`](pipeline/CONTEXT.md), following [ICM](https://github.com/RinDig/Interpretable-Context-Methodology). Each stage's `CONTEXT.md` says what it reads, what it writes, and the one thing a human checks before the next stage starts, and each approval is a file on disk. [`bin/film-status`](bin/film-status) reads a project folder and says which stage the film is in and what it still needs, so any agent with no memory of the film can pick it up.

<table>
<tr>
<td width="33%" valign="top">

### 🎨 Make
- **Stills:** Qwen-Image 2.1, with each character's locked master as a reference picture
- **Motion:** LTX-2.5, about **69 seconds** per shot (it used to take 13–16 min on Wan)
- **Stunts:** real footage drives the character (Wan 2.2 Animate)

</td>
<td width="33%" valign="top">

### 🎙️ Sound
- **Narrator:** Kokoro "Heart"
- **Characters:** ChatterBox, one voice each
- **Talking close-ups:** the video is generated *from* the voice recording
- **Music:** original score from Song Forge / ACE-Step

</td>
<td width="33%" valign="top">

### 👁️ Check
- **Eyes:** Qwen3-VL-32B looks at every shot
- **Ears:** Whisper checks every line lands on time
- **Memory guard:** refuses a render the machine can't afford
- **Never:** fake a pass

</td>
</tr>
</table>

---

## 🧠 It reviews its own work

> **The story that started it:** one episode passed **86 of 91** automated checks and still made no sense. The bear was supposed to shoulder a jammed door open. Instead he poked the wall with a stick. Every check passed anyway, because none of them asked what the picture actually *showed*.

So now a local vision model judges every shot against its story beat before it's kept.

| 🚦 Gate | ❓ The question it asks |
|---|---|
| 🎯 **Beat** | Does this picture actually show what the script says happens here? |
| 🚫 **Forbidden** | Is anything in frame that rules the shot out? |
| 🐻 **Identity** | Is this still the same character as the locked master? |
| 🚂 **Set** | Is this the same train as last scene, or did it invent a new one? |
| 🦴 **Spine** | Is every beat the film can't live without actually on screen? |
| 🎤 **Technical** | Right mouth on the right line, no melting faces, every word heard on time? |
| 💾 **Memory** | Can the laptop afford this render without crashing? |

<table>
<tr>
<td width="50%" valign="top">

### ✨ Four rules that keep it honest
1. 🙈 **Judge blind first.** Describe the frame, *then* hear the beat. Tell a model the answer first and it just agrees.
2. 🗳️ **One frame isn't a verdict.** It votes across several frames and prints every ballot.
3. 📚 **Failures teach.** The reason a shot failed goes into the next attempt, and into memory for every future film.
4. 🙅 **No quiet shortcuts.** Can't pass? It's reported **UNBUILT**. Can't judge? It says **UNCHECKED**.

</td>
<td width="50%" valign="top">

### 📈 The receipts
- First run on a "finished" episode: **2 of 11 shots passed.** It spotted the stick in the door without being told.
- Rebuilding that scene: 3 of 4 tries showed the right action, **2 of those 3 drifted off-model**, and the one that passed both got locked.
- The human verdict: *"looks like he's leaning in and trying to push a door open."* ✅

</td>
</tr>
</table>

---

## 🚀 Where it stands (Sept 22, 2026)

| | |
|---|---|
| ✅ **Full films, hands-off** | The director keeps working until every beat has footage that passed. Current film: **22 of 23** beats built |
| ✅ **~10× faster animation** | LTX-2.5: **~69 s** a shot vs **13–16 min** on Wan |
| ✅ **Voice-driven close-ups** | The video is made from the voice recording, so the mouth follows real speech |
| ✅ **Firsts on a Mac** | LTX 13B running on Apple Silicon · 1-step Wan distillation · a speed harness gated on image quality |
| 🧪 **Tried, measured, dropped** | A hand-written Metal kernel (no real gain) · Bernini-R (25× slower for the same result) · Wav2Lip (paints human lips on cartoons 😬) |
| ⏳ **Next up** | The Mac mini as a second render node · finishing pass built into assembly · new engines in the chat UI |

---

## 🏁 Try it

```bash
git clone https://github.com/nicedreamzapp/story-forge && cd story-forge
./bin/sf doctor                                     # 🩺 what's missing
./bin/sf render story_forge/examples/test_tiny.sf   # 🎬 ~2 min on an M5 Max
```

These commands run the **original `.sf` path**: parse a script, then Flux still → Wan/LTX motion → narration → ffmpeg stitch. It has no judges and no director. Need: **ComfyUI** running · **Flux** + **Wan 2.2** / **LTX** loaded in it · **ffmpeg** · optional **piper**-compatible voice. `sf doctor` tells you what's missing.

The **gated director pipeline** (everything in "The pipeline today") needs the extra requirements below.

<details>
<summary>🎛️ <b>The full gated pipeline</b> (forge / director / forge-shot)</summary>

<br>

```bash
forge new "a documentary about the harbour" --kind doc   # start a film
forge "hank and doug"                                    # pick up exactly where it stopped
forge status                                             # built · blocked · next
```

Extra requirements: mflux + Qwen-Image 2.1, [ltx-2-mlx](https://github.com/dgrauet/ltx-2-mlx), a Qwen3-VL-32B judge on MLX, and mlx-whisper. It still has some paths hard-coded to the machine it was built on. It's published so you can read the method and borrow from it.

| Tool | Job |
|---|---|
| [`forge-animatic`](bin/forge-animatic) | 🎞️ Story reel on the locked stills before anything gets animated |
| [`forge-director`](bin/forge-director) | 🎬 Keeps going until the film is done; escalates instead of repeating the same failure |
| [`forge-shot`](bin/forge-shot) | 🎯 Still → judge → lock → animate → judge the clip → trim to the part that works |
| [`build-episode`](bin/build-episode) | ✂️ Score, title cards, assembly, QC |
| [`forge-finish`](bin/forge-finish) | 🌅 Glow, color grade, contrast |
| [`film_qc.py`](pipeline-tools/film_qc.py) | 🔍 The final verdict |

Rules the code enforces: [`RULES.md`](RULES.md) · lessons from past films: [`LESSONS.json`](LESSONS.json) · speed experiments: [`RENDER_SPEED_RESEARCH.md`](RENDER_SPEED_RESEARCH.md)

</details>

<details>
<summary>📜 <b>The <code>.sf</code> script language</b></summary>

<br>

```
$style = "Studio Ghibli watercolor, soft snowfall, golden hour"
film "Cabin Open" slug=cabin_open scene_dur=8.5

voice warm:  piper/en_US-libritts_r-medium speaker=0 length=1.18
music wintry: ace/wintry-soft-piano vol=0.35
@mix duck voice -> music threshold=-22 ratio=4

scene snow_walk:
    still flux:
        prompt: "{$style}, a child in a red cloak crossing a snowfield"
    motion wan:                     # or  motion ltx:  for B-roll
        prompt: "gentle push-in, soft falling snow"
        duration: 5.0
    narrate warm:
        line: "The snow came down like a hush."
    music wintry vol=0.30
```

Parser, resolver and emitter live in [`story_forge/`](story_forge/). Full example: [`cabin_open.sf`](story_forge/examples/cabin_open.sf). `with lipsync` exists for real human faces only. It never goes on cartoon characters.

</details>

<details>
<summary>🥪 <b>Keyframe sandwich</b>: pinning the last frame too (it made things worse here)</summary>

<br>

The idea: pin the *last* frame as well as the first, so a character can't drift. On LTX 13B distilled, a walking shot came out **worse** with the anchor. At strength 1.0 the figure smeared, at 0.7 it blurred, and with no anchor it stayed clean. So it's **off by default**. If you want it: `still.end_prompt` / `still.end_path`, LTX only. Example: [`keyframe_sandwich.sf`](story_forge/examples/keyframe_sandwich.sf).

</details>

<details>
<summary>🪄 <b>Clever bits</b></summary>

<br>

- 🗣️ **Narration lines up with each scene.** Every line is placed at its scene's start time, so the audio never drifts ahead of the picture.
- 🔥 **Warm storyteller EQ.** Highpass, low-shelf warmth, softened sibilance, gentle compression, a small room echo, −16 LUFS.
- 🎚️ **Auto-ducking.** The music dips about 10 dB whenever someone speaks.
- 🏃 **Wan plays at real speed.** Nothing gets stretched into dreamy slow-mo.
- 🔀 **Engine picked per shot.** Wan for the hero shots, LTX for the atmosphere.
- 🚫 **No fake motion.** Never shakes a still, never paints mouths.

</details>

---

## 💸 Why local

| Service | Cost for a 4-min film (~51 clips) |
|---|---|
| 🟥 Runway Gen-3 | ~$204 |
| 🟧 Pika 2.0 | ~$102–153 |
| 🟨 Sora / Luma | ~$128 |
| 🟦 Kling | ~$89 |
| 🟩 **Story Forge** | **$0**, just electricity ⚡ |

No upload. No queue. No subscription. No telemetry. **Your laptop, your film.** 💚

---

<div align="center">

### 🙌 Built on the shoulders of

Qwen-Image · LTX · Wan · Flux · Kokoro · ChatterBox · ACE-Step · Qwen3-VL · Whisper · ffmpeg<br>
Full credits and licenses → [CREDITS.md](CREDITS.md)

**Code:** [MIT](LICENSE) · **Films:** [see LICENSE-ASSETS](LICENSE-ASSETS.md) (*The Bear Sister* is CC BY-NC-SA 4.0)

🐛 Something broken? [Open an issue](https://github.com/nicedreamzapp/story-forge/issues/new) with your Mac chip, RAM, and the stage that failed.

*Story by Matt Macosko + Claude · made on one MacBook Pro · zero cloud* ✨

</div>
