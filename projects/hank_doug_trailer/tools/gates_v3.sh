#!/bin/bash
cd ~/Desktop/PROJECTS/story-forge; F=projects/hank_doug_trailer/final/hank_doug_wild_rescue_trailer_v3.mp4; L=projects/hank_doug_trailer/final/gates_v3.log
until [ -f projects/hank_doug_trailer/final/contact_sheet_v3_2fps.jpg ]; do sleep 5; done
python3 projects/hank_doug_trailer/tools/write_manifest_v3.py >> $L 2>&1
echo "$(date +%T) audio_check + film_qc start" >> $L
~/chatterbox-env/bin/python pipeline-tools/audio_check.py $F --score projects/hank_doug_trailer/music/theme_2.wav --timeline projects/hank_doug_trailer/final/timeline.json --narration projects/hank_doug_trailer/narration.json > projects/hank_doug_trailer/final/audio_check_v3_report.md 2>projects/hank_doug_trailer/final/audio_check_v3.err &
~/.local/mlx-server/bin/python pipeline-tools/film_qc.py $F projects/hank_doug_trailer/manifest_v3.json --report projects/hank_doug_trailer/final/film_qc_v3_report.md > projects/hank_doug_trailer/final/film_qc_v3.log 2>&1
echo "$(date +%T) film_qc exit $?" >> $L
~/.local/mlx-server/bin/python pipeline-tools/continuity_check.py projects/hank_doug_trailer $F > projects/hank_doug_trailer/final/continuity_v3.log 2>&1
echo "$(date +%T) continuity exit $?" >> $L
wait; echo "$(date +%T) gates v3 done" >> $L
