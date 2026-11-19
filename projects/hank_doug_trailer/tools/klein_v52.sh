#!/bin/bash
# klein_v52.sh — v5.2 owner stills: Doug red on the road still (hunter protected), then night grades. Training is stopped (STOP file,
# 2:04 PM) and m5-bigjob is armed, so these run back to back. Logs to final/run_v52.log + final/klein_v5.log.
cd "$(dirname "$0")/.." || exit 1
MFLUX=$HOME/mflux-venv/bin/mflux-generate-flux2-edit; PY=/usr/bin/python3; MEMCLI=$HOME/SongForgeM5/mem_client.py; SF=$HOME/Desktop/PROJECTS/story-forge
log() { echo "$(date '+%m/%d %H:%M:%S') $*" | tee -a final/run_v52.log; }
klein() { # OUT PROMPT IMG [REF]
  local out=$1 prompt=$2; shift 2; [ -f "$out" ] && { log "skip $out"; return 0; }
  "$SF/bin/mem-gate" "klein $(basename "$out")" || { log "mem-gate refused $out"; return 1; }
  local lid; lid=$($PY "$MEMCLI" wait "klein-$(basename "$out" .png)" 45 --timeout 7200 2>/dev/null | tail -1)
  log "klein -> $out"; "$MFLUX" --model flux2-klein-9b --image-paths "$@" --prompt "$prompt" --steps 4 --guidance 1.0 --seed ${SEED:-1} --output "$out" >> final/klein_v5.log 2>&1; local rc=$?
  [ -n "$lid" ] && $PY "$MEMCLI" release "$lid" >/dev/null 2>&1; [ $rc -eq 0 ] && [ -f "$out" ] && log "  ok $out" || log "klein FAILED rc=$rc $out"; }
NIGHT="Same painting, same brushwork, same composition, everything in the same place: turn the scene into deep NIGHT, cold blue moonlight on the road, the reeds and the water, dark blue-green forest, dark night sky, the only warm light is the lantern's amber glow. Nothing else changes"
klein stills/v52/ROAD_owner_red.png "Repaint ONLY the dog on the road as the dog in the second image: a solid russet-red bloodhound, the same deep red on his back, saddle, ears and legs, no tan, no blond, no black saddle, same pose, same brushwork. The man in the dark coat and hat seen from behind with his lantern stays exactly as he is, same coat, same lantern, still seen from behind. Everything else in the first image unchanged" stills/v52/ROAD_owner_v52.png canon/doug_master.png
klein stills/v52/ROAD_owner_night.png "$NIGHT. The dog stays the same solid russet-red bloodhound, the man stays exactly as he is, seen from behind" stills/v52/ROAD_owner_red.png
klein stills/v52/DITCH_owner_night.png "$NIGHT. The man stays exactly as he is, seen from behind, his face hidden" stills/v52/DITCH_owner_v52.png
klein stills/v52/DITCH_owner_down_night.png "Same painting, same brushwork, same composition, everything in the same place: turn the scene into deep NIGHT, cold blue moonlight on the ditch water, the reeds and the road, dark blue-green forest, dark night sky; the lantern lies dark with its flame out, no warm light anywhere. The man stays exactly as he is, face down, face hidden" stills/v52/DITCH_owner_down_v52.png
log "klein_v52 done"
