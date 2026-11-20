#!/bin/bash
cd ~/Desktop/PROJECTS/story-forge
declare -a L=(
"b2a|lights die in sequence row by row toward the camera, server racks going dark, slow push in"
"b2b|blackout ripples across the skyline from left to right, blocks of windows going dark, static wide shot"
"b2c|slow dolly forward, one person lowers their hands from the keyboard, others frozen staring at screens"
"b4a|slow push toward the glowing window, fog drifting through the redwoods"
"b4b|the laptop lid lifts open, warm screen light spreads across the hands"
"b7a|subtle head drop, the person slumps further, static camera, red monitor glow"
"b7b|very slow orbit around the laptop, dust drifting in the light beam"
"b7c|smooth handheld pan left to right across the dark cabin room ending on the front door"
"b8a|the silhouette takes one slow step forward into the cabin, lantern swaying, fog rolling in, static camera"
"b9|lanterns drift closer along the road toward the glowing cabin window, slow crane up"
"b10|static shot, the laptop screen glow pulses slightly in the darkness"
)
for e in "${L[@]}"; do
  k=${e%%|*}; m=${e#*|}
  [ -f projects/blackout/clips/$k.mp4 ] && continue
  s=$(date +%s)
  for try in 1 2; do
    LOG=projects/blackout/wip/${k}_try${try}.log
    W0=$(date +%s); N=0
    while true; do
      H=$(python3 -c "
import sys; sys.path.insert(0,'$HOME/SongForgeM5'); import mem_client as m
print(round((m.state() or {}).get('headroom_gb',0),1))")
      awk "BEGIN{exit !($H>=78)}" && break
      N=$((N+1)); [ $((N % 4)) -eq 1 ] && echo "$(date '+%T') $k waiting for headroom>=78GB (now ${H}GB, ${N} polls)" >> projects/blackout/ETA.log
      sleep 30
    done
    echo "$(date '+%T') $k headroom ${H}GB after $(( $(date +%s)-W0 ))s wait, launching stock lease" >> projects/blackout/ETA.log
    bin/make-k6 --i2v projects/blackout/stills/$k.png --res 832x480 --duration 3 --seed 11 --label $k "$m" > $LOG 2>&1
    f=$(grep -o 'done in [0-9.]*s → .*' $LOG | sed 's/.*→ //')
    if [ -n "$f" ] && [ -f "$f" ]; then cp "$f" projects/blackout/clips/$k.mp4; echo "$(date '+%F %T') $k K6 OK actual $(( $(date +%s)-s ))s (planned 720s) try$try" >> projects/blackout/ETA.log; break; fi
    echo "$(date '+%F %T') $k K6 try$try FAILED after $(( $(date +%s)-s ))s: $(grep -v '^W11' $LOG | grep -v 'it/s' | tail -2 | tr '\n' ' ' | cut -c1-250)" >> projects/blackout/ETA.log
    [ $(( $(date +%s)-s )) -gt 1200 ] && { echo "$(date '+%T') $k slow failure, queue ABORTED" >> projects/blackout/ETA.log; exit 1; }
  done
done
echo "$(date '+%F %T') K6 queue finished" >> projects/blackout/ETA.log
