#!/bin/bash
# run_v52_c.sh — after run_v52_b: (1) rollout: the Krea still travels LEFT, so hflip -> klein (Doug solid russet, lantern unlit,
# nothing else) -> LTX; (2) fox: both Krea seeds painted the fox free on the ground, so klein tangles it into the wires on seed 2
# -> LTX; (3) LTX re-seed of the v5 fox still (fox hanging by a hind leg) with a "stays hanging, then drops" prompt.
set -u
cd "$(dirname "$0")/.." || exit 1
SF=$HOME/Desktop/PROJECTS/story-forge; LTX=$SF/bin/make-ltx25; PY=/usr/bin/python3; MEMCLI=$HOME/SongForgeM5/mem_client.py
MFLUX=$HOME/mflux-venv/bin/mflux-generate-flux2-edit
log() { echo "$(date '+%m/%d %H:%M:%S') $*" | tee -a final/run_v52.log; }
until grep -q "run_v52_b done" final/run_v52.log; do sleep 10; done
while pgrep -f "krea_batch.py|mflux-generate|make-ltx25|ltx-2-mlx" >/dev/null; do sleep 10; done
klein() { local out=$1 prompt=$2; shift 2; [ -f "$out" ] && { log "skip $out"; return 0; }
  "$SF/bin/mem-gate" "klein $(basename "$out")" || { log "mem-gate refused $out"; return 1; }
  local lid; lid=$($PY "$MEMCLI" wait "klein-$(basename "$out" .png)" 45 --timeout 7200 2>/dev/null | tail -1); log "klein -> $out"
  "$MFLUX" --model flux2-klein-9b --image-paths "$@" --prompt "$prompt" --steps 4 --guidance 1.0 --seed ${SEED:-1} --output "$out" >> final/klein_v5.log 2>&1; local rc=$?
  [ -n "$lid" ] && $PY "$MEMCLI" release "$lid" >/dev/null 2>&1; [ $rc -eq 0 ] && [ -f "$out" ] && log "  ok $out" || log "klein FAILED rc=$rc $out"; }
STYLE="Painted oil-on-canvas animation, thick brush strokes stay fixed and do not flicker, the camera is locked off and the background does not slide, no new creatures or objects appear, faces keep their exact shape."
ltx() { local name=$1 still=$2 secs=$3 seed=$4 prompt=$5; [ -f "clips/v52/$name.mp4" ] && { log "skip $name"; return 0; }
  [ -f "$still" ] || { log "no still for $name ($still)"; return 1; }
  log "ltx25 $name from $still ($secs s, seed $seed)"
  local out; out=$("$LTX" --i2v "$still" --duration "$secs" --res 832x480 --seed "$seed" --label "hd52_$name" --static "$prompt" 2>>final/clips_v5.log | tail -1)
  local src; src=$(echo "$out" | sed -n 's/.*→ \(.*\)$/\1/p'); [ -n "$src" ] && cp "$src" "clips/v52/$name.mp4"; log "$name $out"
  [ -f "clips/v52/$name.mp4" ] && ffmpeg -v error -y -i "clips/v52/$name.mp4" -vf "fps=2,scale=320:-1,tile=6x2" -frames:v 1 "clips/v52/strips/$name.png"; }
klein stills/v52/ROLLOUT_flip_red.png "Repaint ONLY the dog on the wagon bench as the dog in the second image: one solid deep russet-red bloodhound, the same red on his back, ears and legs, no tan, no orange, no black saddle, same pose, same brushwork; and the hanging brass lantern is UNLIT, dark glass, no glow, no light. Everything else in the first image stays exactly the same: the dark-brown bear, the horse, zebra, camel, cow, giraffes, elephants, the red wagon, the hills" stills/v52/ROLLOUT_v52_flip.png canon/doug_master.png
klein stills/v52/FOX_tangle.png "Same painting, same brushwork, same bear in the same pose: the small red fox is now CAUGHT IN the wire fence, its body wedged between the two middle wire strands, the wires pressing into its back and belly, its head and front paws through on the near side and its hind legs stuck on the far side, twisting, mouth open in a frightened yip. Everything else unchanged" stills/v52/FOX_fence_v52_s2.png
P_ROLL="Static shot, locked off, wide clean side profile. The whole team walks to the RIGHT across the frame: the horse, zebra, camel and cow walk in step pulling the red wagon, the big spoked wheels turning, the bear and the russet bloodhound sitting still on the bench, the giraffes and elephants walking behind, all four animals of the team staying in frame, dust drifting behind the wheels, the hills behind not sliding. $STYLE"
P_FOXT="Static shot, locked off. Night forest edge, moonlight. The small red fox caught between the wires twists and kicks, yipping; the young bear grips the two wire strands and pulls them apart, the wires stretching wide; the fox slips free through the gap, drops to the grass, shakes once and bolts out of frame to the RIGHT. The bear stays where he is. $STYLE"
P_FOXH="Static shot, locked off. Night forest edge, moonlight. The small red fox hangs upside-down by one hind leg from the top wire, dangling and kicking its free legs, yipping, and STAYS hanging while the young bear up on his hind legs hooks both front paws into the wire and pulls the strands apart; then the fox's leg comes free, it drops straight down to the grass, lands on all fours, shakes once and bolts out of frame to the RIGHT. The bear stays where he is. $STYLE"
ltx ROLLOUT_flip_v52 stills/v52/ROLLOUT_flip_red.png 5 11 "$P_ROLL"
ltx FOX_tangle_v52   stills/v52/FOX_tangle.png        4.2 11 "$P_FOXT"
ltx FOX_hang_v52     stills/v5/FOX_fence_v5.png       4.2 12 "$P_FOXH"
log "=== run_v52_c done"
