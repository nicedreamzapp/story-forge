---
stage: 10_deliver
outputs:
  - final/thumbnail.png
  - final/youtube.json
  - stages/10_deliver/published.md
gate: none
---
# 10_deliver — ship it

One job: publish the exact approved file and record where it went.

## Commands
`~/chatterbox-env/bin/python pipeline-tools/promo_deliver.py projects/<film>` (inside make-promo):
first the FINAL AUDIO GATE (`final_audio_gate.py`): `final/<film>.mp4` re-mastered in place to -14 LUFS
(promo.json `gates.deliver_lufs`), true peak <= -1 dBTP, rejected if its audio is shorter than the picture
(`final/audio_gate.json`; a FAIL stops delivery), then
`final/thumbnail.png` (1280x720, the frame under the title slam, brand + tagline) and `final/youtube.json`
(title, description, tags, category, files) from `promo.json "youtube"`.

## Writes
`stages/10_deliver/published.md`: URL, date, title, description. Lessons into `LESSONS.json` (frozen rule 15).
Nothing is uploaded without Matt's OK.

## Done when
`published.md` is written. Matt already approved the cut in 09.
