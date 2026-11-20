#!/bin/bash
# Short prep: stills (Krea 2) -> voices (VoiceDesign) -> foley. Sequential, Song-Forge-aware via each tool.
P=~/Desktop/PROJECTS/story-forge/projects/things_we_remember; cd $P
t0=$(date +%s); ~/AI/krea2/venv/bin/python ~/Desktop/PROJECTS/story-forge/projects/last_signal/tools/zimage_batch.py $P/stills_jobs_p01.json > stills_p01.log 2>&1
echo "{\"shot\": \"twr_p01\", \"step\": \"stills_krea2_x120\", \"seconds\": $(( $(date +%s) - t0 ))}" >> ~/Desktop/PROJECTS/story-forge/METRICS.jsonl
echo STILLS_DONE >> stills_p01.log
t0=$(date +%s); (cd voice && ~/.local/mlx-server/bin/python gen_more.py lines_p01.json && ~/chatterbox-env/bin/python score_more.py lines_p01.json) > voice/gen_p01.log 2>&1
echo "{\"shot\": \"twr_p01\", \"step\": \"voices_qwen3tts_x34_score\", \"seconds\": $(( $(date +%s) - t0 ))}" >> ~/Desktop/PROJECTS/story-forge/METRICS.jsonl
tools/p01/sfx_p1.sh
