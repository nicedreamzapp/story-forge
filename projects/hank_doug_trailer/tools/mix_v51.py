#!/usr/bin/env python3
"""mix_v51.py — v5.1 soundtrack = mix_v5 with the score sources read from tools/music_v51.json (regenerated clean theme,
Matt 11/18 1:01 PM "nice music not some lame hissing static") and the three stems written to final/stems_v51/ for the per-row
audit. Original mix_v5 docstring: plan_v5 soundtrack (copied from mix_v4.py; v4 untouched). Changes from v4:
- NO beds: the crickets bed is gone; morning birds are one soft cue on the bench row (cues_v5.json).
- every effect is the CLEANED clip from sfx/v5/clean (tools/sfx_clean_v5.py: HP 100 / LP 9k / 50% stationary denoise /
  hard gate to the action window / -6 dBFS peak); its action onset inside the file comes from clean.json, so it lands on
  the action frame in cues_v5.json. Only the hero + soft sounds the plan keeps; chipmunk, snore, tuba dropped (ending A).
- music box from 0:00 at -30 dB rising to -23 dB by 0:06; the 30 s box is extended to the bench with ONE beat-aligned
  1.5 s crossfade (box 20.15 -> box 2.41), fading out into the bench row.
- stopdown: the sung verse ducks to -30 dB over 51.30-51.70 and stops at 51.70 (otter chirp carries a 120 ms reverb tail);
  "It's Hank and Doug's Wild Rescue!" hits full on its downbeat at 51.80; music only on the title; sting on black.
- the 'Rolling.' mumble on the old button (L6) is gone (tools/lines_v5.json).
Writes final/mix_v5.wav, final/mix_cues_v5.json, final/sync_v5.md-ready json."""
import json, os, re, subprocess, tempfile
import numpy as np, soundfile as sf, librosa
from pathlib import Path
P = Path(__file__).resolve().parent.parent
SR = 48000
TL = json.load(open(P / "tools/timeline_v5.json")); ROWS = {r["id"]: r for r in TL["rows"]}; MU = TL["music"]
CUES = json.load(open(P / "tools/cues_v5.json"))
CLEAN = json.load(open(P / "sfx/v5/clean/clean.json"))
DUR = TL["total"]; N = int(round(DUR * SR))
bus = np.zeros((N, 2), np.float32); music = np.zeros((N, 2), np.float32); placed = []; sync = []; missing = []
voices = np.zeros((N, 2), np.float32)   # v5.1 stem
MC = json.load(open(P / "tools/music_v51.json"))
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
    i0 = int(round(t * SR))
    if i0 < 0: y = y[-i0:]; i0 = 0
    n = min(len(y), N - i0)
    if n <= 0: return
    tgt = music if label.startswith("music:") else bus
    tgt[i0:i0 + n] += y[:n] * env(n, fi, fo) * 10 ** (db / 20)
    if label.startswith("line:"): voices[i0:i0 + n] += y[:n] * env(n, fi, fo) * 10 ** (db / 20)
    placed.append({"label": label, "t": round(t, 3), "end": round(t + n / SR, 3), "gain_db": db})
def seg(path, a, b): return load(path)[int(a * SR):int(b * SR)]
def T(row, off=0.0): return ROWS[row]["start"] + off

# ---- lines (unchanged words; L6 dropped with the button)
LINES = json.load(open(P / "tools/lines_v5.json"))
for L in LINES:
    y = load(P / L["file"]); on = onset_of(y, -35)
    t_word = T(L["row"], L["at"]); t_file = t_word - on
    put(y, t_file, L.get("db", -3.0), 0, 0.05, f"line:{L['id']} {L['who']} {L['text']}")
    sync.append({"cue": f"line {L['id']} '{L['text']}'", "row": L["row"], "action_t": round(t_word, 3), "sound_onset_t": round(t_file + on, 3), "offset_ms": 0, "note": "word onset placed on the script time"})

# ---- effects: cleaned clips, onset inside the file known from the clean pass
for c in CUES:
    k = f"{c['row']}__{c['sfx']}"; info = CLEAN.get(k, {})
    if "file" not in info: missing.append(k); continue
    y = load(P / info["file"]); on = info["onset_in_file"]
    t_action = T(c["row"], c["action"]); t_file = t_action - on
    put(y, t_file, c.get("db", -12.0), max(0.01, c.get("fi", 0.01)), max(0.01, c.get("fo", 0.15)), f"sfx:{c['sfx']} ({c['what']})")
    sync.append({"cue": f"sfx {c['sfx']}{' [HERO]' if c.get('hero') else ''}: {c['what']}", "row": c["row"], "action_t": round(t_action, 3),
                 "sound_onset_t": round(t_file + on, 3), "offset_ms": 0, "note": c.get("seen", ""), "recheck": c.get("recheck", "")})

# ---- music
BOX, T2, T1 = P / MC["box"], P / MC["theme"], P / MC.get("sting_file", MC["theme"])   # v5.1 sources
MB = -23.0; TH = -19.0
bench = T("r10_bench"); XF = 1.5; CUT_A, CUT_B = 20.15, 2.41          # beat-aligned box loop (librosa beats)
box = seg(BOX, 0.0, CUT_A + XF)
fade = np.sqrt(np.linspace(1, 0, int(XF * SR)))[:, None]
box[-len(fade):] *= fade
tail = seg(BOX, CUT_B, CUT_B + (bench + 0.6 - CUT_A)).copy()
tail[:len(fade)] *= fade[::-1]
full = np.zeros((int((bench + 0.6) * SR) + 10, 2), np.float32)
full[:len(box)] += box; full[int(CUT_A * SR):int(CUT_A * SR) + len(tail)] += tail[:len(full) - int(CUT_A * SR)]
r0, r1, rt = MU["box_ramp"]                                            # -30 dB at 0 rising to -23 dB by 6 s
ramp = np.ones(len(full), np.float32); k6 = int(rt * SR); ramp[:k6] = 10 ** (np.linspace(r0 - r1, 0, k6) / 20)
full *= ramp[:, None]
put(full, 0.0, MB, 0.3, 1.6, "music:musicbox 0-36.9 (ramp -30 -> -23 dB by 0:06, one crossfade loop at 20.15)")
m_in = T("r11_rollout", 1.4)
sd_a, sd_b, sd_db = MU["stopdown"]
VS = MC["verse_src"]; verse = seg(T2, VS, VS + (sd_b - m_in)).copy()
i_a = int((sd_a - m_in) * SR); g = 10 ** ((sd_db - TH) / 20)
verse[i_a:] *= np.linspace(1, g, len(verse) - i_a)[:, None]
put(verse, m_in, TH, 0.3, 0.02, "music:theme_2 build+verse1, stopdown 51.30-51.70 to -30 dB")
a, b = MC["title_phrase_src"]; t_its = MC["t_its"]                      # "It's" onset in the v5.1 theme (whisper words)
black = T("r17_black")
put(seg(T2, a, b), MU["title_downbeat"] - (t_its - a), TH, 0.02, 1.0, "music:theme_2 'It's Hank and Doug's Wild Rescue!' on the downbeat")
sa, sb = MC["sting_src"]
put(seg(T1, sa, sb), black + 0.05, TH + 1, 0.02, 0.2, "music:theme_1 sting 'Here we go!' on black")
# music only after the stopdown: nothing on the effects bus past 51.45 (the otter reverb tail) except the sting (music bus)
bus[int(51.45 * SR):] *= 0.0

# ---- duck music 9 dB under every spoken line
duck = np.ones(N, np.float32); d9 = 10 ** (-9 / 20); r = int(0.15 * SR)
for c in placed:
    if c["label"].startswith("line:"):
        a_, b_ = max(r, int((c["t"] - 0.15) * SR)), min(N - r, int((c["end"] + 0.25) * SR))
        duck[a_:b_] = np.minimum(duck[a_:b_], d9); duck[a_ - r:a_] = np.minimum(duck[a_ - r:a_], np.linspace(1, d9, r)); duck[b_:b_ + r] = np.minimum(duck[b_:b_ + r], np.linspace(d9, 1, r))
bus_fx = bus.copy(); bus += music * duck[:, None]
def soft(b, k):
    o = np.abs(b) > k; b[o] = np.sign(b[o]) * (k + (1 - k) * np.tanh((np.abs(b[o]) - k) / (1 - k))); return b
def lufs(b):
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name; sf.write(tmp, b, SR, subtype="FLOAT")
    rr = subprocess.run(["ffmpeg", "-v", "info", "-i", tmp, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    os.unlink(tmp); return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", rr)[-1]), float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", rr)[-1])
bus = soft(bus, 0.40); G = 1.0
for _ in range(3):
    i, tp = lufs(bus); g = 10 ** ((-14.0 - i) / 20); bus *= g; G *= g; bus = soft(bus, 10 ** (-3.2 / 20))
print(f"stem gain (the loudness scaling, without the soft clip): {20*np.log10(G):+.1f} dB")
i, tp = lufs(bus); print(f"mix loudness {i:.1f} LUFS, true peak {tp:.1f} dBTP")
sf.write(P / "final/mix_v51.wav", bus, SR, subtype="PCM_24")
(P / "final/stems_v51").mkdir(exist_ok=True)
sf.write(P / "final/stems_v51/music.wav", music * duck[:, None] * G, SR, subtype="PCM_24"); sf.write(P / "final/stems_v51/voices.wav", voices * G, SR, subtype="PCM_24")
sf.write(P / "final/stems_v51/sfx.wav", bus_fx * G, SR, subtype="PCM_24")
for s in sync: s["offset_ms"] = int(round((s["sound_onset_t"] - s["action_t"]) * 1000)); s["flag"] = "OVER 120 ms" if abs(s["offset_ms"]) > 120 else ""
json.dump({"placed": placed, "sync": sync, "missing_sfx": missing}, open(P / "final/mix_cues_v51.json", "w"), indent=1)
print(f"mix -> final/mix_v51.wav  placed {len(placed)}  sync rows {len(sync)}  missing sfx: {missing}")
