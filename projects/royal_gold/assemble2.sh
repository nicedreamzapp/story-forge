#!/bin/bash
# Royal Gold v2 — smooth motion + animated overlay + Piper narration (speaker 0).
set -e
cd ~/Desktop/PROJECTS/story-forge/projects/royal_gold
FF=/opt/homebrew/bin/ffmpeg
C=coverage; V=vo; W=/tmp/rg_asm2; rm -rf "$W"; mkdir -p "$W"
OUT=RoyalGold_Commercial.mp4

CLIPS=(t1_intro s1_humboldt s2a_coco_macro s2b_coco_fiber s3a_kings s3b_planting \
       s3c_boost s4a_greenhouse s4b_seedling s5a_warehouse s5b_bloom s6_gardener t2_outro)

# ---------- VIDEO ----------
INARGS=(); PRE=""; FILT=""; i=0
for c in "${CLIPS[@]}"; do INARGS+=(-i "$C/$c.mp4"); PRE+="[$i:v]setsar=1,fps=24,format=yuv420p[v$i];"; FILT+="[v$i]"; i=$((i+1)); done
OVI=$i; INARGS+=(-i overlay/particles.mov)   # overlay input index
GRADE="eq=contrast=1.06:saturation=1.11:gamma=0.97,colorbalance=rs=0.05:gs=0.02:bs=-0.05:rm=0.04:bm=-0.04:rh=0.03:bh=-0.03,vignette=PI/5"
$FF -y -hide_banner -loglevel error "${INARGS[@]}" -filter_complex \
 "${PRE}${FILT}concat=n=${#CLIPS[@]}:v=1:a=0[cat];[cat]${GRADE}[g];[g][${OVI}:v]overlay=format=auto:shortest=1[ovl];[ovl]fade=t=in:st=0:d=0.5,fade=t=out:st=31.2:d=0.8,format=yuv420p[v]" \
 -map "[v]" -r 24 -c:v libx264 -preset slow -crf 17 "$W/video.mp4"
echo "video: $(/opt/homebrew/bin/ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$W/video.mp4")s"

# ---------- AUDIO (mirror Song Forge commercial dub recipe) ----------
declare -a T=(0.8 3.4 7.9 13.9 18.4 22.4 28.7)   # P1..P7 start times
AIN=(-i assets/music_bed.wav); AF=""; n=1
for k in 1 2 3 4 5 6 7; do
  AIN+=(-i "$V/P$k.wav")
  ms=$(printf "%.0f" "$(echo "${T[$((k-1))]}*1000"|/usr/bin/bc -l)")
  AF+="[$n]adelay=${ms}|${ms}[a$k];"; n=$((n+1))
done
AF+="[a1][a2][a3][a4][a5][a6][a7]amix=inputs=7:normalize=0:dropout_transition=0[vom];"
# voice polish chain (denoise, EQ presence, de-ess, comp, loudnorm)
AF+="[vom]apad=whole_dur=32,afftdn=nr=10:nf=-25,highpass=f=75,equalizer=f=160:t=q:w=1.0:g=2,equalizer=f=3000:t=q:w=1.5:g=1.5,equalizer=f=11000:t=q:w=1.5:g=2,deesser=i=0.6,acompressor=threshold=-20dB:ratio=3:attack=5:release=160:knee=2.5,alimiter=limit=0.95,loudnorm=I=-16:TP=-1.2:LRA=8[vo];"
AF+="[vo]asplit=2[vo1][vosc];"
AF+="[0]atrim=0:32,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.8,afade=t=out:st=30.8:d=1.2,loudnorm=I=-22:TP=-3:LRA=11[mus];"
AF+="[mus][vosc]sidechaincompress=threshold=0.05:ratio=8:attack=8:release=300:makeup=2:level_sc=1[musd];"
AF+="[vo1][musd]amix=inputs=2:duration=longest:weights=1.0 0.55:dropout_transition=0[mixraw];"
AF+="[mixraw]acompressor=threshold=-12dB:ratio=2:attack=10:release=120,loudnorm=I=-14:TP=-1.0:LRA=8[aout]"
$FF -y -hide_banner -loglevel error "${AIN[@]}" -filter_complex "$AF" -map "[aout]" -t 32 -ac 2 -ar 48000 -c:a pcm_s16le "$W/audio.wav"
echo "audio: $(/opt/homebrew/bin/ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$W/audio.wav")s"

# ---------- MUX ----------
$FF -y -hide_banner -loglevel error -i "$W/video.mp4" -i "$W/audio.wav" \
  -map 0:v -map 1:a -t 32 -c:v copy -c:a aac -b:a 256k -movflags +faststart "$OUT"
echo "FINAL: $OUT  $(/opt/homebrew/bin/ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$OUT")s"
