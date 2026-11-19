#!/usr/bin/env python3
"""mix_v52b.py — the v5.2 soundtrack, engineered as one trailer mix (Matt 11/18 1:52-2:07 PM: "sounds need to flow and not sound
like a hodge podge of edits and clips", "static instead of the real sound effect", "same song in the whole trailer").
Reads tools/timeline_v52.json (rows, music), tools/lines_v5.json (voices), tools/cues_v52.json (real CC0 effects from sfx/library).
  MUSIC  one song, continuous from film 0: its demucs instrumental stem under the narrated story, crossfading (1 bar) into the
         full mix at music.vocal_in (the chorus bar); one slow gain envelope (bed under the story, rising through the rescues to
         full by the title bar); a short stopdown on the half-bar before the title bar; sidechain ducking under every voice with a
         smooth detector (40 ms attack, 500 ms release), max DUCK dB, so it breathes instead of pumping.
  VOICES placed by word onset on the script times (same as v5); Hank's "Hi." is the same voice as "Rolling." (voice_hi_v52).
  SFX    each cue: slice from the library file, high-pass (hp Hz), low-pass (lp Hz), a gentle -2 dB top shelf above 6 kHz,
         raised-cosine fade in/out, peak -6 dBFS then its mix gain, placed on the visible action frame. Nothing AI-generated.
  BED    one optional clean ambience bed per row range (cues with "bed": true), long fades, low level.
  OUT    soft-knee limiter, -14 LUFS, true peak -1 (final_audio_gate does the certified last pass). Writes final/mix_v52.wav,
         final/stems_v52/{music,voices,sfx}.wav and final/mix_cues_v52.json (for the sync table + manifest)."""
import json, os, re, subprocess, tempfile
import numpy as np, soundfile as sf, librosa
from scipy.signal import butter, sosfiltfilt
from pathlib import Path
P = Path(__file__).resolve().parent.parent; SR = 48000
TL = json.load(open(P / "tools/timeline_v52.json")); ROWS = {r["id"]: r for r in TL["rows"]}; MU = TL["music"]
DUR = TL["total"]; N = int(round(DUR * SR))
SONG_BED, SONG_FULL, DUCK = float(MU.get("bed_db", -21.0)), float(MU.get("full_db", -11.0)), float(MU.get("duck_db", -7.0))
music = np.zeros((N, 2), np.float32); voices = np.zeros((N, 2), np.float32); sfx = np.zeros((N, 2), np.float32); placed = []
def load(path, sr=SR):
    y, _ = librosa.load(str(path), sr=sr, mono=False); return (np.stack([y, y], -1) if y.ndim == 1 else y.T).astype(np.float32)
def onset_of(y, db=-35.0):
    m = np.abs(y).max(1); thr = 10 ** (db / 20) * (m.max() + 1e-9); i = int(np.argmax(m > thr)); return i / SR if m[i] > thr else 0.0
def fade(n, fi, fo):
    e = np.ones(n, np.float32); a, b = min(n // 2, int(fi * SR)), min(n // 2, int(fo * SR))
    if a: e[:a] = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, a))
    if b: e[-b:] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, b))
    return e
def put(tgt, y, t, db=0.0, fi=0.005, fo=0.05, label=""):
    i0 = int(round(t * SR)); j0 = 0
    if i0 < 0: j0 = -i0; i0 = 0
    n = min(len(y) - j0, N - i0)
    if n <= 0: return
    tgt[i0:i0 + n] += y[j0:j0 + n] * fade(n, fi, fo)[:, None] * 10 ** (db / 20)
    placed.append({"label": label, "t": round(i0 / SR, 3), "end": round((i0 + n) / SR, 3), "gain_db": db})
T = lambda row, off=0.0: ROWS[row]["start"] + off
# ---- voices
for L in json.load(open(P / "tools/lines_v5.json")):
    if L["row"] not in ROWS: continue
    y = load(P / L["file"]); on = onset_of(y); t_word = T(L["row"], L["at"])
    put(voices, y, t_word - on, L.get("db", -3.0), 0.005, 0.05, f"line:{L['id']} {L['who']} {L['text']}")
# ---- real sound effects
def eq(y, hp=120.0, lp=10000.0, shelf_db=-2.0):
    if hp: y = sosfiltfilt(butter(2, hp / (SR / 2), btype="high", output="sos"), y, axis=0)
    if lp and lp < SR / 2 - 1: y = sosfiltfilt(butter(2, lp / (SR / 2), btype="low", output="sos"), y, axis=0)
    if shelf_db: hi = y - sosfiltfilt(butter(2, 6000 / (SR / 2), btype="low", output="sos"), y, axis=0); y = y + (10 ** (shelf_db / 20) - 1) * hi
    return y.astype(np.float32)
CUES = json.load(open(P / "tools/cues_v52.json")) if (P / "tools/cues_v52.json").exists() else []
for c in CUES:
    if c["row"] not in ROWS: continue
    y = load(P / "sfx/library" / c["file"]); a0 = int(c.get("src_in", 0.0) * SR); a1 = int((c.get("src_in", 0.0) + c["len"]) * SR) if c.get("len") else len(y)
    y = y[a0:a1]
    if c.get("span"):   # beds: tile the file to the span with 1 s raised-cosine crossfades (no seam clicks)
        need = int(c["span"] * SR); xf = int(1.0 * SR); parts = y.copy()
        while len(parts) < need:
            w = (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, xf)))[:, None]; nxt = y.copy()
            parts = np.concatenate([parts[:-xf], parts[-xf:] * (1 - w) + nxt[:xf] * w, nxt[xf:]])
        y = parts[:need]
    if len(y) < SR // 20: continue
    y = eq(y, c.get("hp", 120.0), c.get("lp", 10000.0), c.get("shelf", -2.0)); y *= 10 ** (-6 / 20) / (np.abs(y).max() + 1e-9)
    if c.get("bed"):
        put(sfx, y, T(c["row"], c.get("action", 0.0)), c.get("db", -34.0), c.get("fi", 2.0), c.get("fo", 2.0), f"bed:{c['sfx']} {c.get('what','')}")
    else:
        on = onset_of(y, -30.0) if c.get("align_onset", True) else 0.0
        put(sfx, y, T(c["row"], c["action"]) - on, c.get("db", -16.0), c.get("fi", 0.01), c.get("fo", 0.25), f"sfx:{c['sfx']} {c.get('what','')}")
# ---- the one song
OFF = int(MU.get("song_offset", 0.0) * SR)
song = load(P / MU["song"])[OFF:]; n = min(len(song), N); full = np.zeros((N, 2), np.float32); full[:n] = song[:n]
if MU.get("song_bed"):
    bed = load(P / MU["song_bed"])[OFF:]; nb = min(len(bed), N)
    if MU.get("bed_lp"):   # the demucs instrumental's vocal-residue sits above ~7 kHz; a gentle low-pass under the narrated story
        bed = sosfiltfilt(butter(2, MU["bed_lp"] / (SR / 2), btype="low", output="sos"), bed, axis=0).astype(np.float32); inst = np.zeros((N, 2), np.float32); inst[:nb] = bed[:nb]
    vi = int(MU["vocal_in"] * SR); xf = int(MU.get("vocal_xfade", 2.0) * SR); w = np.zeros(N, np.float32)
    w[vi:] = 1.0; w[max(0, vi - xf):vi] = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, vi - max(0, vi - xf)))
    music = inst * (1 - w)[:, None] + full * w[:, None]
else: music = full
# gain envelope: bed under the story, ramp from the chorus bar (or rescue start) to full by the title bar, full after
env_db = np.full(N, SONG_BED, np.float32)
r_up0 = MU.get("ramp_from", MU.get("chorus_bar", 0.0)); tb = MU["title_bar"]; i0, i1 = int(r_up0 * SR), int(tb * SR)
if i1 > i0: env_db[i0:i1] = np.linspace(SONG_BED, SONG_FULL, i1 - i0)
env_db[i1:] = SONG_FULL
sd = MU.get("stopdown_db", -9.0); s0 = int((tb - MU.get("spb", 0.625) * 2) * SR); s1 = int((tb - 0.02) * SR)   # the half-bar before the title bar
if sd and s1 > s0: env_db[s0:s1] += np.linspace(0, sd, s1 - s0); env_db[s1:i1] += sd
# sidechain ducking under the voices: smooth detector, so no pumping
vmono = np.abs(voices).max(1); det = np.zeros(N, np.float32); att, rel = np.exp(-1 / (0.04 * SR)), np.exp(-1 / (0.5 * SR)); d = 0.0
blk = 480; vb = vmono[: (N // blk) * blk].reshape(-1, blk).max(1)   # 10 ms blocks for speed
db_ = np.zeros(len(vb), np.float32)
for i, v in enumerate(vb):
    d = v + (d - v) * (att ** blk if v > d else rel ** blk); db_[i] = d
det[: len(db_) * blk] = np.repeat(db_, blk); det[len(db_) * blk:] = db_[-1] if len(db_) else 0
thr = 10 ** (-40 / 20); amt = np.clip((20 * np.log10(det + 1e-9) + 40) / 20, 0, 1)   # full duck once the voice is 20 dB over -40 dBFS
duck_db = DUCK * amt
music *= (10 ** ((env_db + duck_db) / 20))[:, None]
placed.append({"label": f"music:{MU['song']} continuous from 0 (instrumental stem {MU.get('song_bed','-')} until {MU.get('vocal_in','-')}), bed {SONG_BED} dB -> full {SONG_FULL} dB by {tb}, stopdown {sd} dB on the half-bar before, duck {DUCK} dB under voices", "t": 0.0, "end": round(n / SR, 3), "gain_db": SONG_BED})
bus = voices + music + sfx
def soft(b, k):
    o = np.abs(b) > k; b[o] = np.sign(b[o]) * (k + (1 - k) * np.tanh((np.abs(b[o]) - k) / (1 - k))); return b
def lufs(b):
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name; sf.write(tmp, b, SR, subtype="FLOAT")
    rr = subprocess.run(["ffmpeg", "-v", "info", "-i", tmp, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    os.unlink(tmp); return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", rr)[-1]), float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", rr)[-1])
G = 1.0
for _ in range(3):
    i, tp = lufs(bus); g = 10 ** ((-14.0 - i) / 20); bus *= g; G *= g; bus = soft(bus, 10 ** (-2.0 / 20))
i, tp = lufs(bus); print(f"mix loudness {i:.1f} LUFS, true peak {tp:.1f} dBTP, stem gain {20*np.log10(G):+.1f} dB")
sf.write(P / "final/mix_v52.wav", bus, SR, subtype="PCM_24"); (P / "final/stems_v52").mkdir(exist_ok=True)
for nm, st in (("music", music), ("voices", voices), ("sfx", sfx)): sf.write(P / f"final/stems_v52/{nm}.wav", st * G, SR, subtype="PCM_24")
json.dump({"placed": placed}, open(P / "final/mix_cues_v52.json", "w"), indent=1)
print(f"mix -> final/mix_v52.wav  placed {len(placed)} (voices {sum(1 for p in placed if p['label'].startswith('line:'))}, sfx {sum(1 for p in placed if p['label'].startswith('sfx:'))}, beds {sum(1 for p in placed if p['label'].startswith('bed:'))}, music 1)")
