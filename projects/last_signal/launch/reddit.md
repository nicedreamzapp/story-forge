# Reddit — THE LAST SIGNAL (DRAFTS ONLY, nothing posted)

**Matt's rule for these posts (8:05 PM 10/31):** "you need to post our whole pipeline so everyone can see exactly how we made it and what hardware we used. You can't skimp." So every post carries the **full breakdown** below: his voice for the opening paragraph, then a numbered "how it was made" list. Markdown is allowed on Reddit.

**Who posts:** not this M5 session. Reddit posting belongs to the **Reddit Mastermind** session (`~/Desktop/PROJECTS/reddit-mastermind`; memory `feedback_reddit_goes_through_reddit_mastermind`, `feedback_reddit_comments_only_no_posts_locallama`). Matt gives an explicit go per post. The handoff prompt is at the bottom.

**How the rules were read:** live on 10/31 through the Reddit API on the mini (the read-only client in `~/scripts/reddit-inbox`: `/r/<sub>/about/rules`, `/about`, `/api/link_flair_v2`). The anonymous `about/rules.json` gives 403 from here. I also pulled u/divinetribe1's own post history per sub.

**Account history that matters (API, 10/31):**
- r/aivideo: The Bear Sister (2026-07-19, flair "LIGHTRICKS LTX 🎬 SHORT FILM") is **removed_by_category: moderator**. Reddit Mastermind's CLAUDE.md files it under the July burst (the same film had gone to r/LocalLLaMA and r/StableDiffusion the day before).
- r/LocalLLaMA: 2 posts **removed by moderator** (4/22, 6/13). Matt's standing rule: no posts there.
- r/StableDiffusion: 2 posts, **both survived** ("i couldnt find anyone making full movies locally on a mac", 7/18, 16 points, 8 comments; the phone vision models post, 9/12).

---

## THE FULL BREAKDOWN (shared by every post; every number is sourced, see the bottom)

```
**Hardware:** MacBook Pro (Mac17,6), Apple M5 Max, 128GB unified memory, macOS 27.2. Nothing else. No cloud renders, no API calls, no subscriptions.

**The memory rule:** one model in memory at a time. Each stage loads its model, batches every job for it, unloads, and the next stage starts. Every heavy step takes a memory lease first and waits if my Song Forge server has a customer job running.

**How it was made, in order (times are the real clock on 10/31):**

1. **Story, 2:00 to 2:52 AM.** Premise and a 10 beat trailer script written in a chat, then cut faster to script v3 (about 40 cuts, about 50 s) and locked before anything rendered.
2. **Shot list, 3:08 to 3:20 AM (12 min).**
3. **The ship, Blender 5.1.1, Cycles on Metal, 3:20 to 4:27 AM (67 min).** A procedural city sized ship modeled by script, 7 hero stills plus 2 camera animations (the arrival flyover with its shadow sweeping the ground). Cycles stills took 11 to 41 s, the volumetric one 6 min, the animation about 12 s a frame at 48 samples.
4. **Stall, 4:32 to 4:48 AM (16 min).** My memory guard refused Qwen-Image (needs 48 GB, only 23 GB were free because another job held memory), so I switched image models instead of forcing it.
5. **Stills, Z-Image-Turbo (6B, bf16, 9 steps, diffusers on MPS), 4:50 to 5:45 AM (55 min).** Character canon and every start frame. Run in two halves so it fit: the text encoder encodes every prompt and unloads, then the transformer and VAE render. The creature's layout started as a painting from MattPaint (my own browser paint engine) and went in through img2img at 0.82 to 0.9 to become photoreal. The Blender ship frames got a light img2img polish (0.42), heavier on the grab shot (0.6 to 0.72). A local vision model judged the stills before any motion.
6. **Previs, LTX-2.5 distilled (MLX, bf16), 5:46 to 6:14 AM (28 min).** One quick draft of every shot (20 drafts, about 106 s each), then a rough cut against the script timings (39 cuts, 39.3 s). That cut decided which shots and which seconds were worth a real render: 18 renders, 35 takes.
7. **Quality pass, LTX-2.5 hq (dev transformer plus CFG, two stage, MLX bf16, 832x480), 6:15 to about 11:30 AM (about 5 h 15 min).** Only the shots that made the cut, at the cut length plus about half a second of handles, 3 takes for the hero shots and 1 to 2 for the rest. About 9.5 min a take, an hour over my estimate. Two strobe shots kept their previs drafts.
8. **Clip gate, Qwen3-VL-32B local vision judge, 11:31 to 11:56 AM (25 min).** 44 takes, 3 frames each. It passed only 10, because it reads motion beats from still frames as "static", so I picked the cut by eye under a written exception.
9. **Score, ACE-Step 1.5 through my local Song Forge server, 11:34 to 11:35 AM.** 3 instrumental candidates, each cut to the trailer's beat map by a script (drone, BRAAAM on the arrival, rising build, dead stop for the line, accelerating ramp, final hit). The best fit won.
10. **Edit and our own synth, 11:36 to 11:57 AM, on CPU while the gate ran.** Final cut 50 shots, 46.6 s. Sub bass written in numpy: a 25 to 40 Hz swell under the arrival, a radio beep that speeds up like a heartbeat and stops dead, a pitch dropping 55 to 28 Hz sub kick on every ramp cut, a long sub drop under the title.
11. **Sound effects, MMAudio large 44k v2 (fp32 on MPS), 11:57 AM to 12:01 PM (4 min).** 25 effects in one model load, 15 of them generated from the actual clips so they sync to picture (hull groan, glass shatter, claws, rumble), the rest from text.
12. **Voices, ChatterBox 0.1.7, 12:02 to 12:03 PM (1.5 min).** 9 takes of the 3 lines in one load. The planet's voice pitched down, octave stacked and drowned in reverb; the captain whispered. Whisper checked every take.
13. **Mix, our own 5.1 panner (numpy), 12:13 to 12:20 PM.** Every moving sound gets an azimuth path: the ship sweeps front to rear, the planet comes from every speaker, LFE on the rumble, dialogue in the center. Static gain, no loudness normalizer. Out comes E-AC3 5.1 plus a stereo mix.
14. **Upscale, SeedVR2-3B (fp16 on MPS).** Stall first, 12:05 to 12:34 PM (29 min): a flash attention crash on Mac, then 4K direct measured at about 7 min just to encode 21 frames, so I changed the plan. The 19 shots held 0.9 s or longer got SeedVR2 at 720p (866 frames, about 12.7 s a frame, 12:34 to 3:56 PM, about 3 h 20 min), then a lanczos resize to 4K. The sub second strobe cuts are lanczos plus light sharpening. So it's a 4K deliverable, not native 4K detail.
15. **Stall, 3:27 to 4:45 PM (78 min).** The arrival shot, the only one long enough to need 3 batches, came back grey with white smears in the middle batch twice. I split it into 2 single batch chunks and it came out clean.
16. **Finish and grade, 3:19 to 4:02 PM, on CPU alongside the upscale.** Bloom and an anamorphic streak on the engines and lights, our own LUTs (cold_space_teal on the space shots, teal_orange_blockbuster everywhere else), light film grain, 2.39:1 scope bars inside a 3840x2160 frame, FFmpeg 8.1 for every cut and encode.
17. **QC, 4:46 to 5:37 PM, two rounds.** film_qc (Qwen3-VL-32B in 4-bit MLX looking at the picture, whisper-large-v3-turbo listening): 51 of 53 checks pass, and the 2 flags are the stone monster itself, which the judge reads as a deformity. Continuity check 209 of 209. A face check (ArcFace) caught the captain looking like a different woman in some shots, so those 4 shots got a face lock (inswapper) back to her canon face, then everything was finished again and checked again.
18. **Ready at 5:38 PM.** About 14 and a half hours from the build starting to the finished trailer, including about 2 hours of stalls.

**Rough spots I know about:** the creature isn't consistent between the rising giant and the strobe close up, the crewmate's face drifts in the strobe, the "her own handwriting on the stone" beat doesn't read, the hook ship holds size more than it charges the camera, and the locked faces are a touch softer than the detail around them.

**Every script is public:** https://github.com/nicedreamzapp/story-forge (the film's whole folder is projects/last_signal, with the plan, the time ledger, the gate reports and the known defects).
```

Before posting, Reddit Mastermind checks the breakdown has no em dashes in Matt's prose. The list items above use commas and colons only. The proper names (Z-Image-Turbo, LTX-2.5, SeedVR2-3B, whisper-large-v3-turbo) keep their hyphens.

---

## Ranked picks

### 1. r/StableDiffusion (1.04M), best fit
- **Permits it.** Rule 1: *"Posts must center on open-source/local AI tools (e.g. Stable Diffusion, Flux, PixArt). When relevant you should clearly list tools in the title/body and explain your workflow. Mixed workflows are OK only if they center on the use of local or free tools."*
- **Limits.** Rule 6: *"Low-effort posts like images/videos without context or workflows are not allowed. Tutorials and tools must be free and directly accessible."* The full breakdown plus GitHub covers this. Rule 4: *"Surreal or eerie imagery is fine, but avoid graphic violence, gore, or shock content."* The scream strobe is eerie, not gore; it's the one thing a mod could point at.
- **Flair:** `Workflow Included` (the breakdown + repo is literally the workflow). Fallback: `Animation - Video`.
- **Format:** native video post, `final/The_Last_Signal_1080p.mp4` (1920x1080, 49 MB), with the text body.
- **Title:** `THE LAST SIGNAL: a 46 second sci fi trailer made fully local on a MacBook M5 Max 128GB, full pipeline inside (Blender, Z-Image-Turbo, LTX-2.5, SeedVR2, MMAudio, ChatterBox, ACE-Step)`
- **Opening (Matt's voice), then the full breakdown:**
```
Started this at 2 in the morning with a one line idea and had a finished trailer at 5:38 that afternoon. Every frame, voice and sound was made on my MacBook, nothing rendered in the cloud, and the whole pipeline is below with the real clock times, the stalls included.
```

### 2. r/LTXVideo (2.6k), small but exactly on topic, low risk
- **Permits it.** Rule 2: *"Posts should be related to LTX Video, its features, uses, and developments... AI topics about VIDEO gen or General AI are tolerated."* Rule 4: *"Avoid spam or excessive self-promotion. Sharing projects is welcome if it's genuinely helpful to the community."*
- **Flair:** the flair list returned 403; pick at post time if the sub offers any.
- **Title:** `Previs with distilled, hq only on what made the cut: a full sci fi trailer on a Mac M5 Max with LTX-2.5 (whole pipeline inside)`
- **Opening (Matt's voice), then the full breakdown:**
```
LTX-2.5 did all the motion in this one, on my M5 Max, and the trick that made it doable in a day was steps 6 and 7 below: a distilled draft of every shot, a rough cut, then the hq pass only on the seconds that made it. Also on this film shots went hazy and dark after 2 to 3.5 seconds, so render to the cut length plus a little handle, never a blanket 5 s.
```

### 3. r/aivideo (411k), the big audience, but it removed us before
- **Permits it.** Rule 1: *"ANYONE CAN SUBMIT, EVEN NEW ACCOUNTS. TO SUBMIT YOUR VIDEO: Upload original video file directly into the sub by using 'add video' button... PG-13 1080p 8 seconds minimum 15min maximum 1GB max file size... TITLE OF POST MUST INCLUDE A NAME FOR YOUR VIDEO... some videos might need manual approval, don't delete it."* Rule 3 bans copyrighted music; our score is ACE-Step, so it's fine. Rule 2: PG-13, *"no excessive gore."*
- **Flair:** `LTX 🍿 MOVIE TRAILER`. The flair set is tool plus genre; there's no local or open-source flair.
- **File:** `final/The_Last_Signal_1080p.mp4` (it meets 1080p and 1 GB). Never the 4K file.
- **Risk:** the July post was mod removed. Post this **at least 24 h after** the r/StableDiffusion post, never in a burst, and leave it alone if it sits in manual approval.
- **Title:** `THE LAST SIGNAL (teaser trailer), made entirely on a MacBook M5 Max 128GB with local models`
- **The video post goes up first. The full breakdown goes in the first comment, opening with:**
```
Everything here ran on my own MacBook, no cloud anywhere. Here's the whole pipeline with the real times, stalls included.
```

### 4. r/OpenSourceAI (34.6k), optional, later
- **Permits it (by its description; no written rules).** *"Community for open-source AI — open weights, open data, open tooling. Model releases, fine-tuning, inference, agents, benchmarks, licensing, and the ecosystem around building AI in the open."*
- Only after the GitHub push. Lead with the repo, same full breakdown. Never on the same day as #1.

## Evaluated and ruled out
- **r/LocalLLaMA (864k):** Matt's hard rule says no posts (two mod removals). Its Rule 3 also bans *"Completely/primarily LLM generated copy."* Comments only.
- **r/comfyui (218k):** the API returns no rules and no sidebar. This film didn't run as a ComfyUI workflow (only the MMAudio and SeedVR2 node code is reused). Weak fit, so skip it.
- **r/blender (1.46M):** Rule 3: *"If your render is remotely intended to be realistic, please include wireframe, viewport or clay render."* Rule 5: *"Don't post a photograph or generated image and claim its a render."* The film's ship frames were img2img polished, so the trailer doesn't qualify. A separate post of the raw Cycles ship renders with a clay pass would.
- **r/MacStudio (47k):** Rule 1 needs it *"directly related to Mac Studio"*, and this is a **MacBook Pro** (system_profiler: Mac17,6, M5 Max, 128 GB).
- **r/mac (3.1M):** Rule 5: *"Promotion or advertising is not allowed... This includes anything you've made (e.g. wallpaper, app, blog post, video)."* Rule 7: *"No Generative AI Content."*
- **r/macbookpro (419k):** *"Intentional spam with the goal to promote is prohibited."* That's risky for a showcase.
- **r/sciencefiction (321k):** Rule 8: *"No AI-generated content."*
- **r/aivideomaking (11k):** *"This place is for asking questions and learning, not self-promotion."*
- **r/aivideos (135k):** the sidebar is an unrelated data science link list. It looks unmoderated, so skip it.
- The subreddit search ("video generation", "local video", "LTX video", "open source video", "ai video", "wan video") found no dedicated local video gen sub; r/LTXVideo is the closest.

## Pacing
Day 1 r/StableDiffusion. Day 2 r/LTXVideo. Day 3 r/aivideo. r/OpenSourceAI later if at all. Before each post, Reddit Mastermind checks u/divinetribe1's last 10 comments in that sub (at most 3 links) and the 2-links-per-24h-across-Reddit cap. No ineedhemp.com links. GitHub and YouTube links are fine. The GitHub link only goes in **after** the github.md push, or the claims point at a repo that doesn't have the tools yet.

## Sources for the breakdown
PRODUCTION-PLAN.md (decisions + both time ledgers), LESSONS.json (10/31 entries: Cycles/LTX timings, SeedVR2 13 s/frame and 6x, the haze, the grey batch), stages/01_story (premise 2:13 AM, v3 locked 2:52 AM), stages/05_sound/score_pick.md, stages/07_gates/known_defects.md, final/film_qc_report.md ("Checks run: 53 | passed: 51 | failed: 2"), final/timeline.json (LUTs, grain, scope), sfx/jobs.json (25 jobs, 15 with video), tools/zimage_batch.py (bf16, 9 steps, staged), tools/seedvr2_batch.py (seedvr2_ema_3b_fp16), bin/make-sfx (MMAudio large 44k v2 fp32 MPS), bin/make-ltx25 (pure MLX bf16, --hq = dev + CFG two stage), ship/shots.py (Cycles, compute_device_type METAL), pipeline-tools/film_qc.py (Qwen3-VL-32B 4bit MLX + whisper-large-v3-turbo), chatterbox-tts 0.1.7 (pip), sw_vers 27.2, blender 5.1.1, ffmpeg 8.1. The "~2:00 AM" start: the premise file was written 2:13 AM and approved then, so the chat started a little before.

## Handoff prompt for Reddit Mastermind (Matt pastes it when he's ready)
```
Post THE LAST SIGNAL trailer to r/StableDiffusion only, nothing else today. File: ~/Desktop/PROJECTS/story-forge/projects/last_signal/final/The_Last_Signal_1080p.mp4 (copy it into the reddit-mastermind folder for the upload tool, delete the copy after). Native video post, flair "Workflow Included", title, opening paragraph and the FULL breakdown exactly as in ~/Desktop/PROJECTS/story-forge/projects/last_signal/launch/reddit.md (Matt wants the whole pipeline, no trimming). Check u/divinetribe1's recent activity in the sub first. Confirm the story-forge GitHub push is live before posting (the breakdown links it). After it's live, register the post with the launch watcher (launch/watchers.md). Matt approved this text on <date>.
```


Approved by Matt 2026-10-31 9:57 PM ("Post it") for r/StableDiffusion, with the opening changed to "nothing rendered in the cloud".
