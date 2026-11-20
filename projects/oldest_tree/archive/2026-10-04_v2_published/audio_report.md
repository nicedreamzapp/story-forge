/Users/dtribe/Desktop/PROJECTS/story-forge/pipeline-tools/audio_check.py:63: UserWarning: PySoundFile failed. Trying audioread instead.
  y, sr = librosa.load(str(f), sr=22050)
/Users/dtribe/chatterbox-env/lib/python3.12/site-packages/librosa/core/audio.py:184: FutureWarning: librosa.core.audio.__audioread_load
	Deprecated as of librosa version 0.10.0.
	It will be removed in librosa version 1.0.
  y, sr_native = __audioread_load(path, offset, duration, dtype)
Fetching 4 files:   0%|          | 0/4 [00:00<?, ?it/s]Fetching 4 files: 100%|██████████| 4/4 [00:00<00:00, 94786.53it/s]
# audio_check — The_Oldest_Tree.mp4
**Verdict: PASS** — 0 fail, 2 warn
I cannot hear. PASS = the measured failure modes are absent, not that it sounds good.

- [PASS] score vocals: vocal stem 24.0 dB under the music (need >= 15)
- [PASS] score drone: 0 sustained low tones []
- [WARN] score repeats: 45/98 4s passages near-identical elsewhere [(2.0, 79.0), (14.0, 57.0), (16.0, 58.0), (18.0, 61.0), (20.0, 65.0), (22.0, 38.0)]; hard jumps at [np.float64(0.5), np.float64(25.3), np.float64(31.2), np.float64(77.4), np.float64(83.4)]s — listen at these times or have Matt pick
- [PASS] film drone: 0 sustained low tones []
- [PASS] balance: narration avg -27.1 dB, music max -35.5 dB, music louder than narration at []
- [PASS] line nia_n01.wav @ 3.8s heard 100%
- [PASS] line nia_n02.wav @ 18.0s heard 100%
- [PASS] line nia_nA.wav @ 22.6s heard 100%
- [PASS] line nia_n03.wav @ 33.8s heard 100%
- [PASS] line nia_n04.wav @ 40.9s heard 100%
- [PASS] line nia_n05.wav @ 50.9s heard 100%
- [PASS] line nia_n06.wav @ 56.4s heard 100%
- [PASS] line nia_n07.wav @ 59.8s heard 100%
- [PASS] line nia_n08.wav @ 71.9s heard 100%
- [PASS] line nia_nB.wav @ 76.1s heard 100%
- [PASS] line nia_n09.wav @ 89.4s heard 100%
- [PASS] line nia_n10b.wav @ 99.9s heard 100%
- [PASS] line nia_n11b.wav @ 106.9s heard 100%
- [PASS] line nia_n12b.wav @ 120.9s heard 100%
- [PASS] line nia_n13.wav @ 125.8s heard 100%
- [PASS] line nia_n14.wav @ 127.9s heard 100%
- [PASS] line nia_n15.wav @ 145.3s heard 100%
- [PASS] line nia_n16b.wav @ 149.2s heard 100%
- [PASS] line nia_n17.wav @ 156.9s heard 100%
- [WARN] loudness: -21.9 LUFS, LRA 16.4 LU, true peak -0.7 dBFS
