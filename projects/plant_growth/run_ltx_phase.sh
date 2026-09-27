#!/bin/bash
# Phase-2 re-run: animate the 19 flower stills with LTX i2v in OFFLINE mode
# (cached models, immune to network blips). Skips any clip already made.
cd ~/Desktop/PROJECTS/story-forge/projects/plant_growth || exit 1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1
LOG=/tmp/flowers20_ltx.log; : > "$LOG"
VENV="$HOME/Desktop/PROJECTS/AI/ComfyUI/venv/bin/python"
LTX="$HOME/Desktop/PROJECTS/story-forge/bin/make-ltx-lightricks"
FF=/opt/homebrew/bin/ffmpeg
log(){ echo "$(date '+%H:%M:%S') $*" >> "$LOG"; }

FLOWERS=(
"dahlia|a large layered deep-pink dahlia bloom"
"rose|a velvety red rose opening"
"poppy|a bright orange-red poppy flower"
"tulip|a smooth pink tulip opening"
"marigold|a ruffled golden-orange marigold"
"zinnia|a bright magenta zinnia"
"daisy|a white daisy with a yellow center"
"cosmos|a delicate pink cosmos flower"
"lavender|tall purple lavender spikes blooming"
"snapdragon|a coral snapdragon spike blooming"
"peony|a lush blush-pink peony unfurling"
"hibiscus|a large red hibiscus opening"
"lily|a white and pink lily opening"
"iris|a purple iris unfurling"
"chrysanthemum|a golden chrysanthemum blooming"
"ranunculus|layered coral ranunculus petals opening"
"anemone|a deep purple anemone opening"
"orchid|a purple and white orchid opening"
"gerbera|a hot-pink gerbera daisy opening"
)
n=0; ok=0
for row in "${FLOWERS[@]}"; do
  key="${row%%|*}"; bloom="${row#*|}"; n=$((n+1))
  if [ -f "clips/${key}_anim.mp4" ]; then log "skip $key (clip exists)"; ok=$((ok+1)); continue; fi
  [ -f "stages/${key}_start.png" ] || { log "no still $key"; continue; }
  log "LTX ($n/19) $key ..."
  "$VENV" "$LTX" --i2v "stages/${key}_start.png" --duration 6 --fps 16 --res 768x512 --label "$key" \
    "extreme time-lapse, the young plant rapidly grows taller, green leaves unfurl and multiply, the bud swells and bursts open into $bloom, continuous upward growth and blooming, gentle breeze, photorealistic, lush, cinematic" \
    >> "$LOG" 2>&1
  out=$(/bin/ls -t "$HOME/AI/videopipe/outputs/"*"${key}"_* 2>/dev/null | head -1)
  if [ -n "$out" ] && [ -f "$out" ]; then
    "$FF" -y -hide_banner -loglevel error -i "$out" -vf "scale=1280:720:flags=lanczos,format=yuv420p" -r 16 -c:v libx264 -crf 17 "clips/${key}_anim.mp4" \
      && { log "CLIP ok $key"; ok=$((ok+1)); } || log "UPSCALE FAIL $key"
  else
    log "LTX FAIL $key (no output)"
  fi
  sleep 2
done
log "LTX PHASE DONE — clips ok: $ok/19"
