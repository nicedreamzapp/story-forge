#!/bin/bash
cd "$(dirname "$0")/.."; SFX=~/Desktop/PROJECTS/story-forge/bin/make-sfx
gen() { [ -f "sfx/$1.wav" ] || $SFX "$2" --seconds $3 --out "sfx/$1.wav" --seed 7 --negative "music, speech, voices, talking, alarm, siren, beep, electronic tone" >> sfx/batch.log 2>&1; echo "$(date +%T) $1" >> sfx/batch.log; }
gen dog_sniffs "a bloodhound sniffing the ground, a series of short wet nose sniffs, close, quiet night" 4
gen whistle_two_note "a person's two-note shepherd whistle, short, distant, outdoors at night, one time" 1.5
gen lantern_creak "a soft metal lantern handle creaking as it swings, quiet, slow" 3
gen fox_yips "a small fox yipping in distress, quick high yips, outdoors at night" 3
gen wire_twang "an old wire fence creaking under strain then twanging loudly as strands snap apart" 2.5
gen dog_barks "a bloodhound barking, deep baying barks, three barks, outdoors at night" 3
gen paws_running "a dog running fast on a dirt road, quick paw steps on dirt, outdoors" 4
gen tail_thumps "a dog's tail thumping softly against dry leaves and ferns, three soft thumps" 3
gen paws_walking "two animals walking slowly away on a dirt road, soft paw steps, quiet night" 4
gen morning_birds "morning songbirds in oak trees, gentle dawn chorus, calm" 6
echo "$(date +%T) sfx v4 done" >> sfx/batch.log
