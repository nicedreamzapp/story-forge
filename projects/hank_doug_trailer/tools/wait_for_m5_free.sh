#!/bin/bash
# Waits for the life-model training (pid in its train.pid) to exit, then wakes the trailer chat.
PIDF=/Users/dtribe/life-model/runs/full-20261117-1030/train.pid
while true; do
  P=$(cat "$PIDF" 2>/dev/null)
  if [ -z "$P" ] || ! kill -0 "$P" 2>/dev/null; then break; fi
  sleep 120
done
sleep 60
chat-send m5~07c0f0f4 "M5 is free: the life-model training finished. Resume the Hank & Doug trailer v5: run the Doug colour test (step 4), text Matt the link, then Fable builds steps 5-8 after his OK."
