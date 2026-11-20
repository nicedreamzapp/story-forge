#!/bin/bash
# score each line as soon as its 6 takes exist, then write any lip-sync block audio that is now complete
P=~/Desktop/PROJECTS/story-forge/projects/lahontan_returns; cd $P
for id in $(python3 -c "import json;print(*json.load(open('voice/lines.json')))"); do
  until [ $(ls voice/pieces/${id}_*.wav 2>/dev/null | wc -l) -ge 6 ]; do sleep 5; done
  ~/chatterbox-env/bin/python voice/score.py $id 2>/dev/null | grep PICK >> voice/picks.log
  ~/chatterbox-env/bin/python tools/build_tl.py --blocks-only >> voice/picks.log 2>&1
done
date +%T > tools/t_voice_end; echo SCORE_DONE >> voice/picks.log
