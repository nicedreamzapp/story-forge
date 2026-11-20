#!/bin/bash
# v4 NEW clips (LTX-2.5 distilled i2v). Each waits for its still; Krea must be done (one heavy model at a time).
cd "$(dirname "$0")/.."; LTX=~/Desktop/PROJECTS/story-forge/bin/make-ltx25; log=clips/v4/run.log
STYLE="Painted oil-on-canvas animation, thick brush strokes stay fixed and do not flicker, the camera is locked off and the background does not slide, no new creatures or objects appear, no lantern, no person, no hands, faces keep their exact shape."
run() { [ -f "clips/v4/$1.mp4" ] && return
  while [ ! -f "$2" ] || pgrep -f krea_batch.py >/dev/null; do sleep 8; done
  out=$($LTX --i2v "$2" --duration $3 --res 832x480 --seed $4 --label "hd4_$1" "$5 $STYLE" 2>>$log | tail -1)
  src=$(echo "$out" | sed -n 's/.*→ \(.*\)$/\1/p'); [ -n "$src" ] && cp "$src" "clips/v4/$1.mp4"; echo "$(date +%T) $1 $out" >> $log; }
run NEW1_hunt stills/v4/G_hunt_fix.png 5 11 "Night forest. The bloodhound walks slowly to the left along the trail, nose down on the ground, sniffing, dipping his nose to the dirt three times; the warm glow on the trunks behind him sways gently from side to side as if a lantern were swinging out of frame."
run NEW2_lookback stills/v4/Doug_close_glow_fix.png 4 11 "Night forest close shot. The warm glow on the trunks behind the bloodhound swings hard across them and across his face at about one second; at that moment his head turns back over his shoulder toward the light, ears going back, eyes low; then he holds, breathing."
run NEW3_fox stills/v4/FOX_fence_fix.png 5 11 "Night forest edge. The small red fox caught in the wire fence kicks and yips, mouth opening; the young bear, up on his hind legs, pulls the wire strands apart with both front paws, the fence creaking and springing; the fox drops free to the ground, shakes, and bolts away into the dark to the right."
run NEW4_watch stills/v4/Doug_watch_fix.png 4 11 "Night forest close shot. The bloodhound lying low in the ferns watches toward the right; his ears lift, his eyes soften, and his tail begins to wag against the leaves behind him, thumping three times; the ferns stir."
run NEW5_lead stills/v4/ROAD_ditch_fix.png 4 11 "Night forest road. The bloodhound runs along the road toward the bend ahead, looking back over his shoulder and barking, mouth opening three times, paws pounding the dirt; the warm glow behind him lurches forward and sweeps along the trunks after him; the ditch at the bend stays dark and still."
echo "$(date +%T) v4 clips done" >> $log
