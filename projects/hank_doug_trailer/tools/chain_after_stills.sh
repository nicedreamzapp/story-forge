#!/bin/bash
# runs after the main Krea batch: D retry (dromedary wording), then hands off to previs
cd "$(dirname "$0")/.."
while pgrep -f "krea_batch.py stills/jobs.json" >/dev/null; do sleep 10; done
echo "$(date +%T) main stills batch done" >> stills/run.log
python3 tools/krea_batch.py stills/jobs_r2.json >> stills/run_r2.log 2>&1
echo "$(date +%T) D retry batch done" >> stills/run.log
