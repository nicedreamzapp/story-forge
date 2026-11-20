# V5 code-rendered shot

The whole shot is built from code: a path tracer written from scratch for the Metal GPU, and procedural triangle geometry. No AI image or video models are used, and nothing is downloaded for the scene.

## Re-render (one command, on the M5)

    cd ~/Desktop/PROJECTS/story-forge/projects/v5-code-render && ./render.sh

That builds the scene, compiles, renders 240 frames into `frames/` and encodes `v5-test.mp4`. Full 1080p at 256 spp takes about 8 min.

- Quick partial run: `SPP=32 FRAMES=0:24 ./render.sh`
- Brighter or darker: `EXPOSURE=1.3 ./render.sh`, window strength `LIGHT=14 ./render.sh`

## Change the camera

Pass key=value pairs after `./render.sh`. They override `cfg` in `scene.py` `main()`:

- `dist0=210 dist1=170` push-in start/end distance in mm
- `az0=-26 az1=-6` orbit start/end angle in degrees
- `h0=55 h1=38` camera height above the target in mm
- `fstop=4.0` depth of field (lower = shallower), `focal_mm=35` lens
- `handheld=0.8` drift amount in mm, `shutter=0.5` motion blur (fraction of a frame)
- `duration=10 fps=24 width=1920 height=1080`

Example: `./render.sh fstop=2.8 dist1=150 az1=10`

## Change the scene

- **The V5:** `build_v5()` in `scene.py`. Every size is in photo pixels from `reference/img0.jpg` (`ypx`/`rpx`, `PX` = mm per pixel).
- **The room:** `build_room()` in `scene.py` (table, walls, window, window light).
- **Materials:** the material block in `render()` in `pt.metal` (steel roughness/colour, glass, ceramic, wood). Wood grain comes from `wood_albedo()`.

## Files

- `scene.py` geometry and camera path, writes `scene.bin` and `cameras.txt`
- `pt.metal` GPU path tracer, a-trous denoise, film finish (ACES, vignette, grain)
- `render.mm` host: BVH build, GPU dispatch, PPM frames
- `render.sh` the one command
- `ETA.md` timing plan
- `reference/` the store photos used for modelling

## The dive shot (v5-dive, 15 s)

    ./dive.sh

This makes `v5-dive.mp4` (about 20 min). The camera path is the keyframe list `K` in `dive.py`: time, eye, target, focal, f-stop, roll. Heater warm-up is `heat()` and exposure is the `expo` line. Vapor density and colour are `vapor_density()` and `march_vapor()` in `pt.metal`. The cup glow is the `M_HOT` block in `render()`. Use `SPP_OUT=96 SPP_IN=48 ./dive.sh` for a quicker draft.

v1 of the product shot (its video, still and sources) is kept in `v1/` on the M5. The v2 product shot is `./render.sh` with `OUT=frames2 NAME=v5-test-v2.mp4`.

## Dive v2: rosin melt (v5-dive-v2, 16 s)

    ./dive2.sh

This makes `v5-dive-v2.mp4` (about 27 min).
- Camera path: keyframes `K` in `dive2.py`. The melt timeline is `melt()` (badder at 9.5 s, oil by 14.5 s).
- Rosin shape: `rosin_sdf()` in `pt.metal`. It covers the lump slump, the grain and the bubble domes (count, size, timing).
- Rosin colour: the `mat == 99u` block in `render()`, cream badder to clear pale-golden oil.
- Vapor wisps: `vapor_density()`. Heat shimmer: the `U.shimmer` block in `render()`.
- Rosin references: `reference/rosin/`.

## Dive v3: real V5 cup + rosin fix pass (v5-dive-v3, 16 s)

    ./dive3.sh

- The V5 ceramic cup is modelled from the store cup photos in `reference/cups/`: polished alumina, thin wall, flat rounded rim, deep body, heater-trace bands and the S-spiral floor trace. That's `build_v5()` in `scene.py` and the `M_HOT` block in `pt.metal`.
- The interior section looks straight down into the cup at f/45 with focus locked, 96 spp and a 5-pass denoise.
- A hidden fill ring (`M_FILL`) lights the cup. The camera never sees it directly.
- The rosin is `rosin_sdf()`: badder lump, golden oil with meniscus, suspended bubbles and surface pops.
