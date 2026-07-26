#!/bin/bash
# Post-block3: lengthening action renders (real animation, no stills) for films 1,2,3
# then final scores with lyric gate. Auto-runs after block3.
source /Users/dtribe/Desktop/PROJECTS/story-forge/bin/render_guard.sh
SF=/Users/dtribe/Desktop/PROJECTS/story-forge
PROJ=$SF/projects
cd "$SF"
stage_reset "fixups-boot"
v() { gpu_clear; guarded_run "act:$4" "$SF/bin/make-video" --i2v "$1" "$2" --res 832x480 --duration 5 --seed "$3" --label "$4"; }

# film 1 — more chase/storm coverage
S1=$PROJ/hank_and_doug/wild_rescue/stills
v "$S1/hank_water_yell.png" "the bear being swept sideways by churning rapids, water crashing over him, rain pouring, no speech, mouth closed" 861 wr_swept
v "$S1/doug_run_storm.png" "the dog leaping over a fallen branch at full sprint, rain streaking, mud flying, dynamic chase, mouth closed" 862 wr_sprint2
v "$S1/storm_title.png" "trees whipping violently in storm wind below boiling clouds, lightning flash, leaves torn away" 863 wr_windstorm
# film 2 — squirrel, park life, puppies (real motion replacements)
S2=$PROJ/leash_snapped/stills
v "$S2/squirrel_path.png" "the squirrel suddenly darts across the path and up a tree, quick nimble motion" 864 ls_squirrel
v "$S2/park_title.png" "gentle breeze through the park trees, fountain water sparkling and splashing, birds flying through frame" 865 ls_parklife
v "$S2/dogs_angelic_row.png" "five puppies sitting in a row, tails wagging, heads tilting curiously in unison, ears flopping" 866 ls_angelic
# film 3 — more battle coverage
S3=$PROJ/red_rock_standoff/stills
v "$S3/w2_charge.png" "the riders thundering past camera left to right, dust exploding, hooves pounding" 867 rr_charge2
v "$S3/w8_stampede.png" "cattle surging forward in panic, dust boiling up, a wagon wheel spinning past" 868 rr_stampede2

v "$S1/bridge_wide.png" "river water flowing steadily under the log bridge, leaves drifting down, branches swaying gently, sunlight shimmering on moving water" 869 wr_bridge_live
v "$S1/sunset_river.png" "calm river current drifting at sunset, sparkles moving on the water surface, soft clouds slowly crossing the sky" 870 wr_sunset_live
S2B=$PROJ/leash_snapped/stills
v "$S2B/park_title.png" "fountain water spraying and splashing, tree branches swaying in the breeze, a bird flying across the park" 871 ls_title_live
echo FIXUP_ACTIONS_DONE
stage_reset "fixups->music"
bash "$SF/projects/render_music2.sh"
echo POST_BLOCK3_DONE
