# Delivery report — The Little Robot Who Built Himself
Built overnight 2026-06-11, 3:14am–5:35am. 100% local on the M5.
Final: `~/Desktop/The_Little_Robot_Who_Built_Himself.mp4` — 3:57, 1280x720, 80MB.

## Spec verification (✓ table, frames extracted and checked)
| Promise | Status | Evidence |
|---|---|---|
| 5-movement story w/ meaning ("unfinished, not broken") | ✓ | narration.txt, final line lands over sunrise + credits |
| Story foundation locked before render | ✓ | BIBLE/CONTINUITY/shots.json written before any GPU work; Matt approved premise + "run" |
| Believability/continuity pass | ✓ | CONTINUITY.md: every sacrificed part visibly appears ON the bike (brass chainring s32, blue seat spring s33, eye-in-lamp s34); June reclaims the eye s40 |
| 48-shot dynamic coverage | ✓ | 29 LTX i2v + 19 ken_burns; zero zoompan/jitter |
| All stills QC'd, emotion drawn in | ✓ | 46 stills individually reviewed; 9 re-rolled (8 + st_eye_on twice); 1 cropped |
| All clips QC'd | ✓ | frame extraction across batch; 2 fails caught (8s LTX melts) → re-rendered at 6s |
| Title + credits | ✓ | PIL Georgia overlays verified at t=29 and t=231 |
| Original score | ✓ | 4 ACE-Step cues (direct API — Song Forge library untouched), spectrogram-verified, crossfaded, sidechain-ducked |
| Narration | ✓ | Piper warm-storyteller (proven recipe), 53 lines, scene-synced adelay+amix, all scenes fit with headroom |
| Audio QC | ✓ | mean -19.1dB, max -2.0dB, loudnorm'd, zero ≥8s silence gaps |
| No crash, no OOM | ✓ | one model at a time, watchdogged subprocesses, resume manifests; machine never went down |

## Known compromises (honest notes)
- Sprocket's design drifts between shots (no LoRA overnight) — canonized for
  scene 2 (he rebuilds himself differently each try = the story), reduced
  elsewhere by picking/re-rolling; June is consistent throughout.
- Basket ending → two-wheeler ending (Flux preference, adopted as MORE
  believable; CONTINUITY.md amendment).
- st_backhead gag carried by narration rather than image (Flux can't draw
  backwards heads).
- 720p final (Real-ESRGAN lives on the mini, path unvalidated — didn't risk it).

## Next project queued
Antarctica scientific documentary (memory: antarctica-documentary-queued).
