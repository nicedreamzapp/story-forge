#!/bin/bash
cd "$(dirname "$0")"
SW0=$(sysctl -n vm.swapusage | sed -E 's/.*used = ([0-9.]+)M.*/\1/' | cut -d. -f1)
echo "baseline swap ${SW0}MB"
caffeinate -ims ~/mflux-venv/bin/mflux-train --mlx-cache-limit-gb 24 --config train_doug_v2.json > train.log 2>&1 &
TPID=$!
echo "train pid $TPID"
while kill -0 $TPID 2>/dev/null; do
  SW=$(sysctl -n vm.swapusage | sed -E 's/.*used = ([0-9.]+)M.*/\1/' | cut -d. -f1)
  FREE=$(memory_pressure -Q 2>/dev/null | sed -nE 's/.*free percentage: ([0-9]+)%.*/\1/p')
  GROWTH=$(( ${SW:-0} - ${SW0:-0} ))
  # kill on REAL pressure: low free memory, or runaway swap growth with low free
  if [ "${FREE:-100}" -lt 12 ] || { [ "$GROWTH" -gt 35000 ] && [ "${FREE:-100}" -lt 20 ]; }; then
    echo "SAFETY KILL: swap_growth=${GROWTH}MB free=${FREE}%"
    kill $TPID
    exit 1
  fi
  J=$(curl -s -m 5 http://127.0.0.1:8767/api/status | python3 -c "import json,sys; print(json.load(sys.stdin).get('jobs_running',0))" 2>/dev/null)
  if [ "${J:-0}" -gt 0 ]; then
    echo "forge customer job — suspending training"
    kill -STOP $TPID
    while [ "${J:-0}" -gt 0 ]; do sleep 30; J=$(curl -s -m 5 http://127.0.0.1:8767/api/status | python3 -c "import json,sys; print(json.load(sys.stdin).get('jobs_running',0))" 2>/dev/null); done
    kill -CONT $TPID
    echo "resumed"
  fi
  sleep 20
done
wait $TPID
echo "TRAIN_EXIT $?"
