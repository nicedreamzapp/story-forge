#!/bin/bash
# sfx_v5.sh — plan_v5 A1: the 3 hissy clips re-made with MMAudio large 44k (make-sfx waits on Song Forge jobs and takes a mem lease).
# Snore and chipmunk squeak are NOT made: Matt chose ending A (no button) on 11/18 1:57 AM.
cd "$(dirname "$0")/.."; SFX=~/Desktop/PROJECTS/story-forge/bin/make-sfx; LOG=sfx/v5/batch.log
NEG="music, speech, voices, talking, alarm, siren, beep, electronic tone, hiss, static, white noise, wind"
gen() { [ -f "sfx/v5/raw/$1.wav" ] || $SFX "$2" --seconds $3 --out "sfx/v5/raw/$1.wav" --seed $4 --negative "$NEG" >> $LOG 2>&1; echo "$(date +%T) $1 rc=$?" >> $LOG; }
gen splash_slosh "a metal lantern drops into a shallow muddy ditch, one short heavy splash then a gentle water slosh and small ripples lapping, close, quiet night" 3 511
gen flame_hiss "a small oil lantern flame dying in water, a short soft sizzle and fizz that fades out, close, quiet" 2 512
gen water_pour "a thick stream of water pouring and splashing into a stone drain, steady pouring water, close" 3 513
echo "$(date +%T) sfx v5 done" >> $LOG
