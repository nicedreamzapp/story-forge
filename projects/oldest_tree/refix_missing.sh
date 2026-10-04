#!/bin/bash
# after the woman portrait: build the two never-finished shots, then face-lock them
cd ~/Desktop/PROJECTS/story-forge
while pgrep -f 'forge-shot projects/oldest_tree/masters3.json' >/dev/null; do sleep 15; done
L=projects/oldest_tree/wip/missing.log
for s in s6_breath s7_coat; do rm -f projects/oldest_tree/wip/${s}_anim_attempts; done
~/.local/mlx-server/bin/python bin/forge-shot projects/oldest_tree/refix_shots.json --only s6_breath --only s7_coat > $L 2>&1
echo MISSING_DONE >> $L
