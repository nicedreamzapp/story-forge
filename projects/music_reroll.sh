#!/bin/bash
# Re-roll ONLY missing scores. Forces instrumental via explicit lyrics="[instrumental]" tag
# (empty lyrics is why ACE invented vocals). Up to 5 tries each; gate on transcribed words.
SF_API=http://127.0.0.1:8767
PROJ=/Users/dtribe/Desktop/PROJECTS/story-forge/projects
WHISPER="/opt/homebrew/bin/whisper-cli -m $HOME/whisper-models/ggml-small.en.bin"

gen() { # gen <dir> <name> <style>
  local dir="$1" name="$2" style="$3" id resp w try
  for try in 1 2 3 4 5; do
    resp=$(curl -s -m 15 -X POST $SF_API/api/song -H "Content-Type: application/json" \
      -d "{\"style\":\"$style\",\"lyrics\":\"[instrumental]\",\"voice\":\"none\"}")
    id=$(python3 -c "import json,sys; print(json.loads(sys.argv[1]).get('id',''))" "$resp" 2>/dev/null)
    [ -z "$id" ] && { echo "[reroll] $name queue fail (try $try)"; sleep 5; continue; }
    echo "[reroll] $name try $try ($id)"
    for i in $(seq 1 100); do
      sleep 12
      st=$(curl -s -m 10 $SF_API/api/song/$id | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status','?'),d.get('audio',''))" 2>/dev/null)
      case "$st" in
        done*) audio="${st#done }"; curl -s -m 60 "$SF_API$audio" -o "$dir/score_$name.wav" 2>/dev/null || cp "$audio" "$dir/score_$name.wav" 2>/dev/null
          curl -s -m 10 -X DELETE $SF_API/api/song/$id >/dev/null
          w=$($WHISPER -f "$dir/score_$name.wav" -np -nt 2>/dev/null | python3 -c "import sys,re; t=sys.stdin.read(); t=re.sub(r'\(.*?\)|\[.*?\]|♪','',t); print(len(re.findall(r'[A-Za-z]{2,}',t)))")
          if [ "${w:-99}" -le 3 ]; then echo "[reroll] CLEAN: $name ($w words)"; return 0
          else echo "[reroll] still vocal: $name ($w words) — retry"; rm -f "$dir/score_$name.wav"; fi
          break;;
        error*) echo "[reroll] err $name"; break;;
      esac
    done
  done
  echo "[reroll] FALLBACK: $name -> reuse a clean instrumental"
  cp "$PROJ/red_horizon/score_red_horizon.wav" "$dir/score_$name.wav"
}

gen "$PROJ/hank_and_doug/wild_rescue" wild_rescue "pure orchestral instrumental film score, adventurous heroic strings and brass and timpani, no voice, no choir, cinematic, Pixar adventure"
gen "$PROJ/leash_snapped" leash_snapped "pure instrumental funk groove, brass stabs walking bass drums organ, no voice, no singing, upbeat comedy bed"
gen "$PROJ/red_rock_standoff" red_rock "pure instrumental spaghetti western score, lone twang electric guitar, mariachi trumpet, whistling melody, galloping percussion, no voice, Morricone"
echo REROLL_DONE
