#!/bin/bash
# BEST pass: Kandinsky 6 Pro distill i2v, 832x480 (the measured setting), 3 s (73 f), 10 steps, one at a time. Headroom 75.9 GB at 21:19.
P=~/Desktop/PROJECTS/story-forge/projects/things_we_remember; cd $P
date +%T > tools/t_best_start
K=~/Desktop/PROJECTS/story-forge/bin/make-k6
pk() { python3 -c "import json;print(json.load(open('tools/picks.json'))['$1'])"; }
run() { n=$1; seed=$2; shift 2
  [ -s clips/best/$n.mp4 ] && return
  until [ "$(curl -s -m5 127.0.0.1:8767/api/status | python3 -c 'import sys,json;print(json.load(sys.stdin).get("jobs_running",0))' 2>/dev/null || echo 0)" = 0 ]; do sleep 20; done
  out=$($K --i2v stills/$(pk $n).png --duration 3 --res 832x480 --seed $seed --label twr-k6-$n "$*" 2>&1 | tee -a clips_best.log | grep -o '→ .*mp4' | tail -1 | sed 's/→ //')
  [ -s "$out" ] && cp "$out" clips/best/$n.mp4 && echo "K6 $n ok $(date +%T)" >> clips_best.log || echo "K6 $n FAILED $(date +%T)" >> clips_best.log
}
LOOK="cinematic horror film, slow and quiet, natural motivated light stays the same"
run s11 211 "the woman stands perfectly still at the dark window, in the window reflection behind her the soft blurred man slowly tilts his head and smiles gently, nobody is behind her in the room, the camera very slowly pushes in over her shoulder, $LOOK"
run s01 201 "the golden sun beam slowly drifts, dust motes float and swirl in the light, raindrops begin to run down the window glass, the lace curtain stirs gently, the camera slowly pushes in toward the window, the room is empty, $LOOK"
run s08 208 "the small boy under the quilt lies still facing the wall, the quilt rises and falls slowly with his breathing, the moonlight stripes stay still, the camera creeps slowly forward toward the bed, $LOOK"
run s04 204 "the old woman slowly lifts her eyes from the photograph and looks up at someone off camera, her face still and grave, she blinks once, her mouth stays closed, rain runs down the window behind her, camera locked off, $LOOK"
run s07 207 "the little girl turns her eyes toward the empty chair beside her and speaks quietly, her mouth opening and closing as she talks, calm flat serious face, she blinks once, camera locked off, $LOOK"
echo BEST_DONE >> clips_best.log; date +%T > tools/t_best_end
