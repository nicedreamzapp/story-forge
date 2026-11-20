#!/usr/bin/env python3
"""Final muxes for HANK & DOUG'S WILD RESCUE (stage 06 outputs):
  final/Hank_and_Doug_Wild_Rescue.mp4        4K (3840x2160, full-frame 16:9), H.264, stereo AAC 320k (static-gain mix)
  final/Hank_and_Doug_Wild_Rescue_51.mp4     same picture, E-AC3 5.1 (track 1) + AAC stereo (track 2), via bin/surround-mix --no-loudnorm
  final/Hank_and_Doug_Wild_Rescue_1080p.mp4  web copy, 1920x1080 lanczos, stereo AAC
  final/timeline.json              the cut (EDL with selects, LUT/bloom/upscale per cut), voice + score placement"""
import json, subprocess
from pathlib import Path
P = Path(__file__).resolve().parent.parent; ROOT = P.parent.parent
pic = P / "final/picture_4k.mp4"
run = lambda c: subprocess.run(c, check=True)
run([str(ROOT / "bin/surround-mix"), str(P / "sfx/mix_plan.json"), "--out", str(P / "final/mix_51.wav"), "--stereo", str(P / "final/mix_stereo.wav"), "--no-loudnorm"])
run(["ffmpeg", "-v", "error", "-y", "-i", str(pic), "-i", str(P / "final/mix_stereo.wav"), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
     "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-movflags", "+faststart", "-metadata", "title=HANK & DOUG'S WILD RESCUE", str(P / "final/Hank_and_Doug_Wild_Rescue.mp4")])
run([str(ROOT / "bin/surround-mix"), str(P / "sfx/mix_plan.json"), "--out", str(P / "final/mix_51.wav"), "--stereo", str(P / "final/mix_stereo.wav"),
     "--no-loudnorm", "--codec", "eac3", "--video", str(P / "final/Hank_and_Doug_Wild_Rescue.mp4"), "--mux", str(P / "final/Hank_and_Doug_Wild_Rescue_51.mp4")])
run(["ffmpeg", "-v", "error", "-y", "-i", str(P / "final/Hank_and_Doug_Wild_Rescue.mp4"), "-vf", "scale=1920:1080:flags=lanczos", "-c:v", "libx264", "-crf", "17",
     "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(P / "final/Hank_and_Doug_Wild_Rescue_1080p.mp4")])
e = json.load(open(P / "final/edl_final_graded.json"))
plan = json.load(open(P / "sfx/mix_plan.json"))
score_n = (P / "music/score_pick.txt").read_text().strip() if (P / "music/score_pick.txt").exists() else "1"
tl = {"film": "HANK & DOUG'S WILD RESCUE", "duration": e["duration"], "fps": e["fps"], "frame": "3840x2160, full-frame 16:9 (no scope bars)",
      "grade": {"tool": "bin/grade", "luts": {"night origin (c01a-c01e)": "moonlit_feature", "every day shot": "warm_feature_pop", "title": "none"},
                "grain": 0, "scope": False, "bloom": "warm highlight glow on lantern/sparks/glints (strength per cut below)"},
      "score": f"music/arranged/score_{score_n}_arranged.wav (candidate {score_n}, builder pick; stages/05_sound/score_pick.md)",
      "narration": [["nia_doug1.wav", next(s["start"] for s in plan["sources"] if s["name"] == "doug1")],
                    ["nia_hank1.wav", next(s["start"] for s in plan["sources"] if s["name"] == "hank1")],
                    ["nia_doug2.wav", next(s["start"] for s in plan["sources"] if s["name"] == "doug2")]],
      "_narration_note": "audio_check names voices nia_<id>.wav; these map to voices/doug1.wav, hank1.wav, doug2.wav",
      "cues": {"theme_hit": [c["start"] for c in e["cuts"] if c["id"] == "c03a_burst"][0],
               "dead_stop": [c["start"] for c in e["cuts"] if c["id"] == "c05a_hank"][0],
               "smash_to_black": [c["start"] for c in e["cuts"] if c["id"] == "c08_black"][0],
               "title_slam": [c["start"] for c in e["cuts"] if c["id"] == "c09_title"][0]},
      "cuts": e["cuts"], "order": [c["id"] for c in e["cuts"]], "starts": [c["start"] for c in e["cuts"]], "lens": [c["len"] for c in e["cuts"]]}
json.dump(tl, open(P / "final/timeline.json", "w"), indent=1)
for f in ("Hank_and_Doug_Wild_Rescue.mp4", "Hank_and_Doug_Wild_Rescue_51.mp4", "Hank_and_Doug_Wild_Rescue_1080p.mp4"):
    o = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name,width,height,channels",
                                 "-of", "compact", str(P / "final" / f)]).decode()
    print(f, o.replace("\n", " | "))
