#!/bin/bash
# usage: render.sh <blend> <shot...> ; pauses blender (SIGSTOP) while Song Forge customer jobs run
cd "$(dirname "$0")"
./gate.sh || exit 1
blend=$1; shift
/opt/homebrew/bin/blender -b "$blend" -P shots.py -- "$@" &
BP=$!
( while kill -0 $BP 2>/dev/null; do
    n=$(curl -s 127.0.0.1:8767/api/status | python3 -c 'import sys,json;print(int(json.load(sys.stdin).get("jobs_running",0)))' 2>/dev/null || echo 0)
    if [ "${n:-0}" -gt 0 ]; then kill -STOP $BP 2>/dev/null; else kill -CONT $BP 2>/dev/null; fi
    sleep 10
  done ) &
WP=$!
wait $BP; rc=$?
kill $WP 2>/dev/null
exit $rc
