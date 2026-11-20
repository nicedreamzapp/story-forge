#!/bin/bash
# foley via MMAudio (text-to-audio), one at a time after the stills batch
P=~/Desktop/PROJECTS/story-forge/projects/things_we_remember; cd $P
while pgrep -f "zimage_batch.py $P/stills_jobs" >/dev/null; do sleep 5; done
S=~/Desktop/PROJECTS/story-forge/bin/make-sfx
g() { [ -s audio/sfx/$1.wav ] || $S "$2" --seconds $3 --seed $4 --out audio/sfx/$1.wav --negative "music, speech, singing" >> audio/sfx.log 2>&1; echo "SFX $1 $(date +%T)" >> audio/sfx.log; }
g glass "a single drinking glass falls and shatters on a hard kitchen tile floor, close, dry room" 3 11
g laugh "a family laughing together warmly at a dinner table, adults and a little girl, indoors, home video" 8 12
g rain "gentle rain tapping on a kitchen window, quiet indoor room tone" 10 13
g heart "slow deep human heartbeat, low thumping, close" 8 14
g creak "old wooden farmhouse floorboards creaking slowly upstairs at night, quiet house" 5 15
g fork "a metal fork slowly scraping across a ceramic dinner plate, quiet room" 3 16
g room "quiet empty farmhouse kitchen at night, faint refrigerator hum, clock ticking softly" 10 17
echo SFX_DONE >> audio/sfx.log
