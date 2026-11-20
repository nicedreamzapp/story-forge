#!/usr/bin/env python3
"""SFX job list for tools/sfx_batch.py (MMAudio, one load). Picture-synced (--video) jobs cut the SELECTED take from the
cut's in-point to the take's end, so MMAudio syncs to the frames the audience sees (plus the natural tail).
Text-mode jobs are the designed hits and beds. Every result is screened for noise-like hiss (spectral flatness +
centroid, LESSONS 10/31) by tools/sfx_screen.py before the mix."""
import json, subprocess
from pathlib import Path
P = Path(__file__).resolve().parent.parent
(P / "sfx/src").mkdir(parents=True, exist_ok=True)
e = {c["id"]: c for c in json.load(open(P / "final/edl_final.json"))["cuts"]}
NEG = "music, speech, voice, talking, singing, melody, human"
V = [  # name, cut id, prompt
 ("forest_sniff", "c01a_hunt", "a dog sniffing the ground in a quiet night forest, crickets chirping, soft footsteps on leaves"),
 ("lantern_tumble", "c01e_ditch", "a metal oil lantern tumbling down a muddy bank, glass and tin clanking, a soft splash into mud"),
 ("rails_scream", "c02a_rails", "steam locomotive steel wheels screeching on the rails, loud metal grinding squeal, sparks"),
 ("rabbit_thump", "c02c_thump", "a jackrabbit thumping its hind foot hard on dry dirt, two deep soft thuds"),
 ("hawk_cry", "c02d_hawk", "a red-tailed hawk screeching a loud piercing cry, wings flapping"),
 ("prairie_whistle", "c02e_prairie", "a prairie dog giving a sharp high-pitched alarm whistle chirp"),
 ("wagon_thunder", "c03a_burst", "galloping horses thundering hoofbeats, a heavy wooden wagon rumbling and creaking, harness bells jingling"),
 ("wheel_roll", "c03b_wheel", "a huge wooden wagon wheel rolling fast over gravel, iron rim crunching, pebbles spraying"),
 ("team_gallop", "c03c_team", "horses, camels and cows galloping, thundering hooves, snorting, harness jingling"),
 ("water_slosh", "c03d_crew", "water sloshing in big wooden barrels, heavy elephant footsteps, wooden wagon creaking"),
 ("train_chug", "c04a_train", "a steam train chugging fast, steam puffing, wheels clacking on the rails"),
 ("canyon_wind", "c04b_gap", "howling wind across a deep canyon, hollow echo"),
 ("ground_moves", "c06a_ground", "sand trickling, pebbles rattling, many tiny insect legs skittering"),
 ("ant_swarm", "c06b_river", "a huge swarm of insects skittering, thousands of tiny metal plates clinking and rattling"),
 ("ant_march", "c06c_hero_ant", "tiny marching footsteps, small metal armor plates clinking in rhythm"),
 ("bridge_lock", "c07a_bridge", "many small metal plates clinking and locking together, creaking strain, wind in a canyon"),
 ("elephant_trumpet", "c07c_trumpet", "an elephant trumpeting loudly, water splashing"),
 ("train_whistle", "c07d_whistle", "a steam train whistle screaming, a violent blast of steam"),
 ("cab_rattle", "c07e_monkey", "a rattling locomotive cab, metal shaking, chugging engine"),
 ("ants_link", "c07f_link", "small metal plates clicking and locking together, tiny legs gripping"),
 ("wheels_edge", "c07h_edge", "heavy train wheels grinding on rails, sparks crackling, pebbles falling into a deep canyon"),
]
T = [  # name, seconds, prompt, seed
 ("barn_burst", 3, "big wooden barn doors bursting open, heavy wooden crash and splintering bang", 31),
 ("boom_theme", 4, "deep cinematic trailer boom hit, huge impact, sub bass", 32),
 ("whoosh_1", 2, "fast whoosh swish transition", 33),
 ("whoosh_2", 2, "fast airy whoosh pass by", 34),
 ("riser", 4, "cinematic tension riser, rising whoosh building up, reverse swell", 35),
 ("smash_hit", 2, "massive cinematic impact hit, metal crash slam, cut off", 36),
 ("title_boom", 5, "colossal warm cinematic final impact boom with long reverb tail", 37),
 ("whistle_long", 4, "a steam locomotive whistle blowing long and loud, passing by", 38),
 ("wind_bed", 8, "steady desert wind blowing, soft and hollow, no birds", 39),
 ("night_bed", 8, "a calm night forest, crickets, a distant owl, soft breeze in pine trees", 40),
 ("salute_pop", 1, "tiny cartoon pop, light playful click", 41),
]
jobs = []
for name, cid, prompt in V:
    c = e[cid]; src = P / c["src"]
    d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)]))
    o = P / f"sfx/src/{name}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(c["in"]), "-i", str(src), "-an", "-c:v", "libx264", "-crf", "10", str(o)], check=True)
    jobs.append({"name": name, "prompt": prompt, "seconds": round(d - c["in"], 2), "video": str(o), "out": str(P / f"sfx/{name}.wav"),
                 "seed": 7, "negative": NEG, "cut": cid})
for name, s, prompt, seed in T:
    jobs.append({"name": name, "prompt": prompt, "seconds": s, "out": str(P / f"sfx/{name}.wav"), "seed": seed, "negative": NEG})
json.dump(jobs, open(P / "sfx/jobs.json", "w"), indent=1)
print(len(jobs), "jobs")
