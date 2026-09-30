#!/usr/bin/env python3
"""finish_test.py — scene 3 test: order clips, 1080p upscale, one grade + grain,
2.39:1 letterbox in a 1920x1080 frame, dissolves, narration over a ducked score."""
import subprocess, json, sys
from pathlib import Path
P = Path(__file__).resolve().parent
FF = "/opt/homebrew/bin/ffmpeg"
ORDER = ["s3_reveal", "s3_seed", "s3_hollow", "s3_profile", "s3_heart", "s3_hand"]
SHOT = 4.0; XF = 0.5
clips = [P / "clips" / f"{s}_final.mp4" for s in ORDER]
missing = [c.name for c in clips if not c.exists()]
if missing: sys.exit(f"missing clips: {missing}")
def dur(f): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(f)]))
lens = [min(SHOT, dur(c)) for c in clips]
inputs = sum([["-i", str(c)] for c in clips], [])
grade = ("scale=1920:768:flags=lanczos,setsar=1,fps=24,"
         "eq=contrast=1.06:saturation=0.9:gamma=0.98,"
         "colorbalance=rs=-0.03:bs=0.03:rh=0.04:bh=-0.03,"
         "unsharp=5:5:0.4")
fc = []
for i, L in enumerate(lens):
    old = ",colorchannelmixer=.95:.05:0:0:.05:.9:.05:0:0:.1:.8:0,eq=saturation=0.7:brightness=0.02,vignette=PI/4" if ORDER[i]=="s3_seed" else ""
    fc.append(f"[{i}:v]trim=0:{L},setpts=PTS-STARTPTS,{grade}{old},format=yuv420p[v{i}]")
prev, off = "v0", lens[0] - XF
for i in range(1, len(lens)):
    fc.append(f"[{prev}][v{i}]xfade=transition=fade:duration={XF}:offset={off:.3f}[x{i}]")
    prev = f"x{i}"; off += lens[i] - XF
total = off + XF
fc.append(f"[{prev}]noise=alls=5:allf=t,pad=1920:1080:0:156:black,"
          f"fade=t=in:st=0:d=1,fade=t=out:st={total-1.2:.2f}:d=1.2[vout]")
n = len(clips)
LINES=[("L1",0.8),("L2",7.4),("L3",11.0),("L4",14.6)]

for k,(ln,t) in enumerate(LINES):
    fc.append(f"[{n+1+k}:a]adelay={int(t*1000)}|{int(t*1000)},aformat=channel_layouts=stereo[l{k}]")
fc.append("".join(f"[l{k}]" for k in range(len(LINES)))+f"amix=inputs={len(LINES)}:normalize=0,volume=2.0,apad,asplit[nar][nar2]")
fc.append(f"[{n}:a]atrim=0:{total},volume=0.75,afade=t=in:st=0:d=1.5,afade=t=out:st={total-2:.2f}:d=2[mus]")
fc.append("[mus][nar]sidechaincompress=threshold=0.05:ratio=4:attack=50:release=600[duck]")
fc.append("[duck][nar2]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.9,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[aout]")
out = P / "final" / "oldest_tree_scene3_test.mp4"
cmd = [FF, "-y", *inputs, "-i", str(P/"score_test.wav"), *sum([["-i", str(P/f"voices/t3_{ln}.wav")] for ln,_ in LINES], []),
       "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
       "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-c:a", "aac", "-b:a", "256k",
       "-t", f"{total:.2f}", str(out)]
subprocess.run(cmd, check=True)
print(out, round(total, 2))
