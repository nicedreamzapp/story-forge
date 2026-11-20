#!/usr/bin/env python3
"""Clip gate input, part 2 (2026-11-01, from last_signal): one entry per take, judged by beat_gate on 3 frames spread
over 15-85% of the clip (majority rules) against the render's clip_beat + must_not, plus house checks for this film:
Doug stays a long-eared bloodhound (beagle drift / merging with Hank was the known R15 risk), no humans, no trucks/tires.
Covers every hq take in clips/takes/ plus the previs drafts that are candidates for the cut (the 7 sub-second renders
kept as previs, and the previs of every render with one hq take so each beat ranks >= 2)."""
import json
from pathlib import Path
P = Path(__file__).resolve().parent.parent
renders = {r["id"]: r for r in json.load(open(P / "renders.json"))["renders"]}
plan = {p["id"]: p for p in json.load(open(P / "final_plan.json"))}
HOUSE = ["a human or person anywhere in frame", "a truck, car, motor vehicle or rubber tires"]
DOUG = ["a beagle, basset or small short-eared dog instead of a lanky long-eared bloodhound",
        "the dog and the bear merged into one body"]
files = sorted((P / "clips/takes").glob("*.mp4"))
for rid in renders:
    if rid not in plan or plan[rid]["takes"] == 1:
        f = P / f"clips/previs/{rid}_t1.mp4"
        if f.exists(): files.append(f)
shots = []
for f in files:
    rid = f.stem.rsplit("_t", 1)[0]; r = renders[rid]
    mn = list(dict.fromkeys(r["must_not"] + HOUSE + (DOUG if "doug" in (r.get("identity") or []) else [])))
    tag = ("previs_" if "previs" in f.parts else "hq_") + f.stem
    shots.append({"id": tag, "clip": str(f), "beat": r["clip_beat"], "must_not": mn})
out = P / "logs/gate_clips.json"
json.dump({"shots": shots}, open(out, "w"), indent=1)
print(out, len(shots))
