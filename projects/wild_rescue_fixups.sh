#!/bin/bash
# Fixups for Wild Rescue, run at block boundary (no queue competition):
# d6 retake — close-up still then S2V re-render.
source /Users/dtribe/Desktop/PROJECTS/story-forge/bin/render_guard.sh
SF=/Users/dtribe/Desktop/PROJECTS/story-forge
ST=$SF/projects/hank_and_doug/wild_rescue/stills
cd "$SF"
guarded_run "still:d6v2" python3 ~/Scripts/flux_t2i.py "Pixar-style 3D animated cartoon bloodhound dog with orange-tan fur, very long floppy brown ears hanging neatly at the sides of his head, big expressive brown eyes, close-up head and shoulders, leaning forward urgently with one front paw reaching toward the camera, mouth open shouting encouragement, raging river rapids and rain behind him, dramatic, high quality 3D cartoon render" --out "$ST/doug_rock_reach_v2.png" --w 832 --h 480 --seed 227
cp -f "$ST/doug_rock_reach_v2.png" /Users/dtribe/Desktop/PROJECTS/AI/ComfyUI/input/
guarded_run "s2v:d6v2" python3 bin/s2v_render.py --image doug_rock_reach_v2.png --audio s2v_d6.wav --prompt "Pixar-style 3D cartoon bloodhound dog shouting encouragement while reaching paw forward urgently, leaning toward camera, rain, determined hopeful expression" --seed 318 --out s2v/wr_d6
echo FIXUPS_DONE
