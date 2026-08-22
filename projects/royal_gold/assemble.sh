#!/bin/bash
# Royal Gold — final assembly: graded video + scene-synced VO + ducked music bed.
set -e
cd ~/Desktop/PROJECTS/story-forge/projects/royal_gold
FF=/opt/homebrew/bin/ffmpeg
C=coverage; V=vo; W=/tmp/rg_asm; rm -rf "$W"; mkdir -p "$W"
OUT=RoyalGold_Commercial.mp4

# order (must total 32.0s)
CLIPS=(t1_intro s1_humboldt s2a_coco_macro s2b_coco_fiber s3a_kings s3b_planting \
       s3c_boost s4a_greenhouse s4b_seedling s5a_warehouse s5b_bloom s6_gardener t2_outro)

# ---------- VIDEO: concat + warm cinematic grade + tail fade ----------
INARGS=(); PRE=""; FILT=""
i=0
for c in "${CLIPS[@]}"; do INARGS+=(-i "$C/$c.mp4"); PRE+="[$i:v]setsar=1,fps=24,format=yuv420p[v$i];"; FILT+="[v$i]"; i=$((i+1)); done
GRADE="eq=contrast=1.06:saturation=1.10:gamma=0.97,colorbalance=rs=0.05:gs=0.02:bs=-0.05:rm=0.04:bm=-0.04:rh=0.03:bh=-0.03,vignette=PI/5,noise=alls=3:allf=t"
$FF -y -hide_banner -loglevel error "${INARGS[@]}" \
  -filter_complex "${PRE}${FILT}concat=n=${#CLIPS[@]}:v=1:a=0[cat];[cat]${GRADE},fade=t=out:st=31.2:d=0.8,format=yuv420p[v]" \
  -map "[v]" -r 24 -c:v libx264 -preset slow -crf 17 "$W/video.mp4"
echo "video built: $(/opt/homebrew/bin/ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$W/video.mp4")s"

# ---------- AUDIO: VO @ scene starts, music bed ducked under VO ----------
# VO line start times (seconds)
declare -a T=(0.6 3.4 7.9 14.0 18.4 22.4 28.7)   # L1..L7
AIN=(-i assets/music_bed.wav)
AF=""
n=1
for k in 1 2 3 4 5 6 7; do
  AIN+=(-i "$V/L$k.wav")
  ms=$(printf "%.0f" "$(echo "${T[$((k-1))]}*1000"|/usr/bin/bc -l)")
  AF+="[$n]adelay=${ms}|${ms}[a$k];"
  n=$((n+1))
done
AF+="[a1][a2][a3][a4][a5][a6][a7]amix=inputs=7:normalize=0:dropout_transition=0[vom];"
AF+="[vom]volume=3.2,alimiter=limit=0.95[vo];"
AF+="[vo]asplit=2[vo1][voscr];[voscr]apad,atrim=0:32[vosc];"
AF+="[0]atrim=0:32,volume=0.55,afade=t=in:st=0:d=0.6,afade=t=out:st=31.0:d=1.0[mus];"
AF+="[mus][vosc]sidechaincompress=threshold=0.06:ratio=8:attack=15:release=350[musd];"
AF+="[musd][vo1]amix=inputs=2:normalize=0[mix];"
AF+="[mix]loudnorm=I=-14:TP=-1.5:LRA=11[aout]"
$FF -y -hide_banner -loglevel error "${AIN[@]}" -filter_complex "$AF" -map "[aout]" -t 32 -c:a pcm_s16le "$W/audio.wav"
echo "audio built: $(/opt/homebrew/bin/ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$W/audio.wav")s"

# ---------- MUX ----------
$FF -y -hide_banner -loglevel error -i "$W/video.mp4" -i "$W/audio.wav" \
  -map 0:v -map 1:a -t 32 -c:v copy -c:a aac -b:a 192k -movflags +faststart "$OUT"
echo "FINAL: $OUT  ($(/opt/homebrew/bin/ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$OUT")s)"
