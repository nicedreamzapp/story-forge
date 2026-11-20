#!/bin/bash
# Build the sitka_demo fixture's local media from the hand-made Sitka promo folder.
# The media never goes in git (mp4/wav/glb/exr are ignored); this script recreates it.
#   SITKA_VIDEO=<path to sitka-video> projects/sitka_demo/prepare_fixture.sh
# Default SITKA_VIDEO: ../sitka-video next to the story-forge checkout.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SV="${SITKA_VIDEO:-$HERE/../../../sitka-video}"
[ -d "$SV/renders" ] || { echo "no Sitka renders under $SV (set SITKA_VIDEO)"; exit 2; }
mkdir -p "$HERE/assets" "$HERE/footage" "$HERE/overlays" "$HERE/music" "$HERE/refs"
cp -n "$SV/cadsnap/cad/glb/sitka_chair.glb" "$SV/cadsnap/cad/glb/sitka_stand.glb" "$HERE/assets/" 2>/dev/null || true
cp -n "$SV/hdri/studio_small_09_2k.exr" "$SV/hdri/cape_hill_4k.exr" "$HERE/assets/" 2>/dev/null || true
cp -n "$SV/music/bed_a.wav" "$HERE/music/bed.wav" 2>/dev/null || true
# the CAD renders the hand-made promo used (Blender Cycles/EEVEE from the same GLBs), as clips
for s in s02_hero_reveal s03_bluff s24_hills_wide s05_leaf_flex s01_knee_macro s06_ghost_walk \
         s10_sit_wide s12_knee_sit_close s04_strut_macro s07_spring_macro s13_lean_back \
         s27_every_part s25_kit_dock s26_finale s20_walk_bands s22_clutch_walk; do
  out="$HERE/footage/$s.mp4"
  [ -f "$out" ] && continue
  ffmpeg -v error -y -framerate 30 -pattern_type glob -i "$SV/renders/${s}_final/f*.png" \
    -c:v libx264 -crf 14 -pix_fmt yuv420p "$out"
  echo "footage/$s.mp4"
done
# design references: CAD stills, side and back
[ -f "$HERE/refs/ref_side.png" ] || cp "$(ls "$SV"/renders/s10_sit_wide_final/f*.png | tail -1)" "$HERE/refs/ref_side.png"
[ -f "$HERE/refs/ref_front.png" ] || cp "$(ls "$SV"/renders/s02_hero_reveal_final/f*.png | tail -1)" "$HERE/refs/ref_front.png"
# a Manim diagram as an alpha overlay (ProRes 4444)
cp -n "$SV/manim/out/d1_strut.mov" "$HERE/overlays/d1_strut.mov" 2>/dev/null || true
echo "fixture media ready in $HERE"
