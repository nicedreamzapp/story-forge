#!/bin/bash
# night-grade the owner ditch still (Krea painted it as grey dusk; row 6 is blue night). Writes DITCH_owner_night.png then
# swaps it in as DITCH_owner_v52.png (the day one kept as _day) so the queued ditch clips render from the night version.
cd "$(dirname "$0")/.."; SF=$HOME/Desktop/PROJECTS/story-forge; PY=/usr/bin/python3; MEMCLI=$HOME/SongForgeM5/mem_client.py
log() { echo "$(date '+%m/%d %H:%M:%S') $*" | tee -a final/run_v52.log; }
while :; do jr=$(curl -s -m 4 127.0.0.1:8767/api/status | $PY -c "import sys,json; print(json.load(sys.stdin).get('jobs_running',0))" 2>/dev/null || echo 0); [ "${jr:-0}" -eq 0 ] && break; sleep 20; done
"$SF/bin/mem-gate" "klein night ditch" || { log "mem-gate refused the night klein"; exit 1; }
lid=$($PY "$MEMCLI" wait klein-DITCH_night 45 --timeout 7200 2>/dev/null | tail -1); log "klein night -> stills/v52/DITCH_owner_night.png"
$HOME/mflux-venv/bin/mflux-generate-flux2-edit --model flux2-klein-9b --image-paths stills/v52/DITCH_owner_v52.png --prompt "Same painting, same brushwork, same composition, same man seen from behind with his lit lantern: turn the scene into deep NIGHT, cold blue moonlight on the road, the reeds and the water, dark blue-green forest, dark sky, the only warm light is the lantern's amber pool on his coat and the ground beside him. Everything else unchanged" --steps 4 --guidance 1.0 --seed 1 --output stills/v52/DITCH_owner_night.png >> final/klein_v5.log 2>&1; rc=$?
[ -n "$lid" ] && $PY "$MEMCLI" release "$lid" >/dev/null 2>&1
if [ $rc -eq 0 ] && [ -f stills/v52/DITCH_owner_night.png ]; then mv stills/v52/DITCH_owner_v52.png stills/v52/DITCH_owner_day.png; cp stills/v52/DITCH_owner_night.png stills/v52/DITCH_owner_v52.png; log "night ditch still in place"; else log "night klein FAILED rc=$rc (day still stays)"; fi
