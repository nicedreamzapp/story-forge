#!/bin/bash
# FINAL STAGE — runs after extensions (clean GPU). Fix red_rock western score, then assemble
# + smooth + deliver all 5 films to Desktop. Single GPU customer at a time.
source /Users/dtribe/Desktop/PROJECTS/story-forge/bin/render_guard.sh
SF=/Users/dtribe/Desktop/PROJECTS/story-forge
PROJ=$SF/projects
WHISPER="/opt/homebrew/bin/whisper-cli -m $HOME/whisper-models/ggml-small.en.bin"

# 1. restart ACE clean, regenerate red_rock western (gated, up to 5 tries)
pkill -f "ComfyUI/main.py" 2>/dev/null; sleep 5
cd "$SF/engines/ACE-Step-1.5" 2>/dev/null || cd "$SF/../Song Forge/engines/ACE-Step-1.5"
nohup bash start_api_server_macos.sh > /tmp/song_forge_ace.log 2>&1 &
for i in $(seq 1 40); do sleep 6; curl -s -m 5 http://127.0.0.1:8001/health >/dev/null 2>&1 && break; done
DIR="$PROJ/red_rock_standoff"; rm -f "$DIR/score_red_rock.wav"
for try in 1 2 3 4 5; do
  resp=$(curl -s -m 15 -X POST http://127.0.0.1:8767/api/song -H "Content-Type: application/json" \
    -d '{"style":"pure instrumental spaghetti western score, lone twang electric guitar, mariachi trumpet, whistling melody, galloping percussion, no voice no singing, Ennio Morricone","lyrics":"[instrumental]","voice":"none"}')
  id=$(python3 -c "import json,sys;print(json.loads(sys.argv[1]).get('id',''))" "$resp" 2>/dev/null)
  [ -z "$id" ] && { sleep 8; continue; }
  for i in $(seq 1 100); do sleep 12
    st=$(curl -s -m 10 http://127.0.0.1:8767/api/song/$id | python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('status','?'),d.get('audio',''))" 2>/dev/null)
    case "$st" in
      done*) au="${st#done }"; curl -s -m 60 "http://127.0.0.1:8767$au" -o "$DIR/score_red_rock.wav" 2>/dev/null
        w=$($WHISPER -f "$DIR/score_red_rock.wav" -np -nt 2>/dev/null | python3 -c "import sys,re;t=sys.stdin.read();t=re.sub(r'\(.*?\)|\[.*?\]|♪','',t);print(len(re.findall(r'[A-Za-z]{2,}',t)))")
        [ "${w:-9}" -le 3 ] && { echo "[final] red_rock CLEAN ($w)"; break 2; } || { echo "[final] red_rock vocal ($w) retry"; rm -f "$DIR/score_red_rock.wav"; }
        break;; error*) break;; esac
  done
done
[ -f "$DIR/score_red_rock.wav" ] || { echo "[final] red_rock fallback to pirate score"; cp "$PROJ/last_treasure/score_last_treasure.wav" "$DIR/score_red_rock.wav"; }

# 2. assemble + mix + deliver all 5
for proj in hank_and_doug/wild_rescue leash_snapped red_rock_standoff red_horizon last_treasure; do
  cd "$PROJ/$proj"
  python3 assemble.py cut    >/dev/null 2>&1
  python3 assemble.py timeline 2>&1 | tail -1
  python3 assemble.py mix    2>&1 | tail -1
done
echo FINAL_STAGE_DONE
