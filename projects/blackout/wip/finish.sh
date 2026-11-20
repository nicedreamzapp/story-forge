#!/bin/bash
cd ~/Desktop/PROJECTS/story-forge/projects/blackout
PY=~/AI/ComfyUI/venv/bin/python; FF=/opt/homebrew/bin/ffmpeg
$PY edit_blackout.py h && $PY edit_blackout.py v && $PY mix_blackout.py || exit 1
D=$($PY -c "import json;print(json.load(open('final/timeline.json'))['duration'])")
for m in h v; do n=blackout_$( [ $m = h ] && echo 1920x1080 || echo 1080x1920 )
 $FF -v error -y -i final/blackout_picture_$m.mp4 -i final/blackout_mix.wav -map 0:v -map 1:a -c:v libx264 -crf 22 -preset medium -pix_fmt yuv420p -c:a aac -b:a 256k -ar 48000 -movflags +faststart -t $D final/$n.mp4
 python3 ../../pipeline-tools/final_audio_gate.py final/$n.mp4 --in-place 2>&1 | tail -1
done
rm -f final/blackout_picture_*.mp4
echo "$(date '+%T') finish.sh done" >> ETA.log
