#!/bin/bash
# rough_cut.sh — first assembly of Circus Train from what exists (2026-07-23).
# Story order: scene wides intercut with a2v dialogue close-ups, everything
# normalized to 832x480@24fps + 44.1k stereo (scene finals are silent → anullsrc).
# S4/S7/S8 don't exist yet; L03/L08/L12/L16 (bird/Ellie VO) not yet placed.
# Output: rough_cut_v1.mp4 (no music) — music gets muxed in a second pass.
cd "$(dirname "$0")"
set -e

ORDER=(
  clips/s1_final.mp4 a2v/L01_hank.mp4 a2v/L02_doug.mp4
  clips/s2_final.mp4 a2v/L04_doug.mp4
  clips/s3_final.mp4 a2v/L05_hank.mp4 a2v/L06_doug.mp4
  clips/s5_final.mp4 a2v/L07_doug.mp4 a2v/L09_doug.mp4 a2v/L10_doug.mp4
  clips/s6_final.mp4 a2v/L11_hank.mp4
  a2v/L13_doug.mp4 a2v/L14_doug.mp4 a2v/L15_hank.mp4
)

INPUTS=()
FILTER=""
i=0
for f in "${ORDER[@]}"; do
  INPUTS+=(-i "$f")
  FILTER+="[$i:v]scale=832:480:force_original_aspect_ratio=decrease,pad=832:480:(ow-iw)/2:(oh-ih)/2,fps=24,setsar=1,format=yuv420p[v$i];"
  if ffprobe -v error -select_streams a -show_entries stream=codec_name -of csv=p=0 "$f" | grep -q .; then
    FILTER+="[$i:a]aresample=44100,aformat=channel_layouts=stereo[a$i];"
  else
    d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
    FILTER+="anullsrc=r=44100:cl=stereo,atrim=duration=$d[a$i];"
  fi
  i=$((i+1))
done
n=$i
for ((k=0; k<n; k++)); do FILTER+="[v$k][a$k]"; done
FILTER+="concat=n=$n:v=1:a=1[vout][aout]"

ffmpeg -loglevel error "${INPUTS[@]}" -filter_complex "$FILTER" \
  -map "[vout]" -map "[aout]" -c:v libx264 -crf 19 -preset medium \
  -c:a aac -b:a 160k -y rough_cut_v1.mp4
echo "ROUGH_CUT_V1_DONE $(ffprobe -v error -show_entries format=duration -of csv=p=0 rough_cut_v1.mp4)s"
