# X — THE LAST SIGNAL (DRAFT, nothing posted)

Account: @NiceDreamzApps. **Attach `final/The_Last_Signal_1080p.mp4` natively** to the first post (46.6 s, 49 MB, 1080p; inside X's standard upload limits for length and size). No YouTube link card. The GitHub link goes in the thread, not the first post.
x-scout's standing go covers its own auto replies only. **This launch post needs Matt's OK.**
Character counts assume the 280 limit (non Premium), counted with Python len(); X counts a URL as 23.

## Option A: one post (with video)
```
My first sci fi trailer, made 100% local on a MacBook M5 Max 128GB.

Blender for the ship, Z-Image-Turbo stills, LTX-2.5 motion, SeedVR2 upscale, MMAudio sound, ChatterBox voices, ACE-Step score, our own 5.1 mix.

No cloud. Started 2 AM, done 5:38 PM.

THE LAST SIGNAL
```

## Option B: thread (Matt asked for the full pipeline; this one carries it)
1/ (video attached)
```
THE LAST SIGNAL. My first sci fi trailer, made 100% local on a MacBook Pro, M5 Max, 128GB unified memory.

Every frame, voice and sound generated on device. No cloud, no API calls, no subscriptions.

The whole pipeline 🧵
```
2/
```
One model in memory at a time. Each stage loads, batches every job, unloads.

Ship: Blender 5.1.1, Cycles on Metal.
Stills: Z-Image-Turbo, bf16. The creature started as a painting and was made photoreal.
```
3/
```
Motion: LTX-2.5 on MLX, bf16. A fast draft of every shot, a rough cut, then the hq pass only on the 35 takes that made the cut. About 5 hours.

Upscale: SeedVR2-3B at 720p on the held shots, resized to 4K. Upscaled, not native 4K.
```
4/
```
Sound: MMAudio effects generated from the clips themselves, our own numpy sub bass, ChatterBox voices, ACE-Step score, and our own 5.1 panner (E-AC3 5.1 plus stereo).

Grade: our own LUTs, bloom, grain, 2.39:1.
```
5/
```
QC: a local vision model checked the finished cut, 51 of 53 passed (the 2 flags are the monster).

Clock: story locked ~2 AM, ready 5:38 PM, ~2 hrs of that were stalls.

Every script is open: https://github.com/nicedreamzapp/story-forge
```

Lengths (Python len, URL counted as 23): A = 268. Thread: 1/ = 220 (the 🧵 emoji weighs 2 on X, so 221), 2/ = 203, 3/ = 230, 4/ = 210, 5/ = 215. All under 280.
My pick is B, since Matt wants the full pipeline everywhere and A can't hold it.

Watching after posting: replies arrive by email via X's notification emails, and `x_reply_mail.py` on the mini (every 15 min) texts Matt one line per new X email. See watchers.md for the sentiment and takedown layer.
