#!/bin/bash
# 2026-10-03: re-roll the shots face_check failed (girl off-model), then re-animate the two
# whose stills pass but whose clips drifted. Face gate is live in forge-shot for all of them.
cd ~/Desktop/PROJECTS/story-forge
PY=~/.local/mlx-server/bin/python
L=projects/oldest_tree/wip/refix_faces.log
echo "START $(date)" > $L
$PY bin/forge-shot projects/oldest_tree/refix_shots.json --only s4_walkback --only s2_wide_walk --only s7_kneel >> $L 2>&1
$PY bin/forge-shot projects/oldest_tree/refix_shots.json --stage animate --only s4_creek --only s8_wide >> $L 2>&1
echo "REFIX_DONE $(date)" >> $L
