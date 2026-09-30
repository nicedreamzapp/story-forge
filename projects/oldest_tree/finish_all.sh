#!/bin/bash
# after the shot queue: lip-sync talk shots, MMAudio foley, full assembly, film QC
P=~/Desktop/PROJECTS/story-forge/projects/oldest_tree
cd $P
while pgrep -f run_film.sh >/dev/null; do sleep 30; done
echo "[finish] queue done $(date +%H:%M)"
# re-run any shot that came out HELD / UNBUILT (up to two passes)
for pass in 1 2; do
  MISSING=$(python3 -c "
import json,os
d=json.load(open('film_shots.json'))
print(' '.join('--only '+s['id'] for s in d['shots'] if not os.path.exists('clips/'+s['id']+('_talk' if s.get('talk') else '_final')+'.mp4') and not (s.get('talk') and os.path.exists('stills/LOCKED_'+s['id']+'.png'))))")
  [ -z "$MISSING" ] && break
  echo "[finish] pass $pass re-running: $MISSING"
  (cd ~/Desktop/PROJECTS/story-forge && ~/.local/mlx-server/bin/python bin/forge-shot projects/oldest_tree/film_shots.json $MISSING >> projects/oldest_tree/wip/forge_film_retry.log 2>&1)
done
[ -f clips/s2_talk_talk.mp4 ] || ./make_talk.sh s2_talk voices/gp_g1.wav "an old man with a white beard in an olive-green jacket talking warmly to his granddaughter in a foggy redwood forest, gentle natural head movement, speaking" > wip/talk_s2.log 2>&1
[ -f clips/s7_talk_talk.mp4 ] || ./make_talk.sh s7_talk voices/gp_g2.wav "an old man with a white beard at night in moonlight, tears in his eyes, recognizing his granddaughter and softly saying her name, slight head movement" > wip/talk_s7.log 2>&1
echo "[finish] talk done $(date +%H:%M)"
until [ -f score_full.wav ]; do sleep 30; done
~/.local/mlx-server/bin/python make_sfx.py > wip/sfx.log 2>&1
echo "[finish] sfx done $(date +%H:%M)"
python3 assemble_film.py > wip/assemble.log 2>&1
echo "[finish] assembled $(date +%H:%M)"
python3 - <<'PY'
import json
t=json.load(open('final/timeline.json'))
sc=[]
names=t['order']
for i,n in enumerate(names):
    sc.append({"name":n,"start":round(t['starts'][i]+0.3,2),"end":round(t['starts'][i]+t['lens'][i]-0.3,2)})
lines=[]
for n,txt in [("s2_talk","Your grandmother used to say these trees were listening."),("s7_talk","Lily, you found me.")]:
    if n in names: lines.append({"t":round(t['starts'][names.index(n)]+0.4,2),"speaker":"grandpa","text":txt})
json.dump({"characters":{"grandpa":"75-year-old man with short white hair, trimmed white beard, olive-green waxed jacket","girl":"10-year-old girl with a long dark brown braid and a mustard-yellow raincoat"},"scenes":sc,"lines":lines},open('final/film_manifest.json','w'),indent=1)
PY
~/.local/mlx-server/bin/python ~/Desktop/PROJECTS/story-forge/pipeline-tools/film_qc.py final/The_Oldest_Tree.mp4 final/film_manifest.json --report final/film_qc_report.md > wip/film_qc.log 2>&1
echo "[finish] QC exit $? $(date +%H:%M)"
