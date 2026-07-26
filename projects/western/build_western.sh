#!/bin/bash
# Old-Western high-noon duel — Leone style. Beautiful stills + gentle i2v + tension
# Ken-Burns punch-ins, ACCELERATING hard cuts into the draw, vintage film grade
# (warm, grain, 2.37:1 letterbox), gunshot at the climax.
set -e
cd ~/Desktop/PROJECTS/story-forge/projects/western
FF=/opt/homebrew/bin/ffmpeg; FP=/opt/homebrew/bin/ffprobe
C=coverage
OUT=WESTERN_duel.mp4
W=/tmp/west; rm -rf "$W"; mkdir -p "$W"
WIDE=$(ls -t $C/wide_ltxL_*.mp4|head -1); WALT=$(ls -t $C/widealt_ltxL_*.mp4|head -1)
GRADE="eq=contrast=1.06:saturation=0.72:gamma=0.98,colorbalance=rs=0.12:gs=0.03:bs=-0.10:rm=0.06:bm=-0.06,vignette=PI/4,noise=alls=7:allf=t,scale=1280:720,crop=1280:540:0:90,pad=1280:720:0:90:black,format=yuv420p"
# normalize+grade+trim a shot:  norm IN OUT DUR
norm(){ $FF -y -hide_banner -loglevel error -i "$1" -t "$3" -vf "$GRADE,fps=24,setsar=1" -an -c:v libx264 -preset medium -crf 18 "$2"; }
norm "$WIDE"          "$W/0.mp4" 2.5
norm "$C/cowboy_kb.mp4"  "$W/1.mp4" 1.75
norm "$C/warrior_kb.mp4" "$W/2.mp4" 1.75
norm "$C/hands_kb.mp4"   "$W/3.mp4" 1.4
norm "$WALT"          "$W/4.mp4" 2.0
norm "$C/cowboy_kb.mp4"  "$W/5.mp4" 0.9
norm "$C/warrior_kb.mp4" "$W/6.mp4" 0.9
norm "$C/hands_kb.mp4"   "$W/7.mp4" 0.7
norm "$WALT"          "$W/8.mp4" 2.6
for n in 0 1 2 3 4 5 6 7 8; do echo "file '$W/$n.mp4'"; done > "$W/list.txt"
$FF -y -hide_banner -loglevel error -f concat -safe 0 -i "$W/list.txt" -c copy "$W/v.mp4"
VD=$($FP -v error -show_entries format=duration -of default=nk=1:nw=1 "$W/v.mp4")
DRAW=$(echo "2.5+1.75+1.75+1.4+2.0+0.9+0.9+0.7" | bc)   # start of the final wide = the draw
FO=$(echo "$VD - 1.6" | bc)
# --- audio: low tension drone (whole) + gunshot crack at the draw ---
$FF -y -hide_banner -loglevel error -f lavfi -i "anoisesrc=d=0.3:c=white:a=1" -af "volume=3,lowpass=f=1600,afade=t=out:st=0.04:d=0.26" "$W/shot.wav"
$FF -y -hide_banner -loglevel error -i "$W/v.mp4" \
  -f lavfi -i "sine=frequency=52:duration=${VD}" \
  -i "$W/shot.wav" \
  -filter_complex "\
   [0:v]fade=t=in:st=0:d=0.6,fade=t=out:st=${FO}:d=1.6[v];\
   [1:a]volume=0.16,tremolo=f=5:d=0.4,aformat=channel_layouts=stereo[dr];\
   [2:a]volume=1.0,aformat=channel_layouts=stereo,adelay=$(echo "$DRAW*1000/1"|bc)|$(echo "$DRAW*1000/1"|bc)[gs];\
   [dr][gs]amix=inputs=2:normalize=0[au]" \
  -map "[v]" -map "[au]" -t "$VD" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart "$OUT"
echo "WESTERN DUEL: ${VD}s  (gunshot @ ${DRAW}s) -> $OUT"