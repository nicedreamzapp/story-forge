#!/bin/bash
# Trailer BEST pass: K6 not granted (budget 50 GB < 72, lease never shrunk) -> LTX-2.5 --hq --low-ram 1024x576 on the new hero
# shots, then upscale-route (auto: Refine-Details on faces, SeedVR2 otherwise) into final/segs/up_trailer (teaser's up/ untouched).
P=~/Desktop/PROJECTS/story-forge/projects/things_we_remember; cd $P
date +%T > tools/trailer/t_best_start
L=~/Desktop/PROJECTS/story-forge/bin/make-ltx25
pk() { python3 -c "import json;print(json.load(open('tools/picks_more.json'))['$1'])"; }
sfwait() { until [ "$(curl -s -m5 127.0.0.1:8767/api/status | python3 -c 'import sys,json;print(json.load(sys.stdin).get("jobs_running",0))' 2>/dev/null || echo 0)" = 0 ]; do sleep 20; done; }
log() { echo "{\"shot\": \"twr_trailer_$1\", \"step\": \"$2\", \"seconds\": $3}" >> ~/Desktop/PROJECTS/story-forge/METRICS.jsonl; }
run() { n=$1; seed=$2; dur=$3; shift 3
  [ -s clips/hq/$n.mp4 ] && return; sfwait; t0=$(date +%s)
  out=$($L --i2v stills/$(pk $n).png --duration $dur --res 1024x576 --hq --low-ram --gb 26 --seed $seed --label twr-hq-$n "$*" 2>&1 | tee -a clips_hq_trailer.log | grep -o '→ .*mp4' | tail -1 | sed 's/→ //')
  [ -s "$out" ] && cp "$out" clips/hq/$n.mp4 && echo "HQ $n ok $(date +%T)" >> clips_hq_trailer.log || echo "HQ $n FAILED $(date +%T)" >> clips_hq_trailer.log
  log $n i2v_ltx25_hq_${dur}s $(( $(date +%s) - t0 ))
}
LOOK="cinematic horror film, slow and quiet, natural motivated light stays the same"
run t13 2111 4 "the woman sits frozen at the kitchen table staring at the cassette recorder, she does not move, only slow breathing, the hanging lamp flickers faintly, the camera very slowly pushes in toward her face, $LOOK"
run t18 2511 3 "the man stands beside the small empty bed looking down at it, he slowly tilts his head, puzzled, he does not touch it, the camera holds still, $LOOK"
run t04 1411 4 "the old woman stands perfectly still at the window with her back to us, rain runs down the glass, the lace curtain stirs very slightly, the camera slowly pushes in toward her, $LOOK"
run t01 1211 4 "the station wagon rolls slowly up the wet gravel driveway toward the old farmhouse and comes to a stop, soft rain keeps falling, puddles ripple, the camera holds still, $LOOK"
if [ ! -s clips/hq/t14.mp4 ]; then
  ~/.local/mlx-server/bin/python tools/trailer/a2vwav.py t14:L03:4.5 >> clips_hq_trailer.log 2>&1; sfwait; t0=$(date +%s)
  out=$($L --i2v stills/$(pk t14).png --audio voice/t14_a2v.wav --res 1024x576 --hq --low-ram --gb 26 --seed 2211 --label twr-hq-t14 "home video, the little girl standing in the garden looks just past the camera and speaks, her mouth moving with the words, she lifts a hand and points past the camera, slight handheld camera shake, sunny afternoon" 2>&1 | tee -a clips_hq_trailer.log | grep -o '→ .*mp4' | tail -1 | sed 's/→ //')
  [ -s "$out" ] && cp "$out" clips/hq/t14.mp4 && echo "HQ t14 ok $(date +%T)" >> clips_hq_trailer.log || echo "HQ t14 FAILED" >> clips_hq_trailer.log
  log t14 a2v_ltx25_hq $(( $(date +%s) - t0 ))
fi
echo HQ_DONE >> clips_hq_trailer.log
mkdir -p final/segs/hq_trailer final/segs/up_trailer
python3 - <<'PY'
import json, shutil, os
ids = [i for i in ["t01", "t04", "t13", "t18", "t14"] if os.path.exists(f"clips/hq/{i}.mp4")]
for k, i in enumerate(ids): shutil.copy(f"clips/hq/{i}.mp4", f"final/segs/hq_trailer/{k:02d}_{i}.mp4")
json.dump({"cuts": [{"id": i, "shot": i, "len": 4.0} for i in ids]}, open("final/edl_hq_trailer.json", "w"), indent=1)
PY
sfwait; t0=$(date +%s)
~/Desktop/PROJECTS/story-forge/bin/upscale-route $P --edl final/edl_hq_trailer.json --segs final/segs/hq_trailer --out final/segs/up_trailer > upscale_trailer.log 2>&1
log upscale upscale_route_x5 $(( $(date +%s) - t0 ))
echo UP_DONE >> upscale_trailer.log; date +%T > tools/trailer/t_best_end
