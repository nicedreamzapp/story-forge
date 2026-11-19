#!/bin/bash
cd "$(dirname "$0")/.."; SFX=~/Desktop/PROJECTS/story-forge/bin/make-sfx
gen() { [ -f "sfx/$1.wav" ] || $SFX "$2" --seconds $3 --out "sfx/$1.wav" --seed 7 --negative "music, speech, voices, talking, alarm, siren, beep, electronic tone" >> sfx/batch.log 2>&1; echo "$(date +%T) $1" >> sfx/batch.log; }
gen wind_mountain "soft natural wind over a high mountain ledge at dawn, gentle airy breeze, distant, calm" 10
gen crickets_night "quiet night forest ambience, real crickets chirping softly in the distance, calm, natural" 14
gen marmot_chirp "one short soft natural marmot chirp whistle, a quick two-note animal call, outdoors, not shrill" 1.5
gen tuba_note "one single soft low tuba note, short, warm, comedic, played once" 1.5
echo "$(date +%T) sfx v3 done" >> sfx/batch.log
