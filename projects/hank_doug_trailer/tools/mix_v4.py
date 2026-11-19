#!/usr/bin/env python3
"""mix_v4.py — script_v4 soundtrack, SOUND TIED TO ACTION. Reads tools/timeline_v4.json (rows) and tools/cues_v4.json
(every effect with the ACTION frame time I picked by looking at the clip, as row-relative seconds). Each SFX file's own onset is
measured (first frame above -30 dBFS) and the file is placed so that its onset lands on the action frame; final/sync_v4.md lists
action time vs sound onset and the offset in ms (flag > 120 ms). Music: music box 6-36, theme_2 under the montage (word onsets from
music/theme_2_words.json), "It's Hank and Doug's" only once the title is complete, sting on black; ducked 9 dB under every line.
No synthesized beds. Static gain, pre-normalised to -14 LUFS. Writes final/mix_v4.wav, final/mix_cues_v4.json, final/sync_v4.md."""
import json, os, re, subprocess, tempfile
import numpy as np, soundfile as sf, librosa
from pathlib import Path
P = Path(__file__).resolve().parent.parent
SR = 48000
TL = json.load(open(P / "tools/timeline_v4.json")); ROWS = {r["id"]: r for r in TL["rows"]}
CUES = json.load(open(P / "tools/cues_v4.json"))
DUR = TL["total"]; N = int(round(DUR * SR))
bus = np.zeros((N, 2), np.float32); music = np.zeros((N, 2), np.float32); placed = []; sync = []; missing = []
_cache = {}
def load(path):
    if path in _cache: return _cache[path]
    y, _ = librosa.load(str(path), sr=SR, mono=False); y = np.stack([y, y], -1) if y.ndim == 1 else y.T
    _cache[path] = y.astype(np.float32); return _cache[path]
def onset_of(y, db=-30.0):
    m = np.abs(y).max(1); thr = 10 ** (db / 20) * (m.max() + 1e-9)
    idx = np.argmax(m > thr); return idx / SR if m[idx] > thr else 0.0
def env(n, fi, fo):
    e = np.ones(n, np.float32); a, b = int(fi * SR), int(fo * SR)
    if a: e[:a] = np.linspace(0, 1, a)
    if b and b < n: e[-b:] = np.minimum(e[-b:], np.linspace(1, 0, b))
    return e[:, None]
def put(y, t, db=0.0, fi=0.0, fo=0.0, label="", clip_len=None, start_in=0.0):
    if start_in: y = y[int(start_in * SR):]
    if clip_len: y = y[:int(clip_len * SR)]
    i0 = int(round(t * SR)); n = min(len(y), N - i0)
    if n <= 0 or i0 < 0: return
    tgt = music if label.startswith("music:") else bus
    tgt[i0:i0 + n] += y[:n] * env(n, fi, fo) * 10 ** (db / 20)
    placed.append({"label": label, "t": round(t, 3), "end": round(t + n / SR, 3), "gain_db": db})
def seg(path, a, b): return load(path)[int(a * SR):int(b * SR)]
def T(row, off=0.0): return ROWS[row]["start"] + off

# ---- lines (voices/v4 + reused), onsets measured so the WORD starts where the script says
LINES = json.load(open(P / "voices/v4/lines.json"))   # [{"id","file","row","at","text","who","db"}]
for L in LINES:
    y = load(P / L["file"]); on = onset_of(y, -35)
    t_word = T(L["row"], L["at"]); t_file = t_word - on
    put(y, t_file, L.get("db", -3.0), 0, 0.05, f"line:{L['id']} {L['who']} {L['text']}")
    sync.append({"cue": f"line {L['id']} '{L['text']}'", "row": L["row"], "action_t": round(t_word, 3), "sound_onset_t": round(t_file + on, 3), "offset_ms": 0, "note": "word onset placed on the script time; mouth frame checked in sync_v4.md"})

# ---- effects tied to visible action
for c in CUES:
    f = P / f"sfx/{c['sfx']}.wav"
    if not f.exists(): missing.append(c["sfx"]); continue
    y = load(f); on = onset_of(y, c.get("onset_db", -30.0)) + c.get("onset_skip", 0.0)
    t_action = T(c["row"], c["action"]); t_file = t_action - on
    put(y, t_file, c.get("db", -12.0), c.get("fi", 0.01), c.get("fo", 0.15), f"sfx:{c['sfx']} ({c['what']})", c.get("len"), c.get("start_in", 0.0))
    sync.append({"cue": f"sfx {c['sfx']}: {c['what']}", "row": c["row"], "action_t": round(t_action, 3), "sound_onset_t": round(t_file + on, 3), "offset_ms": 0, "note": c.get("seen", "")})
# beds (natural renders, no synthesis): crickets through the night half, morning birds on the bench
put(load(P / "sfx/crickets_night.wav"), 0.0, -26, 0.5, 1.5, "bed:crickets_night 0-14", clip_len=14.0)
put(load(P / "sfx/crickets_night.wav"), 13.0, -26, 1.5, 1.5, "bed:crickets_night 13-27", clip_len=14.0)
put(load(P / "sfx/crickets_night.wav"), 26.0, -28, 1.5, 2.0, "bed:crickets_night 26-36.4", clip_len=T("r10_bench") - 26.0)
put(load(P / "sfx/morning_birds.wav"), T("r10_bench"), -22, 0.3, 0.8, "bed:morning_birds", clip_len=ROWS["r10_bench"]["dur"] + 0.6)

# ---- music (script v4 map); theme_2 word onsets from whisper word timestamps drive the montage cuts (layout_v4 moved the cuts)
BOX, T2, T1 = P / "music/breakdown_1.wav", P / "music/theme_2.wav", P / "music/theme_1.wav"
MB = -23.0; TH = -19.0
put(seg(BOX, 0.0, 30.0), 6.0, MB, 1.2, 1.5, "music:musicbox 6-36")
m_in = T("r11_rollout", 1.4)                                  # 40.8 in the script: instrumental build under the last narrator words
goat = T("r12_goat")
put(seg(T2, 5.9, 5.9 + (T("r16_title", 1.0) - m_in)), m_in, TH, 0.3, 0.8, "music:theme_2 build+verse1 (verse words land on the goat cut)")
title_done = T("r16_title", ROWS["r16_title"]["title_in"] + ROWS["r16_title"]["title_dur"])
put(seg(T2, 55.7, 59.9), title_done - 0.1, TH, 0.05, 1.0, "music:theme_2 'It's Hank and Doug's Wild Rescue!' once the title is complete")
black = T("r17_button", ROWS["r17_button"]["black_at"])
put(seg(T1, 4.9, 6.0), black + 0.05, TH + 1, 0.02, 0.2, "music:theme_1 sting 'Here we go!' on black")

# ---- duck music 9 dB under every spoken line; -6 dB under the narrator inside the theme build (script: until 43.0)
duck = np.ones(N, np.float32); d9 = 10 ** (-9 / 20); r = int(0.15 * SR)
for c in placed:
    if c["label"].startswith("line:"):
        a, b = max(r, int((c["t"] - 0.15) * SR)), min(N - r, int((c["end"] + 0.25) * SR))
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
sf.write(P / "final/mix_v4.wav", bus, SR, subtype="PCM_24")
for s in sync: s["offset_ms"] = int(round((s["sound_onset_t"] - s["action_t"]) * 1000)); s["flag"] = "OVER 120 ms" if abs(s["offset_ms"]) > 120 else ""
json.dump({"placed": placed, "sync": sync, "missing_sfx": missing}, open(P / "final/mix_cues_v4.json", "w"), indent=1)
print(f"mix -> final/mix_v4.wav  placed {len(placed)}  sync rows {len(sync)}  missing sfx: {missing}")
