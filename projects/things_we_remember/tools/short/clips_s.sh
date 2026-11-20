#!/bin/bash
# Short FAST pass: LTX-2.5 distilled low-ram i2v 1024x576, then the 2 a2v lip-syncs (after voices).
P=~/Desktop/PROJECTS/story-forge/projects/things_we_remember; cd $P
until [ -f tools/short/PICKS_READY ]; do sleep 5; done
L=~/Desktop/PROJECTS/story-forge/bin/make-ltx25; LOG=clips_short.log
pk() { python3 -c "import json;print(json.load(open('tools/picks_more.json'))['$1'])"; }
sfwait() { until [ "$(curl -s -m5 127.0.0.1:8767/api/status | python3 -c 'import sys,json;print(json.load(sys.stdin).get("jobs_running",0))' 2>/dev/null || echo 0)" = 0 ]; do sleep 20; done; }
run() { n=$1; seed=$2; dur=$3; shift 3
  [ -s clips/$n.mp4 ] && return; sfwait; t0=$(date +%s)
  out=$($L --i2v stills/$(pk $n).png --duration $dur --res 1024x576 --low-ram --gb 26 --seed $seed --label twr-$n "$*" 2>&1 | tee -a $LOG | grep -o '→ .*mp4' | tail -1 | sed 's/→ //')
  [ -s "$out" ] && cp "$out" clips/$n.mp4 && echo "CLIP $n ok $(date +%T)" >> $LOG || echo "CLIP $n FAILED" >> $LOG
  echo "{\"shot\": \"twr_$n\", \"step\": \"i2v_ltx25_lowram_${dur}s\", \"seconds\": $(( $(date +%s) - t0 ))}" >> ~/Desktop/PROJECTS/story-forge/METRICS.jsonl
}
a2v() { n=$1; seed=$2; shift 2
  [ -s clips/$n.mp4 ] && return; sfwait; t0=$(date +%s)
  out=$($L --i2v stills/$(pk $n).png --audio voice/${n}_a2v.wav --res 1024x576 --low-ram --gb 26 --seed $seed --label twr-$n "$*" 2>&1 | tee -a $LOG | grep -o '→ .*mp4' | tail -1 | sed 's/→ //')
  [ -s "$out" ] && cp "$out" clips/$n.mp4 && echo "CLIP $n ok $(date +%T)" >> $LOG || echo "CLIP $n FAILED" >> $LOG
  echo "{\"shot\": \"twr_$n\", \"step\": \"a2v_ltx25_lowram\", \"seconds\": $(( $(date +%s) - t0 ))}" >> ~/Desktop/PROJECTS/story-forge/METRICS.jsonl
}
LOOK="cinematic horror film, slow and quiet, natural motivated light stays the same"
run sh06 3110 4 "the woman lifts the framed photo off the wall and looks at it with a small curious smile, she tilts it toward the lamp, the camera slowly pushes in, $LOOK"
run sh10 3310 4 "the woman's small smile slowly fades, she blinks, her eyes search, confused and uneasy, she does not speak, the camera holds, $LOOK"
run sh12 3460 4 "the woman rinses the glass slowly under the tap, lost in thought, the dusk light dims, the dark doorway behind her stays still, the camera holds, $LOOK"
run sh13 3510 5 "the family eats dinner together, passing a dish, gentle small movements, nobody sits in the empty chair at the near end, the camera slowly pushes in, $LOOK"
run sh13b 3560 3 "the little girl eats happily and swings her legs under the table, she smiles, the camera holds, $LOOK"
run sh14 3610 4 "the man's hands set the white plate down neatly in front of the empty chair and slide away out of frame, the chair stays empty, the camera holds, $LOOK"
run sh15 3710 4 "the man chews calmly and glances to his side, relaxed and easy, the camera holds, $LOOK"
run sh16 3720 4 "the man slowly stops chewing and stares at nothing, his face goes blank and lost, he does not move, the camera very slowly pushes in, $LOOK"
run sh18 3810 4 "the old woman slowly lowers her fork to the plate and closes her eyes, sad, she does not speak, the camera holds, $LOOK"
run sh21 3910 5 "the woman stares at the empty chair off camera, frozen, not breathing, her eyes wide and wet, the camera very slowly pushes in toward her face, $LOOK"
run sh22 3960 4 "the woman stands at the foot of the dark stairs with one hand on the rail, slowly looks up toward the faint nightlight glow upstairs, and takes a frightened breath, the camera holds, $LOOK"
run sh29 4010 5 "morning sunlight slowly drifts across the peaceful kitchen, dust floats in the light, blossoms sway gently outside the window, the camera slowly pushes in, $LOOK"
run sh30 4110 5 "the little girl draws happily with a crayon, her hand moving across the paper, she hums to herself, the camera holds, $LOOK"
run sh31 4210 4 "the woman sips her coffee and smiles down at the little girl drawing, warm and calm, the camera slowly pushes in over her shoulder, $LOOK"
run sh34 4510 5 "the woman looks down at the drawing in her hands, puzzled, she blinks, then her eyes slowly fill with tears as she recognizes someone, her lips tremble, the camera very slowly pushes in, $LOOK"
run sh37 4520 4 "the woman smiles through her tears, a tear runs down her cheek, love and grief together, the camera holds, $LOOK"
run sh38 4610 5 "the reflection in the window glass holds still, the woman and the girl sit at the table, the dark blurred shape standing behind them stays perfectly still, the blossoms sway outside, the camera slowly pushes in, $LOOK"
echo I2V_DONE >> $LOG
until grep -q SCORE_DONE voice/gen_short.log 2>/dev/null; do sleep 5; done
~/.local/mlx-server/bin/python tools/trailer/a2vwav.py sh32:L04:3.5 sh36:L05:3.5 >> $LOG 2>&1
a2v sh32 4310 "the little girl looks calmly up at her mother and speaks quietly, her mouth moving with the words, calm serious face, she blinks once, camera locked off, $LOOK"
a2v sh36 4320 "the little girl looks up at her mother and speaks gently, her mouth moving with the words, a small knowing smile, she blinks once, camera locked off, $LOOK"
echo CLIPS_DONE >> $LOG
