#!/bin/bash
# overnight film build: new masters, then every non-scene-3 shot, one forge-shot run
cd ~/Desktop/PROJECTS/story-forge
PY=~/.local/mlx-server/bin/python
$PY bin/forge-shot projects/oldest_tree/masters2.json > projects/oldest_tree/wip/forge_masters2.log 2>&1
ARGS=""; for i in $(cat projects/oldest_tree/wip/queue_ids.txt); do ARGS="$ARGS --only $i"; done
$PY bin/forge-shot projects/oldest_tree/film_shots.json $ARGS > projects/oldest_tree/wip/forge_film.log 2>&1
echo FILM_QUEUE_DONE
