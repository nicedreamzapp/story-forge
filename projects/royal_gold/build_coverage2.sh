#!/bin/bash
# Royal Gold v2 — SMOOTH sub-pixel coverage via ken_burns.py (NO zoompan, no shake).
set -e
cd ~/Desktop/PROJECTS/story-forge/projects/royal_gold
KB="/usr/bin/python3 /Users/dtribe/Desktop/PROJECTS/story-forge/bin/ken_burns.py"
A=assets; S=stills; C=coverage; mkdir -p "$C"

$KB "$S/humboldt_sunrise.png" "$C/s1_humboldt.mp4"   --dur 4.5 --mode pushin
$KB "$S/coco_macro.png"       "$C/s2a_coco_macro.mp4" --dur 3.0 --mode pushin
$KB "$A/coco_fiber.jpg"       "$C/s2b_coco_fiber.mp4" --dur 3.0 --mode pullback
$KB "$A/kings_mix.jpg"        "$C/s3a_kings.mp4"      --dur 1.5 --mode panR
$KB "$A/grow_c.jpg"           "$C/s3b_planting.mp4"   --dur 1.5 --mode pushin
$KB "$A/grow_d.jpg"           "$C/s3c_boost.mp4"      --dur 1.5 --mode panL
$KB "$A/grow_edit.png"        "$C/s4a_greenhouse.mp4" --dur 2.0 --mode pushin
$KB "$S/hands_soil.png"       "$C/s4b_seedling.mp4"   --dur 2.0 --mode pushin
$KB "$A/grow_b.jpg"           "$C/s5a_warehouse.mp4"  --dur 2.0 --mode pushslow
$KB "$A/grow_a.jpg"           "$C/s5b_bloom.mp4"      --dur 1.5 --mode panR
$KB "$A/special_reserve.jpg"  "$C/s6_gardener.mp4"    --dur 2.5 --mode pushslow
# logo cards: STATIC (animation comes from the shimmer + particle overlay)
$KB "$S/card_intro.png"       "$C/t1_intro.mp4"       --dur 3.0 --mode static
$KB "$S/card_outro.png"       "$C/t2_outro.mp4"       --dur 4.0 --mode static
echo "v2 coverage built: $(/bin/ls $C/*.mp4 | wc -l) clips"
