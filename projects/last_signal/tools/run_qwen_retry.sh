#!/bin/zsh
# Retry a qwen batch until it completes; the guard refusal (another job holding RAM) is a wait, not a failure.
J=$1; L=$2
for i in {1..40}; do
  ~/AI_Models/qwen-image-2.1-test/venv/bin/python tools/qwen_batch.py $J >> $L 2>&1
  rc=$?
  if [ $rc -eq 0 ]; then echo "$(date +%H:%M) batch complete" >> $L; exit 0; fi
  echo "$(date +%H:%M) batch exited rc=$rc, retry in 120s ($i/40)" >> $L
  sleep 120
done
exit 1
