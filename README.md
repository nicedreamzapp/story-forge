# Story Forge

> A local-only generative video system. Any kind of video, any style, on one laptop. No cloud.

```
   ╔════════════════════════════════════════════════════════════╗
   ║                                                            ║
   ║   qwen-image → judge → ltx-2.5 / wan → judge → voices +    ║
   ║        ace-step score → finish → film_qc → a film          ║
   ║                                                            ║
   ║            a script.  a laptop.  a film.                   ║
   ║                                                            ║
   ╚════════════════════════════════════════════════════════════╝
```

Story Forge is a self-contained generative VIDEO system — for making video of **any kind**: narrated explainers, ambient pieces, promos, documentary cuts, music-driven shorts, sagas, and yes, fully animated films — in any style. Motion, narration, character voices, original music, titles and credits, entirely on local hardware, composed by `ffmpeg`. **Zero cloud calls. Zero API charges. Zero rate limits.** Run it once, run it a thousand times.

**And it reviews its own work.** A local vision-language model judges every shot against the story beat it is supposed to depict, votes across frames, holds characters and sets to locked designs, feeds the rejection reason back into the next attempt, and refuses to assemble a film out of shots that don't tell the story. [Jump to the review loop ↓](#-it-reviews-its-own-work--the-verification-loop)

Animation is the *proving ground*, not the limit — talking characters are the hardest case a video system can face, so that's where the pipeline gets battle-tested. Everything it learns there (QC gates, judge models, scene locking, character consistency) applies to every other kind of video it renders.

> **What changed since the first films.** *The Bear Sister* (May) and *The Lucid Engine* (June) were made on the first pipeline: Flux stills, Wan / LTX motion, Piper narration, one pass through `ffmpeg`. Since then almost every stage has been replaced or wrapped in a gate. Stills moved to Qwen-Image 2.1, animation moved to LTX-2.5, the narrator moved to Kokoro, characters got their own voices, and a director loop now owns the film until every beat has footage that passed review. [The current pipeline ↓](#-how-a-film-gets-made-now)

---

## 🛠 How a film gets made now

One command owns a film from first idea to finished cut:

```bash
forge new "a documentary about the harbour" --kind doc   # start a film
forge "hank and doug"                                    # resume one exactly where it stopped
forge status                                             # what's built, what's blocked, what's next
```

Under it, each film lives in `projects/<name>/` with its own story spine, shot specs and lessons, and every film inherits the same two shared brains at the repo root: [`RULES.md`](RULES.md) (the rules the code enforces) and [`LESSONS.json`](LESSONS.json) (what earlier films paid to learn, keyword-matched to new shots).

```
 script ─► beats.json spine ─► forge-animatic (story reel on locked stills, before any animation)
                                      │
                                      ▼
                  forge-director ── loops until every required beat has footage ──┐
                        │                                                          │
                        ▼                                                          │
   forge-shot:  still (Qwen-Image 2.1, canon masters as references)                │
                  → beat gate (blind description, then PASS/FAIL, majority vote)   │
                  → identity gate vs the locked character master                   │
                  → LOCK (chmod 444)                                               │
                  → animate (LTX-2.5 distilled i2v, or Wan 2.2 GGUF)               │
                  → re-judge the clip → keep only the stretch that holds the beat  │
                        │                                                          │
                        ▼                                                          │
   build-episode: score (Song Forge / ACE-Step) → title + credit cards             │
                  → assemble in story order, score ducked under dialogue ◄─────────┘
                        │
                        ▼
   film_qc (eyes + ears) ─► verdict, reported verbatim
```

| Stage | Tool | What it does |
|---|---|---|
| Write | `screenwriting` skills → `*.bible.sf` + `beats.json` | Premise, structure and dialogue are settled in plain screenplay terms before a single still is rendered |
| Story reel | [`bin/forge-animatic`](bin/forge-animatic) | The locked stills cut to the scratch dialogue at real timings; a missing beat shows as a black *MISSING SHOT* slug |
| Direct | [`bin/forge-director`](bin/forge-director) | Finds the beats with no passing footage and drives them; escalates on failure (shorter clip, fresh seeds, still only, then BLOCKED with a written reason) instead of repeating; writes `STATUS.md`, `WIP_REEL.mp4` and `QUESTIONS.md` every cycle |
| Shoot | [`bin/forge-shot`](bin/forge-shot) | The self-proving shot builder described below |
| Lint | [`pipeline-tools/spec_lint.py`](pipeline-tools/spec_lint.py) | Refuses a shot spec that repeats a known mistake (two characters in one frame with no composite, a beat written as intent instead of a visible state) |
| Look | [`pipeline-tools/style_contract.py`](pipeline-tools/style_contract.py) | Reads the film's own approved frames and writes one locked paragraph of visual language that goes into every prompt |
| Assemble | [`bin/build-episode`](bin/build-episode) | Preflight (every EDL entry cross-checked against `beats.json`), score, cards, segments, assembly, QC; resumable per stage |
| Finish | [`bin/forge-finish`](bin/forge-finish) | Bloom, gradient-map colour grade and S-curve contrast in one static ffmpeg pass, identical on stills and clips. Run by hand for now; not yet a stage in `build-episode` |
| Verify | [`pipeline-tools/film_qc.py`](pipeline-tools/film_qc.py) | The last word on every film; its pass/fail counts are reported verbatim |

**Two things the pipeline no longer does.** It never ships a still on a camera move as a finished shot — a Ken Burns glide reads as a slideshow, and a cut that passed 107 of 107 machine checks was rejected on sight for exactly that. And it never repaints a mouth: Wav2Lip and face models paint human mouths onto stylized characters. Dialogue shots either prompt the mouth motion and density-match the voice to it, or, for close-ups, condition the video on the actual voice recording (audio-to-video).

**Motion transfer.** For action i2v can't do on its own (a cartwheel, a strike combo), a real video of a person is traced to a pose track and Wan 2.2 Animate renders the character performing it: [`bin/motion_pose.py`](bin/motion_pose.py) → [`bin/make-motion-video`](bin/make-motion-video). Lateral, single-person source footage at natural speed works; motion toward the camera does not. Identity drifts toward a generic version of the character and that is said out loud, not hidden.

**The machine protects itself, and the paid work on it.** Every heavy step asks a memory guard for room first and is charged for what it actually holds (Metal/GPU memory included, which `ps` cannot see), not what it declared. A refusal is a real answer: the shot is held rather than rendered into swap. Song Forge customer jobs outrank renders.

---

## 🔍 It reviews its own work — the verification loop

Generating a shot is the easy half. The hard half is knowing whether the shot you got is
the shot the story needed — and that is where every AI film pipeline quietly breaks.

We learned it the expensive way. An episode of ours passed **91 automated checks, 86 of
them green**, and was still incoherent. The checks verified that the right character's
mouth moved on the right line, that no faces melted, that no limbs multiplied, that every
voice landed on its timestamp. All true. Meanwhile the shot meant to show a bear driving
his shoulder into a jammed door showed a bear idly poking the wall with a stick, the door
never opened anywhere in the film, the rescued character never appeared on screen, and the
ending was four talking heads in a forest bragging about a rescue the audience never saw.

Every individual check passed. The film made no sense. **Technical QC cannot see story.**

So Story Forge grew a second kind of review — one that asks what a shot *depicts*, not
whether its pixels are clean. It runs entirely locally on Apple Silicon (MLX +
Qwen3-VL-32B 4-bit as the eyes, mlx-whisper as the ears) and it is wired in as a hard
stop, not a warning.

### The gates, cheapest first

| Gate | Question it answers | Where |
|---|---|---|
| **Beat gate** | Does this picture actually depict the beat the script says it is? | [`pipeline-tools/beat_gate.py`](pipeline-tools/beat_gate.py) |
| **Forbidden elements** | Is anything present that disqualifies the shot outright (a tool in the paws that should be empty, a relaxed pose where there should be strain)? | per-shot `must_not` in `beats.json` |
| **Identity gate** | Is this still the same character as the locked master — same head, ears, muzzle, colours? | [`bin/forge-shot`](bin/forge-shot) |
| **Set canon** | Is this the same *train* as the last scene, or did the model invent a new one? | `set_masters` in `beats.json` |
| **Story spine** | Are all the beats the film cannot exist without actually on screen — or was one never shot at all? | `spine` in `beats.json` |
| **Technical QC** | Right mouth moving on the right line, mouths shut in silence, no artifacts, every line audible on time | [`pipeline-tools/film_qc.py`](pipeline-tools/film_qc.py) |
| **Memory gate** | Can this machine actually afford this render, or will it swap-storm and panic? | `core.memory_gate()` / [`bin/mem-gate`](bin/mem-gate) |

### Four rules that make the review honest

**1. Judge blind first.** The model describes what is physically happening in the frame
with no knowledge of the intended beat — every body's posture and effort, every object in
or near their hands, anything unusual in the air. *Only then* does the beat go in for a
PASS/FAIL ruling. Told the answer up front, a vision model simply agrees with you. This
ordering is the difference between a check and a rubber stamp.

**2. One instant is not a verdict.** The same clip sampled at 1.1s and at 2.7s produced
opposite rulings — and days earlier, single-instant sampling had failed seven perfectly
good lip-sync clips. Every judgement now votes across multiple frames, majority rules, and
**every individual ballot is printed**. Nothing hides behind an average.

**3. Rejection reasons are fed back, and remembered.** Re-rolling a seed with the same
prompt is not learning; the same wrong picture returns with different noise. The judge says
*why* it failed in words — "the train is travelling normally with no visible signs of
distress" — and that sentence is appended to the next attempt as a correction, then
persisted to `shot_lessons.json` so a future run starts already knowing it. The mistake
gets paid for once.

**4. Nothing silently lowers a bar.** A shot that never passes is reported **UNBUILT**, not
quietly used. A clip that only partly holds its beat is trimmed to the stretch that does,
and the trim is declared. Failed clips are kept for diagnosis instead of deleted. Anything
the judge cannot assess is reported UNCHECKED — never as a pass.

### The self-proving shot builder

[`bin/forge-shot`](bin/forge-shot) is the loop those gates live inside. Per shot:

```
roll a seed → beat gate (majority vote) → identity gate vs locked master
   ↓ fail                                        ↓ pass
feed the reason into the prompt, roll again    LOCK (chmod 444)
   ↓ still failing after N cycles                ↓
report UNBUILT, lock nothing                  animate (memory-gated)
                                                 ↓
                                        re-judge the CLIP across its length
                                                 ↓ partial
                                        keep only the stretch that holds the beat
```

Cheap gates run before expensive ones on purpose. When this loop was built on Wan 2.2, a
still cost about a minute to roll and judge and animating it cost seventeen, so refusing a
bad shot at the still stage spent one minute instead of eighteen. LTX-2.5 has since cut the
animate to about a minute (see [the status below](#-status--2026-09-22)), so the gate saves
less clock than it used to. It still earns its place: a wrong picture never gets locked,
and a locked picture is what every later shot is held to.

### It gets better every film, not just every retry

Nothing learned is allowed to die with the project it was learned on.

- **`shot_lessons.json`** (per project) — why each specific shot was rejected, fed back into
  its next attempt.
- **`LESSONS.json`** (repo root, versioned, shipped) — the generalised version. Each entry
  carries the keywords it applies to, so a lesson earned on film #1 is matched against any
  future shot whose beat mentions the same things. Film #4 starts out knowing what films
  #1–3 paid to learn. Render tricks live here too, not just story mistakes — a faster
  sampler, a quant that held up, a resolution ladder that survived the quality gate.
- **`METRICS.jsonl`** (repo root, append-only) — every step's real duration and verdict.
  Which stage is the bottleneck is a measured number that accumulates across films, not a
  hunch. It is how the Wan-to-LTX-2.5 switch was decided: the animate step was 85% of a
  shot's time, so that is where the search for a faster engine went.
- **Speedups must earn their way in.** Any multiplier — quantisation, caching, step
  distillation, a hand-written kernel — has to clear [`bin/measure-render`](bin/measure-render),
  an LPIPS-gated harness: per-frame LPIPS < 0.05 **and** speedup > 1.10× or it doesn't ship.
  That's how a hand-written Metal flash-attention kernel ended up documented as a null
  result in [`metal/`](metal/) instead of quietly making renders worse.

Same discipline as the story gates: the pipeline is allowed to get faster and smarter over
time, but only in ways it can prove.

### The numbers, published as measured

First run of the beat gate over an existing "finished" episode: **2 of 11 shots passed.**
It found the stick in the door unprompted, describing it as "a small metallic object
embedded in the door." It failed the establishing shot that was supposed to read as trouble
("no visible signs of distress"). It failed the arrival for showing "a cheerful train that
appears to be running fine." It caught a character turning away from the door mid-clip. And
it failed two stills built the same night by the same author — which is the point.

Then, rebuilding the broken scene through `forge-shot`: three of four candidates passed the
beat, **two of those three failed the identity gate** for drifting off-model, and the one
that passed both got locked and animated — then the clip was trimmed to the 2.4-second
window where the gate votes 4/5 that the effort is real. Human verdict on the result:
*"looks like he's leaning in and trying to push a door open."*

That is the whole thesis. Not "the AI got it right." **The pipeline caught itself getting it
wrong, said so in numbers, and fixed it — on a laptop, offline.**

---

## The manifesto

We're not bound by what was taught. We don't accept upstream library defaults as the speed ceiling. We write our own software when the open-source one's wrong, we write our own DSL when JSON's too clumsy, we write our own Metal kernels when the vendor's path is slow.

Cloud companies will tell you AI cinema needs a server farm. It doesn't. It needs a laptop, a script, and somebody willing to read the source.

What the cloud charges $300-$1000 per film for, this pipeline does for the price of electricity. What people paid big data centers to run, we proved runs on a MacBook Pro on a kitchen table. Public firsts from this work:

1. LTX 13B distilled 0.9.8 working on Apple Silicon MPS
2. LPIPS-gated speedup harness for Mac video diffusion (CI-style regression gates on render quality)
3. 1-step Wan 2.2 i2v distillation on Apple Silicon — a rank-32 LoRA that collapses 4 denoising steps into 1 (see [`distill/`](distill/))

We also hand-wrote a Metal flash-attention kernel for Wan. Measured honestly, it was a wash — PyTorch's MPS SDPA is already too well-tuned to beat at our shapes — so it lives in [`metal/`](metal/) as a documented null result, not a win.

We make our own rules. We build new things constantly. We make possible what people said wasn't possible. That's the whole point.

### ▶ Watch the first Story Forge film — *The Bear Sister*

[![The Bear Sister — a Story Forge production](./hero-screenshot.jpg)](https://youtu.be/_bFQTl7_vF4)

[**▶ Watch on YouTube**](https://youtu.be/_bFQTl7_vF4) · [Download `saga.mp4`](./saga.mp4) · [Read the story (STORYBOOK.md)](./STORYBOOK.md)

---

### ▶ The Lucid Engine — a psychedelic sci-fi short

[![The Lucid Engine — a Story Forge film](./lucid-hero.jpg)](https://www.youtube.com/watch?v=31ZeFu-ePcc)

A ~4:30 short generated end-to-end on one laptop. No cloud. An uploaded mind, uncertain what's real, pieces together how the world ended and what it became — told across five acts (**The Waking → The Wrongness → The Truth → The Hunt → The Break → Resolution**) with a first-person narration spine, character dialogue with baked lip sync, same-location multi-angle coverage, a unified color grade, and an original Song Forge score under a low-drone / boom / shimmer sound-design bus.

[**▶ Watch on YouTube**](https://www.youtube.com/watch?v=31ZeFu-ePcc) · [Download `The_Lucid_Engine.mp4`](https://github.com/nicedreamzapp/story-forge/releases/tag/lucid-engine)

Pipeline at the time (June 2026): **Flux** (stills) → **LTX-2 distilled** (motion) → **Piper** (narration) → **ffmpeg** (grade, transitions, sound, mux). 100% local. It predates the review loop, the director and the current engines; a film made today goes through [the pipeline above](#-how-a-film-gets-made-now).

---

## 🎬 The Director UI — talk to it, get a movie (2026-07-22)

A chat + storyboard UI at `http://127.0.0.1:17600/` that puts
the whole formula behind a conversation. You tell it the movie you want; a
local LLM (any OpenAI-compatible server, `SF_LLM_URL`) locks the concept with
you — title, style, characters, mood — then fills a storyboard. Each scene card
then walks itself through the pipeline with a paper trail:

```
still (Flux) ─► vision-QC gate ─► approve & LOCK ─► draft i2v (~3 min, cheap gate)
                                                        │
                                                        ▼
                              final i2v (Wan 2.2) ─► score (ACE-Step, instrumental)
                                                        │
                                                        ▼
                                    assemble (xfade + music bed) ─► film_qc verdict
```

Design decisions that came from making real films, not from speculation:

- **Approve-and-lock per scene.** A locked scene can never be re-rendered by
  accident. Building one scene at a time, locking wins, is the only workflow
  that survived contact with actual production.
- **Cheap gates before expensive renders.** Every still faces a vision-model QC
  check (seconds) before you spend minutes animating it; a low-res draft render
  (~3 min) catches dead staging before the full render (~9 min). When the QC
  judge is offline the card says **unchecked** — it never fakes a pass.
- **film_qc has the last word.** The assembled film goes to
  [`pipeline-tools/film_qc.py`](pipeline-tools/film_qc.py) — a local
  vision-language judge plus whisper ears — and the UI reports its pass/fail
  counts verbatim.
- **A memory governor, not vibes.** Stages declare what they need before
  touching the GPU: queued stills batch together ahead of video renders so
  model weights load once, the 32B QC judge refuses to share the machine with
  resident video weights (it evicts an idle ComfyUI first), and stages wait for
  headroom instead of shoving the box into swap. One 128 GB machine runs image
  gen, video gen, music gen, an LLM director and a VL judge — sequenced, never
  stacked.
- **Drag your own images onto a card** to replace generated stills; re-roll
  anything unlocked with one click. The old single-clip page lives at `/classic`.
- **The loop closes itself.** Every approved still banks its recipe (style,
  prompt, seed, motion) into `projects/director/recipe_bank.json`, and the chat
  director reads a digest of proven recipes — wins compound instead of being
  re-derived per movie. On the verification side, film_qc failures that map
  inside a scene's core trigger an automatic re-roll of just that scene's
  animation (fresh noise, same locked still), re-assembly, and re-verification
  — up to two rounds — while crossfade-ghost flags (the judge seeing two scenes
  mid-blend) are classified benign instead of failing the film. You see the
  final verdict and a note of what was auto-fixed, not the broken intermediates.

Requirements beyond the base pipeline: a running ComfyUI for stills + i2v, an
OpenAI-compatible LLM server for the chat director, and optionally an ACE-Step
server (`SF_FORGE_URL`) for scores and a vision-judge server (`SF_PE_URL`) for
the still gate. All endpoints are env-overridable; see the top of
[`director.py`](director.py).

The UI still renders through ComfyUI (Flux stills, Wan 2.2 i2v). The newer engines —
Qwen-Image 2.1 stills and LTX-2.5 animation — and the beat and identity gates run through
`forge` / `forge-shot`, not through this page yet.

---

## 🚀 Status — 2026-09-22

What is true today, measured on one MacBook Pro (M5 Max, 128 GB) with Song Forge's paid music engines resident the whole time:

- ✅ **The gated pipeline runs a film end to end.** On the current film (*Circus Train*), the director has footage that passed review for 22 of 23 required beats (last status report, 2026-09-01). The one it could not build is reported UNBUILT with the reason, not papered over.
- ✅ **Animation moved to LTX-2.5** (distilled i2v, pure MLX, bf16, `--low-ram`) via [`bin/make-ltx25`](bin/make-ltx25): **~69 s** for a 5-second shot that took Wan 2.2 **13–16 minutes**, and it held a two-character composition Wan struggled with. Wan 2.2 (Q6_K GGUF by default) stays available per shot or per film.
- ✅ **Dialogue close-ups are conditioned on the real voice** (audio-to-video) instead of voice laid over prompted jaw motion — 41.7 s per close-up, film_qc 4/4.
- ✅ **Stills moved to Qwen-Image 2.1** (2026-09-20) after it beat FLUX.2 klein on a ten-style bake-off. Characters are held by passing each one's locked master in as a reference image, so identity comes from the same picture the identity gate checks against. Per-character LoRAs retired with klein.
- ✅ **The review loop** — beat gate, identity gate, set canon, story spine, EDL cross-check, spec lint — is wired in as hard stops (details above).
- ✅ **Motion transfer** — real footage drives a character through Wan 2.2 Animate (Q6_K GGUF).
- ✅ **Character voices** via ChatterBox (one cloned, one built-in, spares held for new characters); the narrator is **Kokoro-82M "Heart"**, which replaced Piper in August.
- ✅ **LTX 13B distilled 0.9.8 on MPS** — 118 s per 5-sec clip via `bin/make-ltx-lightricks`, still the B-roll engine on the `.sf` path. Likely the first public-confirmed working setup on Apple Silicon.
- ✅ **LPIPS-gated measurement harness** (`bin/measure-render`) and **1-step Wan distillation** ([`distill/`](distill/)) — unchanged.
- ➖ **Tried and deleted:** a hand-written Metal flash-attention kernel (a measurement artifact; kept in [`metal/`](metal/) as a documented null result) and ByteDance's Bernini-R reference-to-video (identity tied with LTX-2.5 on every measured axis at 25× the render time). Both are written up in [`RENDER_SPEED_RESEARCH.md`](RENDER_SPEED_RESEARCH.md).
- ⏳ **Not yet:** the Mac mini as a second render node (installed, not validated end to end); `forge-finish` as a stage in `build-episode`; bringing the Director UI onto the new engines.

---

## Quickstart

```bash
git clone https://github.com/nicedreamzapp/story-forge
cd story-forge
./bin/sf doctor                                    # what's missing, before you burn an hour
./bin/sf parse story_forge/examples/test_tiny.sf   # parser sanity (instant, no deps)
./bin/sf render story_forge/examples/test_tiny.sf  # ~2 min on an M5 Max
# output: ~/story-forge/outputs/test_tiny.mp4
```

`sf doctor` is the honest starting point. Story Forge is a glue layer, not a
self-contained model runtime, so it shells out to a few things that have to
exist on your machine first:

| what | needed for | how it's found |
|---|---|---|
| **ComfyUI**, running | every still | `SF_COMFY_URL`, default `http://127.0.0.1:8188` |
| **Flux** unet + CLIP + VAE, loaded in ComfyUI | every still on the `.sf` path | `SF_FLUX_UNET`, `SF_FLUX_CLIP1`, `SF_FLUX_CLIP2`, `SF_FLUX_VAE` |
| **ffmpeg / ffprobe** | assembling scenes | `PATH` |
| **Wan 2.2** and/or **LTX** in ComfyUI | motion | `bin/render-route` picks per scene |
| **piper** + an `.onnx` voice (or any piper-compatible CLI) | narration (optional) | `SF_PIPER`, `SF_PIPER_MODEL` |
| avatar pipeline (LivePortrait / Wav2Lip) | `with lipsync` on real human faces only (optional) | `SF_AVATAR_DIR` |

Model names must match what your ComfyUI actually lists, including subfolders.
If a still fails with *value not in list*, run:

```bash
python3 tools/flux_t2i.py --list-models
```

and set the `SF_FLUX_*` variables to names from that output.

Nothing in the repo points at an absolute home directory any more. Every path
resolves through `story_forge/config.py`: an `SF_*` environment variable if you
set one, otherwise a default inside this repo or a conventional `~/` location.

`test_tiny.sf` is a single scene, 3 seconds, no narration — the smallest
end-to-end loop. Once it produces an mp4, the heavier examples
(`cabin_open.sf`, multi-scene films) work the same way.

The `.sf` path above is the simple, portable one. The gated pipeline (`forge`,
`forge-shot`, `forge-director`) additionally expects mflux with Qwen-Image 2.1,
[ltx-2-mlx](https://github.com/dgrauet/ltx-2-mlx) for LTX-2.5, a Qwen3-VL-32B judge
(MLX) and mlx-whisper, and it still carries paths from the machine it was built on.
It is published so the method can be read and borrowed; expect to edit paths before it
runs anywhere else.

---

## Keyframe sandwich (FFLF) — opt-in, and measure before you trust it

The idea, from foxdit on r/StableDiffusion: plain image-to-video conditions on
frame 0 and lets the model invent the rest, so anchoring the **last** frame too
should stop a character drifting into someone else.

`still.end_prompt` draws the closing frame reusing the opening seed;
`still.end_path` uses an image you already trust. LTX only, since it is the
engine that takes a conditioning item at an arbitrary frame index. Wan i2v
conditions on the first frame alone and says so instead of ignoring it.

```
still flux:
    prompt:     "a lone hiker in a red jacket on a rocky ridge at sunset"
    end_prompt: "the same hiker further along the ridge, sun lower"
    seed: 42
motion ltx:
    prompt: "the hiker walks steadily along the ridge"
```

### What it measured here, honestly

On this stack — LTX 13B **distilled**, 7+3 multi-scale steps, 768x512, MPS — a
3s walking shot with a small human figure came out **worse with the anchor than
without it**. Same seed, same keyframes, three runs:

| end anchor | subject at the final frame |
|---|---|
| strength 1.0 | disintegrated into a smear |
| strength 0.7 | blurred, damaged, better than 1.0 |
| **none** | **intact, clean silhouette** |

The worst frame was always the anchored one. Told to be exactly somewhere at
frame N *and* to move, the sampler sacrifices the subject. So the feature is
**off unless you ask for it**, the default strength is 0.7 rather than 1.0, and
if you use it: keep the end frame a small delta from the start, and look at the
last frame before trusting the shot.

foxdit reports this working well on a 3090 running full-step models. Few-step
distilled inference is a different animal, and the table above is what it did
here, not what the technique is supposed to do.

Two other findings from the same tests, both larger than the anchor:

- **1216x704 collapses this config.** The image dissolved into colour bands by
  frame 24, and cost 316s against 82s. Stay at 768x512 with the distilled
  recipe.
- **Frame the subject bigger.** Every failure was a small figure in a wide
  shot. There are not enough pixels on a distant person to hold them together
  for 73 frames.

Directly: `bin/render-route --still A.png --last-frame B.png --label shot "…"`
Example: `story_forge/examples/keyframe_sandwich.sf`.

---

## Architecture

There are two ways in, and they share the renderers.

**The `.sf` script path** — simple, portable, what the Quickstart runs. You write a `.sf` script (or use the UI at `:17600/story`) and it goes straight through: a Flux still per scene, Wan or LTX motion routed per scene, narration placed per line, an ACE-Step score, one `ffmpeg` pass.

```
.sf script ──► parser ──► resolver ──► emitter ──► .storyplan.json IR
                                                          │
                                                          ▼
                                                    run.py bridge
                                                          │
                                                          ▼
                                          render-route (per-scene engine pick)
                                              │                       │
                                              ▼                       ▼
                                  make-ltx-lightricks         make-video --i2v
                                  (LTX 13B distilled)         (Wan 2.2 14B, GGUF)
                                              │                       │
                                              └───────────┬───────────┘
                                                          ▼
                                   narration (piper-compatible CLI) + ACE-Step (music + sfx)
                                                          │
                                                          ▼
                                                 ffmpeg stitch + mix
                                                          │
                                                          ▼
                                                      finished.mp4
```

- **`render-route`** auto-selects Wan (hero shots with character action / faces / dialogue) or LTX (B-roll / atmosphere / wide shots) per scene based on the motion prompt, or honors an explicit `motion wan:` / `motion ltx:` block in the DSL.
- **Narration + ACE-Step** run in parallel with the video renders, then `ffmpeg` does sidechain-ducked mixing and xfade stitching at the end.

**The `forge` path** — the gated one every film since July is made on. It takes a project folder (`beats.json` spine, `shots.json` specs, locked canon) instead of a single script, and runs the loop in [How a film gets made now](#-how-a-film-gets-made-now): Qwen-Image 2.1 stills, LTX-2.5 or Wan animation, every shot judged before it is kept, `build-episode` to assemble and `film_qc` to verify.

## The DSL grammar

Story Forge films are written as `.sf` scripts — indentation-aware, comment-friendly, stdlib-only parser. The full grammar as of 2026-05-24 (unchanged since; `piper/` voice presets render through whatever piper-compatible CLI `SF_PIPER` points at — our films use a Kokoro-82M shim):

```
# Comments start with '#' and go to end of line.

# --- Variables (substituted in any "{$name}" inside a string) ----
$style = "Studio Ghibli watercolor, soft snowfall, golden hour, painterly, 4k"
$child = "a small child in a red hooded cloak, mittens"
$cabin = "a hand-built wooden cabin with warm yellow window light"

# --- Film header (one per file) ----------------------------------
film "Cabin Open" slug=cabin_open target=m5+mini scene_dur=8.5

# --- Voice presets -----------------------------------------------
# voice <name>: <engine>/<model> <kv attrs>
voice warm:   piper/en_US-libritts_r-medium speaker=0 length=1.18
voice gravel: piper/en_US-libritts_r-medium speaker=14 length=1.05
voice child:  piper/en_US-amy-medium length=1.30

# --- Music presets -----------------------------------------------
# music <name>: <engine>/<style-slug> <kv attrs>
music wintry: ace/wintry-soft-piano vol=0.35

# --- SFX presets -------------------------------------------------
# sfx <name>: <engine>/sfx prompt="..." duration=N vol=0.NN
sfx fire_crackle: ace/sfx prompt="fire crackling, warm hearth" duration=8 vol=0.25
sfx wind_low:     ace/sfx prompt="low wind through pines" duration=10 vol=0.20

# --- Global directives -------------------------------------------
@transition xfade dur=0.5
@mix duck voice -> music threshold=-22 ratio=4

# --- Scenes ------------------------------------------------------
scene snow_walk:
    still flux:
        prompt: "{$style}, wide shot of {$child} crossing a snowfield toward {$cabin}"
        seed: auto                    # or an explicit int e.g. seed: 42
    motion wan:                       # or "motion ltx:" for B-roll
        prompt: "gentle handheld push-in, soft falling snow, child takes slow steps"
        duration: 5.0
    narrate warm:                     # full block form
        line: "The snow came down like a hush."
    sfx wind_low at=0.0               # per-scene SFX ref with offset
    music wintry vol=0.30             # per-scene music ref (overrides preset vol)

scene fireside:
    still flux:
        prompt: "{$style}, interior, {$child} unwrapping by a stone fireplace"
        seed: auto
    motion wan:
        prompt: "intimate close shot, firelight flickers, slow zoom to flames"
        duration: 5.0
    narrate warm with lipsync:        # human avatars only; never on stylized characters
        line: "And the cold outside became a story she would only tell on warm nights."
    sfx fire_crackle at=2.0
    music wintry vol=0.40
```

Constructs at a glance:

| Form | Purpose |
|---|---|
| `# comment` | Line comment, stripped before parse |
| `$name = value` | Variable, interpolated via `{$name}` in any string |
| `film "Title" slug=... target=... scene_dur=...` | Film header (one per file) |
| `voice NAME: piper/model speaker=N length=F` | Define a reusable voice preset |
| `music NAME: ace/style-slug vol=F` | Define a reusable music preset |
| `sfx NAME: ace/sfx prompt="..." duration=N vol=F` | Define a reusable SFX preset |
| `@transition xfade dur=0.5` | Global film-level directive |
| `@mix duck voice -> music threshold=-22 ratio=4` | Global mix directive |
| `scene NAME:` | Scene block (one per cut) |
| `still flux:` + `prompt:` / `seed:` | Per-scene Flux still spec |
| `motion wan:` or `motion ltx:` + `prompt:` / `duration:` | Per-scene i2v motion spec |
| `narrate VOICE:` + `line:` | Narration in this scene |
| `narrate VOICE with lipsync:` + `line:` | Same, plus a LivePortrait/Wav2Lip pass — for real human faces only; it paints a human mouth onto a cartoon, so our character films never use it |
| `sfx NAME at=N.N` | Per-scene SFX ref, `at=` is start offset in seconds |
| `music NAME vol=F` | Per-scene music ref, vol overrides preset |

The parser, resolver, and emitter live in [`story_forge/parser.py`](story_forge/parser.py), [`story_forge/resolver.py`](story_forge/resolver.py), and [`story_forge/emitter.py`](story_forge/emitter.py). The AST shape is documented in the parser docstring. Full reference example: [`story_forge/examples/cabin_open.sf`](story_forge/examples/cabin_open.sf).

---

## What's inside the repo

```
story-forge/
├── RULES.md                  # the rules the code enforces, in plain words
├── LESSONS.json              # house lessons, keyword-matched to every new shot
├── METRICS.jsonl             # every step's real duration and verdict, append-only
├── RENDER_SPEED_RESEARCH.md  # every speed/quality candidate, with a measurement
│
├── bin/
│   ├── forge                 # one command per film: new / resume / status / stop / list
│   ├── forge-director        # owns the film; loops until every beat has passing footage
│   ├── forge-shot            # the self-proving shot builder (still → gates → lock → animate → re-judge)
│   ├── forge-animatic        # story reel on locked stills, before anything is animated
│   ├── forge-review          # STATUS.md: what ran, what failed and why, what's next
│   ├── forge-finish          # bloom / colour grade / contrast for stills and clips
│   ├── build-episode         # preflight → score → cards → segments → assemble → QC
│   ├── make-ltx25            # LTX-2.5 (MLX, bf16) i2v and audio-to-video
│   ├── make-video            # Wan 2.2 14B i2v (Q6_K GGUF by default)
│   ├── make-motion-video     # Wan 2.2 Animate: a pose track drives a character
│   ├── motion_pose.py        # real video → pose track, with a QC sheet
│   ├── make-ltx-lightricks   # LTX 13B distilled 0.9.8 (the .sf path's B-roll engine)
│   ├── render-route          # per-scene engine picker (Wan vs LTX) for the .sf path
│   ├── mem-gate              # refuse heavy work the machine can't afford
│   ├── measure-render        # LPIPS-gated speedup harness
│   ├── character_voice.py    # ChatterBox character voices
│   └── sf                    # DSL CLI: sf doctor / sf parse / sf render
│
├── pipeline-tools/
│   ├── beat_gate.py          # does the picture depict the beat? (blind, then ruled)
│   ├── film_qc.py            # the last word: mouths, identity, artifacts, audio timing
│   ├── spec_lint.py          # refuse a spec that repeats a known mistake
│   ├── style_contract.py     # one locked paragraph of visual language per film
│   └── scene_audit.py, mouth_sync.py, clone_voice.py, …
│
├── story_forge/              # the .sf DSL: parser, resolver, emitter, run.py, packs, examples, tests
├── projects/                 # one folder per film: beats.json, shots.json, canon/, clips/, STATUS.md
├── director.py               # the chat + storyboard Director UI
├── server.py                 # Flask server for the UI (localhost:17600)
├── ui/                       # the web UI pages
├── metal/                    # the Metal flash-attention null result, documented
├── distill/                  # 1-step Wan distillation
├── build_status/             # live build dashboard (localhost:17602)
├── saga.mp4                  # the first film — The Bear Sister, 4:08
└── STORYBOOK.md              # full prose transcript of saga.mp4
```

## The first film — `saga.mp4`

To prove the pipeline, the first thing through it is a **two-act, 4:08 animated saga** called *The Bear Sister*. Act One is Studio Ghibli watercolor (a child rescued by a mother bear); Act Two is photoreal cinematic (the grown woman returning to find the bear family). One film, two visual languages, stitched with a fade-to-black bridge.

| | |
|---|---|
| **Runtime** | 4 min 8 sec |
| **Scenes** | 43 distinct |
| **Voices** | 1 Piper female (LibriTTS speaker 0), warm-EQ chain |
| **Music** | 2 ACE-Step instrumentals (Ghibli lullaby + cinematic homecoming) |
| **Compute hours** | ~12 hours (51 Wan i2v renders + parallel everything else) |
| **Hardware** | One MacBook Pro · Apple M5 Max · 128 GB unified memory |
| **Cloud calls** | **0** |

[▶ Watch on YouTube](https://youtu.be/_bFQTl7_vF4) · [Download `saga.mp4`](./saga.mp4) · [Read the full story (STORYBOOK.md)](./STORYBOOK.md)

---

## The story (transcript)

<details>
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

<details>
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

---

## Component stack

What a film made today runs on. Everything is local; weights are pulled at runtime and keep their own licenses ([CREDITS.md](CREDITS.md)).

| Stage | Model / tool | Notes |
|---|---|---|
| Still image per shot | [Qwen-Image 2.1](https://huggingface.co/Qwen) via [mflux](https://github.com/filipstrand/mflux), bf16 | Locked character masters passed in as reference images. The `.sf` path and the Director UI still use Flux 1 Dev through ComfyUI |
| Scene animation | [LTX-2.5](https://huggingface.co/Lightricks) via [ltx-2-mlx](https://github.com/dgrauet/ltx-2-mlx), distilled i2v, bf16 | ~69 s per 5-sec shot on the M5 |
| Scene animation (alternate) | [Wan 2.2 i2v 14B](https://huggingface.co/Wan-AI), Q6_K GGUF, in ComfyUI | 13–16 min per shot; the default where a film doesn't set `engine: ltx25` |
| Dialogue close-ups | LTX-2 distilled audio-to-video (mlx-video) | The video is conditioned on the actual voice take |
| Action from real footage | Wan 2.2 Animate, Q6_K GGUF | Pose track from a real performer |
| B-roll on the `.sf` path | [LTX-Video 13B distilled 0.9.8](https://huggingface.co/Lightricks) | 118 s/clip |
| Narrator | [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) "Heart" | Through a piper-compatible CLI, so the DSL's voice presets still work |
| Character voices | [ChatterBox](https://github.com/resemble-ai/chatterbox) | One voice per character, identity confirmed by ear once |
| Music + SFX | [Song Forge / ACE-Step](https://github.com/ace-step/ACE-Step) | Original score, ducked under dialogue |
| Eyes (every gate) | Qwen3-VL-32B, 4-bit, MLX | Beat gate, identity gate, film_qc |
| Ears | mlx-whisper | Every line audible at its planned moment |
| Compose + finish | [ffmpeg 8.1](https://ffmpeg.org/) + [Pillow](https://pillow.readthedocs.io/) | xfade, sidechain ducking, LUT grade, title and credit cards |

## The clever bits (what isn't in the YouTube tutorials)

### 1. Per-sentence narration + `adelay+amix` for scene-synced audio

Most pipelines `concat` narration lines into one block at t=0. By scene 4 the audio is two scenes ahead of the visuals.

Story Forge renders each narration line separately, then places it at its scene's onscreen start time via ffmpeg's `adelay`. All lines are then `amix`'d into a single track padded to full video duration. Audio and visuals stay in lock-step the whole film.

### 2. Warm storyteller EQ chain

Raw TTS output sounds flat. The narrator in Story Forge films runs through a deliberate signal chain:

```
highpass(80) → +2dB low-shelf @ 250Hz   (chest warmth)
             → -2dB high-shelf @ 7kHz   (soften sibilance)
             → compressor (-18dB threshold, 2.5:1 ratio)
             → aecho(60ms, 0.15)         (intimate room tail)
             → loudnorm I=-16 LUFS        (bedtime-story level)
```

The output reads as "a person telling you a story," not "an AI generating speech."

### 3. Music ducks under narration automatically

The instrumental score plays throughout the film at -22 LUFS bed level. When the narrator speaks, ffmpeg's `sidechaincompress` filter ducks the music ~10 dB, then releases back. Zero manual mix automation. Configurable in the DSL via `@mix duck voice -> music threshold=-22 ratio=4`.

### 4. Native-speed Wan, no slow-motion stretch

Many AI-video pipelines render 5-sec Wan clips and stretch them with `setpts*1.5` to fit longer scenes. Everything looks like dreamy slow-motion. Story Forge plays Wan at native 5-sec speed and uses more scenes instead — motion reads as real video.

### 5. xfade-based multi-act stitching

Combining two independently-rendered films into one saga uses `xfade=transition=fadeblack` between them (visual time-jump bridge) and audio gap handling for clean narration handoff. No editor required.

### 6. Per-scene engine routing

On the `.sf` path, `bin/render-route` picks Wan vs LTX automatically based on the motion prompt — hero shots with character action go to Wan, atmospheric B-roll goes to LTX (~5.6× faster). The DSL also lets you pin the engine explicitly with `motion wan:` or `motion ltx:`. On the `forge` path a film or a single shot sets `engine: ltx25` or leaves it on Wan.

### 7. The film watches itself — local QC judges (`pipeline-tools/film_qc.py`)

Generative pipelines fail silently: a character's body warps for one second of action, the wrong mouth moves on a line, scene 3's dog doesn't quite match scene 1's. You find out after you've shipped it — or your viewers do.

Story Forge now runs a **local judge stage** before any film counts as done. A vision-language model (Qwen3-VL) is shown frames pulled at every dialogue line's exact timestamp and asked *whose mouth is open*; it compares the same character across scenes for identity drift; it sweeps the whole film at 1-second intervals for deformities (merged bodies, extra limbs, smeared faces). Whisper transcribes the final mix and verifies every scripted line is audible within tolerance of its planned timestamp. Out comes a defect report with timestamps — pass/fail, no vibes.

It runs as three gates so failures die cheap: judge the stills and voice takes **before** animating (seconds), QC a small draft **before** committing to a long render (minutes), and QC each scene as it completes so a broken scene stops the queue instead of being discovered at final assembly. All of it on-device — the models that make the movie and the models that check it live on the same laptop.

---

## Roadmap — the 30× faster build-out

The goal set in May: a 4-minute film in minutes instead of hours. **Status updated 2026-09-22:**

| Multiplier | Target gain | Status |
|---|---|---|
| **LTX-2.5 distilled i2v for scene animation** | ~10× vs Wan per shot | ✅ **Shipped** — ~69 s vs 13–16 min, `bin/make-ltx25`. |
| **Audio-to-video dialogue close-ups** | (quality, and 6× vs the LTX-2.5 a2v path) | ✅ Shipped — 41.7 s per close-up, film_qc 4/4. |
| **LTX-Video 13B distilled 0.9.8 for B-roll** | 5.6× vs Wan | ✅ Working on M5 MPS — 118 s/clip via Lightricks' upstream multi-scale code. |
| **Batch by model, not by shot** | ~10–15% wall clock | ✅ `forge-shot --stage` locks every still first, then animates every locked still. |
| **Refuse bad shots at the still stage** | (saves whole animate runs) | ✅ The beat and identity gates. |
| **1-step Wan distillation** | 4× perpetual | ✅ Shipped — LPIPS 0.082 vs 0.206 wall (~2.5×), transfers to 256. See `distill/`. |
| **LPIPS-gated speedup harness** | (gate, not gain) | ✅ `bin/measure-render`. |
| **Custom Metal flash-attention kernel** | (null result) | ➖ Measurement artifact — MPS SDPA already wins at our shapes; kept in `metal/`. |
| **Bernini-R reference-to-video** | (identity) | ➖ Deleted — tied LTX-2.5 on identity at 25× the render time. |
| **Wav2Lip lip sync** | (feature) | ➖ Dropped for character films — it paints human mouths onto stylized faces. Audio-to-video replaced it. |
| **Q4_K_M GGUF Wan on the Mac mini** | a second render node | ⏳ Installed; M4 Pro runs ~40 min/clip vs the M5's ~10, and inference is not validated end to end. |
| **EasyCache (DiT-native cache)** | 1.1–1.3× at 4 steps | ⏳ Never measured; matters less now that LTX-2.5 replaced Wan as the main engine. |

### Benchmark to beat

**Liu Liu's Draw Things** (Apple-cited in the M5 launch) — ships Wan 2.2 on M-series and iPad M5 in a closed app. They're the speed reference on Mac. We're building the **open, measured, scriptable** equivalent — same speed bucket, with a DSL, a review loop and a harness no closed app provides.

---

## Why local

The whole thing is the point. A 4-minute video — an animated film, a narrated documentary cut, an ambient piece with an original score — runs on **one laptop you can carry in your bag**. No upload step. No "your queue position is 47." No subscription. No telemetry.

### What the cloud would actually cost

A film like *The Bear Sister* (4 minutes, 51 distinct Wan i2v clips) on cloud-equivalent services:

| Service | $ per 5-sec clip | 1-min film (~12 clips) | 4-min film (~51 clips) | 10-min film (~120 clips) |
|---|---|---|---|---|
| **OpenAI Sora** | $2.50 | $30 | $128 | $300 |
| **Runway Gen-3** | $4.00 | $48 | $204 | $480 |
| **Pika 2.0** | $2.00–$3.00 | $24–36 | $102–153 | $240–360 |
| **Luma Dream Machine** | $2.50 | $30 | $128 | $300 |
| **Kling AI** | $1.75 | $21 | $89 | $210 |
| **fal.ai LTX** *(cheapest cloud)* | $0.10 | $1.20 | $5.10 | $12 |
| **Story Forge (your machine)** | **$0.00** | **$0** | **$0** | **$0** |

Plus the cloud services charge **monthly subscriptions just to access**:
- Runway Pro: $35/mo
- Pika Pro: $35/mo
- Sora: ChatGPT Plus $20/mo minimum

A single 51-clip film with 5× iteration cycles during development = ~$640 on Sora. Story Forge does it for the cost of electricity ($0.20).

Hardware amortization: an M5 Max MacBook Pro + Mac mini M4 Pro (~$4,900 one-time) breaks even against Sora pricing at **~40 films**. After that, every render is pure profit — and you keep the hardware for everything else you do.

---

## Credits — first film

- Story by **Matt Macosko + Claude**
- Animation: Wan 2.2 i2v
- Stills: Flux 1 Dev FP8
- Narration: Piper LibriTTS
- Music: Song Forge / ACE-Step
- Rendered locally on a M5 Max MacBook Pro
- No cloud

*A Story Forge production.*

Whose work the whole pipeline is built on, with licenses, is in [CREDITS.md](CREDITS.md).

---

## Something not working?

Open an [issue](https://github.com/nicedreamzapp/story-forge/issues/new) with your Mac (chip and RAM), which stage failed, and the last lines of its log. It has mostly been run on one M5 Max, so reports from other machines are especially welcome.

---

## License

- **Pipeline code:** [MIT](LICENSE)
- **Films and other assets:** see [LICENSE-ASSETS.md](LICENSE-ASSETS.md) — *The Bear Sister* (`saga.mp4`) is [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/): share with attribution, don't sell
