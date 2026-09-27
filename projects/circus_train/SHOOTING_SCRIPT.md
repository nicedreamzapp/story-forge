# HANK & DOUG'S WILD RESCUE
## Episode 1 — "The Circus Train"

**Shooting script — v2, 2026-07-25**
Runtime target 2:10 · 8 scenes · Story Forge local pipeline

---

> ## ⚠️ UNRESOLVED CANON CONFLICT — READ BEFORE RENDERING
>
> This script tells the circus-train story as **a jammed boxcar door with a frightened
> elephant behind it**, freed by Hank's shoulder.
>
> **Jeremy's canon version is a different episode:** *a circus train about to derail at a
> gap in the tracks, saved by an army of ants strapped with metal.* His full canon —
> Doug's bear-hunting origin, the horse-drawn fire-wagon, giraffe ladders, elephant water
> pumps, and eight pilot scenes — is written up in the story vault on the mini at
> `~/Desktop/PROJECTS/hank-and-doug/STORY_IDEAS.md`.
>
> Matt has NOT chosen between them. Do not spend render time on Episode 1 until he does.

---

### WHY THIS DRAFT EXISTS

Matt watched rough cut v1 on 2026-07-23 and called it: *the story doesn't make sense.*
Three specific failures, all real:

1. **No call to adventure.** A bird crash-lands and announces the plot. Nobody
   *discovers* anything, so the audience never leans in.
2. **Ellie is never on screen.** The whole rescue is for a character who exists only
   as a voice behind a door. There is nothing to root for.
3. **The door never opens.** Hank heaves, and then the film cuts to animals already
   free. The single promised payoff happens off-screen.

This draft fixes all three without discarding a frame of approved work. Five scene
finals, sixteen voice takes, three locked character masters and the Ellie canon all
survive. What changes is *structure*: a discovery instead of an announcement, Ellie
made visible in three escalating stages, and a door that actually bursts open on
camera.

---

### CAST

| Character | Who they are | Voice |
|---|---|---|
| **HANK** | Brown bear. Strength, few words, dry. Solves things with his shoulder. | ChatterBox built-in, torch seed 44 |
| **DOUG** | Bloodhound. The heart and the talker. Reads people, counts them down. | Matt's cloned voice |
| **ELLIE** | Young circus elephant. Frightened, then radiant. The reason for the episode. | spare_voiceB |
| **BIRD** | Off-screen messenger. One gag, no design. | spare_voiceA |

**Rule carried forward:** wide shots are pure diffusion frames only. No character is
ever composited into a wide — characters who can't survive a wide get their own insert.
This is film grammar, not a limitation.

---

## SCENE 1 — COLD OPEN: THE CREEK

*Exterior. A slow green creek. The Fire Engine wagon parked in dappled shade, two
fishing rods propped against the wheel. Late morning, warm and unhurried.*

**Runtime:** 0:00–0:14 · **Status:** LOCKED (`clips/s1_final.mp4`)

**Shots**
1. WIDE — the wagon, the creek, two friends doing nothing much. Establish the calm
   we are about to break.
2. CLOSE — Hank, watching his line go nowhere.
3. CLOSE — Doug, unbothered.

**Action.** Nothing happens, and that is the point. Fourteen seconds of a good day, so
the interruption costs something.

> **HANK:** Doug. The fish are winning again.
>
> **DOUG:** That's cause they practice, Hank.

**Notes.** Dialogue takes L01, L02 exist and are cut in. Do not touch this scene.

---

## SCENE 2 — THE CALL *(REWRITTEN — this is fix #1)*

*The same creek. Something arrives on the wind.*

**Runtime:** 0:14–0:32 · **Status:** NEW — needs one still + one animated beat

**Shots**
1. CLOSE — Hank's ear turns. He heard it before he understood it.
2. WIDE — over the treeline, a thin column of smoke. Far off, a train whistle drops
   and drags — a sound with something wrong in it.
3. TWO-SHOT — Doug already on his feet. He doesn't ask what it is. He asks what it needs.

**Action.** No messenger explains the plot. The boys *notice* it. Hank hears, Doug
stands, and the wagon is moving before either of them has finished thinking.

> **BIRD** *(off-screen, thin and far away, over the wide):* Help! The circus train
> broke down — everybody's stuck in the sun!
>
> **DOUG:** Circus train? Hank — we're rolling.

**Notes.** The bird stays a voice only; no bird character is designed for this episode
(Matt's standing call). Its line now lands *after* the smoke, so it confirms what we
already saw rather than announcing it cold. Voice takes L03, L04 exist. Needs: one new
locked still (smoke over treeline, golden hour) — candidate `stills/wip/s4_call_11.png`
is strong but carries gibberish lettering on a train car; inpaint or reroll before
Matt sees it.

---

## SCENE 3 — ROLL OUT

*The Fire Engine wagon charges out of the trees, full wood and brass, dust behind it.*

**Runtime:** 0:32–0:44 · **Status:** LOCKED (`clips/s2_final.mp4`)

**Shots**
1. WIDE — the wagon takes the road, low camera, everything committed.

**Action.** Silent. The theme carries it. This is the show's promise in one shot: these
two go when called.

**Notes.** No dialogue by design. Theme music enters here and the episode's single
continuous song strings across everything that follows.

---

## SCENE 4 — ARRIVAL

*The stalled circus train, baking. Heat shimmer off the roofs. Painted cars, silent.*

**Runtime:** 0:44–0:58 · **Status:** LOCKED (`clips/s3_final.mp4`)

**Shots**
1. WIDE — the train in the heat, too still.
2. MEDIUM — Hank surveying the length of it.
3. MEDIUM — Doug moving straight to work.

> **HANK:** Whole train's cooking out here.
>
> **DOUG:** Easy everybody! The Wild Rescue's here!

**Notes.** Takes L05, L06 cut in.

---

## SCENE 5 — THE DOOR, AND THE EYE *(EXPANDED — this is fix #2)*

*A boxcar. The door pin driven crooked and locked solid. Inside, something large and
frightened.*

**Runtime:** 0:58–1:18 · **Status:** partially locked (`clips/s5_final.mp4` = Doug at
the crack) · needs the Ellie insert

**Shots**
1. CLOSE — the jammed pin. Doug's paw tests it. It does not move.
2. CLOSE — Doug puts his nose to the gap between the planks.
3. **INSERT — through the crack: a single amber eye, wet and enormous, finds the light.**
   *This is the shot the film has been missing.* Two seconds. We finally see who we
   are saving.
4. CLOSE — Doug's whole manner changes. He stops solving and starts talking to her.

**Action.** Doug's approach is the character beat of the episode: he doesn't force the
door, he calms the animal behind it first.

> **DOUG:** Pin's jammed tight.
>
> **ELLIE** *(from inside, shaky):* I can't... it's too heavy...
>
> **DOUG:** Ellie? It's Doug. One push, girl. I'll count you down.

**Notes.** Takes L07, L08, L09 exist. The eye insert derives from `canon/ellie_canon.png`
— never fresh-generated. Proven recipe: PIL rough composite of the eye region behind
the plank slit, then img2img weld at ~0.62 denoise. **Known trap:** the weld drifts her
skin porcelain-white and can add a stray gold collar. Tint the composite toward her
canon warm gray *before* welding, then side-by-side color QC against canon before Matt
sees it.

---

## SCENE 6 — THE HEAVE *(REBUILT — this is fix #3)*

*Hank sets his shoulder against the door. Doug counts. Inside, Ellie leans.*

**Runtime:** 1:18–1:34 · **Status:** REBUILD — existing `clips/s6_final.mp4` is rejected

**Shots**
1. MEDIUM — Hank plants his feet, drops his shoulder, and drives. Real weight, real
   effort, sustained.
2. CLOSE — Doug's face, counting, willing it.
3. **INTERIOR — dark boxcar. The frame shudders. Dust sifts down through a blade of
   light. The light-crack at the door widens.** The impact is *felt* here, never shown.
4. CUT.

> **DOUG:** Three... two... one... PUSH!
>
> **HANK:** Doors don't argue with bears.

**Notes — read before rebuilding.** The current S6 final is why this scene is being
redone. Matt's verdict: *"him drilling a stick in the box car... senseless."* Root
cause: the prompt asked for an impact, and the pipeline cannot render collisions — it
converted the hit into a continuous spray of splinters, which reads as drilling. The
locked still (wind-up pose) is fine and stays.

**The rebuild uses motion transfer** (proven and approved 2026-07-25). Hank's heave is
driven by real footage of a person shoving hard against a fixed object — a lateral,
constant-distance action, exactly the kind this pipeline handles well. Source footage
must keep the performer side-on and single-subject.

**Never prompt for the hit itself.** The bang lives in shot 3, inside the dark car,
carried by shudder and falling dust. That is the whole trick.

---

## SCENE 7 — THE DOOR OPENS *(NEW — the payoff)*

*The door gives.*

**Runtime:** 1:34–1:52 · **Status:** NEW — needs staging

**Shots**
1. WIDE — the boxcar door bursts wide, daylight flooding in.
2. **MEDIUM — Ellie steps down into the sun.** Full body, whole animal, blinking. The
   promise of the episode, paid in full.
3. WIDE — the rest of them pour out behind her. Giraffes finding the water ladders,
   a turtle already claiming the tank, spray going everywhere.
4. CLOSE — Ellie, laughing.

> **ELLIE** *(laughing):* Best. Rescue. Ever!
>
> **DOUG:** Turtle called dibs on the tank an hour ago.

**Notes.** Takes L12, L13 exist. Ellie's step-down derives from her canon master via the
composite-then-weld recipe — direct img2img will not restage her and has already been
proven useless for this. Build the empty doorway plate first, then place her in it.

---

## SCENE 8 — PAW BUMP AND TAG

*Late light. The wagon, packed. The train alive again behind them.*

**Runtime:** 1:52–2:10 · **Status:** NEW — needs one wide

**Shots**
1. TWO-SHOT — Hank and Doug, paw bump.
2. WIDE — the wagon pulling away down the golden road.
3. CLOSE — the bird lands on Hank's hat. Beat. Gag.

> **DOUG:** Anybody, anywhere, any trouble at all...
>
> **HANK:** ...the Wild Rescue rolls.
>
> **BIRD:** Can I get a hat like this?

**Notes.** Takes L14, L15, L16 exist. The bird is a silhouette landing on the hat brim —
still no bird design required.

---

## PRODUCTION STATUS

| Scene | Asset | State |
|---|---|---|
| 1 Cold open | `clips/s1_final.mp4` | ✅ locked |
| 2 The call | still + animation | ⬜ new — reroll the lettering flaw |
| 3 Roll out | `clips/s2_final.mp4` | ✅ locked |
| 4 Arrival | `clips/s3_final.mp4` | ✅ locked |
| 5 Door + eye | `clips/s5_final.mp4` + Ellie insert | 🟡 half — insert needed |
| 6 The heave | rebuild via motion transfer | 🔴 current final rejected |
| 7 Door opens | doorway plate + Ellie step-down | ⬜ new — the payoff |
| 8 Paw bump | wide + hat gag | ⬜ new |

**Already in hand:** all 16 dialogue takes, Hank/Doug/Ellie canon masters, Doug LoRA V2,
the music bed, and a proven motion-transfer path for physical action.

**Build order** — one approval at a time, nothing rendered before the still is locked:
Scene 5's Ellie eye → Scene 7's door-open payoff → Scene 6's heave rebuild →
Scene 2's call → Scene 8's goodbye → full assembly with song, titles, and QC.

Ellie first, because she is the fix that matters most: the moment the audience sees who
is behind that door, every other scene starts working.
