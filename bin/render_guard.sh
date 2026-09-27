#!/bin/bash
# render_guard.sh — source this; provides guarded_run "label" cmd...
# Health-checks ComfyUI before each render, restarts it on crash, retries the shot once.
comfy_up() { curl -s -m 5 http://127.0.0.1:8188/system_stats >/dev/null 2>&1; }
comfy_restart() {
  echo "[guard] ComfyUI down — restarting" >&2
  pkill -f "main.py --listen" 2>/dev/null; sleep 5
  cd /Users/dtribe/Desktop/PROJECTS/AI/ComfyUI && nohup ./venv/bin/python main.py --listen >> /tmp/comfyui_overnight.log 2>&1 &
  cd - >/dev/null
  for i in $(seq 1 24); do sleep 5; comfy_up && { echo "[guard] back up" >&2; return 0; }; done
  echo "[guard] FAILED to restart ComfyUI" >&2; return 1
}
guarded_run() {
  local label="$1"; shift
  gpu_clear || { echo "[guard] mem-gate refused, skipping: $label" >&2; echo "$label" >> /tmp/render_failures.txt; return 1; }
  comfy_up || comfy_restart || return 1
  if "$@"; then echo "[guard] OK: $label"; return 0; fi
  echo "[guard] FAILED once: $label — restarting Comfy + retrying" >&2
  comfy_restart || return 1
  if "$@"; then echo "[guard] OK on retry: $label"; return 0; fi
  echo "[guard] FAILED twice, skipping: $label" >&2
  echo "$label" >> /tmp/render_failures.txt
  return 0  # keep the chain moving; failures logged for review
}
stage_reset() {  # full ComfyUI restart between model stages — memory starts clean
  echo "[guard] stage reset: $1"
  pkill -f "main.py --listen" 2>/dev/null; sleep 8
  cd /Users/dtribe/Desktop/PROJECTS/AI/ComfyUI && nohup ./venv/bin/python main.py --listen >> /tmp/comfyui_overnight.log 2>&1 &
  cd - >/dev/null
  for i in $(seq 1 24); do sleep 5; comfy_up && return 0; done; return 1
}
gpu_clear() {  # pause while other known-heavy TRANSIENT GPU programs run — never stack
  # Pattern fixed 2026-07-23: old pattern matched "mlx_lm" (the ALWAYS-ON gemma
  # server — infinite pause) and bare "train" (matches any projects/circus_train/
  # script path — guard paused on ITSELF). Match transient hogs only.
  while pgrep -f "make-ltx-|ltx_video|mlx_lm.lora|wan_distill|lora_build" >/dev/null 2>&1; do
    echo "[guard] another GPU program is running — pausing renders 60s" >&2; sleep 60
  done
  # Memory gate (2026-07-23 panic): refuse to launch into a swap-thrashing box.
  "$(dirname "${BASH_SOURCE[0]:-$0}")/mem-gate" "guarded step" || return 1
}
