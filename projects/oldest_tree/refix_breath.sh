#!/bin/bash
cd ~/Desktop/PROJECTS/story-forge
while pgrep -f 'refix_missing.sh' >/dev/null; do sleep 10; done
~/.local/mlx-server/bin/python bin/forge-shot projects/oldest_tree/refix_shots.json --only s6_breath >> projects/oldest_tree/wip/missing.log 2>&1
echo BREATH_DONE >> projects/oldest_tree/wip/missing.log
