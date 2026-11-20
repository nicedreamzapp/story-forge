"""Trailer stills (12 new shots, 2 seeds each, same look strings as the teaser's mkjobs.py)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILM = ("35mm film still from a quiet supernatural horror movie, warm faded Kodak color, fine film grain, soft halation, "
        "shallow depth of field, photorealistic, natural skin texture, no text, no letters, no words, no captions, no watermark")
CLAIRE = "a woman in her late thirties with shoulder-length wavy chestnut-brown hair and a pale freckled face, faded blue knit cardigan over a cream blouse"
RUTH = "an old woman in her mid seventies with short curled silver-white hair, thin wire glasses, a lavender knit cardigan"
LILY = "a seven-year-old girl with straight blonde hair in two braids, a pale yellow dress"
TOM = "a man in his early forties with short sandy-brown hair and a short trimmed beard, a faded gray henley shirt"
MANS = "the dark soft silhouette of a man in an old-fashioned suit, his face completely lost in shadow and out of focus"
J = [
 ("t01", 1201, "a wood-paneled 1990s station wagon pulling slowly up a wet gravel driveway toward an old white two-story farmhouse in soft gray rain, overcast late afternoon, warm lamp light glowing in one downstairs window, wet green lawn, tall old trees, seen from the porch side"),
 ("t03", 1301, f"a narrow wooden farmhouse staircase seen from the bottom step, {LILY} running up the stairs away from camera halfway up, warm afternoon light from a landing window at the top, the upper hallway beyond the landing in shadow, family photos on the stair wall"),
 ("t04", 1401, f"{RUTH} seen from behind, standing alone at a rain-streaked living room window, gray afternoon daylight on her silver hair, a lace curtain, the room around her dim and quiet, a dark armchair in the foreground"),
 ("t07", 1701, "a small old wooden child's chair painted faded blue standing alone in the corner of an attic bedroom among moving boxes, dusty, low afternoon sunlight from a side window, and on the wall above it a second small brass coat hook at a child's height, eerie stillness"),
 ("t10", 1801, f"a dark child's bedroom at night, pale blue moonlight through window blinds casting stripes, a woman's hand gripping the edge of a patchwork quilt on a small single bed, the quilt shaped as if a small child lies under it facing the wall, a dim star nightlight, deep shadows"),
 ("t10e", 1802, "a dark child's bedroom at night, pale blue moonlight through window blinds casting stripes, a small single bed with its patchwork quilt thrown back, the bed completely empty, a small dent in the pillow, a dim star nightlight, deep shadows, eerie stillness"),
 ("t11", 1901, f"close shot of {LILY} lying in bed at night under a quilt, wide awake, her eyes open looking calmly up toward someone standing over her, face clearly visible in soft cold moonlight, a faint warm nightlight glow, dark room, lips gently closed, serious face"),
 ("t12", 2001, "close-up of an old 1980s silver portable cassette tape recorder on a wooden kitchen table at night, the clear cassette window showing the two white tape reels, a warm lamp from the left, dark room behind, rain on a dark window"),
 ("t13", 2101, f"{CLAIRE} sitting alone at a wooden kitchen table at night, staring down at an old silver cassette recorder in front of her, frozen still, one warm hanging lamp above, the rest of the kitchen in darkness, rain on the black window behind her"),
 ("t14", 2201, "1990s home video camcorder footage of a three-year-old little girl with blonde hair in two short pigtails and a white sundress standing in a sunny backyard garden facing the camera, looking curiously just past the camera, her face clearly visible, lips closed, summer afternoon, flowers and a wooden fence, soft washed-out VHS colors"),
 ("t15", 2301, "1990s home video camcorder footage of a wide sunny backyard garden, an old wooden swing hanging from a big tree, a wooden fence, flower beds and a green lawn, completely empty, nobody there, summer afternoon, soft washed-out VHS colors"),
 ("t17", 2401, f"a dark farmhouse upstairs hallway at night, a child's bedroom door slightly ajar with a faint warm nightlight glow, and standing perfectly still beside the door, {MANS}, cold moonlight from a window at the end of the hall, deep shadows"),
 ("t18", 2501, f"{TOM} standing in a dark child's bedroom at night beside a small neatly made single bed with a pale yellow quilt, looking down at it with a puzzled frown, cold moonlight stripes from window blinds, a dim nightlight, his face lit softly from the side"),
 ("t20", 2601, f"a family dinner table at night with plates set and empty chairs, at the far end of the table {MANS} sits perfectly still in a chair, one warm hanging lamp over the near end of the table, the far end in darkness"),
]
jobs = []
for n, s, p in J:
    tail = FILM if n not in ("t14", "t15") else "authentic 1990s camcorder home video still, soft focus, washed out colors, photorealistic, no text, no timestamp, no watermark"
    for k, sd in (("a", s), ("b", s + 50)):
        jobs.append({"out": f"{P}/stills/{n}_{k}.png", "prompt": p + ". " + tail, "w": 1344, "h": 768, "seed": sd})
json.dump(jobs, open(f"{P}/stills_jobs_trailer.json", "w"), indent=1)
print(len(jobs))
