# ETA: V5 code-rendered test (M5 Max)

Measured from 3 full-quality preview frames (1920x1080, 256 spp, frames 0/120/239): 1.94 s, 1.78 s, 2.01 s per frame, average 1.91 s.
(At 64 spp the same frames took 0.42-0.62 s, so we used 256 spp. That's well past the 36 spp target and still inside the 60 min cap.)

| Part | Predicted |
|---|---|
| Scene build (scene.py, 160k triangles) + compile + BVH | ~10 s |
| Frame render, 240 frames x ~1.9 s | ~7.6 min |
| Denoise (a-trous, runs on the GPU inside each frame, ~0.05 s/frame) | ~12 s (inside the frame time) |
| ffmpeg encode (x264 slow, crf 16) | ~40 s |
| **Total** | **~8.5 min** |

Start: about 2:36 AM (M5 clock). Predicted finish: about 2:45 AM.
