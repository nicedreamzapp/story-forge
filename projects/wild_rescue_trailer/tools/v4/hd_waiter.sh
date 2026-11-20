#!/bin/bash
# HANK & DOUG v4 auto-start waiter (plain code, no model). Polls every POLL seconds and launches tools/v4/hd_queue.py
# (Krea stills -> Qwen3-VL gate -> K6 motion) the moment THE LAST SIGNAL v2 redo is finished AND the M5 GPU is free.
#   finished = projects/last_signal/renders_v2_krea_k6/logs/REDO_V2_FINISHED exists (redo_v2.py writes it as its very
#              last act) and no tools/redo_v2.py / tools/redo_v2_wait.sh process is alive. Fallback: if the redo dies
#              without the marker (crash), its process vanishing counts, but then the GPU must stay free CRASH_NEED=15 polls (30 min),
#              so a session fixing and restarting the redo gets there first (11/1 5:21 PM the 10-min fallback grabbed the GPU
#              during a Last Signal crash-and-fix and had to be STOPped at 5:50).
#   GPU free = no python/Blender process matching the same heavy-engine pattern the Last Signal waiter uses
#              (make-k6, make-ltx, kandinsky, seedvr, krea, zimage, comfy, blender, ...), FREE_NEED polls in a row.
# Never touches a running job. Gives up after 20 h. Matches processes by PID listing (never `pgrep -f` on its own
# command line, LESSONS 10/31). Detached:  nohup tools/v4/hd_waiter.sh > v4/logs/waiter.log 2>&1 < /dev/null &
#   --dry-run : same checks, prints the decision, launches NOTHING (exits after the decision or after DRY_POLLS polls)
# Test hooks (env): LS_LOGS (marker dir), LS_PAT (redo process pattern), GPU_PAT, POLL (s), FREE_NEED, DRY_POLLS.
P="$(cd "$(dirname "$0")/../.." && pwd)"
LS_LOGS="${LS_LOGS:-$P/../last_signal/renders_v2_krea_k6/logs}"
LS_PAT="${LS_PAT:-tools/redo_v2\.py|tools/redo_v2_wait\.sh}"
GPU_PAT="${GPU_PAT:-make-k6|make-wa2|make-ltx|wan|kandinsky|seedvr|zimage|krea|comfy|mflux|blender|face_lock}"
POLL="${POLL:-120}"; FREE_NEED="${FREE_NEED:-2}"; CRASH_NEED="${CRASH_NEED:-15}"; DRY=0; DRY_POLLS="${DRY_POLLS:-1}"
[ "$1" = "--dry-run" ] && DRY=1
PY="$HOME/AI/krea2/venv/bin/python"
mkdir -p "$P/v4/logs"
ME=$$
say() { echo "$(date '+%F %T') $([ $DRY = 1 ] && echo '[DRY] ')$*"; }
procs() { ps -axo pid=,ppid=,command= | awk -v me="$ME" '$1 != me && $2 != me' ; }
ls_alive() { procs | grep -E "$LS_PAT" | grep -v -e 'grep' | head -1 | cut -c1-150; }
gpu_busy() { procs | grep -iE 'python|blender' | grep -v -e grep -e hd_waiter | grep -iE "$GPU_PAT" | head -1 | cut -c1-150; }

end=$(( $(date +%s) + 20*3600 )); free=0; seen=0; polls=0
say "waiting for THE LAST SIGNAL v2 redo to finish ($LS_LOGS/REDO_V2_FINISHED) and a free GPU; then $P/tools/v4/hd_queue.py"
while :; do
  polls=$((polls+1))
  marker=0; [ -f "$LS_LOGS/REDO_V2_FINISHED" ] && marker=1
  ls="$(ls_alive)"; [ -n "$ls" ] && seen=1
  busy="$(gpu_busy)"
  if [ -n "$ls" ]; then
    free=0; why="Last Signal redo still running: ${ls:0:110}"
  elif [ $marker = 0 ] && [ $seen = 0 ] && [ $DRY = 0 ] && [ $polls -lt 3 ]; then
    free=0; why="Last Signal redo not seen yet and no finished marker (grace poll $polls/3)"
  elif [ -n "$busy" ]; then
    free=0; why="GPU busy: ${busy:0:110}"
  else
    free=$((free+1)); why="Last Signal $([ $marker = 1 ] && echo "FINISHED ($(cat "$LS_LOGS/REDO_V2_FINISHED"))" || echo 'process gone WITHOUT its finished marker'); GPU free ($free/$([ $marker = 1 ] && echo $FREE_NEED || echo $CRASH_NEED))"
  fi
  say "$why"
  need=$FREE_NEED; [ $marker = 0 ] && need=$CRASH_NEED
  if [ $free -ge $need ]; then
    if [ $DRY = 1 ]; then say "WOULD LAUNCH: nohup $PY $P/tools/v4/hd_queue.py >> $P/v4/logs/hd_queue.out (dry run: nothing started)"; exit 0; fi
    cd "$P" && nohup "$PY" tools/v4/hd_queue.py >> v4/logs/hd_queue.out 2>&1 < /dev/null &
    qp=$!; disown $qp 2>/dev/null
    echo "$(date '+%F %T') pid $qp marker=$marker" > "$P/v4/logs/WAITER_LAUNCHED"
    say "LAUNCHED hd_queue.py pid $qp (log v4/logs/queue.log)"; exit 0
  fi
  if [ $DRY = 1 ] && [ $polls -ge $DRY_POLLS ]; then say "dry run: would keep waiting (poll every ${POLL}s)"; exit 0; fi
  if [ "$(date +%s)" -ge $end ]; then say "GAVE UP after 20 h"; exit 1; fi
  sleep "$POLL"
done
