#!/usr/bin/env python3
"""Build a beat_gate input.
  gate_file.py stills [glob]  -> logs/gate_stills.json  (stills/cand/*.png, judged on the render's beat)
  gate_file.py clips  [dir]   -> logs/gate_clips.json   (clips/takes/*.mp4 judged on clip_beat at 3 times)"""
import json, sys
from pathlib import Path
P = Path(__file__).resolve().parent.parent
renders = {r["id"]: r for r in json.load(open(P / "renders.json"))["renders"]}
beats = json.load(open(P / "beats.json"))
setkey = {v: k for k, v in beats["set_masters"].items()}
mode = sys.argv[1]; shots = []
if mode == "stills":
    for f in sorted((P / "stills/cand").glob(sys.argv[2] if len(sys.argv) > 2 else "*.png")):
        rid = f.stem.rsplit("_", 1)[0]; r = renders[rid]
        e = {"id": f.stem, "image": str(f), "beat": r["beat"], "must_not": r["must_not"]}
        if r["set"] and (P / r["set"]).exists() and setkey.get(r["set"]) == "canyon" and r["source"] != "blender":
            e["set"] = "canyon"
        shots.append(e)
else:
    d = P / (sys.argv[2] if len(sys.argv) > 2 else "clips/takes")
    for f in sorted(d.glob("*.mp4")):
        rid = f.stem.rsplit("_t", 1)[0]; r = renders[rid]
        dur = float(json.loads((f.with_suffix(".done")).read_text()).get("duration") or 2) if f.with_suffix(".done").exists() else 2.0
        for t in (0.3, dur * 0.5, max(0.4, dur - 0.4)):
            shots.append({"id": f"{f.stem}@{t:.1f}", "clip": str(f), "t": round(t, 2), "beat": r["clip_beat"], "must_not": r["must_not"]})
out = P / f"logs/gate_{mode}.json"
json.dump({"set_masters": {k: str(P / v) for k, v in beats["set_masters"].items() if (P / v).exists()}, "shots": shots}, open(out, "w"), indent=1)
print(out, len(shots))
