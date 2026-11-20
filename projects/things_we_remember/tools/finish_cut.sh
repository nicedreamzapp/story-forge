#!/bin/bash
# finish_cut.sh NAME TIMELINE TEXTS : compose (cached segs) -> score -> mix -> mux -> final_audio_gate -> gate files -> readtime -> film_qc
P=~/Desktop/PROJECTS/story-forge/projects/things_we_remember; cd $P; N=$1; export TWR_TL=$2 TWR_TEXTS=$3
PY=~/.local/mlx-server/bin/python; SEG=final/segs/${N%_fast}; SEG=${SEG%_best}
export TWR_SEGDIR=$SEG TWR_PIC=final/picture_$N.mp4 TWR_SCORE=audio/score_$N.wav TWR_MIX=audio/mix_$N.wav
t0=$(date +%s); $PY tools/compose2.py 2>&1 | grep -v cached | tail -3 || exit 1
$PY tools/music2.py | tail -1; $PY tools/mix2.py | tail -1
F=final/the_things_we_remember_$N.mp4
ffmpeg -v error -y -i $TWR_PIC -i $TWR_MIX -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart $F
python3 ../../pipeline-tools/final_audio_gate.py $F --in-place 2>&1 | tail -1
echo "{\"shot\": \"twr_$N\", \"step\": \"compose_mix_mux\", \"seconds\": $(( $(date +%s) - t0 ))}" >> ../../METRICS.jsonl
$PY tools/mk_manifest2.py; python3 ../../pipeline-tools/text_readtime_check.py . 2>&1 | tail -1
until [ "$(curl -s -m5 127.0.0.1:8767/api/status | python3 -c 'import sys,json;print(json.load(sys.stdin).get("jobs_running",0))' 2>/dev/null || echo 0)" = 0 ]; do sleep 20; done
t0=$(date +%s); $PY ../../pipeline-tools/film_qc.py $F manifest.json > qc/film_qc_$N.log 2>&1
echo "{\"shot\": \"twr_$N\", \"step\": \"film_qc\", \"seconds\": $(( $(date +%s) - t0 ))}" >> ../../METRICS.jsonl
echo "QC: $(grep -c '^\[PASS' qc/film_qc_$N.log) pass, $(grep -c '^\[FAIL' qc/film_qc_$N.log) fail, $(grep -c '^\[SKIP' qc/film_qc_$N.log) skip"
grep -E "^\[FAIL|^(PASS|FAIL) —" qc/film_qc_$N.log | cut -c1-140
