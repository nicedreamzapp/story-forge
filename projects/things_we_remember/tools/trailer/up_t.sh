#!/bin/bash
P=~/Desktop/PROJECTS/story-forge/projects/things_we_remember; cd $P
until [ "$(curl -s -m5 127.0.0.1:8767/api/status | python3 -c 'import sys,json;print(json.load(sys.stdin).get("jobs_running",0))' 2>/dev/null || echo 0)" = 0 ]; do sleep 20; done
t0=$(date +%s)
~/Desktop/PROJECTS/story-forge/bin/upscale-route $P --edl final/edl_hq_trailer.json --segs final/segs/hq_trailer --out final/segs/up_trailer > upscale_trailer.log 2>&1
echo "{\"shot\": \"twr_trailer\", \"step\": \"upscale_seedvr2_x5\", \"seconds\": $(( $(date +%s) - t0 ))}" >> ~/Desktop/PROJECTS/story-forge/METRICS.jsonl
echo UP_DONE2 >> upscale_trailer.log
