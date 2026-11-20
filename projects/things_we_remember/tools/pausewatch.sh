#!/bin/bash
# SIGSTOP this film's renders while Song Forge has customer jobs running; SIGCONT when clear.
PAT='things_we_remember|twr-'
stopped=0
while [ ! -f "$HOME/Desktop/PROJECTS/story-forge/projects/things_we_remember/tools/STOPWATCH" ]; do
  n=$(curl -s -m 5 127.0.0.1:8767/api/status | python3 -c 'import sys,json;print(json.load(sys.stdin).get("jobs_running",0))' 2>/dev/null || echo 0)
  pids="$(for q in $(pgrep -f "$PAT"); do ps -o comm= -p $q | grep -qiE "python|ltx|ffmpeg" && echo $q; done) $(cat $HOME/Desktop/PROJECTS/story-forge/projects/things_we_remember/tools/pids 2>/dev/null)"
  if [ "${n:-0}" -gt 0 ]; then
    [ -n "$pids" ] && kill -STOP $pids 2>/dev/null; [ $stopped = 0 ] && echo "$(date +%T) Song Forge busy ($n) -> SIGSTOP"; stopped=1
  elif [ $stopped = 1 ]; then
    [ -n "$pids" ] && kill -CONT $pids 2>/dev/null; echo "$(date +%T) clear -> SIGCONT"; stopped=0
  fi
  sleep 5
done
