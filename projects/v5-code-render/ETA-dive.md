# ETA: v5-dive (15 s, 360 frames, 1920x1080, M5 Max)

Measured at full quality from the preview frames:
- outside, frame 60: 0.86 s at 192 spp
- inside the bore, frame 260: 5.7 s at 96 spp
- over the glowing cup with vapor, frames 320/345/350/355: 7.5 / 8.2 / 8.2 / 5.9 s at 96 spp

| Part | Predicted |
|---|---|
| Scene build + cameras + compile + BVH (634k triangles) | ~10 s |
| Outside frames 0-239 at 192 spp (~1.2-1.5 s avg, slower near the tip) | ~5-6 min |
| Inside frames 240-359 at 96 spp (~7 s avg) | ~14 min |
| Denoise (a-trous on the GPU, inside each frame's time) | ~20 s (included above) |
| ffmpeg encode 360 frames | ~45 s |
| **Total** | **~20 min** |

That's under the 30 min cap. Start: about 3:06 AM (M5 clock). Predicted finish: about 3:26 AM.
