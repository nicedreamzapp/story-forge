#!/bin/bash
# K6 Pro quality render of the hero shot (pipeline 04 step 5c): waits for the LTX previs pass to finish (one heavy model at a time).
cd "$(dirname "$0")/.."
until grep -q "previs done" clips/previs/run.log 2>/dev/null; do sleep 15; done
log=clips/k6.log
out=$(~/Desktop/PROJECTS/story-forge/bin/make-k6 --i2v stills/D_rollout.png --duration 5 --res 832x480 --seed 11 --label hd_D_k6 "Painted oil-on-canvas animation, wide clean side profile. The team walks to the LEFT, the direction the horse faces, and the camera tracks left alongside the red wagon at exactly the wagon's speed so the wagon and the four-animal team stay in the same place in the frame; the horse, zebra, camel and cow walk in step pulling, the big spoked wheels turn, the brass lantern swings on its hook, the bear and the dog sit still on the bench, the two giraffes jog behind and the two elephants walk at the back, dust drifting behind the wheels, the hills sliding past behind. Thick brush strokes stay fixed, no flicker." 2>>$log | tail -1)
src=$(echo "$out" | sed -n 's/.*→ \(.*\)$/\1/p'); [ -n "$src" ] && cp "$src" clips/D_rollout_k6.mp4
echo "$(date +%T) D_k6 $out" >> $log
