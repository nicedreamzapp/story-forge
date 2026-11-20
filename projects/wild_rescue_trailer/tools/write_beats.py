#!/usr/bin/env python3
"""Stage 02 for HANK & DOUG'S WILD RESCUE (script v3, LOCKED): writes beats.json (the cuts, script order),
renders.json (each render = one start still -> one LTX clip, feeding one or more cuts) and continuity.json.
Re-run after any edit; both files are written with os.replace."""
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bible import STYLE_DAY as D, STYLE_NIGHT as N, STYLE_NIGHT_NOLAMP as NN, STYLE_SET_DAY as SD, STYLE_SET_NIGHT as SN, CHAR as C, SET as S, p

P = Path(__file__).resolve().parent.parent
B = "blender/renders/"
HOUSE = ["a human or person anywhere in frame", "legible text, letters or numbers anywhere in frame",
         "a photographic live-action look instead of 3D animation"]
WAGON_MN = ["a truck, car or engine", "rubber tires", "the wagon in front of the animals or pushing them"]

# id, source, hero, script shot, still prompt, init/strength, animate, beat (one frame), clip_beat (one frame,
# true at any moment), identity, set, must_not extras, dialogue
R = []
def r(id, source, hero, still, animate, beat, clip_beat, identity=(), set=None, init=None, strength=None,
      must_not=(), static=False, dialogue=None):
    R.append(dict(id=id, source=source, hero=hero, still=still, init=init, strength=strength, animate=animate,
                  beat=beat, clip_beat=clip_beat, identity=list(identity), set=set,
                  must_not=HOUSE + list(must_not), static=static, dialogue=dialogue))

# ---------------- 1 ORIGIN TEASE (night) ----------------
r("R01_night_hunt", "zimage", False,
  p(N, "Low tracking shot on a moonlit forest trail.", C["doug"] + ", younger and leaner, nose pressed to the "
    "ground sniffing, head low, ears dragging in the dirt, following a scent along the trail toward camera. Behind "
    "him an oil lantern dangles on a short rope from the very top edge of the frame, held from above out of view, "
    "casting a warm amber pool of light on the trail. The lantern is not on the ground.", S["forest"] + "."),
  "the bloodhound sniffs his way forward along the trail toward camera, ears swinging, the lantern behind him "
  "sways and its amber light swings across the ground; camera tracks backward with him",
  "a bloodhound with nose to the ground tracking a scent along a moonlit forest trail, a swinging oil lantern "
  "glowing behind him above", "a bloodhound with his nose to the ground on a moonlit forest trail, a lantern "
  "glowing behind him", identity=["doug"], must_not=["daylight", "a gun or weapon"])
r("R02_bear_hiding", "zimage", False,
  p(NN, "Medium shot.", C["hank"] + ", younger, crouched low and trembling behind a fallen mossy log in the moonlit "
    "forest, eyes wide with fear, ears pinned back, paws gripping the log, lit only by cold blue moonlight, the "
    "forest floor around him dark and empty.", S["forest"] + "."),
  "the frightened bear trembles and shrinks lower behind the log, his wide eyes darting toward the sweeping "
  "lantern light; slow push in on his face",
  "a frightened brown bear hiding behind a fallen log in a moonlit forest, eyes wide, ears pinned back",
  "a frightened brown bear crouched behind a fallen log in a moonlit forest", identity=["hank"],
  must_not=["daylight", "the bear smiling or relaxed", "the bear standing tall and roaring"])
r("R03_eye_contact", "composite", True,
  p(N, "Two-shot at eye level in the moonlit forest.", C["doug"] + ", younger and leaner, has stopped dead on the "
    "trail at left, one paw raised, face softening as he looks at", C["hank"] + ", younger, peeking frightened over "
    "a fallen mossy log at right. Their eyes meet. Warm lantern glow from behind the dog, blue moonlight on the bear.",
    S["forest"] + "."),
  "the bloodhound slowly lowers his raised paw and his worried brow softens as he holds the frightened bear's "
  "gaze; the bear blinks; gentle push in between them",
  "a bloodhound standing still on a forest trail looking at a frightened brown bear peeking over a fallen log, "
  "their eyes meeting, at night", "a bloodhound and a brown bear looking at each other across a fallen log at "
  "night", identity=["doug", "hank"], must_not=["daylight", "the dog barking or attacking", "the dog and bear "
  "merged into one body"])
r("R04_doug_leads_away", "zimage", False,
  p(NN, "Wide shot of a forest fork.", C["doug"] + ", younger and leaner, bolting away down the right-hand side "
    "path toward the right edge of frame, seen from the side, ears flying, looking back over his shoulder as if "
    "calling someone to follow, a beam of amber light from off-screen left chasing after him, AWAY from the fallen "
    "mossy log on the left, lit only by cold blue moonlight, the trail behind him dark and empty.", S["forest"] + "."),
  "the bloodhound bolts away down the side path toward frame right, ears flapping, glancing back over his "
  "shoulder, cold moonlight on the empty trail, no lantern; camera pans right to follow him",
  "a bloodhound running away down a forest path at night, ears flying, looking back over his shoulder, a lantern "
  "beam following him", "a bloodhound running down a forest path at night, ears flying", identity=["doug"],
  must_not=["daylight", "the dog running toward the camera with a bear"])
r("R05_lantern_ditch", "zimage", True,
  p(SN, "Low close shot.", "A lit brass oil lantern tumbling end over end down the muddy bank of a dark ditch "
    "among tangled roots, its glass glinting, warm light spinning across the mud and ferns, a splash of mud.",
    S["forest"] + ". No people, no hands, no feet."),
  "the lit lantern tumbles down the muddy bank and rolls into the ditch, its light spinning across the roots, "
  "mud splashing; camera holds low",
  "a lit oil lantern tumbling down into a muddy ditch among tangled roots at night",
  "a lit oil lantern lying in or falling into a muddy ditch at night", must_not=["daylight", "a hand, arm, boot "
  "or any part of a person", "a burning fire spreading"])

# ---------------- 2 THE CALL ----------------
r("R06_rails_scream", "blender", False,
  p(SD, "Extreme low close shot.", "The steel drive wheels and side rods of a red-and-gold circus steam locomotive "
    "screaming along the rail, bright orange sparks spraying from the wheel flange, motion blur, desert sand.",),
  "the steel drive wheels spin fast along the rail, side rods pumping, orange sparks spraying, the ground "
  "streaks past; camera rides alongside low",
  "the steel wheels of a steam locomotive racing on a rail with sparks flying",
  "steel locomotive wheels on a rail with sparks", init=B + "B07_train_wheels.png", strength=0.55,
  set="train")
r("R07_rabbit_ears", "zimage", False,
  p(D, "Close shot in the early morning desert.", C["rabbit"] + ", crouched on red sand by a sagebrush, its "
    "enormous ears shooting straight up alert, eyes wide, whiskers trembling.", S["desert"] + "."),
  "the jackrabbit's ears snap straight up and swivel toward the sound, whiskers trembling, eyes widening; quick "
  "push in", "a jackrabbit with both tall ears standing straight up, alert, in the desert",
  "an alert jackrabbit with tall upright ears in the desert", identity=["rabbit"])
r("R08_rabbit_thump", "zimage", False,
  p(D, "Low ground-level shot.", C["rabbit"] + " stamping one long hind foot hard on the red desert ground, a "
    "puff of dust bursting up around the foot, ears high.", S["desert"] + "."),
  "the jackrabbit thumps its hind foot hard on the ground twice, dust puffing up each time, ears quivering; "
  "camera holds low", "a jackrabbit stamping its hind foot on the desert ground with a puff of dust",
  "a jackrabbit with a hind foot on dusty desert ground, dust in the air", identity=["rabbit"])
r("R09_hawk_cry", "zimage", False,
  p(D, "Medium close shot against a turquoise sky.", C["hawk"] + " perched on top of a tall saguaro cactus, "
    "beak wide open in a piercing cry, wings half spread.", S["desert"] + "."),
  "the hawk throws its head back and screeches, beak wide open, then spreads its wings to launch; slight low "
  "angle push in", "a red-tailed hawk on a saguaro cactus with its beak wide open crying out",
  "a red-tailed hawk on a saguaro cactus, beak open", identity=["hawk"])
r("R10_prairie_whistle", "zimage", False,
  p(D, "Close shot.", C["prairie"] + " popping straight up out of its sandy burrow mound, standing tall on its "
    "hind legs, mouth open in a sharp whistle, paws at its chest.", S["desert"] + "."),
  "the prairie dog pops up out of its burrow, stands tall and whistles with its mouth open, little body "
  "shaking; camera holds", "a prairie dog standing upright at its burrow with its mouth open whistling",
  "a prairie dog standing upright at its burrow", identity=["prairie"])

# ---------------- 3 THEME HITS ----------------
r("R11_wagon_burst", "blender", True,
  p(D, "Low three-quarter front shot.", "The crew's fire-wagon bursts out through the open doors of a red-rock "
    "firehouse barn in a cloud of golden dust,", C["team"], "charging in front, pulling", S["wagon"] + ".",
    C["giraffe"], "riding tall on the wagon bed."),
  "the team charges forward out of the barn pulling the fire-wagon, the huge wooden wheels roll, dust billows, "
  "the brass bell swings; camera low as they thunder past toward frame left",
  "a big red wooden fire-wagon on huge wooden wheels pulled by horses, camels and cows bursting out of a barn in "
  "dust, the animals out in front", "a red wooden fire-wagon with huge wooden wheels pulled by horses, camels and "
  "cows in front of it, dust in the air", init=B + "B12_wagon_burst.png", strength=0.62, set="wagon",
  must_not=WAGON_MN)
r("R12_wheel", "blender", False,
  p(SD, "Ground-level close shot.", "A huge spoked wooden fire-wagon wheel with an iron rim and a polished brass "
    "hub thundering over the red desert ground, sand spraying, motion blur."),
  "the huge wooden wheel rolls fast past camera, spokes blurring, sand and pebbles spraying from the iron rim; "
  "camera low and tracking", "a huge spoked wooden wheel with an iron rim and brass hub rolling over desert ground",
  "a huge spoked wooden wheel with a brass hub on desert ground", init=B + "B13_wheel_close.png", strength=0.5,
  set="wagon", must_not=["a rubber tire", "a car or truck wheel"])
r("R13_team", "blender", False,
  p(D, "Front three-quarter shot.", C["team"] + ", charging straight toward camera across the desert, manes and "
    "humps bouncing, determined faces, leather traces running back to", S["wagon"], "behind them, golden dust."),
  "the horses, camels and cows gallop toward camera in their harness, heads bobbing, dust kicking up, the wagon "
  "following behind; camera tracks backward ahead of them",
  "a team of horses, camels and cows in harness galloping toward camera pulling a wooden wagon behind them",
  "horses, camels and cows in harness in front of a wooden wagon in the desert", init=B + "B14_team_front.png",
  strength=0.66, set="wagon", must_not=WAGON_MN)
r("R14_crew_side", "blender", False,
  p(D, "Side tracking shot.", S["wagon"] + ", rolling across the desert,", C["giraffe"], "standing tall on the "
    "wagon bed with their necks high, and two big friendly grey African elephants with huge flapping ears trotting "
    "alongside, oak water barrels with brass hoops strapped to their sides sloshing water, the team ahead at left."),
  "the wagon rolls left with the giraffes swaying tall on its bed, the elephants trot alongside with water "
  "sloshing out of their barrels, ears flapping; camera tracks sideways with them",
  "a red wooden fire-wagon with two giraffes standing on it and two elephants with water barrels trotting beside "
  "it in the desert", "a red wooden wagon with giraffes on it and elephants with barrels beside it",
  init=B + "B15_wagon_side.png", strength=0.45, set="wagon", must_not=WAGON_MN)
r("R15_bench", "composite", True,
  p(D, "Medium shot from in front of the wagon looking back at the driver's bench.", C["hank"], "sitting on the "
    "wooden driver's bench holding the leather reins in his big paws, grinning, and beside him", C["doug"] + ", "
    "sitting tall and eager, his long ears flapping back in the wind, the brass bell swinging, golden dust, the "
    "rumps of the cows soft in the foreground.", S["wagon"] + "."),
  "the wagon bounces gently, the bear grins and shakes the reins, the bloodhound beside him lifts his nose "
  "proudly into the breeze, both stay side by side and separate, the brass bell swings; camera rides steady in "
  "front of them",
  "a big brown bear holding reins and a bloodhound with long ears sitting side by side on the driver's bench of "
  "a red wooden wagon", "a brown bear and a bloodhound sitting on a red wagon's driver's bench",
  identity=["hank", "doug"], init=B + "B16_bench.png", strength=0.45, set="wagon",
  must_not=WAGON_MN + ["the dog and bear merged into one body", "the bear the same size as the dog"])

# ---------------- 4 STAKES ----------------
r("R16_train_desert", "blender", True,
  p(SD, "High aerial three-quarter shot.", S["train"] + ", barreling across the red-rock desert trailing a long "
    "plume of white steam, the single track curving ahead toward a canyon in the distance, mesas, long shadows."),
  "the circus train barrels across the desert trailing steam, wheels pumping; camera glides along above it",
  "a colorful circus steam train racing across a red desert on a single track, steam trailing",
  "a colorful circus steam train on a track in a red desert", init=B + "B17_train_wide.png", strength=0.55,
  set="train", must_not=["a modern diesel or electric train"])
r("R17_tracks_end", "blender", True,
  p(SD, "Low point-of-view shot between the rails.", "The railroad track runs straight ahead and simply ends at the "
    "rim of a deep red-rock canyon, the rails stopping in mid-air over the gap, the far rim across with the track "
    "continuing, mesas beyond.", S["canyon"] + "."),
  "the camera rushes forward low along the rails toward the canyon edge where the track ends, ties flashing "
  "past underneath",
  "railroad tracks running straight ahead and ending abruptly at the edge of a deep canyon gap",
  "railroad tracks ending at the edge of a deep canyon", init="canon/set_canyon_gap.png", strength=0.35,
  set="canyon", must_not=["a complete bridge across the gap", "the track continuing unbroken"])

# ---------------- 5 THE LAUGH ----------------
r("R18_hank_line", "composite", True,
  p(D, "Medium close shot at the canyon rim.", C["hank"] + ", standing at the edge of the canyon staring at the "
    "gap, eyebrows raised in disbelief, mouth open mid-word, one big paw scratching his head.", S["canyon"] + "."),
  "the bear stares at the gap and talks, his mouth opening and closing as he speaks slowly, eyebrows raised, "
  "scratching his head with one paw; slow push in",
  "a big brown bear at a canyon rim staring at the gap, eyebrows raised, mouth open talking",
  "a big brown bear at a canyon rim with his mouth open", identity=["hank"], set="canyon",
  must_not=["the bear roaring with fangs bared", "the bear smiling happily"],
  dialogue={"speaker": "HANK", "line": "Doug... that's a big hole."})
r("R19_doug_line", "composite", True,
  p(D, "Medium close shot at the canyon rim.", C["doug"] + ", looking up at his big friend with a determined "
    "little smile, mouth open mid-word, ears lifting in the breeze.", S["canyon"] + "."),
  "the bloodhound looks up and speaks with a determined smile, his mouth opening and closing as he talks, long "
  "ears lifting in the breeze; camera holds then eases in",
  "a bloodhound at a canyon rim looking up with a determined expression, mouth open talking",
  "a bloodhound at a canyon rim with his mouth open", identity=["doug"], set="canyon",
  must_not=["the dog barking aggressively", "the dog sad or crying"],
  dialogue={"speaker": "DOUG", "line": "Then we need a lot of help."})

# ---------------- 6 THE REVEAL ----------------
r("R20_ground_moves", "blender", False,
  p(D, "Macro shot low over the desert floor.", "Sand grains and pebbles trembling and sliding, and the first few "
    "tiny red ants with glinting steel plates on their backs pushing up out of the sand, sunlight flashing off "
    "the metal."),
  "the sand trembles and slides, pebbles hop, tiny metal-plated ants push up out of the ground, glints flashing; "
  "slow push in", "tiny red ants with shiny metal plates on their backs emerging from desert sand",
  "tiny red ants with shiny metal plates on desert sand", init=B + "B21_ground.png", strength=0.55)
r("R21_ant_river", "blender", True,
  p(D, "Elevated wide shot.", "A vast flowing river of millions of tiny red ants, each with a glinting steel plate "
    "on its back, pouring across the red desert toward the canyon rim like liquid metal, thousands of sparkles "
    "of sunlight.", S["canyon"] + "."),
  "the river of ants pours forward across the desert toward the canyon, shimmering with glints; camera cranes "
  "up and forward over it", "a vast river of countless tiny ants with glinting metal plates pouring across the "
  "desert toward a canyon", "a vast river of tiny glinting metal-plated ants across the desert",
  init=B + "B22_ant_river.png", strength=0.5, set="canyon", must_not=["water or a real river"])
r("R22_ant_hero", "zimage", False,
  p(D, "Macro low shot.", C["ant"] + ", marching toward camera at the head of a column of thousands of identical "
    "metal-plated ants, the sun catching the steel plate, determined little face, golden sand."),
  "the lead ant marches toward camera with the column behind it, legs stepping, steel plate glinting, antennae "
  "bobbing; camera tracks backward low", "a tiny red ant wearing a metal plate on its back marching at the head "
  "of a column of ants", "a tiny red ant wearing a metal plate at the front of a column of ants",
  identity=["ant"], init=None)

# ---------------- 7 THE RAMP ----------------
r("R23_ant_bridge", "blender", True,
  p(D, "Wide shot of the canyon gap.", "Millions of tiny metal-plated ants linking legs into a living bridge that "
    "spans the gap from rim to rim right under the ends of the rails, glinting in the sun, a deep canyon below.",
    S["canyon"] + "."),
  "the living bridge of ants ripples and tightens across the gap as more ants pour on and lock together, "
  "glinting; camera pushes in toward the bridge",
  "a living bridge made of countless tiny metal-plated ants spanning a canyon gap under the ends of the rails",
  "a bridge of countless tiny ants spanning a canyon gap", init=B + "B24_ant_bridge.png", strength=0.5,
  set="canyon", must_not=["a wooden or steel bridge", "the gap empty"])
r("R24_giraffes_spot", "zimage", False,
  p(D, "Low angle shot.", C["giraffe"] + ", standing at the canyon rim with their long necks craned far out over "
    "the gap, peering down to guide, one nodding.", S["canyon"] + "."),
  "the two giraffes stretch their long necks out over the gap and peer down, one nods; camera tilts up their "
  "necks", "two giraffes standing at a canyon rim with their long necks stretched out over the gap",
  "two giraffes at a canyon rim with long necks over the gap", identity=["giraffe"], set="canyon")
r("R25_elephant_trumpet", "zimage", False,
  p(D, "Low angle medium shot.", C["elephant"] + ", rearing its head back and raising its own long trunk high in the "
    "air, mouth open bellowing a mighty call through the trunk, ears flared wide, a spray of water from the trunk "
    "tip sparkling. No musical instrument, no horn, nothing held.", S["canyon"] + "."),
  "the elephant raises its trunk high and trumpets, ears flaring, water spraying from the trunk; camera low "
  "and pushing in", "an elephant with its own trunk raised high, bellowing, at a canyon rim, no instrument",
  "an elephant with its trunk raised at a canyon rim", identity=["elephant"], set="canyon")
r("R26_whistle", "blender", False,
  p(SD, "Close shot against the turquoise sky.", "The brass steam whistle on top of a red-and-gold circus "
    "locomotive's boiler shrieking, a violent jet of white steam blasting up from it, the tall black smokestack "
    "behind."),
  "the brass whistle shrieks and blasts a violent jet of white steam upward, the boiler shuddering; camera "
  "holds tight", "a brass steam whistle on a locomotive blasting a jet of white steam",
  "a brass locomotive whistle with white steam", init=B + "B27_whistle.png", strength=0.5, set="train")
r("R27_monkey_eyes", "zimage", False,
  p(D, "Medium close shot inside the cab of a red-and-gold circus steam locomotive.", C["monkey"] + ", covering "
    "his eyes with both little hands, mouth in a wobbly grimace, cap askew, the desert rushing past the cab "
    "window behind him."),
  "the monkey conductor clamps both hands over his eyes and shakes, cap wobbling, the cab rattling, desert "
  "streaking past the window; camera shakes with the cab",
  "a small monkey conductor in a cap covering his eyes with both hands inside a locomotive cab",
  "a monkey conductor in a cap with hands over his eyes in a locomotive cab", identity=["monkey"], set="train")
r("R28_bridge_link", "zimage", False,
  p(D, "Macro shot.", "Dozens of tiny red ants with dented steel plates on their backs gripping each other's legs "
    "and locking together into a woven chain over a deep red-rock canyon drop, more ants climbing on, the steel "
    "plates forming a glinting road surface."),
  "the ants grip and lock legs, climbing over each other to close the chain, plates sliding into place and "
  "glinting; camera pushes in", "tiny metal-plated ants gripping each other's legs to form a chain over a canyon",
  "tiny metal-plated ants linked together over a canyon drop", identity=["ant"])
r("R29_doug_tense", "composite", False,
  p(D, "Close shot at the canyon rim.", C["doug"] + ", ears perked straight up, wide eyes fixed on something "
    "rushing toward him off-screen, wrinkled brow tense, holding his breath, mouth closed.", S["canyon"] + "."),
  "the bloodhound holds his breath, eyes widening as he tracks the oncoming train, ears lifting, brow tense, "
  "mouth closed; fast push in on his face",
  "a bloodhound at a canyon rim with ears up and wide tense eyes", "a tense bloodhound with wide eyes at a canyon "
  "rim", identity=["doug"], set="canyon", must_not=["the dog smiling", "the dog's mouth open talking"])
r("R30_wheels_edge", "blender", True,
  p(SD, "Low side close shot.", "The front wheels of a red-and-gold circus steam locomotive rolling onto the last "
    "wooden ties at the very edge of the canyon rim, the rail ending just ahead, the deep canyon void below, "
    "sparks at the wheels."),
  "the locomotive's front wheels roll forward onto the last ties right at the edge, sparks spitting, pebbles "
  "falling into the void; camera low and holding",
  "locomotive wheels on the last ties at the edge of a canyon where the rail ends",
  "locomotive wheels at the edge of a canyon where the rail ends", init=B + "B31_wheels_edge.png",
  strength=0.5, set="canyon", must_not=["the train falling", "the wheels on solid ground with no gap"])

# ---------------- 10 BUTTON ----------------
r("R31_ant_salute", "zimage", True,
  p(D, "Macro shot.", C["ant"] + ", standing on a warm sandstone pebble raising one front leg to its brow in a "
    "crisp salute, looking up proudly, the dented steel plate catching the sunset, and far behind it, softly "
    "out of focus, the big droopy-eared face of a bloodhound looking down at it."),
  "the tiny ant snaps one front leg up to its brow in a salute and holds it, antennae twitching, standing proud; "
  "camera eases in", "a tiny ant with a dented metal plate saluting with one front leg raised to its head",
  "a tiny ant with a metal plate saluting", identity=["ant"])
r("R32_doug_salute", "zimage", True,
  p(D, "Medium close shot at the canyon rim at sunset.", C["doug"] + ", raising one front paw to his brow in a "
    "proud salute, a warm soft smile, looking down at something tiny on the ground, mouth closed.", S["canyon"] + "."),
  "the bloodhound raises one front paw to his brow in a salute and holds it, his face crinkling into a warm "
  "smile; camera eases in", "a bloodhound raising one front paw to his brow in a salute, smiling warmly",
  "a bloodhound with one front paw raised to his brow in a salute", identity=["doug"], set="canyon",
  must_not=["the dog sad or angry"])

# ---------------- cuts (script order) ----------------
K = []
def k(id, shot, secs, sentiment, render=None, note=None):
    K.append(dict(id=id, script_shot=shot, seconds=secs, sentiment=sentiment, render=render, note=note))
k("c01a_hunt", 1, 1.5, "intrigue, a hero with a past", "R01_night_hunt")
k("c01b_bear", 1, 1.0, "intrigue, a hero with a past", "R02_bear_hiding")
k("c01c_eyes", 1, 1.3, "intrigue, a hero with a past", "R03_eye_contact")
k("c01d_away", 1, 1.0, "intrigue, a hero with a past", "R04_doug_leads_away")
k("c01e_ditch", 1, 1.2, "intrigue, a hero with a past", "R05_lantern_ditch", "DOUG (low, V.O.): I picked a side.")
k("c02a_rails", 2, 0.8, "urgency spreading", "R06_rails_scream")
k("c02b_ears", 2, 0.9, "urgency spreading", "R07_rabbit_ears")
k("c02c_thump", 2, 0.8, "urgency spreading", "R08_rabbit_thump")
k("c02d_hawk", 2, 0.8, "urgency spreading", "R09_hawk_cry")
k("c02e_prairie", 2, 0.7, "urgency spreading", "R10_prairie_whistle")
k("c03a_burst", 3, 1.5, "joy, here comes the cavalry", "R11_wagon_burst")
k("c03b_wheel", 3, 0.9, "joy, here comes the cavalry", "R12_wheel")
k("c03c_team", 3, 1.0, "joy, here comes the cavalry", "R13_team")
k("c03d_crew", 3, 1.2, "joy, here comes the cavalry", "R14_crew_side")
k("c03e_bench", 3, 1.4, "joy, here comes the cavalry", "R15_bench")
k("c04a_train", 4, 1.5, "dread", "R16_train_desert")
k("c04b_gap", 4, 1.5, "dread", "R17_tracks_end")
k("c05a_hank", 5, 2.0, "a laugh inside the tension", "R18_hank_line", "HANK: Doug... that's a big hole.")
k("c05b_doug", 5, 2.0, "a laugh inside the tension", "R19_doug_line", "DOUG: Then we need a lot of help.")
k("c06a_ground", 6, 1.2, "wonder", "R20_ground_moves")
k("c06b_river", 6, 1.6, "wonder", "R21_ant_river")
k("c06c_hero_ant", 6, 1.2, "wonder", "R22_ant_hero")
k("c07a_bridge", 7, 1.2, "maximum tension", "R23_ant_bridge")
k("c07b_giraffes", 7, 0.8, "maximum tension", "R24_giraffes_spot")
k("c07c_trumpet", 7, 0.8, "maximum tension", "R25_elephant_trumpet")
k("c07d_whistle", 7, 0.8, "maximum tension", "R26_whistle")
k("c07e_monkey", 7, 0.8, "maximum tension", "R27_monkey_eyes")
k("c07f_link", 7, 0.8, "maximum tension", "R28_bridge_link")
k("c07g_doug", 7, 0.8, "maximum tension", "R29_doug_tense")
k("c07h_edge", 7, 1.2, "maximum tension", "R30_wheels_edge")
k("c07i_rush", 7, 0.8, "maximum tension", "R17_tracks_end")
k("c08_black", 8, 1.0, "silence", None, "SMASH TO BLACK, silence")
k("c09_title", 9, 3.0, "title slam", None, "TITLE: HANK & DOUG'S WILD RESCUE (title card, part 2)")
k("c10a_ant_salute", 10, 1.8, "warmth, a smile", "R31_ant_salute")
k("c10b_doug_salute", 10, 2.0, "warmth, a smile", "R32_doug_salute")

rd = {x["id"]: x for x in R}
for x in R:
    x["feeds_cuts"] = [c["id"] for c in K if c["render"] == x["id"]]
    x["start_still"] = f"stills/LOCKED_{x['id']}.png"
    x["res"] = "832x480"
    x["takes"] = 3 if x["hero"] else (2 if x["identity"] else 1)
shots = []
for c in K:
    s = dict(c)
    if c["render"]:
        x = rd[c["render"]]
        s.update(beat=x["beat"], clip_beat=x["clip_beat"], must_not=x["must_not"], lock=x["start_still"],
                 clip=f"clips/{c['id']}.mp4")
        if x["set"]: s["set"] = x["set"]
        if x["identity"]: s["identity"] = x["identity"]
    else:
        s.update(beat="black screen" if c["id"] == "c08_black" else "the title card HANK & DOUG'S WILD RESCUE",
                 must_not=[])
    shots.append(s)
spine = [
    {"beat": "a bloodhound is hunting a bear at night for a lantern-carrying owner", "shots": ["c01a_hunt", "c01b_bear"]},
    {"beat": "the dog looks the frightened bear in the eye and chooses the bear", "shots": ["c01c_eyes"]},
    {"beat": "the dog leads the lantern away and it ends up in a ditch", "shots": ["c01d_away", "c01e_ditch"]},
    {"beat": "a train is in trouble and the call for help jumps animal to animal", "shots": ["c02a_rails", "c02b_ears", "c02c_thump", "c02d_hawk", "c02e_prairie"]},
    {"beat": "the all-animal crew rolls out on the wooden fire-wagon pulled by horses, camels and cows", "shots": ["c03a_burst", "c03c_team", "c03d_crew"]},
    {"beat": "Hank and Doug lead the crew", "shots": ["c03e_bench"]},
    {"beat": "a circus train races toward tracks that end at a canyon gap", "shots": ["c04a_train", "c04b_gap"]},
    {"beat": "Hank and Doug size up the gap with a joke", "shots": ["c05a_hank", "c05b_doug"]},
    {"beat": "an army of metal-plated ants answers", "shots": ["c06b_river", "c06c_hero_ant"]},
    {"beat": "the ants link into a living bridge as the train reaches the edge", "shots": ["c07a_bridge", "c07f_link", "c07h_edge"]},
    {"beat": "the title", "shots": ["c09_title"]},
    {"beat": "a tiny ant salutes Doug and Doug salutes back", "shots": ["c10a_ant_salute", "c10b_doug_salute"]},
]
sets = {"forest": "canon/set_forest.png", "desert": "canon/set_desert_rails.png", "canyon": "canon/set_canyon_gap.png",
        "wagon": "canon/wagon.png", "train": "canon/train.png"}
beats = {"_note": "HANK & DOUG'S WILD RESCUE (script v3, LOCKED 2026-10-31). shots[] = the cuts in script order; "
         "each cut is pulled from a RENDER (renders.json). beat = one-frame visible state for beat_gate; clip_beat = "
         "a state ONE frame can show at any moment of the clip (no verbs of motion, LESSONS 10/31). Pull geometry: "
         "animals out in front, wagon behind (rule 26).", "spine": spine, "set_masters": sets, "shots": shots}
for x in R:
    if x["set"]: x["set"] = sets[x["set"]]
renders = {"_note": "each render = one LOCKED start still -> LTX-2.5 clip (+takes); feeds_cuts = the cuts pulled "
           "from it. source: zimage (t2i), blender (Z-Image img2img over the Blender frame at 'strength'), "
           "composite (canon cutouts welded onto a plate, then img2img; rule 24 for two-character frames).",
           "renders": R}
def dump(obj, path):
    tmp = path.with_suffix(".tmp"); json.dump(obj, open(tmp, "w"), indent=1); os.replace(tmp, path)
dump(beats, P / "beats.json"); dump(renders, P / "renders.json")

cont = {"_note": "Story-state facts for HANK & DOUG'S WILD RESCUE. continuity_check.py votes on each.", "rules": [
    {"id": "no_humans", "shots": ["*"], "question": "Is there a human being or any part of a person (hand, boot, face) in this frame?", "expect": "NO"},
    {"id": "no_text", "from": "c01a_hunt", "to": "c07i_rush", "question": "Is there any legible text, lettering or numbers anywhere in this frame?", "expect": "NO"},
    {"id": "animated_look", "shots": ["*"], "question": "Does this frame look like a 3D animated cartoon feature film (not live-action photography)?", "expect": "YES"},
    {"id": "origin_is_night", "from": "c01a_hunt", "to": "c01e_ditch", "question": "Is this a daytime scene with a bright sky?", "expect": "NO"},
    {"id": "present_is_day", "from": "c02a_rails", "to": "c07i_rush", "question": "Is this a dark night scene?", "expect": "NO"},
    {"id": "wagon_not_truck", "shots": ["c03a_burst", "c03b_wheel", "c03c_team", "c03d_crew", "c03e_bench"], "question": "Is there a truck, car, engine or rubber tire in this frame?", "expect": "NO"},
    {"id": "animals_pull", "shots": ["c03a_burst", "c03c_team"], "question": "Is the wagon in front of the animals, as if pushing them?", "expect": "NO"},
    {"id": "doug_bloodhound", "shots": ["c01a_hunt", "c01c_eyes", "c01d_away", "c03e_bench", "c05b_doug", "c07g_doug", "c10b_doug_salute"], "question": "Is the dog in this frame a bloodhound with long droopy ears and a wrinkled face?", "expect": "YES"},
    {"id": "hank_big_brown_bear", "shots": ["c01b_bear", "c01c_eyes", "c03e_bench", "c05a_hank"], "question": "Is there a big brown bear in this frame?", "expect": "YES"},
    {"id": "hank_bigger_than_doug", "shots": ["c01c_eyes", "c03e_bench"], "question": "Is the bear clearly much bigger than the dog?", "expect": "YES"},
    {"id": "rails_end", "shots": ["c04b_gap", "c07h_edge", "c07i_rush"], "question": "Do the railroad tracks visibly end at the edge of a gap or drop?", "expect": "YES"},
    {"id": "ants_metal", "shots": ["c06b_river", "c06c_hero_ant", "c07a_bridge", "c07f_link", "c10a_ant_salute"], "question": "Are there ants wearing shiny metal plates in this frame?", "expect": "YES"},
    {"id": "train_is_circus_steam", "shots": ["c02a_rails", "c04a_train", "c07d_whistle", "c07h_edge"], "question": "Is the train in this frame a modern diesel or electric train?", "expect": "NO"},
]}
dump(cont, P / "continuity.json")
print(f"beats: {len(K)} cuts, {sum(c['seconds'] for c in K):.1f}s; renders: {len(R)} "
      f"({sum(1 for x in R if x['hero'])} hero); takes if all used: {sum(x['takes'] for x in R)}")
