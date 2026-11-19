#!/bin/bash
cd ~/Desktop/PROJECTS/story-forge
while pgrep -f "film_qc.py projects/hank_doug_trailer/final/hank_doug_wild_rescue_trailer.mp4 projects/hank_doug_trailer/manifest.json --report projects/hank_doug_trailer/final/film_qc_v1" >/dev/null; do sleep 10; done
echo "$(date +%T) film_qc v2 start" >> projects/hank_doug_trailer/final/gates_v2.log
~/.local/mlx-server/bin/python pipeline-tools/film_qc.py projects/hank_doug_trailer/final/hank_doug_wild_rescue_trailer.mp4 projects/hank_doug_trailer/manifest.json --report projects/hank_doug_trailer/final/film_qc_report.md > projects/hank_doug_trailer/final/film_qc_v2.log 2>&1
echo "$(date +%T) film_qc v2 exit $?" >> projects/hank_doug_trailer/final/gates_v2.log
~/.local/mlx-server/bin/python pipeline-tools/continuity_check.py projects/hank_doug_trailer > projects/hank_doug_trailer/final/continuity_v2.log 2>&1
echo "$(date +%T) continuity exit $?" >> projects/hank_doug_trailer/final/gates_v2.log
