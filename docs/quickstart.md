---
title: Quickstart - your first local AI video from a .sf script
description: Render a first video with Story Forge. Parse the bundled test_tiny.sf script, dry-run it without ComfyUI, then render a 3 second clip with Flux and LTX on an Apple Silicon Mac.
---

# Quickstart

This walks through the bundled smallest film, `story_forge/examples/test_tiny.sf`: one scene,
3 seconds, no narration. Do the [Install](install.md) steps first.

## 1. Look at the script

```text
film "Test Tiny" slug=test_tiny target=m5 scene_dur=3.0

scene drifting_clouds:
    still flux:
        prompt: "wide cinematic shot of distant mountain ridges at sunset, soft golden light, painterly atmosphere, 4k"
        seed: 42
    motion ltx:
        prompt: "slow ambient drift, light clouds move gently across the sky, gentle wind, no camera movement"
        duration: 3.0
```

A film is a header line, then scenes. Each scene has a `still` (the first frame) and a
`motion` block (what moves). The full syntax is on the [Configuration](configuration.md#the-sf-script-language) page.

## 2. Parse it (no models needed)

```bash
./bin/sf parse story_forge/examples/test_tiny.sf
```

This prints the parsed AST and the storyplan JSON. Parse errors exit with code 2 and resolve
errors with code 3. Add `--out plan.json` to write the storyplan to a file.

## 3. Dry run (no ComfyUI needed)

```bash
./bin/sf render story_forge/examples/test_tiny.sf --dry
```

This writes `story_forge/examples/test_tiny.storyplan.json` next to the script and prints the
pipeline config the renderer would get. Nothing is rendered.

## 4. Render

With ComfyUI running and `./bin/sf doctor` showing no `MISS` lines:

```bash
./bin/sf render story_forge/examples/test_tiny.sf
```

The script header says the target wall time is about 2 minutes on an M5. For each scene the
lean engine:

1. draws the still with Flux (or copies the image you gave with `still image:` and `path:`),
2. animates it through `bin/render-route`, which picks Wan or LTX,
3. conforms the clip to the target size and frame rate,
4. renders narration if the scene has any,
5. and stitches everything with ffmpeg.

Useful flags:

```bash
./bin/sf render my_film.sf --scenes intro,ending   # render only these scenes
./bin/sf render my_film.sf --out ~/Movies/my_film.mp4
./bin/sf render my_film.sf --engine full           # hand off to story_pipeline.py
```

!!! warning "Check the paths first"
    In the current code the lean renderer (`story_forge/run.py`) uses its own hard-coded
    locations for the Flux script, `render-route`, the narration voice and the work folder,
    not the `SF_*` variables that `sf doctor` checks. A render can fail even when
    `sf doctor` is clean. See
    [Troubleshooting](troubleshooting.md#sf-doctor-is-clean-but-sf-render-cannot-find-a-tool)
    for the exact paths.

## Where the files go

- The final video: the `--out` path, else `$SF_OUT_DIR/<slug>.mp4` (default
  `~/story-forge/outputs/<slug>.mp4`).
- Per-scene stills and clips (`still_01.png`, `raw_01.mp4`, `clip_01.mp4`, ...): the work
  folder, which `run.py` sets to `~/Desktop/AI Videos/<slug>/`.

## Next steps

- Copy an example and edit it. `story_forge/examples/` has `cabin_open.sf` (narration, music
  and ducking), `multi_voice.sf`, `sfx_demo.sf` and `styled_reel.sf` (style and format packs).
- Read [How it works](how-it-works.md) for the gated director pipeline (`bin/forge`), which
  judges every shot with local vision and audio models before it is kept.
