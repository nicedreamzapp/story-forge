# The Little Robot Who Built Himself
*A Story Forge film — overnight build 2026-06-11, approved by Matt ("run") at 3:14am.*

## Meaning
You're not broken, you're unfinished. Sprocket builds himself — but he's only
finished when someone else adds a piece. Self-made isn't the whole story.

## Style (every Flux prompt ends with this block)
STYLE: "Pixar-style 3D animated film still, cinematic volumetric lighting,
shallow depth of field, rich warm color grading, highly detailed, soft
subsurface scattering, 35mm film look"

## Characters (fixed description blocks — paste verbatim into every prompt)
SPROCKET: "a small endearing vintage robot assembled from mismatched
clip-together parts: rounded cream-white tin chest with visible copper
clip-latches, one slender silver arm and one chunky orange toy-excavator arm,
a single brass wagon wheel for a left leg and a blue spring piston for the
right leg, oversized round head with two circular glass eyes, the left eye
glowing warm blue brighter than the right, a small bent antenna on top"

JUNE: "a 9-year-old girl with curly dark brown hair, light brown skin,
freckles, denim overalls over a yellow t-shirt, a red bandana tied around
her neck"

WORLD: "a cluttered small-town maker's workshop, pegboard walls of hand
tools, mason jars full of screws, warm tungsten work lamps, sawdust in the
air" — out back: a dented metal recall bin stenciled FAILED INSPECTION.

## Emotional rules (from memory, non-negotiable)
- Sprocket is EAGER, never worried. Draw the emotion INTO the still (i2v
  can't change pose/expression). Eager = antenna perked, eye bright, head up.
- Emotion via body/action/VO, never talking faces. Nobody's mouth speaks.
- Narrator VO carries the story (storybook fable voice).

## Five movements
1. THE BIN — night. One eye flickers on in the failed-inspection bin. He reaches.
2. THE BUILD — montage. Wrong a dozen ways, falls, re-clips, more himself each try.
3. JUNE — she fights the old bike all summer for the county race. He secretly
   fixes pieces at night; she thinks it's her dad.
4. THE STORM — night before the race the workshop floods, drivetrain wrecked.
   He unclips his own parts and gives them to the bike. Morning: bike perfect,
   Sprocket in pieces beside it.
5. THE REBUILD — June understands, rebuilds him on the workbench with leftover
   bike parts (red reflector becomes his right eye's new lens, the bike bell
   clips to his chest). Sunrise ride-out together.
   Final line: "Nothing in that workshop was ever broken. It just wasn't
   finished yet."

## Render plan
- Stills: Flux Dev FP8 local (~36s ea), 768x512-friendly compositions.
- Motion: make-ltx-lightricks multi-scale i2v @ 768x512 (NEVER higher), ~44 shots.
- Quiet beats: bin/ken_burns.py glides (~16 shots). NO zoompan, NO jitter.
- Score: ACE-Step via Song Forge :8767, 4 instrumental cues, copied here then
  deleted from Matt's library.
- Narration: Piper, one sentence per file, concat w/ silence, adelay+amix sync.
- Crash safety: one model phase at a time, per-shot subprocess, resume manifest,
  caffeinate running, disk checked (777GB free).
