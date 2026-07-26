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
