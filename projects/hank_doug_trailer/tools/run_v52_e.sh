#!/bin/bash
# run_v52_e.sh — after run_v52_d: a LONGER title shot (8 s) so the sung "Hank and Doug" chorus plays out over the title card
# instead of over black; LTX i2v from the hflipped title hill still (team travels right), title text is laid on by finish_v5.
set -u
cd "$(dirname "$0")/.." || exit 1
SF=$HOME/Desktop/PROJECTS/story-forge; LTX=$SF/bin/make-ltx25
log() { echo "$(date '+%m/%d %H:%M:%S') $*" | tee -a final/run_v52.log; }
until grep -q "run_v52_d done" final/run_v52.log; do sleep 10; done
while pgrep -f "krea_batch.py|mflux-generate|make-ltx25|ltx-2-mlx" >/dev/null; do sleep 10; done
STYLE="Painted oil-on-canvas animation, thick brush strokes stay fixed and do not flicker, the camera is locked off and the background does not slide, no new creatures or objects appear, no text, no lettering."
PY=/usr/bin/python3; MEMCLI=$HOME/SongForgeM5/mem_client.py; MFLUX=$HOME/mflux-venv/bin/mflux-generate-flux2-edit
# the v3 title still's camel has two humps (continuity camel_one_hump): klein it to one hump on the flipped still first
if [ ! -f stills/v52/J_title_flip_1hump.png ]; then "$SF/bin/mem-gate" "klein title camel" && lid=$($PY "$MEMCLI" wait klein-title 45 --timeout 7200 2>/dev/null | tail -1); log "klein -> stills/v52/J_title_flip_1hump.png"
  "$MFLUX" --model flux2-klein-9b --image-paths stills/v52/J_title_flip_raw.png --prompt "Same painting, same brushwork, same composition, same sunset: the camel in the team now has exactly ONE hump, a dromedary, same colour and harness. Everything else unchanged: the horse, zebra, cow, the red wagon with its lit lantern, the giraffes, the hill" --steps 4 --guidance 1.0 --seed 1 --output stills/v52/J_title_flip_1hump.png >> final/klein_v5.log 2>&1 && log "  ok J_title_flip_1hump" || log "klein title FAILED"
  [ -n "${lid:-}" ] && $PY "$MEMCLI" release "$lid" >/dev/null 2>&1; fi
STILL=${TITLE_STILL:-stills/v52/J_title_flip_1hump.png}; [ -f "$STILL" ] || STILL=stills/v52/J_title_flip_raw.png
for secs in 8 6; do
  [ -f clips/v52/J_title_v52.mp4 ] && break
  log "ltx25 J_title_v52 from $STILL ($secs s, seed 11)"
  out=$("$LTX" --i2v "$STILL" --duration "$secs" --res 832x480 --seed 11 --label "hd52_J_title" --static "Static shot, locked off, wide. Sunset over rolling hills: the fire wagon and its whole team of animals roll slowly to the RIGHT along the crest of the hill in silhouette, wheels turning, legs walking, the small amber lantern point glowing on the wagon's front post, the giraffes' necks swaying, the clouds drifting very slowly. Nothing else moves. $STYLE" 2>>final/clips_v5.log | tail -1)
  src=$(echo "$out" | sed -n 's/.*→ \(.*\)$/\1/p'); [ -n "$src" ] && cp "$src" clips/v52/J_title_v52.mp4; log "J_title_v52 $out"
done
[ -f clips/v52/J_title_v52.mp4 ] && ffmpeg -v error -y -i clips/v52/J_title_v52.mp4 -vf "fps=2,scale=320:-1,tile=8x2" -frames:v 1 clips/v52/strips/J_title_v52.png
log "=== run_v52_e done"
