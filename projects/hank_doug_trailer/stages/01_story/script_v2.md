# HANK & DOUG'S WILD RESCUE — 60-second trailer, script v2 (one canvas, painted by the call)
Written 2026-11-17 (stage 01, writing only). 15 beats, 0:00-1:00, ONE unbroken travelling shot. Painted look
per look_test/PREFIX.txt (pure matte-painting oil). Spoken lines: 5 short (plus 1 narrator). On-camera mouths: 2
(beats 10 and 14). v1 script.md is untouched and stays as the fallback cut.

## How the one-shot is built (for stages 02-05)
Every beat is a Krea still (or a 5 s image-to-video clip grown from one). The camera never cuts; it TRAVELS.
Three code-rendered layers make that possible, all over existing frames, none needing a model:
- **UNPAINTED state** of any still: desaturate, multiply by a linen canvas weave, edge-detect lines as faint
  pencil. Derived from the finished still, so the grey and the colour are the same pixels (no identity drift).
- **RIPPLE + REVEAL:** a ring of thick wet paint (brush-texture stroke, ochre and white) expands from the mouth of
  whoever calls; a stroke-edged matte grows with it and reveals the full-colour still inside the ring. Ring size
  is the loudness: goat bleat medium, marmot whistle big (two rings), kitten mew tiny, chipmunk squeak tiniest.
- **WHIP-PAN JOINS:** the camera rides the ripple from one still to the next with a motion-blurred whip (camera
  token, quintic ease, 6 sub-frame blur). The join between two stills sits inside the blur. Other joins hide under
  a full-frame pass (the goose flock, the elephant spray, a tree trunk, dusk). No panorama stitching, no outpainting.
- **OLD PAINT (beats 9-11):** craquelure overlay, varnish-yellow grade, cooler and darker. Heals under the "Hi." bloom.
- **LEADING EDGE (beats 4, 12):** during a travel the world ~300 px ahead of the subject is still linen and paints
  in just before the camera reaches it (Opus's wet-edge idea, used only where the wagon or the pair is moving).
Timeline is a pure function of time (seek(t)); ripple times are the sound-event list. Remotion/ffmpeg finish.

## Rules this script is built on (v1 rules kept)
Trouble on screen before any signal; one read at a time; small cast per shot; one design string per character,
reused word for word, no added adjectives; a spoken time marker on the flashback; NO humans, hands, boots, guns,
text (except the title); pulling shots in clean side profile, one wagon, the only vehicle; light sources named only
in the beats that need them (the lantern).

---

## Beat list (one continuous shot; "STILL+MOVE" = code camera over a painted still, "CLIP" = 5 s image-to-video,
## "TALK" = image-to-video with a prompted mouth, "CODE" = a code-rendered layer on top)

### 0 · 0:00-0:03 (3 s) · THE LINEN · STILL+CODE
**Picture.** Raw linen canvas filling the frame, a few faint pencil lines: a mountain face, a ledge, and on it a
pencil-grey GOAT, four feet bunched, head turned down toward us, mouth open. Nothing else. Then the bleat: a ring
of wet ochre-and-white paint pushes out from her open mouth, and inside the ring the rock, the dawn light and the
white goat arrive in full colour. Pebbles trickle off the ledge (hand-painted 3-frame flicker, code).
**Reads.** 1. the blank canvas and the pencil goat 2. the bleat 3. the paint ring brings the colour
**Sound.** Wind on linen (dry, close). One long wobbly bleat. A soft wet "shhk" as the ring spreads. No music.
**Sentiment.** "Wait, what is happening." A lean-in.
**Assets.** Still A (goat on the ledge, environment + goat). Unpainted state derived in code.

### 1 · 0:03-0:06 (3 s) · THE RIPPLE RUNS DOWN THE MOUNTAIN · STILL+MOVE (whip A→B)
**Picture.** The ring keeps going, the camera rides it: a whip-tilt down the grey rock face, the valley colouring
in under the ring as it passes (sage green meadow, slate-blue haze). The whip lands on a sun-warmed boulder in
the meadow where MARMOT sits hunched chewing a stem, the last pencil-grey thing in frame; the colour reaches her
and her head snaps up.
**Reads.** 1. the ring runs down and paints the valley 2. it reaches the marmot 3. her head snaps up
**Sound.** The bleat fades into the "shhk" of the moving ring. Chewing stops.
**Assets.** Still A (bottom half) and Still B (marmot boulder, mountain soft behind). Join hidden in the whip blur.

### 2 · 0:06-0:09 (3 s) · THE WHISTLE · STILL+MOVE (whip B→C)
**Picture.** MARMOT rises tall on her hind legs, chest out, and whistles, mouth a small round O. Two big rings burst
from her, twice the goat's size, and the camera whips along them across the meadow, down to a dirt road under oaks,
painting the road as it goes.
**Reads.** 1. she stands tall 2. the whistle, two big rings 3. the camera rides them to the road
**Sound.** One piercing marmot whistle, very loud. Ring "shhk", doubled.
**Assets.** Still B (marmot standing; the still is painted standing, the "sits then stands" is sold by the ripple
arrival + a 2-frame hold on a crouched crop; if stage 04 wants a true rise, swap B for a 5 s CLIP).

### 3 · 0:09-0:13 (4 s) · THE BENCH · STILL+MOVE (push)
**Picture.** The rings arrive at WAGON parked on the road under oaks, morning light, and the paint floods it red
with ochre trim. Medium two-shot from the road side, three-quarter front: DOUG left, his long ears already lifted
and swung toward where the sound came from; HANK right, face turned down the road in profile, his big paw closing
around the reins. On the iron hook on the wagon's front post, beside Hank, hangs the dented brass LANTERN,
unlit. Slow push in on the paw and the reins. Hank's mouth, in profile, moves once.
**Reads.** 1. the paint floods the wagon 2. Doug's ears up 3. Hank's paw on the reins 4. "Rolling."
**Line.** HANK (low, unhurried, almost a yawn): "Rolling."
**Sound.** The whistle tails off. A banjo roll starts under the word and runs into beat 4.
**Sentiment.** A grin: these two have done this a hundred times.
**Assets.** Still C. Hank in profile so the one word needs no mouth clip; stage 04 may upgrade C to a TALK clip
if the profile mouth reads badly (optional 3rd talking clip).

### 4 · 0:13-0:18 (5 s) · ROLLOUT, THE THEME HITS · CLIP + CODE leading edge
**Picture.** Wide, clean side profile, camera low beside the road through rolling sage-green hills (the look-test
composition). Left to right: TEAM in a single line (horse, zebra, camel, cow), WAGON with HANK and DOUG small on the
bench and the LANTERN swinging on its hook, the two GIRAFFES jogging on the far side at the back, the two
ELEPHANTS behind with oak barrels. The wagon rolls right; the camera tracks with it; ahead of the horse's nose the
road and hills are still linen and paint in just before the team reaches them. Dust behind the wheels.
**Reads.** 1. the team pulling 2. the world painting in ahead of them 3. the giraffes and elephants with it
**Narrator** (warm, storybook): "Somebody always hears the call."
**Sound.** THEME SONG verse 1 full on the first frame. Hooves, wheels, one elephant bellow.
**Sentiment.** Joy. "Here comes the cavalry."
**Assets.** Still D (the look-test rollout frame or its re-render with the lantern) grown into a 5 s CLIP (wagon
rolls right, wheels turn, dust); leading-edge matte in code. must_not: loose animals, a second wagon, more heads than
bodies, a two-humped camel.

### 5 · 0:18-0:22 (4 s) · GOAT AIRLIFT · CLIP
**Picture.** The camera tilts up the grey mountain face as a flat wooden PLATFORM rises on four ropes held in the
beaks of a dozen GEESE, wings beating; it comes level with the ledge; GOAT steps on, front hooves first, then all
four; the platform dips and holds. The goose flock crossing frame at the top of the tilt is the join from beat 4.
**Reads.** 1. the platform rising on ropes 2. the geese holding the ropes 3. the goat steps on
**Sound.** Verse 1 continues. Wing beats, one happy short bleat.
**Assets.** Still L (ledge, platform, geese, goat) grown into a 5 s CLIP (platform rises, goat steps).

### 6 · 0:22-0:27 (5 s) · TURTLE · STILL hold + CLIP
**Picture.** The camera comes down off the mountain onto a shrunken pond, edge cracked, drying mud. TURTLE sunk to
the rim of his shell, legs paddling and going nowhere. Hold (1.5 s). Two long grey ELEPHANT trunks swing in from
the left and right edges and spray two arcs of water into the mud; each arc leaves a wet slate-blue brush stroke
hanging in the air for a beat (code); the mud darkens, rises, the turtle lifts off the bottom and floats. Only
the trunks and the front of each elephant's head enter frame.
**Reads.** 1. the turtle stuck 2. the trunks swing in and spray 3. the water rises 4. he floats
**Sound.** CHORUS hits on the first frame ("Hank and Doug!"). Squelch, two big sprays, "SPLOOSH" on the second
arc if the cut allows.
**Sentiment.** Worry, then a laugh of relief.
**Assets.** Still E (turtle stuck, pond) held, then grown into a 5 s CLIP (trunks in, spray, float), trimmed.
The spray fills frame at its peak = the join into beat 7.

### 7 · 0:27-0:30 (3 s) · KITTEN, THE TINIEST RING · STILL+MOVE (push)
**Picture.** Close, straight down through an iron storm-drain GRATE in cobblestones at the edge of a quiet lane
(no people, no vehicles, no signs). Two meters down, tiny KITTEN looks up, mouth open in a mew, a shallow puddle
around her paws. From her mouth the smallest paint ring in the film, no bigger than her head, rises up the
drain shaft and out through the bars, and the cobbles around the grate take their colour from it.
**Reads.** 1. the grate 2. the kitten far below 3. her mew, the tiniest ring, and it still gets out
**Sound.** Chorus continues. One tiny mew, echoing up. A very small "shhk".
**Sentiment.** Tenderness. "Even that small, somebody hears."
**Assets.** Still F.

### 8 · 0:30-0:34 (4 s) · THE OTTER CHAIN · CLIP
**Picture.** Medium, eye level with the cobbles, the GRATE flipped open beside the hole. A chain of four OTTERS
hangs into the drain, each holding the next one's hind feet; the top otter's hind feet held by HANK's two big paws
at the top of frame (only his forearms and paws, dark chocolate-brown fur). The bottom otter comes up out of the
hole holding KITTEN gently by the scruff, eyes wide, legs dangling.
**Reads.** 1. the otter chain 2. the kitten lifted out 3. Hank's paws anchoring the top
**Sound.** Chorus continues. Otter chirps, the small mew, a soft rumble (no words).
**Sentiment.** "Yes!"
**Assets.** Still M grown into a 5 s CLIP (chain hauls up, kitten rises). The camera then drifts right off the
lane toward the forest edge; a dark tree trunk wipes the frame = the join into beat 9.

### 9 · 0:34-0:39 (5 s) · THE OLD PAINT (flashback, no cut) · STILL+MOVE + CODE crackle
**Picture.** The camera keeps travelling along the road into the trees and the paint under it changes: older,
varnish-yellowed, a web of fine cracks, the colour draining to cold silver-blue night. This is the same road, further
on. Night forest in moonlight. DOUG (same design, a little smaller) moves nose-down along a trail toward camera-left;
from off-frame right behind him a warm amber lantern glow spills across the ground and the trunks, following him;
no lantern and no one holding it is visible. He stops; his head lifts. Ahead, half behind a fallen log, crouches
YOUNG HANK, eyes wide, ears flat. Slow push along Doug's trail.
**Reads.** 1. the road goes old and dark 2. Doug tracking, nose down 3. the glow following him 4. he stops
5. the frightened bear behind the log
**Line.** DOUG (V.O., quiet, older, telling it): "Long time ago... I hunted bears."
**Sound.** The song drops to the music-box breakdown. Crickets. Doug's sniffing.
**Sentiment.** Hush. "Wait, Doug was a hunter?"
**Assets.** Still G. must_not: a visible lantern, a hand, a person, a boot, a gun. Crackle + grade in code.

### 10 · 0:39-0:43 (4 s) · "HI." · TALK + CODE bloom
**Picture.** Close two-shot in moonlight over the top of the log, side-on, old cracked paint: DOUG's face left,
YOUNG HANK's right, noses almost touching. The bear's eyes wide and scared. A long beat. His mouth moves, one small
word. On the word, warm colour blooms outward from the two noses, russet and chocolate-brown and sage, and the
cracks heal under it; it is the first fresh paint in this part of the canvas. Doug's eyes soften; behind him his
tail starts to wag (last read).
**Reads.** 1. nose to nose, cracked and cold 2. "Hi." 3. the colour blooms from the noses 4. Doug's tail wags
**Line.** DOUG (V.O., before the bear speaks): "Then I met one."
**Line.** YOUNG HANK (small, hopeful, on camera): "Hi."
**Sound.** Music box only. Crickets, a long beat, "Hi.", then one warm chord as the colour arrives.
**Sentiment.** The catch in the throat.
**Assets.** Still N grown into a TALK clip (one word, one mouth, then the tail). Bloom + crack-heal in code over it.

### 11 · 0:43-0:46 (3 s) · THE DITCH · STILL+CODE (lantern animated as a cutout)
**Picture.** The camera drifts right off the pair to the roadside DITCH at the forest edge, low and wide. The
dented brass LANTERN, alone, tumbles end over end into frame from above-right, lands in the mud with a splash,
hisses and goes dark; the warm glow that has been on the trunks goes out with it and the frame is moonlight only.
Nothing and no one else is in frame; the road runs away into the background.
**Reads.** 1. the lantern falls 2. the splash 3. the light goes out
**Sound.** Music box. A clank, a splash, a hiss. Then just crickets.
**Sentiment.** "He chose the bear."
**Assets.** Still H1 (empty ditch plate, environment-only prefix) + Still H2 (the lantern on its own, cut out) flown
on a code parabola with rotation; splash is a 4-frame painted splash; the glow-out is a grade key. No model clip
here on purpose: a model is where a hand would appear.

### 12 · 0:46-0:49 (3 s) · WALKING AWAY, AND THE PAINT FOLLOWS · STILL+MOVE (pull back and rise)
**Picture.** Wide from behind, the moonlit road into silver hills. DOUG and YOUNG HANK walk away side by side, the
bear a head taller, Doug's tail up. Ahead of them the road is still old and dark, and fresh colour runs up it just
ahead of their feet (leading edge), the night thinning toward a warm sky at the top of frame. The camera pulls
back and rises, leading them.
**Reads.** 1. the two walking away together 2. the colour running up the road ahead of them 3. Doug's tail
**Line.** DOUG (V.O., warm): "Same nose. Same light. Different job."
**Sound.** Chorus 2 builds from "Nobody's too big...".
**Sentiment.** Warmth.
**Assets.** Still I. Optional upgrade to a 5 s CLIP (walk cycle) if the still pull-back reads dead at stage 05.

### 13 · 0:49-0:54 (5 s) · TITLE · STILL+CODE
**Picture.** The rise clears the last trees onto a warm ochre-and-rust sunset over sage-green hills; on the
hilltop the WAGON in dark silhouette with the team and the two giraffes in profile, a tiny amber point of light on
the wagon's front post. The title paints itself in, stroke by stroke, hand-lettered storybook style, two lines:
"HANK & DOUG'S" over "WILD RESCUE". The only text in the trailer.
**Reads.** 1. the silhouette and the small light 2. the title (25 chars: 3.2 s minimum fully visible; it is fully
painted by 1.2 s and holds 3.8 s)
**Sound.** "It's Hank and Doug's Wild Rescue!" lands on the first stroke. Final chord.
**Sentiment.** Pride. Singing along.
**Assets.** Still J (environment + silhouette, no text). Lettering is a code-rendered brush-font layer with a stroke
reveal matte, never model-generated text.

### 14 · 0:54-1:00 (6 s) · BUTTON · TALK
**Picture.** The camera comes down the hill to under a big oak at golden sunset: WAGON parked, everyone asleep in a
pile. HANK slumped on the bench, head back, mouth slightly open. DOUG sprawled across Hank's lap, ears to the
floorboards. One GIRAFFE neck droops over the wagon from behind. MARMOT curled on top of Hank's head. On the front
post the dented brass LANTERN, lit, warm amber, the one light in the dusk. Hold on the quiet. CHIPMUNK pops up onto
the rim of the near wheel in the foreground and squeaks: the tiniest paint ring of the film, a thumbnail of ochre.
Doug's ears shoot straight up, eyes wide. Hank's eyes stay shut; only his mouth moves.
**Reads.** 1. the sleeping pile and the lit lantern 2. the chipmunk pops up, the tiny ring 3. Doug's ears
4. Hank speaks without opening his eyes
**Line.** HANK (eyes closed, flat, immediate): "Rolling."
**Sound.** Silence after the title chord. One sharp squeak. A beat. One soft tuba note on "Rolling.", then the
2-second sting "Rollin'! Here we go!" and the cut to black.
**Sentiment.** A laugh. "I want more."
**Assets.** Still K grown into a TALK clip (chipmunk pops, ears up, one word with eyes shut). Ring in code.

---

## Spoken lines (5 short, plus 1 narrator)
1. HANK (beat 3): "Rolling."
2. DOUG, V.O. (beats 9-10): "Long time ago... I hunted bears. Then I met one."
3. YOUNG HANK (beat 10): "Hi."
4. DOUG, V.O. (beat 12): "Same nose. Same light. Different job."
5. HANK (beat 14): "Rolling."
Narrator (beat 4): "Somebody always hears the call."
Mouth motion needed only in beats 10 and 14 (beat 3 optional). Voices per `voices/cast.md`: wr3_hank / wr3_doug;
Young Hank = the Hank voice pitched a little higher and softer, never a new voice.

## Theme song
Lyrics unchanged (theme_song.md). Cue map for this cut: 0:00-0:09 no music; 0:09-0:13 pickup (banjo roll, "Rollin',
rollin', here we go!" lands on Hank's "Rolling." at ~0:12); 0:13-0:22 verse 1; 0:22-0:34 chorus; 0:34-0:46 music-box
breakdown (one warm chord added at the "Hi." bloom, ~0:41); 0:46-0:54 chorus 2 from "Nobody's too big...", last line
on the first title stroke at 0:49; 0:54-1:00 silence, tuba note, 2 s sting.

## Asset counts (for the per-part ETA)
- **Krea stills: 15** (A ledge+goat, B marmot, C bench, D rollout, E turtle stuck, F drain, G forest flashback,
  H1 ditch plate, H2 lantern cutout, I walk away, J title hill, K sleeping pile, L geese platform, M otter chain,
  N nose to nose). Unpainted states, rings, crackle, title and the lantern fall are code, not stills.
- **Image-to-video CLIPS (~5 s): 4** (D rollout, L airlift, E spray, M otter chain). Optional 5th: I walk cycle.
- **TALK clips: 2** (N "Hi.", K "Rolling."). Optional 3rd: C bench.
- **Code layers:** unpainted derivation (all stills), ripple/reveal (beats 0,1,2,3,7,10,14), whip-pan joins (3),
  leading edge (4, 12), crackle + grade (9-11), lantern parabola + splash (11), title strokes (13).

## Character design sheet (reuse WORD FOR WORD; never add adjectives)
**Style prefix (every shot):** the text of look_test/PREFIX.txt, word for word.
**Environment-only prefix (A before the goat, F before the kitten, H1, J plate):** same, plus "empty of characters
and creatures, no animals".

| Name | Design string (fixed) | Color lock |
|---|---|---|
| HANK | Hank, a huge round gentle grizzly bear with thick dark chocolate-brown fur painted as soft dense brush marks, a lighter tan muzzle, small round ears, kind dark-brown eyes, no clothing, no collar, no hat; smooth dense fur, no feather shapes, no wings | body dark chocolate brown; muzzle tan; eyes dark brown |
| YOUNG HANK (beats 9-12) | the same string as Hank, then: "a little smaller and rounder than full-grown" | identical to Hank |
| DOUG | Doug, a sturdy heavy-built bloodhound with a deep chest, one solid russet-red coat all over, very long droopy velvet ears in the same russet a shade darker, deep wrinkles over his forehead, droopy eyes, a big black nose, a worn dark-brown leather collar with one small brass ring; no black saddle, no white legs, no white chest | coat russet red; ears darker russet; collar dark brown; nose black |
| WAGON | a big red-painted wooden fire-wagon with ochre-gold trim on four huge spoked wooden wheels with iron rims, a plank bench up front, a dented old brass hand lantern hanging from an iron hook on the front post beside the bench, a coiled canvas hose and a brass hand-pump lever at the back, no engine, no tires, no cab, no roof | body red; trim ochre gold; wheels natural wood with dark iron rims; lantern brass |
| TEAM | a single line of four harnessed animals pulling in front of the wagon, nose to tail: one chestnut horse, one black-and-white striped zebra, one tan one-humped camel, one black-and-white dairy cow, all in brown leather harness; four heads, four bodies | as named |
| GIRAFFES | two tall friendly reticulated giraffes with orange-brown patch patterns on cream, short ossicone horns, long dark lashes | orange-brown on cream |
| ELEPHANTS | two big friendly grey African elephants with huge ears, each carrying an oak water barrel strapped on its back | slate grey; barrel oak brown |
| GOAT | a small white nanny goat with short grey horns, a little white beard and grey knees | white; horns and knees grey |
| MARMOT | a plump yellow-brown marmot with a cream belly, small round ears and buck teeth | yellow brown; belly cream |
| GEESE | a dozen big white domestic geese with orange beaks and feet | white; beaks orange |
| TURTLE | a green-brown pond turtle with a yellow-striped neck and a domed shell | shell green brown; neck stripes yellow |
| KITTEN | a tiny grey tabby kitten with big round green eyes and a pink nose | grey with darker grey stripes; eyes green |
| OTTERS | four sleek dark-brown river otters with pale throats and long tapered tails | dark brown; throats pale |
| CHIPMUNK | a small chipmunk, orange-brown with five dark stripes down its back and white cheeks | orange brown; stripes dark; cheeks white |
| LANTERN (prop; glow only in 9, the object in 3, 4, 11, 13, 14) | a dented old brass hand lantern with a glass panel, warm amber flame | brass; amber light |

Only change from the v1 sheet: the lantern added to the WAGON string and "dented old" added to the LANTERN string
so the ditch lantern and the wagon lantern are the same object.

**Cast per beat.** 0-1 goat · 1-2 marmot · 3 Doug, Hank, wagon, lantern · 4 team, wagon, Hank, Doug small,
giraffes, elephants · 5 goat, geese, platform · 6 turtle, two trunks · 7 kitten · 8 otters, kitten, Hank's paws ·
9 Doug, Young Hank · 10 Doug, Young Hank · 11 lantern only · 12 Doug, Young Hank · 13 wagon silhouette, team,
giraffes · 14 Hank, Doug, wagon, lantern, giraffe neck, marmot, chipmunk.

---

## Story test (from the picture ALONE, no lines, no song)
A blank canvas with a pencil goat on a ledge; she bleats and the world around her colours in like wet paint. The
colour runs down the mountain to a marmot, who whistles, and the colour runs down to a parked wooden wagon where a
bloodhound's ears go up and a bear already has the reins. The wagon rolls out behind a horse, a zebra, a camel and
a cow, the road painting itself in front of them, giraffes and elephants alongside. Geese lift a goat off her ledge.
A turtle stuck in mud floats free when elephants spray water. A kitten mews from the bottom of a drain, the smallest
ripple yet, and a chain of otters hauls her up with the bear holding the top. The road goes into dark trees and the
paint gets old and cracked: the same dog, younger, is tracking with a light behind him and finds a scared bear
behind a log. The bear says one word and colour blooms over both of them and the cracks heal. A lantern falls in a
ditch and goes out. The dog and the bear walk away down a road that colours in ahead of them, up into a sunset where
the title paints itself over the wagon. Under an oak everyone sleeps with a lantern lit on the wagon; a chipmunk
squeaks a tiny ring; the dog's ears shoot up and the bear answers without opening his eyes.

**Against the premise.** The switch is shown (tracking with the hunter's light, the meeting, the light in the ditch,
leaving together) and given a cause a kid can see (the bear's word brought the colour). "Nobody too small" is shown
four times in paint (goat, marmot, kitten, chipmunk; the rings get smaller and still travel). Every rescue shows the
trouble first. No humans anywhere. The lantern on the wagon is planted in 3 and 4 before it falls in 11 and is lit in
13 and 14. Holds.

**Gaps checked.** Fur: Hank's string keeps "no feather shapes, no wings". Colour drift: colour locks unchanged, and
the grey/colour states are the same pixels. Extra creatures: must_not on every multi-animal still. One-shot risk:
every join is listed with the device that hides it (whip, flock, spray, trunk, dusk); if a join fails, v1's straight
cut at that point is the fallback with no other change.
