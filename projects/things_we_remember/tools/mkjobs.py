import json, os
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILM = ("35mm film still from a quiet supernatural horror movie, warm faded Kodak color, fine film grain, soft halation, "
        "shallow depth of field, photorealistic, natural skin texture, no text, no letters, no words, no captions, no watermark")
HOUSE = "an old 1970s family farmhouse kitchen, worn wooden cabinets, lace curtains, family photos on the walls"
CLAIRE = "a woman in her late thirties with shoulder-length wavy chestnut-brown hair and a pale freckled face, faded blue knit cardigan over a cream blouse"
RUTH = "an old woman in her mid seventies with short curled silver-white hair, thin wire glasses, a lavender knit cardigan"
LILY = "a seven-year-old girl with straight blonde hair in two braids, a pale yellow dress"
MAN = "a gentle-faced man in his fifties with neatly combed dark hair, an old-fashioned charcoal gray wool suit, white shirt buttoned at the collar, no tie"
J = [
 ("s01_a", 101, f"{HOUSE}, empty and still, late afternoon golden sun streams low through the window above the sink from camera right, dust motes floating in the beam, the first raindrops beading on the glass, a dark wall on the camera side for negative fill, warm and nostalgic"),
 ("s01_b", 102, f"{HOUSE}, wide view toward the window over the sink, low warm sun from the window making a soft beam full of dust, raindrops starting on the glass, a teacup on the counter, deep shadow in the near corner"),
 ("s02", 201, f"a narrow farmhouse hallway wall densely covered with dozens of old framed family photographs of different eras, color and black and white, a small brass table lamp on the right glowing warm and lighting the frames, soft pool of light, shadowy far end of the hall"),
 ("s03", 301, f"extreme close-up of a woman's hands holding a faded 1970s square color snapshot photograph: a young smiling couple stands in a sunny garden, and slightly behind them, half in the shade of a tree, stands {MAN}, his face soft and unclear. warm lamp light from the left over the photo, dark background"),
 ("s04_a", 401, f"medium close shot of {RUTH} sitting at a kitchen table holding an old photograph in both hands, looking down at it, soft overcast window light from camera left as the key, camera on her shadow side, a dim lamp behind her, rain on the window, her lips gently closed, sad knowing expression"),
 ("s04_b", 402, f"close shot of {RUTH} at a kitchen table, an old photograph in her hands, eyes lowered to the photo, gray rainy window light from the left, deep shadow on the right side of her face, a soft warm practical lamp glowing behind her, lips closed"),
 ("s05_a", 501, f"dusk inside {HOUSE}, a woman's hand at the sink letting a clear drinking glass slip, the glass in midair falling, and in the dark open doorway behind her in the background, the silhouette of a man standing perfectly still in shadow, barely visible, cold blue dusk light through the window, a single warm lamp"),
 ("s05_b", 502, f"medium wide shot in a dim farmhouse kitchen at dusk, {CLAIRE} at the sink seen from the side, a clear glass slipping from her fingers, behind her an open doorway into a pitch dark hallway where a tall man's silhouette stands motionless, faint, cold window light from the right, deep shadows"),
 ("s06_a", 601, f"close shot of an empty wooden dining chair at the end of a family dinner table, in front of it a full plate of roast dinner with a fork resting on the plate, glasses of milk, the blurred arms of family members at the edges of the frame, warm low pendant lamp above, the chair back in deep shadow, unsettling stillness"),
 ("s06_b", 602, f"a family dinner table set with five plates in a warm farmhouse dining room at night, four people seated eating, blurred, and one empty wooden chair at the near end of the table in sharp focus with an untouched full plate and a fork, a warm hanging lamp, rain on the dark window"),
 ("s07_a", 701, f"medium close shot of {LILY} sitting at a dinner table at night, turning her head to look calmly toward an empty chair just off frame on the right, serious unblinking expression, warm hanging lamp above as the key from the right, shadowy dining room behind, lips gently closed, face fully visible and well lit"),
 ("s07_b", 702, f"close shot of {LILY} at a family dinner table, looking to the side at an empty chair beside her, calm serious face, warm pendant lamp key light, dark room behind, lips closed, face fully visible"),
 ("s08_a", 801, f"a dark child's bedroom at night, pale blue moonlight through window blinds casting stripes, two small single beds side by side, in the near bed a small boy lies under a quilt facing the wall, only his messy brown hair visible, in the far bed a little blonde girl sleeps, a dim star nightlight, deep shadows, eerie stillness"),
 ("s08_b", 802, f"close view of a small single bed in a dark child's bedroom, a little boy curled under a patchwork quilt facing the wall, only the back of his messy brown hair showing, cold moonlight stripes across the quilt from blinds, a nightlight glow, another bed blurred in the background"),
 ("s11_a", 1101, f"night, {CLAIRE} seen from behind standing at the kitchen sink facing a black window, her reflection in the glass, and in the window reflection, softly out of focus, {MAN} standing right behind her shoulder, kind gentle smile, a single dim warm lamp on the left, the rest of the kitchen in darkness"),
 ("s11_b", 1102, f"over-the-shoulder shot from behind {CLAIRE} at a dark kitchen window at night, the glass reflects her face and, just behind her in the reflection, the blurred face of a gentle smiling man in a gray suit, nobody behind her in the room, one warm lamp, deep darkness"),
]
ERAS = [
 ("s09_1", "a 1990s glossy color snapshot of a family birthday party in a backyard, kids with cake"),
 ("s09_2", "a 1980s faded color photograph of a family picnic by a lake"),
 ("s09_3", "a 1970s square color snapshot of a young couple's wedding outside a small church"),
 ("s09_4", "a 1960s Kodachrome color photo of a family christmas morning in a living room"),
 ("s09_5", "a 1950s black and white photograph of a family standing in front of a farmhouse"),
 ("s09_6", "a 1930s black and white photograph of a farming family beside a truck"),
 ("s09_7", "a 1910s sepia photograph of a stiff formal family portrait in a parlor"),
 ("s09_8", "an 1880s scratched tintype photograph of a pioneer family in front of a log cabin"),
]
for i, (n, d) in enumerate(ERAS):
    J.append((n, 900 + i, f"{d}, and standing slightly apart behind the group, the same man every time: {MAN}, looking straight at the camera with a soft gentle smile, unchanged and unaged, an authentic vintage photograph with period-correct grain, wear and color"))
jobs = []
for n, s, p in J:
    tail = FILM if not n.startswith("s09") else "photorealistic authentic old photograph, no text, no watermark"
    jobs.append({"out": f"{P}/stills/{n}.png", "prompt": p + ". " + tail, "w": 1344, "h": 768, "seed": s})
json.dump(jobs, open(f"{P}/stills_jobs.json", "w"), indent=1)
print(len(jobs))
