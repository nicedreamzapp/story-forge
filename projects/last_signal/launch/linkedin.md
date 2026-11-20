# LinkedIn — THE LAST SIGNAL (DRAFT, nothing posted)

**Media:** upload `final/The_Last_Signal_1080p.mp4` natively with Add media (49 MB, 1080p, 46.6 s). Never post a YouTube link as the post itself; LinkedIn buries link posts (memory `feedback_upload_video_natively_never_link`). The video is the post's media, which covers the always-attach-an-image rule.
**Links:** GitHub in the text. The YouTube link, if wanted, goes in the first comment.
**Voice:** normal capitalization, no dashes, no "solo" or "one person", no coding assistant credit. Models and hardware named on purpose.

## Post

```
I made a sci fi movie trailer overnight, and every frame, voice and sound of it came off my MacBook. No cloud, no API calls, no subscriptions.

THE LAST SIGNAL is 46 seconds. A cargo ship follows a signal nobody has charted, and the planet at the end of it already knows the captain's name.

The hardware is a MacBook Pro with an M5 Max and 128GB of unified memory. The rule that makes it work on one machine is one model in memory at a time. Each stage loads its model, batches every job, unloads, and hands the memory to the next.

The stack, in order:
Blender 5.1.1 (Cycles on Metal) for the city sized ship.
Z-Image-Turbo in bf16 for every still. The creature started as a painting and was made photoreal from it.
LTX-2.5 for motion. A fast draft of every shot first, a rough cut, then the slow high quality pass only on the shots that made the cut. That one change is why it finished in a day.
SeedVR2 to upscale toward a 4K deliverable.
MMAudio for sound effects generated from the picture itself, plus sub bass we wrote in numpy.
ChatterBox for the voices, ACE-Step for the score.
Our own color LUTs and our own 5.1 surround panner.
A local vision model as QC on the finished cut: 51 of 53 checks passed.

The clock was honest too. The story was locked around 2 AM and the finished trailer was ready at 5:38 PM. About 5 hours of that was motion rendering, about 3 and a half was the upscale, and about 2 were stalls I had to work around.

The whole pipeline is open, including the plan, the time ledger and the list of what's still rough: https://github.com/nicedreamzapp/story-forge

This is what local AI can do on a laptop today. Next one goes further.

#LocalAI #AppleSilicon #GenerativeAI #OpenSource #Filmmaking
```

Notes:
- "Overnight" is fair: 2 AM to 5:38 PM the same day. If Matt wants it exact, swap it for "in one day".
- Word count is about 290. The first two lines carry the hook before LinkedIn's "see more" fold.
- The stack lines are plain lines, not bullet glyphs. If Matt wants zero list feel, they collapse into one paragraph.
- Covered after posting by `linkedin-comment-watch` on the mini (see watchers.md). The memory note says it walks recent own posts automatically, so there's nothing to register. Confirm on the activity page right after posting, the same as the 10/29 post.
- Monetization isn't an issue on LinkedIn. The captain's CC-NC voice note only matters for YouTube revenue.
