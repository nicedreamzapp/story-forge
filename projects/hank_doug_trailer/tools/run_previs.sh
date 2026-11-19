#!/bin/bash
# LTX-2.5 previs of the 4 motion beats + the 2 a2v talking clips (pipeline 04 step 5a). One model, loaded per call.
cd "$(dirname "$0")/.."; mkdir -p clips/previs
LTX=~/Desktop/PROJECTS/story-forge/bin/make-ltx25
log=clips/previs/run.log
run() { # id still seconds prompt
  [ -f "clips/previs/$1.mp4" ] && return
  while [ ! -f "$2" ] || pgrep -f krea_batch.py >/dev/null; do sleep 10; done
  out=$($LTX --i2v "$2" --duration $3 --res 832x480 --seed 11 --label "hd_$1" "$4" 2>>$log | tail -1)
  src=$(echo "$out" | sed -n 's/.*→ \(.*\)$/\1/p'); [ -n "$src" ] && cp "$src" "clips/previs/$1.mp4"
  echo "$(date +%T) $1 $out" >> $log
}
talk() { # id still wav prompt
  [ -f "clips/previs/$1.mp4" ] && return
  while [ ! -f "$2" ] || pgrep -f krea_batch.py >/dev/null; do sleep 10; done
  out=$($LTX --i2v "$2" --audio "$3" --res 832x480 --seed 11 --label "hd_$1" "$4" 2>>$log | tail -1)
  src=$(echo "$out" | sed -n 's/.*→ \(.*\)$/\1/p'); [ -n "$src" ] && cp "$src" "clips/previs/$1.mp4"
  echo "$(date +%T) $1 $out" >> $log
}
run D_rollout stills/D_rollout.png 5 "Painted oil-on-canvas animation. The whole team pulls the red wagon to the right along the dirt road, the horse, zebra, camel and cow walking in step, the big spoked wheels turning, the brass lantern swinging on its hook, the bear and the dog sitting still on the bench, the two giraffes jogging behind, the elephants walking at the back, dust drifting behind the wheels; the camera tracks right alongside the wagon at a steady pace. Thick brush strokes stay fixed, no flicker."
run L_airlift stills/L_airlift.png 4 "Painted oil-on-canvas animation. The dozen white geese beat their wings and the wooden platform on its four ropes rises slowly and comes level with the rock ledge; the white goat steps onto the platform, front hooves first, then all four; the platform dips a little and holds. The camera tilts up gently with the platform. Thick brush strokes stay fixed, no flicker."
run E_turtle stills/E_turtle.png 4 "Painted oil-on-canvas animation. Two long grey elephant trunks swing into the frame from the left and right edges and spray two arcs of water down onto the cracked mud around the stuck turtle; the mud darkens and the water rises and the turtle lifts and floats, his legs paddling. The camera holds still. Thick brush strokes stay fixed, no flicker."
run M_otters stills/M_otters.png 4 "Painted oil-on-canvas animation. The chain of four otters is hauled slowly upward out of the drain hole by the bear's two paws at the top of frame; the bottom otter rises out of the hole holding the small grey kitten by the scruff, the kitten's legs dangling; the otters' tails sway. The camera holds still. Thick brush strokes stay fixed, no flicker."
talk N_hi stills/N_nose.png voices/L4_younghank_hi_padded.wav "Painted oil-on-canvas animation, close two-shot in moonlight. The young bear on the right, eyes wide, opens his mouth and says one small word, his jaw moving once; the dog on the left holds still, then his eyes soften. No other motion. Thick brush strokes stay fixed, no flicker."
talk K_rolling stills/K_sleeping.png voices/L6_hank_rolling2_padded.wav "Painted oil-on-canvas animation, golden sunset under the oak. Everyone sleeps; the small chipmunk on the wheel rim squeaks, the dog's long ears shoot straight up and his eyes open wide, and the big bear, eyes still shut, head back, moves his mouth once to speak one word; the lantern flame flickers warm. The camera holds still. Thick brush strokes stay fixed, no flicker."
echo "$(date +%T) previs done" >> $log
