#!/bin/bash
# Deploy THE LAST SIGNAL section to the Story Forge page + the card on /software/.
# Pulls fresh live copies first (the site-syncer touches /software/ daily), rebuilds, backs up, uploads, verifies.
set -euo pipefail
cd "$(dirname "$0")"
R=domains/nicedreamzwholesale.com/public_html/software
STAMP=$(date +%Y%m%d-%H%M)
scp -q ineedhemp:$R/story-forge/index.html live/story-forge.index.html
scp -q ineedhemp:$R/index.html live/software.index.html
grep -q 'id="last-signal"' live/story-forge.index.html && { echo "already deployed"; exit 0; }
python3 build_pages.py
ssh ineedhemp "cp $R/story-forge/index.html $R/story-forge/index.html.bak-lastsignal-$STAMP && cp $R/index.html $R/index.html.bak-lastsignal-$STAMP"
scp -q staged/story-forge.index.html ineedhemp:$R/story-forge/index.html
scp -q staged/software.index.html ineedhemp:$R/index.html
ssh ineedhemp "cd domains/nicedreamzwholesale.com/public_html && wp cache flush" || true
sleep 3
a=$(curl -s "https://nicedreamzwholesale.com/software/story-forge/?v=$STAMP" | grep -c 'id="last-signal"' || true)
b=$(curl -s "https://nicedreamzwholesale.com/software/?v=$STAMP" | grep -c 'story-forge/#last-signal' || true)
echo "story-forge section: $a (expect 1) | software card links: $b (expect 2)"
echo "rollback: ssh ineedhemp 'cp $R/story-forge/index.html.bak-lastsignal-$STAMP $R/story-forge/index.html; cp $R/index.html.bak-lastsignal-$STAMP $R/index.html'"
