#!/usr/bin/env python3
"""SFX job list for tools/sfx_batch.py. Picture-synced (--video) jobs cut the SELECTED take from the cut's in-point to
the take's end (the picture the audience sees, plus the natural tail), so MMAudio syncs to the actual frames."""
import json, subprocess
from pathlib import Path
P = Path(__file__).resolve().parent.parent
e = {c["id"]: c for c in json.load(open(P / "final/edl_final.json"))["cuts"]}
NEG = "music, speech, voice, talking, singing, melody"
V = [  # name, cut id, prompt
 ("arrival_rumble", "c04_arrival", "colossal spaceship descending overhead, deep thunderous engine rumble, roaring thrusters, wind blast and debris"),
 ("claws_impact", "c05_claws", "massive metal landing claw slamming into black glass ground, huge heavy impact, glass shattering, shards scattering"),
 ("engines_explosion", "c12_engines", "enormous explosion, blue fire roaring out of rocket engines, crackling sparks, violent blast"),
 ("lightwave_whoosh", "c08_lightwave", "deep resonant energy whoosh sweeping outward, rising electric hum, powerful wave of light"),
 ("creature_rise", "c13_mountain", "colossal stone giant rising, grinding rock, deep earth rumble, monstrous low groan"),
 ("ship_grab", "c15_grab", "giant metal starship hull crushed and groaning, electric crackling, huge impact, metal screeching"),
 ("glass_crack", "c14_boots", "boots running on glass, glass cracking and splintering loudly under each footstep"),
 ("asteroids_flyby", "c01_asteroids", "spaceship roaring toward camera, rocks whooshing past, deep engine rumble"),
 ("cockpit_alarm", "c02a_cockpit", "spaceship cockpit alarm klaxon blaring, rattling cabin, electrical sparks"),
 ("dive_thunder", "c03_dive", "thunder cracking, lightning strikes, howling storm wind, distant engine roar"),
 ("yanked", "c11_yanked", "violent whoosh, body dragged away through dust, sudden wind gust"),
 ("second_sun", "c10_second_sun", "blinding flash, searing rising tone, deep rumble"),
 ("monolith_reveal", "c06_monolith_reveal", "rushing wind through fog, rolling thunder"),
 ("handwriting_glow", "c07_handwriting", "soft resonant hum growing, shimmering energy, stone vibrating"),
 ("crew_walk", "c06b_crew_walk", "footsteps crunching on glass gravel, howling wind"),
]
T = [  # name, seconds, prompt, seed
 ("boom_1", 4, "deep cinematic trailer boom hit, huge impact, sub bass", 21),
 ("boom_2", 4, "massive cinematic impact boom, deep thud with long rumble tail", 22),
 ("braam", 5, "massive low brass braam, enormous foghorn blast, cinematic trailer", 23),
 ("riser_4s", 4, "cinematic tension riser, rising whoosh building up, reverse swell", 24),
 ("riser_6s", 6, "long cinematic riser, rising metallic screech and whoosh building to a peak", 25),
 ("radio_beep", 2, "radio beep, electronic sonar ping", 26),
 ("horn_hit", 2, "short loud brass horn stab hit, orchestral", 27),
 ("whoosh", 2, "fast whoosh swish transition", 28),
 ("final_hit", 5, "colossal cinematic final impact hit with long reverb tail", 29),
 ("sub_drop", 3, "deep sub bass drop boom", 30),
]
jobs = []
for name, cid, prompt in V:
    c = e[cid]; src = P / c["src"]
    d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)]))
    o = P / f"sfx/src/{name}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(c["in"]), "-i", str(src), "-an", "-c:v", "libx264", "-crf", "10", str(o)], check=True)
    jobs.append({"name": name, "prompt": prompt, "seconds": round(d - c["in"], 2), "video": str(o), "out": str(P / f"sfx/{name}.wav"),
                 "seed": 7, "negative": NEG, "film_start": c["start"]})
for name, s, prompt, seed in T:
    jobs.append({"name": name, "prompt": prompt, "seconds": s, "out": str(P / f"sfx/{name}.wav"), "seed": seed, "negative": NEG})
json.dump(jobs, open(P / "sfx/jobs.json", "w"), indent=1)
print(len(jobs), "jobs")
