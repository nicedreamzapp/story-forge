#!/bin/bash
cd "$(dirname "$0")/.."
while pgrep -f "krea_batch.py stills/v4/jobs.json" >/dev/null; do sleep 5; done
python3 tools/krea_batch.py stills/v4/jobs_r2.json >> stills/v4/run_r2.log 2>&1
echo "$(date +%T) fox retry done" >> stills/v4/run.log
