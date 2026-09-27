# Story Forge — Character Voice Casting (ChatterBox TTS)

Engine: ChatterBox (~/chatterbox-env). Each character clones a FIXED reference clip
so the voice is identical every time (the no-reference default voice drifts — don't use it).

Generate a line:
  ~/chatterbox-env/bin/python ~/Desktop/PROJECTS/AI/videopipe/bin/character_voice.py \
      --character hank --line "your line here" --out /tmp/line.wav

## LOCKED
- hank (bear)  -> hank.wav         (Tone 4 — Matt's pick, 2026-05-25)
- doug (dog)   -> voice2_matt.wav  (Matt's own voice)

## SPARE POOL — ready to cast to new characters this episode
- voiceA -> spare_voiceA.wav
- voiceB -> spare_voiceB.wav
- voiceC -> spare_voiceC.wav

## ruby & nia — African American female voices (added 2026-08-07)
Matt's picks from an 8-voice Chatterbox-clone audition of EARS dataset speakers
(ethnicity/gender self-reported in the dataset's speaker_statistics.json).
- **ruby** = EARS p098 (46-55) — mature, assertive. Ref: `ruby.wav` (15s), fuller source: `ruby_source_full.wav`
- **nia** = EARS p080 (26-35) — same register, younger/lighter. Ref: `nia.wav`, fuller source: `nia_source_full.wav`
- Use anywhere: `speak-as ruby "line"` CLI, or `chatterbox/ruby` voice spec in .sf scripts (character_voice.py has both).
- ⚠️ EARS is CC-NC (non-commercial). Fine for personal/test work; before using in monetized videos, replace the ref wav with audio Matt has clean rights to.
