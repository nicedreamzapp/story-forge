#!/usr/bin/env bash
# overnight_expansion.sh — 2026-07-31 expansion run (Matt: "a ton of animals,
# way more action, tell the story with pictures").
# Phase 1: lock the 4 new character masters (monkey, lion, giraffe, parrot).
# Phase 2: hand the 14 open beats to the director via keepalive; it builds,
#          gates, assembles and QCs, and stops with reasons if blocked.
# Launched under caffeinate. Stop everything: touch STOP_DIRECTOR in this dir.
set -u
SF="$HOME/Desktop/PROJECTS/story-forge"
PROJ="$SF/projects/circus_train"
MLX_PY="$HOME/.local/mlx-server/bin/python"
LOG="$PROJ/overnight_expansion.log"

cd "$SF"
echo "[overnight $(date '+%H:%M:%S')] phase 1 — new-cast masters" | tee -a "$LOG"
"$MLX_PY" bin/forge-shot "$PROJ/masters_build.json" --stage stills >> "$LOG" 2>&1
M_CODE=$?
echo "[overnight $(date '+%H:%M:%S')] masters stage exit=$M_CODE" | tee -a "$LOG"
for m in monkey lion giraffe parrot; do
  if [ -f "$PROJ/canon/${m}_canon.png" ]; then
    chmod 444 "$PROJ/canon/${m}_canon.png"
    echo "[overnight] master LOCKED: ${m}_canon.png" | tee -a "$LOG"
  else
    echo "[overnight] WARNING: no ${m}_canon.png — shots gating on it will block" | tee -a "$LOG"
  fi
done

echo "[overnight $(date '+%H:%M:%S')] phase 2 — director takes the film" | tee -a "$LOG"
rm -f "$PROJ/STOP_DIRECTOR"
exec bash bin/forge-keepalive "$PROJ" 9
