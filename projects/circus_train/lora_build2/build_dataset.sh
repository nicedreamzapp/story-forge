#!/bin/bash
# Doug LoRA v2 dataset — every image DERIVED from the locked master (canon by construction)
set -e
D="$HOME/Desktop/PROJECTS/story-forge/projects/circus_train/lora_build2/dataset"
C="$HOME/Desktop/PROJECTS/story-forge/projects/circus_train/canon"
G2="$HOME/mflux-venv/bin/mflux-generate-flux2"
GR="$HOME/mflux-venv/bin/mflux-generate-redux"
M="AITRADER/FLUX2-klein-9B-mlx-8bit"

# anchors straight from canon
cp "$C/doug_canon.png" "$D/d01_master.png"
cp "$C/doug_face.png"  "$D/d02_face.png"
python3 - <<'PY'
from PIL import Image
import os
D = os.path.expanduser("~/Desktop/PROJECTS/story-forge/projects/circus_train/lora_build2/dataset")
m = Image.open(f"{D}/d01_master.png")
m.crop((250, 60, 800, 610)).save(f"{D}/d03_upperbody.png")
PY

# 6 Redux identity variations from the canon face (FLUX.1, strength .86-.88)
i=4
for s in 0.86 0.87 0.88; do
  for seed in 11 23; do
    nice -n 10 $GR --base-model dev -q 8 --redux-image-paths "$C/doug_face.png" \
      --redux-image-strengths $s --steps 24 --seed $seed --width 768 --height 768 \
      --output "$D/d0${i}_redux_${s}_${seed}.png" \
      --prompt "Pixar 3D animated bloodhound dog portrait" 2>&1 | tail -1
    i=$((i+1))
  done
done

# 3 low-strength FLUX.2 img2img full-body variations from the master
j=0
for s in 0.22 0.28 0.34; do
  nice -n 10 $G2 -m $M --guidance 1.0 --steps 24 --seed $((41+j)) \
    --image-path "$C/doug_canon.png" --image-strength $s --width 832 --height 832 \
    --output "$D/d1${j}_body_${s}.png" \
    --prompt "dougdog tall lanky orange-tan Pixar 3D bloodhound standing on grass, very long heavy flat smooth dark-brown floppy ears hanging straight down, droopy jowls, bare neck no collar, full body" 2>&1 | tail -1
  j=$((j+1))
done

# captions — trigger + the exact rules
for f in "$D"/*.png; do
  base="${f%.png}"
  echo "dougdog, a tall lanky orange-tan Pixar 3D bloodhound dog, very long heavy flat smooth dark-brown floppy ears hanging straight down past the jaw, droopy jowls, soulful eyes, completely bare neck with no collar" > "$base.txt"
done
echo DATASET_DONE
ls "$D" | wc -l
