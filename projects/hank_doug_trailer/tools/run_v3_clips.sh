#!/bin/bash
# v3 fix pass: every still-only beat becomes a real LTX-2.5 distilled i2v clip; K re-rendered static. One model at a time.
cd "$(dirname "$0")/.."; LTX=~/Desktop/PROJECTS/story-forge/bin/make-ltx25; log=clips/v3/run.log
STYLE="Painted oil-on-canvas animation, thick brush strokes stay fixed and do not flicker, the background does not slide, no new creatures appear."
run() { # id still seconds seed prompt
  [ -f "clips/v3/$1.mp4" ] && return
  out=$($LTX --i2v "$2" --duration $3 --res 832x480 --seed $4 --label "hd3_$1" "$5 $STYLE" 2>>$log | tail -1)
  src=$(echo "$out" | sed -n 's/.*→ \(.*\)$/\1/p'); [ -n "$src" ] && cp "$src" "clips/v3/$1.mp4"
  echo "$(date +%T) $1 $out" >> $log
}
run K_button stills/K_sleeping.png 6 21 "Locked-off static camera, the wagon stays parked under the oak and nothing in the background moves; the animals rest in a pile; the big bear's chest rises and falls and his mouth opens and closes once as he speaks a single word; the dog's long ears twitch up; the lantern flame flickers warm; leaves stir gently."
run A_goat stills/A_ledge_goat.png 4 11 "The small white goat on the high ledge shifts her feet, lifts her head and bleats, mouth opening and closing, her beard and ears moving; thin dawn haze drifts slowly across the valley below; the camera holds still."
run B_marmot stills/B_marmot.png 4 11 "The plump marmot on the boulder rises up tall on her hind legs, chest out, and whistles with a small round mouth, head turning; meadow grass sways in the breeze; the camera holds still."
run C_bench stills/C_bench_v3.png 4 11 "On the wagon bench the bloodhound's long ears lift and swing forward as his head turns toward a far-off sound; the big bear, head in profile, closes his paw around the leather reins and his mouth moves once as he says one word; oak leaves stir above; the camera holds still."
run F_kitten stills/F_drain.png 4 11 "Seen straight down through the iron grate, the tiny grey kitten at the bottom of the drain looks up, opens her mouth in a mew, blinks and shifts in the shallow puddle, the water rippling; slow gentle push in; the grate stays fixed."
run G_forest stills/G_forest.png 5 11 "Night forest, the bloodhound walks slowly along the trail nose down to the ground, sniffing, tail low, the warm lantern glow behind him moving with him across the trunks; the young bear behind the fallen log stays crouched, eyes wide, ears flat, breathing; the camera tracks slowly alongside the dog."
run H_ditch stills/H3_ditch_lantern.png 3 11 "The brass lantern lies in the muddy ditch, its warm flame flickers, sputters and goes out, the warm light fading from the grass and water until only cold moonlight is left; the puddle ripples; the camera holds still."
run I_walkaway stills/I_walkaway.png 4 11 "Seen from behind, the bloodhound and the young bear walk away side by side down the moonlit road into the hills, legs moving, the dog's tail up and wagging, the bear's shoulders rolling; the camera pulls back slowly; the hills stay fixed."
run J_title stills/J_title_hill.png 5 11 "In silhouette against the sunset, the team of four animals pulls the red wagon slowly along the hilltop from left to right, legs moving, the big wheels turning, the two giraffes walking behind, the tiny lantern light flickering; the sunset clouds drift slowly; the camera holds still."
echo "$(date +%T) v3 clips done" >> $log
