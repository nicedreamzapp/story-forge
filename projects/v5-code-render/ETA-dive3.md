# ETA: v5-dive-v3, real V5 cup + rosin (16 s, 384 frames, 1920x1080, M5 Max)

Measured 10:24 AM, with training finished. The Song Forge API server (PID 64265) was running but idle.
- full-quality interior frame 330 (oil, bubbles, wisps): 11.3 s at 96 spp, 5-pass denoise
- earlier previews: badder frame 250 ~6.5 s; outside ~1.25 s at 192 spp; bore ~2.4 s at 48 spp (so ~5 s at 96)

| Part | Predicted |
|---|---|
| Scene build + cameras + compile + BVH (~930k triangles) | ~10 s |
| Outside frames 0-164 at 192 spp (~1.3 s) | ~3.6 min |
| Bore frames 165-215 at 96 spp (~5 s) | ~4.3 min |
| Cup + melt frames 216-383 at 96 spp (~9.5 s avg, 6.5-11.5 s) | ~26.6 min |
| Denoise (5-pass a-trous on the GPU, inside each frame's time) | included |
| ffmpeg encode 384 frames | ~1.1 min |
| **Total** | **~36 min** |

Start: about 10:25 AM (M5 clock). Predicted finish: about 11:01 AM.
