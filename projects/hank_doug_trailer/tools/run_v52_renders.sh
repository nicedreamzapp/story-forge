#!/bin/bash
# run_v52_renders.sh — v5.2 picture fixes (Matt 1:52-1:55 PM: show the owner falling in the ditch + fix every visible defect).
# Training is running (57 GB resident): every step fits the guard's 51 GB budget one at a time (klein 45, LTX --low-ram 20,
# Krea 40). Nothing here is auto-swapped into the timeline: the builder eye-checks every output first.
#  1. klein (bear/horse protected): D_rollout_right_red2 (v5's edit also turned the horse red), I_walkaway_red2 (Hank went
#     russet), ROAD_owner_red (only if Doug measures a saddle; the hunter must stay).
#  2. LTX-2.5 i2v --low-ram, seed 11 then 12 where noted: rollout (5 s), walkaway (3.7 s), fox re-seed (4.2 s), turtle re-seed
#     (4 s), owner road (4 s), owner ditch fall (3.4 s, 2 seeds).
set -u
cd "$(dirname "$0")/.." || exit 1
SF=$HOME/Desktop/PROJECTS/story-forge; LTX=$SF/bin/make-ltx25; MEMGATE=$SF/bin/mem-gate
MFLUX=$HOME/mflux-venv/bin/mflux-generate-flux2-edit; PY=/usr/bin/python3; MEMCLI=$HOME/SongForgeM5/mem_client.py
LOG=final/run_v52.log; mkdir -p clips/v52 clips/v52/strips stills/v52
log() { echo "$(date '+%m/%d %H:%M:%S') $*" | tee -a "$LOG"; }
eval "$(grep -E '^(STYLE|P_I_WALK|P_ROLLOUT|P_FOX)=' tools/run_v5_renders.sh)"
P_TURTLE="Static shot, locked off. Two long grey elephant trunks swing into the frame from the left and right edges and spray two arcs of water down onto the cracked mud around the stuck turtle; the mud darkens, the water rises and the turtle lifts and floats, his legs paddling, his shell and head keeping their exact shape. $STYLE"
P_ROAD_OWNER="Static shot, locked off. Night forest road, moonlight. The russet bloodhound, small in frame, runs AWAY from the camera down the road toward the bend, looking back over his shoulder; the hunter, seen only from behind, walks after him with long strides, his lantern swinging in his hand, the amber light swaying on the trunks; his back stays to the camera the whole time, his face is never seen. $STYLE"
P_DITCH_OWNER="Static shot, locked off. Night road edge, moonlight. The hunter, seen only from behind, slips: his boot slides down the muddy bank, he topples forward and drops into the ditch with a splash, disappearing into the reeds and water; his lantern flies from his hand, lands in the ditch water and its light goes OUT, the warm amber glow draining away until only cold blue moonlight is left. His back stays to the camera, his face is never seen. Nothing else moves. $STYLE"
songforge_wait() { while :; do jr=$(curl -s -m 4 127.0.0.1:8767/api/status | $PY -c "import sys,json; print(json.load(sys.stdin).get('jobs_running',0))" 2>/dev/null || echo 0)
    [ "${jr:-0}" -eq 0 ] && return; log "Song Forge busy, waiting"; sleep 20; done; }
klein() {  # klein OUT IMG PROMPT
  local out=$1 img=$2 prompt=$3; [ -f "$out" ] && { log "skip $out"; return 0; }
  songforge_wait; "$MEMGATE" "klein $(basename "$out")" || { log "mem-gate refused klein $out"; return 1; }
  local lid; lid=$($PY "$MEMCLI" wait "klein-$(basename "$out" .png)" 45 --timeout 7200 2>/dev/null | tail -1)
  log "klein -> $out"; "$MFLUX" --model flux2-klein-9b --image-paths "$img" canon/doug_master.png --prompt "$prompt" --steps 4 --guidance 1.0 --seed 1 --output "$out" >> final/klein_v5.log 2>&1; local rc=$?
  [ -n "$lid" ] && $PY "$MEMCLI" release "$lid" >/dev/null 2>&1
  [ $rc -eq 0 ] && [ -f "$out" ] && log "  $($PY tools/doug_box_v5.py "$out" | cut -c1-140)" || log "klein FAILED rc=$rc for $out"; }
ltx() {  # ltx NAME STILL SECONDS SEED PROMPT
  local name=$1 still=$2 secs=$3 seed=$4 prompt=$5; [ -f "clips/v52/$name.mp4" ] && { log "skip $name"; return 0; }
  [ -f "$still" ] || { log "no still for $name ($still)"; return 1; }
  songforge_wait; log "ltx25 $name from $still ($secs s, seed $seed, low-ram)"
  local out; out=$("$LTX" --i2v "$still" --duration "$secs" --res 832x480 --seed "$seed" --label "hd52_$name" --static --low-ram "$prompt" 2>>final/clips_v5.log | tail -1)
  local src; src=$(echo "$out" | sed -n 's/.*→ \(.*\)$/\1/p'); [ -n "$src" ] && cp "$src" "clips/v52/$name.mp4"; log "$name $out"
  [ -f "clips/v52/$name.mp4" ] && bash tools/strip.sh "clips/v52/$name.mp4" "clips/v52/strips/$name.png" 24 2>/dev/null; }

log "=== v5.2 renders (pid $$)"
while pgrep -f "krea_batch.py stills/v52" >/dev/null; do sleep 15; done; log "Krea owner stills done: $(ls stills/v52/*.png | xargs -n1 basename | tr '\n' ' ')"
# 1. klein edits, Doug only, everyone else protected
klein stills/v52/D_rollout_right_red2.png stills/v5/D_rollout_flip.png "Repaint ONLY the dog sitting on the wagon bench as the dog in the second image: a solid russet-red bloodhound, no black or tan saddle, same pose, same brushwork. Everything else stays exactly as it is: the brown horse stays a brown horse, the zebra, camel, cow, giraffes and elephants keep their own colours and shapes, the big dark-brown bear beside the dog stays a bear. Everything else in the first image unchanged"
klein stills/v52/I_walkaway_red2.png stills/I_walkaway_s1101.png "Repaint ONLY the dog as the dog in the second image: a solid russet-red bloodhound, no black or tan saddle, same pose, same brushwork. The big dark-brown bear walking beside him stays a dark-brown bear, exactly as he is, same fur, not red, not a dog. Everything else in the first image unchanged"
# Krea painted Doug tan/blond on the owner road still (hue 28, light coat): always klein him red, the hunter protected
klein stills/v52/ROAD_owner_red.png stills/v52/ROAD_owner_v52.png "Repaint ONLY the dog on the road as the dog in the second image: a solid russet-red bloodhound, the same deep red on his back, saddle, ears and legs, no tan, no blond, no black saddle, same pose, same brushwork. The man in the dark coat and hat seen from behind with his lantern stays exactly as he is, same coat, same lantern, still seen from behind. Everything else in the first image unchanged"
# 1b. night-grade the owner ditch still (Krea painted grey dusk; row 6 is blue night). Runs here, in the queue, after the
#     other kleins: the first attempt ran alongside Krea and the guard SIGTERMed it (rc 143).
if [ ! -f stills/v52/DITCH_owner_day.png ]; then
  klein_plain() { local out=$1 img=$2 prompt=$3; songforge_wait; "$MEMGATE" "klein $(basename "$out")" || return 1
    local lid; lid=$($PY "$MEMCLI" wait "klein-$(basename "$out" .png)" 45 --timeout 7200 2>/dev/null | tail -1); log "klein -> $out"
    "$MFLUX" --model flux2-klein-9b --image-paths "$img" --prompt "$prompt" --steps 4 --guidance 1.0 --seed 1 --output "$out" >> final/klein_v5.log 2>&1; local rc=$?
    [ -n "$lid" ] && $PY "$MEMCLI" release "$lid" >/dev/null 2>&1; [ $rc -eq 0 ] && [ -f "$out" ]; }
  if klein_plain stills/v52/DITCH_owner_night.png stills/v52/DITCH_owner_v52.png "Same painting, same brushwork, same composition, same man seen from behind with his lit lantern: turn the scene into deep NIGHT, cold blue moonlight on the road, the reeds and the water, dark blue-green forest, dark sky, the only warm light is the lantern's amber pool on his coat and the ground beside him. Everything else unchanged"; then
    mv stills/v52/DITCH_owner_v52.png stills/v52/DITCH_owner_day.png; cp stills/v52/DITCH_owner_night.png stills/v52/DITCH_owner_v52.png; log "night ditch still in place"
  else log "night klein failed; the day still stays"; fi
fi
# 2. clips
ltx D_rollout_right_v52 stills/v52/D_rollout_right_red2.png 5   11 "$P_ROLLOUT"
ltx I_walkaway_v52      stills/v52/I_walkaway_red2.png      3.7 11 "$P_I_WALK"
ltx FOX_fence_v52       stills/v5/FOX_fence_v5.png          4.2 12 "$P_FOX"
ltx E_turtle_v52        stills/E_turtle.png                 4   12 "$P_TURTLE"
ltx ROAD_owner_v52      stills/v52/ROAD_owner_red.png       4   11 "$P_ROAD_OWNER"
ltx DITCH_owner_v52     stills/v52/DITCH_owner_v52.png      3.4 11 "$P_DITCH_OWNER"
ltx DITCH_owner_v52_s12 stills/v52/DITCH_owner_v52.png      3.4 12 "$P_DITCH_OWNER"
ltx D_rollout_right_v52_s12 stills/v52/D_rollout_right_red2.png 5 12 "$P_ROLLOUT"
log "=== v5.2 renders done: $(ls clips/v52/*.mp4 2>/dev/null | wc -l | tr -d ' ') clips (eye pass next)"
