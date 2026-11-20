#!/bin/bash
# One command for the 16 s "v5-dive-v2" shot (rosin melt): scene, cameras, compile, frames, encode.
# Outside frames 0-164 at 192 spp; bore + chamber/melt frames 165-383 at 48 spp (enclosed bounces + rosin SDF + vapor).
set -e
cd "$(dirname "$0")"
echo "start $(date +%s)"
python3 scene.py && python3 dive2.py
clang++ -O3 -std=c++17 -fobjc-arc render.mm -framework Metal -framework Foundation -o render
echo "built $(date +%s)"
./render --cams cameras_dive2.txt --frames 0:165 --spp ${SPP_OUT:-192} --light 10 --vapor 1 --out frames_dive2
echo "outside $(date +%s)"
./render --cams cameras_dive2.txt --frames 165:384 --spp ${SPP_IN:-48} --light 10 --vapor 1 --out frames_dive2
echo "rendered $(date +%s)"
ffmpeg -y -loglevel error -framerate 24 -i frames_dive2/f_%04d.ppm -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -movflags +faststart v5-dive-v2.mp4
echo "encoded $(date +%s)"
echo "done: $(pwd)/v5-dive-v2.mp4"
