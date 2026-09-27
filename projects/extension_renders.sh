#!/bin/bash
# Extension renders — bring all five films toward 3 min with REAL animation (no stills ever).
# Auto-runs after post_block3 fixups+music. ~28 clips.
source /Users/dtribe/Desktop/PROJECTS/story-forge/bin/render_guard.sh
SF=/Users/dtribe/Desktop/PROJECTS/story-forge
PROJ=$SF/projects
cd "$SF"
stage_reset "extensions-boot"
v() { gpu_clear; guarded_run "ext:$4" "$SF/bin/make-video" --i2v "$1" "$2" --res 832x480 --duration 5 --seed "$3" --label "$4"; }

S1=$PROJ/hank_and_doug/wild_rescue/stills
v "$S1/hank_talk_close.png" "the bear listening and nodding gently, ears twitching, warm sunny forest, mouth staying closed" 881 wr_hank_react
v "$S1/doug_worried_close.png" "the dog's ears slowly drooping as worry grows, eyes scanning the dark sky, leaves blowing past, mouth closed" 882 wr_doug_react
v "$S1/hank_water_yell.png" "the bear reaching desperately for a passing log in the rapids, water crashing, mouth closed straining" 883 wr_reach_log
v "$S1/doug_rock_reach_v2.png" "the dog bracing against the wind on the rock, fur rippling, determined stare, rain driving past, mouth closed" 884 wr_brace
v "$S1/f04_paw_bump_pixar.png" "the dog and bear laughing together, shoulders shaking with joy, sunbeams brightening, mouth closed smiles" 885 wr_laugh_together

S2=$PROJ/leash_snapped/stills
v "$S2/blonde_park_walk.png" "the woman strolling with the dogs, one dog suddenly stopping to stare at something off screen, her head turning, mouth closed" 886 ls_stare
v "$S2/dogs_bolting.png" "two dogs tumbling over each other mid-chase on the grass, rolling and springing back up" 887 ls_tumble
v "$S2/blonde_sprint.png" "the woman vaulting over a park bench at full sprint, athletic, hair flying, mouth closed" 888 ls_vault
v "$S2/fountain_dog_splash.png" "the soaked dog shaking off a huge spray of water droplets in glittering sunlight" 889 ls_shake
v "$S2/blonde_soaked_wrap.png" "the dogs behind her all lying down in unison, her eyebrows rising in surprise, mouth closed" 890 ls_liedown

S3=$PROJ/red_rock_standoff/stills
v "$S3/w3_wagon.png" "a cowboy diving behind the wagon as splinters fly off the top plank, dust kicking" 891 rr_dive_cover
v "$S3/w4_rear.png" "the rider wheeling the horse around in the dust and galloping away from camera into the sun" 892 rr_wheel_away
v "$S3/w6_weave.png" "a rider leaning low off his saddle at full gallop, reaching down to scoop a fallen hat from the dust" 893 rr_hat_scoop
v "$S3/w2_charge.png" "the dust slowly settling over the empty plain, riders disappearing into the haze in the distance" 894 rr_dust_settle
v "$S3/end_sunset.png" "the two silhouetted figures shaking hands as the sun sinks, dust drifting golden, coats moving in the breeze" 895 rr_handshake_live

M=$PROJ/red_horizon/stills
v "$M/m_a1_outpost.png" "dust devils spinning slowly across the sand in front of the outpost, antenna swaying, moons hanging still" 896 rh_outpost_live
v "$M/m_a2_rover.png" "the rover stopping abruptly, sand spraying from its wheels, dust drifting over it" 897 rh_rover_stop
v "$M/dean_calm.png" "the astronaut turning his head slowly to look at something off screen, visor reflecting the dunes, mouth closed" 898 rh_dean_turn
v "$M/m_a4_sphere.png" "the sand around the sphere beginning to vibrate and trickle away from it in rings, mysterious" 899 rh_sand_rings
v "$M/m_a6_sprint.png" "the astronaut stumbling in the sand, catching himself with one hand and pushing back up into a run" 900 rh_stumble

P=$PROJ/last_treasure/stills
v "$P/p_a1_ship.png" "the ghost ship's tattered sails catching a gust, ship heeling slightly, fog parting around the bow" 901 lt_sails
v "$P/crow_wheel.png" "the captain gripping the wheel hard as the ship lurches, lantern swinging wildly, rain starting, mouth closed" 902 lt_wheel_lurch
v "$P/p_a2_storm.png" "a barrel sliding across the tilting deck, ropes whipping, spray bursting over the rail" 903 lt_barrel
v "$P/p_a3_serpent.png" "the serpent diving back beneath the waves, an enormous splash, the ship rocking in the swell" 904 lt_serpent_dive
v "$P/p_a5_island.png" "birds scattering from the island cliffs as dawn light spreads across the water" 905 lt_birds
v "$P/p_a6_gold_v2.png" "a trickle of gold coins sliding down the treasure mountain, torch flames dancing, glints sparkling" 906 lt_coins

echo EXTENSIONS_DONE
