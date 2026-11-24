# Story Forge — Character Voice Casting (ChatterBox TTS)

Engine: ChatterBox (~/chatterbox-env). Each character clones a FIXED reference clip
so the voice is identical every time (the no-reference default voice drifts — don't use it).

Generate a line:
  ~/chatterbox-env/bin/python ~/Desktop/PROJECTS/AI/videopipe/bin/character_voice.py \
      --character hank --line "your line here" --out /tmp/line.wav

## LOCKED
- hank (bear)  -> hank.wav         (Tone 4 — Matt's pick, 2026-05-25)
- doug (dog) and every Matt narration -> Matt's LOCKED voice (11/24): `pipeline-tools/matt_voice.py` = ChatterBox, `~/Desktop/PROJECTS/avatar-assets/matt-inputs/matt_real_ref.wav`, exaggeration 0.45, cfg 0.5, temperature 0.75, seed 7, silence trim only. voice2_matt.wav is retired for Matt and must never voice him again

## SPARE POOL — ready to cast to new characters this episode
- voiceA -> spare_voiceA.wav
- voiceB -> spare_voiceB.wav
- ~~voiceC -> spare_voiceC.wav~~ RETIRED 2026-09-29 — Matt: "that gruff one... really isn't useful for anything." Never cast it.

## ruby & nia — African American female voices (added 2026-08-07)
Matt's picks from an 8-voice Chatterbox-clone audition of EARS dataset speakers
(ethnicity/gender self-reported in the dataset's speaker_statistics.json).
- **ruby** = EARS p098 (46-55) — mature, assertive. Ref: `ruby.wav` (15s), fuller source: `ruby_source_full.wav`
- **nia** = EARS p080 (26-35) — same register, younger/lighter. Ref: `nia.wav`, fuller source: `nia_source_full.wav`
- Use anywhere: `speak-as ruby "line"` CLI, or `chatterbox/ruby` voice spec in .sf scripts (character_voice.py has both).
- ⚠️ EARS is CC-NC (non-commercial). Fine for personal/test work; before using in monetized videos, replace the ref wav with audio Matt has clean rights to.

## WILD RESCUE cast (2026-11-01), brand-new
- **wr_hank** (big gentle bear) -> wr_hank_ref.wav = Kokoro am_onyx passage; ChatterBox ex 0.5 cfg 0.35; film voice_fx -1.5 st + chest shelf (~88 Hz)
- **wr_doug** (bloodhound, quick and bright) -> wr_doug_ref.wav = Kokoro am_liam passage; ex 0.3 (low line) / 0.6 (bright line); light gravel in voice_fx
- Never reuse for other characters. Old Hank (built-in) / Doug (Matt clone) / voiceA / voiceB are NOT this cast.

## THE HEADING cast (2026-11-07)
- **wes** (57, dry Humboldt man) -> wes_ref.wav = Kokoro am_eric passage; ChatterBox ex 0.4 cfg 0.4 seed 7. Never reuse.
- **nia** narrates (existing ref, CC-NC: swap before monetized use).

## KSSN 8 NEWS cast (lahontan_returns, 2026-11-13), brand-new Kokoro refs
- **kssn_dan** (anchor, 50s, deep newsroom) -> kssn_dan_ref.wav = Kokoro am_michael passage
- **kssn_halverson** (older scientist) -> kssn_halverson_ref.wav = Kokoro am_adam passage
- **kssn_resident** (grizzled local) -> kssn_resident_ref.wav = Kokoro am_santa passage
- field reporter (woman 30s) = **nia** (CC-NC ref).
