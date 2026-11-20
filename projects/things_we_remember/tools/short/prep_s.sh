#!/bin/bash
# Short prep: stills (Krea 2) -> voices (VoiceDesign) -> foley. Sequential, Song-Forge-aware via each tool.
P=~/Desktop/PROJECTS/story-forge/projects/things_we_remember; cd $P
t0=$(date +%s); ~/AI/krea2/venv/bin/python ~/Desktop/PROJECTS/story-forge/projects/last_signal/tools/zimage_batch.py $P/stills_jobs_short.json > stills_short.log 2>&1
echo "{\"shot\": \"twr_short\", \"step\": \"stills_krea2_x38\", \"seconds\": $(( $(date +%s) - t0 ))}" >> ~/Desktop/PROJECTS/story-forge/METRICS.jsonl
echo STILLS_DONE >> stills_short.log
t0=$(date +%s); (cd voice && ~/.local/mlx-server/bin/python gen_more.py lines_short.json && ~/chatterbox-env/bin/python score_more.py lines_short.json) > voice/gen_short.log 2>&1
echo "{\"shot\": \"twr_short\", \"step\": \"voices_qwen3tts_x32_score\", \"seconds\": $(( $(date +%s) - t0 ))}" >> ~/Desktop/PROJECTS/story-forge/METRICS.jsonl
tools/short/sfx_s.sh
