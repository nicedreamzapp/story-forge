#!/bin/bash
# Block 2c — resume after second crash: last Mars clip, pirate actions, music, then block 3.
source /Users/dtribe/Desktop/PROJECTS/story-forge/bin/render_guard.sh
SF=/Users/dtribe/Desktop/PROJECTS/story-forge
PROJ=$SF/projects
cd "$SF"
stage_reset "block2c-boot"
v() { gpu_clear; guarded_run "act:$4" "$SF/bin/make-video" --i2v "$1" "$2" --res 832x480 --duration 5 --seed "$3" --label "$4"; }
M=$PROJ/red_horizon/stills; P=$PROJ/last_treasure/stills
v "$M/m_a8_lab.png" "the sphere pulsing on the table, room lights flickering in rhythm" 848 rh_a8
v "$P/p_a1_ship.png" "the ghost ship gliding through moonlit fog, tattered sails swaying, water rippling" 851 lt_a1
v "$P/p_a2_storm.png" "huge waves crashing over the deck, rigging whipping in the wind, spray flying" 852 lt_a2
v "$P/p_a3_serpent.png" "the sea serpent coils rising higher from the water, lightning flashing" 853 lt_a3
v "$P/p_a4_arch.png" "the ship surging through the rock arch, waves exploding against the stone" 854 lt_a4
v "$P/p_a5_island.png" "mist clearing to reveal the jagged island, birds circling the peaks" 855 lt_a5
v "$P/p_a7_sunrise.png" "the ship sailing into the golden sunrise, calm waves, sails full" 857 lt_a7
echo ACTIONS_M5_DONE
stage_reset "actions->music"
bash "$SF/projects/render_music.sh"
bash /Users/dtribe/Desktop/PROJECTS/story-forge/projects/overnight_block3.sh >> /tmp/block3.log 2>&1
echo MASTER_BLOCK2C_DONE
