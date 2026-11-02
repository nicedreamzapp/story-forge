# Upscale test 2026-11-02: SeedVR2-3B vs LTX-2.5 IC-LoRA Refine-Details

The idea came from u/DaLyon92x on r/LTXVideo: "Instead of seedvr2 it's worth a shot trying the Refine lora with ltx 2.5, which will actually get you the native 4k detail instead of deliverable." Matt approved the test at 12:54 AM. It ran on the M5 Max (128 GB) from 1:01 to 1:48 AM.

## The model
- `Lightricks/LTX-2.5-22b-IC-LoRA-Refine-Details`, file `ltx-2.5-22b-ic-lora-refine-details-1.0.safetensors`: bf16, rank 128, 1.3 GB. Its metadata says `model_version 2.5` and `reference_downscale_factor 1`.
- How it works: you lanczos-upscale the clip to the output canvas and feed that as the IC-LoRA reference. It runs on the distilled transformer with 8 steps at cfg 1. It was trained on 1024x576 tiles, and anything bigger is meant to be tiled with about 50% overlap, fused at every denoising step.
- License: LTX-2.x Community License. Companies above $10M revenue need a paid license. Clause 20 also bars products that compete with Lightricks' own offerings.
- The HF repo is gated with auto-approval. Our `divinetribe` account was approved by POSTing to `/<repo>/ask-access` with the token, so no browser was needed.

## Running it on MLX
- ltx-2-mlx upstream main (v0.18+, commit 747b30e) runs 2.5 IC-LoRAs. Our production checkout (0.15.1, which `bin/make-ltx25` uses) still marks ic-lora as 2.3-only. Upstream lives in a separate worktree, `~/Desktop/PROJECTS/ltx-2-mlx-main`, with its own `.venv`. Production was not touched.
- `ic-lora` has no spatial tiling in the CLI (upstream removed the `--tile-*` flags on purpose in #178). Our driver `tools/ltx25_refine_tiled.py` wraps the IC-LoRA transformer in ltx-2-mlx's own `TiledLTXModel`. That gives per-step fused tiles, and the appended reference tokens are kept per tile by coordinate. On a 1920x800 canvas that means a 3x2 grid of 992x544 tiles with about 50% overlap, single-stage, `--low-ram` block streaming.
- Prompt: the card's generic one ("sharp photographic detail, crisp natural texture, ... natural film grain, high resolution footage"). Seed 42.

## Clips
These are Last Signal v2 Kandinsky clips taken from the 832x348 scope crop: `00_c01_asteroids` (ship wide), `11_c07b_captain_face` (face) and `08_c06_monolith_reveal` (texture). SeedVR2 outputs were reused from the redo's `final/segs/up/`.

## Results
| path | output | clip | time | per output frame | peak memory |
|---|---|---|---|---|---|
| SeedVR2-3B fp16 720p (redo, reused) | 1720x720, then lanczos to 4K | asteroids 44 f / face 42 f / monolith 46 f | 558 / 552 / 604 s | ~12.7-13.1 s | 34 GB lease (not measured tonight, see note) |
| LTX-2.5 Refine, 6 fused tiles | 1920x800, then lanczos to 4K | 49 f each (3-7 padding frames) | 921 / 822 / 826 s | ~16.8-18.8 s | 56.2 GB Metal peak, 31 GB RSS (`--low-ram`) |
| LTX-2.5 Refine, 2nd pass at native 4K scale, one 1024x576 tile (face) | 1024x576 crop of the 4K frame | 49 f | 146 s | ~3 s per tile-frame | 22.5 GB |

Full-frame native 4K (3840x1600) would need about 42 tiles, roughly 7x the 1920x800 pass. That is about 95 min for a 2 s clip on this M5, so it doesn't fit the film budget.

Measured on the same 4K crops (frame 20, plus mean frame-to-frame change over 40 frames, where higher than the source means shimmer or boiling):
| clip | source | SeedVR2 | Refine |
|---|---|---|---|
| face | 3.76 | **5.77 (+53%)** | 3.66 |
| ship | 12.81 | 13.85 | 14.02 |
| monolith | 11.65 | **15.05 (+29%)** | 11.66 |

Face edge energy (crop): lanczos 1.69, Refine 2.13, SeedVR2 2.92.

## What I saw
- **Face:** SeedVR2 is the sharpest, but it invents texture. The skin cracks like dried mud, red rims appear around the eyes, contrast goes up, and the texture boils from frame to frame. Refine stays true to the source and steady over time but looks soft at 4K. The second Refine pass at native 4K scale adds real pores and skin texture while still looking natural. It's the best-looking face of the three, but too slow to run on full frames.
- **Ship:** SeedVR2 is crisper (clean panel edges, window grids). Refine is softer, with slightly smeared panel shapes. SeedVR2 wins.
- **Monolith glyphs:** SeedVR2 is crisper, but its texture shimmers (+29%). Refine is a little smudged but steady.

## Decision (Matt, 1:53 AM)
Matt watched the side-by-side: "The only one I can really tell was the lady's face. Her wrinkles on the first one look fake and AI, but the second one looks a lot better... more smoothed out and normal looking." He saw no difference on the ship or the monoliths. Now wired as `bin/upscale-route`: SeedVR2 for everything, Refine for faces and close-ups, lanczos under 0.9 s (06_assemble step 7, 04_shots step 5d). The dry run on Last Signal routes 18 shots to SeedVR2, 1 to Refine (the captain close-up, face 20.9% of the frame) and 29 to lanczos.

## Recommendation before the pick
- Keep SeedVR2-3B as the default for hard-surface and wide shots. Refine is ~35% slower per frame and softer on our 832x348 K6 sources. The LoRA was trained for about 2x upscales (1080p to 4K), and our sources need 4.6x.
- Refine is the better pick for faces and close-ups. It doesn't invent skin, and it doesn't boil. If Matt agrees, the next step is a per-shot router: face and close-up cuts go through Refine at about 2x, wides and hard surfaces through SeedVR2. A Refine second pass at 4K only pays off on a single hero tile, since a full frame costs about 95 min.
- The reverse experiment is worth trying later: Refine at 1920x800, then SeedVR2 at low strength. Not tested.

## Note on tonight's reboot
The M5 hit a watchdog panic at 12:20 AM (`panic-full-2026-11-02-002040`). The snapshot shows one Python process at 110.9 GB resident plus Song Forge's ~34 GB and only 892 free pages. That was during the Last Signal redo's SeedVR2 step on segment 14 (`13_c09_welcome`). The process name in the snapshot is only "Python", so it is most likely SeedVR2 but not proven. SeedVR2's 34 GB lease does not cap what it really uses.

The test outputs were deleted after Matt picked (frozen rule 13). This doc and the LESSONS entries are what's kept.
