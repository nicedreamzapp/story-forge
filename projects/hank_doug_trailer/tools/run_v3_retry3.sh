#!/bin/bash
cd "$(dirname "$0")/.."; LTX=~/Desktop/PROJECTS/story-forge/bin/make-ltx25; log=clips/v3/run.log
until grep -q "v3 retry2 done" $log; do sleep 10; done
STYLE="Painted oil-on-canvas animation, thick brush strokes stay fixed and do not flicker, the hills and the sky stay exactly in place, the camera does not tilt or pan, no new objects appear, colours stay as they are."
run() { [ -f "clips/v3/$1.mp4" ] && return
  out=$($LTX --i2v "$2" --duration $3 --res 832x480 --seed $4 --label "hd3_$1" "$5 $STYLE" 2>>$log | tail -1)
  src=$(echo "$out" | sed -n 's/.*→ \(.*\)$/\1/p'); [ -n "$src" ] && cp "$src" "clips/v3/$1.mp4"; echo "$(date +%T) $1 $out" >> $log; }
run I_walkaway_r2 stills/I_walkaway_gentle.png 4 44 "Locked-off camera. Seen from behind, the bloodhound and the young bear walk slowly away from us down the moonlit road, side by side, legs moving, the dog's tail wagging, both getting a little smaller as they go; the road and hills hold still."
echo "$(date +%T) v3 retry3 done" >> $log
