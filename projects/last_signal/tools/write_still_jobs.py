#!/usr/bin/env python3
"""Start-still jobs for every qwen render in renders.json (+ the R18 Blender edit). 2 candidates each."""
import json
from pathlib import Path
P = Path(__file__).resolve().parent.parent
STYLE = ("Cinematic film still from a big-budget science fiction blockbuster, photorealistic, anamorphic lens, "
         "dramatic teal and orange grade, fine film grain, highly detailed, dynamic composition with strong depth.")
NAMES = {"canon/captain.png": "the Captain, the weathered woman in her forties with grey-streaked dark hair tied back, the chin scar and the worn olive-grey flight jacket",
         "canon/crewmate.png": "the Crewmate, the man in his thirties with warm brown skin, short dark curly hair, trimmed beard and olive-grey padded vest",
         "canon/plain_monoliths.png": "the alien world: black glass sand plain, dark carved monoliths with looping glyphs, orange storm sky",
         "canon/cockpit.png": "the cargo ship cockpit",
         "stills/refs/creature_layout_nobanner.png": "a rough painted layout guide of the creature and composition (layout only, not the final look)"}
EXTRA = {  # extra staging detail per render (beats.json keeps the judgeable wording)
 "R02_cockpit_alarm": "Medium shot from the side: the Captain in the pilot seat gripping the big throttle lever with both hands, jaw set, everything lit deep red by flashing alarm lamps, the orange storm outside the windows.",
 "R06_monolith_reveal": "Low camera just above the black glass ground, looking down an endless avenue of towering monoliths that recede to the horizon, torn fog in the foreground, epic scale.",
 "R07_crew_walk": "Wide side-on shot: the Captain in front and the Crewmate just behind her, both walking warily between two towering monoliths, small against them, faces visible in three-quarter view.",
 "R08_handwriting_glow": "Extreme close-up: a gloved right hand pressed flat against the dark stone; deep carved looping handwritten-style strokes, like a giant signature, run under and around the fingers and glow bright teal from within; dust in the light. Five fingers, natural pose.",
 "R09_captain_face": "Tight close-up of the Captain's face, lit from below by teal light, eyes wide with shocked recognition, lips slightly parted, wind-blown strands of hair, dark monolith behind.",
 "R10_lightwave": "High aerial view over the monolith plain at dusk-dark storm light: a huge expanding ring of teal-white light spreading outward across thousands of monoliths, lit ones glowing, unlit ones dark beyond the ring, curved horizon.",
 "R11_captain_welcome": "Wide low-angle shot: the Captain tiny and alone in the middle of a forest of towering monoliths that all glow teal, she looks up at the orange storm sky, frozen.",
 "R12_second_sun": "Wide shot looking up over monolith tops: the orange storm clouds torn open around a blinding white second sun, god rays blasting down, lens flare.",
 "R13_crewmate_yanked": "Dynamic action frame: the Crewmate airborne, body horizontal, flying backward away from camera into a wall of dark fog, arms and face toward camera in terror, motion blur, monoliths around.",
 "R15_mountain_shape": "Use the painted layout guide ONLY for composition and silhouette, and render it fully photoreal: The Watcher Beyond the Stones, a colossal tall thin giant made of weathered dark stone and drifting fog, long thin arms hanging to the ground, a crown of jagged stone spines on its head, a single vertical line of glowing teal eyes running down the center of its face and chest, standing behind the field of carved monoliths, as tall as a mountain. A tiny human figure in a spacesuit stands on the black glass in the foreground for scale. Orange storm sky with a blinding second sun and forks of lightning. Real rock texture, atmospheric haze, terrifying scale.",
 "R16_boots_crack": "Low ground-level close shot: heavy scuffed space boots mid-stride on the glossy black glass, bright white-hot cracks splitting through the glass beneath them, shards flying, motion blur.",
 "R17_captain_sprint": "Medium-wide shot from the front: the Captain sprinting straight toward camera between monoliths, desperate, motion blur, fog and orange lightning behind her.",
 "R19_giant_eye": "Photoreal close shot of the Watcher's face from the painted guide: weathered dark stone and drifting fog, a vertical line of enormous glowing teal eyes down the center, jagged stone spines above, dust falling, orange storm light.",
 "R20_crewmate_scream": "Tight close-up of the Crewmate screaming in terror, mouth wide open, harsh flashing white light on one side and orange on the other, fog behind.",
}
renders = json.load(open(P / "renders.json"))["renders"]
jobs = []
for r in renders:
    rid = r["id"]
    if r["source"] == "qwen":
        refs = r["identity"] + [r["set"]]
        if rid in ("R15_mountain_shape", "R19_giant_eye"):
            refs = ["stills/refs/creature_layout_nobanner.png"] + refs
        intro = " ".join(f"Image {i+1} shows {NAMES[x]}." for i, x in enumerate(refs))
        prompt = (f"{intro} Create a brand-new cinematic shot with a new camera angle and composition, keeping the people "
                  f"exactly as in their reference images and the same world, materials and colors. {STYLE} {EXTRA[rid]}")
        for s in (101, 202):
            jobs.append({"out": str(P / f"stills/cand/{rid}_s{s}.png"), "prompt": prompt,
                         "refs": [str(P / x) for x in refs], "w": 1248, "h": 720, "seed": s, "steps": 40})
    elif rid == "R18_ship_grab":
        prompt = ("Image 1 is a spaceship lifting off an alien black glass plain. Keep the spaceship exactly as it is, same design, "
                  "position and lighting. Add enormous dark rock-like claws, each bigger than a skyscraper, rising out of the black "
                  "glass ground and closing around the ship's hull from below, rock and glass pouring off them, lightning in the "
                  "orange storm sky. " + STYLE)
        for s in (101, 202):
            jobs.append({"out": str(P / f"stills/cand/{rid}_s{s}.png"), "prompt": prompt,
                         "refs": [str(P / "ship/renders/r15_liftoff.png")], "w": 1248, "h": 720, "seed": s, "steps": 40})
SHIPDESC = ("a colossal 8 km dark gunmetal cargo hauler with a long slightly wedge-shaped armored spine, stepped superstructure ridge, "
            "tall bridge tower near the stern, broad flat underbelly, blunt layered-armor prow, dense panel plating and greebles, "
            "thousands of tiny warm-white window lights, dashed cold teal running-light strips, six huge round blue-white engine nozzles")
for r in renders:
    if r["source"] == "blender" and r["id"] != "R18_ship_grab":
        src = P / r["start_still"].replace("_832.png", ".png")
        prompt = (f"Image 1 is a 3D render of {SHIPDESC}. Keep the spaceship's design, shape, position, camera angle and framing exactly "
                  "the same. Re-render the whole image as a real photographed frame from a big-budget film: realistic hull materials with "
                  "subtle reflections, volumetric atmosphere and haze, glowing light bloom on the lights and engines, rich cinematic lighting, "
                  "the ground (if any) is glossy black glass sand with sharp glassy shards. " + STYLE)
        jobs.append({"out": str(P / f"stills/cand/{r['id']}_polish.png"), "prompt": prompt, "refs": [str(src)],
                     "w": 1248, "h": 720, "seed": 7, "steps": 40})
json.dump(jobs, open(P / "tools/jobs_stills.json", "w"), indent=1)
print(len(jobs), "still jobs")
