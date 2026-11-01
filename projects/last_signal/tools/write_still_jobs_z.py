#!/usr/bin/env python3
"""Start-still jobs for Z-Image-Turbo (no reference-image input): characters by full fixed description
(face_lock from canon after lock), creature/ship edits by img2img."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
P = Path(__file__).resolve().parent.parent
import importlib.util
spec = importlib.util.spec_from_file_location("w", P / "tools/write_still_jobs.py")
src = open(P / "tools/write_still_jobs.py").read()
STYLE = src.split('STYLE = (')[1].split(')\n')[0]; STYLE = eval("(" + STYLE + ")")
EXTRA = eval(src.split("EXTRA = ")[1].split("\n}\n")[0] + "\n}")
CAP = ("the Captain: a weathered woman in her mid-forties with lightly sun-lined skin, grey-green eyes, "
       "dark brown hair streaked with grey tied back tightly, wearing a worn olive-grey zip-up flight suit with mission patches and a utility belt")
CREW = ("the Crewmate: a man in his early thirties with warm brown skin, short dark curly hair and a short trimmed beard, wearing a worn dark armored spacesuit with a metal neck ring "
        "and an olive-grey chest plate and scuffed shoulder armor")
WORLD = ("The alien world: an endless flat plain of glossy black glass sand with sharp glassy shards, thousands of tall dark carved stone monoliths covered "
         "in deep looping handwritten-style glyphs, drifting fog, a churning dark orange and rust storm sky with lightning.")
COCK = "Inside the cockpit of a huge heavy industrial cargo starship: worn consoles with physical switches and small teal screens, thick angled windows, a big steel throttle lever."
SHIPDESC = ("a colossal 8 km dark gunmetal cargo hauler with a long slightly wedge-shaped armored spine, stepped superstructure ridge, tall bridge tower near the stern, "
            "broad flat underbelly, blunt layered-armor prow, dense panel plating and greebles, thousands of tiny warm-white window lights, dashed cold teal running-light strips, six huge round blue-white engine nozzles")
renders = json.load(open(P / "renders.json"))["renders"]
jobs = []
for r in renders:
    rid = r["id"]
    who = []
    if "canon/captain.png" in r["identity"]: who.append(CAP)
    if "canon/crewmate.png" in r["identity"]: who.append(CREW)
    people = (" People: " + "; and ".join(who) + ".") if who else ""
    setting = COCK if r["set"].endswith("cockpit.png") else (WORLD if r["source"] == "qwen" else "")
    if r["source"] == "qwen":
        prompt = f"{STYLE} {EXTRA[rid]}{people} {setting}"
        for s in (101, 202):
            j = {"out": str(P / f"stills/cand/{rid}_s{s}.png"), "prompt": prompt, "w": 1248, "h": 720, "seed": s, "steps": 9}
            if rid == "R15_mountain_shape":
                j.update(init=str(P / "stills/refs/creature_layout_nobanner.png"), strength=0.82 if s == 101 else 0.9)
            jobs.append(j)
    elif rid == "R18_ship_grab":
        prompt = (f"{STYLE} A real photographed film frame: {SHIPDESC}, lifting off a glossy black glass plain, engines blazing blue, while enormous dark "
                  "rock-like claws, each bigger than a skyscraper, rise out of the ground and close around its hull from below, rock and glass pouring off them, "
                  "lightning in a churning orange storm sky.")
        for s, st in ((101, 0.6), (202, 0.72)):
            jobs.append({"out": str(P / f"stills/cand/{rid}_s{s}.png"), "prompt": prompt, "init": str(P / "ship/renders/r15_liftoff.png"),
                         "strength": st, "w": 1248, "h": 720, "seed": s, "steps": 9})
    else:
        srcimg = P / r["start_still"].replace("_832.png", ".png")
        prompt = (f"{STYLE} A real photographed frame from a big-budget film of {SHIPDESC}. Realistic hull materials with subtle reflections, volumetric "
                  "atmosphere and haze, glowing bloom on the lights and engines, rich cinematic lighting; any ground is glossy black glass sand with sharp glassy shards.")
        jobs.append({"out": str(P / f"stills/cand/{rid}_polish.png"), "prompt": prompt, "init": str(srcimg), "strength": 0.42,
                     "w": 1248, "h": 720, "seed": 7, "steps": 9})
json.dump(jobs, open(P / "tools/jobs_stills_z.json", "w"), indent=1)
print(len(jobs), "jobs")
