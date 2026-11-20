#!/bin/bash
# v5.1 row 1: re-render G_hunt_red without the hallucinated hand + lantern (Matt 1:01 PM). LTX-2.5 i2v --low-ram (training
# is running; the guard seats 20 GB), seed 12, same still + prompt with the no-hand wording doubled. Up to 2 seeds; each
# result is eye-checked by the builder before it goes into the timeline (no auto-swap).
set -u; cd "$(dirname "$0")/.." || exit 1
LTX=$HOME/Desktop/PROJECTS/story-forge/bin/make-ltx25; LOG=final/run_v51.log
log() { echo "$(date '+%m/%d %H:%M:%S') $*" | tee -a "$LOG"; }
STYLE="Painted oil-on-canvas animation, thick brush strokes stay fixed and do not flicker, the camera is locked off and the background does not slide, no new creatures or objects appear, no lantern, no person, no hands, no arms, nobody holds anything, faces keep their exact shape."
P="Static shot, locked off. Night forest trail, moonlight. The russet bloodhound walks slowly to the LEFT along the trail, nose down on the ground, dipping his nose to the dirt three times, tail low; the warm amber glow on the trunks behind him sways slowly from side to side, its source stays out of frame, no lantern and no hand ever appear. Nothing else moves. $STYLE"
for sd in 12 13; do
  out=clips/v5/G_hunt_red_s$sd.mp4; [ -f "$out" ] && continue
  log "ltx25 G_hunt_red seed $sd (low-ram)"
  r=$("$LTX" --i2v stills/v5/G_hunt_red.png --duration 5 --res 832x480 --seed $sd --label hd51_G_hunt_s$sd --static --low-ram "$P" 2>>final/clips_v5.log | tail -1)
  src=$(echo "$r" | sed -n 's/.*→ \(.*\)$/\1/p'); [ -n "$src" ] && cp "$src" "$out"; log "G_hunt seed $sd: $r"
  [ -f "$out" ] && bash tools/strip.sh "$out" "clips/v5/strips/G_hunt_red_s$sd.png" 24 2>/dev/null
done
log "hunt re-renders done"
