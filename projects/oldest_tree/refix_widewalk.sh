#!/bin/bash
# wait for refix_faces.sh, then re-roll s2_wide_walk framed closer if it has no kept clip
cd ~/Desktop/PROJECTS/story-forge
L=projects/oldest_tree/wip/refix_faces.log
until grep -q REFIX_DONE $L; do sleep 20; done
if [ ! -f projects/oldest_tree/clips/s2_wide_walk_final.mp4 ]; then
  echo "=== WIDEWALK closer framing $(date)" >> $L
  chmod 644 projects/oldest_tree/stills/LOCKED_s2_wide_walk.png
  mv projects/oldest_tree/stills/LOCKED_s2_wide_walk.png projects/oldest_tree/archive/2026-10-03_face_fail/LOCKED_s2_wide_walk_try2.png
  ~/.local/mlx-server/bin/python bin/forge-shot projects/oldest_tree/refix_shots.json --only s2_wide_walk >> $L 2>&1
fi
echo "WIDEWALK_DONE $(date)" >> $L
