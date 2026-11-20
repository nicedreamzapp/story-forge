#!/bin/bash
cd ~/Desktop/PROJECTS/story-forge/projects/blackout/avatar
export AUDIO_STRENGTH=0.5 H=736 W=544
S=$(date +%s)
~/Desktop/PROJECTS/avatar-assets/longcat/render_clip.sh $PWD/matt_cabin.png $PWD/a2_line.wav $PWD/a2.mp4 $PWD/p_a2.txt
echo "$(date '+%F %T') A2 LongCat actual $(( $(date +%s)-S ))s" >> ../ETA.log
S=$(date +%s)
~/Desktop/PROJECTS/avatar-assets/longcat/render_clip.sh $PWD/matt_cabin.png $PWD/a1_silent.wav $PWD/a1.mp4 $PWD/p_a1.txt
echo "$(date '+%F %T') A1 LongCat actual $(( $(date +%s)-S ))s" >> ../ETA.log
