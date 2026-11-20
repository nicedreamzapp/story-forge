#!/usr/bin/env python3
"""Start-still candidates for every render (renders.json) -> stills/cand/<rid>_<tag>.png
  write_still_jobs.py t2i      -> tools/jobs_stills_t2i.json   (zimage renders 3 seeds; composite renders 2 t2i seeds)
  write_still_jobs.py guided   -> tools/jobs_stills_guided.json (blender: img2img over the Blender frame, 2 seeds at
                                  'strength' + 1 at strength+0.1; composite: img2img over stills/plates/<rid>.png)"""
import json, sys
from pathlib import Path
P = Path(__file__).resolve().parent.parent
R = json.load(open(P / "renders.json"))["renders"]
mode = sys.argv[1]
jobs = []
def job(rid, tag, prompt, seed, init=None, strength=None):
    j = {"out": str(P / f"stills/cand/{rid}_{tag}.png"), "prompt": prompt, "w": 1248, "h": 720, "seed": seed, "steps": 9}
    if init: j.update(init=str(P / init), strength=strength)
    jobs.append(j)
for r in R:
    if mode == "t2i":
        if r["source"] == "zimage":
            for s in (101, 202, 303): job(r["id"], f"s{s}", r["still"], s)
        elif r["source"] == "composite" and r["id"] != "R15_bench":
            for s in (101, 202): job(r["id"], f"s{s}", r["still"], s)
    elif mode == "guided":
        if r["source"] == "blender":
            if not (P / r["init"]).exists():
                print("MISSING blender frame", r["init"]); continue
            job(r["id"], "b101", r["still"], 101, r["init"], r["strength"])
            job(r["id"], "b202", r["still"], 202, r["init"], r["strength"])
            job(r["id"], "b303", r["still"], 303, r["init"], round(r["strength"] + 0.1, 2))
        elif r["source"] == "composite":
            plate = f"stills/plates/{r['id']}.png"
            if not (P / plate).exists():
                print("MISSING plate", plate); continue
            st = r.get("strength") or 0.5
            job(r["id"], "c101", r["still"], 101, plate, st)
            job(r["id"], "c202", r["still"], 202, plate, round(st + 0.08, 2))
            if r["id"] == "R15_bench" and r.get("init"):   # also paint the Blender bench frame directly
                job(r["id"], "b303", r["still"], 303, r["init"], 0.62)
if mode == "guided":   # prompt fixes after the first look (lantern logic, elephant "trumpet" = instrument)
    for r in R:
        if r["id"] in ("R01_night_hunt", "R02_bear_hiding", "R04_doug_leads_away", "R25_elephant_trumpet"):
            for s in (404, 505, 606): job(r["id"], f"r{s}", r["still"], s)
    sys.path.insert(0, str(P / "tools"))
    from bible import STYLE_SET_DAY as SD, SET as S
    for name, init, pr in (("wagon", "blender/renders/B15_wagon_side.png", "Side view. " + S["wagon"] + ", standing in the red-rock desert."),
                           ("train", "blender/renders/B17_train_wide.png", "Aerial three-quarter view. " + S["train"] + ", on a single track in the red-rock desert.")):
        for s, st in ((11, 0.5), (23, 0.6)):
            jobs.append({"out": str(P / f"canon/cand/{name}_s{s}.png"), "prompt": SD + " " + pr, "w": 1248, "h": 720,
                         "seed": s, "steps": 9, "init": str(P / init), "strength": st})
out = P / f"tools/jobs_stills_{mode}.json"
json.dump(jobs, open(out, "w"), indent=1)
print(out.name, len(jobs), "jobs")
