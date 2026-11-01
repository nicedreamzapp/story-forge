#!/bin/bash
cd "$(dirname "$0")"
for a in ${@:-anim04 anim15}; do
  while [ "$(curl -s 127.0.0.1:8767/api/status | grep -o '"jobs_running": [0-9]*' | grep -o '[0-9]*$')" != "0" ]; do sleep 30; done
  ~/Desktop/PROJECTS/story-forge/bin/mem-gate "blender ship" >/dev/null || { echo "mem-gate refused"; exit 1; }
  /opt/homebrew/bin/blender -b ship.blend -P shots.py -- $a --samples 48 2>&1 | grep -E "Error|Traceback|total|mp4"
done
echo ANIMS_DONE
