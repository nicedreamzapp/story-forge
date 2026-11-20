#!/bin/bash
# LatentSync twin (make_twin.sh, fast preset) per on-camera block, then mouthfix; one at a time as inputs appear.
P=~/Desktop/PROJECTS/story-forge/projects/lahontan_returns; cd $P/lips
MT=~/Desktop/PROJECTS/avatar-assets/lipsync/scripts/make_twin.sh; MF=~/Desktop/PROJECTS/avatar-assets/mouthfix
for b in "AN1 anchor" "REP reporter" "SCI sci" "RES res" "AN2 anchor" "AN3 anchor"; do set -- $b
  [ -s $1.mp4 ] && continue
  until [ -s ${1}_a.wav ] && [ -s ../clips/$2.mp4 ]; do sleep 5; done
  [ -f ../tools/t_lips_start ] || date +%T > ../tools/t_lips_start
  echo "$1 start $(date +%T)" >> lips.log
  bash $MT ../clips/$2.mp4 ${1}_a.wav ${1}_raw.mp4 > $1.log 2>&1 </dev/null
  (cd $MF && .venv/bin/python -I mouthfix.py $P/lips/${1}_raw.mp4 $P/lips/$1.mp4 </dev/null 2>&1 | grep MOUTHFIX) >> lips.log
  [ -s $1.mp4 ] || cp ${1}_raw.mp4 $1.mp4
  echo "$1 end $(date +%T) $(tail -1 $1.log)" >> lips.log
done
date +%T > ../tools/t_lips_end; echo LIPS_DONE >> lips.log
