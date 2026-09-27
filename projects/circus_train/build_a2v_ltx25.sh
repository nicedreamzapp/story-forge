#!/bin/bash
# Lipsync close-ups on LTX-2.5 (2026-08-29): canon faces driven by the verified voice wavs,
# through bin/make-ltx25 --audio (a2v). Same lines, prompts and framing as build_a2v.sh
# (the July LTX-2 path); output goes to a2v_ltx25/ so the two can be QC'd side by side,
# then the losers are deleted per rule 13.
cd "$(dirname "$0")"
MK=~/Desktop/PROJECTS/story-forge/bin/make-ltx25
mkdir -p a2v_ltx25
declare -a LINES=(
  "L01_hank|hank" "L02_doug|doug" "L04_doug|doug" "L05_hank|hank"
  "L06_doug|doug" "L07_doug|doug" "L09_doug|doug" "L10_doug|doug"
  "L11_hank|hank" "L13_doug|doug" "L14_doug|doug" "L15_hank|hank"
)
for entry in "${LINES[@]}"; do
  IFS='|' read -r id who <<< "$entry"
  [ -s "a2v_ltx25/${id}.mp4" ] && { echo "skip $id"; continue; }
  while [ "$(curl -s -m 5 http://127.0.0.1:8767/api/status | python3 -c 'import json,sys; print(json.load(sys.stdin).get("jobs_running",0))' 2>/dev/null)" != "0" ]; do
    echo "forge busy"; sleep 120
  done
  if [ "$who" = "doug" ]; then
    PROMPT="a Pixar 3D animated bloodhound dog with long floppy ears talking, his mouth moving naturally with the speech, gentle head movements, forest background"
  else
    PROMPT="a Pixar 3D animated brown bear with a tan muzzle talking, his mouth moving naturally with the speech, gentle head movements, forest background"
  fi
  echo "=== $id ($who) $(date +%H:%M:%S)"
  OUT=$("$MK" --i2v "canon/${who}_face.png" --audio "voices/${id}.wav" --res 768x512 --seed 42 --label "$id" "$PROMPT" 2>>a2v_ltx25/errors.log | tail -1)
  echo "$OUT"
  P=$(echo "$OUT" | sed -n 's/.*→ //p')
  if [ -n "$P" ] && [ -s "$P" ]; then cp "$P" "a2v_ltx25/${id}.mp4" && rm -f "$P" && echo "$id A2V DONE"; else echo "$id A2V FAILED"; fi
done
echo A2V_LTX25_BATCH_DONE
