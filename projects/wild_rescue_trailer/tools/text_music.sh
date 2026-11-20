#!/bin/bash
# Text the 3 score candidates to Matt from the mini, exactly as last_signal did (2026-10-31):
# scp to mini-vps:Pictures/, one plain Messages text first, then each mp4 via `send (POSIX file ...)` to participant
# "matt@ineedhemp.com" of the iMessage account; then read is_delivered from the mini's chat.db and delete the mini copies.
set -u
P="$(cd "$(dirname "$0")/.." && pwd)"
FILES=(HankDoug_music_1.mp4 HankDoug_music_2.mp4 HankDoug_music_3.mp4)
for f in "${FILES[@]}"; do scp -q "$P/music/send/$f" "mini-vps:Pictures/$f" || exit 1; done
START=$(ssh mini-vps 'sqlite3 ~/Library/Messages/chat.db "select max(ROWID) from message"')
ssh mini-vps "osascript -e 'tell application \"Messages\" to send \"Hank & Doug music: 3 versions coming, reply 1, 2 or 3\" to participant \"matt@ineedhemp.com\" of (1st account whose service type = iMessage)'"
sleep 4
for f in "${FILES[@]}"; do
  ssh mini-vps "osascript -e 'tell application \"Messages\" to send (POSIX file \"/Users/matthewmacosko/Pictures/$f\") to participant \"matt@ineedhemp.com\" of (1st account whose service type = iMessage)'"
  sleep 6
done
echo "rows after $START:"
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
  OUT=$(ssh mini-vps "sqlite3 ~/Library/Messages/chat.db \"select m.ROWID, m.is_delivered, m.is_from_me, coalesce(m.text,''), coalesce(a.transfer_name,'') from message m left join message_attachment_join j on j.message_id=m.ROWID left join attachment a on a.ROWID=j.attachment_id where m.ROWID > $START and m.is_from_me=1 order by m.ROWID\"")
  N=$(echo "$OUT" | grep -c "|1|1|")
  [ "$N" -ge 4 ] && break
  sleep 10
done
echo "$OUT"
for f in "${FILES[@]}"; do ssh mini-vps "rm -f ~/Pictures/$f"; done
echo "mini copies deleted"
