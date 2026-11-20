#!/bin/bash
# LTX-2.5 distilled low-ram i2v, 576x1024 portrait, one at a time after the stills (Derelict/Lost Letters recipe).
P=~/Desktop/PROJECTS/story-forge/projects/lahontan_returns; cd $P
while pgrep -f "zimage_batch.py $P/stills_jobs" >/dev/null; do sleep 5; done
date +%T > tools/t_anim_start
L=~/Desktop/PROJECTS/story-forge/bin/make-ltx25
run() { n=$1; src=$2; seed=$3; dur=$4; shift 4
  [ -s clips/$n.mp4 ] && return
  [ -f tools/pick_$src ] && src=$(cat tools/pick_$src)
  out=$($L --i2v stills/$src.png --duration $dur --res 576x1024 --low-ram --gb 26 --seed $seed --label lr-s$n "$*" 2>&1 | tee -a clips.log | grep -o '→ .*mp4' | tail -1 | sed 's/→ //')
  [ -s "$out" ] && cp "$out" clips/$n.mp4 && echo "CLIP $n ok $(date +%T)" >> clips.log || echo "CLIP $n FAILED" >> clips.log
}
TALK="camera locked off on a tripod, steady broadcast framing, natural soft light"
run anchor anchor_a 51 5 "the news anchor speaks seriously to the camera, his mouth opening and closing as he talks, small natural head nods, he blinks, his hands stay folded on the desk, $TALK"
run reporter reporter_b 52 5 "the field reporter speaks into her microphone looking at the camera, her mouth moving as she talks, a light breeze moves her hair, the shallow floodwater ripples around her, $TALK, slight handheld news camera"
run sci sci 56 5 "the old scientist speaks to the camera, his mouth moving as he talks, he gestures slightly toward the whiteboard, he blinks, $TALK"
run res res 57 5 "the old man in the lawn chair talks to the camera, his mouth moving as he speaks, he shrugs and nods, the floodwater ripples around the chair, $TALK"
run reservoir reservoir 53 3 "muddy water surges and climbs up the dry hillside, waves rolling uphill against gravity, the helicopter camera slowly orbits"
run sage sage 54 3 "the clumps of sagebrush drift slowly and bob on the rippling floodwater, gentle current, the camera slowly pans right"
run hwy hwy 55 3 "floodwater spreads across the highway, ripples and little waves wash over the yellow line, the camera slowly pushes forward"
run fish fish 58 3 "the giant prehistoric fish swims slowly down the flooded street toward the camera, its dorsal fin cutting the water, a wake spreading behind it"
run aerial aerial 59 3 "the news helicopter camera slowly flies forward over the flooding town, sunlight glints on the spreading water"
echo CLIPS_DONE >> clips.log; date +%T > tools/t_anim_end
