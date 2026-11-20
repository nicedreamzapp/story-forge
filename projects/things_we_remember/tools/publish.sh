#!/bin/bash
# publish.sh NAME : private link on the VPS; re-encode crf 20 +faststart if over 200 MB; URL -> final/link_NAME.txt
P=~/Desktop/PROJECTS/story-forge/projects/things_we_remember; cd $P; N=$1; F=final/the_things_we_remember_$N.mp4; U=$F
if [ $(stat -f %z $F) -gt 200000000 ]; then U=/tmp/twr_pub_$N.mp4; ffmpeg -v error -y -i $F -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p -c:a copy -movflags +faststart $U; fi
NAME="things-we-remember-${N//_/-}-$(openssl rand -hex 6).mp4"
SF_ENV="${STORY_FORGE_ENV:-$HOME/.config/story-forge/publish.env}"; if [ -f "$SF_ENV" ]; then . "$SF_ENV"; fi; : "${SF_VPS:?set SF_VPS (user@host) in $SF_ENV}" "${SF_VPS_DIR:?set SF_VPS_DIR in $SF_ENV}" "${SF_VPS_URL:?set SF_VPS_URL in $SF_ENV}"
scp -q $U "$SF_VPS:$SF_VPS_DIR/$NAME" && ssh "$SF_VPS" "chmod 644 $SF_VPS_DIR/$NAME"
URL="$SF_VPS_URL/$NAME"; code=$(curl -s -o /dev/null -w '%{http_code}' -I "$URL")
echo "$code $URL $(du -h $U | cut -f1)"; [ "$code" = 200 ] && echo "$URL" > final/link_$N.txt
