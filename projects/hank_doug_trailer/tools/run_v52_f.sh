#!/bin/bash
# run_v52_f.sh — after run_v52_e: the rollout colour fix the right way. Two full-frame kleins (flip_red, s2_red) both turned the COW
# maroon instead of the dog (same failure twice -> change approach): region-only klein edits on the original seed-2 still
# (bench crop: Doug solid russet; post crop: bell -> unlit brass lantern), feather-blended back, then LTX.
set -u
cd "$(dirname "$0")/.." || exit 1
SF=$HOME/Desktop/PROJECTS/story-forge; LTX=$SF/bin/make-ltx25; PY=$HOME/chatterbox-env/bin/python
log() { echo "$(date '+%m/%d %H:%M:%S') $*" | tee -a final/run_v52.log; }
until grep -q "run_v52_e done" final/run_v52.log; do sleep 10; done
while pgrep -f "krea_batch.py|mflux-generate|make-ltx25|ltx-2-mlx" >/dev/null; do sleep 10; done
"$SF/bin/mem-gate" "klein rollout regions" || exit 1
log "region klein: bench (Doug russet)"
$PY tools/region_klein_v52.py stills/v52/ROLLOUT_v52_s2.png stills/v52/ROLLOUT_fix_a.png 790 230 1070 500 "Repaint ONLY the dog sitting on the wagon bench as the dog in the second image: one solid deep russet-red bloodhound coat all over, the same red on his back, head, ears and legs, no tan, no orange, same pose, same brushwork. The big dark-brown bear beside him, the red wagon and the post stay exactly the same" canon/doug_master.png >> final/klein_v5.log 2>&1 && log "  ok ROLLOUT_fix_a" || log "region klein a FAILED"
log "region klein: post (bell -> unlit lantern)"
$PY tools/region_klein_v52.py stills/v52/ROLLOUT_fix_a.png stills/v52/ROLLOUT_fix.png 740 240 900 420 "Same painting, same brushwork: replace the brass bell hanging from the iron post with a dented brass hand lantern hanging from the hook, UNLIT, dark glass, no glow. Everything else unchanged" >> final/klein_v5.log 2>&1 && log "  ok ROLLOUT_fix" || { log "region klein b FAILED"; cp stills/v52/ROLLOUT_fix_a.png stills/v52/ROLLOUT_fix.png; }
STYLE="Painted oil-on-canvas animation, thick brush strokes stay fixed and do not flicker, the camera is locked off and the background does not slide, no new creatures or objects appear, faces keep their exact shape."
P_ROLL="Static shot, locked off, wide clean side profile. The whole team walks to the RIGHT across the frame: the horse, zebra, camel and cow walk in step pulling the red wagon, the big spoked wheels turning, the bear and the russet bloodhound sitting still on the bench, the giraffes and elephant walking behind, all four animals of the team staying in frame, dust drifting behind the wheels, the hills behind not sliding. $STYLE"
if [ ! -f clips/v52/ROLLOUT_fix_v52.mp4 ]; then log "ltx25 ROLLOUT_fix_v52 from stills/v52/ROLLOUT_fix.png (5 s, seed 11)"
  out=$("$LTX" --i2v stills/v52/ROLLOUT_fix.png --duration 5 --res 832x480 --seed 11 --label hd52_ROLLOUT_fix --static "$P_ROLL" 2>>final/clips_v5.log | tail -1)
  src=$(echo "$out" | sed -n 's/.*→ \(.*\)$/\1/p'); [ -n "$src" ] && cp "$src" clips/v52/ROLLOUT_fix_v52.mp4; log "ROLLOUT_fix_v52 $out"
  [ -f clips/v52/ROLLOUT_fix_v52.mp4 ] && ffmpeg -v error -y -i clips/v52/ROLLOUT_fix_v52.mp4 -vf "fps=2,scale=320:-1,tile=6x2" -frames:v 1 clips/v52/strips/ROLLOUT_fix_v52.png; fi
log "=== run_v52_f done"
