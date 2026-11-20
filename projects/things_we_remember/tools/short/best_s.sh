#!/bin/bash
# SHORT BEST pass: K6 refused (guard budget ~50 GB < 72) -> LTX-2.5 --hq --low-ram on the 12 hero shots (SHORT_3MIN.md),
# then upscale-route into final/segs/up_short. Fast takes stay in clips/; HQ goes to clips/hq/. Never deletes anything.
P=~/Desktop/PROJECTS/story-forge/projects/things_we_remember; cd $P
until grep -q "^QC:" finish_short_fast.log 2>/dev/null; do sleep 15; done
date +%T > tools/short/s_best_start
L=~/Desktop/PROJECTS/story-forge/bin/make-ltx25; LOG=clips_hq_short.log
pk() { python3 -c "import json;print(json.load(open('tools/picks_more.json'))['$1'])"; }
sfwait() { until [ "$(curl -s -m5 127.0.0.1:8767/api/status | python3 -c 'import sys,json;print(json.load(sys.stdin).get("jobs_running",0))' 2>/dev/null || echo 0)" = 0 ]; do sleep 20; done; }
log() { echo "{\"shot\": \"twr_short_$1\", \"step\": \"$2\", \"seconds\": $3}" >> ~/Desktop/PROJECTS/story-forge/METRICS.jsonl; }
run() { n=$1; seed=$2; dur=$3; shift 3
  [ -s clips/hq/$n.mp4 ] && return; sfwait; t0=$(date +%s)
  out=$($L --i2v stills/$(pk $n).png --duration $dur --res 1024x576 --hq --low-ram --gb 26 --seed $seed --label twr-hq-$n "$*" 2>&1 | tee -a $LOG | grep -o '→ .*mp4' | tail -1 | sed 's/→ //')
  [ -s "$out" ] && cp "$out" clips/hq/$n.mp4 && echo "HQ $n ok $(date +%T)" >> $LOG || echo "HQ $n FAILED $(date +%T)" >> $LOG
  log $n i2v_ltx25_hq_${dur}s $(( $(date +%s) - t0 ))
}
LOOK="cinematic horror film, slow and quiet, natural motivated light stays the same"
run sh06 3111 4 "the woman lifts the framed photo off the wall and looks at it with a small curious smile, she tilts it toward the lamp, the camera slowly pushes in, $LOOK"
run sh10 3311 4 "the woman's small smile slowly fades, she blinks, her eyes search, confused and uneasy, she does not speak, the camera holds, $LOOK"
run sh13 3511 5 "the family eats dinner together, passing a dish, gentle small movements, nobody sits in the empty chair at the near end, the camera slowly pushes in, $LOOK"
run sh14 3611 4 "the man's hands set the white plate down neatly in front of the empty chair and slide away out of frame, the chair stays empty, the camera holds, $LOOK"
run sh15 3711 4 "the man chews calmly and glances to his side, relaxed and easy, the camera holds, $LOOK"
run sh16 3721 4 "the man slowly stops chewing and stares at nothing, his face goes blank and lost, he does not move, the camera very slowly pushes in, $LOOK"
run sh18 3811 4 "the old woman slowly lowers her fork to the plate and closes her eyes, sad, she does not speak, the camera holds, $LOOK"
run sh21 3911 5 "the woman stares at the empty chair off camera, frozen, not breathing, her eyes wide and wet, the camera very slowly pushes in toward her face, $LOOK"
run sh30 4111 5 "the little girl draws happily with a crayon, her hand moving across the paper, she hums to herself, the camera holds, $LOOK"
run sh31 4211 4 "the woman sips her coffee and smiles down at the little girl drawing, warm and calm, the camera slowly pushes in over her shoulder, $LOOK"
run sh34 4511 5 "the woman looks down at the drawing in her hands, puzzled, she blinks, then her eyes slowly fill with tears as she recognizes someone, her lips tremble, the camera very slowly pushes in, $LOOK"
run sh37 4521 4 "the woman smiles through her tears, a tear runs down her cheek, love and grief together, the camera holds, $LOOK"
echo HQ_DONE >> $LOG
mkdir -p final/segs/hq_short final/segs/up_short
python3 - <<'PY2'
import json, shutil, os
H = ['sh06', 'sh10', 'sh13', 'sh14', 'sh15', 'sh16', 'sh18', 'sh21', 'sh30', 'sh31', 'sh34', 'sh37']
ids = [i for i in H if os.path.exists(f"clips/hq/{i}.mp4")]
cuts = []
for k, i in enumerate(ids):
    d = f"final/segs/hq_short/{k:02d}_{i}.mp4"; shutil.copy(f"clips/hq/{i}.mp4", d)
    cuts.append({"id": i, "shot": i, "len": 4.0, "src": d})
json.dump({"cuts": cuts}, open("final/edl_hq_short.json", "w"), indent=1)
PY2
sfwait; t0=$(date +%s)
~/Desktop/PROJECTS/story-forge/bin/upscale-route $P --edl final/edl_hq_short.json --segs final/segs/hq_short --out final/segs/up_short > upscale_short.log 2>&1
log upscale upscale_route_x12 $(( $(date +%s) - t0 ))
echo UP_DONE >> upscale_short.log; date +%T > tools/short/s_best_end
