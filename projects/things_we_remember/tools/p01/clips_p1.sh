#!/bin/bash
# Part 1 FAST pass: LTX-2.5 distilled low-ram i2v 1024x576, then the 2 a2v lip-syncs (after voices).
P=~/Desktop/PROJECTS/story-forge/projects/things_we_remember; cd $P
until [ -f tools/p01/PICKS_READY ]; do sleep 5; done
L=~/Desktop/PROJECTS/story-forge/bin/make-ltx25; LOG=clips_p01.log
pk() { python3 -c "import json;print(json.load(open('tools/picks_more.json'))['$1'])"; }
sfwait() { until [ "$(curl -s -m5 127.0.0.1:8767/api/status | python3 -c 'import sys,json;print(json.load(sys.stdin).get("jobs_running",0))' 2>/dev/null || echo 0)" = 0 ]; do sleep 20; done; }
run() { n=$1; seed=$2; dur=$3; shift 3
  [ -s clips/$n.mp4 ] && return; sfwait; t0=$(date +%s)
  out=$($L --i2v stills/$(pk $n).png --duration $dur --res 1024x576 --low-ram --gb 26 --seed $seed --label twr-$n "$*" 2>&1 | tee -a $LOG | grep -o '→ .*mp4' | tail -1 | sed 's/→ //')
  [ -s "$out" ] && cp "$out" clips/$n.mp4 && echo "CLIP $n ok $(date +%T)" >> $LOG || echo "CLIP $n FAILED" >> $LOG
  echo "{\"shot\": \"twr_$n\", \"step\": \"i2v_ltx25_lowram_${dur}s\", \"seconds\": $(( $(date +%s) - t0 ))}" >> ~/Desktop/PROJECTS/story-forge/METRICS.jsonl
}
a2v() { n=$1; seed=$2; shift 2
  [ -s clips/$n.mp4 ] && return; sfwait; t0=$(date +%s)
  out=$($L --i2v stills/$(pk $n).png --audio voice/${n}_a2v.wav --res 1024x576 --low-ram --gb 26 --seed $seed --label twr-$n "$*" 2>&1 | tee -a $LOG | grep -o '→ .*mp4' | tail -1 | sed 's/→ //')
  [ -s "$out" ] && cp "$out" clips/$n.mp4 && echo "CLIP $n ok $(date +%T)" >> $LOG || echo "CLIP $n FAILED" >> $LOG
  echo "{\"shot\": \"twr_$n\", \"step\": \"a2v_ltx25_lowram\", \"seconds\": $(( $(date +%s) - t0 ))}" >> ~/Desktop/PROJECTS/story-forge/METRICS.jsonl
}
LOOK="cinematic horror film, slow and quiet, natural motivated light stays the same"
run sh06 3110 4 "the woman lifts the framed photo off the wall and looks at it with a small curious smile, she tilts it toward the lamp, the camera slowly pushes in, $LOOK"
run sh10 3310 4 "the woman's small smile slowly fades, she blinks, her eyes search, confused and uneasy, she does not speak, the camera holds, $LOOK"
run p03 5010 5 "raindrops bead and run slowly down the window glass, the golden sunlight outside fades behind clouds, the lace curtain stirs, the camera holds, $LOOK"
run p04 5020 5 "the station wagon drives slowly along the wet country road under the tall trees in the rain, headlights glowing, the camera pans slowly with it, $LOOK"
run p05 5030 5 "the little girl in the back seat hugs the music box and watches the rain on the window, raindrop shadows move across her face, she blinks, the camera holds, $LOOK"
run p06 5040 5 "the music box lid is open and the tiny ballerina slowly spins on her mirror, the brass cylinder turns, the girl's fingers hold the box still, the camera holds, $LOOK"
run p07 5050 5 "in the rear-view mirror the woman's tired kind eyes glance back toward the back seat and soften with a smile, the wipers sweep the windshield, the camera holds, $LOOK"
run p08 5060 4 "the man sleeps peacefully against the rainy window, his head rocks gently with the road, the wipers sweep, the camera holds, $LOOK"
run pa1 6000 5 "rain falls over the old farmhouse among the tall dark trees, the trees sway slightly, the warm window glows, the camera slowly pushes in, $LOOK"
run pa2 6010 4 "the man wakes, stretches his arms and smiles out at the farmhouse through the wet windshield, the camera holds, $LOOK"
run p10 5070 4 "the old woman holds the screen door open and waits, her face softening into a smile as she sees someone arrive, rain falls in front of the porch, the camera holds, $LOOK"
run p11 5080 5 "the little girl and the old woman hug tightly and rock gently side to side, the old woman's eyes stay closed, smiling, rain falls behind them, the camera holds, $LOOK"
run p12 5090 5 "the woman holding the moving box looks up at the old house and takes a long slow breath, rain falls lightly, the camera slowly pushes in, $LOOK"
run p15 5100 4 "the woman's careful smile holds but her eyes turn sad and glisten, she swallows, she does not speak, the camera very slowly pushes in, $LOOK"
run p16 5110 4 "the man carries the stack of boxes along the hallway past the photographs and out of frame, the camera holds, $LOOK"
run pa3 6020 5 "the woman runs her fingertips slowly along the old wallpaper and breathes in with her eyes half closed, a small sad smile, the camera holds, $LOOK"
run p18 5120 5 "the little girl stands still and looks up at the wall of old photographs, tilting her head, the camera slowly pushes in, $LOOK"
run pa4 6030 5 "the little girl twirls round and round in her new bedroom with her arms out, her braids swinging, laughing, the camera holds, $LOOK"
run p20 5130 5 "the woman unwraps a plate from newspaper and sets it on the counter while the old woman watches quietly from the table, the camera holds, $LOOK"
run p21 5140 4 "the lamp bulb flickers twice and then holds steady, warm light fills the man's face, he smiles, the camera holds, $LOOK"
run pa5 6040 4 "the old woman hands the teacup to her daughter, their fingers touch for a moment and stay, the camera holds, $LOOK"
run pa6 6050 5 "the old woman and the little girl clap their hands together in a playful rhythm, laughing, the camera holds, $LOOK"
run p22 5150 4 "the upstairs landing is still and empty, dust floats in the beam of light, the open door at the end stays dark, the camera slowly pushes in, $LOOK"
run p26 5160 4 "looking down the stairwell, the old woman at the bottom of the stairs stands still and looks up in silence, the camera holds, $LOOK"
run p27 5170 5 "the old woman at the bottom of the stairs looks up for a long moment, says nothing, then slowly turns away and walks out of frame, the camera holds, $LOOK"
run pa7 6060 5 "the woman pushes the old coats aside and her hand stops at the very small coat hanging at the back, she stares at it, the camera slowly pushes in, $LOOK"
run p28 5180 5 "the man hangs raincoats one by one on the old coat rack by the door, rain on the door glass, the camera holds, $LOOK"
run p30 5190 4 "the man's hands hang the small yellow raincoat on the low hook and smooth it down, the camera holds, $LOOK"
run p31 5200 5 "the little girl carefully sets the music box on the shelf and steps back to look at it, smiling, the camera holds, $LOOK"
run pa8 6070 5 "the little girl in the yellow raincoat jumps and stomps in the puddles, splashing water, laughing, rain falling, the camera holds, $LOOK"
run pa9 6080 5 "the old woman stirs the pot slowly and hums, her eyes soft and far away, steam rises, the camera slowly pushes in, $LOOK"
run pa10 6090 4 "the little girl draws with a crayon, her hand moving across the paper, focused, the camera holds, $LOOK"
run pa12 6110 4 "the little girl giggles with the crayon in her hand and shakes her head, looking up at someone, the camera holds, $LOOK"
run pa13 6120 4 "the woman's hands turn the pill organizer slowly, looking at the handwritten labels, the camera holds, $LOOK"
run p33 5210 5 "the woman smooths the yellow quilt, then slowly stops and looks at the wall beside the bed, puzzled, the camera holds, $LOOK"
run p34 5220 5 "the couple eats takeout and laughs quietly together on the moving boxes, the man bumps her shoulder, the camera holds, $LOOK"
run p36 5230 4 "the woman laughs, then her laugh fades as her eyes drift to something across the room, the camera holds, $LOOK"
run p37 5240 5 "the old woman sets the place mats down one by one, carefully, counting under her breath, the camera holds, $LOOK"
run p39 5245 4 "the old woman looks down at the place mats, puzzled, as if she cannot see what is wrong, she blinks slowly, the camera holds, $LOOK"
run pa14 6130 5 "the old woman slowly turns a page of the photo album and smiles softly at it, the lamp glows, the camera slowly pushes in, $LOOK"
run p40 5250 5 "the woman walks slowly into the dark living room carrying two cups of tea, steam rising, the camera holds, $LOOK"
run p42 5260 4 "the woman watches across the room, worried, she does not speak, the camera very slowly pushes in, $LOOK"
run p43 5270 5 "the old woman's reflection in the dark window stays still, rain runs down the glass over it, her eyes far away, the camera very slowly pushes in, $LOOK"
run p44 5265 4 "the woman waits for an answer, her eyes searching, she does not speak, the camera holds, $LOOK"
run p45 5280 5 "the old woman turns from the window and looks at her daughter with an empty lost expression, then slowly smiles politely like meeting a stranger, the camera holds, $LOOK"
run p46 5290 4 "the woman's eyes fill with tears, she swallows and holds it in, the camera holds, $LOOK"
run pa16 6140 5 "the man sleeps, the woman lies awake on her back with her eyes open, listening to the rain, rain shadows move on the ceiling, the camera holds, $LOOK"
run pa17 6150 4 "the woman looks at herself in the mirror, tired, the mirror glass slowly fogs at the edges, the camera holds, $LOOK"
run pa18 6160 5 "the woman leans in the doorway watching the little girl sleep, soft and loving, the girl breathes slowly, the camera holds, $LOOK"
run pa19 6170 4 "the closed music box sits still on the shelf in the moonlight, the blind shadows drift very slightly, the camera very slowly pushes in, $LOOK"
run pa20 6180 4 "the empty dark hallway is perfectly still, nothing moves, the moonlight stays still, the camera holds, $LOOK"
run pa21 6190 4 "the woman walks slowly down the dark stairs with one hand on the rail, away from the camera, the camera holds, $LOOK"
run pa22 6200 3 "rain runs down the rippled glass of the front door, the moonlight flickers through it, the camera holds, $LOOK"
run p47 5300 5 "the dark front hall is still, the yellow raincoat hangs on the low hook, rain sound, the camera very slowly pushes in toward the coat rack, $LOOK"
run p48 5310 5 "the small wet dark blue raincoat hangs beside the yellow one, water drips slowly from its hem onto the floor, drop by drop, nothing else moves, the camera holds, $LOOK"
echo I2V_DONE >> $LOG
until grep -q SCORE_DONE voice/gen_p01.log 2>/dev/null; do sleep 5; done
~/.local/mlx-server/bin/python tools/trailer/a2vwav.py p13:C07:2.5 p24:L07:3.0 p35:T04:2.5 >> $LOG 2>&1
a2v p13 5400 "the woman looks at her mother and says hello softly, her mouth moving with the words, a careful tender smile, she blinks, camera locked off, $LOOK"
a2v p24 5410 "the little girl on the small chair looks up and speaks, her mouth moving with the words, a small frown, she blinks, camera locked off, $LOOK"
a2v p35 5420 "the man looks at his wife and speaks with a tired happy smile, his mouth moving with the words, he blinks, camera locked off, $LOOK"
echo CLIPS_DONE >> $LOG
