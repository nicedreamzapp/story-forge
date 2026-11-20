"""Short stills: 16 new shots x 2 seeds, same look strings as the teaser/trailer."""
import json, os
P = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILM = ("35mm film still from a quiet supernatural horror movie, warm faded Kodak color, fine film grain, soft halation, "
        "shallow depth of field, photorealistic, natural skin texture, no text, no letters, no words, no captions, no watermark")
CLAIRE = "a woman in her late thirties with shoulder-length wavy chestnut-brown hair and a pale freckled face, faded blue knit cardigan over a cream blouse"
RUTH = "an old woman in her mid seventies with short curled silver-white hair, thin wire glasses, a lavender knit cardigan"
LILY = "a seven-year-old girl with straight blonde hair in two braids, a pale yellow dress"
TOM = "a man in his early forties with short sandy-brown hair and a short trimmed beard, a faded gray henley shirt"
DIN = "a warm farmhouse dining room at night, one warm hanging lamp over the table, rain on the dark window"
MORN = "a sunny farmhouse kitchen on a spring morning, soft golden sunlight through the window over the sink, white blossoms on a tree outside"
J = [
 ("sh06", 3101, f"{CLAIRE} in a narrow hallway lined with framed family photographs, lifting an old framed photo off the wall with both hands and looking at it with a curious small smile, a warm brass table lamp lighting her from the right"),
 ("sh07", 3201, "extreme close-up of an old woman's wrinkled hands with a thin gold wedding ring taking a faded 1970s square snapshot photograph from a younger woman's hands, warm lamp light, dark background, shallow focus on the hands"),
 ("sh10", 3301, f"close-up of {CLAIRE} in a dim hallway, her small smile fading into confusion, eyes searching, warm lamp light from the right, deep shadow on the left side of her face, lips closed"),
 ("sh11", 3401, "an old wooden dresser drawer seen from above, a faded square photograph lying face down inside on top of folded linens, warm lamp light, the drawer half open, dark room"),
 ("sh12", 3451, f"dusk inside an old 1970s farmhouse kitchen, {CLAIRE} at the sink rinsing a clear drinking glass, lost in thought, cold blue dusk light through the window, a single warm lamp, the dark open doorway to the hall behind her"),
 ("sh13b", 3551, f"medium shot of {LILY} at the family dinner table happily eating and swinging her legs, {DIN}, warm lamp light, her face fully visible, lips closed"),
 ("sh22", 3951, f"{CLAIRE} climbing a dark wooden farmhouse staircase at night in her nightgown and cardigan, seen from below, one hand on the rail, cold moonlight from a window at the top, a faint nightlight glow from a child's door upstairs"),
 ("sh13", 3501, f"wide shot of a family dinner in {DIN}: {TOM}, {CLAIRE}, {LILY} and {RUTH} sit around a wooden table, and the table is set with five plates, one place at the near end has an empty chair, warm and cozy, steam from the food"),
 ("sh14", 3601, f"close shot of a man's hands setting a white dinner plate down on the table in front of an empty wooden chair, {DIN}, the family blurred in the background"),
 ("sh15", 3701, f"medium close shot of {TOM} sitting at the dinner table chewing, relaxed and easy, {DIN}, warm lamp light from above, lips closed, face fully visible"),
 ("sh18", 3801, f"medium close shot of {RUTH} at the dinner table, slowly lowering her fork to her plate and closing her eyes, sad, {DIN}, warm lamp light from above"),
 ("sh21", 3901, f"close-up of {CLAIRE} at the dinner table staring at something just off camera to the left, frozen, not breathing, wide still eyes, {DIN}, the warm lamp light from above, lips closed"),
 ("sh29", 4001, f"{MORN}, the kitchen empty and peaceful, dust in the light, a vase of fresh flowers on the table"),
 ("sh30", 4101, f"{LILY} sitting at a kitchen table drawing with crayons on white paper, happy and focused, crayons scattered around, {MORN}"),
 ("sh31", 4201, f"over-the-shoulder shot from behind {CLAIRE} holding a coffee mug, looking down and smiling at {LILY} who is drawing with crayons at the kitchen table, {MORN}"),
 ("sh32", 4301, f"close shot of {LILY} at a kitchen table with crayons, looking calmly up at someone standing beside her, face fully visible in soft morning light, lips gently closed, serious calm face, {MORN}"),
 ("sh33", 4401, "a child's crayon drawing on white paper lying on a kitchen table: a smiling woman with long brown wavy hair and a blue sweater holding hands with a small smiling boy with messy brown hair, a yellow sun and a house, simple childlike wax crayon strokes, seen from directly above, crayons beside it, morning light"),
 ("sh34", 4501, f"close-up of {CLAIRE} in a sunny kitchen looking down at something in her hands, her eyes filling with tears, recognition dawning, soft morning window light from the right, lips closed"),
 ("sh38", 4601, f"a kitchen window glass seen from inside on a bright morning, reflecting {CLAIRE} and {LILY} at the table behind the camera, and standing behind them in the reflection, softly out of focus, a man in an old charcoal gray suit, his face blurred and in shadow, white blossoms outside the glass"),
]
jobs = []
for n, s, p in J:
    for k, sd in (("a", s), ("b", s + 50)):
        jobs.append({"out": f"{P}/stills/{n}_{k}.png", "prompt": p + ". " + FILM, "w": 1344, "h": 768, "seed": sd})
json.dump(jobs, open(f"{P}/stills_jobs_short.json", "w"), indent=1); print(len(jobs))
