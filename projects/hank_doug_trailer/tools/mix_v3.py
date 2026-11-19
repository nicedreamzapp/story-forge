#!/usr/bin/env python3
"""mix_v3.py — fix-pass soundtrack. Reads final/cuts_v3.json for the real beat times. Theme = the take whisper heard singing
"Doug" (theme_2) for the sung sections; theme_1 only for the 2 s "Rollin'! Here we go!" sting (no name in it).
No synthesized beds (the v2 gated 4.2 kHz cricket synth was the "alarm"); natural MMAudio ambience instead; no paint_shhk.
Static gain, ducked 9 dB under lines, pre-normalised to -14 LUFS. Writes final/mix_v3.wav + final/mix_cues_v3.json."""
import json, os, re, subprocess, tempfile
import numpy as np, soundfile as sf, librosa
from pathlib import Path
P = Path(__file__).resolve().parent.parent
SR = 48000
cuts = {c["id"]: c for c in json.load(open(P / "final/cuts_v3.json"))["cuts"]}
DUR = max(60.0, json.load(open(P / "final/cuts_v3.json"))["total"]); N = int(round(DUR * SR))
bus = np.zeros((N, 2), np.float32); music = np.zeros((N, 2), np.float32); placed = []; missing = []
def T(bid, off=0.0): return cuts[bid]["start"] + off if bid in cuts else None
def load(path):
    y, _ = librosa.load(str(path), sr=SR, mono=False)
    y = np.stack([y, y], -1) if y.ndim == 1 else y.T
    return y.astype(np.float32)
def env(n, fi, fo):
    e = np.ones(n, np.float32); a, b = int(fi * SR), int(fo * SR)
    if a: e[:a] = np.linspace(0, 1, a)
    if b: e[-b:] = np.minimum(e[-b:], np.linspace(1, 0, b))
    return e[:, None]
def put(y, t, db=0.0, fi=0.0, fo=0.0, label="", clip_len=None):
    if t is None: return
    if clip_len: y = y[:int(clip_len * SR)]
    i0 = int(t * SR); n = min(len(y), N - i0)
    if n <= 0: return
    tgt = music if label.startswith("music:") else bus
    tgt[i0:i0 + n] += y[:n] * env(n, fi, fo) * 10 ** (db / 20)
    placed.append({"label": label, "t": round(t, 2), "end": round(t + n / SR, 2), "gain_db": db})
def seg(path, a, b): return load(path)[int(a * SR):int(b * SR)]
def sfx(name, t, db=-10, fi=0.02, fo=0.2, clip_len=None):
    f = P / f"sfx/{name}.wav"
    if not f.exists(): missing.append(name); return
    put(load(f), t, db, fi, fo, f"sfx:{name}", clip_len)

T1, T2, BOX = P / "music/theme_1.wav", P / "music/theme_2.wav", P / "music/breakdown_1.wav"
# cue map on the v3 beats: pickup under the bench, verse from the rollout, chorus from the turtle, music box through the flashback,
# chorus 2 from the walk-away so "It's Hank and Doug's Wild Rescue" lands on the title, silence + tuba + sting on the button
M = -19.0
t_bench, t_roll, t_turtle, t_forest, t_walk, t_title, t_button = T("b03_bench"), T("b04_rollout"), T("b06_turtle"), T("b09_forest"), T("b12_walkaway"), T("b13_title"), T("b14_button")
put(seg(T2, 1.0, 6.2), t_bench - 0.6, M, 0.05, 0.3, "music:pickup (theme_2 'Who's that coming... here we go')")
put(seg(T2, 9.3, 18.2), t_roll, M, 0.05, 0.2, "music:verse1 (theme_2 first two lines)")
put(seg(T2, 27.2, 27.2 + (t_forest - t_turtle) + 0.6), t_turtle, M, 0.2, 0.9, "music:chorus1 (theme_2 'Hank and Doug!')")
put(seg(BOX, 0.0, (t_walk - t_forest) + 1.0), t_forest - 0.4, M - 4, 1.0, 1.0, "music:musicbox")
c2_len = (t_button - t_walk) + 0.4
put(seg(T2, 48.0, 48.0 + c2_len), t_walk - 0.2, M, 0.6, 0.8, "music:chorus2 (theme_2 'Nobody's too big...' to 'It's Hank and Doug's Wild Rescue!')")
put(seg(T1, 3.1, 6.0), t_button + 3.4, M + 1, 0.02, 0.3, "music:sting (theme_1 'Rollin'! Here we go!')", clip_len=1.1)

# lines (times from the clips' own mouth motion where there is one)
V = -3.0
put(load(P / "voices/L1_hank_rolling.wav"), t_bench + 2.4, V + 2, 0, 0.05, "line:L1 hank Rolling.")
put(load(P / "voices/N1_narrator_heart.wav"), t_roll + 1.2, V - 1, 0, 0.05, "line:N1 narrator Somebody always hears the call.")
put(load(P / "voices/L2_doug_longago.wav"), t_forest + 1.0, V, 0, 0.05, "line:L2 doug Long time ago... I hunted bears.")
put(load(P / "voices/L3_doug_metone.wav"), T("b10_hi") + 0.3, V, 0, 0.05, "line:L3 doug Then I met one.")
put(load(P / "voices/L4_younghank_hi.wav"), T("b10_hi") + 2.0, V + 4, 0, 0.05, "line:L4 young_hank Hi.")
put(load(P / "voices/L5_doug_samenose.wav"), t_walk + 0.3, V, 0, 0.05, "line:L5 doug Same nose. Same light. Different job.")
put(load(P / "voices/L6_hank_rolling2.wav"), t_button + 2.0, V, 0, 0.05, "line:L6 hank Rolling.")

# sound design, natural only
sfx("wind_mountain", 0.0, -24, 1.0, 1.5, clip_len=9.0)
sfx("goat_bleat", T("b00_goat") + 0.8, -9, clip_len=2.2)
sfx("marmot_chirp", T("b02_marmot") + 1.2, -12, clip_len=1.3)
sfx("hooves_wheels", t_roll, -16, 0.3, 0.6, clip_len=5.0)
sfx("wing_beats", T("b05_airlift"), -16, 0.3, 0.6, clip_len=4.0)
sfx("goat_bleat", T("b05_airlift") + 2.6, -16, clip_len=0.9)
sfx("water_spray", t_turtle + 0.6, -12, 0.05, 0.5, clip_len=3.2)
sfx("kitten_mew", T("b07_kitten") + 1.5, -10, clip_len=1.4)
sfx("otter_chirps", T("b08_otters") + 0.3, -16, 0.2, 0.5, clip_len=3.2)
sfx("kitten_mew", T("b08_otters") + 2.4, -16, clip_len=1.0)
sfx("crickets_night", t_forest - 0.3, -26, 1.5, 1.0, clip_len=(t_walk - t_forest) + 1.0)
sfx("lantern_fall", T("b11_ditch") + 0.4, -14, 0.05, 0.4, clip_len=2.4)   # the hiss of the flame going out
sfx("chipmunk_squeak", t_button + 1.3, -9, clip_len=0.8)

# duck music 9 dB under every line, static dips
duck = np.ones(N, np.float32); d9 = 10 ** (-9 / 20); r = int(0.15 * SR)
for c in placed:
    if c["label"].startswith("line:"):
        a, b = int((c["t"] - 0.15) * SR), int((c["end"] + 0.25) * SR)
        duck[a:b] = np.minimum(duck[a:b], d9); duck[a - r:a] = np.minimum(duck[a - r:a], np.linspace(1, d9, r)); duck[b:b + r] = np.minimum(duck[b:b + r], np.linspace(d9, 1, r))
bus += music * duck[:, None]
def soft(b, k):
    o = np.abs(b) > k; b[o] = np.sign(b[o]) * (k + (1 - k) * np.tanh((np.abs(b[o]) - k) / (1 - k))); return b
def lufs(b):
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name; sf.write(tmp, b, SR, subtype="FLOAT")
    rr = subprocess.run(["ffmpeg", "-v", "info", "-i", tmp, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    os.unlink(tmp); return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", rr)[-1]), float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", rr)[-1])
bus = soft(bus, 0.40)
for _ in range(3):
    i, tp = lufs(bus); bus *= 10 ** ((-14.0 - i) / 20); bus = soft(bus, 10 ** (-3.2 / 20))
i, tp = lufs(bus); print(f"mix loudness {i:.1f} LUFS, true peak {tp:.1f} dBTP")
sf.write(P / "final/mix_v3.wav", bus, SR, subtype="PCM_24")
json.dump({"placed": placed, "missing_sfx": missing}, open(P / "final/mix_cues_v3.json", "w"), indent=1)
print(f"mix -> final/mix_v3.wav  placed {len(placed)}  missing sfx: {missing}")
