# Story Forge — Film Bible Spec

**The foundation every film locks before a single frame is produced.**

This is OUR pre-production system, in OUR language. It gives us the discipline a real
studio gets from model sheets, color keys, and style guides — without adopting anyone
else's software, file formats, or rules. One `*.bible.sf` file per film. Write it, lock
it, and the pipeline enforces it on every scene.

## Why this exists (the principle)

You think everything through **up front**, or you suffer in production fixing drift.
A character with no written color key gets a different chest marking every shot. A
character with no ban-list grows a second pair of ears. We pay that cost once, here, in
a file — not a thousand times, later, in finished shots.

Reusable forever: the next film is just a new bible. Same format, same phase gates, same
consistency engine.

## Cartoons are the proving ground, not the limit

This format is **style-agnostic on purpose**. Hank & Doug is our first build because
talking cartoon characters are the *hardest* consistency case — if we can lock a
four-legged bloodhound across poses, a realistic human is easier. The exact same bible
produces **normal, realistic, live-action-looking films.** Nothing here assumes cartoons.

A realistic character is just another `character` block:

| Field | Cartoon (Doug) | Realistic film (a human lead) |
|-------|----------------|-------------------------------|
| `design` | "red-brown bloodhound, floppy ears" | "late-30s man, weathered face, short beard" |
| `palette` | coat / belly / nose colors | skin tone / hair / eye color / signature wardrobe |
| `features` | "exactly two floppy ears" | "scar over left brow, green eyes" |
| `never` | "extra ears, collar" | "no glasses, no tattoos, no age drift" |
| `scale` | Hank = 2.6× Doug | real-world heights (e.g. 1.0 / 0.94) |
| `plate` | locked model-sheet render | a locked reference still of the actor/look |
| `lora` | cartoon-Doug consistency | that person's likeness consistency |
| `expressions` | happy/worried/… | the dramatic range to hold on-model |

Only the `style:` block changes (Pixar-3D → photoreal cinematic). The discipline, the
gates, and the consistency engine are identical. **We build it once, here, and it carries
to every kind of film we make.**

## Universal Rules — every film, every style, no exceptions

These hold whether it's a cartoon bloodhound or a photoreal human drama. They are not
per-film choices; they are constants the pipeline enforces on every project. The bible
above tunes *what* a film looks like; these govern *how* it's always made.

**A. Craft rules (filmmaking fundamentals)**
- **Continuity:** within a scene, every character / prop / wardrobe / light / time-of-day stays identical shot to shot.
- **Character consistency:** a character is the same design in every shot of every episode — guaranteed by the plate + LoRA, not by luck.
- **Scale is law:** relative sizes from the bible hold in every shot (Hank 2.6× Doug; real heights for people).
- **Screen direction / 180° rule:** keep spatial relationships and left/right positions consistent so the viewer is never disoriented; eyelines match who or what a character looks at.
- **Shot grammar / coverage:** every beat is a *sequence* of shots (establish → push-in → detail → return), never one static held frame.
- **Light & color continuity:** lighting direction and palette stay consistent within a scene/sequence.
- **Staging & readability:** clear silhouette, one focal point per shot — the audience always knows where to look.
- **Pacing:** cuts serve the story and the music; no dead air, no held slideshow shots.
- **Sound:** dialogue lands on the character's mouth motion; one talker per beat; cues never overlap or bleed across shots.

**B. Production law (our pipeline, hard-won)**
- **Foundation before production:** gates 1–4 locked before any story shot. No exceptions.
- **On-model or it doesn't ship:** every shot is QC'd at full resolution against the character's plate; off-model = rejected and regenerated. *Never rubber-stamp a contact sheet* (the four-ears lesson).
- **Ban-lists are enforced:** every generation respects each character's `never:` list.
- **Test small before batch:** prove one before making many.
- **Machine safety:** never render on battery; one heavy GPU job at a time; never crash the box — production must run unattended.
- **Validate audio cue timing before every composite;** never trust duration alone.
- **100% local:** every frame and every sound made on our hardware, in our language. No cloud inference, ever.

## The phase gates (nothing proceeds until the prior gate is LOCKED)

```
1. BIBLE        — write world + style + every lead's full spec        → Matt approves
2. DESIGN LOCK  — one approved hero plate per lead (the model sheet)   → Matt signs off the look
3. FORGE        — build each lead's LoRA from a curated on-model set   → the consistency engine
4. VALIDATE     — generate each lead in fresh poses, check vs plate    → on-model or re-forge
5. PRODUCE      — board → animatic → render (scenes ref chars by name) → QC each shot vs plate
6. POST         — edit, music, mix
```

**Rule:** no rendering of story scenes until gates 1–4 are locked. This is the discipline
we add. Skipping it is what cost us the four-eared, collar-drifting dog.

## The bible block (format)

```
film "<Title>" slug=<slug> style=<style-pack> format=<film|series>

world:
    setting:  "<where/when, the place the camera lives>"
    tone:     "<emotional register, audience>"

style:                              # = STYLE GUIDE
    look:     "<render style: e.g. Pixar-3D feature, rounded forms, soft GI>"
    lighting: "<key/rim/ambient rules>"
    banned:   "<global no-gos: photoreal, harsh shadows, etc.>"

character <name>:
    role:        lead | supporting | villain | incidental
    species:     "<what it is>"
    silhouette:  "<the shape, must read in pure black>"          # = SILHOUETTE TEST
    design:      "<prose description of the character's look>"   # = CHARACTER DESIGN
    palette:                                                     # = COLOR KEY (exact, law)
        <part>: <color name / hint>
        ...
    features:    "<signature, non-negotiable features — count them>"   # e.g. "exactly TWO floppy ears"
    markings:    "<distinguishing marks + what they are NOT>"
    never:       [<ban-list — defects/additions that are forbidden>]   # = the guardrail
    scale:       <number>                                        # = LINEUP/SCALE (relative size, law)
    voice:       <engine/id>                                     # = VOICE CASTING
    plate:       <path to locked model-sheet hero image>         # = MODEL SHEET
    lora:        <path to trained consistency LoRA>              # = "every artist draws it on-model"
    expressions: [<the emotional range to hold on-model>]        # = EXPRESSION SHEET
    status:      bible | design-locked | forged | validated      # which gate it has cleared
```

### Field → studio artifact (so the craft is baked into the format)

| Field | What a studio calls it | Why it matters |
|-------|------------------------|----------------|
| `silhouette` | silhouette test | a character must be recognizable as pure black shape |
| `design` | character design | the prose look, the starting point |
| `palette` | color key / color script | **exact colors written down** — kills marking/coat drift |
| `features` / `markings` | model sheet notes | counts the non-negotiables (e.g. ear count) |
| `never` | — (our addition) | the ban-list; the literal defects we forbid the generator |
| `scale` | lineup / scale chart | relative size is law, every duo shot uses it |
| `plate` | model sheet / turnaround | the locked hero the LoRA + every shot references |
| `lora` | the animation staff's skill | our consistency engine, encodes the plate |
| `expressions` | expression sheet | stay on-model while emoting |

## How the pipeline uses it

A story scene never re-describes a character. It names them:

```
scene riverbank with doug, hank:
    action: "Doug spots a fox stuck on a rock; Hank wades in"
```

The pipeline pulls each named character's `plate`, `lora`, `palette`, `scale`, and
`voice` automatically, and refuses anything on the `never:` list. Consistency is not a
per-scene chore — it's resolved from the bible.

## Authoring a new film (quickstart)

1. Copy this format into `projects/<slug>/<slug>.bible.sf`.
2. Fill `world` + `style`, then a `character` block per lead (leads first; villains and
   incidental cast can be added when their episode is boarded).
3. Get the bible approved (gate 1), then design-lock each lead (gate 2), then forge.
4. Only then write story scenes that reference the characters by name.

Leads get the full treatment. One-off/incidental characters (a rescued animal seen once)
stay `role: incidental` — background or SFX, no plate, no LoRA. Don't boil the ocean.
