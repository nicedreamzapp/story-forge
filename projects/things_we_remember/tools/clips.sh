#!/bin/bash
# LTX-2.5 distilled low-ram i2v, 1024x576, one at a time after the stills + picks (lahontan recipe). s07 = a2v on Lily's line.
P=~/Desktop/PROJECTS/story-forge/projects/things_we_remember; cd $P
until [ -f tools/PICKS_READY ]; do sleep 5; done
while pgrep -f "zimage_batch.py $P/stills_jobs" >/dev/null || pgrep -f "make_sfx.py" >/dev/null || pgrep -f "gen_narration.py" >/dev/null; do sleep 5; done
date +%T > tools/t_anim_start
L=~/Desktop/PROJECTS/story-forge/bin/make-ltx25
pk() { python3 -c "import json;print(json.load(open('tools/picks.json'))['$1'])"; }
run() { n=$1; seed=$2; dur=$3; shift 3
  [ -s clips/$n.mp4 ] && return
  src=$(pk $n)
  out=$($L --i2v stills/$src.png --duration $dur --res 1024x576 --low-ram --gb 26 --seed $seed --label twr-$n "$*" 2>&1 | tee -a clips.log | grep -o '→ .*mp4' | tail -1 | sed 's/→ //')
  [ -s "$out" ] && cp "$out" clips/$n.mp4 && echo "CLIP $n ok $(date +%T)" >> clips.log || echo "CLIP $n FAILED" >> clips.log
}
LOOK="cinematic horror film, slow and quiet, natural motivated light stays the same"
run s06 61 5 "the fork resting on the plate in front of the empty chair slowly slides by itself across the plate, nobody touches it, the empty chair stays empty, the camera slowly pushes in toward the empty chair, the warm hanging lamp flickers faintly, $LOOK"
run s05 51 5 "the clear glass slips from the woman's fingers and falls toward the floor, in the dark doorway behind her the shadowy man slowly turns his head down toward the floor, he does not walk, the camera holds still, $LOOK"
run s11 111 5 "the woman stands perfectly still at the dark window, in the window reflection behind her the blurred gentle man slowly tilts his head and smiles, nobody is behind her in the room, the camera very slowly pushes in over her shoulder, $LOOK"
run s08 81 5 "the small boy under the quilt lies still facing the wall, the quilt rises and falls slowly with his breathing, the moonlight stripes stay still, the camera creeps slowly forward toward the bed, $LOOK"
run s04 41 3 "the old woman slowly lifts her eyes from the photograph and looks up at someone off camera, her face still and grave, she blinks once, her mouth stays closed, rain runs down the window behind her, camera locked off, $LOOK"
run s01 11 5 "the golden sun beam slowly drifts, dust motes float and swirl in the light, raindrops begin to run down the window glass, the lace curtain stirs gently, the camera slowly pushes in toward the window, the room is empty, $LOOK"
# s07: Lily speaks, a2v on her picked line (lead-in 0.35 s, padded to 2.8 s)
if [ ! -s clips/s07.mp4 ]; then
  src=$(pk s07)
  out=$($L --i2v stills/$src.png --audio voice/L01_a2v.wav --res 1024x576 --low-ram --gb 26 --seed 71 --label twr-s07 "the little girl looks toward the empty chair beside her and speaks quietly, her mouth moving with the words, calm flat serious face, she blinks, camera locked off, $LOOK" 2>&1 | tee -a clips.log | grep -o '→ .*mp4' | tail -1 | sed 's/→ //')
  [ -s "$out" ] && cp "$out" clips/s07.mp4 && echo "CLIP s07 ok $(date +%T)" >> clips.log || echo "CLIP s07 FAILED" >> clips.log
fi
echo CLIPS_DONE >> clips.log; date +%T > tools/t_anim_end
