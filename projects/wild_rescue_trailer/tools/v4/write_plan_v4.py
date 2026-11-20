#!/usr/bin/env python3
"""Rebuild v4 plan writer (2026-11-01 evening). Reads renders.json + beats.json (kept, the cut map) and writes:
  v4/plan.json          every render: engine (k6 | ltx_a2v | blender), still prompt (bible_v4 strings word for word),
                        animate prompt, beat (one-frame state for the gate), must_not, clip seconds (cut + 0.5 s
                        handles, floor 1.5 s), takes, still seeds
  v4/jobs_canon.json    Krea 2 Turbo canon masters (2 seeds each)
  v4/jobs_stills.json   Krea 2 Turbo start-still candidates (3 seeds heroes, 2 the rest)
Blender owns every cut where vehicle wheels read (LESSONS 11/1) plus the ant-swarm animations; the queue uses
clips/blender/T_<cut>.mp4 for those. Re-run any time; it never touches images."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bible_v4 import (STYLE_DAY, STYLE_NIGHT, STYLE_SET_DAY, STYLE_SET_NIGHT, STYLE_PROP_DAY, STYLE_PROP_NIGHT,
                      CHAR, SET, p)

P = Path(__file__).resolve().parents[2]
V4 = P / "v4"; V4.mkdir(exist_ok=True)
R = {r["id"]: r for r in json.load(open(P / "renders.json"))["renders"]}
CUTS = {s["id"]: s for s in json.load(open(P / "beats.json"))["shots"]}
D, H, F, W, T, C, DS = CHAR["doug"], CHAR["hank"], SET["forest"], SET["wagon"], SET["train"], SET["canyon"], SET["desert"]
TEAM = CHAR["team"]

DOUG_NOT = ["a beagle, basset or short-eared hound instead of a long-eared wrinkled bloodhound",
            "a black saddle marking or white legs on the dog"]
TEAM_NOT = ["more or fewer than four pulling animals", "two horses, two camels or two cows in the team",
            "rubber tires, a truck or a car", "the wagon in front of the animals or pushing them"]
BEAR_DOG_NOT = ["the dog and bear merged into one body", "the bear the same size as the dog"]

# id: (engine, style, body, animate, beat, extra must_not)
S = {
 "R01_night_hunt": ("k6", STYLE_NIGHT, f"Low tracking shot on a moonlit forest trail. {D}, younger and leaner, nose pressed to the ground sniffing, head low, ears dragging in the dirt, following a scent along the trail toward camera. Behind him an oil lantern dangles on a short rope from the very top edge of the frame, held from above out of view, casting a warm amber pool of light on the trail. {F}.",
    "the bloodhound sniffs his way forward along the trail toward camera, long ears swinging, the lantern behind him sways and its amber light swings across the ground; camera tracks backward with him",
    "a long-eared russet-red bloodhound with his nose to the ground on a moonlit forest trail, a lantern glowing above and behind him", DOUG_NOT),
 "R02_bear_hiding": ("k6", STYLE_NIGHT, f"Medium shot. {H}, younger, crouched low and trembling behind a fallen mossy log in the moonlit forest, eyes wide with fear, ears pinned back, paws gripping the log, the forest floor around him dark and empty. {F}.",
    "the frightened bear trembles and shrinks lower behind the log, his wide eyes darting toward a sweep of amber light off-screen; slow push in on his face",
    "a frightened brown bear hiding behind a fallen log in a moonlit forest, eyes wide, ears pinned back", ["a lantern on the ground"]),
 "R03_eye_contact": ("k6", STYLE_NIGHT, f"Two-shot at eye level in the moonlit forest. At left, {D}, younger and leaner, has stopped dead on the trail, one front paw raised, his face softening as he looks across at the bear. His back, sides and legs are all the same warm russet-red as his face, one single color all over, lit warm by the amber glow. At right, {H}, younger, peeking frightened over a fallen mossy log. Their eyes meet across the trail, a clear gap between them. Warm amber glow from behind the dog, blue moonlight on the bear. {F}.",
    "the bloodhound slowly lowers his raised paw and his worried brow softens as he holds the frightened bear's gaze; the bear blinks; gentle push in between them",
    "a long-eared bloodhound standing on a forest trail looking at a frightened brown bear peeking over a fallen log, their eyes meeting, at night", DOUG_NOT + BEAR_DOG_NOT + ["the dog barking or attacking"]),
 "R04_doug_leads_away": ("k6", STYLE_NIGHT, f"Wide side shot of a fork in a forest trail. {D}, younger and leaner, bolting away down the right-hand path toward the right edge of frame, ears flying, looking back over his shoulder as if calling someone to follow, a beam of amber light from off-screen left chasing after him, away from the fallen mossy log on the left. His back, sides and legs are all the same warm russet-red as his face, one single color all over, lit warm by the amber glow. {F}.",
    "the bloodhound bolts away down the side path toward frame right, long ears flapping, glancing back over his shoulder; camera pans right to follow him",
    "a long-eared bloodhound running away down a forest path at night, ears flying, looking back over his shoulder", DOUG_NOT + ["a lantern standing on the ground"]),
 "R05_lantern_ditch": ("k6", STYLE_PROP_NIGHT, f"Low close shot. A lit brass oil lantern tumbling end over end down the muddy bank of a dark ditch among tangled roots, its glass glinting, warm light spinning across the mud and ferns, a splash of mud. {F}. No people, no hands, no feet.",
    "the lit lantern tumbles down the muddy bank and rolls into the ditch, its light spinning across the roots, mud splashing; camera holds low",
    "a lit oil lantern tumbling down into a muddy ditch among tangled roots at night", ["a hand, arm, boot or any part of a person", "a burning fire spreading"]),
 "R06_rails_scream": ("blender", None, None, None, None, []),
 "R07_rabbit_ears": ("k6", STYLE_DAY, f"Close shot in the early morning desert. {CHAR['rabbit']}, crouched on red sand by a sagebrush, its enormous ears shooting straight up alert, eyes wide, whiskers trembling. {DS}.",
    "the jackrabbit's ears snap straight up and swivel toward the sound, whiskers trembling, eyes widening; quick push in",
    "a jackrabbit with both tall ears standing straight up, alert, in the desert", []),
 "R08_rabbit_thump": ("k6", STYLE_DAY, f"Low ground-level shot. {CHAR['rabbit']}, stamping one long hind foot hard on the red desert ground, a puff of dust bursting up around the foot, ears high. {DS}.",
    "the jackrabbit thumps its hind foot hard on the ground twice, dust puffing up each time, ears quivering; camera holds low",
    "a jackrabbit with one hind foot down on the desert ground in a puff of dust", []),
 "R09_hawk_cry": ("k6", STYLE_DAY, f"Medium close shot against a turquoise sky. {CHAR['hawk']}, perched on top of a tall saguaro cactus, beak wide open in a piercing cry, wings half spread. {DS}.",
    "the hawk throws its head back and screeches, beak wide open, then spreads its wings to launch; slight low angle push in",
    "a red-tailed hawk on a saguaro cactus with its beak wide open", []),
 "R10_prairie_whistle": ("k6", STYLE_DAY, f"Close shot. {CHAR['prairie']}, popping straight up out of its sandy burrow mound, standing tall on its hind legs, mouth open in a sharp whistle, paws at its chest. {DS}.",
    "the prairie dog pops up out of its burrow, stands tall and whistles with its mouth open, little body shaking; camera holds",
    "a prairie dog standing upright at its burrow with its mouth open", []),
 "R11_wagon_burst": ("k6", STYLE_DAY, f"Low front shot, close on the team bursting out through the open doors of a red-rock firehouse barn in a thick cloud of golden dust: {TEAM}, charging toward camera, filling the lower two thirds of the frame. Behind and above them the front of {W} with its brass bell, and {CHAR['giraffe']} riding tall on the wagon bed; the bottom of frame is hooves and dust, the wagon's wheels hidden behind the animals and the dust cloud.",
    "the four animals charge forward out of the barn pulling the fire-wagon, legs galloping, a thick cloud of golden dust rolling around the wagon, the brass bell swings; camera low as they thunder past toward frame left",
    "a red wooden fire-wagon pulled by a horse, a zebra, a camel and a cow side by side bursting out of a barn in dust, the animals out in front", TEAM_NOT),
 "R12_wheel": ("blender", None, None, None, None, []),
 "R13_team": ("k6", STYLE_DAY, f"Front shot, low, close on the team. {TEAM}, charging straight toward camera across the desert, manes, stripes and hump bouncing, determined faces, leather traces running back to the front of {W} behind them, deep in golden dust; the bottom of frame is dust and hooves, no wheels visible.",
    "the horse, zebra, camel and cow gallop toward camera side by side in their harness, heads bobbing, dust kicking up; camera tracks backward ahead of them",
    "a horse, a zebra, a camel and a cow side by side in harness galloping toward camera in desert dust", TEAM_NOT),
 "R14_crew_side": ("k6", STYLE_DAY, f"Side tracking shot, framed from the wagon bed up. The top of {W}, rolling left across the desert above a low wall of golden dust that hides its wheels, {CHAR['giraffe']} standing tall on the wagon bed with their necks high, and {CHAR['elephants']}, trotting alongside, water sloshing from their barrels.",
    "the wagon rolls left with the giraffes swaying tall on its bed, the elephants trot alongside with water sloshing out of their barrels, ears flapping, dust rolling low; camera tracks sideways with them",
    "a red wooden fire-wagon with two giraffes standing on it and two elephants with water barrels trotting beside it in the desert", ["rubber tires, a truck or a car", "the wagon in front of the animals or pushing them"]),
 "R15_bench": ("k6", STYLE_DAY, f"Medium shot from just in front of the wagon looking back at the driver's bench, framed from the bench up, no wheels in frame. On the left, {H}, sitting on the wooden driver's bench holding the leather reins in his big paws, grinning. On the right beside him, {D}, much smaller than the bear, sitting tall and eager, his long ears flapping back in the wind. The brass bell swinging, golden dust, the bright red-and-gold wagon behind them.",
    "the wagon bounces gently, the bear grins and shakes the reins, the bloodhound beside him lifts his nose proudly into the breeze, both stay side by side and separate, the brass bell swings; camera rides steady in front of them",
    "a big brown bear holding reins and a smaller long-eared bloodhound sitting side by side on the driver's bench of a red wooden wagon", DOUG_NOT + BEAR_DOG_NOT + ["rubber tires, a truck or a car"]),
 "R16_train_desert": ("blender", None, None, None, None, []),
 "R17_tracks_end": ("k6", STYLE_SET_DAY, f"Low point-of-view shot between the rails. The railroad track runs straight ahead and simply ends at the rim of a deep red-rock canyon, the rails stopping in mid-air over the gap, the far rim across with the track continuing, mesas beyond. {C}.",
    "the camera rushes forward low along the rails toward the canyon edge where the track ends, ties flashing past underneath",
    "railroad tracks running straight ahead and ending abruptly at the edge of a deep canyon gap", ["the track continuing unbroken", "a train or vehicle"]),
 "R18_hank_line": ("ltx_a2v", STYLE_DAY, f"Medium close shot at the canyon rim. {H}, standing at the edge of the canyon staring at the gap, eyebrows raised in disbelief, mouth open mid-word, one big paw scratching his head. {C}.",
    "the bear stares at the gap and talks slowly, his mouth opening and closing as he speaks, eyebrows raised, scratching his head with one paw; slow push in",
    "a big brown bear at a canyon rim, eyebrows raised, mouth open", ["the bear smiling happily"]),
 "R19_doug_line": ("ltx_a2v", STYLE_DAY, f"Medium close shot at the canyon rim. {D}, looking up at his big friend off-screen with a determined little smile, mouth open mid-word, long ears lifting in the breeze. {C}.",
    "the bloodhound looks up and speaks with a determined smile, his mouth opening and closing as he talks, long ears lifting in the breeze; camera holds then eases in",
    "a long-eared bloodhound at a canyon rim looking up with a determined expression, mouth open", DOUG_NOT + ["the dog sad or crying"]),
 "R20_ground_moves": ("blender_alt_k6", STYLE_PROP_DAY, f"Macro shot low over the desert floor. Sand grains and pebbles trembling and sliding, and the first few {CHAR['ants']} pushing up out of the sand, sunlight flashing off the metal.",
    "the sand trembles and slides, pebbles hop, tiny metal-plated ants push up out of the ground, glints flashing; slow push in",
    "tiny red ants with shiny metal plates on their backs emerging from desert sand", ["beetles instead of ants"]),
 "R21_ant_river": ("blender_alt_k6", STYLE_PROP_DAY, f"Elevated wide shot. A vast flowing river of millions of {CHAR['ants']}, pouring across the red desert toward the canyon rim like liquid metal, thousands of sparkles of sunlight. {C}.",
    "the river of ants pours forward across the desert toward the canyon, shimmering with glints; camera cranes up and forward over it",
    "a vast river of countless tiny ants with glinting metal plates pouring across the desert toward a canyon", ["water instead of ants"]),
 "R22_ant_hero": ("k6", STYLE_PROP_DAY, f"Macro low shot. {CHAR['ant']}, marching toward camera at the head of a column of thousands of identical metal-plated ants, the sun catching the steel plate, determined little face, golden sand.",
    "the lead ant marches toward camera with the column behind it, six legs stepping, steel plate glinting, antennae bobbing; camera tracks backward low",
    "a tiny red ant wearing a metal plate on its back at the head of a column of ants", ["a beetle instead of an ant"]),
 "R23_ant_bridge": ("blender_alt_k6", STYLE_PROP_DAY, f"Wide shot of the canyon gap. Millions of {CHAR['ants']}, linking legs into a living bridge that spans the gap from rim to rim right under the ends of the rails, glinting in the sun, a deep canyon below. {C}.",
    "the living bridge of ants ripples and tightens across the gap as more ants pour on and lock together, glinting; camera pushes in toward the bridge",
    "a living bridge made of countless tiny metal-plated ants spanning a canyon gap under the ends of the rails", ["the gap empty"]),
 "R24_giraffes_spot": ("k6", STYLE_DAY, f"Low angle shot. {CHAR['giraffe']}, standing at the canyon rim with their long necks craned far out over the gap, peering down to guide, one nodding. {C}.",
    "the two giraffes stretch their long necks out over the gap and peer down, one nods; camera tilts up their necks",
    "two giraffes standing at a canyon rim with their long necks stretched out over the gap", []),
 "R25_elephant_trumpet": ("k6", STYLE_DAY, f"Low angle medium shot. {CHAR['elephant']}, rearing its head back and raising its own long trunk high in the air, mouth open bellowing a mighty call through the trunk, ears flared wide, a spray of water from the trunk tip sparkling. Nothing held in the trunk. {C}.",
    "the elephant raises its trunk high and bellows, ears flaring, water spraying from the trunk tip; camera low and pushing in",
    "an elephant with its own trunk raised high at a canyon rim, nothing held", ["a brass horn, trumpet or any musical instrument"]),
 "R26_whistle": ("blender", None, None, None, None, []),
 "R27_monkey_eyes": ("k6", STYLE_DAY, f"Medium close shot inside the cab of a red-and-gold circus steam locomotive. {CHAR['monkey']}, covering his eyes with both little hands, mouth in a wobbly grimace, cap askew, the desert rushing past the cab window behind him.",
    "the monkey conductor clamps both hands over his eyes and shakes, cap wobbling, the cab rattling, desert streaking past the window; camera shakes with the cab",
    "a small monkey conductor in a cap covering his eyes with both hands inside a locomotive cab", []),
 "R28_bridge_link": ("k6", STYLE_PROP_DAY, f"Macro shot. Dozens of {CHAR['ants']}, gripping each other's legs and locking together into a woven chain over a deep red-rock canyon drop, more ants climbing on.",
    "the ants grip and lock legs, climbing over each other to close the chain, plates glinting; camera pushes in",
    "tiny metal-plated ants gripping each other's legs to form a chain over a canyon", ["a paved road or road markings", "beetles instead of ants"]),
 "R29_doug_tense": ("k6", STYLE_DAY, f"Close shot at the canyon rim. {D}, ears lifted, wide eyes fixed on something rushing toward him off-screen, wrinkled brow tense, holding his breath, mouth closed. {C}.",
    "the bloodhound holds his breath, eyes widening as he tracks the oncoming train off-screen, ears lifting, brow tense, mouth closed; fast push in on his face",
    "a long-eared bloodhound at a canyon rim with wide tense eyes, mouth closed", DOUG_NOT + ["the dog's mouth open talking"]),
 "R30_wheels_edge": ("blender", None, None, None, None, []),
 "R31_ant_salute": ("k6", STYLE_PROP_DAY, f"Macro shot. {CHAR['ant']}, standing on a warm sandstone pebble raising one front leg to its brow in a crisp salute, looking up proudly, the dented steel plate catching the sunset, and far behind it, softly out of focus, the big droopy-eared face of a russet-red bloodhound looking down at it.",
    "the tiny ant snaps one front leg up to its brow in a salute and holds it, antennae twitching, standing proud; camera eases in",
    "a tiny ant with a dented metal plate with one front leg raised to its head", ["a beetle instead of an ant"]),
 "R32_doug_salute": ("k6", STYLE_DAY, f"Medium close shot at the canyon rim at sunset. {D}, raising one front paw to his brow in a proud salute, a warm soft smile, looking down at something tiny on the ground, mouth closed. {C}.",
    "the bloodhound raises one front paw to his brow in a salute and holds it, his face crinkling into a warm smile; camera eases in",
    "a long-eared bloodhound raising one front paw to his brow, smiling warmly", DOUG_NOT),
}
BLENDER_CUTS = {"R06_rails_scream": ["c02a_rails"], "R12_wheel": ["c03b_wheel"], "R16_train_desert": ["c04a_train"],
                "R26_whistle": ["c07d_whistle"], "R30_wheels_edge": ["c07h_edge"],
                "R20_ground_moves": ["c06a_ground"], "R21_ant_river": ["c06b_river"], "R23_ant_bridge": ["c07a_bridge"]}
NIGHT_NOT = "daylight"

plan = []
for rid, (eng, style, body, anim, beat, extra) in S.items():
    r = R[rid]
    cut_s = sum(CUTS[c]["seconds"] for c in r["feeds_cuts"])
    # generic: human / text / live-action (+ daylight on the night renders), then the render's own extras from renders.json
    base_not = r["must_not"][:3] + (["daylight"] if "daylight" in r["must_not"] else [])
    e = {"id": rid, "engine": eng, "hero": r["hero"], "feeds_cuts": r["feeds_cuts"], "cut_seconds": round(cut_s, 2),
         "clip_seconds": round(max(1.5, cut_s + 0.5), 2), "static": r.get("static", False),
         "blender_cuts": BLENDER_CUTS.get(rid, [])}
    if style:
        e.update(still=p(style, body), animate=anim, beat=beat,
                 must_not=list(dict.fromkeys(base_not + extra + [m for m in r["must_not"][3:] if m != "daylight"
                                                                   and "bridge" not in m])),
                 seeds=[11, 23, 37] if r["hero"] else [11, 23])
        # takes: renders.json count (3 heroes, 2/1 the rest); Blender-primary ant shots get ONE K6 alternate at the end
        e["takes"] = 1 if eng == "blender_alt_k6" else min(r["takes"], 3)
        if eng == "ltx_a2v":
            e["voice"] = {"R18_hank_line": "voices/c05a_hank.wav", "R19_doug_line": "voices/c05b_doug.wav"}[rid]
            e["takes"] = 2
    else:
        e["takes"] = 0
    if rid == "R14_crew_side":
        e["crop"] = [300, 0, 1049, 432]   # 1248x720 candidate -> top band (aspect kept), wheels below the cut
    plan.append(e)
json.dump(plan, open(V4 / "plan.json", "w"), indent=1)

# canon masters (stage 03): one per character and set, 2 seeds; the gate does not judge these, Matt approves them
CANON = {
 "doug": p(STYLE_DAY, f"Full-body character portrait in three-quarter view, standing on golden desert sand, centered, whole body and both long ears in frame. {D}."),
 "hank": p(STYLE_DAY, f"Full-body character portrait in three-quarter view, standing on golden desert sand, centered, whole body in frame. {H}."),
 "hank_doug_scale": p(STYLE_DAY, f"Full-body two-character portrait, standing side by side on golden desert sand, a clear gap between them. On the left {H}. On the right {D}."),
 "rabbit": p(STYLE_DAY, f"Full-body character portrait in three-quarter view, centered. {CHAR['rabbit']}. {DS}."),
 "hawk": p(STYLE_DAY, f"Character portrait, perched, three-quarter view, centered. {CHAR['hawk']}. {DS}."),
 "prairie": p(STYLE_DAY, f"Full-body character portrait, standing upright at its burrow, centered. {CHAR['prairie']}. {DS}."),
 "monkey": p(STYLE_DAY, f"Full-body character portrait in three-quarter view, centered. {CHAR['monkey']}, standing in a locomotive cab."),
 "giraffes": p(STYLE_DAY, f"Full-body portrait, centered. {CHAR['giraffe']}, standing side by side. {DS}."),
 "elephants": p(STYLE_DAY, f"Full-body portrait, centered. {CHAR['elephants']}, standing side by side. {DS}."),
 "ant": p(STYLE_PROP_DAY, f"Macro full-body character portrait in three-quarter view, centered on a sandstone pebble. {CHAR['ant']}."),
 "wagon_team": p(STYLE_DAY, f"Wide three-quarter side view of the whole rig standing still in the desert: {TEAM}, harnessed in front of {W}. {DS}."),
 "set_forest": p(STYLE_SET_NIGHT, f"Wide establishing shot. {F}."),
 "set_desert": p(STYLE_SET_DAY, f"Wide establishing shot. {DS}."),
 "set_canyon": p(STYLE_SET_DAY, f"Wide establishing shot. {C}."),
 "train": p(STYLE_SET_DAY, f"Wide three-quarter side view, standing on the track in the desert. {T}. {DS}."),
}
jobs_canon = [{"out": str(P / f"canon/cand/{k}_s{s}.png"), "prompt": v, "w": 1248, "h": 720, "seed": s}
              for k, v in CANON.items() for s in (11, 23)]
json.dump(jobs_canon, open(V4 / "jobs_canon.json", "w"), indent=1)
jobs = [{"out": str(P / f"stills/cand/{e['id']}_s{s}.png"), "prompt": e["still"], "w": 1248, "h": 720, "seed": s}
        for e in plan if e.get("still") for s in e["seeds"]]
json.dump(jobs, open(V4 / "jobs_stills.json", "w"), indent=1)
k6 = [e for e in plan if e["engine"] in ("k6", "blender_alt_k6")]
print(f"plan: {len(plan)} renders | k6 {sum(e['engine']=='k6' for e in plan)} (+{sum(e['engine']=='blender_alt_k6' for e in plan)} blender-alt) "
      f"| ltx_a2v {sum(e['engine']=='ltx_a2v' for e in plan)} | blender {sum(e['engine']=='blender' for e in plan)}")
print(f"krea jobs: canon {len(jobs_canon)}, stills {len(jobs)}; k6 takes {sum(e['takes'] for e in k6)}")
