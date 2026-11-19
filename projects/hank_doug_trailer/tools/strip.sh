#!/bin/bash
# strip.sh CLIP OUT.png [every_n_frames]  -> 6-frame horizontal strip for the agent's eye (rule 26 frame-grid look)
ffmpeg -v error -y -i "$1" -vf "select='not(mod(n\,${3:-24}))',scale=480:-1,tile=6x1" -frames:v 1 "$2"
