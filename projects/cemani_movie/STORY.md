# Cemani: the movie. Story plan

Written 2026-11-16. A documentary-style build log about Matt Macosko's homestead robot Cemani
(1 kW, four hub motors, 24 V LiFePO4, 2020 aluminum frame, Teensy 4.1 + two ZLAC8015D drivers,
ESP32 bridge, Jetson Orin Nano, RPLidar, PTZ cameras).

Rules this plan is built on:
- Matt's recorded voice carries every chapter. No narrator, no voice clone, no title cards that tell the story.
- The prompts below are questions he answers into a voice memo in his own words. They are never lines to read.
- Nothing stated here as fact comes from anywhere but the repo, the docs, the memory notes and the chat
  transcript. Where the sources are silent, the prompt is an open question and the fact sits under UNKNOWN.
- Photos IMG_7681 and IMG_7682 are excluded from every cut.
- Music is instrumental, made locally (ACE-Step / Song Forge). One recurring motif ties the film together.

---

## 1. Title options and logline

1. **Cemani: Four Wheels, One Brain**
2. **The Shudder** (the problem that started the rebuild)
3. **Built on a Homestead** (recommended)

**Logline:** A 1 kW robot built from scratch on a Humboldt homestead learns to roll, hauls firewood,
shakes itself apart in the turns, and comes back with a steering system designed in one long night.

---

## 2. Runtime, tone, style

- **Runtime target:** 5 to 6 minutes (hard ceiling 7).
- **Tone:** cool maker documentary. Honest about what broke. Confident about where it's going.
  Think a well-shot build log with real engineering in it, not a product ad.
- **Picture style:** real footage first, always. Phone clips and photos are the spine. The CAD and viewer
  animations are the "X-ray" that shows what the camera can't. Cuts land on the beat. Slow push-ins on
  stills (2 to 4 seconds each, never a slideshow feel, max 3 stills in a row before motion returns).
- **Color:** keep the real footage natural (wet gravel, redwood shade, overcast Humboldt light). CAD
  sections are dark background with the part being discussed lit; everything else dimmed.
- **Graphics:** small part labels only, on CAD/viewer animations (part name, size, qty where useful).
  Nothing else on screen. No lower thirds with story text, no chapter cards.
- **Voice treatment:** Matt's memo audio as recorded. Light clean-up only (noise, levels). Nothing else.

**The recurring motif:** a 4-note synth/guitar figure, first heard faint in the cold open, returns at every
"it works" moment (first roll, firewood, the 4WS decision), and plays in full at the end.

---

## 3. Chapters

Each chapter: what it shows, shot list (exact files), talking prompts, music, sound design, labels allowed.

Footage root: `~/Desktop/PROJECTS/story-forge/projects/cemani_movie/footage/`
Repo root (GitHub nicedreamzapp/CemaniHomesteadRobot, local clone `~/Desktop/PROJECTS/CemaniHomesteadRobot`).

### Cold open (0:00 to 0:10)

**Shows:** black. Motor whine rising. Cut to the robot mid-turn on gravel, the frame visibly vibrating
(pull the shakiest 2 seconds from the maneuverability clip or the YouTube demo). Hard cut to black on
the worst shake. One line of Matt's voice over black (from his memo, whichever line of his answers lands
hardest, e.g. his answer to "What did the shudder feel like?"). Then the motif enters and chapter 1 begins.

**Shot list:**
- `footage/repo_clips/` maneuverability clip (the README's "Maneuverability" attachment) or
  `footage/youtube_demo.mkv` (NWnGvvdvRik), the tightest turn.
- Phone pull (pending): any clip of it turning in place.

**Music:** none for the first 6 seconds, only sound design. Motif enters at the cut to black.
**Sound design:** hub motor whine (pitch rising), tire scrub on gravel, frame rattle. Silence on the black.

---

### Chapter 1: Four motors, one brain (0:10 to 1:00)

**Shows:** what Cemani is and how it started. The bare build: 2020 extrusion, the black suspension modules
with coil-overs, four knobby hub motors, the Teensy and the two ZLAC drivers, the battery, the Jetson,
the LIDAR on top. Then the early problems in Matt's words.

**Shot list:**
- `footage/photos/steering_v3_real/` (his reference photo `matt_robot_ref.jpg`, `IMG_7735.jpg`) for the
  robot as built.
- `footage/photos/steering_rebuild/` IMG_7679, 7680, 7683, 7684 (component close-ups). NEVER 7681/7682.
- `footage/photos/repo_media_stills/` (Photoroom_20251025_185931.JPG, Photoroom_20251027_050455.JPG).
- Repo `docs/robot-diagram.png` for 2 seconds max, as a push-in, while he names the parts (it's a diagram,
  not a story card; allowed because it's his own doc).
- Phone pull (pending): any bench or wiring footage, driver LEDs, the Teensy on the bench.

**Talking prompts (Matt answers in his own words):**
1. What is Cemani, in one breath? What's it for on the homestead?
2. Walk me through the parts the first time you put it together: the frame, the four hub motors, the
   drivers, the Teensy, the Jetson. What did each one take to get right?
3. What went wrong the first time you wired the drivers? (UNKNOWN: the sources don't record this.)
4. Were the wheels spinning the right way the first time you powered it up? What did you have to flip
   or change? (UNKNOWN.)
5. What was the moment you thought "this might actually work"?

**Music:** motif in a sparse arrangement. 92 BPM. Muted electric guitar plucks, a low analog pad, soft kick
on 1 and 3. No drums beyond that yet. Builds a hi-hat in the last 10 seconds leading into chapter 2.
**Sound design:** bench ambience, relay clicks, the ZLAC driver's startup beep if a phone clip has it,
screwdriver on aluminum.
**Labels:** none in this chapter (real footage only, except the 2-second diagram).

---

### Chapter 2: It rolls (1:00 to 1:40)

**Shows:** the first time it moved. The repo clip literally titled "Robot is finally mobile. Have to work on
the acceleration ramp up still." Let the jerky starts show; that IS the story of the ramp.

**Shot list:**
- `footage/repo_clips/Robot is finally mobile.   Have to work on the acceleration ramp up still.MP4` (full
  use, trimmed to the best 15 to 20 seconds).
- `footage/repo_clips/6E106B08-FC6D-423A-8807-EC3339DD2111.mp4` (the unnamed clip; screen it, use if it's
  early driving).
- `footage/youtube_demo.mkv` mobility test segment.

**Talking prompts:**
1. Tell me about the day it first rolled. Where were you, what did it do, what did you yell?
2. The clip says "have to work on the acceleration ramp up still." What was happening when it started
   moving, and how did you fix the ramp? (UNKNOWN: fix details not in the sources.)
3. How did you drive it then: the Xbox controller through the ESP32, the browser command center, or text
   from your phone? Which came first?
4. What surprised you about how it handled?

**Music:** the motif opens up. Drums come in on the first roll (kick, snare, hats), 92 BPM, bass synth
doubles the motif. First "lift" of the film. Drops back to pads for the ramp-up talk, then rebuilds.
**Sound design:** motor whine ramping, gravel crunch, the jerk of the frame on each hard start (a short
low thud per lurch), wind.
**Labels:** none.

---

### Chapter 3: Earning its keep (1:40 to 2:25)

**Shows:** the robot doing work. Firewood cart. The mobility, maneuverability and speed tests from the README.
Quick split: the command center UI (cameras + 3D LIDAR point cloud) next to the robot moving.

**Shot list:**
- `footage/repo_clips/Robot  pulling cart carrying firewood.mp4` (hero clip, hold it long).
- `footage/youtube_demo.mkv` speed test + mobility segments.
- Repo `docs/command-center.png` (push-in, 3 seconds) or a screen recording of the command center if the
  phone pull or a future session gives one.
- Phone pull (pending): any clip of it around the yard, the chickens, the coop, the firewood pile.

**Talking prompts:**
1. The firewood cart. Whose idea, how much weight, how did it pull?
2. What can it do today that you actually use? (text commands, object detection, LIDAR mapping, the
   command center.)
3. What did the speed test tell you? How fast does it really go?
4. What were you proudest of at this point?

**Music:** fullest groove so far. 96 BPM, a little faster. Add a second guitar line and a clap on 2 and 4.
The motif returns as a hook when the cart is moving. Clean cut to near-silence at the end of the chapter
(sets up the shudder).
**Sound design:** cart wheels rattling, wood shifting, motor whine under load (lower pitch), gravel.
**Labels:** none.

---

### Chapter 4: The shudder (2:25 to 3:05)

**Shows:** the problem. Skid steer with four fixed wheels drags the tires sideways in every turn; the whole
tall robot shakes. A wheel came off. It sat for about five months. (Source: rebuild README and the
2026-10-01 transcript: "Cemani wheel came off, and it's been about five months at least.")

**Shot list:**
- The shakiest turn from the maneuverability clip and the YouTube demo, slowed to 50 percent for 3 seconds.
- Repo `docs/rebuild-2026/photos/current-front.jpg` and the measurement photos
  (`photos/measure-IMG_7729.jpg` through `measure-IMG_7733.jpg`): the tape on the frame, the 4 1/2 in gap
  between front and rear tire.
- Repo `docs/rebuild-2026/photos/current-corner.jpg` (also in `footage/photos/repo_docs_photos/`): the
  single-side clamp on the hub motor axle (the transcript names the cantilevered axle as the likely reason the
  wheel came off).
- Phone pull (pending): the robot sitting, dusty, wheel off, if it exists.

**Talking prompts:**
1. What did the shudder feel like in a turn? Describe it like I'm standing next to it.
2. Tell me about the wheel coming off. What happened, and what did you find when you looked at the mount?
3. Why did it sit for five months? What got you back to it on October 1st?
4. When did you realize skid steer was the problem and steering was the answer?

**Music:** drops to a single low pad and a slow pulse, 70 BPM feel. The motif is played wrong on purpose
once (one note flat, or stopped short) when the wheel comes off, then silence under "five months."
**Sound design:** the scrub, the rattle, then one metallic clank for the wheel. Then room tone only.
**Labels:** one small label allowed on a still: "4 1/2 in between tires" on the measurement photo, matching
the README number. Nothing else.

---

### Chapter 5: Back to the drawing board (3:05 to 3:50)

**Shows:** the rebuild of the frame. Frame v1 plan (longer, built from the 2020 pieces on hand, no cutting),
frame v2 (cross rails at the wheel mounts, 8 uprights, a gusset on every upright, batteries low), then the
REAL frame v3 built in November: a low box in front, a tall box over the back, two black rails on top.
Intercut the Blender renders with photos of the actual frame.

**Shot list:**
- Repo `docs/rebuild-2026/new-frame.png` (v1 render), `how-it-steers.jpg`, `where-the-lazy-susan-goes.jpg`
  (marked-up photos of his own robot, 2 seconds each).
- Repo `docs/rebuild-2026/frame-v2/bare-frame.jpg`, `bare-above.jpg`, `bare-side.jpg`, `bare-underneath.jpg`
  (Blender renders, dark background).
- Repo `docs/rebuild-2026/frame-v3/iso.jpg`, `side.jpg`, `top.jpg` (the built frame).
- `footage/photos/steering_v3_real/v3/` IMG_8097 through IMG_8110 (2026-11-11, the real frame, the best 5).
- Phone pull (pending): building the frame, tightening T-nuts, squaring the diagonals.

**Talking prompts:**
1. The new frame: what did you want it to fix? (The README says the shudder and how easily a tall robot on a
   short footprint could tip.)
2. You built it from the 2020 pieces you already had, no cutting. Why that rule?
3. What changed from the first drawing to the frame that's sitting in your shop now?
4. How long did the frame take you to put together once the plan was set?

**Music:** rebuild energy. 100 BPM, driving hats, a plucked arpeggio over the motif's chords, builds steadily
through the whole chapter. Think "montage" without being cheesy: keep it mid-energy, save the peak.
**Sound design:** T-nuts dropping into slots, hex key ratcheting, aluminum tapping aluminum, tape measure
snapping back.
**Labels:** on renders only. "400 mm 2020", "cross rail", "gusset", "top plate". Small, one at a time,
matching whatever Matt is talking about.

---

### Chapter 6: The corner problem (3:50 to 4:50)

**Shows:** the steering saga. The one question the whole rebuild came down to: how does one corner pivot
and still hold the wheel on? Every answer that got thrown out, in order, each one as a quick CAD beat:
1. 6 in square lazy susan (the first plan). Matt bought them. Way too big; the corner holes couldn't all land
   on a 20 mm rail ("not enough room for the screws").
2. KFL001 eared flange bearing on an M12 bolt (the 10/21 kingpin plan). Matt watched the bolt-by-bolt
   animation on 11/15 and called it: two M5 screws won't hold the wheel. He wants at least four bolts per
   corner, and the load can't hang on a set screw.
3. Round slewing ring (RU85 crossed roller, 8 bolts each side). Strong, about $114 a corner.
4. UCF205 flange bearing (1 in bore). 1/2 in bolts don't fit 2020 slots, so it needs an adapter plate.
5. UCF204-12 flange bearing (3/4 in bore) under TWO 2020 rails 64 mm apart. All four M5 bolts go straight
   into T-nuts. No adapter plate. The winner.
Then the "load goes UP" correction: the wheel pushes the shaft up, so the collar that carries the weight sits
under the bearing. And the rule that held through all of it: no cutting, no welding, no drilling.

**Shot list:**
- `steering-v3/cad/renders/exploded_corner.png` and `front.png`, `iso.png`, `top.png`.
- `steering-v3/cad/renders/parts/*_alone.png` and `*_inplace.png` (77 renders: pick the UCF204 bearing,
  shaft, flanged collar, steering plate, black suspension plate, clevis pin, heim joint, tie rod).
- `steering-v3/corner-simple.html` recorded with `_scripts/rec.mjs` (the door-hinge exploded corner, the
  user-controlled swing). This is the clearest single image of the final corner.
- `steering-v3/parts-front-img/` (21 real part photos from listings) as quick inserts.
- `steering-v3/pin-vs-tierod.png`.
- Lazy susan: a photo of the actual too-big lazy susans in his hand (FOOTAGE GAP) or the repo's
  `where-the-lazy-susan-goes.jpg`.
- `footage/photos/steering_rebuild/2026-10-15-measurements/` diagrams (23_10-21_new_plate_holes.jpg,
  24_10-21_full_stack_every_piece.jpg) for the kingpin plan beat.

**Talking prompts:**
1. The lazy susans showed up. What happened when you held one up to the frame?
2. You watched the eared-bearing animation and said two screws won't hold the wheel. What did you see that
   made you sure?
3. Walk me through the bearings you looked at and why each one was out, until the UCF204 under two rails.
4. Your rule is no cutting, no welding, no drilling. Why does that matter to you on this build?
5. The weight pushes UP from the wheel into the frame. When did that click, and what did it change?

**Music:** tension and iteration. 104 BPM, a ticking percussive loop (woodblock/rim), bass pulses on each
rejected design, a short rising riser into each new candidate. The beat stops dead on "the winner" (UCF204),
one bar of silence, then the motif comes back clean on the exploded corner.
**Sound design:** a soft click as each label lands, a low "thunk" when a design is dropped (dim it on screen),
bearing spinning (a real ball bearing spun by hand would be perfect: FOOTAGE GAP).
**Labels:** this is the chapter for labels, still small and one at a time: "6 in lazy susan", "KFL001, 2 x M5",
"RU85 slewing ring", "UCF205, 1 in bore", "UCF204-12, 3/4 in bore", "second 2020 rail, 64 mm", "3/4 in shaft",
"flanged collar", "1/4 in steering plate", "clevis pin", "heim joint", "5/16 tie rod", "Glideforce actuator".

---

### Chapter 7: Turn all four (4:50 to 5:35)

**Shows:** the 4-wheel steering decision (made 1:41 AM, 11/16) and the design that came out of it. The turn
radius viewer: front steering alone turns in about an 8.8 ft circle; all four wheels steering, back wheels
turned the opposite way, about 5.9 ft. Then the 25-step build viewer assembling itself, part by part, front
first, then the back mirrored, then the counter-steer swing. The CAD clash checks that caught real mistakes
before anything was bought: the 2 1/2 in clevis pin was wrong (needs 2 in), the M5x30 bearing bolts were
wrong (M5x18), the 200 mm tie rod he already owns fits if the arm holes move in front of the axle.

**Shot list:**
- `footage/steering_4ws_normal_1080p.mp4` and `footage/steering_4ws_real_1080p.mp4` (the recorded
  25-step viewer, CAD look and real look). Use the real look for the final swing.
- `footage/gif_clips/build-4ws.mp4`, `footage/gif_clips/steering-4ws.mp4`.
- `steering-v3/viewer-turn-radius.html` recorded with `_scripts/rec.mjs`: the two circles side by side.
- `steering-v3/cad/renders/iso.png` for the full assembly, `top.png` with wheels angled.
- Phone pull (pending): Matt at the mini late at night watching the viewer, if it exists.

**Talking prompts:**
1. You asked "how crazy would 4-wheel steering be." What made you ask, and what made you say yes?
2. Front first, back later. Why that order?
3. The CAD caught the clevis pin and the bolt lengths before you bought them. How does that compare to how
   you used to find out a part was wrong?
4. What does a 5.9 ft circle mean around the coop and the woodpile compared to 8.8?

**Music:** the peak. 104 BPM carried over, full arrangement: drums, bass, both guitars, pad, the motif as the
lead line. The drop lands exactly on the first frame of the counter-steer swing (all four wheels turning).
Hold the energy through the build-viewer montage, then ease down for the carts.
**Sound design:** the viewer's build steps get a soft mechanical "seat" sound per part (two or three
variations, not every step). Actuator hum on the swing. Tire scrub is GONE here: the absence is the point.
**Labels:** "8.8 ft" and "5.9 ft" on the turn-radius circles. "front actuator", "back actuator", "tie rod" on
the viewer. Step numbers are already in the viewer and are fine.

---

### Chapter 8: Faster every time (5:35 to 6:10) and the ending

**Shows:** where it stands right now. The real frame in the shop. The parts picked one at a time and sitting in
three carts (Amazon: front hardware; eBay: two UCF204-12 and two 3/4 x 2 in clevis pins; Zoro: two Ruland
face-mount collars). Steering plates go to the laser cutter once the bearings and collars are measured.
Then Matt on how each round is getting faster.

**Shot list:**
- `footage/photos/steering_v3_real/v3/` the frame today (best 2 photos, slow push-in).
- `steering-v3/parts-front.html` recorded (the labeled front parts list) or `steering-v3/cad/renders/parts/`
  as a fast grid.
- Phone pull (pending): the bearings arriving and getting calipered (FOOTAGE GAP if not filmed yet).
- End on real footage: the firewood clip's best 3 seconds or the first-roll clip, color held natural.

**Talking prompts:**
1. Where is Cemani right now, today, in one breath?
2. In October you said you were confused by the drawings. Last night you were the one catching the design
   mistakes. What changed?
3. First rebuild plan to a 4-wheel-steering design with every part picked: how long did that take, and how
   long would it have taken a year ago?
4. What's the first thing you're going to do when the bearings land?
5. What's next after steering? (The repo roadmap lists a depth camera, the IMU, auto-docking, predator
   alerts, the coop.)

**Music:** motif in full, warm, 92 BPM again (back to the opening tempo, so the film closes a loop). Drums
drop out for the last 15 seconds, leaving guitar and pad. Last note rings over black.
**Sound design:** shop ambience, a box being cut open (gap), then outdoors: wind, birds, gravel, one motor
spin-up that fades.
**Labels:** none.

**The ending (last 10 seconds):** the robot rolling away on gravel (firewood or mobility clip), Matt's answer to
"what's the first thing you'll do when the bearings land" as the last voice heard, cut to black on the motor
spin-down, the motif's final note. No end card with story text. If anything appears on the black, it is only
the repo URL and the robot's name, small, 3 seconds.

---

## 4. Cold open and ending, in one place

**Cold open (0:00 to 0:10):** black, motor whine rising. Hard cut to the robot shaking in a turn (2 s).
Cut to black on the worst shake. One line of Matt's voice over black. Motif enters.

**Ending:** robot rolling away, Matt's "when the bearings land" answer, black on spin-down, final motif note.

---

## 5. Footage gaps (short list; Matt can film these on his phone in a few minutes each)

1. The actual too-big lazy susans held up against the frame (10 seconds).
2. One real corner today: the black suspension plate, shock, hub motor, slow handheld orbit (20 seconds).
3. A bearing spun by hand, close up, when the UCF204s arrive (10 seconds). Also calipering it.
4. The Teensy and the two ZLAC drivers in the robot, powered, LEDs on (10 seconds).
5. The robot's shaft/axle clamp where the wheel came off, if the old mount still exists (10 seconds).
6. Him at the bench or at the mini with the build viewer on screen, over the shoulder (10 seconds).
7. Any old phone clip of the robot turning in place on gravel, the shakier the better (the separate phone
   pull may already cover this).
8. Boxes arriving and getting opened (whenever they come).

---

## 6. UNKNOWN facts (not in the sources; the prompts ask, we never state)

1. What specifically went wrong with the driver wiring the first time (RS-485, power, fuse, anything).
2. Whether any wheels spun the wrong direction at first power-up and what was flipped to fix it.
3. How the acceleration ramp was fixed after the "finally mobile" clip (firmware change, driver setting,
   or still open).
4. The exact date of the first roll and of the firewood clip (repo stills are dated 2025-10-25 and 10-27;
   the clips themselves are undated in what we have).
5. The weight of the firewood load and the cart.
6. Which control path came first for driving it (Xbox via ESP32, browser, or text).
7. Whether the dropped parts (lazy susans, KFL001 bearings) were actually bought and received, beyond the
   lazy susans, which Matt said he bought and were way too big.
8. The actual top speed from the speed test.
9. How long the real v3 frame took to assemble.
10. Whether the shudder clip we have IS the shudder, or only a mild version of it (Matt should confirm by
    watching the maneuverability clip).

---

## Production notes (not for Matt, for the editor/agent)

- Voice memo collection: 8 chapters, 35 prompts. Matt skips any he wants. One take per prompt is fine;
  talking while the robot moves beats standing still. Mistakes and "this broke" moments stay in.
- Music: 6 cues from one motif (cold open sting, ch1-2 sparse-to-groove, ch3 full groove, ch4 low pad,
  ch5-6 iteration build, ch7 peak, ch8 warm close). All instrumental, ACE-Step via Song Forge, 92 to 104 BPM
  as marked. Health-check Song Forge (`127.0.0.1:8767/api/status`) before rendering anything heavy.
- Viewer recordings: `_scripts/rec.mjs` and `rec_realtime.mjs` record the HTML viewers headless to MP4.
  Record `viewer-turn-radius.html` and `corner-simple.html` the same way.
- Per-part ETA before any render, per the house rule.
- QC: `film_qc.py` on the finished cut with a manifest before anything is called done.
