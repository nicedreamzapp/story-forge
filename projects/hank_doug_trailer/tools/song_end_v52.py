#!/usr/bin/env python3
"""song_end_v52.py — anthem_9 is the pick (the only take where whisper hears the "Hank and Doug" chorus; hiss floor -80.7 dBFS vs
the old theme's -58.0) but ACE-Step ran out of its 64 s on the last sung word ("small!" ends 63.3) and fades in the final 0.7 s
instead of ringing a chord. Engineered ending (no hard cut, no fade-out): a spectral freeze of the final chord (the 0.35 s before
the fade) sustained for TAIL s with an exponential decay, crossfaded in over the fade. Writes music/anthem_9_end.wav."""
import numpy as np, soundfile as sf, librosa
from scipy.signal import butter, sosfiltfilt
SR = 48000; SRC = "music/anthem_9.wav"; OUT = "music/anthem_9_end.wav"
CUT, TAIL = 63.05, 3.6            # the chord is still full at 63.05 (rms -13.6); the native fade starts after
y, _ = librosa.load(SRC, sr=SR, mono=False); y = y.T.astype(np.float32)
n_fft, hop = 4096, 1024; rng = np.random.default_rng(9)
tail = np.zeros((int(TAIL * SR) + n_fft, 2), np.float32)
for ch in range(2):
    seg = y[int((CUT - 0.35) * SR):int(CUT * SR), ch]
    S = np.abs(librosa.stft(seg, n_fft=n_fft, hop_length=hop)); mag = S.mean(1)
    frames = int(TAIL * SR / hop) + 2
    ph = np.exp(2j * np.pi * rng.random((len(mag), frames)))
    out = librosa.istft(mag[:, None] * ph, hop_length=hop, n_fft=n_fft, length=len(tail))
    tail[:, ch] = out
seg2 = y[int((CUT - 0.35) * SR):int(CUT * SR)]; tail *= np.sqrt((seg2 ** 2).mean()) / (np.sqrt((tail[:int(0.35 * SR)] ** 2).mean()) + 1e-9)
tail = np.tanh(tail / 0.7) * 0.7   # random-phase overlap-add spikes: match the chord's RMS, then soft-clip
t = np.arange(len(tail)) / SR; tail *= np.exp(-t / (TAIL / 3.2))[:, None]            # ~-27 dB by the end
tail = sosfiltfilt(butter(2, 7000 / (SR / 2), btype="low", output="sos"), tail, axis=0).astype(np.float32)
xf = int(0.25 * SR); i0 = int(CUT * SR)
res = np.zeros((i0 + len(tail), 2), np.float32); res[:i0] = y[:i0]
w = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, xf))
res[i0 - xf:i0] = y[i0 - xf:i0] * (1 - w)[:, None] + tail[:xf] * w[:, None]
res[i0:i0 + len(tail) - xf] = tail[xf:]; res[-int(0.1 * SR):] *= np.linspace(1, 0, int(0.1 * SR))[:, None]
sf.write(OUT, res, SR, subtype="PCM_24"); print(f"{OUT}: {len(res)/SR:.2f} s (song to {CUT}, chord ring-out {TAIL} s)")
