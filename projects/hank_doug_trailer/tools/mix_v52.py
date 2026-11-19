#!/usr/bin/env python3
"""mix_v52.py — v5.2 soundtrack: voices + ONE continuous song, no AI sound effects (Matt 1:52-1:53 PM: the MMAudio effects
"just sound like static"; "same song in the whole trailer"). Reads tools/timeline_v52.json (music.song, rows) and
tools/lines_v5.json. The song plays from film 0.0 at song 0.0 with ONE gain envelope: SONG_BED dB under the narrated story
(rows 1-11), rising over the rescues (rows 12-15) to SONG_FULL by the title bar, then full to the end; it ducks 9 dB under
every spoken line (150 ms ramps). Loudness -14 LUFS, soft limiter. Writes final/mix_v52.wav, final/stems_v52/{music,voices}.wav,
final/mix_cues_v52.json. Set KEEP_SFX=1 to also place the cues listed in tools/sfx_keep_v52.json (default: none)."""
import json, os, re, subprocess, tempfile, sys
import numpy as np, soundfile as sf, librosa
from pathlib import Path
P = Path(__file__).resolve().parent.parent; SR = 48000
TL = json.load(open(P / "tools/timeline_v52.json")); ROWS = {r["id"]: r for r in TL["rows"]}; MU = TL["music"]
DUR = TL["total"]; N = int(round(DUR * SR))
SONG_BED, SONG_FULL = -22.0, -12.0           # dB on the song under the story / in the anthem
bus = np.zeros((N, 2), np.float32); music = np.zeros((N, 2), np.float32); voices = np.zeros((N, 2), np.float32); placed = []
def load(path):
    y, _ = librosa.load(str(path), sr=SR, mono=False); return (np.stack([y, y], -1) if y.ndim == 1 else y.T).astype(np.float32)
def onset_of(y, db=-35.0):
    m = np.abs(y).max(1); thr = 10 ** (db / 20) * (m.max() + 1e-9); i = np.argmax(m > thr); return i / SR if m[i] > thr else 0.0
def put(tgt, y, t, db=0.0, fo=0.05, label=""):
    i0 = int(round(t * SR)); n = min(len(y), N - i0)
    if n <= 0: return
    e = np.ones(n, np.float32); b = int(fo * SR)
    if b and b < n: e[-b:] = np.linspace(1, 0, b)
    tgt[i0:i0 + n] += y[:n] * e[:, None] * 10 ** (db / 20); placed.append({"label": label, "t": round(t, 3), "end": round(t + n / SR, 3), "gain_db": db})
T = lambda row, off=0.0: ROWS[row]["start"] + off
# ---- lines (same words, same script times; L4 is now the Hank-voice take)
for L in json.load(open(P / "tools/lines_v5.json")):
    if L["row"] not in ROWS: continue
    y = load(P / L["file"]); on = onset_of(y); t_word = T(L["row"], L["at"]); put(voices, y, t_word - on, L.get("db", -3.0), 0.05, f"line:{L['id']} {L['who']} {L['text']}")
# ---- optional kept effects (none by default)
if os.getenv("KEEP_SFX") == "1" and (P / "tools/sfx_keep_v52.json").exists():
    CLEAN = json.load(open(P / "sfx/v5/clean/clean.json"))
    for c in json.load(open(P / "tools/sfx_keep_v52.json")):
        info = CLEAN.get(f"{c['row']}__{c['sfx']}", {}); y = load(P / info["file"]); put(bus, y, T(c["row"], c["action"]) - info["onset_in_file"], c.get("db", -14.0), 0.15, f"sfx:{c['sfx']}")
# ---- the one song, continuous from 0, one envelope
OFF = int(MU.get("song_offset", 0.0) * SR)
song = load(P / MU["song"])[OFF:]; n = min(len(song), N); music[:n] = song[:n]
if MU.get("song_bed"):   # the same song's instrumental stem under the story, crossfading (0.6 s) into the full mix at vocal_in
    bed = load(P / MU["song_bed"])[OFF:]; nb = min(len(bed), n); vi = int(MU["vocal_in"] * SR); xf = int(0.6 * SR)
    w = np.ones(n, np.float32); w[:max(0, vi - xf)] = 0.0; w[max(0, vi - xf):vi] = np.linspace(0, 1, vi - max(0, vi - xf)); w = w[:, None]
    music[:nb] = bed[:nb] * (1 - w[:nb]) + music[:nb] * w[:nb]
env = np.full(N, 10 ** (SONG_BED / 20), np.float32)
r12 = T("r12_goat") if "r12_goat" in ROWS else T("r11_rollout"); tb = MU["title_bar"]; i0, i1 = int(r12 * SR), int(tb * SR)
env[i0:i1] = 10 ** (np.linspace(SONG_BED, SONG_FULL, max(1, i1 - i0)) / 20); env[i1:] = 10 ** (SONG_FULL / 20)
duck = np.ones(N, np.float32); d9 = 10 ** (-9 / 20); r = int(0.15 * SR)
for c in placed:
    if c["label"].startswith("line:"):
        a_, b_ = max(r, int((c["t"] - 0.15) * SR)), min(N - r, int((c["end"] + 0.25) * SR))
        duck[a_:b_] = np.minimum(duck[a_:b_], d9); duck[a_ - r:a_] = np.minimum(duck[a_ - r:a_], np.linspace(1, d9, r)); duck[b_:b_ + r] = np.minimum(duck[b_:b_ + r], np.linspace(d9, 1, r))
music *= (env * duck)[:, None]
placed.append({"label": f"music:{MU['song']} continuous from 0, bed {SONG_BED} dB -> full {SONG_FULL} dB by the title bar {tb}", "t": 0.0, "end": round(n / SR, 3), "gain_db": SONG_BED})
bus += voices + music
def soft(b, k):
    o = np.abs(b) > k; b[o] = np.sign(b[o]) * (k + (1 - k) * np.tanh((np.abs(b[o]) - k) / (1 - k))); return b
def lufs(b):
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name; sf.write(tmp, b, SR, subtype="FLOAT")
    rr = subprocess.run(["ffmpeg", "-v", "info", "-i", tmp, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    os.unlink(tmp); return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", rr)[-1]), float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", rr)[-1])
bus = soft(bus, 0.40); G = 1.0
for _ in range(3):
    i, tp = lufs(bus); g = 10 ** ((-14.0 - i) / 20); bus *= g; G *= g; bus = soft(bus, 10 ** (-3.2 / 20))
i, tp = lufs(bus); print(f"mix loudness {i:.1f} LUFS, true peak {tp:.1f} dBTP, stem gain {20*np.log10(G):+.1f} dB")
sf.write(P / "final/mix_v52.wav", bus, SR, subtype="PCM_24"); (P / "final/stems_v52").mkdir(exist_ok=True)
sf.write(P / "final/stems_v52/music.wav", music * G, SR, subtype="PCM_24"); sf.write(P / "final/stems_v52/voices.wav", voices * G, SR, subtype="PCM_24")
json.dump({"placed": placed}, open(P / "final/mix_cues_v52.json", "w"), indent=1)
print(f"mix -> final/mix_v52.wav  placed {len(placed)} (voices {sum(1 for p in placed if p['label'].startswith('line:'))}, sfx {sum(1 for p in placed if p['label'].startswith('sfx:'))}, music 1)")
