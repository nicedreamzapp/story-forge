#!/bin/bash
cd "$(dirname "$0")"
while [ "$(curl -s -m 5 http://127.0.0.1:8767/api/status | python3 -c 'import json,sys; print(json.load(sys.stdin).get("jobs_running",0))' 2>/dev/null)" != "0" ]; do sleep 120; done
NAME=$(curl -s -F "image=@stills/s1_final_v3.png" http://127.0.0.1:17600/api/upload | python3 -c "import json,sys; print(json.load(sys.stdin)['name'])")
JOB=$(curl -s -X POST http://127.0.0.1:17600/api/render -H 'Content-Type: application/json' -d "{\"prompt\": \"the dog's tail wagging happily, the bear lifting and lowering the fishing rod, the fishing line swinging, ripples spreading across the creek water, leaves falling steadily, both characters shifting their weight and turning their heads toward each other, breeze moving the grass\", \"image_name\": \"$NAME\", \"duration\": 5, \"quality\": \"fast\", \"resolution\": \"480x272\"}" | python3 -c "import json,sys; print(json.load(sys.stdin).get('job_id',''))")
echo "s1 redo job $JOB"
for i in $(seq 1 200); do
  ST=$(curl -s -m 10 "http://127.0.0.1:17600/api/status/$JOB")
  STATE=$(echo "$ST" | python3 -c "import json,sys; print(json.load(sys.stdin).get('state',''))" 2>/dev/null)
  [ "$STATE" = "done" ] && { MP4=$(echo "$ST" | python3 -c "import json,sys; print(json.load(sys.stdin).get('mp4',''))"); cp "$MP4" clips/s1_draft.mp4; echo "S1 REDO DONE"; break; }
  { [ "$STATE" = "error" ] || [ "$STATE" = "cancelled" ]; } && { echo "S1 REDO FAILED: $ST"; break; }
  sleep 6
done
