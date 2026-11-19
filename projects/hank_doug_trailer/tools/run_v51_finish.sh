#!/bin/bash
# run_v51_finish.sh — v5.1 (Matt 1:01 PM: no hand in row 1, "nice music not some lame hissing static").
# Inputs ready before this runs: final/picture_v51.mp4 (finish_v5 with row 1 = G_hunt_red_s12), final/mix_v51.wav
# (mix_v51: warm-filtered themes, stems in final/stems_v51). Here: mux, final_audio_gate in place, manifest/sync, 2 fps
# sheet, then the gates in parallel (audio_check, film_qc, continuity), the Doug gate on the changed row, and publish +
# text only when audio_check has no FAIL beyond the known "score vocals" line, the audit has no HISS window, film_qc
# did not get worse than v5 (23 defects) and continuity doug_colour has 0 FAIL. Training keeps running (memory gate).
set -u
cd "$(dirname "$0")/.." || exit 1
PROJ=$(pwd); SF=$HOME/Desktop/PROJECTS/story-forge
PY=/usr/bin/python3; QC_PY=$HOME/.local/mlx-server/bin/python; AC_PY=$HOME/chatterbox-env/bin/python; MEMGATE=$SF/bin/mem-gate
SF_ENV="${STORY_FORGE_ENV:-$HOME/.config/story-forge/publish.env}"; if [ -f "$SF_ENV" ]; then . "$SF_ENV"; fi; CHAT="${SF_CHAT:-}"; SF_ENV="${STORY_FORGE_ENV:-$HOME/.config/story-forge/publish.env}"; if [ -f "$SF_ENV" ]; then . "$SF_ENV"; fi; VPS="${SF_VPS:?set SF_VPS (user@host) in $SF_ENV}"; VPS_DIR="${SF_VPS_DIR:?set SF_VPS_DIR in $SF_ENV}"; VPS_URL="${SF_VPS_URL:?set SF_VPS_URL in $SF_ENV}"
LOG=$PROJ/final/run_v51.log
log() { echo "$(date '+%m/%d %H:%M:%S') $*" | tee -a "$LOG"; }
die() { log "STOP: $*"; chat-send "$CHAT" "v5.1 finish STOP: $*" >/dev/null 2>&1; exit 1; }
songforge_wait() { while :; do jr=$(curl -s -m 4 127.0.0.1:8767/api/status | $PY -c "import sys,json; print(json.load(sys.stdin).get('jobs_running',0))" 2>/dev/null || echo 0)
    [ "${jr:-0}" -eq 0 ] && return; log "Song Forge busy, waiting"; sleep 20; done; }
FILM=final/hank_doug_wild_rescue_trailer_v51.mp4
log "=== v5.1 finish (pid $$)"
for i in $(seq 1 60); do [ -f final/picture_v51.mp4 ] && ! pgrep -f "finish_v5.py --out final/picture_v51.mp4" >/dev/null && break; sleep 10; done
[ -f final/picture_v51.mp4 ] || die "no final/picture_v51.mp4"
[ -f final/mix_v51.wav ] || die "no final/mix_v51.wav"
ffmpeg -v error -y -i final/picture_v51.mp4 -i final/mix_v51.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -shortest "$FILM" || die "mux failed"
$PY "$SF/pipeline-tools/final_audio_gate.py" "$FILM" --in-place --lufs -14.5 --tp -1.9 --report final/final_audio_gate_v51.md >> final/render_v51.log 2>&1 || log "final_audio_gate rc=$?"
$PY tools/write_manifest_v5.py >> "$LOG" 2>&1; $PY tools/sync_table_v5.py >> "$LOG" 2>&1
cp manifest_v5.json manifest_v51.json 2>/dev/null
ffmpeg -v error -y -i "$FILM" -vf "fps=2,scale=320:-1,tile=12x10" -frames:v 1 final/contact_sheet_v51_2fps.jpg
log "film: $FILM ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$FILM") s)"
# the delivered audio, per 3 s window (after the gate's loudness/limiter pass)
ffmpeg -v error -y -i "$FILM" -vn -ar 48000 final/film_v51_audio.wav
$AC_PY tools/audio_audit_v51.py --timeline tools/timeline_v5.json final/film_v51_audio.wav > final/audio_audit_v51.txt 2>/dev/null
hiss=$(grep -c "HISS$" final/audio_audit_v51.txt); log "delivered audio: $(grep '^==' final/audio_audit_v51.txt | cut -c1-120)"
# gates
songforge_wait; "$MEMGATE" "gates v5.1" || die "mem-gate refused the gates"
( cd "$SF" && "$AC_PY" pipeline-tools/audio_check.py "$PROJ/$FILM" --score "$PROJ/music/theme_2_v51.wav" --timeline "$PROJ/final/timeline.json" --narration "$PROJ/narration.json" > "$PROJ/final/audio_check_v51_report.md" 2> "$PROJ/final/audio_check_v51.err" ) & AC=$!
( cd "$SF" && "$QC_PY" pipeline-tools/film_qc.py "$PROJ/$FILM" "$PROJ/manifest_v51.json" --report "$PROJ/final/film_qc_v51_report.md" > "$PROJ/final/film_qc_v51.log" 2>&1 ); log "film_qc exit $?"
( cd "$SF" && "$QC_PY" pipeline-tools/continuity_check.py "$PROJ" "$PROJ/$FILM" > "$PROJ/final/continuity_v51.log" 2>&1 ); log "continuity_check exit $?"
wait $AC
ac_fail=$(grep -c "^\- \[FAIL\]" final/audio_check_v51_report.md); ac_other=$(grep "^\- \[FAIL\]" final/audio_check_v51_report.md | grep -vc "score vocals")
fq=$(grep -m1 "Verdict" final/film_qc_v51_report.md); fq_n=$(echo "$fq" | sed -n 's/.*— \([0-9]*\) defect.*/\1/p')
dc_fail=$(grep -c "FAIL\] doug_colour" final/continuity_v51.log); dc_pass=$(grep -c "PASS\] doug_colour" final/continuity_v51.log)
hands=$(grep -c "FAIL\] no_humans" final/continuity_v51.log)
log "gates: audio_check FAIL lines $ac_fail (other than 'score vocals': $ac_other) | film_qc: $fq | continuity doug_colour $dc_pass PASS / $dc_fail FAIL, no_humans FAIL $hands | audit HISS windows $hiss"
if [ "${ac_other:-1}" -eq 0 ] && [ "${hiss:-1}" -eq 0 ] && [ "${fq_n:-99}" -le 23 ] && [ "${dc_fail:-1}" -eq 0 ] && [ "${hands:-1}" -eq 0 ]; then
  name="hank-doug-v51-$(LC_ALL=C tr -dc a-z0-9 </dev/urandom | head -c 12).mp4"
  scp -q -o ConnectTimeout=30 "$FILM" "$VPS:$VPS_DIR/$name" || die "scp failed; film is $FILM"
  url="$VPS_URL/$name"; log "published $url"
  bash "$HOME/.claude/imessage-send.sh" "Hank & Doug v5.1 is ready (no hand in the opener, warm clean score): $url" >/dev/null 2>&1 && log "texted Matt"
  chat-send "$CHAT" "v5.1 published: $url" >/dev/null 2>&1
else
  log "HOLD: v5.1 not published (see the gates line above)"; chat-send "$CHAT" "v5.1 finished but HELD: audio_check other FAIL $ac_other, HISS windows $hiss, film_qc $fq_n, doug_colour FAIL $dc_fail, no_humans FAIL $hands" >/dev/null 2>&1
fi
log "=== v5.1 finish done"
