#!/usr/bin/env python3
"""Mix for the concert trailer: score's kick-in aligned to the picture's DROP, music + sfx ducked under the voices."""
import json, subprocess
from pathlib import Path
P = Path(__file__).resolve().parent
tl = json.load(open(P / "final/concert_timeline.json"))
onset = float((P / "music2/onset.txt").read_text())
start = tl["drop"] - onset                       # film time the score starts
ins = ["-i", "final/concert_picture.mp4", "-i", "music2/cand1.wav", "-stream_loop", "-1", "-i", "sfx/surf.wav",
       "-stream_loop", "-1", "-i", "sfx/crowd.wav", "-i", "sfx/hum.wav"]
for v in tl["voice"]:
    ins += ["-i", v["file"]]
g0 = ins.count("-i")
for _ in tl["glitch_at"]:
    ins += ["-i", "sfx/glitch.wav"]
ms = int(start * 1000); d = int(tl["drop"] * 1000)
f = [f"[1]afade=t=out:st={28.3 - start:.2f}:d=1.7,volume=0.22,adelay={ms}|{ms}[sc]",
     "[2]atrim=0:13,afade=t=out:st=11.5:d=1.5,volume=0.12[su]",
     f"[3]atrim=0:16,afade=t=in:d=0.4,afade=t=out:st=14.5:d=1.5,volume=0.22,adelay={d}|{d}[cr]",
     "[4]atrim=0:13,afade=t=out:st=11:d=2,volume=0.05[hu]"]
bed = ["[sc]", "[su]", "[cr]", "[hu]"]
vo = []
for k, v in enumerate(tl["voice"]):
    m = int(v["start"] * 1000); f.append(f"[{5 + k}]adelay={m}|{m}[v{k}]"); vo.append(f"[v{k}]")
for k, t in enumerate(tl["glitch_at"]):
    m = int(t * 1000); f.append(f"[{g0 + k}]atrim=0:0.35,afade=t=out:st=0.2:d=0.15,volume=0.2,adelay={m}|{m}[g{k}]"); bed.append(f"[g{k}]")
f.append("".join(bed) + f"amix=inputs={len(bed)}:normalize=0[bed]")
f.append("".join(vo) + f"amix=inputs={len(vo)}:normalize=0,apad=whole_dur=30,asplit=2[vox][key]")
f.append("[bed][key]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=350[duck]")
f.append("[duck][vox]amix=inputs=2:normalize=0,atrim=0:30,aformat=channel_layouts=stereo[a]")
r = subprocess.run(["/opt/homebrew/bin/ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(f), "-map", "0:v",
                    "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-t", "30",
                    "final/the_heading_concert_trailer.mp4"], capture_output=True, text=True, cwd=P)
print("mix", r.returncode, r.stderr[-300:], "score starts at", round(start, 2))
