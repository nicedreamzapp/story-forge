# YouTube — THE LAST SIGNAL (DRAFT, nothing uploaded)

Channel: **Nice Dreamz (@nicedreamzapps)**, UCAXvNbN6FYpzjeh1aPvYgrw
Category: **1, Film & Animation** (same as The Oldest Tree upload, `upload_oldest_tree.py`)
Audience: **Not made for kids** (`selfDeclaredMadeForKids: False`). It has a screaming crewmate and a stone monster in a strobe; keep it off the kids shelf.
Privacy plan: upload **private** first, Matt watches it on YouTube, then flip to public on his OK.
Language: `defaultLanguage: en`, `defaultAudioLanguage: en`.

## Which file to upload

**Upload `final/The_Last_Signal.mp4`** (the 4K stereo master).
Checked with ffprobe 10/31: 3840x2160, 24 fps, H.264 at ~41 Mbps, AAC stereo 48 kHz, 46.625 s, 230 MB.
That sits inside YouTube's own 2160p/24fps SDR bitrate band, so it won't be re-encoded down from a starved source.

**About the 5.1 mux (`final/The_Last_Signal_51.mp4`): don't use it for YouTube.**
YouTube's "Recommended upload encoding settings" page (support.google.com/youtube/answer/1722171, read 10/31) says:
audio codec "AAC-LC or Opus or Eclipsa Audio", channels "Stereo or Stereo + 5.1", sample rate "48kHz".
Our _51 file carries **E-AC3** 5.1 as its first track, and E-AC3 isn't on that list. So I can't source that YouTube keeps our 5.1. The page also doesn't say which viewers would actually hear a 5.1 track. If Matt wants to try surround on YouTube, the sourced route is a separate test upload (private) with the 5.1 re-encoded to **AAC-LC 5.1, 48 kHz**. Untested.
The E-AC3 5.1 file stays the deliverable for anything that plays it straight (Plex, a TV, a download link).

## Thumbnail (not made yet)
There's no thumbnail in `final/`. Suggest one frame from the arrival (c04, 7.0 to 11.4 s: the city-sized ship over the land), pulled from the 4K master at full res, no text or just "THE LAST SIGNAL". Custom thumbnails need a verified channel. The channel reads `longUploadsStatus: allowed`, which normally means verified, but I didn't test a thumbnail call.

## Title options (all under 100 characters)
1. `THE LAST SIGNAL | My first AI sci-fi trailer, made 100% local on a Mac M5 128GB`
2. `My first AI sci-fi trailer, made 100% local on a Mac M5 128GB | THE LAST SIGNAL`
3. `THE LAST SIGNAL: my first AI sci-fi trailer, made 100% local on a Mac M5 Max 128GB, no cloud`

My pick is 1. The film name leads, and the brag is the hook. "sci-fi" is kept because it's Matt's own wording and how people search. The no-hyphens rule would make it "sci fi", so it's his call.

## Description (draft, his voice, full pipeline per Matt 8:05 PM: "you can't skimp")

3,267 characters (YouTube limit 5,000; no angle brackets, which YouTube rejects). Same stages and numbers as the reddit.md breakdown, a little condensed.

```
THE LAST SIGNAL. A cargo ship follows a signal nobody has ever charted, and the planet at the end of it already knows the captain's name.

My first sci fi trailer. Every frame, voice, sound and note was generated on my MacBook, no cloud renders, no API calls, no subscriptions. Here is the whole pipeline with the real clock times from 10/31, stalls included.

HARDWARE
MacBook Pro, Apple M5 Max, 128GB unified memory, macOS 27.2. One model in memory at a time: each stage loads its model, batches every job, unloads, and the next one starts.

HOW IT WAS MADE
1. Story, 2:00 to 2:52 AM: premise and trailer script written in chat, cut faster to v3 (about 40 cuts) and locked before anything rendered.
2. Shot list, 3:08 to 3:20 AM.
3. The ship, Blender 5.1.1 Cycles on Metal, 3:20 to 4:27 AM: a procedural city sized ship, 7 hero stills and 2 camera animations.
4. Stall, 16 min: the memory guard refused a 48 GB image model, so I switched models instead of forcing it.
5. Stills, Z-Image-Turbo 6B bf16, 4:50 to 5:45 AM: character canon and every start frame. The creature began as a MattPaint painting and went in through img2img to become photoreal; the Blender ship frames got a light img2img polish.
6. Previs, LTX-2.5 distilled (MLX, bf16), 5:46 to 6:14 AM: a quick draft of every shot (20 drafts, about 106 s each) and a rough cut that decided which shots and seconds earned a real render.
7. Quality pass, LTX-2.5 hq two stage (MLX, bf16, 832x480), 6:15 to about 11:30 AM: 35 takes of only the shots that made the cut, about 9.5 min a take.
8. Clip gate, Qwen3-VL-32B local vision judge, 25 min.
9. Score, ACE-Step 1.5 through my local Song Forge server: 3 instrumental candidates, each cut to the trailer's beat map by script.
10. Our own numpy synth: the sub bass swell under the arrival, the heartbeat radio beep, a sub kick on every ramp cut, the title drop.
11. Sound effects, MMAudio large 44k v2: 25 effects in one load, 15 of them generated from the clips so they sync to picture. 4 min.
12. Voices, ChatterBox: 9 takes of the 3 lines in 1.5 min, the planet pitched down and layered, the captain whispered.
13. Mix, our own 5.1 panner: the ship sweeps front to rear, the planet comes from every speaker, LFE on the rumble. E-AC3 5.1 plus stereo.
14. Upscale, SeedVR2-3B fp16, 12:34 to 3:56 PM: held shots restored at 720p (866 frames, about 12.7 s a frame), then resized to 4K. Honest note: a 4K deliverable, not native 4K detail. Two stalls here, 29 min getting it running and 78 min when one shot came back smeared twice and had to be split.
15. Grade: bloom on the engines, our own LUTs (cold space teal, teal orange blockbuster), light grain, 2.39:1 scope, FFmpeg for every cut.
16. QC, two rounds: a local vision model (Qwen3-VL-32B) plus Whisper checked the finished cut, 51 of 53 checks passed (the 2 flags are the stone monster itself). A face check caught the captain drifting, so 4 shots got a face lock back to her canon face.
17. Ready at 5:38 PM. About 14 and a half hours from build start to finished trailer, about 2 hours of that stalls.

Every script, the plan, the time ledger and the known defects are public: https://github.com/nicedreamzapp/story-forge

0:00 Uncharted
0:12 The monoliths
0:25 It wakes up

#localai #aivideo #scifi
```

Notes on the description:
- The chapters follow YouTube's rule (the first at 0:00, at least 3, each at least 10 s): 0:00 to 0:12 hook and arrival, 0:12 to 0:25 monoliths and "Welcome back, Captain", 0:25 to 0:46 the ramp, the whisper and the title. The times come from `final/edl_final.json` (arrival cut 7.04, claws 11.46, welcome 21.54, second sun 25.33, black 41.0, title 43.62).
- The GitHub link only goes live **after** the github.md push, or it points at a repo without the new tools.
- No "made with" credit for the coding assistant. Models and hardware are named because local AI is the subject.
- "Open weights" rather than "open source" is the safe word for the models. LTX-2.5's weights ship under Lightricks' own licence, not an OSI licence, so I left "open source" off the model list. The pipeline code itself is open.

## Tags
```
THE LAST SIGNAL, sci-fi trailer, AI trailer, AI short film, local AI, local AI video, on device AI, Mac M5 Max, M5 Max 128GB, MacBook Pro M5, Apple Silicon AI, LTX-2.5, LTX Video, Z-Image-Turbo, SeedVR2, MMAudio, ChatterBox, ACE-Step, Blender Cycles, Story Forge, AI filmmaking, open weights, no cloud AI, 5.1 surround
```
(Leave out any Humboldt or Trinidad tag, same as the Sitka uploader strips them.)

## Monetization: hold
The captain's voice is the "ruby" reference from the EARS dataset, which is **CC-NC (non-commercial)** (`stages/07_gates/known_defects.md`, and `bin/character_voice.py` line 39). That's fine for a non-monetized upload. **Before turning on monetization, re-voice the captain's line ("I've never been here.") with a commercially clean reference.** I'd also check the MMAudio and LTX-2.5 weight licences before monetizing. I didn't verify those terms here.

## How uploads actually work here (checked, nothing uploaded)
- The tools are on the **M5**, not the mini: `/Users/dtribe/Desktop/PROJECTS/ineedhemp website/youtube/` (`yt_auth.py`, `upload.py`, and per-video uploaders like `upload_oldest_tree.py` and `upload_sitka_v3.py`). The path in `rules/public-writing.md` ("Tools on Mac Mini") is stale. That folder doesn't exist on the mini (`ls` there: No such file or directory).
- Nice Dreamz token: `token_nicedreamz.json`, scopes `youtube` + `youtube.force-ssl`. The `youtube` scope covers `videos.insert` and `thumbnails.set`.
- A live read-only check on 10/31 (`channels.list mine=true`) refreshed the token fine and returned `UCAXvNbN6FYpzjeh1aPvYgrw Nice Dreamz`, longUploads allowed, 29 videos. **There's no upload blocker.**
- To upload once Matt approves: copy `upload_oldest_tree.py` to `upload_last_signal.py`, set VIDEO to the 4K master, paste the title, description and tags above, category "1", kids False, embeddable True, then run `.venv/bin/python upload_last_signal.py private`. Add `thumbnails().set` after the thumbnail exists.
- After it's live: fill in `stages/08_deliver/published.md` (URL, date, title, description), and swap the video ID into storyforge-page.md and the README section in github.md.
- Housekeeping, one line: the OAuth token files sit inside a Desktop project folder. If Desktop syncs to iCloud, that breaks the no-secrets-in-cloud-folders rule. I didn't check the iCloud setting.
