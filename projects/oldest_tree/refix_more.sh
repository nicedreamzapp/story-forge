#!/bin/bash
# after the wide-walk retry: re-animate any of the five refix shots still missing a kept clip (2 passes)
cd ~/Desktop/PROJECTS/story-forge
L=projects/oldest_tree/wip/refix_faces.log
until grep -q WIDEWALK_DONE $L; do sleep 20; done
for pass in 1 2; do
  ARGS=""
  for s in s2_wide_walk s4_walkback s7_kneel s4_creek s8_wide; do
    [ -f projects/oldest_tree/clips/${s}_final.mp4 ] || { [ -f projects/oldest_tree/stills/LOCKED_$s.png ] && ARGS="$ARGS --only $s"; }
  done
  [ -z "$ARGS" ] && break
  echo "=== REANIMATE pass $pass:$ARGS $(date)" >> $L
  ~/.local/mlx-server/bin/python bin/forge-shot projects/oldest_tree/refix_shots.json --stage animate $ARGS >> $L 2>&1
done
echo "ALL_REFIX_DONE $(date)" >> $L
