#!/bin/bash
# One command: build the scene, compile the renderer, render all frames, encode the mp4.
#   ./render.sh                      full 1920x1080, 240 frames, 36 spp
#   SPP=16 FRAMES=0:24 ./render.sh   quick partial run
# Scene/camera overrides go to scene.py as key=value, e.g.  ./render.sh dist0=300 fstop=2.8
set -e
cd "$(dirname "$0")"
OUT=${OUT:-frames}; NAME=${NAME:-v5-test.mp4}; SPP=${SPP:-256}; FRAMES=${FRAMES:-0:240}; EXPOSURE=${EXPOSURE:-1.0}; LIGHT=${LIGHT:-10}
echo "start $(date +%s)"
python3 scene.py "$@"
clang++ -O3 -std=c++17 -fobjc-arc render.mm -framework Metal -framework Foundation -o render
echo "built $(date +%s)"
./render --frames "$FRAMES" --spp "$SPP" --out "$OUT" --exposure "$EXPOSURE" --light "$LIGHT"
echo "rendered $(date +%s)"
ffmpeg -y -loglevel error -framerate 24 -start_number "${FRAMES%%:*}" -i "$OUT"/f_%04d.ppm -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -movflags +faststart "$NAME"
echo "encoded $(date +%s)"
echo "done: $(pwd)/$NAME"
