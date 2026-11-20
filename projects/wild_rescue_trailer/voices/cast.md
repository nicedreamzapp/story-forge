# WILD RESCUE cast, rebuild (2026-11-01 evening): wr3_hank / wr3_doug

Brand-new voices. Excluded: wr_hank (am_onyx), wr_doug (am_liam), all 7 Kokoro voices auditioned that morning, the ChatterBox built-in voice (old hank), Matt's clone (old doug), and voiceA/B/C.
Pipeline: a reference (Kokoro-82M or Qwen3-TTS VoiceDesign, both Apache) is cloned by ChatterBox (MIT). Everything ran on the PC's CPU, because the mini's guard had no room and the M5 GPU is taken.
Auditions: 8 references (4 per character), 3 seeds per line, 36 takes. Every take was whisper-checked with faster-whisper large-v3-turbo (CPU). Pitch is the yin median on loud frames, cross-checked with pyin.

## HANK, a huge gentle grizzly: wr3_hank
- Reference: Qwen3-TTS-12Hz-1.7B-VoiceDesign, prompt "Adult man in his fifties, a very deep warm bass voice, huge chest resonance, slow unhurried pace, gentle and kind, a little dry understated humor, soft-spoken, American." Reference median ~81 Hz. File: story-forge/voices/wr3_hank_ref.wav (copy in refs/).
- Why: it was the only Hank candidate that sits in a real bass range. am_adam was ~118 Hz, am_michael ~127 Hz and the second VoiceDesign ref ~101 Hz; those takes landed at 97-128 Hz, too close to Doug.
- Processing (voice_fx): -1.5 semitones (size), +3 dB low shelf at 160 Hz (chest), no reverb.
- c05a_hank.wav (pick): seed 101, ex 0.45, cfg 0.3, 2.00 s (time-stretched 1.07x to fit the cut). Median ~80 Hz. Whisper heard "Doug, that's a big hole." The pause after "Doug" runs 0.30 to 0.88 s.
- alt/c05a_hank_alt.wav: seed 303, 1.77 s, ~72 Hz, whisper "Doug, that's a big hole.", shorter pause (0.30 to 0.50 s).
- The third take (seed 202) failed whisper ("it's a big hole") and was dropped.

## DOUG, a lanky bloodhound: wr3_doug
- Reference: Kokoro-82M voice am_eric at speed 1.05 (never used before for Hank & Doug). Bright American adult male, reference median ~158 Hz. File: story-forge/voices/wr3_doug_ref.wav (copy in refs/).
- Why: all 6 takes passed whisper, "Doug" was never heard as "Dug", and the pitch held steady at 136-161 Hz (bright adult male, clearly above Hank).
  - The other candidates fell short. bm_daniel sat at ~126 Hz and is British. VoiceDesign 1 came out ~220 Hz, reading young. VoiceDesign 2 ("wiry, gravelly, around forty") swung from 128 to 220 Hz between takes.
- Processing: line 1 gets an 8 kHz low-pass, light gravel (22%) and a small dark room at 8%. Line 2 gets a +2 dB presence shelf at 3 kHz and 18% gravel.
- c01e_doug.wav (pick, "I picked a side.", low V.O.): seed 303, ex 0.3, cfg 0.5, 1.11 s (cut 1.2 s). Median ~136 Hz, the lowest Doug read. Whisper heard "I picked a side."
- alt/c01e_doug_alt.wav: seed 202, 1.02 s, ~142 Hz, whisper exact.
- c05b_doug.wav (pick, "Then we need a lot of help."): seed 101, ex 0.6, cfg 0.45, 1.66 s (cut 2.0 s). Median ~151 Hz. Whisper exact.
- alt/c05b_doug_alt.wav: seed 303, 1.16 s (a quicker read), ~149 Hz, whisper exact.

## Pitch separation
Hank's dialogue take is ~80 Hz and Doug's is ~151 Hz, almost an octave apart. All files are 48 kHz mono 24-bit.
Registered in ~/AI/videopipe/bin/character_voice.py as wr3_hank / wr3_doug (backup: character_voice.py.bak-20261101-wr3).
The losing takes and references were deleted after delivery.
