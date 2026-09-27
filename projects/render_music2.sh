#!/bin/bash
# render_music.sh — 5 film scores via Song Forge/ACE-Step. STRICTLY one at a time,
# only runs when ComfyUI queue is empty (block 2 sequencing guarantees this).
# Downloads each wav into its project, then DELETES it from the Song Forge library
# (library = Matt's music only).
set -u
SF_API=http://127.0.0.1:8767
PROJ=/Users/dtribe/Desktop/PROJECTS/story-forge/projects

# ensure Song Forge is up
curl -s -m 5 $SF_API/api/status >/dev/null 2>&1 || {
  echo "[music] Song Forge down — starting"
  cd "/Users/dtribe/Desktop/PROJECTS/Song Forge" && nohup python3 forge_server.py > /tmp/songforge_overnight.log 2>&1 &
  sleep 20
}

gen() { # gen <out_dir> <name> <idea> <style>
  local dir="$1" name="$2" idea="$3" style="$4"
  local id resp status audio
  resp=$(curl -s -m 15 -X POST $SF_API/api/song -H "Content-Type: application/json" \
    -d "{\"idea\":\"$idea\",\"style\":\"$style\"}")
  id=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['id'])" "$resp") || { echo "[music] queue failed: $name"; return 1; }
  echo "[music] $name queued ($id)"
  for i in $(seq 1 120); do
    sleep 15
    status=$(curl -s -m 10 $SF_API/api/song/$id | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('status','?'), d.get('audio',''))" 2>/dev/null) || continue
    case "$status" in
      done*) audio="${status#done }"
        curl -s -m 60 "$SF_API$audio" -o "$dir/score_$name.wav" 2>/dev/null || cp "$audio" "$dir/score_$name.wav" 2>/dev/null
        [ -s "$dir/score_$name.wav" ] && echo "[music] DONE: $name" || echo "[music] download FAILED: $name"
        # LYRIC GATE: strip (annotations)/[brackets]/♪, count remaining words; >3 words = lyrics
        t=$(/opt/homebrew/bin/whisper-cli -m ~/whisper-models/ggml-small.en.bin -f "$dir/score_$name.wav" -np -nt 2>/dev/null)
        w=$(python3 -c "import sys,re; t=sys.argv[1]; t=re.sub(r'\(.*?\)|\[.*?\]|♪','',t); print(len(re.findall(r'[A-Za-z]{2,}',t)))" "$t")
        if [ "${w:-0}" -gt 3 ]; then echo "[music] LYRICS DETECTED in $name ($w words) — deleted"; rm -f "$dir/score_$name.wav"; fi

        curl -s -m 10 -X DELETE $SF_API/api/song/$id >/dev/null  # library stays Matt's music only
        return 0;;
      error*) echo "[music] FAILED: $name"; return 1;;
    esac
  done
  echo "[music] TIMEOUT: $name"; return 1
}

gen "$PROJ/hank_and_doug/wild_rescue" wild_rescue \
  "adventurous heroic orchestral score for an animated kids film, playful warm opening, building storm danger, soaring triumphant rescue finale" \
  "INSTRUMENTAL ONLY, NO VOCALS, NO LYRICS, NO SINGING, NO HUMMING, NO CHOIR, NO RAP, pure instrumental, cinematic orchestral adventure, Pixar soundtrack, 3 minutes 30 seconds"
gen "$PROJ/leash_snapped" leash_snapped \
  "upbeat funky comedy chase score for a dog-walking disaster story, energetic brass stabs, walking bassline, playful percussion, feel-good ending" \
  "INSTRUMENTAL ONLY, NO VOCALS, NO LYRICS, NO SINGING, NO HUMMING, NO CHOIR, NO RAP, pure instrumental, funk pop comedy score, upbeat, 3 minutes 30 seconds"
gen "$PROJ/red_rock_standoff" red_rock \
  "1960s spaghetti western film score, lone twangy electric guitar, mariachi trumpet, galloping rhythm, tense standoff passages, epic showdown crescendo" \
  "INSTRUMENTAL ONLY, NO VOCALS, NO LYRICS, NO SINGING, NO HUMMING, NO CHOIR, NO RAP, pure instrumental, vintage 1960s western soundtrack, Ennio Morricone style, 3 minutes"
gen "$PROJ/red_horizon" red_horizon \
  "tense ambient sci-fi score, deep synth drones, slow pulse like a heartbeat, wonder and dread, building to a sprint sequence, mysterious resolving end" \
  "INSTRUMENTAL ONLY, NO VOCALS, NO LYRICS, NO SINGING, NO HUMMING, NO CHOIR, NO RAP, pure instrumental, cinematic sci-fi ambient score, 3 minutes"
gen "$PROJ/last_treasure" last_treasure \
  "dark seafaring orchestral adventure, low male-choir-like swells without words, storm strings, heroic brass for the island reveal, bittersweet warm ending" \
  "INSTRUMENTAL ONLY, NO VOCALS, NO LYRICS, NO SINGING, NO HUMMING, NO CHOIR, NO RAP, pure instrumental, pirate adventure film score, orchestral, 3 minutes"
echo MUSIC_ALL_DONE
