---
stage: 08_mix
outputs:
  - stages/08_mix/score_pick.md
  - final/mix.wav
  - final/*.mp4
gate: approved
---
# 08_mix — score, mix, render

One job: the soundtrack (voice + ducked bed + SFX + sting) and the finished render.

## Commands (inside `bin/make-promo`)
1. Bed: `promo.json music.bed`, or `~/chatterbox-env/bin/python pipeline-tools/promo_music.py projects/<film>`
   (local Song Forge, `[inst]`, private + video_only, downloaded at once, whisper-checked for vocals).
   Song Forge must be idle. Matt picks the score by ear from 2–3 candidates before release.
2. `~/chatterbox-env/bin/python pipeline-tools/promo_mix.py projects/<film>`: the bed's downbeat
   (`music.hit`, else auto-detected) offset onto the slam, gain 0.55, sidechain duck, fade into the
   slam; hit + whoosh on titles, blip on callouts, whoosh into overlays; the major sting at the slam;
   two-pass loudnorm `linear=true` (static gain) → `final/mix.wav` + stems `_vo/_fx/_music.wav`.
3. `render_edl.py --renderer ffmpeg|remotion projects/<film> --out final/<film>.mp4 --audio final/mix.wav --bug <brand>`
   (ffmpeg = PIL overlays, no node; remotion = `promo-remotion/`, springs and tracked arrows).

## Done when
`final/<film>.mp4` probes right, `score_pick.md` records the bed (make-promo writes a draft), and
Matt's pick is recorded with `stages/08_mix/APPROVED.md` before release.
