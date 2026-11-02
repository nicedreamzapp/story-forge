#!/bin/bash
# Starts tools/redo_v2.py (THE LAST SIGNAL v2 redo) only when the M5 GPU is free: no make-k6 / make-wa2 / make-ltx /
# wan / kandinsky / seedvr / zimage / krea / comfy / mflux / blender / face_lock python (or Blender) process for 10
# straight minutes (5 polls, 2 min apart). Gives up after 10 h. Never touches a running job.
#   nohup tools/redo_v2_wait.sh > renders_v2_krea_k6/logs/waiter.log 2>&1 < /dev/null &
P="$(cd "$(dirname "$0")/.." && pwd)"; V2="$P/renders_v2_krea_k6"; mkdir -p "$V2/logs"
PAT='make-k6|make-wa2|ltx|wan|kandinsky|seedvr|zimage|krea|comfy|mflux|blender|face_lock'
busy() { ps -axo command= | grep -iE 'python|blender' | grep -v -e grep -e redo_v2 | grep -iE "$PAT" | cut -c1-160; }
end=$(( $(date +%s) + 10*3600 )); free=0
while [ $free -lt 5 ]; do
  b="$(busy)"
  if [ -z "$b" ]; then free=$((free+1)); echo "$(date '+%F %T') GPU free ($free/5)"
  else free=0; echo "$(date '+%F %T') busy: $(echo "$b" | head -1)"; fi
  [ $free -ge 5 ] && break
  if [ "$(date +%s)" -ge $end ]; then echo "$(date '+%F %T') GAVE UP after 10 h, GPU never free 10 min"; exit 1; fi
  sleep 120
done
echo "$(date '+%F %T') starting redo_v2.py"
cd "$P" && exec "$HOME/AI/ComfyUI/venv/bin/python" tools/redo_v2.py >> "$V2/logs/redo_v2.log" 2>&1 < /dev/null
