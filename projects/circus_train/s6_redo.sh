#!/bin/bash
cd "$(dirname "$0")"
until grep -q "A2V_BATCH_DONE" a2v.log 2>/dev/null; do sleep 60; done
try() { # resolution big_mode
  NAME=$(curl -s -F "image=@stills/LOCKED_s6.png" http://127.0.0.1:17600/api/upload | python3 -c "import json,sys; print(json.load(sys.stdin)['name'])")
  JOB=$(curl -s -X POST http://127.0.0.1:17600/api/render -H 'Content-Type: application/json' -d "{\"prompt\": \"the bear pushes hard against the wooden door with his shoulder, the door shuddering, splinters and dust bursting from the frame, his fur rippling with effort, camera holding steady\", \"image_name\": \"$NAME\", \"duration\": 5, \"quality\": \"fast\", \"resolution\": \"$1\", \"big_mode\": $2}" | python3 -c "import json,sys; print(json.load(sys.stdin).get('job_id',''))")
  [ -z "$JOB" ] && return 1
  for i in $(seq 1 400); do
    ST=$(curl -s -m 10 "http://127.0.0.1:17600/api/status/$JOB")
    STATE=$(echo "$ST" | python3 -c "import json,sys; print(json.load(sys.stdin).get('state',''))" 2>/dev/null)
    [ "$STATE" = "done" ] && { MP4=$(echo "$ST" | python3 -c "import json,sys; print(json.load(sys.stdin).get('mp4',''))"); cp "$MP4" clips/s6_final.mp4; return 0; }
    { [ "$STATE" = "error" ] || [ "$STATE" = "cancelled" ]; } && return 1
    sleep 8
  done
  return 1
}
if try "832x480" "true"; then echo "S6 REDO DONE (big mode)"
elif try "768x448" "false"; then echo "S6 REDO DONE (768x448 standard fallback)"
else echo "S6 REDO FAILED BOTH"; fi
