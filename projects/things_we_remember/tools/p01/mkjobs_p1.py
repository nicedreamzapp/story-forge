"""Part 1 stills (PART_01.md): 38 setups x 2 seeds, same look strings as every prior cut."""
import json, os
P = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILM = ("35mm film still from a quiet supernatural horror movie, warm faded Kodak color, fine film grain, soft halation, "
        "shallow depth of field, photorealistic, natural skin texture, no text, no letters, no words, no captions, no watermark")
C = "a woman in her late thirties with shoulder-length wavy chestnut-brown hair and a pale freckled face, faded blue knit cardigan over a cream blouse"
R = "an old woman in her mid seventies with short curled silver-white hair, thin wire glasses, a lavender knit cardigan"
L = "a seven-year-old girl with straight blonde hair in two braids, a pale yellow dress"
T = "a man in his early forties with short sandy-brown hair and a short trimmed beard, a faded gray henley shirt"
HOUSE = "an old 1970s family farmhouse"
CAR = "inside an old wood-paneled 1990s station wagon on a rainy day, gray daylight through rain-streaked windows"
NIGHT = "night, rain on the dark windows, one warm lamp, deep shadows"
J = [
 ("p03", "close-up of an old farmhouse kitchen window pane, the first raindrops beading and starting to run down the glass, low golden sun fading behind clouds outside, lace curtain edge, warm and melancholy"),
 ("p04", "a wood-paneled 1990s station wagon driving along a narrow country road under tall green trees in steady rain, headlights on, wet asphalt, seen from the roadside, overcast"),
 ("p05", f"{CAR}, {L} sitting in the back seat holding a small old wooden music box to her chest, her face near the window, watching the rain, calm"),
 ("p06", "extreme close-up of an open antique wooden music box in a little girl's hands, a tiny ballerina figure on the spinning mirror, brass comb and cylinder visible, soft gray window light, shallow focus"),
 ("p07", f"{CAR}, close-up of the rear-view mirror showing the tired kind eyes of {C} looking back toward the back seat, the road ahead blurred through the wet windshield"),
 ("p08", f"{CAR}, {T} asleep in the passenger seat with his head against the rainy window, peaceful, wipers on the windshield"),
 ("p10", f"{HOUSE} front porch on a rainy afternoon, {R} standing in the open doorway holding the screen door open, small and waiting, warm light from the hall behind her"),
 ("p11", f"{HOUSE} front porch on a rainy afternoon, {L} hugging {R} tightly on the porch steps, the old woman bending down with her eyes closed and smiling, rain falling behind them"),
 ("p12", f"{C} standing at the bottom of the porch steps of {HOUSE} in light rain, holding a cardboard moving box on her hip, looking up at the house with a long breath, seen from the side"),
 ("p13", f"close shot of {C} on a covered farmhouse porch, looking at someone just off camera with a careful tender smile, soft gray daylight, rain behind her, lips closed, face fully visible"),
 ("p14", f"extreme close-up of an old woman's wrinkled hand gently touching the freckled cheek of {C}, soft gray daylight, shallow focus, tender"),
 ("p16", f"{T} carrying a stack of cardboard moving boxes through a narrow farmhouse hallway lined with framed family photographs, his shirt damp from the rain, warm lamp light"),
 ("p18", f"{L} standing in a narrow farmhouse hallway, looking up at a wall densely covered with old framed family photographs, seen from behind and a little to the side, warm lamp light"),
 ("p20", f"an old farmhouse kitchen in the afternoon, {C} unwrapping dishes from newspaper at the counter, {R} sitting at the kitchen table watching her, moving boxes everywhere, soft window light"),
 ("p21", f"{T} crouching beside an old brass floor lamp in a farmhouse living room full of moving boxes, the lamp bulb just flickering on, warm glow on his face"),
 ("p22", "an empty upstairs landing in an old farmhouse in the afternoon, a narrow hallway with three closed doors and one open door, dust in a beam of window light, quiet"),
 ("p24", f"{L} sitting on a small old blue-painted wooden child's chair in an attic bedroom among moving boxes, her knees up high because the chair is too small, looking up at someone, face fully visible, lips closed, afternoon light"),
 ("p25", "extreme close-up of the back of an old blue-painted wooden child's chair, letters of a child's name scratched out deeply with a knife so they can't be read, worn paint, dust, side light"),
 ("p27", f"looking down a steep wooden farmhouse staircase from the top, {R} standing at the bottom of the stairs looking up, small and silent, warm hall light below"),
 ("p28", f"{T} hanging coats on an old wooden coat rack beside a farmhouse front door, raincoats and umbrellas, rain on the door glass, afternoon light"),
 ("p29", "close-up of an old wooden coat rack board on a farmhouse wall: four brass hooks at adult height and one small brass hook mounted much lower at a small child's height, empty, side light"),
 ("p30", f"close shot of a man's hands hanging a small pale yellow child's raincoat on a low brass hook near the floor, on an old wooden coat rack, warm hall light"),
 ("p31", f"{L} placing a small antique wooden music box on a white bookshelf in a child's bedroom, afternoon light, toys and moving boxes"),
 ("p32", "a child's bedroom wall with faded old floral wallpaper, and on it a clean bright rectangle the size of a small bed where the wallpaper was protected from the sun for years, a single bed beside it, afternoon light"),
 ("p33", f"{C} making a child's bed with a pale yellow quilt, pausing and looking at the wall beside it, puzzled, faded floral wallpaper, afternoon light"),
 ("p34", f"an old farmhouse kitchen at dusk, {C} and {T} sitting on moving boxes eating takeout from cartons with chopsticks and laughing quietly, warm lamp, blue dusk window"),
 ("p35", f"medium close shot of {T} sitting on a moving box in a farmhouse kitchen at dusk holding a takeout carton, looking at someone off camera with a tired happy smile, face fully visible, warm lamp, lips closed"),
 ("p36", f"close shot of {C} in a farmhouse kitchen at dusk, laughing, then her eyes drifting to something across the room, warm lamp light"),
 ("p37", f"{R} setting woven place mats on an old wooden kitchen table at dusk, carefully placing them one by one, counting under her breath, warm lamp light"),
 ("p38", "an old wooden kitchen table seen from above at dusk, five woven place mats set around it, warm lamp light, empty chairs"),
 ("p40", f"{NIGHT}, {C} carrying two cups of tea into a dark farmhouse living room, steam rising, lamp light on her face"),
 ("p42", f"{NIGHT}, close-up of {C} in a dark living room, worried, watching someone across the room, warm lamp light from the side, lips closed"),
 ("p43", f"{NIGHT}, the reflection of {R}'s face in a dark rainy window pane, her eyes far away, rain running down the glass over the reflection"),
 ("p45", f"{NIGHT}, close shot of {R} standing at a dark window, turning to look at someone with an empty lost expression, warm lamp light on her face, rain on the glass behind her, lips closed"),
 ("p46", f"{NIGHT}, close-up of {C}'s face in a dark farmhouse living room, eyes glistening, losing her mother, lamp light from the side, lips closed"),
 ("p47", f"{NIGHT}, a dark farmhouse front hall, the old wooden coat rack beside the door, a pale yellow child's raincoat hanging on a low hook, moonlight through the door glass"),
 ("p48", "night, close shot of an old wooden coat rack in a dark front hall: on the low child's hook a pale yellow girl's raincoat, and beside it on the same low hook a small dark blue boy's raincoat, soaking wet and dripping water onto the floor, cold moonlight, eerie"),
 ("p49", "night, extreme close-up of old wooden floorboards in a dark hallway, a small puddle of rainwater with one drop hitting it, a ripple, cold moonlight glint"),
]
J += [
 ("pa1", f"{HOUSE} seen from the country road through falling rain, wide, alone among tall dark trees, one warm window, overcast afternoon"),
 ("pa2", f"{CAR}, {T} waking up in the passenger seat and stretching, smiling out the windshield at an old farmhouse, rain on the glass"),
 ("pa3", f"{C} stepping into the front hall of {HOUSE}, touching the old faded floral wallpaper with her fingertips, eyes half closed, breathing in, warm lamp light"),
 ("pa4", f"{L} twirling with her arms out in a child's bedroom with faded floral wallpaper and moving boxes, happy, afternoon light"),
 ("pa5", f"close shot of {R} handing a teacup to {C} in an old farmhouse kitchen, their hands touching on the cup, soft afternoon light"),
 ("pa6", f"{R} and {L} sitting on an old floral couch playing a hand-clapping game, both laughing, lamp light, moving boxes behind them"),
 ("pa7", f"{C} opening an old hall closet full of old coats, and at the back hangs one very small child's coat, she pauses, warm hall light"),
 ("pa8", f"{L} wearing a pale yellow raincoat and rubber boots stomping in puddles in a farmhouse garden in the rain, laughing, gray afternoon"),
 ("pa9", f"{R} standing at an old stove stirring a pot, humming, eyes soft and far away, warm kitchen light, steam"),
 ("pa10", f"{L} sitting at an old kitchen table drawing with crayons on white paper, focused, warm lamp light, dusk window"),
 ("pa11", "a child's crayon drawing on white paper on a kitchen table, seen from above: four simple stick figures, a tall man, a woman with brown hair, a little blonde girl and an old woman, standing in front of a house, wax crayon strokes"),
 ("pa12", f"{L} at the kitchen table giggling with a crayon in her hand, looking up at someone off camera, warm lamp light, lips closed"),
 ("pa13", f"close-up of {C}'s hands holding an old plastic weekly pill organizer, each day labeled with a strip of tape in neat handwriting, kitchen counter, warm light"),
 ("pa14", f"{R} sitting on an old floral couch turning the pages of a thick old family photo album on her lap, smiling softly, lamp light"),
 ("pa15", "close-up of an open old photo album page with small faded color birthday party snapshots under plastic, and one photo torn out leaving only a small triangle corner, lamp light"),
 ("pa16", f"{NIGHT}, a farmhouse bedroom, {T} asleep, and {C} lying awake beside him on her back, eyes open, listening to the rain"),
 ("pa17", f"{NIGHT}, a small old farmhouse bathroom, {C} looking at herself in the mirror, tired, the mirror glass slowly fogging at the edges, one bulb above"),
 ("pa18", f"{NIGHT}, {C} standing in a child's bedroom doorway looking in at {L} asleep in her bed, soft moonlight, a star nightlight"),
 ("pa19", "night, an antique wooden music box on a white bookshelf in a child's bedroom, lit by cold moonlight through the blinds, closed, still"),
 ("pa20", "night, a dark farmhouse upstairs hallway seen from a bedroom doorway, empty, cold moonlight from a window at the far end, closed doors, nobody there"),
 ("pa21", f"night, {C} going down a dark wooden farmhouse staircase, one hand on the rail, seen from below, moonlight"),
 ("pa22", "night, the inside of an old farmhouse front door with a window of rippled glass, rain running down it, cold moonlight, a dark coat rack beside it"),
]
jobs = []
for i, (n, p) in enumerate(J):
    for k, sd in (("a", 5000 + 10 * i), ("b", 5005 + 10 * i)):
        jobs.append({"out": f"{P}/stills/{n}_{k}.png", "prompt": p + ". " + FILM, "w": 1344, "h": 768, "seed": sd})
json.dump(jobs, open(f"{P}/stills_jobs_p01.json", "w"), indent=1); print(len(jobs))
