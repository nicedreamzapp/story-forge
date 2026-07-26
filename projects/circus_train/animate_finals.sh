#!/bin/bash
cd "$(dirname "$0")"
declare -a SCENES=(
  "s1|stills/s1_final_v3.png|the dog's tail wagging, the bear lifting the fishing rod up and down, the line swinging, ripples and small splashes on the creek, leaves falling, both characters turning their heads toward each other, wind moving grass and fur"
  "s2|stills/LOCKED_s2_wide.png|the wooden wagon rolls forward along the road, wheels turning, dust billowing behind, the horse galloping, the bear's fur and the rope reins swaying with the motion, camera tracking alongside"
  "s3|stills/LOCKED_s3.png|heat shimmer rising from the train cars, dust motes floating in the bright light, the bear and dog slowly stepping forward looking up at the train, tails swaying gently, mouths stay closed"
  "s5|stills/LOCKED_s5.png|subtle slow camera push-in, the dog's ears swaying slightly as he presses his nose near the door crack, dust drifting in warm light rays, gentle breathing"
  "s6|stills/LOCKED_s6.png|the bear pushes hard against the wooden door with his shoulder, the door shuddering, splinters and dust bursting from the frame, his fur rippling with effort, camera holding steady"
)
for entry in "${SCENES[@]}"; do
  IFS='|' read -r id img motion <<< "$entry"
  [ -f "clips/${id}_final.mp4" ] && { echo "skip $id"; continue; }
  while [ "$(curl -s -m 5 http://127.0.0.1:8767/api/status | python3 -c 'import json,sys; print(json.load(sys.stdin).get("jobs_running",0))' 2>/dev/null)" != "0" ]; do
    echo "forge busy — waiting"; sleep 120
  done
  echo "=== $id final"
  NAME=$(curl -s -F "image=@$img" http://127.0.0.1:17600/api/upload | python3 -c "import json,sys; print(json.load(sys.stdin)['name'])")
  [ -z "$NAME" ] && { echo "$id upload FAILED"; continue; }
  JOB=$(curl -s -X POST http://127.0.0.1:17600/api/render -H 'Content-Type: application/json' \
    -d "{\"prompt\": \"$motion\", \"image_name\": \"$NAME\", \"duration\": 5, \"quality\": \"fast\", \"resolution\": \"832x480\", \"big_mode\": true}" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('job_id',''))")
  [ -z "$JOB" ] && { echo "$id submit FAILED"; continue; }
  echo "$id job $JOB"
  for i in $(seq 1 400); do
    ST=$(curl -s -m 10 "http://127.0.0.1:17600/api/status/$JOB")
    STATE=$(echo "$ST" | python3 -c "import json,sys; print(json.load(sys.stdin).get('state',''))" 2>/dev/null)
    if [ "$STATE" = "done" ]; then
      MP4=$(echo "$ST" | python3 -c "import json,sys; print(json.load(sys.stdin).get('mp4',''))")
      cp "$MP4" "clips/${id}_final.mp4" && echo "$id FINAL DONE"
      break
    elif [ "$STATE" = "error" ] || [ "$STATE" = "cancelled" ]; then
      echo "$id FINAL FAILED: $ST"; break
    fi
    sleep 8
  done
done
echo FINALS_DONE
