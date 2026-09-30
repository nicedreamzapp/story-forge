#!/bin/bash
# finish2: one forge-shot process PER SHOT (a hang only loses that shot), two rounds,
# then lip-sync, foley, assembly, film QC.
P=~/Desktop/PROJECTS/story-forge/projects/oldest_tree
SF=~/Desktop/PROJECTS/story-forge
cd $P
missing() { python3 -c "
import json,os
d=json.load(open('film_shots.json'))
print(' '.join(s['id'] for s in d['shots'] if not s.get('cut') and not os.path.exists('clips/'+s['id']+'_final.mp4') and not (s.get('talk') and os.path.exists('stills/LOCKED_'+s['id']+'.png'))))"; }
for round in 1 2; do
  for id in $(missing); do
    echo "[finish2] round $round $id $(date +%H:%M)"
    (cd $SF && ~/.local/mlx-server/bin/python bin/forge-shot projects/oldest_tree/film_shots.json --only $id >> projects/oldest_tree/wip/forge_finish2.log 2>&1)
  done
done
echo "[finish2] still missing after 2 rounds: $(missing)"
[ -f clips/s2_talk_talk.mp4 ] || ./make_talk.sh s2_talk voices/gp_g1.wav "an old man with a white beard in an olive-green jacket talking warmly to his granddaughter in a foggy redwood forest, gentle natural head movement, speaking" > wip/talk_s2.log 2>&1
[ -f stills/LOCKED_s7_talk.png ] && [ ! -f clips/s7_talk_talk.mp4 ] && ./make_talk.sh s7_talk voices/gp_g2.wav "an old man with a white beard at night in moonlight, tears in his eyes, recognizing his granddaughter and softly saying her name, slight head movement" > wip/talk_s7.log 2>&1
echo "[finish2] talk done $(date +%H:%M)"
~/.local/mlx-server/bin/python make_sfx.py > wip/sfx.log 2>&1
echo "[finish2] sfx done $(date +%H:%M) $(ls sfx | wc -l) files"
python3 assemble_film.py > wip/assemble.log 2>&1
echo "[finish2] assembled $(date +%H:%M) $(tail -1 wip/assemble.log)"
