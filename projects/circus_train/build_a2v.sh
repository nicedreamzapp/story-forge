#!/bin/bash
# Lipsync close-ups: LTX-2 a2v from canon faces driven by verified voice wavs.
# Doug + Hank on-screen; bird/Ellie stay off-screen VO (no canon designs; Ellie
# is behind the door in-story anyway). Idempotent. Waits for finals first.
cd "$(dirname "$0")"
export HF_HUB_DISABLE_XET=1

mkdir -p a2v
declare -a LINES=(
  "L01_hank|hank" "L02_doug|doug" "L04_doug|doug" "L05_hank|hank"
  "L06_doug|doug" "L07_doug|doug" "L09_doug|doug" "L10_doug|doug"
  "L11_hank|hank" "L13_doug|doug" "L14_doug|doug" "L15_hank|hank"
)
for entry in "${LINES[@]}"; do
  IFS='|' read -r id who <<< "$entry"
  [ -f "a2v/${id}.mp4" ] && { echo "skip $id"; continue; }
  while [ "$(curl -s -m 5 http://127.0.0.1:8767/api/status | python3 -c 'import json,sys; print(json.load(sys.stdin).get("jobs_running",0))' 2>/dev/null)" != "0" ]; do
    echo "forge busy"; sleep 120
  done
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "voices/${id}.wav")
  # frames = round(dur*24/8)*8+1, clamped 97-257 (pilot-proven formula)
  N=$(python3 -c "d=float('$DUR'); n=round(d*24/8)*8+1; print(max(97, min(257, n)))")
  if [ "$who" = "doug" ]; then
    PROMPT="a Pixar 3D animated bloodhound dog with long floppy ears talking, his mouth moving naturally with the speech, gentle head movements, forest background"
  else
    PROMPT="a Pixar 3D animated brown bear with a tan muzzle talking, his mouth moving naturally with the speech, gentle head movements, forest background"
  fi
  echo "=== $id (${who}, ${DUR}s, ${N}f)"
  ~/Desktop/PROJECTS/story-forge/bin/mem-gate "a2v $id" || { echo "$id A2V SKIPPED (mem-gate)"; continue; }
  ~/ai-video-bench/mlxvid-venv/bin/mlx_video.ltx_2.generate \
    --model-repo prince-canuma/LTX-2-distilled \
    --image "canon/${who}_face.png" --audio-file "voices/${id}.wav" \
    --prompt "$PROMPT" \
    --pipeline distilled --height 512 --width 768 --num-frames $N --fps 24 \
    --output-path "a2v/${id}.mp4" 2>&1 | tail -1
  [ -f "a2v/${id}.mp4" ] && echo "$id A2V DONE" || echo "$id A2V FAILED"
done
echo A2V_BATCH_DONE
