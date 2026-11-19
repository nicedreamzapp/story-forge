#!/bin/bash
# designed SFX for the ripple cues (MMAudio via bin/make-sfx; one load per call, it gates itself on Song Forge + memory)
cd "$(dirname "$0")/.."; mkdir -p sfx
SFX=~/Desktop/PROJECTS/story-forge/bin/make-sfx
gen() { [ -f "sfx/$1.wav" ] || $SFX "$2" --seconds $3 --out "sfx/$1.wav" --seed 7 --negative "music, speech, voices, talking" >> sfx/batch.log 2>&1; echo "$(date +%T) $1" >> sfx/batch.log; }
gen goat_bleat "one long wobbly bleat of a single nanny goat, close, outdoors on a mountain, dry air" 3
gen marmot_whistle "one very loud piercing marmot alarm whistle, a single sharp high whistle, alpine meadow" 2
gen kitten_mew "one tiny kitten mew, high and small, echoing up a stone drain shaft" 2
gen chipmunk_squeak "one sharp tiny chipmunk squeak, very short, close" 1.5
gen paint_shhk "a soft wet brush stroke dragging thick oil paint across canvas, a wet shhk" 2
gen wing_beats "a dozen big geese wings beating heavily, flapping, close" 4
gen water_spray "two elephant trunks spraying big arcs of water onto thick mud, splashing, squelch" 4
gen lantern_fall "a brass lantern clanks and tumbles, lands in a muddy puddle with a splash, then a short hiss of a flame going out" 3
gen hooves_wheels "horse hooves and heavy wooden wagon wheels rolling on a dirt road, a team pulling, dust" 5
gen otter_chirps "small river otters chirping and squeaking, playful, close" 3
echo "$(date +%T) sfx batch done" >> sfx/batch.log
