#!/bin/bash
# ONE sequential orchestrator — no more parallel chain races.
cd "$(dirname "$0")"
log(){ echo "[$(date +%H:%M:%S)] $*"; }

# 1. wait for the in-flight S6 redo to finish
log "waiting for s6 redo"
while pgrep -f s6_redo.sh >/dev/null; do sleep 30; done
log "s6 redo finished: $(tail -1 s6redo.log 2>/dev/null)"

# 2. wait for LTX-2 download, then run a2v
log "waiting for LTX-2 download"
while pgrep -f "hf download prince-canuma" >/dev/null; do sleep 60; done
if [ -f ~/.cache/huggingface/hub/models--prince-canuma--LTX-2-distilled/snapshots/*/transformer/config.json ] 2>/dev/null || ls ~/.cache/huggingface/hub/models--prince-canuma--LTX-2-distilled/snapshots/*/transformer/config.json >/dev/null 2>&1; then
  log "LTX-2 present — running a2v"
  rm -f a2v.log
  ./build_a2v.sh > a2v.log 2>&1
  log "a2v done: $(grep -c 'A2V DONE' a2v.log) ok, $(grep -c 'A2V FAILED' a2v.log) failed"
else
  log "LTX-2 STILL MISSING — skipping a2v"
fi

# 3. round 3 scene hunt last
log "starting round 3"
~/.local/mlx-server/bin/python scenes_gen.py
log "ORCHESTRATION COMPLETE"
