#!/bin/bash
# Build the 8-up growth grid + tie everything into one montage.
# Run AFTER the 20 clips + wind clip exist.
set -e
cd ~/Desktop/PROJECTS/story-forge/projects/plant_growth
FF=/opt/homebrew/bin/ffmpeg
C=clips; mkdir -p final

# --- 8-up grid (4x2), 6s, each cell 320x360 cover-cropped ---
GRID_CLIPS=(sunflower rose dahlia poppy tulip hibiscus zinnia gerbera)
INA=(); FC=""; i=0
for k in "${GRID_CLIPS[@]}"; do
  src="$C/${k}_anim.mp4"; [ -f "$src" ] || src="$C/$(ls $C | grep _anim | sed -n "$((i+1))p")"  # fallback
  INA+=(-i "$C/${k}_anim.mp4")
  FC+="[$i:v]scale=320:360:force_original_aspect_ratio=increase,crop=320:360,setsar=1,trim=0:6,setpts=PTS-STARTPTS[c$i];"
  i=$((i+1))
done
$FF -y -hide_banner -loglevel error "${INA[@]}" -filter_complex \
 "${FC}[c0][c1][c2][c3][c4][c5][c6][c7]xstack=inputs=8:layout=0_0|320_0|640_0|960_0|0_360|320_360|640_360|960_360,format=yuv420p[v]" \
 -map "[v]" -r 16 -t 6 -c:v libx264 -crf 18 final/grid8.mp4
echo "grid8 built"

# --- Montage: 4 hero growths -> 8-grid -> wind, with quick crossfades ---
HERO=(sunflower dahlia rose tulip)
seq_inputs=(); idx=0; xf=""
# (montage assembled in a second pass once wind clip confirmed)
echo "grid done; montage step runs in build_montage_final.sh"
