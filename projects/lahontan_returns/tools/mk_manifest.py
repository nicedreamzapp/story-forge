#!/usr/bin/env python3
"""manifest.json for film_qc from timeline.json. Each line is split at shot cuts; a piece over b-roll/graphics is "offscreen"
(audio-checked only), a piece on its own speaker's lip-synced shot is mouth-checked."""
import json, re
from pathlib import Path
P = Path(__file__).resolve().parent.parent
TL = json.load(open(P / "timeline.json"))
SPK = {"kssn_dan": "anchor", "nia": "reporter", "kssn_halverson": "scientist", "kssn_resident": "resident"}
BLK = {"AN1": "anchor", "AN2": "anchor", "AN3": "anchor", "REP": "reporter", "SCI": "scientist", "RES": "resident"}
def shot(t):
    for s in TL["shots"]:
        if s["s"] <= t < s["e"]: return s
    return TL["shots"][-1]
lines = []
for lid, L in TL["lines"].items():
    who = SPK[L["spk"]]; segs = []
    for w in L["words"]:
        s = shot(w["s"]); on = s["src"].startswith("lips:") and BLK[s["src"][5:]] == who
        if segs and segs[-1]["shot"] is s: segs[-1]["words"].append(w)
        else: segs.append({"shot": s, "on": on, "words": [w]})
    for g in segs:
        ws = g["words"]; e = {"t": ws[0]["s"], "dur": max(0.6, round(ws[-1]["e"] - ws[0]["s"], 2)), "speaker": who, "text": re.sub(r" (?=[,.!?])|(?<=\d) (?=,\d)", "", " ".join(x["w"] for x in ws)), "id": lid}
        if not g["on"]: e["offscreen"] = True
        lines.append(e)
names = {"lips": "talk", "clip": "broll", "still": "broll", "map": "map", "evac": "evac"}
shots = [{"name": f"sh{i+1:02d}_{s['src'].replace(':', '_')}", "start": s["s"], "end": s["e"]} for i, s in enumerate(TL["shots"])]
scenes = [{"name": "cold_open", "start": 0, "end": TL["gfx"]["cold"]}, {"name": "newscast", "start": TL["gfx"]["cold"], "end": TL["end"]}]
M = {"characters": {"anchor": "gray-haired male TV news anchor in his fifties, navy suit, red tie, at a news desk",
                    "reporter": "brown-haired female field reporter in a red rain jacket holding a microphone on a flooded highway",
                    "scientist": "white-haired older man with wire-rimmed glasses and a white beard, tan cardigan, in front of a whiteboard",
                    "resident": "grizzled gray-bearded man in a cap and orange life jacket sitting in a lawn chair"},
     "scenes": scenes, "lines": lines, "shots": shots,
     "spec": {"width": 1080, "height": 1920, "fps": 25, "lufs": -14.5}}
json.dump(M, open(P / "manifest.json", "w"), indent=1)
print(len(lines), "manifest lines,", sum(1 for l in lines if not l.get("offscreen")), "mouth-checked")
