# ETA: v5-dive-v2, rosin melt (16 s, 384 frames, 1920x1080, M5 Max)

Measured at full quality from the preview frames:
- outside, frame 60: 0.89 s at 192 spp
- outside, frame 100: 1.31 s at 192 spp
- bore, frame 190: 3.4 s at 64 spp
- badder lump, frame 268: 6.4 s at 64 spp
- melt with bubbles and wisps, frames 310/320/360: 9.6 / 10.0 / 10.2 s at 64 spp

The full run uses 48 spp inside: about 0.75x of those times.

| Part | Predicted |
|---|---|
| Scene build + cameras + compile + BVH (~720k triangles) | ~10 s |
| Outside frames 0-164 at 192 spp (~1.1 s avg) | ~3 min |
| Bore frames 165-215 at 48 spp (~2.6 s) | ~2.2 min |
| Chamber + melt frames 216-383 at 48 spp (~7.3 s) | ~20.5 min |
| Denoise (a-trous on the GPU, inside each frame's time) | ~25 s (included above) |
| ffmpeg encode 384 frames | ~1 min |
| **Total** | **~27 min** |

That's under the 35 min cap. The M5 was checked at 3:41 AM: no heavy job running (Brave helper ~57% CPU, nothing training).
Start: about 3:42 AM (M5 clock). Predicted finish: about 4:09 AM.
