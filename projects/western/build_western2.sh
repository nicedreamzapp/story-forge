#!/bin/bash
# Old-Western MOUNTED duel — cowboy w/ revolver vs Native warrior w/ bow, both on
# horseback. Leone rhythm, vintage film grade, accelerating cuts into the draw;
# arrow-loose whoosh + gunshot at the climax.
set -e
cd ~/Desktop/PROJECTS/story-forge/projects/western
FF=/opt/homebrew/bin/ffmpeg; FP=/opt/homebrew/bin/ffprobe
C=coverage2
OUT=WESTERN_mounted_duel.mp4
W=/tmp/west2; rm -rf "$W"; mkdir -p "$W"
WIDE=$(ls -t $C/mwide_*.mp4|head -1); WALT=$(ls -t $C/mwidealt_*.mp4|head -1)
GRADE="eq=contrast=1.06:saturation=0.72:gamma=0.98,colorbalance=rs=0.12:gs=0.03:bs=-0.10:rm=0.06:bm=-0.06,vignette=PI/4,noise=alls=7:allf=t,scale=1280:720,crop=1280:540:0:90,pad=1280:720:0:90:black,format=yuv420p"
norm(){ $FF -y -hide_banner -loglevel error -i "$1" -t "$3" -vf "$GRADE,fps=24,setsar=1" -an -c:v libx264 -preset medium -crf 18 "$2"; }
norm "$WIDE"             "$W/0.mp4" 2.5
norm "$C/cowboy_kb.mp4"  "$W/1.mp4" 1.75
norm "$C/warrior_kb.mp4" "$W/2.mp4" 1.75
norm "$C/bow_kb.mp4"     "$W/3.mp4" 1.4
norm "$WALT"             "$W/4.mp4" 2.0
norm "$C/cowboy_kb.mp4"  "$W/5.mp4" 0.9
norm "$C/warrior_kb.mp4" "$W/6.mp4" 0.9
norm "$C/bow_kb.mp4"     "$W/7.mp4" 0.7
norm "$WALT"             "$W/8.mp4" 2.6
for n in 0 1 2 3 4 5 6 7 8; do echo "file '$W/$n.mp4'"; done > "$W/list.txt"
$FF -y -hide_banner -loglevel error -f concat -safe 0 -i "$W/list.txt" -c copy "$W/v.mp4"
VD=$($FP -v error -show_entries format=duration -of default=nk=1:nw=1 "$W/v.mp4")
DRAW=$(echo "2.5+1.75+1.75+1.4+2.0+0.9+0.9+0.7" | bc)
FO=$(echo "$VD - 1.6" | bc)
DMS=$(echo "$DRAW*1000/1"|bc)
# gunshot crack + arrow whoosh
$FF -y -hide_banner -loglevel error -f lavfi -i "anoisesrc=d=0.3:c=white:a=1" -af "volume=3,lowpass=f=1600,afade=t=out:st=0.04:d=0.26" "$W/shot.wav"
$FF -y -hide_banner -loglevel error -f lavfi -i "anoisesrc=d=0.35:c=brown:a=0.8" -af "volume=2,highpass=f=400,lowpass=f=4000,afade=t=in:st=0:d=0.02,afade=t=out:st=0.08:d=0.27" "$W/whoosh.wav"
$FF -y -hide_banner -loglevel error -i "$W/v.mp4" \
  -f lavfi -i "sine=frequency=52:duration=${VD}" -i "$W/shot.wav" -i "$W/whoosh.wav" \
  -filter_complex "\
   [0:v]fade=t=in:st=0:d=0.6,fade=t=out:st=${FO}:d=1.6[v];\
   [1:a]volume=0.16,tremolo=f=5:d=0.4,aformat=channel_layouts=stereo[dr];\
   [2:a]volume=1.0,aformat=channel_layouts=stereo,adelay=${DMS}|${DMS}[gs];\
   [3:a]volume=1.0,aformat=channel_layouts=stereo,adelay=${DMS}|${DMS}[wh];\
   [dr][gs][wh]amix=inputs=3:normalize=0[au]" \
  -map "[v]" -map "[au]" -t "$VD" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart "$OUT"
echo "MOUNTED DUEL: ${VD}s (draw @ ${DRAW}s) -> $OUT"