#!/usr/bin/env python3
"""Build a beat_gate input from candidate stills or clip takes.
  gate_file.py stills  -> logs/gate_stills.json   (every stills/cand/*.png + Blender start stills)
  gate_file.py clips   -> logs/gate_clips.json    (every clips/takes/*.mp4, judged on clip_beat at 3 times)"""
import json, sys
from pathlib import Path
P = Path(__file__).resolve().parent.parent
renders = {r["id"]: r for r in json.load(open(P / "renders.json"))["renders"]}
beats = json.load(open(P / "beats.json"))
mn = {}
for s in beats["shots"]:
    if s.get("render"): mn.setdefault(s["render"], s["must_not"])
setkey = {v: k for k, v in beats["set_masters"].items()}
shots = []
mode = sys.argv[1]
if mode == "stills":
    items = []
    for f in sorted((P / "stills/cand").glob("*.png")):
        rid = "_".join(f.stem.split("_")[:-1]); items.append((f.stem, rid, f))
    for rid, r in renders.items():
        if r["source"] == "blender" and rid != "R18_ship_grab":
            f = P / r["start_still"]
            if f.exists(): items.append((f"{rid}_blender", rid, f))
    for sid, rid, f in items:
        r = renders[rid]
        e = {"id": sid, "image": str(f), "beat": r["beat"], "must_not": mn[rid]}
        if r["set"] in setkey and r["source"] == "qwen": e["set"] = setkey[r["set"]]
        shots.append(e)
else:
    for f in sorted((P / "clips/takes").glob("*.mp4")):
        rid = f.stem.rsplit("_t", 1)[0]; r = renders[rid]
        for t in (1.0, 2.5, 4.0):
            shots.append({"id": f"{f.stem}@{t}", "clip": str(f), "t": t, "beat": r["clip_beat"], "must_not": mn[rid]})
out = P / f"logs/gate_{mode}.json"
json.dump({"set_masters": {k: str(P / v) for k, v in beats["set_masters"].items()}, "shots": shots}, open(out, "w"), indent=1)
print(out, len(shots))
