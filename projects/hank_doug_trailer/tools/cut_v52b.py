#!/usr/bin/env python3
"""cut_v52b.py SONG.wav --chorus-t S --title-t S --end S [--bpm 96] [--rows tools/rows_v52.json]
v5.2 picture cut to ONE continuous song (Matt 1:53 PM: same song all the way). Two anchors instead of cut_v52's one:
  - the STORY rows (1..11, narrated) are re-laid proportionally from film 0 to the chorus bar (--chorus-t = whisper onset of
    the first sung "Hank" of the chorus, snapped to the beat grid); the narration keeps its row-relative times;
  - the RESCUE rows (12..15) share [chorus_t, title_t) equally (each rescue gets the same number of beats);
  - the TITLE row starts on --title-t (whisper onset of "It's" in "It's Hank and Doug's Wild Rescue", snapped to the nearest beat),
    then black from the end of the title hold to --end (the song's final chord tail);
Row starts snap to the song's beats (half-beats for rows under 2 s). Reads tools/rows_v52.json (ordered rows: id, clip, in,
min_dur/max_dur) and writes tools/timeline_v52.json. Prints the row table and flags any row longer than its clip."""
import sys, json, subprocess, numpy as np, librosa, os
a = sys.argv[1:]; song = a[0]
g = lambda k, d: type(d)(a[a.index(k) + 1]) if k in a else d
BPM, CH, TW, END, ROWS, OFF = g("--bpm", 96.0), g("--chorus-t", 0.0), g("--title-t", 0.0), g("--end", 0.0), g("--rows", "tools/rows_v52.json"), g("--offset", 0.0)
# --offset S: film 0 = song S (the song's first S seconds are not used; no stretch of the story rows)
y, sr = librosa.load(song, sr=48000, mono=True); dur = len(y) / sr - OFF; END = (END - OFF) if END else dur; CH -= OFF; TW -= OFF
tempo, beats = librosa.beat.beat_track(y=y, sr=sr, start_bpm=BPM, units="time"); tempo = float(np.atleast_1d(tempo)[0]); beats = np.asarray(beats)
spb = 60.0 / tempo if tempo > 0 else 60.0 / BPM
if len(beats) < 8: beats = np.arange(0.0, dur + OFF, spb)
beats = beats - OFF; beats = beats[beats >= 0]
grid = beats; half = np.sort(np.concatenate([grid, grid[:-1] + np.diff(grid) / 2]))
snap = lambda t, gg: float(gg[np.argmin(np.abs(gg - t))])
rows = json.load(open(ROWS))
def clip_len(p):
    try: return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).decode().strip())
    except Exception: return 0.0
story = [r for r in rows if r["group"] == "story"]; resc = [r for r in rows if r["group"] == "rescue"]; title = next(r for r in rows if r["group"] == "title")
t_ch = snap(CH, grid); t_ti = snap(TW, grid)
# story: proportional to the v5 starts (r["v5_start"]), scaled so the last story row ends at t_ch
v5_end = story[-1]["v5_start"] + story[-1]["v5_dur"]; scale = t_ch / v5_end
out = []
for r in story:
    s = r["v5_start"] * scale; gsel = half if r["v5_dur"] * scale < 2.0 else grid
    out.append(dict(r, start=round(snap(s, gsel), 3)))
# rescues: equal beats across [t_ch, t_ti)
nb = int(round((t_ti - t_ch) / spb)); per = max(1, nb // len(resc))
for i, r in enumerate(resc): out.append(dict(r, start=round(snap(t_ch + i * per * spb, grid), 3)))
out.append(dict(title, start=round(t_ti, 3)))
for i, r in enumerate(out):
    if i and r["start"] <= out[i - 1]["start"] + 0.5: r["start"] = round(out[i - 1]["start"] + spb, 3)
for i, r in enumerate(out):
    nxt = out[i + 1]["start"] if i + 1 < len(out) else min(END, t_ti + title["v5_dur"])
    r["dur"] = round(nxt - r["start"], 3)
black = out[-1]["start"] + out[-1]["dur"]
out.append({"id": "r17_black", "group": "end", "start": round(black, 3), "dur": round(END - black, 3), "clip": "black", "in": 0.0, "note": "v5.2: the song's final chord rings over black"})
print(f"song {song} {dur:.2f} s, tempo {tempo:.1f} (hint {BPM}), spb {spb:.3f}; chorus bar {t_ch:.2f}; title {t_ti:.2f}; end {END:.2f}")
for i, r in enumerate(out):
    r["n"] = i + 1; c = r["clip"]; L = clip_len(c) if c != "black" else 0.0; need = r["in"] + r["dur"]
    flag = f"  SHORT: clip {L:.2f} < {need:.2f}" if c != "black" and L + 0.05 < need else ""
    print(f"  {r['n']:2d} {r['id']:14s} {r['start']:6.2f} +{r['dur']:5.2f}  {c}{flag}")
tl = {"note": "timeline_v52 (cut_v52b): one continuous song from film 0; story rows proportional to v5 up to the chorus bar, rescues share the chorus, title on the sung title line, black to the final chord.",
      "music": {"song": song, "song_offset": OFF, "tempo": round(tempo, 2), "spb": round(spb, 4), "chorus_bar": round(t_ch, 3), "title_bar": round(t_ti, 3), "end": round(END, 3)},
      "rows": [{k: v for k, v in r.items() if k not in ("v5_start", "v5_dur", "group")} for r in out], "total": round(END, 3)}
for r in tl["rows"]:
    if "title_in" not in r and r["id"] == "r16_title": r["title_in"] = 0.3; r["title_dur"] = 1.2
json.dump(tl, open("tools/timeline_v52.json", "w"), indent=1); print("-> tools/timeline_v52.json")
