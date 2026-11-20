#!/bin/bash
# run_v52_d.sh — after run_v52_c: rollout seed 2 (travels RIGHT, team all visible) gets Doug solid russet + an unlit brass lantern
# where Krea painted a bell; the turtle still gets sunk into the cracked mud (Krea painted it standing free). Then LTX both.
set -u
cd "$(dirname "$0")/.." || exit 1
SF=$HOME/Desktop/PROJECTS/story-forge; LTX=$SF/bin/make-ltx25; PY=/usr/bin/python3; MEMCLI=$HOME/SongForgeM5/mem_client.py
MFLUX=$HOME/mflux-venv/bin/mflux-generate-flux2-edit
log() { echo "$(date '+%m/%d %H:%M:%S') $*" | tee -a final/run_v52.log; }
until grep -q "run_v52_c done" final/run_v52.log; do sleep 10; done
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
klein stills/v52/ROLLOUT_s2_red.png "Repaint ONLY the dog on the wagon bench as the dog in the second image: one solid deep russet-red bloodhound, the same red on his back, ears and legs, no tan, no orange, no black saddle, same pose, same brushwork; and replace the brass bell on the wagon's front post with a dented brass hand lantern hanging UNLIT from the iron hook, dark glass, no glow. Everything else in the first image stays exactly the same: the dark-brown bear, the horse, zebra, camel, cow, giraffes, elephant, the red wagon, the hills" stills/v52/ROLLOUT_v52_s2.png canon/doug_master.png
klein stills/v52/TURTLE_sunk.png "Same painting, same brushwork, same elephant, same barrel and pouring water: the small green turtle is now STUCK, sunk down into the cracked dry mud up to the rim of its shell, only the top of its shell, its head and its front legs showing above the hard mud plates, head stretched up, mouth open. Everything else unchanged" stills/v52/TURTLE_v52.png
P_ROLL="Static shot, locked off, wide clean side profile. The whole team walks to the RIGHT across the frame: the horse, zebra, camel and cow walk in step pulling the red wagon, the big spoked wheels turning, the bear and the russet bloodhound sitting still on the bench, the giraffes and elephant walking behind, all four animals of the team staying in frame, dust drifting behind the wheels, the hills behind not sliding. $STYLE"
P_TURTLE="Static shot, locked off. The elephant tips the wooden barrel further and clear water pours down in a steady stream onto the cracked mud around the stuck turtle; the mud darkens, a puddle spreads and rises, and the turtle lifts its head, paddles its front legs and floats free of the mud as the water lifts it. The turtle's shell and head keep their exact shape. $STYLE"
ltx ROLLOUT_s2_v52 stills/v52/ROLLOUT_s2_red.png 5 11 "$P_ROLL"
ltx TURTLE_sunk_v52 stills/v52/TURTLE_sunk.png 4 11 "$P_TURTLE"
log "=== run_v52_d done"
