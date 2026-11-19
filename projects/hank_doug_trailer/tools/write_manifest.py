#!/usr/bin/env python3
"""manifest.json for film_qc (schema in film_qc.py docstring) + the coverage list (frozen rule 13 amended / 29)."""
import json, glob
from pathlib import Path
P = Path(__file__).resolve().parent.parent
cues = json.load(open(P / "final/mix_cues.json"))["placed"] if (P / "final/mix_cues.json").exists() else []
lines = []
for c in cues:
    if c["label"].startswith("line:"):
        _, rest = c["label"].split(":", 1); tag, who, text = rest.split(" ", 2)
        who = {"hank": "hank", "young": "young_hank", "doug": "doug", "narrator": "narrator"}[who]
        if who == "young_hank": text = text.replace("hank ", "", 1)
        lines.append({"t": c["t"], "speaker": who, "text": text})
beats = json.load(open(P / "beats.json"))["shots"]
m = {
 "characters": {"hank": "huge round dark chocolate-brown grizzly bear with a tan muzzle",
                "young_hank": "the same brown bear, a little smaller and rounder",
                "doug": "sturdy russet-red bloodhound with very long droopy ears and a dark leather collar",
                "narrator": "off-screen narrator, no character on screen"},
 "scenes": [{"name": b["id"], "start": b["start"], "end": b["end"]} for b in beats],
 "lines": lines,
 "shots": [{"name": b["id"], "start": b["start"], "end": b["end"], "note": b["beat"][:160]} for b in beats],
 "spec": {"width": 1920, "height": 1080, "fps": 24, "duration": 60.0, "lufs": -14},
 "coverage": {
   "stills": sorted(str(Path(p).relative_to(P)) for p in glob.glob(str(P / "stills/*.png"))),
   "clips_previs": sorted(str(Path(p).relative_to(P)) for p in glob.glob(str(P / "clips/previs/*.mp4"))),
   "clips_k6": sorted(str(Path(p).relative_to(P)) for p in glob.glob(str(P / "clips/*.mp4"))),
   "clips_alternates": sorted(str(Path(p).relative_to(P)) for p in glob.glob(str(P / "clips/alternates/*.mp4"))),
   "music": sorted(str(Path(p).relative_to(P)) for p in glob.glob(str(P / "music/*.wav"))),
   "voices": sorted(str(Path(p).relative_to(P)) for p in glob.glob(str(P / "voices/**/*.wav"), recursive=True)),
   "sfx": sorted(str(Path(p).relative_to(P)) for p in glob.glob(str(P / "sfx/*.wav")))},
}
json.dump(m, open(P / "manifest.json", "w"), indent=1)
print("manifest:", len(lines), "lines,", len(m["scenes"]), "scenes")
