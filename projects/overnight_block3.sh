#!/bin/bash
# Block 3 — films 4+5 talking pipeline (voices -> talk stills -> 12 S2V shots).
# Auto-starts after block 2b. QC pauses: stills get a 10-min QC window before S2V begins.
source /Users/dtribe/Desktop/PROJECTS/story-forge/bin/render_guard.sh
SF=/Users/dtribe/Desktop/PROJECTS/story-forge
cd "$SF"
stage_reset "block3-boot"

echo "=== B3.0 voices (films 4+5) ==="
~/chatterbox-env/bin/python "$SF/projects/red_horizon/gen_voices.py" || echo "rh voices FAILED" >> /tmp/render_failures.txt
~/chatterbox-env/bin/python "$SF/projects/last_treasure/gen_voices.py" || echo "lt voices FAILED" >> /tmp/render_failures.txt

echo "=== B3.1 talk stills ==="
M=$SF/projects/red_horizon/stills; P=$SF/projects/last_treasure/stills
DEAN="photorealistic rugged male astronaut in his 40s, buzz cut, stubble, orange EVA spacesuit with helmet visor OPEN showing his full face clearly, Mars"
CROW="painterly cinematic fantasy oil-painting style, grizzled old pirate captain, gray beard, tricorn hat, scarred weathered face, lantern light"
g() { guarded_run "still:$(basename $2)" python3 ~/Scripts/flux_t2i.py "$1" --out "$2" --w 832 --h 480 --seed "$3"; }
g "$DEAN, close-up head and shoulders, calm focused expression, mouth open mid-sentence, dusty Mars plain behind" "$M/dean_calm.png" 641
g "$DEAN, close-up, alarmed urgent wide eyes, mouth open exclaiming, dust storm glow behind" "$M/dean_alarm.png" 642
g "$DEAN, close-up, awestruck wonder expression, soft blue glow reflecting on his face, mouth open speaking softly" "$M/dean_wonder.png" 643
g "$CROW, close-up at the ship's wheel, determined expression, mouth open mid-sentence, stormy night sea behind" "$P/crow_wheel.png" 651
g "$CROW, close-up, yelling into the storm, rain streaming off his hat, mouth wide open, lightning behind" "$P/crow_storm.png" 652
g "$CROW, close-up, awestruck soft expression, golden treasure light on his face, mouth open speaking gently" "$P/crow_awe.png" 653
echo B3_STILLS_DONE
echo "QC WINDOW: 10 minutes before S2V begins"; sleep 600

echo "=== B3.2 films 4+5 S2V (12 shots) ==="
IN=/Users/dtribe/Desktop/PROJECTS/AI/ComfyUI/input
cp -f "$M"/dean_*.png "$P"/crow_*.png "$IN/" 2>/dev/null
r() { guarded_run "$5" python3 bin/s2v_render.py --image "$1" --audio "$2" --prompt "$3" --seed "$4" --out "s2v/$5"; }
r dean_calm.png   s2v_m1.wav "rugged astronaut speaking calmly to his helmet camera, slight head movement, Mars wind dust drifting" 901 rh_m1
r dean_alarm.png  s2v_m2.wav "astronaut speaking with rising alarm, eyes widening, glancing aside and back" 902 rh_m2
r dean_wonder.png s2v_m3.wav "astronaut speaking in hushed wonder, blue glow flickering on his face" 903 rh_m3
r dean_alarm.png  s2v_m4.wav "astronaut speaking urgently, jaw set, wind whipping dust past him" 904 rh_m4
r dean_alarm.png  s2v_m5.wav "astronaut shouting while breaking into a run, bouncing motion, storm closing in" 905 rh_m5
r dean_wonder.png s2v_m6.wav "astronaut speaking softly with awe, gentle head shake of disbelief, blue pulsing light" 906 rh_m6
r crow_wheel.png  s2v_p1.wav "old pirate captain speaking with gravelly determination at the wheel, ship rocking gently, rain starting" 911 lt_p1
r crow_storm.png  s2v_p2.wav "pirate captain yelling commands into the storm, rain streaming, ship pitching" 912 lt_p2
r crow_storm.png  s2v_p3.wav "pirate captain shouting in alarm, eyes wide with dread, lightning flashing" 913 lt_p3
r crow_storm.png  s2v_p4.wav "pirate captain roaring orders, gripping the wheel hard, spray flying" 914 lt_p4
r crow_wheel.png  s2v_p5.wav "pirate captain speaking in soft awe, mist parting, dawn light growing on his face" 915 lt_p5
r crow_awe.png    s2v_p6.wav "old pirate captain speaking warmly and wistfully, golden light dancing on his face, gentle smile forming" 916 lt_p6
echo "=== B3.3 gold cave retake ==="
stage_reset "s2v->i2v-fixup"
g "painterly fantasy oil-painting, interior of a dark sea cave, enormous glittering mountain of gold coins and goblets and jewels lit by flickering torchlight, treasure chests overflowing, warm golden glow" "$P/p_a6_gold_v2.png" 654
cd "$SF" && guarded_run "act:lt_a6v2" ./bin/make-video --i2v "$P/p_a6_gold_v2.png" "torchlight flickering across the mountain of gold, coins trickling down the pile, warm glow dancing" --res 832x480 --duration 5 --seed 856 --label lt_a6v2
W=$SF/projects/red_rock_standoff/stills
guarded_run "act:rr_w1v2" ./bin/make-video --i2v "$W/w1_street.png" "a single tumbleweed rolling slowly across the empty dirt street, dust haze drifting, heat shimmer, the distant figure standing still, 1860s frontier town, no vehicles" --res 832x480 --duration 5 --seed 871 --label rr_w1v2
echo MASTER_BLOCK3_DONE
