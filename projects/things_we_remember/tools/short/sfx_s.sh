#!/bin/bash
P=~/Desktop/PROJECTS/story-forge/projects/things_we_remember; cd $P
S=~/Desktop/PROJECTS/story-forge/bin/make-sfx
g() { [ -s audio/sfx/$1.wav ] || $S "$2" --seconds $3 --seed $4 --out audio/sfx/$1.wav --negative "music, speech, singing" >> audio/sfx.log 2>&1; echo "SFX $1 $(date +%T)" >> audio/sfx.log; }
g drawer "a wooden dresser drawer slid shut with a soft thud, quiet bedroom" 2 31
g plate "a ceramic dinner plate set down gently on a wooden table, a soft clink" 2 32
g crayon "a child coloring with a wax crayon on paper on a wooden table, soft scratching" 4 33
g giggle "a small boy giggling softly, far away in another room, gentle and echoing" 3 34
echo SFX_S_DONE >> audio/sfx.log
