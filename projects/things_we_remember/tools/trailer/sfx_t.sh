#!/bin/bash
# trailer foley via MMAudio (same as tools/sfx.sh), after the stills batch
P=~/Desktop/PROJECTS/story-forge/projects/things_we_remember; cd $P
while pgrep -f "zimage_batch.py $P/stills_jobs" >/dev/null; do sleep 5; done
S=~/Desktop/PROJECTS/story-forge/bin/make-sfx
g() { [ -s audio/sfx/$1.wav ] || $S "$2" --seconds $3 --seed $4 --out audio/sfx/$1.wav --negative "music, speech, singing" >> audio/sfx.log 2>&1; echo "SFX $1 $(date +%T)" >> audio/sfx.log; }
g car "a car slowly rolling up a wet gravel driveway in light rain and stopping, engine idling then turning off" 5 21
g steps "a small child running quickly up a wooden staircase, light fast footsteps, giggling fading away upstairs, indoors" 3 22
g quilt "a heavy cotton quilt pulled back quickly from a bed, fabric rustle, quiet bedroom at night" 2 23
g click "the mechanical click of an old cassette tape recorder play button pressed, then soft tape hiss and motor whir" 4 24
g party "a small family birthday party in a living room, adults and children laughing and clapping, recorded on an old cassette" 8 25
g garden "a sunny backyard garden in summer, birds singing, distant lawnmower, light breeze, outdoors" 8 26
g birds "soft morning birdsong outside a farmhouse window after rain, gentle and calm" 8 27
echo SFX_DONE >> audio/sfx.log
