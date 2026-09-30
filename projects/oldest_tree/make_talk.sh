#!/bin/bash
# LTX-2 distilled a2v lip-sync (proven formula: image-strength 0.4, audio-cfg 14)
# usage: make_talk.sh <shot_id> <voice.wav> "<prompt>"
set -e
P=~/Desktop/PROJECTS/story-forge/projects/oldest_tree
ID=$1; WAV=$2; PROMPT=$3
PADDED=$P/wip/${ID}_voice_pad.wav
# 0.4s lead-in + 0.8s tail so the mouth settles; clip length follows the audio
/opt/homebrew/bin/ffmpeg -v error -y -i "$WAV" -af "adelay=400|400,apad=pad_dur=0.8" -ar 48000 -ac 1 "$PADDED"
SECS=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$PADDED")
N=$(python3 -c "s=float('$SECS');n=round(s*24/8)*8+1;print(max(49,n))")
LID=$(python3 ~/SongForgeM5/mem_client.py wait "ltx2-render oldest_tree $ID" 40 --timeout 3600)
trap '[ -n "$LID" ] && python3 ~/SongForgeM5/mem_client.py release "$LID"' EXIT
cd ~/ai-video-bench && HF_HUB_DISABLE_XET=1 ./mlxvid-venv/bin/python -m mlx_video.models.ltx_2.generate \
  --pipeline distilled --model-repo prince-canuma/LTX-2-distilled \
  --image $P/stills/LOCKED_${ID}.png --image-strength ${STRENGTH:-0.4} \
  --audio-file "$PADDED" --audio-cfg-scale ${ACFG:-14} \
  --prompt "$PROMPT" -W 1216 -H 512 -n $N --fps 24 --output-path $P/clips/${ID}_talk.mp4
