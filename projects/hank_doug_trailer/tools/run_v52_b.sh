#!/bin/bash
# run_v52_b.sh — v5.2 picture chain after the owner klein edits: (1) klein: hide the ditch owner's cheek (back of the head only),
# (2) Krea montage stills (jobs_v52_montage.json), (3) LTX-2.5 i2v clips: owner road (row 6), owner ditch fall x2 seeds (row 7),
# then every montage still (fox x2, rollout x2, goat, turtle x2, otters x2); the builder picks by eye afterwards. Training is
# stopped (STOP file) and m5-bigjob armed, so LTX runs full-RAM (no --low-ram). Sequential on purpose (guard).
set -u
cd "$(dirname "$0")/.." || exit 1
SF=$HOME/Desktop/PROJECTS/story-forge; LTX=$SF/bin/make-ltx25; PY=/usr/bin/python3; MEMCLI=$HOME/SongForgeM5/mem_client.py
MFLUX=$HOME/mflux-venv/bin/mflux-generate-flux2-edit
log() { echo "$(date '+%m/%d %H:%M:%S') $*" | tee -a final/run_v52.log; }
songforge_wait() { while :; do jr=$(curl -s -m 4 127.0.0.1:8767/api/status | $PY -c "import sys,json; print(json.load(sys.stdin).get('jobs_running',0))" 2>/dev/null || echo 0)
    [ "${jr:-0}" -eq 0 ] && return; log "Song Forge busy, waiting"; sleep 20; done; }
until grep -q "klein_v52 done" final/run_v52.log; do sleep 10; done
# the first Krea batch (old chain) may still be painting: never two Krea/klein jobs at once
while pgrep -f "krea_batch.py stills/v52|mflux-generate" >/dev/null; do sleep 10; done
# 1. ditch owner: back of the head only
out=stills/v52/DITCH_owner_night2.png
if [ ! -f $out ]; then "$SF/bin/mem-gate" "klein head" && lid=$($PY "$MEMCLI" wait klein-head 45 --timeout 7200 2>/dev/null | tail -1); log "klein -> $out"
  "$MFLUX" --model flux2-klein-9b --image-paths stills/v52/DITCH_owner_night.png --prompt "Same painting, same brushwork, same composition, same man, same coat, same lantern, same night: only his head is turned fully away from us so we see ONLY the back of his hat and the back of his head and collar, no cheek, no ear, no skin, no face visible at all. Everything else unchanged" --steps 4 --guidance 1.0 --seed 2 --output $out >> final/klein_v5.log 2>&1 && log "  ok $out" || log "klein head FAILED"
  [ -n "${lid:-}" ] && $PY "$MEMCLI" release "$lid" >/dev/null 2>&1; fi
# 2. Krea montage stills
log "krea montage stills start"; $PY tools/krea_batch.py stills/v52/jobs_v52_montage.json >> final/krea_v52.log 2>&1; log "krea montage stills done rc=$?"
# 3. LTX clips
STYLE="Painted oil-on-canvas animation, thick brush strokes stay fixed and do not flicker, the camera is locked off and the background does not slide, no new creatures or objects appear, faces keep their exact shape."
ltx() {  # ltx NAME STILL SECONDS SEED PROMPT
  local name=$1 still=$2 secs=$3 seed=$4 prompt=$5; [ -f "clips/v52/$name.mp4" ] && { log "skip $name"; return 0; }
  [ -f "$still" ] || { log "no still for $name ($still)"; return 1; }
  songforge_wait; log "ltx25 $name from $still ($secs s, seed $seed)"
  local out; out=$("$LTX" --i2v "$still" --duration "$secs" --res 832x480 --seed "$seed" --label "hd52_$name" --static "$prompt" 2>>final/clips_v5.log | tail -1)
  local src; src=$(echo "$out" | sed -n 's/.*→ \(.*\)$/\1/p'); [ -n "$src" ] && cp "$src" "clips/v52/$name.mp4"; log "$name $out"
  [ -f "clips/v52/$name.mp4" ] && ffmpeg -v error -y -i "clips/v52/$name.mp4" -vf "fps=2,scale=320:-1,tile=6x2" -frames:v 1 "clips/v52/strips/$name.png"; }
P_ROAD="Static shot, locked off. Night forest road, moonlight. The russet bloodhound trots AWAY from the camera down the road ahead, looking back over his shoulder at the man; the man, seen only from behind, walks after him with long strides, his lantern swinging gently in his hand, the amber light swaying on the road and the trunks; his back stays to the camera the whole time, his face is never seen. Nothing else moves. $STYLE"
P_DITCH="Static shot, locked off. Night road edge, moonlight. The man, seen only from behind, takes one step, his boot slides on the muddy bank, he loses his balance, arms flailing, and topples sideways down into the ditch with a splash, disappearing into the reeds and the water; the lantern flies from his hand, lands in the ditch water and its light goes OUT, the warm amber glow fading until only cold blue moonlight is left. His back stays to the camera, his face is never seen. Nothing else moves. $STYLE"
DH=stills/v52/DITCH_owner_night2.png; [ -f $DH ] || DH=stills/v52/DITCH_owner_night.png
ltx ROAD_owner_v52  stills/v52/ROAD_owner_night.png 4   11 "$P_ROAD"
ltx DITCH_owner_v52 $DH 3.4 11 "$P_DITCH"
ltx DITCH_owner_v52_s12 $DH 3.4 12 "$P_DITCH"
P_FOX="Static shot, locked off. Night forest edge, moonlight. The small red fox caught in the wire fence kicks and struggles, yipping; the young bear grips the two wire strands and pulls them apart, the wires stretching and springing; the fox slips free through the gap, drops to the ground, shakes once and bolts out of frame to the RIGHT. The bear stays where he is. $STYLE"
P_ROLL="Static shot, locked off, wide clean side profile. The whole team walks to the RIGHT across the frame: the horse, zebra, camel and cow walk in step pulling the red wagon, the big spoked wheels turning, the bear and the russet bloodhound sitting still on the bench, the giraffes and elephants walking behind, all four animals of the team staying in frame, dust drifting behind the wheels, the hills behind not sliding. $STYLE"
P_GOAT="Static shot, locked off. The geese beat their wings and climb, the ropes pull taut and the goat in its rope sling rises up and away from the cliff ledge, its legs dangling and swaying gently, the ledge left empty below. Nothing else moves. $STYLE"
P_TURTLE="Static shot, locked off. The elephant tips the wooden barrel further and clear water pours down in a steady stream onto the cracked mud around the stuck turtle; the mud darkens, a puddle spreads and rises, and the turtle lifts its head, paddles its front legs and floats free of the mud as the water lifts it. The turtle's shell and head keep their exact shape. $STYLE"
P_OTTERS="Static shot, locked off. The chain of otters sways gently as the bear's arm pulls it up a little; the bottom otter lifts the wet kitten higher, the kitten wriggles and mews; the other otters hold tight. Nothing else moves. $STYLE"
ltx FOX_fence_v52     stills/v52/FOX_fence_v52.png     4.2 11 "$P_FOX"
ltx ROLLOUT_v52       stills/v52/ROLLOUT_v52.png       5   11 "$P_ROLL"
ltx GOAT_airlift_v52  stills/v52/GOAT_airlift_v52.png  4   11 "$P_GOAT"
ltx TURTLE_v52        stills/v52/TURTLE_v52.png        4   11 "$P_TURTLE"
ltx OTTERS_v52        stills/v52/OTTERS_v52.png        4   11 "$P_OTTERS"
ltx FOX_fence_v52_s2  stills/v52/FOX_fence_v52_s2.png  4.2 11 "$P_FOX"
ltx ROLLOUT_v52_s2    stills/v52/ROLLOUT_v52_s2.png    5   11 "$P_ROLL"
ltx TURTLE_v52_s2     stills/v52/TURTLE_v52_s2.png     4   11 "$P_TURTLE"
ltx OTTERS_v52_s2     stills/v52/OTTERS_v52_s2.png     4   11 "$P_OTTERS"
log "=== run_v52_b done: $(ls clips/v52/*.mp4 2>/dev/null | wc -l | tr -d ' ') clips"
