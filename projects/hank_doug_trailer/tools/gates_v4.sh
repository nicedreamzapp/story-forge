#!/bin/bash
cd ~/Desktop/PROJECTS/story-forge; F=projects/hank_doug_trailer/final/hank_doug_wild_rescue_trailer_v4.mp4; L=projects/hank_doug_trailer/final/gates_v4.log
until [ -f projects/hank_doug_trailer/final/contact_sheet_v4_2fps.jpg ]; do sleep 5; done
echo "$(date +%T) gates v4 start" >> $L
~/chatterbox-env/bin/python pipeline-tools/audio_check.py $F --score projects/hank_doug_trailer/music/theme_2.wav --timeline projects/hank_doug_trailer/final/timeline.json --narration projects/hank_doug_trailer/narration.json > projects/hank_doug_trailer/final/audio_check_v4_report.md 2>projects/hank_doug_trailer/final/audio_check_v4.err &
~/.local/mlx-server/bin/python pipeline-tools/film_qc.py $F projects/hank_doug_trailer/manifest_v4.json --report projects/hank_doug_trailer/final/film_qc_v4_report.md > projects/hank_doug_trailer/final/film_qc_v4.log 2>&1
echo "$(date +%T) film_qc exit $?" >> $L
wait; echo "$(date +%T) gates v4 done" >> $L
