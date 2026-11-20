#!/bin/bash
P=~/Desktop/PROJECTS/story-forge/projects/things_we_remember; cd $P
until grep -q T10_DONE clips_trailer.log; do sleep 10; done
L=~/Desktop/PROJECTS/story-forge/bin/make-ltx25; t0=$(date +%s)
out=$($L --i2v stills/t03_a.png --duration 3 --res 1024x576 --low-ram --gb 26 --seed 1311 --label twr-t03r "the little girl keeps running up the stairs away from the camera and turns the corner at the top landing out of sight, she is gone, then the staircase is empty and still, the camera holds on the empty stairs, cinematic horror film, slow and quiet, natural motivated light stays the same" 2>&1 | tee -a clips_t03r.log | grep -o '→ .*mp4' | tail -1 | sed 's/→ //')
[ -s "$out" ] && cp "$out" clips/t03_r1.mp4 && echo "CLIP t03_r1 ok $(date +%T)" >> clips_trailer.log || echo "CLIP t03_r1 FAILED" >> clips_trailer.log
echo "{\"shot\": \"twr_trailer_t03r\", \"step\": \"i2v_ltx25_lowram_3s\", \"seconds\": $(( $(date +%s) - t0 ))}" >> ~/Desktop/PROJECTS/story-forge/METRICS.jsonl
echo T03_DONE >> clips_trailer.log
