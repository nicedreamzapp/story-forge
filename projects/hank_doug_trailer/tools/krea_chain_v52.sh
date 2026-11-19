#!/bin/bash
# wait for klein_v52 to finish (guard: never Krea + klein together), then paint the v5.2 montage stills
cd "$(dirname "$0")/.." || exit 1
until grep -q "klein_v52 done" final/run_v52.log; do sleep 10; done
echo "$(date '+%m/%d %H:%M:%S') krea montage stills start" | tee -a final/run_v52.log
/usr/bin/python3 tools/krea_batch.py stills/v52/jobs_v52_montage.json >> final/krea_v52.log 2>&1
echo "$(date '+%m/%d %H:%M:%S') krea montage stills done rc=$?: $(ls stills/v52/*_v52*.png | wc -l | tr -d ' ') stills" | tee -a final/run_v52.log
