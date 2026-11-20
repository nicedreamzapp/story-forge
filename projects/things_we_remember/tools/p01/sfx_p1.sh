#!/bin/bash
P=~/Desktop/PROJECTS/story-forge/projects/things_we_remember; cd $P
S=~/Desktop/PROJECTS/story-forge/bin/make-sfx
g() { [ -s audio/sfx/$1.wav ] || $S "$2" --seconds $3 --seed $4 --out audio/sfx/$1.wav --negative "music, speech, singing" >> audio/sfx.log 2>&1; echo "SFX $1 $(date +%T)" >> audio/sfx.log; }
g wipers "car windshield wipers sweeping slowly back and forth in rain, inside a quiet car, engine hum" 8 41
g screen "an old wooden screen door creaking open on a porch, rain" 2 42
g drip "slow water drops dripping one by one onto a wooden floor in a quiet dark house" 6 43
echo SFX_P1_DONE >> audio/sfx.log
