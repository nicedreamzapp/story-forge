#!/bin/bash
# sfswap.sh <project> <minutes>: Song Forge takes turns too. Brain thinking -> Song Forge paused (its own pause marker);
# that project's make-promo running -> Song Forge up (the mix needs a music bed). Logs each flip.
P=$1; END=$(( $(date +%s) + $2*60 )); L=$HOME/.local/brainswap/sfswap.log; HOLD=""
pause() { [ -n "$HOLD" ] && kill -0 $HOLD 2>/dev/null && return
  curl -s -m 5 localhost:8767/api/status | grep -q '"jobs_running": 0' || { echo "$(date +%T) customer job running, not pausing" >> $L; return; }
  nohup sleep 7200 >/dev/null 2>&1 & HOLD=$!; echo $HOLD > /tmp/songforge_paused_by
  for p in 8001 9420; do lsof -ti tcp:$p -sTCP:LISTEN | xargs -r kill; done; echo "$(date +%T) paused Song Forge (brain turn)" >> $L; }
resume() { [ -z "$HOLD" ] && return; kill $HOLD 2>/dev/null; HOLD=""; launchctl kickstart gui/$(id -u)/com.nicedreamz.songforge-m5-stack
  echo "$(date +%T) Song Forge back (render turn)" >> $L; }
while [ $(date +%s) -lt $END ]; do
  if pgrep -f "bin/make-promo projects/$P" >/dev/null; then resume; else pause; fi; sleep 3
done
resume; echo "$(date +%T) sfswap done" >> $L
