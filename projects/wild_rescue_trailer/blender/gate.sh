#!/bin/bash
# customer jobs outrank renders; then the memory gate
while true; do
  n=$(curl -s 127.0.0.1:8767/api/status | python3 -c 'import sys,json;print(int(json.load(sys.stdin).get("jobs_running",0)))' 2>/dev/null || echo 0)
  [ "${n:-0}" -gt 0 ] || break
  echo "songforge jobs_running=$n, waiting"; sleep 30
done
/Users/dtribe/Desktop/PROJECTS/story-forge/bin/mem-gate "wildrescue blender" || exit 1
