#!/usr/bin/env python3
"""Stage 03 canon candidates: one master per character (full body, plain warm studio backdrop for clean
cutouts) and per natural set. Wagon/train masters derive from the Blender renders (img2img) in a 2nd batch."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bible import STYLE_DAY as D, STYLE_NIGHT as N, CHAR as C, SET as S, p
P = Path(__file__).resolve().parent.parent
BG = ("Character turnaround master: full body, three-quarter front view, standing on a plain smooth warm "
      "light-grey studio backdrop with a soft floor shadow, nothing else in frame, mouth closed, a warm friendly "
      "expression.")
chars = {
    "doug": C["doug"] + ", standing on all fours, head turned slightly toward camera.",
    "hank": C["hank"] + ", standing upright on his hind legs, arms relaxed at his sides.",
    "rabbit": C["rabbit"] + ", sitting up alert.",
    "hawk": C["hawk"] + ", perched on a weathered wooden post.",
    "prairie": C["prairie"] + ", standing upright on its hind legs.",
    "monkey": C["monkey"] + ", standing upright.",
    "giraffe": "a tall friendly reticulated giraffe with orange-brown patch patterns, short ossicone horns and long eyelashes, standing.",
    "elephant": C["elephant"] + ", standing.",
    "team": "A lineup side by side of three harnessed draft animals in brown leather harness: a chestnut horse, a tan one-humped camel and a black-and-white dairy cow, standing.",
    "ant": C["ant"] + ", standing proudly, seen large like a hero.",
}
jobs = []
for name, desc in chars.items():
    for seed in (11, 23, 37):
        jobs.append({"out": str(P / f"canon/cand/{name}_s{seed}.png"), "prompt": p(D, BG, desc),
                     "w": 1024, "h": 1024, "seed": seed, "steps": 9})
sets = {"set_forest": p(N, "Wide establishing shot, no animals.", S["forest"] + "."),
        "set_desert_rails": p(D, "Wide establishing shot, no animals, no train.", S["desert"] + "."),
        "set_canyon_gap": p(D, "Wide establishing shot, no animals, no train.", S["canyon"] + ".")}
for name, prompt in sets.items():
    for seed in (11, 23, 37):
        jobs.append({"out": str(P / f"canon/cand/{name}_s{seed}.png"), "prompt": prompt,
                     "w": 1248, "h": 720, "seed": seed, "steps": 9})
json.dump(jobs, open(P / "tools/jobs_canon.json", "w"), indent=1)
print(len(jobs), "jobs")
