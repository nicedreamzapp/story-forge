#!/bin/bash
# All 16 Circus Train lines. Idempotent — skips existing wavs.
CV="$HOME/chatterbox-env/bin/python $HOME/Desktop/PROJECTS/story-forge/pipeline-tools/character_voice.py"
V="$HOME/Desktop/PROJECTS/story-forge/projects/circus_train/voices"
gen() { # id char line [exaggeration]
  [ -f "$V/$1.wav" ] && { echo "skip $1"; return; }
  $CV --character "$2" --line "$3" ${4:+--exaggeration $4} --out "$V/$1.wav" && echo "done $1"
}
gen L01_hank    hank   "Doug. The fish are winning again."
gen L02_doug    doug   "That's cause they practice, Hank."
gen L03_bird    voiceA "HELP! The circus train broke down! Everybody's stuck in the sun!" 0.7
gen L04_doug    doug   "Circus train? Hank, we're rolling."
gen L05_hank    hank   "Whole train's cooking out here."
gen L06_doug    doug   "Easy everybody! The Wild Rescue's here!"
gen L07_doug    doug   "Pin's jammed tight."
gen L08_ellie   voiceB "I can't... it's too heavy..." 0.6
gen L09_doug    doug   "Ellie? It's Doug. One push, girl. I'll count you down."
gen L10_doug    doug   "Three... two... one... PUSH!"
gen L11_hank    hank   "Doors don't argue with bears."
gen L12_ellie   voiceB "Best. Rescue. Ever!" 0.7
gen L13_doug    doug   "Turtle called dibs on the tank an hour ago."
gen L14_doug    doug   "Anybody, anywhere, any trouble at all..."
gen L15_hank    hank   "...the Wild Rescue rolls."
gen L16_bird    voiceA "Can I get a hat like this?" 0.6
echo ALL_VOICES_DONE
