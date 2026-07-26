#!/usr/bin/env python3
"""Assemble the Disclosure music video: concat all shot clips in order,
upscale 1.5x, apply a cohesive cinematic grade, lay the Disclosure track over it.
Run AFTER disc_build.py finishes. Reports any missing shots.
Output: ~/Desktop/Disclosure_movie_v1.mp4
"""
import glob, subprocess, sys, shutil
from pathlib import Path

HOME = Path.home()
OUT = HOME / "AI/videopipe/outputs"
SONG = HOME / "Desktop/PROJECTS/Song Forge/outputs/08bee5f5e5764453814107446048b391.wav"
FINAL = HOME / "Desktop/Disclosure_movie_v1.mp4"
TMP = Path("/tmp/disc_assembly"); TMP.mkdir(exist_ok=True)
FFMPEG = next((p for p in ["/opt/homebrew/bin/ffmpeg","/usr/local/bin/ffmpeg","ffmpeg"] if shutil.which(p) or Path(p).exists()), "ffmpeg")

labels = [f"{n:02d}" for n in range(1,37)]
clips, missing = [], []
for lb in labels:
    found = sorted(glob.glob(str(OUT / f"disc_shot{lb}_ltxL_*.mp4")))
    if found: clips.append(found[-1])
    else: missing.append(lb)

print(f"clips found: {len(clips)}/36  missing: {missing or 'none'}")
if not clips:
    sys.exit("no clips found — run disc_build.py first")
if not SONG.exists():
    sys.exit(f"song wav missing: {SONG}")

# concat list
listf = TMP / "concat.txt"
listf.write_text("".join(f"file '{c}'\n" for c in clips))

GRADE = ("scale=1152:768:flags=lanczos,"
         "eq=contrast=1.06:saturation=1.12:brightness=-0.012,"
         "colorbalance=bs=0.05:rh=0.04:gm=-0.02,"
         "vignette=PI/5,fps=24,format=yuv420p")

cmd = [FFMPEG,"-y","-f","concat","-safe","0","-i",str(listf),
       "-i",str(SONG),
       "-map","0:v","-map","1:a",
       "-vf",GRADE,
       "-c:v","libx264","-crf","18","-preset","medium",
       "-c:a","aac","-b:a","256k","-shortest",str(FINAL)]
print("assembling -> ", FINAL)
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print("FFMPEG ERROR:\n", r.stderr[-1500:]); sys.exit(1)
print("DONE ->", FINAL)
subprocess.run([FFMPEG.replace("ffmpeg","ffprobe"),"-v","error","-show_entries",
                "format=duration","-of","default=nw=1:nk=1",str(FINAL)])
