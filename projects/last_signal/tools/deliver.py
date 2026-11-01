#!/usr/bin/env python3
"""Final muxes for THE LAST SIGNAL (stage 06 outputs):
  final/The_Last_Signal.mp4        4K (3840x2160, 2.39:1 scope bars), H.264, stereo AAC 320k (static-gain mix)
  final/The_Last_Signal_51.mp4     same picture, E-AC3 5.1 (track 1) + AAC stereo (track 2), via bin/surround-mix --no-loudnorm
  final/The_Last_Signal_1080p.mp4  web copy, 1920x1080 lanczos, stereo AAC
  final/timeline.json              the cut (EDL with selects, LUT/bloom/upscale per cut), voice + score placement"""
import json, subprocess
from pathlib import Path
P = Path(__file__).resolve().parent.parent; ROOT = P.parent.parent
pic = P / "final/picture_4k.mp4"
run = lambda c: subprocess.run(c, check=True)
run([str(ROOT / "bin/surround-mix"), str(P / "sfx/mix_plan.json"), "--out", str(P / "final/mix_51.wav"), "--stereo", str(P / "final/mix_stereo.wav"), "--no-loudnorm"])
run(["ffmpeg", "-v", "error", "-y", "-i", str(pic), "-i", str(P / "final/mix_stereo.wav"), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
     "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-movflags", "+faststart", "-metadata", "title=THE LAST SIGNAL", str(P / "final/The_Last_Signal.mp4")])
run([str(ROOT / "bin/surround-mix"), str(P / "sfx/mix_plan.json"), "--out", str(P / "final/mix_51.wav"), "--stereo", str(P / "final/mix_stereo.wav"),
     "--no-loudnorm", "--codec", "eac3", "--video", str(P / "final/The_Last_Signal.mp4"), "--mux", str(P / "final/The_Last_Signal_51.mp4")])
run(["ffmpeg", "-v", "error", "-y", "-i", str(P / "final/The_Last_Signal.mp4"), "-vf", "scale=1920:1080:flags=lanczos", "-c:v", "libx264", "-crf", "17",
     "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(P / "final/The_Last_Signal_1080p.mp4")])
e = json.load(open(P / "final/edl_final_graded.json"))
plan = json.load(open(P / "sfx/mix_plan.json"))
vo = {s["name"]: s["start"] for s in plan["sources"] if s["name"] in ("computer", "planet", "captain")}
tl = {"film": "THE LAST SIGNAL", "duration": e["duration"], "fps": e["fps"], "frame": "3840x2160, 2.39:1 scope (276 px bars)",
      "grade": {"tool": "bin/grade", "luts": {"space shots (c01, c01b)": "cold_space_teal", "everything else": "teal_orange_blockbuster", "title": "none"},
                "grain": 0.12, "scope": True, "bloom": "highlight glow + anamorphic streak on engines/lights (strength per cut below)"},
      "score": "music/arranged/score_1_arranged.wav (candidate 1, provisional pick; stages/05_sound/score_pick.md)",
      "narration": [["nia_computer.wav", vo.get("computer")], ["nia_planet.wav", vo.get("planet")], ["nia_captain.wav", vo.get("captain")]],
      "_narration_note": "audio_check names voices nia_<id>.wav; these map to voices/computer.wav, planet.wav, captain.wav",
      "cues": {"beep_stops_dead": [c["start"] for c in e["cuts"] if c["id"] == "c09_welcome"][0],
               "black_silence": [c["start"] for c in e["cuts"] if c["id"] == "c17_black"][0],
               "title_slam": [c["start"] for c in e["cuts"] if c["id"] == "c18_title"][0]},
      "cuts": e["cuts"], "order": [c["id"] for c in e["cuts"]], "starts": [c["start"] for c in e["cuts"]], "lens": [c["len"] for c in e["cuts"]]}
json.dump(tl, open(P / "final/timeline.json", "w"), indent=1)
for f in ("The_Last_Signal.mp4", "The_Last_Signal_51.mp4", "The_Last_Signal_1080p.mp4"):
    o = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name,width,height,channels",
                                 "-of", "compact", str(P / "final" / f)]).decode()
    print(f, o.replace("\n", " | "))
