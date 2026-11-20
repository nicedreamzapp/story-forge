#!/bin/bash
P=~/Desktop/PROJECTS/story-forge/projects/things_we_remember; cd $P
until grep -q CLIPS_DONE clips_trailer.log; do sleep 10; done
L=~/Desktop/PROJECTS/story-forge/bin/make-ltx25
LOOK="cinematic horror film, slow and quiet, natural motivated light stays the same"
t0=$(date +%s)
out=$($L --i2v stills/t10_b.png --duration 3 --res 1024x576 --low-ram --gb 26 --seed 1810 --label twr-t10 "the woman's hand quickly pulls the patchwork quilt back off the small bed, revealing that the bed is completely empty, nobody is there, only a dent in the pillow, the moonlight stripes stay still, the camera holds still, $LOOK" 2>&1 | tee -a clips_t10.log | grep -o '→ .*mp4' | tail -1 | sed 's/→ //')
[ -s "$out" ] && cp "$out" clips/t10.mp4 && echo "CLIP t10 ok $(date +%T)" >> clips_trailer.log || echo "CLIP t10 FAILED2" >> clips_trailer.log
echo "{\"shot\": \"twr_trailer_t10\", \"step\": \"i2v_ltx25_lowram_3s\", \"seconds\": $(( $(date +%s) - t0 ))}" >> ~/Desktop/PROJECTS/story-forge/METRICS.jsonl
echo T10_DONE >> clips_trailer.log
