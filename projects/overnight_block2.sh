#!/bin/bash
# Block 2 — auto-starts when block 1 (cartoon S2V chain) finishes.
# Order is strictly GPU-serial: voices (tiny) -> western stills -> blonde S2V chain ->
# western S2V -> all action shots -> music last. Guard wraps everything.
source /Users/dtribe/Desktop/PROJECTS/story-forge/bin/render_guard.sh
SF=/Users/dtribe/Desktop/PROJECTS/story-forge
cd "$SF"

echo "=== B2.-1 wild rescue fixups ==="
bash /Users/dtribe/Desktop/PROJECTS/story-forge/projects/wild_rescue_fixups.sh

echo "=== B2.0 western voices (ChatterBox, GPU gap) ==="
~/chatterbox-env/bin/python "$SF/projects/red_rock_standoff/gen_voices.py" || echo "western voices FAILED" >> /tmp/render_failures.txt

echo "=== B2.1 western stills (Flux) ==="
cd "$SF/projects/red_rock_standoff" && mkdir -p stills && cd stills
P60="1960s western movie still, slightly faded Technicolor, soft vintage film look"
guarded_run "w:sheriff" python3 ~/Scripts/flux_t2i.py "weathered cowboy sheriff close-up, gray stubble, worn leather hat and duster, dusty frontier town behind, mouth open mid-sentence, squinting, $P60" --out sheriff_close.png --w 832 --h 480 --seed 601
guarded_run "w:chief" python3 ~/Scripts/flux_t2i.py "Native American war chief close-up, traditional feathered headdress and war paint, dignified stern face, mouth open mid-sentence, plains behind, $P60" --out chief_close.png --w 832 --h 480 --seed 602
guarded_run "w:title" python3 ~/Scripts/flux_t2i.py "1960s western movie title background, painted-poster style wide shot of a dusty frontier town main street at high noon, dramatic sky, $P60" --out title_60s.png --w 832 --h 480 --seed 603
guarded_run "w:sunset" python3 ~/Scripts/flux_t2i.py "two silhouetted figures shaking hands on a dusty street at sunset, 1960s western movie final shot, warm faded color, $P60" --out end_sunset.png --w 832 --h 480 --seed 604


echo "=== B2.1.6 cartoon action shots on M5 (make-video, critical path) ==="
cd "$SF"
A1=projects/hank_and_doug/wild_rescue/mini_actions; mkdir -p "$A1"
mvid() { guarded_run "act:$3" ./bin/make-video --i2v "$1" "$2" --res 832x480 --duration 5 --seed "$4" --label "$3"; }
ST1=projects/hank_and_doug/wild_rescue/stills
mvid "$ST1/log_snap_close.png" "the cracked wooden log bridge splintering apart in the middle, wood fibers snapping, rain falling hard, pieces giving way" wr_log_snap 811
mvid "projects/hank_and_doug/stills/eager_doug3/DOUG_EAGER_canonical_403.png" "the cartoon dog sprinting at full speed toward the camera through the forest, ears flying back, paws pounding, splashing through puddles" wr_sprint 812
mvid "$ST1/doug_midair_leap.png" "the cartoon dog flying through the air over raging river rapids, water spraying up, dramatic leap, rain streaking" wr_leap 813
mvid "$ST1/f04_paw_bump_pixar.png" "the dog and bear gently bump paws, warm sunlight rays breaking through trees, leaves drifting down softly" wr_paw_bump 814
# collect newest outputs into the film dir
ls -t output/*.mp4 2>/dev/null | head -8 || true

echo "=== B2.2 blonde S2V chain (12 talking shots) ==="
bash "$SF/projects/leash_snapped/render_s2v_chain.sh"

echo "=== B2.3 western S2V (4 lines) ==="
cd "$SF" && IN=/Users/dtribe/Desktop/PROJECTS/AI/ComfyUI/input
cp -f projects/red_rock_standoff/stills/*.png "$IN/" 2>/dev/null
cp -f projects/red_rock_standoff/voices/s2v_*.wav "$IN/" 2>/dev/null
guarded_run rr_s1 python3 bin/s2v_render.py --image sheriff_close.png --audio s2v_rs1.wav --prompt "weathered cowboy sheriff speaking slowly and gravely, steely calm, wind moving his coat, dusty street, 1960s western film" --seed 701 --out s2v/rr_s1
guarded_run rr_c1 python3 bin/s2v_render.py --image chief_close.png --audio s2v_rc1.wav --prompt "Native war chief speaking with solemn intensity, head high, feathers moving in wind, 1960s western film" --seed 702 --out s2v/rr_c1 --length 81
guarded_run rr_s2 python3 bin/s2v_render.py --image sheriff_close.png --audio s2v_rs2.wav --prompt "weathered sheriff speaking quietly, exhausted relief, dust settling behind him, 1960s western film" --seed 703 --out s2v/rr_s2
guarded_run rr_c2 python3 bin/s2v_render.py --image chief_close.png --audio s2v_rc2.wav --prompt "war chief speaking final solemn words, slow respectful nod, sunset light, 1960s western film" --seed 704 --out s2v/rr_c2

echo "=== B2.4 action shots (Wan i2v/t2v) ==="
bash "$SF/projects/render_actions.sh"

echo "=== B2.5 music (ACE-Step, GPU now clear) ==="
bash "$SF/projects/render_music.sh"

echo MASTER_BLOCK2_DONE
