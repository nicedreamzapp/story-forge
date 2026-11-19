#!/bin/bash
cd "$(dirname "$0")/.."; LTX=~/Desktop/PROJECTS/story-forge/bin/make-ltx25; log=clips/v3/run.log
until grep -q "v3 clips done" $log; do sleep 10; done
STYLE="Painted oil-on-canvas animation, thick brush strokes stay fixed and do not flicker, the background does not slide, no new creatures appear, nobody disappears, faces keep their exact shape."
run() { [ -f "clips/v3/$1.mp4" ] && return
  out=$($LTX --i2v "$2" --duration $3 --res 832x480 --seed $4 --label "hd3_$1" "$5 $STYLE" 2>>$log | tail -1)
  src=$(echo "$out" | sed -n 's/.*→ \(.*\)$/\1/p'); [ -n "$src" ] && cp "$src" "clips/v3/$1.mp4"; echo "$(date +%T) $1 $out" >> $log; }
run K_button_r2 stills/K_sleeping.png 5 33 "Locked-off static camera on a parked wagon under an oak at dusk; every animal stays exactly where it is: the marmot stays curled on top of the bear's head, the giraffe heads stay behind the wagon, the dog stays on the bear's lap. Very little motion: the bear's chest rises and falls, his mouth opens briefly once, the dog's ears lift once, the lantern flame flickers, a few leaves stir."
for extra in "$@"; do :; done
echo "$(date +%T) v3 retry done" >> $log
