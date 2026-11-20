#!/bin/bash
# Trailer FAST pass: LTX-2.5 distilled low-ram i2v 1024x576 (teaser recipe), one at a time; then the 2 a2v lip-syncs.
P=~/Desktop/PROJECTS/story-forge/projects/things_we_remember; cd $P
until [ -f tools/trailer/PICKS_READY ]; do sleep 5; done
date +%T > tools/trailer/t_anim_start
L=~/Desktop/PROJECTS/story-forge/bin/make-ltx25
pk() { python3 -c "import json;print(json.load(open('tools/picks_more.json'))['$1'])"; }
sfwait() { until [ "$(curl -s -m5 127.0.0.1:8767/api/status | python3 -c 'import sys,json;print(json.load(sys.stdin).get("jobs_running",0))' 2>/dev/null || echo 0)" = 0 ]; do sleep 20; done; }
run() { n=$1; seed=$2; dur=$3; shift 3
  [ -s clips/$n.mp4 ] && return
  sfwait; t0=$(date +%s)
  out=$($L --i2v stills/$(pk $n).png --duration $dur --res 1024x576 --low-ram --gb 26 --seed $seed --label twr-$n "$*" 2>&1 | tee -a clips_trailer.log | grep -o '→ .*mp4' | tail -1 | sed 's/→ //')
  [ -s "$out" ] && cp "$out" clips/$n.mp4 && echo "CLIP $n ok $(date +%T)" >> clips_trailer.log || echo "CLIP $n FAILED" >> clips_trailer.log
  echo "{\"shot\": \"twr_trailer_$n\", \"step\": \"i2v_ltx25_lowram_${dur}s\", \"seconds\": $(( $(date +%s) - t0 ))}" >> ~/Desktop/PROJECTS/story-forge/METRICS.jsonl
}
a2v() { n=$1; seed=$2; shift 2
  [ -s clips/$n.mp4 ] && return
  sfwait; t0=$(date +%s)
  out=$($L --i2v stills/$(pk $n).png --audio voice/${n}_a2v.wav --res 1024x576 --low-ram --gb 26 --seed $seed --label twr-$n "$*" 2>&1 | tee -a clips_trailer.log | grep -o '→ .*mp4' | tail -1 | sed 's/→ //')
  [ -s "$out" ] && cp "$out" clips/$n.mp4 && echo "CLIP $n ok $(date +%T)" >> clips_trailer.log || echo "CLIP $n FAILED" >> clips_trailer.log
  echo "{\"shot\": \"twr_trailer_$n\", \"step\": \"a2v_ltx25_lowram\", \"seconds\": $(( $(date +%s) - t0 ))}" >> ~/Desktop/PROJECTS/story-forge/METRICS.jsonl
}
LOOK="cinematic horror film, slow and quiet, natural motivated light stays the same"
run t10 1810 3 "the woman's hand quickly pulls the patchwork quilt back off the small bed, revealing that the bed is completely empty, nobody is there, only a dent in the pillow, the moonlight stripes stay still, the camera holds still, $LOOK"
run t01 1210 5 "the station wagon rolls slowly up the wet gravel driveway toward the old farmhouse and comes to a stop, soft rain keeps falling, puddles ripple, the camera holds still, $LOOK"
run t03 1310 3 "the little girl runs quickly up the wooden stairs and disappears around the top of the landing, then the staircase is empty and still, the camera holds on the empty stairs, $LOOK"
run t04 1410 4 "the old woman stands perfectly still at the window with her back to us, rain runs down the glass, the lace curtain stirs very slightly, the camera slowly pushes in toward her, $LOOK"
run t13 2110 5 "the woman sits frozen at the kitchen table staring at the cassette recorder, she does not move, only slow breathing, the hanging lamp flickers faintly, the camera very slowly pushes in toward her face, $LOOK"
run t17 2410 3 "the dark hallway is perfectly still, the shadowy figure stands motionless beside the child's door and does not move, the nightlight glow flickers faintly, the camera slowly creeps forward, $LOOK"
run t18 2510 3 "the man stands beside the small empty bed looking down at it, he slowly tilts his head, puzzled, he does not touch it, the camera holds still, $LOOK"
echo I2V_DONE >> clips_trailer.log
until grep -q SCORE_DONE voice/gen_trailer.log; do sleep 5; done
~/.local/mlx-server/bin/python tools/trailer/a2vwav.py t11:L02:3.0 t14:L03:4.5 >> clips_trailer.log 2>&1
a2v t11 1910 "the little girl lies in bed looking up at someone above her and speaks quietly, her mouth moving with the words, calm flat serious face, she blinks once, camera locked off, $LOOK"
a2v t14 2210 "home video, the little girl standing in the garden looks just past the camera and speaks, her mouth moving with the words, she lifts a hand and points past the camera, slight handheld camera shake, sunny afternoon"
echo CLIPS_DONE >> clips_trailer.log; date +%T > tools/trailer/t_anim_end
