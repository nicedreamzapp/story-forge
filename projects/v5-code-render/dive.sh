#!/bin/bash
# One command for the 15 s "v5-dive" shot: scene, cameras, compile, frames, encode.
# Outside frames (0-239) at 192 spp, the interior (240-359, slower: enclosed bounces + vapor) at 96 spp.
set -e
cd "$(dirname "$0")"
echo "start $(date +%s)"
python3 scene.py && python3 dive.py
clang++ -O3 -std=c++17 -fobjc-arc render.mm -framework Metal -framework Foundation -o render
echo "built $(date +%s)"
./render --cams cameras_dive.txt --frames 0:240 --spp ${SPP_OUT:-192} --light 10 --vapor 1 --out frames_dive
echo "outside $(date +%s)"
./render --cams cameras_dive.txt --frames 240:360 --spp ${SPP_IN:-96} --light 10 --vapor 1 --out frames_dive
echo "rendered $(date +%s)"
ffmpeg -y -loglevel error -framerate 24 -i frames_dive/f_%04d.ppm -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -movflags +faststart v5-dive.mp4
echo "encoded $(date +%s)"
echo "done: $(pwd)/v5-dive.mp4"
