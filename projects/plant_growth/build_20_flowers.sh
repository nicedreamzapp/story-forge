#!/bin/bash
# 20 animated seed-to-bloom flower clips. LOCKED RECIPE (Matt: "that was perfect"):
# Flux seedling still -> LTX i2v @768x512 growth+bloom -> upscale to 1280x720.
# Memory-safe: stills first (ComfyUI), then kill ComfyUI and run LTX one-at-a-time alone.
cd ~/Desktop/PROJECTS/story-forge/projects/plant_growth || exit 1
mkdir -p stages clips
LOG=/tmp/flowers20.log; : > "$LOG"
FLUX="$HOME/Scripts/flux_t2i.py"
VENV="$HOME/Desktop/PROJECTS/AI/ComfyUI/venv/bin/python"
LTX="$HOME/Desktop/PROJECTS/story-forge/bin/make-ltx-lightricks"
FF=/opt/homebrew/bin/ffmpeg
STILL_COMMON="single plant centered in frame, small terracotta pot in rich dark soil, lush dreamy green garden bokeh background, warm golden hour light, macro photography, photorealistic yet painterly and artistic, ultra detailed, shallow depth of field, vibrant and lush"
log(){ echo "$(date '+%H:%M:%S') $*" >> "$LOG"; }
comfy_up(){ /usr/bin/curl -s -m 6 -o /dev/null -w "%{http_code}" http://127.0.0.1:8188/system_stats 2>/dev/null | /usr/bin/grep -q 200; }

# key | start-subject (Flux) | bloom description (LTX)
FLOWERS=(
"dahlia|young dahlia plant with a forming bud|a large layered deep-pink dahlia bloom"
"rose|young rose bush with a forming bud|a velvety red rose opening"
"poppy|young poppy plant with a closed bud|a bright orange-red poppy flower"
"tulip|young tulip plant with a closed bud|a smooth pink tulip opening"
"marigold|young marigold plant with a forming bud|a ruffled golden-orange marigold"
"zinnia|young zinnia plant with a forming bud|a bright magenta zinnia"
"daisy|young daisy plant with a forming bud|a white daisy with a yellow center"
"cosmos|young cosmos plant with a forming bud|a delicate pink cosmos flower"
"lavender|young lavender plant with forming spikes|tall purple lavender spikes blooming"
"snapdragon|young snapdragon plant with a forming spike|a coral snapdragon spike blooming"
"peony|young peony plant with a round bud|a lush blush-pink peony unfurling"
"hibiscus|young hibiscus plant with a forming bud|a large red hibiscus opening"
"lily|young lily plant with a closed bud|a white and pink lily opening"
"iris|young iris plant with a forming bud|a purple iris unfurling"
"chrysanthemum|young chrysanthemum plant with a forming bud|a golden chrysanthemum blooming"
"ranunculus|young ranunculus plant with a round bud|layered coral ranunculus petals opening"
"anemone|young anemone plant with a forming bud|a deep purple anemone opening"
"orchid|young orchid plant with a forming bud|a purple and white orchid opening"
"gerbera|young gerbera daisy plant with a forming bud|a hot-pink gerbera daisy opening"
)

# ---------- PHASE 1: Flux start stills (needs ComfyUI) ----------
if ! comfy_up; then
  log "starting ComfyUI"
  ( cd "$HOME/Desktop/PROJECTS/AI/ComfyUI" && ./venv/bin/python main.py --listen 127.0.0.1 --port 8188 >/tmp/comfy_boot.log 2>&1 & )
fi
for i in $(seq 1 60); do comfy_up && break; sleep 3; done
log "ComfyUI ready; generating start stills"
for row in "${FLOWERS[@]}"; do
  key="${row%%|*}"; rest="${row#*|}"; subj="${rest%%|*}"
  [ -f "stages/${key}_start.png" ] && { log "still $key exists, skip"; continue; }
  /usr/bin/python3 "$FLUX" "a $subj, $STILL_COMMON" --out "stages/${key}_start.png" --w 1280 --h 720 --seed 77 >> "$LOG" 2>&1 \
    && log "STILL ok $key" || log "STILL FAIL $key"
done

# ---------- PHASE 2: kill ComfyUI, LTX i2v one-at-a-time ----------
log "killing ComfyUI before LTX (free its memory)"
/usr/bin/pkill -9 -f "main.py --listen" 2>/dev/null; sleep 5
comfy_up && log "WARN ComfyUI still up" || log "ComfyUI down, starting LTX phase"
n=0
for row in "${FLOWERS[@]}"; do
  key="${row%%|*}"; rest="${row#*|}"; bloom="${rest#*|}"
  n=$((n+1))
  [ -f "clips/${key}_anim.mp4" ] && { log "clip $key exists, skip"; continue; }
  [ -f "stages/${key}_start.png" ] || { log "no still for $key, skip"; continue; }
  log "LTX ($n/19) $key ..."
  "$VENV" "$LTX" --i2v "stages/${key}_start.png" --duration 6 --fps 16 --res 768x512 --label "$key" \
    "extreme time-lapse, the young plant rapidly grows taller, green leaves unfurl and multiply, the bud swells and bursts open into $bloom, continuous upward growth and blooming, gentle breeze, photorealistic, lush, cinematic" \
    >> "$LOG" 2>&1
  out=$(/bin/ls -t "$HOME/AI/videopipe/outputs/"*"${key}"_* 2>/dev/null | head -1)
  if [ -n "$out" ] && [ -f "$out" ]; then
    "$FF" -y -hide_banner -loglevel error -i "$out" -vf "scale=1280:720:flags=lanczos,format=yuv420p" -r 16 -c:v libx264 -crf 17 "clips/${key}_anim.mp4" \
      && log "CLIP ok $key" || log "UPSCALE FAIL $key"
  else
    log "LTX FAIL $key (no output)"
  fi
  sleep 2
done
log "BATCH DONE"
