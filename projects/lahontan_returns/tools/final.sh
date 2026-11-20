#!/bin/bash
# finish: picture + mix, static gain to -14.5 LUFS (2-pass: measure, gain), true-peak limiter at -2.2 dBTP, verify.
set -e
P=~/Desktop/PROJECTS/story-forge/projects/lahontan_returns; cd $P
D=$(python3 -c "import json;print(json.load(open('timeline.json'))['end'])")
I=$(ffmpeg -nostdin -i audio/mix.wav -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1 | awk '{print $2}')
G=$(python3 -c "print(round(-14.5-($I)+${XG:-0},2))")
ffmpeg -nostdin -v error -y -i audio/mix.wav -af "volume=${G}dB,aresample=192000,alimiter=limit=0.74:level=false:attack=1:release=60,aresample=48000" -c:a pcm_s24le audio/mix_norm.wav
ffmpeg -nostdin -v error -y -i final/picture.mp4 -i audio/mix_norm.wav -map 0:v -map 1:a -t $D \
  -c:v libx264 -profile:v high -level 4.2 -crf 15 -maxrate 16000k -bufsize 32000k -preset slow -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart final/lahontan_returns.mp4
ffmpeg -nostdin -i final/lahontan_returns.mp4 -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|Peak):" | tail -2
ffprobe -v error -show_entries format=duration -of csv=p=0 final/lahontan_returns.mp4
echo FINAL_DONE
