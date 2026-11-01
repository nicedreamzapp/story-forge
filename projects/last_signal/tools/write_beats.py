#!/usr/bin/env python3
"""Writes beats.json + renders.json for THE LAST SIGNAL from one table (re-runnable)."""
import json, os
from pathlib import Path
P = Path(__file__).resolve().parent.parent

CAP = {"master": "canon/captain.png", "subject": "the Captain, a weathered woman in her 40s"}
CREW = {"master": "canon/crewmate.png", "subject": "the Crewmate, a man in his 30s"}
PLAIN = "canon/plain_monoliths.png"; COCKPIT = "canon/cockpit.png"; SHIP = "canon/ship.png"
NO_TEXT = "legible text, letters or numbers anywhere in frame"
HOUSE = [NO_TEXT, "a cartoon or toy look"]

# id, source, hero, start still, beat (visible state, one frame), clip_beat (true for the whole clip),
# animate (motivated action / camera move), must_not, identity, set
R = [
 ("R01_asteroids", "blender", False, "ship/renders/r01_asteroids_832.png",
  "an enormous dark armored spaceship racing through a dense field of tumbling asteroids in deep space",
  "the huge spaceship rushes toward camera between asteroids for the whole shot, rocks streaking past",
  "fast forward rush: the camera flies backward as the massive spaceship charges straight at it, asteroids tumble and streak past the lens left and right, engine glow flickers, debris flashes by",
  ["a small fighter jet", "an airplane", "a planet surface"], [], SHIP),
 ("R02_cockpit_alarm", "qwen", False, "stills/R02_cockpit_alarm.png",
  "a woman pilot in her 40s gripping the flight controls in a dark spaceship cockpit lit by red alarm lights",
  "the cockpit stays bathed in pulsing red alarm light while the pilot holds the lever, the cabin shaking",
  "red alarm lights pulse and strobe across the cockpit, the woman shoves the big throttle lever forward hard, the whole cabin shudders violently, sparks drift, the camera shakes with the turbulence",
  ["a man as the pilot", "daylight", "a calm smiling face"], [CAP], COCKPIT),
 ("R03_dive", "blender", False, "ship/renders/r03_dive_832.png",
  "the dark armored spaceship seen from behind, engines blazing blue, flying into a vast orange storm",
  "the spaceship dives into the orange storm wall for the whole shot, lightning flashing inside the clouds",
  "the camera chases the spaceship from behind as it dives steeply into the wall of orange storm clouds, lightning bolts flash and fork inside the clouds, engines blaze blue, cloud vapor whips past",
  ["blue sky", "a small airplane"], [], SHIP),
 ("R04_arrival", "blender", True, "ship/renders/r04_arrival_a_832.png",
  "a colossal city-sized spaceship emerging from an orange cloud ceiling above a black glass plain, its dark underbelly filling the sky, tiny lights across its hull",
  "the colossal ship descends out of the clouds for the whole shot, its hull filling the sky and its shadow over the plain",
  "the colossal ship pushes down out of the churning orange clouds, cloud vapor tearing off its hull and spilling around it, the camera whips forward and tilts up under its enormous belly while its huge dark shadow races across the black glass ground toward and past the camera, swallowing the light, lightning flickers in the clouds",
  ["a small ship", "blue sky", "green land"], [], SHIP),
 ("R05_claws", "blender", False, "ship/renders/r05_claws_832.png",
  "a massive mechanical landing leg with a claw foot planted on dark ground beneath the looming lit hull of a giant spaceship, orange storm sky",
  "the landing claw stays planted while a ring of glass shards and black dust rushes outward toward camera",
  "a shockwave ring of shattered black glass shards and dust blasts outward from the planted landing claw and rushes toward the camera, the hull above rumbles, the camera shakes from the shockwave",
  ["a robot hand", "an animal claw", "green ground"], [], SHIP),
 ("R06_monolith_reveal", "qwen", True, "stills/R06_monolith_reveal.png",
  "a vast dark glassy plain covered with tall carved dark stone monoliths stretching to the horizon under an orange storm sky with lightning, fog drifting between them",
  "thousands of carved monoliths fill the plain to the horizon for the whole shot while fog streams past the camera",
  "the camera rockets forward low and fast through thick fog, the fog tears apart and thousands of carved monoliths rush into view stretching to the horizon, fog streaming past the lens, lightning flickers in the orange storm sky",
  ["trees or grass", "buildings or a city", "people"], [], PLAIN),
 ("R07_crew_walk", "qwen", False, "stills/R07_crew_walk.png",
  "a woman and a man in worn spacesuits walking between towering carved dark monoliths on black glass sand under an orange storm sky",
  "the two crew members keep walking between the monoliths, wind blowing fog and grit past them",
  "the camera tracks sideways alongside the woman and the man as they walk warily between the towering monoliths, wind whips fog and black grit across the ground, their suits flutter, lightning flickers above",
  ["more than two people", "helmets hiding both faces", "daylight blue sky"], [CAP, CREW], PLAIN),
 ("R08_handwriting_glow", "qwen", True, "stills/R08_handwriting_glow.png",
  "close-up of a gloved hand pressed flat on carved handwritten-looking glyphs in a dark stone monolith, the carved grooves glowing bright teal under the fingers",
  "the hand stays still on the stone while teal light spreads through the carved grooves for the whole shot",
  "the hand stays perfectly still on the stone while bright teal light flows outward through the carved handwritten grooves, spreading from under the fingers across the rock, dust motes drift in the glow, the camera pushes in slowly as the light grows",
  ["moving or morphing fingers", "extra fingers", "a bare skeletal hand"], [], PLAIN),
 ("R09_captain_face", "qwen", False, "stills/R09_captain_face.png",
  "close-up of the weathered woman in her 40s, her face lit from below by teal light, eyes wide with shocked recognition",
  "the woman's face stays lit by the teal glow, eyes wide, for the whole shot",
  "the teal glow pulses brighter on her face from below, her eyes widen and her breath catches, wind moves strands of her hair, the camera pushes in slowly on her eyes",
  ["a smile", "a young woman", "a man"], [CAP], PLAIN),
 ("R10_lightwave", "qwen", True, "stills/R10_lightwave.png",
  "a high wide view of the dark monolith plain with a huge ring of bright teal light glowing among the monoliths",
  "a wave of teal light keeps racing outward across the monoliths toward the horizon for the whole shot",
  "a wave of teal-white light races outward from the center across thousands of monoliths, each one igniting in turn all the way to the curved horizon, the camera rises and pulls back to reveal the scale, storm clouds churn above",
  ["a city with streets", "water", "people in the foreground"], [], PLAIN),
 ("R11_captain_welcome", "qwen", False, "stills/R11_captain_welcome.png",
  "the weathered woman in a worn spacesuit standing small and frozen among towering glowing teal monoliths, looking up at the orange storm sky",
  "the woman stays frozen among the glowing monoliths, looking up, for the whole shot",
  "the woman stands frozen, slowly lifting her gaze upward as the glowing monoliths around her pulse together like a heartbeat, wind drives grit past her, the camera slowly pulls back and rises above her",
  ["a smile", "the woman running", "more than one person"], [CAP], PLAIN),
 ("R12_second_sun", "qwen", False, "stills/R12_second_sun.png",
  "two suns in an orange storm sky above dark monoliths: a dim orange sun low on the horizon and a second blinding white sun high above, blazing through a rip in the clouds",
  "the blinding second sun keeps burning through the torn clouds, rays sweeping over the monoliths",
  "the storm clouds rip open around a blinding white second sun, light rays explode outward and sweep across the monolith field, clouds boil away from the tear, lens flare, the camera tilts up fast toward the light",
  ["a normal sunset", "a moon", "blue sky"], [], PLAIN),
 ("R13_crewmate_yanked", "qwen", False, "stills/R13_crewmate_yanked.png",
  "a man in a worn spacesuit with his feet off the ground, his body bent backward as he is dragged away sideways into a wall of dark fog among monoliths",
  "the man is pulled backward away into the fog for the whole shot, receding and vanishing",
  "the man is yanked backward off his feet and hurtles away into the thick fog, arms flailing toward the camera, fog swirling violently around him, he vanishes into the dark, the camera lurches after him",
  ["the man standing calmly", "a woman", "a visible creature"], [CREW], PLAIN),
 ("R14_engines_fire", "blender", False, "ship/renders/r12_engines_832.png",
  "the rear engine bank of the giant dark spaceship erupting in roaring blue fire and sparks against an orange sky",
  "the engines keep blasting blue fire and sparks for the whole shot",
  "the huge engine nozzles explode into roaring blue fire, jets of blue flame and showers of sparks blast outward, heat distortion ripples, debris flies, the camera is rocked by the blast",
  ["orange flames only", "a car", "a rocket on a launch pad"], [], SHIP),
 ("R15_mountain_shape", "qwen", True, "stills/R15_mountain_shape.png",
  "a towering thin giant made of dark stone and fog with long arms, a crown of jagged spines and a vertical line of glowing teal eyes down its face, standing behind a field of carved monoliths under an orange storm sky, a tiny human figure in the foreground",
  "the colossal stone-and-fog giant keeps rising behind the monoliths for the whole shot, its vertical line of teal eyes glowing",
  "the colossal stone-and-fog giant rises up behind the monoliths, rock and black sand pouring off its long arms, fog streaming off its spine crown, its vertical line of teal eyes igniting one by one from top to bottom, lightning silhouettes it, the camera tilts up slowly to follow its terrifying height",
  ["a cute monster", "a normal mountain with snow", "a city", "a robot"], [], PLAIN),
 ("R16_boots_crack", "qwen", False, "stills/R16_boots_crack.png",
  "low close view of heavy space boots running on black glass sand, bright cracks splitting through the glass under them",
  "the boots keep running while cracks race through the black glass behind them",
  "low tracking shot racing alongside heavy boots sprinting across the black glass, bright cracks race and split through the glass under each step, shards and grit kick up, the camera tracks fast and low",
  ["bare feet", "grass", "a road"], [], PLAIN),
 ("R17_captain_sprint", "qwen", False, "stills/R17_captain_sprint.png",
  "the weathered woman in a worn spacesuit sprinting toward camera between dark monoliths, fog and orange storm light behind her, face desperate",
  "the woman keeps sprinting toward the camera between the monoliths for the whole shot",
  "the woman sprints straight toward the camera, the camera tracks backward fast in front of her, monoliths whip past on both sides, fog and grit blast around her, orange lightning flashes behind",
  ["a smile", "a man", "the woman standing still"], [CAP], PLAIN),
 ("R18_ship_grab", "blender", True, "stills/R18_ship_grab.png",
  "the giant dark spaceship caught in the air between enormous dark stone claws rising from the plain, lightning in an orange storm sky",
  "the giant claws keep closing around the rising ship for the whole shot",
  "the giant ship strains upward, engines blazing blue, while the enormous dark claws rise and tighten around its hull, rock and black glass pouring off them, lightning flashes, the camera tilts up with the ship and shakes",
  ["a small ship", "a human hand", "blue sky"], [], SHIP),
 ("R19_giant_eye", "qwen", False, "stills/R19_giant_eye.png",
  "close-up of a vertical line of glowing teal eyes set in a dark stone-and-fog face",
  "the vertical line of teal eyes stays open and glowing for the whole shot",
  "the vertical line of teal eyes snaps open one after another down the dark stone face, the glowing irises contract and focus on the camera, dust and fog shake loose around them, the camera jolts forward",
  ["a human face", "a cartoon eye"], [], PLAIN),
 ("R20_crewmate_scream", "qwen", False, "stills/R20_crewmate_scream.png",
  "close-up of the man in his 30s in a worn spacesuit screaming in terror, face lit by flashing light, fog behind him",
  "the man keeps screaming in terror for the whole shot, light flashing on his face",
  "the man screams in terror, mouth wide open, flashing white and orange light strobes across his face, fog whips behind him, the camera shakes",
  ["a smile", "a woman"], [CREW], PLAIN),
]

# cuts in script order: (id, render, script shot, seconds, sentiment)
C = [
 ("c01_asteroids", "R01_asteroids", 1, 1.6, "instant adrenaline"),
 ("c02a_cockpit", "R02_cockpit_alarm", 2, 1.0, "danger"),
 ("c02b_lever", "R02_cockpit_alarm", 2, 0.9, "danger"),
 ("c01b_asteroids_close", "R01_asteroids", 1, 0.8, "instant adrenaline"),
 ("c03_dive", "R03_dive", 3, 1.6, "point of no return"),
 ("c03b_dive_clouds", "R03_dive", 3, 1.0, "point of no return"),
 ("c04_arrival", "R04_arrival", 4, 4.0, "overwhelming awe, the floor shakes"),
 ("c05_claws", "R05_claws", 5, 1.0, "impact"),
 ("c06_monolith_reveal", "R06_monolith_reveal", 6, 1.4, "wonder"),
 ("c06b_crew_walk", "R07_crew_walk", 6, 1.2, "wary wonder"),
 ("c07_handwriting", "R08_handwriting_glow", 7, 1.6, "the chill"),
 ("c07b_captain_face", "R09_captain_face", 7, 1.0, "the chill"),
 ("c08_lightwave", "R10_lightwave", 8, 2.2, "wonder turning to fear"),
 ("c09_welcome", "R11_captain_welcome", 9, 3.0, "the gut-punch"),
 ("c10_second_sun", "R12_second_sun", 10, 0.6, "panic"),
 ("c10b_second_sun", "R12_second_sun", 10, 0.5, "panic"),
 ("c11_yanked", "R13_crewmate_yanked", 11, 0.7, "panic"),
 ("c11b_yanked", "R13_crewmate_yanked", 11, 0.5, "panic"),
 ("c12_engines", "R14_engines_fire", 12, 0.6, "panic"),
 ("c12b_engines", "R14_engines_fire", 12, 0.5, "panic"),
 ("c13_mountain", "R15_mountain_shape", 13, 0.9, "terror"),
 ("c13b_mountain", "R15_mountain_shape", 13, 0.6, "terror"),
 ("c14_boots", "R16_boots_crack", 14, 0.5, "panic"),
 ("c14b_sprint", "R17_captain_sprint", 14, 0.6, "panic"),
 ("c14c_boots", "R16_boots_crack", 14, 0.4, "panic"),
 ("c15_grab", "R18_ship_grab", 15, 0.9, "overload"),
 ("c15b_grab", "R18_ship_grab", 15, 0.6, "overload"),
 ("c15c_sprint", "R17_captain_sprint", 15, 0.4, "overload"),
 ("c16a_light", "R12_second_sun", 16, 0.35, "overload"),
 ("c16b_eye", "R19_giant_eye", 16, 0.35, "overload"),
 ("c16c_claw", "R18_ship_grab", 16, 0.3, "overload"),
 ("c16d_fire", "R14_engines_fire", 16, 0.3, "overload"),
 ("c16e_monolith", "R10_lightwave", 16, 0.25, "overload"),
 ("c16f_scream", "R20_crewmate_scream", 16, 0.3, "overload"),
 ("c16g_eye", "R19_giant_eye", 16, 0.25, "overload"),
 ("c16h_mountain", "R15_mountain_shape", 16, 0.2, "overload"),
 ("c16i_scream", "R20_crewmate_scream", 16, 0.2, "overload"),
 ("c17_black", None, 17, 2.5, "the question that stays"),
 ("c18_title", None, 18, 4.0, "wanting more"),
]

rmap = {r[0]: r for r in R}
shots = []
for cid, rid, sn, sec, sent in C:
    if rid is None:
        shots.append({"id": cid, "script_shot": sn, "seconds": sec, "sentiment": sent,
                      "render": None, "kind": "graphic",
                      "beat": "black frame" if sn == 17 else "the title THE LAST SIGNAL on black",
                      "note": "made in part 2 (edit/graphics), no render"})
        continue
    r = rmap[rid]
    s = {"id": cid, "script_shot": sn, "seconds": sec, "sentiment": sent, "render": rid,
         "clip": f"clips/{rid}.mp4", "lock": f"stills/LOCKED_{rid}.png", "beat": r[4], "clip_beat": r[5],
         "must_not": r[7] + HOUSE}
    if r[8]: s["identity"] = r[8]
    s["set"] = r[9]
    shots.append(s)

spine = [
 {"beat": "a spaceship is in danger, racing through an asteroid field", "shots": ["c01_asteroids"]},
 {"beat": "a woman captain is at the controls under red alarms", "shots": ["c02a_cockpit", "c02b_lever"]},
 {"beat": "the ship plunges into an orange lightning storm", "shots": ["c03_dive"]},
 {"beat": "the ship is colossal, city-sized, and arrives over an alien plain", "shots": ["c04_arrival"]},
 {"beat": "the ship lands hard on black glass", "shots": ["c05_claws"]},
 {"beat": "the plain is covered with endless carved monoliths", "shots": ["c06_monolith_reveal"]},
 {"beat": "the captain and her crewmate walk among the monoliths", "shots": ["c06b_crew_walk"]},
 {"beat": "the captain's touch makes a carved symbol glow, and she recognizes it", "shots": ["c07_handwriting", "c07b_captain_face"]},
 {"beat": "every monolith lights up in a wave across the planet", "shots": ["c08_lightwave"]},
 {"beat": "the captain stands frozen as the planet speaks to her", "shots": ["c09_welcome"]},
 {"beat": "the planet attacks: second sun, crewmate taken, engines destroyed, a colossal shape rises", "shots": ["c10_second_sun", "c11_yanked", "c12_engines", "c13_mountain"]},
 {"beat": "the captain runs for her life", "shots": ["c14_boots", "c14b_sprint"]},
 {"beat": "something huge grabs the ship as it tries to leave", "shots": ["c15_grab"]},
]

renders = []
for r in R:
    cuts = [c[0] for c in C if c[1] == r[0]]
    renders.append({"id": r[0], "source": r[1], "hero": r[2], "takes": 3 if r[2] else 2,
                    "start_still": f"stills/LOCKED_{r[0]}.png", "source_still": r[3], "animate": r[6], "beat": r[4], "clip_beat": r[5],
                    "identity": [i["master"] for i in r[8]], "set": r[9], "feeds_cuts": cuts,
                    "res": "832x480", "duration": 5.0})

beats = {"_note": "THE LAST SIGNAL (script v3, locked). shots[] = the ~40 CUTS in script order; each cut is pulled from a RENDER (renders.json). Several half-second cuts come from one 5s render. beat = one-frame visible state for beat_gate; clip_beat = what stays true over the clip.",
         "spine": spine, "set_masters": {"plain_monoliths": PLAIN, "cockpit": COCKPIT, "ship": SHIP},
         "shots": shots}
tmp = P / "beats.json.tmp"; tmp.write_text(json.dumps(beats, indent=1)); os.replace(tmp, P / "beats.json")
tmp = P / "renders.json.tmp"
tmp.write_text(json.dumps({"_note": "Render plan: each render is one 5s start-still->motion clip (plus takes); feeds_cuts = the cuts in beats.json pulled from it.", "renders": renders}, indent=1))
os.replace(tmp, P / "renders.json")
tot = sum(c[3] for c in C)
print(f"{len(C)} cuts, {tot:.1f}s, {len(R)} renders, {sum(3 if r[2] else 2 for r in R)} takes")
