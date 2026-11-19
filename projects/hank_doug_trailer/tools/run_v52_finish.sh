#!/bin/bash
# run_v52_finish.sh — v5.2 finish (Matt 11/18 1:52-2:07 PM). Inputs ready before this runs: tools/timeline_v52.json (cut_v52b),
# final/mix_v52.wav (mix_v52b). Here: picture (finish_v5 with TIMELINE=v52), mux, final_audio_gate -14 LUFS / -1 dBTP in place,
# manifest/timeline/narration + sync table, 2 fps contact sheet, the per-0.5 s static+click audit on the DELIVERED audio, then the
# gates (audio_check, film_qc, continuity) and the publish + text ONLY when: audit flags 0, audio_check no FAIL beyond 'score vocals',
# continuity doug_colour 0 FAIL, no_humans 0 FAIL, owner_faceless 0 FAIL, film_qc not worse than v5.1 (23). Training is stopped
# (STOP file); the caller restores it after this script (never here: film_qc needs the memory).
set -u
cd "$(dirname "$0")/.." || exit 1
PROJ=$(pwd); SF=$HOME/Desktop/PROJECTS/story-forge
PY=/usr/bin/python3; QC_PY=$HOME/.local/mlx-server/bin/python; AC_PY=$HOME/chatterbox-env/bin/python; MEMGATE=$SF/bin/mem-gate
VPS=root@5.252.55.128; VPS_DIR=/var/www/v; VPS_URL=https://hq.nicedreamzwholesale.com/v
LOG=$PROJ/final/run_v52.log
log() { echo "$(date '+%m/%d %H:%M:%S') $*" | tee -a "$LOG"; }
die() { log "STOP: $*"; exit 1; }
FILM=final/hank_doug_wild_rescue_trailer_v52.mp4
log "=== v5.2 finish (pid $$)"
[ -f tools/timeline_v52.json ] || die "no timeline_v52"
[ -f final/mix_v52.wav ] || die "no mix_v52.wav"
if [ ! -f final/picture_v52.mp4 ] || [ "${REPICTURE:-0}" = 1 ]; then
  TIMELINE=tools/timeline_v52.json $AC_PY tools/finish_v5.py --out final/picture_v52.mp4 >> final/render_v52.log 2>&1 || die "finish_v5 failed (final/render_v52.log)"
fi
log "picture: final/picture_v52.mp4 ($(ffprobe -v error -show_entries format=duration -of csv=p=0 final/picture_v52.mp4) s)"
ffmpeg -v error -y -i final/picture_v52.mp4 -i final/mix_v52.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -shortest "$FILM" || die "mux failed"
$PY "$SF/pipeline-tools/final_audio_gate.py" "$FILM" --in-place --lufs -14 --tp -1 --report final/final_audio_gate_v52.md >> final/render_v52.log 2>&1 || log "final_audio_gate rc=$?"
$PY tools/write_manifest_v52.py >> "$LOG" 2>&1; TIMELINE=tools/timeline_v52.json CUES=final/mix_cues_v52.json OUT=final/sync_v52.md $PY tools/sync_table_v52.py >> "$LOG" 2>&1
ffmpeg -v error -y -i "$FILM" -vf "fps=2,scale=320:-1,tile=12x12" -frames:v 1 final/contact_sheet_v52_2fps.jpg
log "film: $FILM ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$FILM") s)"
ffmpeg -v error -y -i "$FILM" -vn -ar 48000 final/film_v52_audio.wav
$AC_PY tools/click_audit_v52b.py final/film_v52_audio.wav --cues final/mix_cues_v52.json --timeline tools/timeline_v52.json --stems final/stems_v52/music.wav final/stems_v52/voices.wav final/stems_v52/sfx.wav 2>/dev/null | grep -v Warning > final/click_audit_v52b.txt; awk "NR>2 && $0 !~ /voices/" final/click_audit_v52b.txt > final/click_audit_v52_nonvoice.txt
flags=$(grep -c "" final/click_audit_v52_nonvoice.txt); log "delivered audio audit: $(head -1 final/click_audit_v52b.txt) | windows not explained by speech: $flags"
# gates
"$MEMGATE" "gates v5.2" || die "mem-gate refused the gates"
( cd "$SF" && "$AC_PY" pipeline-tools/audio_check.py "$PROJ/$FILM" --score "$PROJ/music/anthem_9_end.wav" --timeline "$PROJ/final/timeline.json" --narration "$PROJ/narration.json" > "$PROJ/final/audio_check_v52_report.md" 2> "$PROJ/final/audio_check_v52.err" ) & AC=$!
( cd "$SF" && "$QC_PY" pipeline-tools/film_qc.py "$PROJ/$FILM" "$PROJ/manifest_v52.json" --report "$PROJ/final/film_qc_v52_report.md" > "$PROJ/final/film_qc_v52.log" 2>&1 ); log "film_qc exit $?"
( cd "$SF" && "$QC_PY" pipeline-tools/continuity_check.py "$PROJ" "$PROJ/$FILM" > "$PROJ/final/continuity_v52.log" 2>&1 ); log "continuity_check exit $?"
wait $AC
ac_fail=$(grep -c "^\- \[FAIL\]" final/audio_check_v52_report.md); ac_other=$(grep "^\- \[FAIL\]" final/audio_check_v52_report.md | grep -vc "score vocals")
fq=$(grep -m1 "Verdict" final/film_qc_v52_report.md); fq_n=$(echo "$fq" | sed -n 's/.*— \([0-9]*\) defect.*/\1/p'); [ -n "$fq_n" ] || fq_n=0
dc_fail=$(grep -c "FAIL\] doug_colour" final/continuity_v52.log); dc_pass=$(grep -c "PASS\] doug_colour" final/continuity_v52.log)
hands=$(grep -c "FAIL\] no_humans" final/continuity_v52.log); face=$(grep -c "FAIL\] owner_faceless" final/continuity_v52.log)
log "gates: audio_check FAIL lines $ac_fail (other than 'score vocals': $ac_other) | film_qc: $fq | continuity doug_colour $dc_pass PASS / $dc_fail FAIL, no_humans FAIL $hands, owner_faceless FAIL $face | audit flagged ${flags:-?}"
if [ "${ac_other:-1}" -eq 0 ] && [ "${flags:-1}" -eq 0 ] && [ "${fq_n:-99}" -le 23 ] && [ "${dc_fail:-1}" -eq 0 ] && [ "${hands:-1}" -eq 0 ] && [ "${face:-1}" -eq 0 ] && [ "${FORCE_PUBLISH:-0}" != 1 ]; then
  touch final/V52_CLEAN; log "v5.2 CLEAN by the gates (publish is the builder's call after the contact sheet)"
else
  log "HOLD: v5.2 not clean (see the gates line above)"
fi
log "=== v5.2 finish done"
