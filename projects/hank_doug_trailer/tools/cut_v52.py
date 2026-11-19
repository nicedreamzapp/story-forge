#!/usr/bin/env python3
"""cut_v52.py SONG.wav [--bpm 96] [--title-word-t SECONDS] [--end SECONDS]
v5.2 picture cut to ONE song (Matt 1:53 PM: same song all the way, no skipping; explorer anthem). Reads tools/timeline_v5.json
(row order, clips, replace_with) and writes tools/timeline_v52.json:
  - the song plays from film 0.0 at song 0.0, continuously, to its end (no music edits at all);
  - beats from librosa (tempo hinted by --bpm); bars = every 4th beat from the first strong beat;
  - every row START snaps to the nearest beat (half-beat for rows under 2 s) so cuts sit on the pulse, row order kept,
    durations re-derived from the snapped starts; row 16 (title) starts on the bar line at/just before the chorus title
    line (--title-word-t = whisper onset of "Hank and Doug" / "It's" in the chorus) so the title lands on the sung words;
  - the film ends at --end (the song's final chord tail) with a black row after the title; total = --end.
Prints the row table. Clips shorter than their new duration are flagged (finish_v5 holds the last frame)."""
import sys, json, subprocess, numpy as np, librosa
a = sys.argv[1:]; song = a[0]
g = lambda k, d: type(d)(a[a.index(k) + 1]) if k in a else d
BPM, TW, END, OFF = g("--bpm", 96.0), g("--title-word-t", 0.0), g("--end", 0.0), g("--offset", 0.0)   # --offset: film 0 = song OFF
y, sr = librosa.load(song, sr=48000, mono=True)
dur = len(y) / sr - OFF; END = END or dur
tempo, beats = librosa.beat.beat_track(y=y, sr=sr, start_bpm=BPM, units="time")
tempo = float(np.atleast_1d(tempo)[0]); beats = np.asarray(beats)
if len(beats) < 8:   # sparse intro: fall back to a grid from the first onset
    first = float(librosa.onset.onset_detect(y=y, sr=sr, units="time")[0]); beats = np.arange(first, dur, 60.0 / BPM)
spb = 60.0 / tempo if tempo > 0 else 60.0 / BPM
beats = beats - OFF; beats = beats[beats >= 0]
grid = beats; half = np.sort(np.concatenate([grid, grid[:-1] + np.diff(grid) / 2]))
bars = grid[::4]
def snap(t, g): return float(g[np.argmin(np.abs(g - t))])
tl = json.load(open("tools/timeline_v5.json")); rows = [r for r in tl["rows"] if r["clip"] != "black"]
def clip_len(p):
    try: return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).decode().strip())
    except Exception: return 0.0
# proportional re-lay: keep v5 relative timing over the span [0, title_start], then title to END
title = next(r for r in rows if r["id"] == "r16_title"); body = [r for r in rows if r["id"] != "r16_title"]
v5_title_start = title["start"]
t_title = snap(TW, bars) if TW else snap(v5_title_start, bars)
if TW and t_title > TW: t_title = float(bars[bars <= TW][-1]) if (bars <= TW).any() else t_title
scale = t_title / v5_title_start
out = []
for r in body:
    s = r["start"] * scale; gsel = half if r["dur"] * scale < 2.0 else grid
    out.append(dict(r, start=round(snap(s, gsel), 3)))
for i, r in enumerate(out):   # keep strictly increasing
    if i and r["start"] <= out[i - 1]["start"]: r["start"] = round(out[i - 1]["start"] + spb / 2, 3)
out.append(dict(title, start=round(t_title, 3)))
for i, r in enumerate(out):
    nxt = out[i + 1]["start"] if i + 1 < len(out) else min(END, t_title + title["dur"])
    r["dur"] = round(nxt - r["start"], 3)
black_start = out[-1]["start"] + out[-1]["dur"]
out.append({"n": len(out) + 1, "id": "r17_black", "start": round(black_start, 3), "dur": round(END - black_start, 3), "clip": "black", "in": 0.0, "note": "v5.2: the song's final chord rings over black"})
for i, r in enumerate(out): r["n"] = i + 1
print(f"song {song} {dur:.2f} s, tempo {tempo:.1f} (hint {BPM}), {len(grid)} beats, first bar {bars[0]:.2f}; title at {t_title:.2f}; end {END:.2f}")
for r in out:
    c = r.get("replace_with") if r.get("replace_with") and __import__("os").path.exists(r["replace_with"]) else r["clip"]
    L = clip_len(c) if c != "black" else 0.0; need = r["in"] + r["dur"]
    flag = "  SHORT: clip {:.2f} < {:.2f}".format(L, need) if c != "black" and L + 0.05 < need else ""
    print(f"  {r['n']:2d} {r['id']:14s} {r['start']:6.2f} +{r['dur']:5.2f}  {c}{flag}")
tl2 = dict(tl); tl2["rows"] = out; tl2["total"] = round(END, 3)
tl2["music"] = {"song": song, "song_offset": OFF, "tempo": round(tempo, 2), "bars_from": round(float(bars[0]), 3), "title_bar": round(t_title, 3),
                "note": "v5.2: one continuous song from film 0, no cuts in the music; rows snapped to its beats; title row on the chorus bar"}
tl2["note"] = tl.get("note", "") + " | v5.2 cut_v52: one song, beat-snapped rows."
json.dump(tl2, open("tools/timeline_v52.json", "w"), indent=1); print("-> tools/timeline_v52.json")
