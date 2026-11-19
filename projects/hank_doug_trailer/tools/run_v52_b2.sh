#!/bin/bash
# run_v52_b2.sh — trims chain b: after the GOAT render finishes, render only OTTERS_v52_s2 (the still picked by eye), skip the
# unfixed rollout seed 2 / turtle / fox seed 2 / otters seed 1 renders (their fixed versions come in chains c and d), then
# release chains c, d, e with the "run_v52_b done" line.
set -u
cd "$(dirname "$0")/.." || exit 1
SF=$HOME/Desktop/PROJECTS/story-forge; LTX=$SF/bin/make-ltx25
log() { echo "$(date '+%m/%d %H:%M:%S') $*" | tee -a final/run_v52.log; }
while pgrep -f "make-ltx25|ltx-2-mlx" >/dev/null; do sleep 5; done
STYLE="Painted oil-on-canvas animation, thick brush strokes stay fixed and do not flicker, the camera is locked off and the background does not slide, no new creatures or objects appear, faces keep their exact shape."
P_OTTERS="Static shot, locked off. The otters lean further into the open drain, the bottom otter lifting the wet kitten up toward the bear's paw; the kitten wriggles and mews, the bear's paw closes gently around it and lifts it clear of the water; nothing else moves. $STYLE"
if [ ! -f clips/v52/OTTERS_v52_s2.mp4 ]; then log "ltx25 OTTERS_v52_s2 from stills/v52/OTTERS_v52_s2.png (4 s, seed 11)"
  out=$("$LTX" --i2v stills/v52/OTTERS_v52_s2.png --duration 4 --res 832x480 --seed 11 --label hd52_OTTERS_v52_s2 --static "$P_OTTERS" 2>>final/clips_v5.log | tail -1)
  src=$(echo "$out" | sed -n 's/.*→ \(.*\)$/\1/p'); [ -n "$src" ] && cp "$src" clips/v52/OTTERS_v52_s2.mp4; log "OTTERS_v52_s2 $out"
  [ -f clips/v52/OTTERS_v52_s2.mp4 ] && ffmpeg -v error -y -i clips/v52/OTTERS_v52_s2.mp4 -vf "fps=2,scale=320:-1,tile=6x2" -frames:v 1 clips/v52/strips/OTTERS_v52_s2.png; fi
[ -f clips/v52/GOAT_airlift_v52.mp4 ] && ffmpeg -v error -y -i clips/v52/GOAT_airlift_v52.mp4 -vf "fps=2,scale=320:-1,tile=6x2" -frames:v 1 clips/v52/strips/GOAT_airlift_v52.png
log "=== run_v52_b done (trimmed by b2)"
