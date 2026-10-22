---
title: Configuration reference - flags, environment variables and .sf syntax
description: Every Story Forge option read from the source code. sf CLI flags, forge and forge-shot options, SF_* environment variables, memory gate settings, the .sf script language, style and format packs, and the web UI server.
---

# Configuration

Everything on this page was read from the source. File and line references point at the code
on `main` as of October 2026. Where the code does something other than what its comments or
the README say, the page documents what the code does and marks it **TODO-VERIFY**.

!!! warning "Read this first: which settings a render actually uses"
    `story_forge/config.py` defines the `SF_*` path variables, and `sf doctor` checks them.
    But the lean renderer, `story_forge/run.py`, does not import that module. It has its own
    hard-coded, home-relative paths (`run.py` lines 58 to 81). So today the `SF_*` path
    variables change what `sf doctor` reports and where `sf render` writes its output
    (`SF_OUT_DIR`), and nothing else. The table under
    [Environment variables](#environment-variables) says which variable reaches which code.
    TODO-VERIFY: whether `run.py` should go back to reading `config.py`, as it did after
    commit `e837143` (July 20, 2026) and before commit `44e923b` (August 30, 2026).

## `sf`: the `.sf` script CLI

`bin/sf` (Python, argparse). A subcommand is required.

| Command | Flag | Default | What it does |
|---|---|---|---|
| `sf doctor` | | | Checks every external piece a lean render needs. Exit code 1 if a required one is missing. |
| `sf parse FILE.sf` | `--out PATH` | none | Prints the AST and the storyplan JSON. `--out` also writes the storyplan to `PATH`. |
| `sf render FILE.sf` | `--dry` | off | Writes `FILE.storyplan.json` next to the script and prints the renderer config. Renders nothing. |
| | `--out FILE.mp4` | `$SF_OUT_DIR/<slug>.mp4` | Output path. `<slug>` is the film's `slug`, else the file name. |
| | `--scenes a,b,c` | all scenes | Render only these scenes. An unknown name is an error. |
| | `--engine lean\|full` | `lean` | `lean` renders scene by scene in `run.py`. `full` pipes the config to `story_pipeline.py` (see [below](#story_pipelinepy-the-full-engine)). |

Exit codes: `2` for a parse error, `3` for a resolve error (for example an undefined
`{$variable}`).

`story_forge/run.py` can also be run directly on a storyplan:
`python3 story_forge/run.py PLAN.storyplan.json [--dry] [--engine lean|full] [--out PATH] [--scenes a,b]`.

## The `.sf` script language

Source: `story_forge/parser.py`, `resolver.py`, `emitter.py`, and `run.py` for what the
renderer actually uses. Examples live in `story_forge/examples/`.

### Basics

- Blocks are set by indentation. A tab counts as 4 spaces.
- `#` starts a comment, except inside quotes.
- Values are typed: quoted text is a string; `true`/`yes`/`on` and `false`/`no`/`off` are
  booleans; `none`/`null` is empty; numbers are ints or floats; anything else is a string.
- `$name = value` defines a variable. Use it inside strings as `{$name}`. An undefined name
  is a resolve error.
- `key=value` pairs can follow most block heads.

### `film`

```text
film "Cabin Open" slug=cabin_open scene_dur=8.5 style=watercolor format=reel
```

| Attribute | Default | Used by the lean renderer |
|---|---|---|
| title (first quoted value, or `title=`) | `Untitled` | yes |
| `slug` | `untitled` | yes: output and work folder names, and seeds |
| `scene_dur` | `8.5` (or the format pack's value if the script does not set it) | yes, as the fallback clip length |
| `style=<pack>` | none | yes: appends the pack's text to every Flux still prompt |
| `format=<pack>` | none | yes: still size, output size and fps |
| `target` | `m5` | no |
| anything else | | stored in `film_meta.extras`, not used |

An unknown `style` or `format` name is an error.

### Presets: `voice`, `music`, `sfx`

```text
voice warm:  piper/en_US-libritts_r-medium speaker=0 length=1.18
voice hank:  chatterbox/hank
music wintry: ace/wintry-soft-piano vol=0.35
sfx creak: prompt="old wooden door creak" duration=2 vol=0.5
```

- The **first** `voice` declared is the default narrator.
- In the lean renderer, a voice value of `chatterbox/<character>` sends the line through
  ChatterBox (`bin/character_voice.py --character <character>`). Any other value uses the
  renderer's fixed narration voice; the model named after `piper/` is not read.
  Attributes read: `length` (speech length scale, default 1.10) and `speaker` (default 0).
  TODO-VERIFY.
- `music` and `sfx` presets, and scene-level `music`/`sfx` references, are parsed and kept in
  the storyplan, but the lean renderer does not mix music or sound effects. TODO-VERIFY.

### Directives

```text
@mix duck voice -> music threshold=-22 ratio=4
@transition xfade duration=0.5
```

Both are parsed into the storyplan. The lean renderer ignores them: it always uses a 0.5
second crossfade between scenes and has no music to duck. TODO-VERIFY. Any other `@name`
line is stored as a transition.

### `scene`

```text
scene snow_walk:
    still flux:
        prompt: "{$style}, a child in a red cloak crossing a snowfield"
        seed: 42
    motion wan:
        prompt: "gentle push-in, soft falling snow"
        duration: 5.0
    narrate warm:
        line: "The snow came down like a hush."
    music wintry vol=0.30
```

A scene name is required. Extra attributes on the scene line, and loose `key: value` lines
inside it, are stored but not used by the renderer.

**`still flux:`** or **`still image:`**

| Key | Meaning |
|---|---|
| `prompt` | Flux prompt. The style pack's suffix is appended. |
| `path` (or `image`) | Use this existing image instead of drawing one. Checked first. `~` is expanded. |
| `seed` | Integer, or `auto` (a hash of film slug, scene name and block). If missing, `run.py` uses `1000 + 17 × scene number`. |
| `end_prompt`, `end_path`, `end_seed` | The "keyframe sandwich" (anchor the last frame). Parsed, but **ignored by the current renderer**. See [Troubleshooting](troubleshooting.md#test_keyframespy-fails). |

A scene with neither `prompt` nor `path` fails with
`scene <name>: needs still.prompt (flux) or still.path (image)`.

**`motion wan:`** or **`motion ltx:`** (any other engine name means `auto`)

| Key | Meaning |
|---|---|
| `prompt` | Motion prompt. Falls back to the still prompt. |
| `duration` | Seconds. Falls back to the film's `scene_dur`. |
| `seed` | Resolved into the storyplan, but not passed to the renderer. |

`auto` lets `bin/render-route` choose: motion prompts with words like *face, talks, walks,
grabs, reaches* go to Wan; words like *wind, snow, fog, distant, wide, establishing* go to LTX;
anything else goes to Wan.

**`narrate <voice>:`**

```text
narrate warm:
    line: "The snow came down like a hush."
narrate warm: "An inline line works too."
narrate host with lipsync=wav2lip:
    line: "Real human faces only."
```

A scene can have several `narrate` blocks. Each line is placed at its scene's start time in the
final mix. `with lipsync` (or `with lipsync=lp`) renders a LivePortrait talking head from the
driver still; `with lipsync=wav2lip` adds a Wav2Lip mouth pass. The head is overlaid in the
bottom right at 30% of the frame width, 32 px from the edges, with a 0.05 second fade in. The
README is clear that this is for real human faces only, never cartoon characters.

### Lean renderer defaults

When no format pack is set: stills at 768x512, clips conformed to 1280x720 at 30 fps, a 0.5
second crossfade between scenes. Per-scene files go to `~/Desktop/AI Videos/<slug>/`
(hard-coded in `run.py`).

### Style and format packs

Source: `story_forge/packs.py`. List them with `python3 -m story_forge.packs`; the web UI gets
them from `GET /api/packs`.

**Styles** (`style=`): `pixar-3d`, `flat-2d`, `photoreal`, `watercolor`, `anime`, `claymation`,
`noir`. Each adds a `still_suffix` to Flux prompts. Each also defines a `negative` prompt,
which the lean renderer does not use.

**Formats** (`format=`):

| Name | Size | fps | Aspect | Default `scene_dur` |
|---|---|---|---|---|
| `film` | 1280x720 | 30 | 16:9 | 5.0 |
| `reel` | 720x1280 | 30 | 9:16 | 5.0 |
| `square` | 1080x1080 | 30 | 1:1 | 5.0 |
| `narrated-doc` | 1280x720 | 30 | 16:9 | 8.0 |
| `cinematic` | 1280x536 | 24 | 2.39:1 | 6.0 |

A format is only applied when the script asks for one.

## Environment variables

### Read by `sf doctor` and `config.py`

| Variable | Default | Effect today |
|---|---|---|
| `SF_COMFY_URL` | `http://127.0.0.1:8188` | ComfyUI address for `tools/flux_t2i.py` and the doctor check |
| `SF_OUT_DIR` | `~/story-forge/outputs` | Default `sf render --out` folder |
| `SF_FLUX_SCRIPT` | `<repo>/tools/flux_t2i.py` | Doctor check only (`director.py` also reads it) |
| `SF_RENDER_ROUTE` | `<repo>/bin/render-route` | Doctor check only |
| `SF_PIPER` | `piper` on `PATH`, else `~/.local/bin/piper` | Doctor check only |
| `SF_PIPER_MODEL` | `~/piper_voices/en_US-libritts_r-medium.onnx` | Doctor check only |
| `SF_CHATTERBOX_PY` | `~/chatterbox-env/bin/python` | Doctor check only |
| `SF_CHARACTER_VOICE` | `<repo>/bin/character_voice.py` | Not used by the renderer |
| `SF_AVATAR_DIR` | `~/avatar-pipeline` | Doctor check only |
| `SF_DRIVER_STILL` | `<repo>/assets/walk_frame.png` | Not used by the renderer |
| `SF_VIDEOPIPE` | the repo root | Not used by the renderer |
| `SF_WORK_DIR` | `~/story-forge/work` | Not used anywhere |

### Image stage (Flux through ComfyUI)

Read by `tools/flux_t2i.py`. The names must match what ComfyUI lists, including any subfolder.
Run `python3 tools/flux_t2i.py --list-models` to see yours.

| Variable | Default |
|---|---|
| `SF_FLUX_UNET` | `flux/flux1-dev-fp8.safetensors` |
| `SF_FLUX_CLIP1` | `clip_l.safetensors` |
| `SF_FLUX_CLIP2` | `t5xxl_fp16.safetensors` |
| `SF_FLUX_VAE` | `flux/ae.safetensors` |
| `SF_FLUX_STEPS` | `20` |

`flux_t2i.py` flags: `prompt`, `--out FILE`, `--w` (1280), `--h` (720), `--seed`,
`--list-models`.

### Lean renderer (`story_forge/run.py`)

| Variable | Default | Effect |
|---|---|---|
| `LIPSYNC_DRIVER_STILL` | `~/AI/videopipe/test_stills/walk_frame.png` | Face image for `with lipsync` |
| `STORY_FORGE_SKIP_AVATAR` | unset | `1` makes a placeholder head clip instead of running the avatar pipeline (used by tests) |

### Motion engines

| Variable | Read by | Default | Effect |
|---|---|---|---|
| `SF_LTX_PYTHON` | `bin/render-route` | `~/AI/ComfyUI/venv/bin/python` | Python used to run `bin/make-ltx-lightricks` |
| `SF_LTX25_PACK` | `bin/make-ltx25` | newest local Hugging Face snapshot of `dgrauet/ltx-2.5-mlx` | LTX-2.5 model folder |
| `SF_ANIMATE_ENGINE` | `bin/forge-shot` | unset (Wan) | `ltx25` sends animation to `bin/make-ltx25` |
| `COMFY_URL` | `core.py`, `bin/forge-shot` | `http://127.0.0.1:8188` | ComfyUI address for the Wan workflows |
| `VIDEOPIPE_OUT` | `core.py` | `~/AI/videopipe/outputs` | Where `core.py` and the web UI keep renders |

### Memory gate and scheduling (`core.py`)

| Variable | Default | Effect |
|---|---|---|
| `SF_MEM_GATE` | `1` | `0` disables the memory gate and model eviction. It prints `[mem-gate] DISABLED via SF_MEM_GATE=0 — you are on your own`. |
| `SF_MEM_GATE_MIN_FREE` | `30` | Minimum free memory, in percent, before a heavy step may start |
| `SF_MEM_GATE_MAX_SWAP_GB` | `8` | Swap use above this triggers a restart of an idle ComfyUI to release memory |
| `SF_MEM_GATE_MAX_WAIT` | `900` | Seconds to wait for memory before refusing |
| `SF_COMFY_START_CMD` | starts `./venv/bin/python main.py --listen` in `~/Desktop/PROJECTS/AI/ComfyUI` or `~/AI/ComfyUI` | Command used to restart ComfyUI |
| `SF_STAGE_HEADROOM_GB` | `12` | Extra GB added to a stage's memory need |
| `SF_MODEL_OVERHEAD` | `1.2` | Multiplier on a model's size when budgeting memory |
| `PE_URL` | `http://127.0.0.1:8181` | Local vision server that may be unloaded to make room |
| `SONGFORGE_URL` | `http://127.0.0.1:8767` | Song Forge. Its customer jobs take priority over renders. |
| `SF_CUSTOMER_POLL_S` | `20` | Seconds between checks for Song Forge customer jobs |
| `SF_STILL_GB` / `SF_ANIMATE_GB` | `48` / `46` | Memory reserved by `forge-shot` for the still and animate phases |

The gate fails when macOS reports memory pressure above normal or free memory is below
`SF_MEM_GATE_MIN_FREE`. It re-checks every 30 seconds until `SF_MEM_GATE_MAX_WAIT`.
`bin/mem-gate [label]` runs the same check from a shell and exits 1 on refusal.

### Director (`bin/forge-director`, `director.py`)

| Variable | Default | Effect |
|---|---|---|
| `SF_MAX_UNBUILT_ATTEMPTS` | `2` | Attempts before a beat is given up as unbuilt |
| `SF_DRY_HOURS` | `2` | Hours without a kept clip before the director stands down |
| `SF_LLM_URL` | `http://127.0.0.1:9420/v1/chat/completions` | Local chat model for the Director UI |
| `SF_CHAT_MODEL` | `mlx-community/gemma-3-12b-it-4bit` | Model name sent to it |
| `SF_FILM_QC` | `<repo>/pipeline-tools/film_qc.py` | QC script path |
| `SF_QC_PYTHON` | the current Python | Interpreter for QC |
| `SF_COMFY_START` | empty | ComfyUI start command for the Director UI |
| `SF_PE_URL`, `SF_FORGE_URL`, `SF_SELF_URL` | `:8181`, `:8767`, `http://127.0.0.1:17600` | Local service addresses |
| `SF_VOICES_DIR` | `<repo>/voices` | Reference clips for cloned character voices (`pipeline-tools/character_voice.py`) |

### Web UI and queue

| Variable | Read by | Default | Effect |
|---|---|---|---|
| `PORT` | `server.py` | `17600` | Web UI port (binds to `127.0.0.1`) |
| `SF_ENGINE` | `queue/runner.py` | `lean` | Engine for queued renders |
| `SF_PUBLISH` | `queue/runner.py` | off | `1` publishes finished queue renders |
| `SF_MEM_FLOOR` / `SF_MEM_KILL` / `SF_SWAP_KILL` | `queue/runner.py` | `60` / `14` / `8` GB | Queue watchdog limits |

`server.py` also sets `SF_USE_MINI_Q4`, `SF_QUALITY_GATE` and `SF_VOICE_CLONE` for `.sf` renders
started from the UI, but no code reads them. TODO-VERIFY.

### Optional cloud backup

`bin/make-ltx-cloud` reads `FAL_KEY` and sends one image-to-video job to fal.ai. Nothing else in
the repo calls it; the pipeline itself never uses it.

## The gated pipeline tools

### `bin/forge`

```bash
./bin/forge new "a documentary about the harbour" --kind doc
./bin/forge "hank and doug"      # fuzzy-matches a project and resumes it
./bin/forge status               # also: list
./bin/forge stop
```

| Flag | Default | Effect |
|---|---|---|
| `--kind` | `animated` | Kind of film for `new` |
| `--hours` | `8` | Hours the keepalive will keep the director running |

No argument means `status`. `new` creates `projects/<slug>/` with a `shots.json` whose defaults
are 832x480, 5 second clips, seeds `[11, 47, 82, 119]` and 3 votes. `stop` writes a
`STOP_DIRECTOR` marker and stops the director process.

### `bin/forge-director`

`forge-director PROJECT [--max-hours 8.0] [--dry-run]`. Fixed limits in the code: 4 attempts
per beat, 3 infrastructure failures, 5 held strikes.

### `bin/forge-shot`

`forge-shot SHOTS.json [--only ID ...] [--stage all|stills|animate] [--dry-run]`.
`--only` can be repeated. `--stage animate` uses the locked still instead of re-rolling it.

`shots.json` keys, from the code:

- `defaults`: `res` (`832x480`; read only from defaults), `seeds` (`[11,22,33,44]`), `votes`
  (3), `retry_cycles` (2), `duration` (5), `engine` (`wan` or `ltx25`).
- Per shot: `id`, `prompt`, `beat`, `must_not`, `identity`, `refs`, `lock`, `animate`, `clip`,
  `min_window` (2.0 s), `init`, `denoise` (0.45), `negative`, `loras`, `seeds`, `votes`,
  `retry_cycles`, `engine`, `duration`, `clip_beat`, `allow_text`, `talk`.

Engine order: `SF_ANIMATE_ENGINE`, then the shot's `engine`, then `defaults.engine`, then Wan.
It writes `forge_shot_results.json`, `forge_shot.log` and `shot_lessons.json`.

### `bin/build-episode`

`build-episode PROJECT [--from preflight|song|cards|segments|assemble|qc] [--no-song]`.
`--from` re-runs from that stage. Output is 832x480 at 24 fps with 44.1 kHz audio. State is
kept in `build_state.json`.

### `bin/forge-finish`

`forge-finish SRC [OUT] [--look golden|blacklight|moonlight|clean] [--bloom N] [--grade N] [--contrast N] [--saturation N]`.
Default look `golden`; the numeric flags override the look. `OUT` defaults to
`<src>_finished.<ext>`.

| Look | bloom | grade | contrast | saturation |
|---|---|---|---|---|
| `golden` | 0.25 | 0.12 | 0.35 | 1.12 |
| `blacklight` | 0.55 | 0.35 | 0.40 | 1.15 |
| `moonlight` | 0.30 | 0.30 | 0.25 | 0.95 |
| `clean` | 0.25 | 0 | 0.25 | 1.05 |

### Other tools

| Tool | Usage |
|---|---|
| `bin/forge-animatic PROJECT` | Story reel from the locked stills, `ANIMATIC.mp4`, 832x480 at 24 fps. No audio in the current code. |
| `bin/film-status [FILM] [--all] [--init]` | Which `pipeline/` stage a film is in. `--init` stamps a new film from `_templates/film/`. |
| `bin/story-new NAME [--style S] [--format F] [--scenes 1-4] [--dir D] [--force]` | Scaffolds a project with a starter `.sf`. Default `--dir` is `~/Desktop/PROJECTS/AI/videopipe/projects`. |
| `bin/render-route PROMPT --still S.png [--last-frame E.png] [--duration 5] [--res WxH] [--label L] [--engine wan\|ltx\|auto] [--tag hero\|broll\|auto]` | Picks Wan or LTX for one shot. Default res: Wan 832x480, LTX 768x512. `--last-frame` forces LTX unless `--engine wan` is given. |
| `bin/make-video PROMPT [--i2v IMG] [--hq] [--duration 5] [--res 1280x720] [--gguf] [--seed 0] ...` | One Wan 2.2 clip through ComfyUI. 16 fps. |
| `bin/make-ltx25 PROMPT [--i2v IMG] [--audio WAV] [--duration 5] [--res 832x480] [--low-ram] [--gb 45] ...` | One LTX-2.5 clip through ltx-2-mlx, 24 fps. `--audio` makes the video from a voice recording. `--res` must be multiples of 32. |
| `bin/mem-gate [LABEL]` | Runs the memory gate; exit 1 on refusal. |

## Web UI server (`server.py`)

A Flask app on `http://127.0.0.1:17600` (`PORT` to change). Main pages: `/` (index),
`/story` (the `.sf` editor), `/story-classic`, `/review` (human review queue), `/pulse` (live
pipeline step), `/short`.

| Route | Purpose |
|---|---|
| `POST /api/render` | One Wan clip from a prompt and optional uploaded image; or, with an `sf` field, runs `bin/sf render` on the script |
| `GET /api/render/<id>/status` | Status and log tail of a `.sf` render |
| `POST /api/story` | Runs `story_pipeline.py` with the posted config |
| `GET /api/estimate` | Time and memory estimate (`duration`, `quality`, `resolution`, `big_mode`) |
| `POST /api/upload` | Sends an image to ComfyUI |
| `GET /api/status/<id>`, `POST /api/cancel/<id>` | Status and cancel for a single clip job |
| `GET /api/output/<name>`, `GET /thumb/<name>.jpg` | Serve a render and its thumbnail |
| `GET /api/recent`, `GET /api/recent_renders` | Recent renders |
| `GET /api/packs` | Style and format packs |
| `GET /api/example/<name>` | Text of a bundled example script |
| `GET /api/live`, `GET /build_status/live.json`, `GET /api/pulse`, `GET /api/short-status` | Live status feeds |
| `GET /api/review/queue`, `GET /api/review/clip/<id>`, `POST /api/review/verdict` | Human review of clips (`{id, verdict: yes\|no, note}`) |
| `POST /api/kill_all` | Kills ComfyUI (`pkill -9 -f main.py`) |
| `POST /api/reveal/<name>` | Shows a file in Finder |
| `POST /api/sf_render` | Renders a posted script. TODO-VERIFY: it passes the resolver output to `run.py`, which expects a storyplan with `film_meta`, so it likely fails. |

## `story_pipeline.py` (the full engine)

The older full pipeline, reached by `sf render --engine full` or `POST /api/story`. It reads a
JSON config from `--config PATH` or stdin:

| Key | Default | Notes |
|---|---|---|
| `slug` | required | |
| `title` | `Untitled` | |
| `scenes` | required | list of `{still, motion, narration}` |
| `scene_duration` | 8.5 | |
| `voice` | `warm_female_storyteller` | any other value means no narration |
| `overlays.dust_all` | false | |
| `overlays.film_grain` | true | |
| `overlays.vignette` | true | |
| `overlays.snow_scenes`, `fireflies_scenes`, `aurora_scenes`, `blossom_scenes` | none | lists of scene numbers |
| `overlays.chapter_grades` | none | `{"<scene number>": preset}`, presets `winter`, `dawn`, `cave`, `cosmic`, `spring`, `neutral` |

Its docstring also lists `style` and `character`, and `run.py` sends per-scene seeds and
durations, but the code does not read them: seeds are fixed at `73 + 17 × i` and clips at 5
seconds, 832x480. TODO-VERIFY. Note that `sf render --engine full` runs the copy of
`story_pipeline.py` at `~/Desktop/PROJECTS/AI/videopipe/`, not the one in the clone.
