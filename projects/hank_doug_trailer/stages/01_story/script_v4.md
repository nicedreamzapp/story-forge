# HANK & DOUG'S WILD RESCUE — 60-second trailer, script v4 ("Doug leaves the hunt")
Written 2026-11-17 (stage 01, writing only; nothing rendered). Replaces v2/v3 as the working script. v2 and its
approval are archived (APPROVED_v2.md). Painted look unchanged (look_test/PREFIX.txt). Straight cuts (v3 finish).

## Why v4 (Matt, after watching v3)
"its off the sounds and times and it needs to be more explanatory and things need to match up with the times and
sounds" and "make it better and more explanatory, show him abandoning the hunter, show how the bear is saving an
animal and that makes him realize the bear is cool, go back and look at our stories".

## The canon this is built on (read first, 2026-11-17)
- Jeremy's story vault, mini: `~/Desktop/PROJECTS/hank-and-doug/STORY_IDEAS.md` ("Doug's origin": "Doug is a bloodhound
  who used to hunt bears for his owner. He had a change of heart, led his owner into a ditch so he could save a bear,
  and then left to rescue animals alongside Hank." / "There are NO humans in the show.").
- The story-keeper agent's persona, the text Matt loaded from Jeremy's telling: mini
  `~/Desktop/PROJECTS/hank-and-doug/jeremy-agent-from-vps/jeremy_chat.py` line 36, same sentence word for word, plus
  the wagon crew (horses, camels, cows; giraffe ladders; elephant pumps) and the rule "some animal always eventually
  hears the call for help and signals the rescue crew".
- VPS live sessions `/root/hq-dashboard/jeremy_sessions/*.json`: the agent's own recap card "Doug leaves the hunt":
  "hunted bears for his owner, had a change of heart, led his owner into a ditch so he could save the bear, then left
  for good to rescue animals alongside Hank." No further detail from Jeremy himself exists anywhere (he never used
  the agent; every chat entry is Matt's testing). Jeremy's word is **owner**, never "hunter"; the narrator uses it.
- Rescue bank used here: fox caught in a fence (STORY_IDEAS "Later additions", filed June 2026), goat airlift,
  turtle in mud + elephants, kitten in a drain + otter chain (pilot scenes 1, 4 and the kitten addition).

## Spine (the heart, in order)
Doug on the hunt, the owner only a lantern glow and a whistle (no hands, boots, faces, guns, ever) → his nose finds a
bear → he sees that bear SAVING a fox caught in a fence → "that bear is cool" → the whistle again; Doug leads the
owner the other way → the lantern tumbles into the ditch and goes out → Doug goes back: "Hi." → the two walk away →
today: the wagon, the all-animal crew, a taste of rescues (sung) → title → button.

## Voice rules
Narrator = the warm storybook voice (Kokoro Heart, as v3's N1). Short clear lines, ~2.5 words/s, every line fits its
slot with air on both sides. Hank = wr3_hank, Doug = wr3_doug, Young Hank = Hank pitched +7 st (never a new voice).
Spoken words total: narrator 72, Doug 5, Young Hank 1, Hank 2.

## Music map
- 0:00-0:06 no music: crickets and the forest only (cold open).
- 0:06-0:36 `music/breakdown_1.wav` (music box, 30 s) at about -23 dB; one warm chord on "Hi." at 31.4 if stage 05 has
  one, else the music box carries. It ends as the day begins.
- 0:36-0:40.8 no music (the day, "Rolling.").
- 0:40.8-0:51.8 `music/theme_2.wav` 5.9 → 16.9 (instrumental build, then verse 1 words land at 44.4 exactly on the
  goat cut; the verse lists goat / turtle / kitten while each is on screen). Ducked -6 dB under the narrator until 43.0.
- 0:52.8-0:56.8 `music/theme_2.wav` 55.7 → 59.7 ("It's Hank and Doug's Wild Rescue!" + its chord tail) on the title.
  Splice on the downbeat, as v3 spliced its sections.
- 0:59.0-1:00 `music/theme_1.wav` sting "Here we go!" (the last ~1.1 s of 3.1-6.0) over black.
- Word onsets inside theme_2 segments are estimated below from `music/theme_2_words.json` (segment level); stage 05
  measures each onset with whisper word timestamps and moves the CUT to the word, never the word to the cut.

---

## THE TIMED TABLE (0-60 s). Rule: a sound exists only if the action making it is visible in that shot at that moment.
Footage: EXISTING = file + in/out seconds of the clip; NEW = must be rendered (Krea still, then LTX i2v).

| # | Time | Words (who, onset-end) | Picture on screen during the words | Sound, tied to the visible action | Footage |
|---|---|---|---|---|---|
| 1 | 0:00.0-0:05.0 | NARRATOR 0.5-3.3: "This is Doug. Doug used to hunt bears." | Night forest in moonlight, cold silver-blue. DOUG (design string, "a little younger") moves camera-left along a trail, nose on the ground. From off-frame right behind him a warm amber lantern glow lies across the trunks and the ground and follows him. No lantern object, no one, nothing else. Camera locked. | crickets (the night forest is the frame); Doug's sniffs on each nose-to-ground dip; a faint sway of the glow across the trunks = a soft lantern-handle creak on each sway | NEW-1 (5 s). Still: "G_hunt" from the G_forest raw prompt with the log and bear removed. must_not: lantern, hand, boot, person, gun, bear |
| 2 | 0:05.0-0:09.0 | NARRATOR 5.2-8.8: "Not because he wanted to. His owner made him." | DOUG close, side-on, stopped. The glow behind him swings hard across the trunks and his face; his head turns back over his shoulder toward it, ears back, eyes low. Camera locked. | the owner's WHISTLE (two short notes) exactly on the glow swing and Doug's head turn (the swing + turn are the whistle's visible action); crickets | NEW-2 (4 s). Still: Doug close, moonlight, glow from right. (If the ETA is tight, NEW-1 and NEW-2 merge into one 6 s clip: track, then look back.) |
| 3 | 0:09.0-0:13.0 | NARRATOR 9.2-12.0: "One night, his nose found a bear." | DOUG walks left nose down sniffing; YOUNG HANK is behind the fallen log at the forest edge, eyes wide. Locked camera, moonlight, no lantern. | sniffs on the nose dips; crickets. (The glow is gone in this clip: read as "the owner is behind, Doug is ahead of the light".) | EXISTING `clips/v3/G_forest_r2.mp4` 0.0-4.0 |
| 4 | 0:13.0-0:18.0 | NARRATOR 13.2-17.6: "But this bear wasn't hurting anybody. He was saving a fox." | Moonlit forest edge: an old sagging wire fence on grey wooden posts, nobody near it. A small RED FOX hangs by one hind leg caught in the wire, kicking, mouth open. YOUNG HANK rises on his hind legs, hooks both front paws into the wire and pulls the strands apart; the fox drops free, lands, shakes, bolts into the dark. Locked camera. | fox yips on every kick (mouth open, visible); the wire creaks then TWANGS as the bear pulls it apart (visible pull); quick paws on leaves as the fox bolts (visible run); crickets | NEW-3 (5 s). Still: "FOX_fence" (fence, fox caught, Young Hank reaching). FOX design: "a small red fox with a white chest and a black-tipped tail". must_not: person, hand, gate latch, sign, lantern |
| 5 | 0:18.0-0:22.0 | DOUG (V.O., quiet, to himself) 18.6-20.6: "Huh. That bear is... cool." | DOUG close in the brush, watching toward frame right: his ears lift, his eyes go soft, his tail starts to wag against the leaves. The lantern glow is faint and far on the trunks behind him. Locked camera. | the tail thumping leaves on each wag (visible); the fox's run fading (carried from row 4); crickets | NEW-4 (4 s). Still: Doug close, three-quarter, in ferns, moonlight, faint glow far right |
| 6 | 0:22.0-0:26.0 | NARRATOR 22.2-25.8: "So Doug led his owner away from the bear..." | Wide: the dark dirt road through the trees. DOUG runs away from the bear's side of frame along the road, barking back over his shoulder; the warm glow surges and sweeps along the trunks behind him, following; ahead at the bend the road's edge drops into a dark reedy DITCH. No lantern object, no one. Camera locked. | Doug's barks (mouth open, visible); running paws on dirt (visible); the whistle again, shrill, on the glow's lurch forward (visible surge); crickets | NEW-5 (4 s). Still: "ROAD_ditch" (road, bend, ditch edge, Doug running, glow). must_not: person, hand, boot, lantern object |
| 7 | 0:26.0-0:29.0 | NARRATOR 26.0-27.6: "...right into a ditch." | 26.0-27.4: the dented brass LANTERN alone tumbles end over end into frame from above-right and lands in the ditch water with a splash (the word "ditch" lands on the splash at 27.2). 27.4-29.0: the lantern lies lit in the ditch, flame flickering, water rippling, grass swaying; 28.4-29.0 the flame goes dark and the warm light leaves the frame. Nothing and no one else in frame. | clank-and-tumble on the lantern's rolling frames 26.2-27.1 (visible roll); SPLASH on the landing frame 27.2 (visible); hiss as the flame dies 28.4-29.0 (visible grade ramp); crickets back after | EXISTING, code: `stills/H2_lantern.png` cutout flown on a parabola with rotation over `stills/H1_ditch.png` + 4-frame painted splash (the v2 build plan), then `clips/v3/H_ditch.mp4` 1.0-2.6 with the grade ramp. sfx `sfx/lantern_fall.wav` |
| 8 | 0:29.0-0:33.0 | NARRATOR 29.0-30.6: "Then he went back." YOUNG HANK 31.0-31.7: "Hi." | Close two-shot in moonlight over the log: DOUG left, YOUNG HANK right, noses almost touching. A long beat. The bear's jaw opens once on the word; Doug's eyes soften. Moon only, no glow anywhere (the light is gone). | the one word on the visible jaw (clip 2.0-2.7 → 31.0-31.7; stage 05 confirms the onset by frame); crickets; one warm music-box chord at 31.4 | EXISTING `clips/previs/N_hi.mp4` 0.0-4.0 |
| 9 | 0:33.0-0:36.4 | NARRATOR 33.2-36.2: "That bear was Hank. Doug never hunted again." | Wide from behind: DOUG and YOUNG HANK walk away side by side down the moonlit road and shrink into the hills; a faint moon brightens. Locked camera. | paws on dirt as they walk (visible); crickets fading; the music box resolves and ends at 36.0 | EXISTING `clips/v3/I_walkaway_r2.mp4` 0.3-3.7 |
| 10 | 0:36.4-0:39.4 | NARRATOR 36.4-38.0: "Now they rescue animals." HANK 38.4-39.3: "Rolling." | Morning, the red WAGON parked under oaks: DOUG's ears flip up and his head turns; HANK (grown) turns from profile toward us and his mouth opens on the word (clip 2.4 → 38.4). The brass LANTERN hangs on its hook beside him. | morning birds in the oaks (daylight trees visible); Hank's word on his visible mouth | EXISTING `clips/v3/C_bench.mp4` 0.4-3.4 |
| 11 | 0:39.4-0:44.4 | NARRATOR 39.6-43.2: "A fire wagon, and a crew that's all animals." | Wide side profile: the TEAM (horse, zebra, camel, cow) pulls the wagon left, HANK and DOUG on the bench, giraffes and elephants with it, big spoked wheels turning, dust. | hooves and wheels on dirt (visible team and wheels) `sfx/hooves_wheels.wav`; theme_2 instrumental enters at 40.8 under the last words, ducked until 43.0 | EXISTING `clips/D_rollout_k6.mp4` 0.0-5.0 |
| 12 | 0:44.4-0:46.3 | SUNG (theme_2 9.5-11.4): "When a goat's stuck high" | The GOAT on the wooden platform, a dozen GEESE beating their wings on the ropes, the platform rising by the ledge. | wing beats (visible geese) `sfx/wing_beats.wav`; the sung words carry | EXISTING `clips/previs/L_airlift.mp4` 0.8-2.7 |
| 13 | 0:46.3-0:48.6 | SUNG (11.4-13.7): "and a turtle's stuck low" | Two grey ELEPHANT trunks pour splashy water from both sides onto the mud; the TURTLE lifts and floats. | water pouring and splashing (visible pour) `sfx/water_spray.wav` | EXISTING `clips/v3/E_turtle_r2.mp4` 0.6-2.9 |
| 14 | 0:48.6-0:50.0 | SUNG (13.7-15.1): "and a kitten" | Straight down through the drain GRATE: the tiny grey KITTEN looks up and mews, mouth open (clip 1.5-3.0 → mew at 48.9). | the kitten's mew on her visible open mouth `sfx/kitten_mew.wav` | EXISTING `clips/v3/F_kitten.mp4` 1.2-2.6 |
| 15 | 0:50.0-0:51.8 | SUNG (15.1-16.9): "is stuck in a drain" | The chain of four OTTERS is hauled up out of the hole; the bottom otter rises holding the kitten by the scruff. | otter chirps (visible otters) `sfx/otter_chirps.wav`; the small mew on the visible kitten | EXISTING `clips/previs/M_otters.mp4` 1.4-3.2 |
| 16 | 0:51.8-0:56.8 | SUNG (55.7-58.5) at 52.8-55.6: "It's Hank and Doug's Wild Rescue!" then the chord tail to 56.8 | Sunset hilltop: the silhouetted team pulls the wagon across, giraffes following, a tiny amber point on the wagon post. The TITLE paints in by brush strokes 52.0-53.2 ("HANK & DOUG'S" over "WILD RESCUE"), fully readable as "Hank" is sung at ~53.2, holds to 56.8 (3.6 s; 25 chars need 3.2). | the song only (the silhouette is far; no hooves) | EXISTING `clips/v3/J_title.mp4` 0.0-5.0 + the code title layer (`texts.json` start/end move to 52.0/56.8) |
| 17 | 0:56.8-1:00.0 | HANK 58.2-59.1 (eyes shut, flat): "Rolling." | Golden dusk under the oak: the wagon parked, the MARMOT on Hank's head, giraffes behind, the lantern lit. The CHIPMUNK pops onto the near wheel rim at 57.2 and squeaks; DOUG's head turns; HANK's mouth opens on the word (clip 2.0 → 58.2). Cut to black at 59.2. | silence after the chord; the chipmunk's squeak on the pop 57.2-57.9 `sfx/chipmunk_squeak.wav`; one tuba note on "Rolling." 58.2 `sfx/tuba_note.wav`; sting "Here we go!" 59.0-60.0 over black | EXISTING `clips/v3/K_button_r2.mp4` 0.6-3.8 + the chipmunk cutout composite (v3 code) |

Running check: 5+4+4+5+4+4+3+4+3.4+3+5+1.9+2.3+1.4+1.8+5+3.2 = 60.0 s.

## The words in order (what Matt hears)
- 0:00.5 NARRATOR: This is Doug. Doug used to hunt bears.
- 0:05.2 NARRATOR: Not because he wanted to. His owner made him.
- 0:09.2 NARRATOR: One night, his nose found a bear.
- 0:13.2 NARRATOR: But this bear wasn't hurting anybody. He was saving a fox.
- 0:18.6 DOUG (V.O.): Huh. That bear is... cool.
- 0:22.2 NARRATOR: So Doug led his owner away from the bear...
- 0:26.0 NARRATOR: ...right into a ditch.
- 0:29.0 NARRATOR: Then he went back.
- 0:31.0 YOUNG HANK: Hi.
- 0:33.2 NARRATOR: That bear was Hank. Doug never hunted again.
- 0:36.4 NARRATOR: Now they rescue animals.
- 0:38.4 HANK: Rolling.
- 0:39.6 NARRATOR: A fire wagon, and a crew that's all animals.
- 0:44.4 SUNG: When a goat's stuck high, and a turtle's stuck low, and a kitten is stuck in a drain
- 0:52.8 SUNG: It's Hank and Doug's Wild Rescue!
- 0:58.2 HANK: Rolling.

## New work list
- NEW clips (LTX i2v, each ~2-3 min): **5** — NEW-1 Doug tracks with the glow (5 s), NEW-2 Doug looks back at the
  whistle (4 s), NEW-3 Young Hank frees the fox (5 s), NEW-4 Doug watches, tail wags (4 s), NEW-5 Doug leads the
  light toward the ditch (4 s). Merge NEW-1 + NEW-2 into one 6 s clip if time is short (4 renders).
- NEW stills (Krea, seconds each): one per NEW clip (G_hunt, Doug_close_glow, FOX_fence, Doug_watch, ROAD_ditch).
  Style prefix word for word; Doug colour-locked in code after the render as before.
- NEW voice lines: 10 narrator lines (one batch), Doug "Huh. That bear is... cool." Reused as is: L4 "Hi." (padded,
  already in N_hi), L1/L6 "Rolling." (L1 is 0.97 s; both reusable), N1 is retired.
- NEW sfx (sfx batch tool): dog sniffs, two-note whistle, lantern creak, fox yips, wire creak + twang, dog barks,
  running paws on dirt, tail thumps in leaves, walking paws on dirt, morning birds. Existing sfx reused as named.
- Retired from v3: beats A_goat, B_marmot (the opening ripple), the "Long time ago / Then I met one / Same nose"
  V.O. lines, the pickup and chorus-1 placements, the music-box flashback grade (the night IS the first half now).

## Rows that need a sync check by frame in stage 05 (not by ear alone)
Row 7 splash frame = "ditch"; row 8 jaw onset = "Hi."; row 10 mouth onset = "Rolling."; rows 12-15 cut on the sung
word onsets (whisper word timestamps on theme_2); row 16 title complete before "Hank" is sung; row 17 pop = squeak,
mouth = "Rolling.". A row that fails its check is fixed by moving the picture or the cue, never by leaving them apart.

## Story test (picture alone, no words)
A bloodhound tracks at night with a warm light behind him; the light swings and he looks back at it, ears down. He
finds a young bear behind a log. The bear pulls a fox out of a fence and lets it run. The dog watches and his tail
wags. The dog runs the other way down the road, barking, the light chasing him toward a ditch. A lantern tumbles into
the ditch and goes out. The dog and the bear touch noses; the bear speaks; they walk away together under the moon. In
daylight the same two sit on a red wagon; the bear speaks; a horse, a zebra, a camel and a cow pull the wagon with
giraffes and elephants. Geese lift a goat. Elephants float a turtle. A kitten mews in a drain and otters lift her out.
The title paints over the wagon at sunset. A chipmunk squeaks at the sleeping crew and the bear answers without
opening his eyes.
Against the premise: the switch is shown with its cause (the bear saved somebody), the abandoning is shown (the light
led into the ditch), the leaving-together is shown, the crew and what it does are shown and said. No humans anywhere.

## Character design sheet
Unchanged from v2 (strings reused word for word) plus one: **FOX** = "a small red fox with a white chest and a
black-tipped tail" (colour lock: red orange; chest white; tail tip black). **FENCE** (prop, row 4 only) = "an old
sagging wire fence on weathered grey wooden posts at the forest edge, no gate, no sign".
