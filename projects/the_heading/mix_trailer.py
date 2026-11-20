#!/usr/bin/env python3
"""Audio mix for the trailer: finished voices (-16 LUFS each) on top, score ~11 dB under, sfx under that."""
import json, subprocess
from pathlib import Path
P = Path(__file__).resolve().parent
tl = json.load(open(P / "final/timeline.json"))
ins = ["-i", "final/heading_trailer_picture.mp4", "-i", "music/cand1.wav", "-stream_loop", "-1", "-i", "sfx/surf.wav",
       "-stream_loop", "-1", "-i", "sfx/hum.wav", "-i", "sfx/truck.wav"]
for v in tl["voice"]:
    ins += ["-i", f"voices/final/{v['line']}.wav"]
g0 = ins.count("-i")
for _ in tl["glitch_at"]:
    ins += ["-i", "sfx/glitch.wav"]
f = ["[1]atrim=0:30,afade=t=in:d=0.6,afade=t=out:st=28.3:d=1.7,volume=0.17[sc]",
     "[2]atrim=0:30,volume='if(lt(t,12),0.10,if(gt(t,24),0.08,0.0))':eval=frame[su]",
     "[3]atrim=0:30,volume='0.02+0.10*t/30':eval=frame[hu]",
     "[4]atrim=0:6,afade=t=in:d=0.3,afade=t=out:st=5.4:d=0.6,volume=0.12,adelay=18000|18000[tr]"]
mixl = ["[sc]", "[su]", "[hu]", "[tr]"]
for k, v in enumerate(tl["voice"]):
    ms = int(v["start"] * 1000)
    f.append(f"[{5 + k}]adelay={ms}|{ms}[v{k}]"); mixl.append(f"[v{k}]")
for k, t in enumerate(tl["glitch_at"]):
    ms = int(t * 1000)
    f.append(f"[{g0 + k}]atrim=0:0.35,afade=t=out:st=0.2:d=0.15,volume=0.2,adelay={ms}|{ms}[g{k}]"); mixl.append(f"[g{k}]")
f.append("".join(mixl) + f"amix=inputs={len(mixl)}:normalize=0,atrim=0:30,aformat=channel_layouts=stereo[a]")
r = subprocess.run(["/opt/homebrew/bin/ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join(f), "-map", "0:v",
                    "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-t", "30",
                    "final/the_heading_trailer.mp4"], capture_output=True, text=True, cwd=P)
print("mix", r.returncode, r.stderr[-300:])
