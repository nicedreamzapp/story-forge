"""Flag SFX with a sustained narrow-band tone (alarm/siren-like): any STFT bin holding > 35% of frame energy for > 0.5 s continuous."""
import glob, numpy as np, librosa
for f in sorted(glob.glob("sfx/*.wav")):
    y, sr = librosa.load(f, sr=22050, mono=True)
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=256)) ** 2
    tot = S.sum(0) + 1e-9; peak = S.max(0) / tot; bins = S.argmax(0)
    loud = tot > tot.max() * 0.01
    narrow = (peak > 0.35) & loud
    run = 0; worst = 0; freq = 0
    for i, n in enumerate(narrow):
        if n and (i == 0 or abs(int(bins[i]) - int(bins[i-1])) <= 2): run += 1
        else: run = 1 if n else 0
        if run > worst: worst = run; freq = bins[i] * sr / 2048
    secs = worst * 256 / sr
    print(f"{f:28s} {len(y)/sr:5.1f}s  longest narrow tone {secs:4.2f}s at ~{freq:5.0f} Hz  {'<-- TONE' if secs > 0.5 else ''}")
