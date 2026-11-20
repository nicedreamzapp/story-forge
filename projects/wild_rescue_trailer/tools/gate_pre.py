#!/usr/bin/env python3
"""gate input from tools/preselect.txt (agent's by-eye shortlist, 2-4 per render) -> logs/gate_stills.json"""
import json
from pathlib import Path
P = Path(__file__).resolve().parent.parent
R = {r["id"]: r for r in json.load(open(P / "renders.json"))["renders"]}
beats = json.load(open(P / "beats.json"))
shots = []
for line in open(P / "tools/preselect.txt"):
    rid, *tags = line.split()
    for t in tags:
        f = P / f"stills/cand/{rid}_{t}.png"
        if f.exists():
            e = {"id": f.stem, "image": str(f), "beat": R[rid]["beat"], "must_not": R[rid]["must_not"]}
            if R[rid]["set"] and R[rid]["set"].endswith("set_canyon_gap.png") and R[rid]["source"] != "blender":
                e["set"] = "canyon"
            shots.append(e)
json.dump({"set_masters": {k: str(P / v) for k, v in beats["set_masters"].items() if (P / v).exists()}, "shots": shots},
          open(P / "logs/gate_stills.json", "w"), indent=1)
print(len(shots))
