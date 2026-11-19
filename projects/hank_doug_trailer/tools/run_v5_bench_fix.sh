#!/bin/bash
# run_v5_bench_fix.sh — 11/18 12:35 PM. The v5 Doug gate held the film: the klein red edit of the bench still
# (stills/v5/C_bench_red.png) had turned HANK into a second red dog (continuity: doug_colour NO on r10_bench, hank_colour
# broken). Fix: stop the life-model training again (Matt's OK stands for these renders), m5-bigjob start, klein edit the
# bench still with the bear protected in the prompt and a bear-unchanged numeric gate, re-render the a2v bench clip the way
# the main script did (Hank's "Rolling." wav), gate the clip too, then hand over to run_v5_doug_all.sh (resumes: finish,
# gates, Doug gate, publish, text, m5-bigjob end, training restart). No loops: a gate that fails twice stops and reports.
set -u
cd "$(dirname "$0")/.." || exit 1
PROJ=$(pwd); SF=$HOME/Desktop/PROJECTS/story-forge
LTX=$SF/bin/make-ltx25; MEMGATE=$SF/bin/mem-gate; MFLUX=$HOME/mflux-venv/bin/mflux-generate-flux2-edit
PY=/usr/bin/python3; MEMCLI=$HOME/SongForgeM5/mem_client.py; SF_ENV="${STORY_FORGE_ENV:-$HOME/.config/story-forge/publish.env}"; if [ -f "$SF_ENV" ]; then . "$SF_ENV"; fi; CHAT="${SF_CHAT:-}"
TRAIN_RUN=$HOME/life-model/runs/full2-20261118-1003
LOG=$PROJ/final/run_v5_bench_fix.log
log() { echo "$(date '+%m/%d %H:%M:%S') $*" | tee -a "$LOG"; }
die() { log "STOP: $*"; chat-send "$CHAT" "bench fix STOP: $*" >/dev/null 2>&1; exit 1; }
STYLE="Painted oil-on-canvas animation, thick brush strokes stay fixed and do not flicker, the camera is locked off and the background does not slide, no new creatures or objects appear, no lantern, no person, no hands, faces keep their exact shape."
KLEIN_BENCH="Repaint only the dog on the left in the first image as the dog in the second image: a solid russet-red bloodhound, the same red on his back, saddle and ears, no black or tan saddle, same pose, same brushwork. The big dark-brown grizzly bear sitting on the right stays a bear, exactly as he is, same brown fur, same face, not a dog. Everything else in the first image unchanged"
P_BENCH="Hank the bear in profile on the wagon bench says one word, his jaw opening wide on it and closing; beside him the russet bloodhound's ears flip up and his head turns toward the bear. Static shot, locked off. $STYLE"
RES=832x480; SEED=11
# boxes (1344x768 still): Doug 580 110 780 510 saddle 600 200 740 340 (run_v5_renders); bear 735 60 1050 610 (12:33 PM).
# Before: bear box warm-coat fraction 26%, median S 0.52; the bad edit: 64%, S 0.85. Gate: fraction <= 40 AND S <= 0.65.
measure() { $PY tools/doug_hue_v5.py "$@"; }
num() { echo "$1" | sed -n "s/.*$2 *\(-\{0,1\}[0-9.]*\).*/\1/p"; }
doug_ok() { local m; m=$(measure "$@"); log "  doug: $m"; local h d; h=$(num "$m" "hue"); d=$(echo "$m" | sed -n 's/.*fraction \([0-9]*\)%.*/\1/p')
  $PY -c "import sys; sys.exit(0 if abs($h-20)<=6 and $d<=30 else 1)"; }
# clip gate (12:42 PM): hue + bear only. On this pose the "saddle" box lands on Doug's black collar and shaded chest
# (hue 20, V 0.21), not a saddle; the VL doug_colour rule in doug_all and the eye on the strip judge the saddle.
doug_hue_ok() { local m; m=$(measure "$@"); log "  doug: $m"; local h; h=$(num "$m" "hue"); $PY -c "import sys; sys.exit(0 if abs($h-20)<=8 else 1)"; }
bear_ok() { local m; m=$(measure "$@"); log "  bear: $m"; local f s; f=$(echo "$m" | sed -n 's/.*(n=[0-9]*, \([0-9]*\)% of box).*/\1/p'); s=$(num "$m" "median S")
  $PY -c "import sys; sys.exit(0 if $f<=40 and $s<=0.65 else 1)"; }

log "=== bench fix (pid $$)"
# ---------------------------------------------------------------- 1. training off again, M5 free (Matt "Fix it" 12:35 PM)
# Same way as 10:55: kill the wrapper (its TERM trap touches STOP so train saves and exits cleanly, and nothing retries),
# the pause watcher, then wait for the trainer to exit on its own; only then SIGTERM it if it is still there after 5 min.
if pgrep -f train_full.py >/dev/null; then
  w=$(cat "$TRAIN_RUN/wrapper.pid" 2>/dev/null); tp=$(cat "$TRAIN_RUN/train.pid" 2>/dev/null)
  [ -n "$w" ] && kill "$w" 2>/dev/null; pkill -f "$TRAIN_RUN/watch.sh" 2>/dev/null; pkill -f "watch.sh $tp" 2>/dev/null; touch "$TRAIN_RUN/STOP"
  log "training wrapper $w + watcher stopped, STOP set; waiting for trainer $tp to save and exit"
  for i in $(seq 1 30); do pgrep -f train_full.py >/dev/null || break; sleep 10; done
  pgrep -f train_full.py >/dev/null && { kill "$tp" 2>/dev/null; sleep 20; }
  pgrep -f train_full.py >/dev/null && die "training did not stop in 5 min"
  log "training exited: $(tail -1 "$TRAIN_RUN/train.log" | cut -c1-120)"
fi
curl -s -m 5 http://127.0.0.1:8790/api/state | $PY -c "
import sys,json,subprocess; d=json.load(sys.stdin)
for l in d['leases']:
    if l['used_gb']==0: print('releasing orphan lease', l['name'], l['id']); subprocess.run(['$PY','$MEMCLI','release',l['id']])" | tee -a "$LOG"
for try in 1 2; do out=$(m5-bigjob start 2>&1); rc=$?; log "m5-bigjob start (try $try) rc=$rc: $(echo "$out" | tail -1)"; [ $rc -eq 0 ] && break; sleep 60; done
[ $rc -eq 0 ] || die "m5-bigjob start failed twice"
touch /tmp/hd5_bigjob_on   # run_v5_doug_all.sh sees this, skips its own start and runs m5-bigjob end at exit

# ---------------------------------------------------------------- 2. klein edit with the bear protected
# 12:40 PM resume: seed 1 (hue 18, no saddle, bear intact) was picked BY EYE and put in place with tools/BENCH_STILL_OK;
# the numeric saddle box (600-740) was catching the bear's dark fur next to Doug's narrower pose, not a saddle.
if [ -f tools/BENCH_STILL_OK ] && [ -f stills/v5/C_bench_red.png ]; then log "bench still already approved by eye (tools/BENCH_STILL_OK), skipping klein"; else
# ---------------------------------------------------------------- 2. klein edit with the bear protected
rm -f stills/v5/C_bench_red.png   # the loser
ok=0
for sd in 1 2; do
  "$MEMGATE" "klein C_bench_red" || die "mem-gate refused klein"
  lid=$($PY "$MEMCLI" wait klein-C_bench_red 45 --timeout 7200 2>/dev/null | tail -1)
  log "klein -> stills/v5/C_bench_red.png (seed $sd, bear protected)"
  "$MFLUX" --model flux2-klein-9b --image-paths stills/C_bench_v3.png canon/doug_master.png --prompt "$KLEIN_BENCH" --steps 4 --guidance 1.0 --seed $sd --output stills/v5/C_bench_red.png >> final/klein_v5.log 2>&1; rc=$?
  [ -n "$lid" ] && $PY "$MEMCLI" release "$lid" >/dev/null 2>&1
  [ $rc -eq 0 ] && [ -f stills/v5/C_bench_red.png ] || { log "klein rc=$rc"; continue; }
  d=0; b=0; doug_ok stills/v5/C_bench_red.png 580 110 780 510 s 600 200 740 340 || d=1; bear_ok stills/v5/C_bench_red.png 735 60 1050 610 || b=1
  if [ $d = 0 ] && [ $b = 0 ]; then ok=1; log "seed $sd passes (Doug red, bear unchanged)"; break; fi
  log "seed $sd fails (doug_fail=$d bear_fail=$b)"; mv stills/v5/C_bench_red.png "stills/v5/C_bench_red_s${sd}_fail.png"
done
if [ $ok = 0 ]; then   # mask the klein edit to Doug's region only: Doug's box from the last klein output, feathered, over the original
  src=$(ls -t stills/v5/C_bench_red_s*_fail.png | head -1); [ -n "$src" ] || die "no klein output to mask"
  $PY - "$src" <<'PYEOF' | tee -a "$LOG"
import sys, cv2, numpy as np
src = cv2.imread(sys.argv[1]); base = cv2.imread("stills/C_bench_v3.png")
m = np.zeros(base.shape[:2], np.float32); m[110:510, 560:790] = 1.0          # Doug's box with a little air
m = cv2.GaussianBlur(m, (41, 41), 0)[..., None]
out = (src.astype(np.float32) * m + base.astype(np.float32) * (1 - m)).clip(0, 255).astype(np.uint8)
cv2.imwrite("stills/v5/C_bench_red.png", out); print("masked edit written: Doug's box from", sys.argv[1], "over C_bench_v3")
PYEOF
  doug_ok stills/v5/C_bench_red.png 580 110 780 510 s 600 200 740 340 || die "masked edit: Doug still fails the colour gate"
  bear_ok stills/v5/C_bench_red.png 735 60 1050 610 || die "masked edit: bear box changed (should be impossible)"
fi
# eye check before animating (coordinator 12:35): the builder looks at the still and touches tools/BENCH_STILL_OK (or _BAD)
rm -f tools/BENCH_STILL_OK tools/BENCH_STILL_BAD; log "WAITING for the eye check: stills/v5/C_bench_red.png -> touch tools/BENCH_STILL_OK"
while [ ! -f tools/BENCH_STILL_OK ]; do [ -f tools/BENCH_STILL_BAD ] && die "bench still rejected by eye"; sleep 10; done; log "bench still approved by eye"

fi
# ---------------------------------------------------------------- 3. the a2v bench clip, as the main script made it
log "ltx25 a2v C_bench_red (Hank's Rolling. wav)"
out=$("$LTX" --i2v stills/v5/C_bench_red.png --audio voices/L1_hank_rolling.wav --res $RES --seed $SEED --label hd5_C_bench_red "$P_BENCH" 2>>final/clips_v5.log | tail -1)
src=$(echo "$out" | sed -n 's/.*→ \(.*\)$/\1/p'); [ -n "$src" ] && cp "$src" clips/v5/C_bench_red.mp4; log "C_bench_red $out"
[ -f clips/v5/C_bench_red.mp4 ] || die "a2v bench clip did not land (final/clips_v5.log)"
bash tools/strip.sh clips/v5/C_bench_red.mp4 clips/v5/strips/C_bench_red.png 24 2>/dev/null
# clip gate on the mid frame (832x480: boxes scaled by 0.619)
ffmpeg -v error -y -ss 2.0 -i clips/v5/C_bench_red.mp4 -frames:v 1 /tmp/hd5_bench_mid.png
cd=0; cb=0; doug_hue_ok /tmp/hd5_bench_mid.png 359 68 483 316 || cd=1; bear_ok /tmp/hd5_bench_mid.png 455 37 650 378 || cb=1
if [ $cd = 1 ] || [ $cb = 1 ]; then
  log "clip gate failed once (doug_fail=$cd bear_fail=$cb); one re-render with seed 12"
  rm -f clips/v5/C_bench_red.mp4
  out=$("$LTX" --i2v stills/v5/C_bench_red.png --audio voices/L1_hank_rolling.wav --res $RES --seed 12 --label hd5_C_bench_red_s12 "$P_BENCH" 2>>final/clips_v5.log | tail -1)
  src=$(echo "$out" | sed -n 's/.*→ \(.*\)$/\1/p'); [ -n "$src" ] && cp "$src" clips/v5/C_bench_red.mp4; log "C_bench_red (seed 12) $out"
  [ -f clips/v5/C_bench_red.mp4 ] || die "a2v bench clip (seed 12) did not land"
  ffmpeg -v error -y -ss 2.0 -i clips/v5/C_bench_red.mp4 -frames:v 1 /tmp/hd5_bench_mid.png
  cd=0; cb=0; doug_hue_ok /tmp/hd5_bench_mid.png 359 68 483 316 || cd=1; bear_ok /tmp/hd5_bench_mid.png 455 37 650 378 || cb=1
  { [ $cd = 1 ] || [ $cb = 1 ]; } && die "bench clip failed the gate twice (doug_fail=$cd bear_fail=$cb); stopping, not looping"
fi
log "bench clip passes; handing over to run_v5_doug_all.sh (finish, gates, Doug gate, publish, text, bigjob end, training)"
exec bash tools/run_v5_doug_all.sh
