#!/bin/bash
# SIGSTOP renders while Song Forge on the M5 reports jobs_running > 0; SIGCONT when it is back to 0.
PATS="krea_batch.py|make-k6|ltx-2-mlx|make-ltx25|film_qc.py"
paused=0
while true; do
  jr=$(curl -s -m 4 127.0.0.1:8767/api/status | python3 -c "import sys,json; print(json.load(sys.stdin).get('jobs_running',0))" 2>/dev/null || echo 0)
  if [ "${jr:-0}" -gt 0 ] && [ $paused = 0 ]; then pkill -STOP -f "$PATS"; paused=1; echo "$(date +%T) paused (jobs_running=$jr)"; fi
  if [ "${jr:-0}" -eq 0 ] && [ $paused = 1 ]; then pkill -CONT -f "$PATS"; paused=0; echo "$(date +%T) resumed"; fi
  sleep 10
done
