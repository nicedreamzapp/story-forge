#!/bin/bash
# Fetch Rhubarb Lip Sync (macOS) next to this script.
#
# Rhubarb is a third-party tool (github.com/DanielSWolf/rhubarb-lip-sync) with
# its own license, and its release bundles a Sphinx acoustic model plus Adobe
# After Effects extras. It is fetched here rather than committed so the repo
# does not carry ~83 MB of someone else's binaries in its history forever.
set -euo pipefail
VER="${RHUBARB_VERSION:-1.14.0}"
DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$DIR/Rhubarb-Lip-Sync-$VER-macOS"

if [ -x "$TARGET/rhubarb" ]; then
  echo "Rhubarb $VER already present: $TARGET"
  exit 0
fi

URL="https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v$VER/Rhubarb-Lip-Sync-$VER-macOS.zip"
echo "Fetching Rhubarb $VER..."
curl -fL --retry 3 -o "$DIR/Rhubarb-Lip-Sync-$VER-macOS.zip" "$URL"
unzip -q -o "$DIR/Rhubarb-Lip-Sync-$VER-macOS.zip" -d "$DIR"
rm -f "$DIR/Rhubarb-Lip-Sync-$VER-macOS.zip"
chmod +x "$TARGET/rhubarb"
echo "Rhubarb ready: $TARGET/rhubarb"
