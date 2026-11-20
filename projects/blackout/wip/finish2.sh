#!/bin/bash
cd ~/Desktop/PROJECTS/story-forge/projects/blackout
wip/finish.sh && python3 build_texts.py && python3 wip/qc_manifest_build.py && cd ../.. && python3 pipeline-tools/text_readtime_check.py projects/blackout > projects/blackout/wip/readtime.log 2>&1
cd ~/Desktop/PROJECTS/story-forge
~/.local/mlx-server/bin/python pipeline-tools/film_qc.py projects/blackout/final/blackout_1920x1080.mp4 projects/blackout/qc_manifest.json --report projects/blackout/final/film_qc_report.md --spec > projects/blackout/wip/qc2.log 2>&1
echo "$(date '+%T') finish2 done" >> projects/blackout/ETA.log
