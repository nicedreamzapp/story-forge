#!/bin/bash
# BEST pass fallback: LTX-2.5 --hq --low-ram 1024x576 4 s (K6 refused 21:34)
P=~/Desktop/PROJECTS/story-forge/projects/things_we_remember; cd $P
date +%T > tools/t_hq_start
K=~/Desktop/PROJECTS/story-forge/bin/make-ltx25
pk() { python3 -c "import json;print(json.load(open('tools/picks.json'))['$1'])"; }
run() { n=$1; seed=$2; shift 2
  [ -s clips/hq/$n.mp4 ] && return
  until [ "$(curl -s -m5 127.0.0.1:8767/api/status | python3 -c 'import sys,json;print(json.load(sys.stdin).get("jobs_running",0))' 2>/dev/null || echo 0)" = 0 ]; do sleep 20; done
  out=$($K --i2v stills/$(pk $n).png --duration 4 --res 1024x576 --hq --low-ram --gb 26 --seed $seed --label twr-hq-$n "$*" 2>&1 | tee -a clips_hq.log | grep -o '→ .*mp4' | tail -1 | sed 's/→ //')
  [ -s "$out" ] && cp "$out" clips/hq/$n.mp4 && echo "HQ $n ok $(date +%T)" >> clips_hq.log || echo "HQ $n FAILED $(date +%T)" >> clips_hq.log
}
LOOK="cinematic horror film, slow and quiet, natural motivated light stays the same"
run s11 211 "the woman stands perfectly still at the dark window, in the window reflection behind her the soft blurred man slowly tilts his head and smiles gently, nobody is behind her in the room, the camera very slowly pushes in over her shoulder, $LOOK"
run s01 201 "the golden sun beam slowly drifts, dust motes float and swirl in the light, raindrops begin to run down the window glass, the lace curtain stirs gently, the camera slowly pushes in toward the window, the room is empty, $LOOK"
run s08 208 "the small boy under the quilt lies still facing the wall, the quilt rises and falls slowly with his breathing, the moonlight stripes stay still, the camera creeps slowly forward toward the bed, $LOOK"
run s04 204 "the old woman slowly lifts her eyes from the photograph and looks up at someone off camera, her face still and grave, she blinks once, her mouth stays closed, rain runs down the window behind her, camera locked off, $LOOK"
if [ ! -s clips/hq/s07.mp4 ]; then
  out=$($K --i2v stills/$(pk s07).png --audio voice/L01_a2v.wav --res 1024x576 --hq --low-ram --gb 26 --seed 207 --label twr-hq-s07 "the little girl looks toward the empty chair beside her and speaks quietly, her mouth moving with the words, calm flat serious face, she blinks, camera locked off, $LOOK" 2>&1 | tee -a clips_hq.log | grep -o '→ .*mp4' | tail -1 | sed 's/→ //')
  [ -s "$out" ] && cp "$out" clips/hq/s07.mp4 && echo "HQ s07 ok $(date +%T)" >> clips_hq.log || echo "HQ s07 FAILED $(date +%T)" >> clips_hq.log
fi
echo BEST_DONE >> clips_hq.log; date +%T > tools/t_hq_end
