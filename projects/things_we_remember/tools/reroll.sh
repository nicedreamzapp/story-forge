#!/bin/bash
P=~/Desktop/PROJECTS/story-forge/projects/things_we_remember; cd $P
until grep -q CLIPS_DONE clips.log; do sleep 5; done
L=~/Desktop/PROJECTS/story-forge/bin/make-ltx25
out=$($L --i2v stills/s06_a.png --duration 5 --res 1024x576 --low-ram --gb 26 --seed 62 --label twr-s06r "camera locked off and perfectly still. the silver fork on the dinner plate in front of the empty chair moves by itself: it slowly turns and slides across the plate toward the empty chair, as if an invisible hand is picking it up. nobody touches it, the chair stays empty, the warm hanging lamp flickers once, quiet horror film" 2>&1 | tee -a clips.log | grep -o '→ .*mp4' | tail -1 | sed 's/→ //')
[ -s "$out" ] && cp "$out" clips/s06_r.mp4 && echo "CLIP s06_r ok $(date +%T)" >> clips.log || echo "CLIP s06_r FAILED" >> clips.log
echo REROLL_DONE >> clips.log
