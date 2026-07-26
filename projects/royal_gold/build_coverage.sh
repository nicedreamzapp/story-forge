#!/bin/bash
# Royal Gold — generate all Ken-Burns coverage clips (clean 1280x720/24, no grade).
set -e
cd ~/Desktop/PROJECTS/story-forge/projects/royal_gold
FF=/opt/homebrew/bin/ffmpeg
A=assets; S=stills; C=coverage; mkdir -p "$C"

kb(){ # src out dur mode
  local SRC="$1" OUT="$2" D="$3" MODE="$4"
  local DF=$(printf "%.0f" "$(echo "$D*24"|/usr/bin/bc -l)")
  local BASE="scale=3840:2160:force_original_aspect_ratio=increase,crop=3840:2160"
  local Z X Y
  case "$MODE" in
    pushin)   Z="min(1.0+0.18*on/$DF,1.18)"; X="iw/2-(iw/zoom/2)"; Y="ih/2-(ih/zoom/2)";;
    pushslow) Z="min(1.0+0.10*on/$DF,1.10)"; X="iw/2-(iw/zoom/2)"; Y="ih/2-(ih/zoom/2)";;
    pullback) Z="max(1.18-0.18*on/$DF,1.0)"; X="iw/2-(iw/zoom/2)"; Y="ih/2-(ih/zoom/2)";;
    panR)     Z="1.14"; X="(iw-iw/zoom)*on/$DF"; Y="ih/2-(ih/zoom/2)";;
    panL)     Z="1.14"; X="(iw-iw/zoom)*(1-on/$DF)"; Y="ih/2-(ih/zoom/2)";;
  esac
  $FF -y -hide_banner -loglevel error -i "$SRC" \
    -vf "$BASE,zoompan=z='$Z':x='$X':y='$Y':d=$DF:s=1280x720:fps=24,format=yuv420p" \
    -frames:v "$DF" -c:v libx264 -preset medium -crf 18 -an "$OUT"
  echo "  $OUT  (${D}s ${MODE})"
}

echo "building coverage..."
kb "$S/humboldt_sunrise.png" "$C/s1_humboldt.mp4"   4.5 pushin
kb "$S/coco_macro.png"       "$C/s2a_coco_macro.mp4" 3.0 pushin
kb "$A/coco_fiber.jpg"       "$C/s2b_coco_fiber.mp4" 3.0 pullback
kb "$A/kings_mix.jpg"        "$C/s3a_kings.mp4"      1.5 panR
kb "$A/grow_c.jpg"           "$C/s3b_planting.mp4"   1.5 pushin
kb "$A/grow_d.jpg"           "$C/s3c_boost.mp4"      1.5 panL
kb "$A/grow_edit.png"        "$C/s4a_greenhouse.mp4" 2.0 pushin
kb "$S/hands_soil.png"       "$C/s4b_seedling.mp4"   2.0 pushin
kb "$A/grow_b.jpg"           "$C/s5a_warehouse.mp4"  2.0 pushslow
kb "$A/grow_a.jpg"           "$C/s5b_bloom.mp4"      1.5 panR
kb "$A/special_reserve.jpg"  "$C/s6_gardener.mp4"    2.5 pushslow
echo "DONE"; /bin/ls -la "$C"/*.mp4 | wc -l
