#!/usr/bin/env python3
"""mix.py — the trailer soundtrack as one static-gain stereo mix (no dynamic loudnorm), cue map from script_v2.md.
Theme sections are cut from music/theme_1.wav at the whisper-measured section times (music/theme_1_words.json),
the music-box breakdown from music/breakdown_1.wav, voices from voices/, SFX from sfx/ (missing SFX are skipped and
listed). Wind and crickets are synthesised (filtered noise) so the sound bed never depends on a model.
Writes final/mix_stereo.wav + final/mix_cues.json (every placed sound with its time, for the manifest and audio_check).
Run in ~/chatterbox-env."""
import json, numpy as np, soundfile as sf, librosa, scipy.signal as ss
from pathlib import Path
P = Path(__file__).resolve().parent.parent
SR = 48000; DUR = 60.0
N = int(DUR * SR)
bus = np.zeros((N, 2), np.float32)
music_bus = np.zeros((N, 2), np.float32)
placed = []; missing = []

def load(path, mono=False):
    y, _ = librosa.load(str(path), sr=SR, mono=mono)
    if y.ndim == 1: y = np.stack([y, y], -1)
    else: y = y.T
    return y.astype(np.float32)

def env(n, fade_in, fade_out):
    e = np.ones(n, np.float32)
    fi, fo = int(fade_in * SR), int(fade_out * SR)
    if fi: e[:fi] = np.linspace(0, 1, fi)
    if fo: e[-fo:] = np.minimum(e[-fo:], np.linspace(1, 0, fo))
    return e[:, None]

def put(y, t, gain_db=0.0, fade_in=0.0, fade_out=0.0, label="", clip_len=None):
    if clip_len: y = y[:int(clip_len * SR)]
    i0 = int(t * SR); n = min(len(y), N - i0)
    if n <= 0: return
    g = 10 ** (gain_db / 20)
    target = music_bus if label.startswith('music:') else bus
    target[i0:i0 + n] += y[:n] * env(n, fade_in, fade_out) * g
    placed.append({"label": label, "t": round(t, 2), "end": round(t + n / SR, 2), "gain_db": gain_db})

def seg(path, a, b): return load(path)[int(a * SR):int(b * SR)]

def sfx(name, t, gain_db=-8, fade_in=0.01, fade_out=0.15, clip_len=None):
    f = P / f"sfx/{name}.wav"
    if not f.exists(): missing.append(name); return
    put(load(f), t, gain_db, fade_in, fade_out, f"sfx:{name}", clip_len)

def noise_bed(t0, t1, lo, hi, gain_db, lfo=0.0, seed=1):
    rng = np.random.default_rng(seed); n = int((t1 - t0) * SR)
    y = rng.normal(0, 1, n).astype(np.float32)
    sos = ss.butter(2, [lo / (SR / 2), hi / (SR / 2)], btype="band", output="sos"); y = ss.sosfilt(sos, y)
    if lfo: y *= (0.6 + 0.4 * np.sin(2 * np.pi * lfo * np.arange(n) / SR + rng.random() * 6)).astype(np.float32)
    y /= (np.abs(y).max() + 1e-9)
    put(np.stack([y, y * 0.9], -1), t0, gain_db, 1.0, 1.0, f"bed:{lo}-{hi}")

def crickets(t0, t1, gain_db):
    rng = np.random.default_rng(3); n = int((t1 - t0) * SR); t = np.arange(n) / SR
    chirp = (np.sin(2 * np.pi * 4200 * t) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 14 * t)))).astype(np.float32)
    gate = (np.sin(2 * np.pi * 1.1 * t + 1) > -0.2).astype(np.float32)
    y = chirp * gate; y = ss.sosfilt(ss.butter(2, [3000 / (SR / 2), 6000 / (SR / 2)], btype="band", output="sos"), y)
    y /= (np.abs(y).max() + 1e-9)
    put(np.stack([y, y * 0.8], -1), t0, gain_db, 1.5, 1.0, "bed:crickets")

def tuba(t, f0=58.0, dur=0.7, gain_db=-14):
    n = int(dur * SR); tt = np.arange(n) / SR
    y = sum((1 / k) * np.sin(2 * np.pi * f0 * k * tt) for k in range(1, 7)).astype(np.float32)
    y *= np.exp(-3.5 * tt) * np.minimum(1, tt / 0.02); y /= (np.abs(y).max() + 1e-9)
    put(np.stack([y, y], -1), t, gain_db, 0, 0.1, "tuba")

T1 = P / "music/theme_1.wav"; BOX = P / "music/breakdown_1.wav"
# --- music (cue map, script v2): 0-9 none; 9.2-12.6 pickup "Rollin' rollin' here we go" landing on Hank's "Rolling." at 12.3;
# 13.0 verse 1; 21.2 chorus; 33.5-46.5 music box; 45.1 chorus 2 "Nobody's too big" so "It's Hank and Doug's" lands at 49.0; 54+ silence
MUSIC_DB = -19.0
put(seg(T1, 2.6, 6.4), 9.2, MUSIC_DB, 0.05, 0.4, "music:pickup")
put(seg(T1, 9.4, 18.2), 13.0, MUSIC_DB, 0.05, 0.0, "music:verse1")
put(seg(T1, 18.2, 30.4), 21.8, MUSIC_DB, 0.0, 0.8, "music:chorus1")
put(seg(BOX, 0.0, 13.5), 33.3, MUSIC_DB - 4, 1.2, 1.0, "music:musicbox")
put(seg(T1, 30.0, 37.6), 45.1, MUSIC_DB, 0.6, 0.0, "music:chorus2")
put(seg(T1, 37.6, 40.0), 52.7, MUSIC_DB, 0.0, 1.2, "music:chord_out")
tuba(58.1)
put(seg(T1, 3.1, 6.0), 58.6, MUSIC_DB + 1, 0.02, 0.3, "music:sting", clip_len=1.4)

# --- voices (dialogue sits above the music)
V = -3.0
put(load(P / "voices/L1_hank_rolling.wav"), 12.3, V + 2, 0, 0.05, "line:L1 hank Rolling.")
put(load(P / "voices/N1_narrator_heart.wav"), 14.6, V - 1, 0, 0.05, "line:N1 narrator Somebody always hears the call.")
put(load(P / "voices/L2_doug_longago.wav"), 35.2, V, 0, 0.05, "line:L2 doug Long time ago... I hunted bears.")
put(load(P / "voices/L3_doug_metone.wav"), 39.4, V, 0, 0.05, "line:L3 doug Then I met one.")
put(load(P / "voices/L4_younghank_hi.wav"), 41.0, V + 4, 0, 0.05, "line:L4 young hank Hi.")
put(load(P / "voices/L5_doug_samenose.wav"), 46.3, V, 0, 0.05, "line:L5 doug Same nose. Same light. Different job.")
put(load(P / "voices/L6_hank_rolling2.wav"), 58.5, V, 0, 0.05, "line:L6 hank Rolling.")

# --- sound design (the ripple cues ARE the sound-event list)
noise_bed(0.0, 9.5, 120, 900, -26, lfo=0.3, seed=1)       # wind on linen
sfx("goat_bleat", 0.6, -9, clip_len=2.2)
sfx("paint_shhk", 0.95, -14, clip_len=1.6)
sfx("paint_shhk", 3.2, -16, clip_len=1.6)
sfx("marmot_whistle", 6.25, -8, clip_len=1.2)
sfx("paint_shhk", 6.35, -14, clip_len=1.6); sfx("paint_shhk", 6.85, -14, clip_len=1.6)
sfx("paint_shhk", 8.3, -15, clip_len=1.6)
sfx("hooves_wheels", 13.0, -16, fade_in=0.3, fade_out=0.6, clip_len=5.0)
sfx("wing_beats", 18.0, -16, fade_in=0.3, fade_out=0.6, clip_len=4.0)
sfx("goat_bleat", 20.8, -16, clip_len=0.9)
sfx("water_spray", 23.9, -12, fade_in=0.05, fade_out=0.5, clip_len=3.2)
sfx("kitten_mew", 27.6, -10, clip_len=1.4)
sfx("paint_shhk", 27.8, -20, clip_len=1.2)
sfx("otter_chirps", 30.4, -16, fade_in=0.2, fade_out=0.5, clip_len=3.2)
sfx("kitten_mew", 32.4, -16, clip_len=1.0)
crickets(34.0, 46.5, -30)
sfx("lantern_fall", 44.4, -10, clip_len=2.4)
sfx("chipmunk_squeak", 57.0, -9, clip_len=0.8)
sfx("paint_shhk", 57.05, -22, clip_len=0.8)

# --- static gain to about -14 LUFS is the final gate's job (final_audio_gate.py); here just keep peaks sane
# duck the music 9 dB under every spoken line (static dips with 0.15 s ramps; not a dynamic loudnorm)
duck = np.ones(N, np.float32)
for c in placed:
    if c["label"].startswith("line:"):
        a, b = int((c["t"] - 0.15) * SR), int((c["end"] + 0.25) * SR); r = int(0.15 * SR)
        duck[a:b] = np.minimum(duck[a:b], 10 ** (-9 / 20))
        duck[a - r:a] = np.minimum(duck[a - r:a], np.linspace(1, 10 ** (-9 / 20), r)); duck[b:b + r] = np.minimum(duck[b:b + r], np.linspace(10 ** (-9 / 20), 1, r))
bus += music_bus * duck[:, None]
# tame hot transients, then set the mix itself to -14 LUFS integrated with a STATIC gain (measured with ffmpeg ebur128),
# so final_audio_gate.py only confirms it (its own two-pass gain kept landing at -14.7 against the peak ceiling)
import subprocess, re, tempfile, os
def soft(b, k):
    over = np.abs(b) > k
    b[over] = np.sign(b[over]) * (k + (1 - k) * np.tanh((np.abs(b[over]) - k) / (1 - k))); return b
def lufs(b):
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name; sf.write(tmp, b, SR, subtype="FLOAT")
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", tmp, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    os.unlink(tmp); i = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1]); tp = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1]); return i, tp
bus = soft(bus, 0.40)
for _ in range(3):
    i, tp = lufs(bus); g = 10 ** ((-14.0 - i) / 20); bus *= g
    bus = soft(bus, 10 ** (-3.2 / 20))
i, tp = lufs(bus); print(f"mix loudness {i:.1f} LUFS, true peak {tp:.1f} dBTP")
peak = np.abs(bus).max()
sf.write(P / "final/mix_stereo.wav", bus, SR, subtype="PCM_24")
json.dump({"placed": placed, "missing_sfx": missing}, open(P / "final/mix_cues.json", "w"), indent=1)
print(f"mix -> final/mix_stereo.wav  peak {peak:.2f}  placed {len(placed)}  missing sfx: {missing}")
