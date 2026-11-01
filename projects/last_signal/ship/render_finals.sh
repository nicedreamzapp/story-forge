#!/bin/bash
# Final still batch. Usage: render_finals.sh [shots...]
cd "$(dirname "$0")"
SHOTS=${@:-r01 r04a r04b r05 r12 r15 r03}
for s in $SHOTS; do
  while [ "$(curl -s 127.0.0.1:8767/api/status | grep -o '"jobs_running": [0-9]*' | grep -o '[0-9]*$')" != "0" ]; do sleep 30; done
  ~/Desktop/PROJECTS/story-forge/bin/mem-gate "blender ship" >/dev/null || { echo "mem-gate refused"; exit 1; }
  /opt/homebrew/bin/blender -b ship.blend -P shots.py -- $s --samples 128 2>&1 | grep -E "Error|Traceback|^r[0-9]"
done
echo BATCH_DONE
