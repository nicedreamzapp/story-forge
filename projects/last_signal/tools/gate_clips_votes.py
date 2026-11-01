#!/usr/bin/env python3
"""Clip gate input, part 2 (2026-10-31 11:40): one entry per take, judged by beat_gate on 3 frames
spread over 15-85% of the clip (majority rules), against the render's clip_beat + must_not.
Covers every hq take in clips/takes/ plus the previs drafts that are candidates for the cut
(R19/R20 strobe drafts, and the previs of every render with only one hq take, so each beat ranks >= 2)."""
import json
from pathlib import Path
P = Path(__file__).resolve().parent.parent
renders = {r["id"]: r for r in json.load(open(P / "renders.json"))["renders"]}
beats = json.load(open(P / "beats.json"))
mn = {}
for s in beats["shots"]:
    if s.get("render"): mn.setdefault(s["render"], s["must_not"])
plan = {p["id"]: p for p in json.load(open(P / "final_plan.json"))}
files = sorted((P / "clips/takes").glob("*.mp4"))
for rid in renders:
    if rid not in plan or plan[rid]["takes"] == 1:
        f = P / f"clips/previs/{rid}_t1.mp4"
        if f.exists(): files.append(f)
shots = []
for f in files:
    rid = f.stem.rsplit("_t", 1)[0]; r = renders[rid]
    tag = ("previs_" if "previs" in f.parts else "hq_") + f.stem
    shots.append({"id": tag, "clip": str(f), "beat": r["clip_beat"], "must_not": mn.get(rid, [])})
out = P / "logs/gate_clips.json"
json.dump({"shots": shots}, open(out, "w"), indent=1)
print(out, len(shots))
