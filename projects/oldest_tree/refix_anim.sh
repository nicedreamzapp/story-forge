#!/bin/bash
# re-animate s2_wide_walk + s4_walkback with a NEW seed each attempt (up to 4 each)
cd ~/Desktop/PROJECTS/story-forge
L=projects/oldest_tree/wip/refix_faces.log
for pass in 1 2 3; do
  ARGS=""
  for s in s2_wide_walk s4_walkback; do
    [ -f projects/oldest_tree/clips/${s}_final.mp4 ] || ARGS="$ARGS --only $s"
  done
  [ -z "$ARGS" ] && break
  echo "=== REANIMATE (rotating seed) pass $pass:$ARGS $(date)" >> $L
  ~/.local/mlx-server/bin/python bin/forge-shot projects/oldest_tree/refix_shots.json --stage animate $ARGS >> $L 2>&1
done
echo "ALL_REFIX_DONE $(date)" >> $L
