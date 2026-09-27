#!/bin/bash
# Overnight master — block 1: blonde stills (Flux) + cartoon S2V chain. GPU-serial via ComfyUI queue.
source /Users/dtribe/Desktop/PROJECTS/story-forge/bin/render_guard.sh
cd /Users/dtribe/Desktop/PROJECTS/story-forge/projects/leash_snapped/stills
B="photorealistic beautiful blonde woman, long wavy blonde hair, striking blue-green eyes, orange knit headband, fitted athletic top and leggings"
PR="photorealistic, shot on 35mm, natural morning light, shallow depth of field"
f() { guarded_run "still:$2" python3 /Users/dtribe/Scripts/flux_t2i.py "$1" --out "$2" --w 832 --h 480 --seed "$3"; }

f "$B, close-up, shocked wide-eyed expression, mouth open in disbelief, holding up the frayed end of a snapped dog leash, sunny park, $PR" blonde_shock_close.png 403
f "$B, full body sprinting hard across park grass, athletic running form, yelling, hair flying, urgent, $PR" blonde_sprint.png 404
f "$B, standing at the edge of a large park fountain, water splashing onto her, exasperated yelling expression, arms out, $PR" blonde_fountain_yell.png 405
f "$B, dramatic horizontal dive through the air toward a muddy patch of grass, arms outstretched reaching, action freeze, $PR" blonde_mud_dive.png 406
f "$B, medium close-up, soaked clothes and mud streaks, amused triumphant smirk talking to camera, golden afternoon park light, five dogs blurred sitting behind her, $PR" blonde_soaked_wrap.png 407
f "$B, lying on muddy grass laughing and hugging a squirming muddy terrier, triumphant, joyful, $PR" blonde_mud_catch.png 415
f "alert gray squirrel standing upright in the middle of a sunny park path, close low angle, $PR" squirrel_path.png 408
f "five dogs of different breeds bolting in different directions on park grass, leashes flying loose, dynamic chaotic action, motion blur, $PR" dogs_bolting.png 409
f "a beagle leaping up at a hot dog vendor cart in a park stealing a string of hot dogs, vendor flinching back, comedic action, $PR" hotdog_cart_dog.png 410
f "a large golden retriever mid-cannonball leap into a park fountain, huge water splash, comedic, $PR" fountain_dog_splash.png 411
f "a dog park gate bursting open with a dozen excited dogs streaming out onto the grass, dynamic, low angle, $PR" dogpark_gate_pack.png 412
f "five dogs of different breeds sitting in a perfect row on park grass looking innocently at camera, comedic angelic composition, golden light, $PR" dogs_angelic_row.png 413
f "wide establishing shot of a beautiful sunny city park in golden morning light, paths and fountain and big trees, $PR" park_title.png 414
echo BLONDE_STILLS_DONE

bash /Users/dtribe/Desktop/PROJECTS/story-forge/projects/hank_and_doug/wild_rescue/render_s2v_chain.sh
echo MASTER_BLOCK1_DONE
