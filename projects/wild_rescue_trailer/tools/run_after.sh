#!/bin/bash
# run_after.sh PID jobs.json log : wait for PID to exit (not pgrep), then run a Z-Image batch
while kill -0 "$1" 2>/dev/null; do sleep 10; done
cd "$(dirname "$0")/.."
~/AI/ComfyUI/venv/bin/python tools/zimage_batch.py "$2" >> "$3" 2>&1
echo "EXIT $?" >> "$3"
