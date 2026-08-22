#!/bin/bash
# Block 2b — post-panic resume with stage_reset between every model switch.
source /Users/dtribe/Desktop/PROJECTS/story-forge/bin/render_guard.sh
SF=/Users/dtribe/Desktop/PROJECTS/story-forge
cd "$SF"
stage_reset "boot"

echo "=== B2b.1 cartoon actions (i2v models only) ==="
A1=$SF/projects/hank_and_doug/wild_rescue/mini_actions; mkdir -p "$A1"
mvid() { guarded_run "act:$3" ./bin/make-video --i2v "$1" "$2" --res 832x480 --duration 5 --seed "$4" --label "$3"; }
ST1=projects/hank_and_doug/wild_rescue/stills
mvid "$ST1/log_snap_close.png" "the cracked wooden log bridge splintering apart in the middle, wood fibers snapping, rain falling hard, pieces giving way" wr_log_snap 811
mvid "projects/hank_and_doug/stills/eager_doug3/DOUG_EAGER_canonical_403.png" "the cartoon dog sprinting at full speed toward the camera through the forest, ears flying back, paws pounding, splashing through puddles" wr_sprint 812
mvid "$ST1/doug_midair_leap.png" "the cartoon dog flying through the air over raging river rapids, water spraying up, dramatic leap, rain streaking" wr_leap 813
mvid "$ST1/f04_paw_bump_pixar.png" "the dog and bear gently bump paws, warm sunlight rays breaking through trees, leaves drifting down softly" wr_paw_bump 814
cp -f "$SF"/output/wr_*.mp4 "$A1/" 2>/dev/null || true
stage_reset "i2v->s2v"

echo "=== B2b.2 blonde S2V chain ==="
bash "$SF/projects/leash_snapped/render_s2v_chain.sh"

echo "=== B2b.3 western S2V ==="
IN=/Users/dtribe/Desktop/PROJECTS/AI/ComfyUI/input
cp -f "$SF"/projects/red_rock_standoff/stills/*.png "$IN/" 2>/dev/null
guarded_run rr_s1 python3 bin/s2v_render.py --image sheriff_close.png --audio s2v_rs1.wav --prompt "weathered cowboy sheriff speaking slowly and gravely, steely calm, wind moving his coat, dusty street, 1960s western film" --seed 701 --out s2v/rr_s1
guarded_run rr_c1 python3 bin/s2v_render.py --image chief_close.png --audio s2v_rc1.wav --prompt "Native war chief speaking with solemn intensity, head high, feathers moving in wind, 1960s western film" --seed 702 --out s2v/rr_c1 --length 81
guarded_run rr_s2 python3 bin/s2v_render.py --image sheriff_close.png --audio s2v_rs2.wav --prompt "weathered sheriff speaking quietly, exhausted relief, dust settling behind him, 1960s western film" --seed 703 --out s2v/rr_s2
guarded_run rr_c2 python3 bin/s2v_render.py --image chief_close.png --audio s2v_rc2.wav --prompt "war chief speaking final solemn words, slow respectful nod, sunset light, 1960s western film" --seed 704 --out s2v/rr_c2
stage_reset "s2v->mixed-actions"

echo "=== B2b.4 remaining stills+actions ==="
bash "$SF/projects/render_actions.sh"
stage_reset "actions->music"

echo "=== B2b.5 music ==="
bash "$SF/projects/render_music.sh"
echo MASTER_BLOCK2B_DONE
