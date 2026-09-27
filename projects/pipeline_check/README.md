# Pipeline Check

A Story Forge project. **Story Forge is a general video system** — this project
can be any kind of video; cartoons are just one thing it does well.

- **Style:** Pixar-style 3D
- **Format:** 16:9 film (1280x720 @ 30fps)
- **Script:** `pipeline_check.sf`

## Render it
```bash
sf render projects/pipeline_check/pipeline_check.sf --out projects/pipeline_check/pipeline_check.mp4
```
The starter renders out of the box (every scene uses a Flux still prompt — no
assets required). Add `--dry` to print the plan without rendering, or
`--scenes opening,closing` to render a subset.

## Use your own art
Drop images in `stills/`, then in `pipeline_check.sf` replace a scene's `still flux:`
block with:
```
    still image:
        path: "{$stills}/your_frame.png"
```
The locked method: lay voice over the **untouched** animation. Never repaint
mouths.

## Cast voices
Drop cloned voice wavs in `voices/`. Use a cloned character voice in the script
with `voice doug: chatterbox/doug` (Doug = Matt's cloned voice). Built-in
narrator voices use `piper/...`.

## Change the look or shape
Edit the `film` line in `pipeline_check.sf`:
- `style=` one of: pixar-3d, flat-2d, photoreal, watercolor, anime, claymation, noir
- `format=` one of: film, reel, square, narrated-doc, cinematic

The style is appended to every Flux still prompt; the format sets the
dimensions and fps. List them anytime with `python3 -m story_forge.packs`.
