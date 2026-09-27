#!/bin/bash
# render_actions.sh — block2 B2.4: generate remaining film stills on M5 (Flux),
# then render ALL action-critical shots on M5 via make-video (lightx2v 4-step, ~4 min each).
# The mini (slow node) handles only its 6 ambient shots independently.
source /Users/dtribe/Desktop/PROJECTS/story-forge/bin/render_guard.sh
SF=/Users/dtribe/Desktop/PROJECTS/story-forge
PROJ=$SF/projects
P60="1960s western movie still, slightly faded Technicolor, soft vintage film look"
MARS="photorealistic cinematic sci-fi, Mars surface, orange-red dust, harsh sunlight"
PIR="painterly cinematic fantasy oil-painting style, dramatic lantern and moonlight"

g() { guarded_run "still:$(basename $2)" python3 ~/Scripts/flux_t2i.py "$1" --out "$2" --w 832 --h 480 --seed "$3"; }
v() { cd "$SF" && guarded_run "act:$4" ./bin/make-video --i2v "$1" "$2" --res 832x480 --duration 5 --seed "$3" --label "$4"; }

W=$PROJ/red_rock_standoff/stills; M=$PROJ/red_horizon/stills; P=$PROJ/last_treasure/stills
mkdir -p "$W" "$M" "$P"

# ---- blonde actions FIRST ----
B=$PROJ/leash_snapped/stills
v "$B/dogs_bolting.png" "five dogs bolting forward and scattering across the park grass, leashes whipping loose behind them, chaotic energy" 821 ls_dogs_bolt
v "$B/hotdog_cart_dog.png" "the beagle snatching the string of hot dogs and bolting away from the cart, the vendor flailing his arms" 822 ls_hotdog
v "$B/fountain_dog_splash.png" "the golden retriever crashing into the fountain water, a huge splash erupting, water drops flying everywhere" 823 ls_fountain
v "$B/dogpark_gate_pack.png" "a dozen excited dogs streaming out through the gate running toward the camera, tails wagging, dust kicking up" 824 ls_gate_pack
v "$B/blonde_mud_dive.png" "the woman scrambling forward through the mud reaching desperately ahead, mud splashing" 825 ls_dive
echo FILM12_ACTIONS_DONE

# ---- stills ----
g "wide dusty frontier town main street at high noon, wooden buildings, tumbleweed, $P60" "$W/w1_street.png" 611
g "mounted riders charging across open plains kicking up huge dust clouds, $P60" "$W/w2_charge.png" 612
g "cowboys crouched behind an overturned wagon firing rifles, muzzle smoke, $P60" "$W/w3_wagon.png" 613
g "a horse rearing dramatically with rider silhouetted against dust and sun, $P60" "$W/w4_rear.png" 614
g "saloon windows with gun smoke drifting out, splintered wood, chaos, $P60" "$W/w5_saloon.png" 615
g "warriors on horseback weaving between wooden buildings at speed, dynamic, $P60" "$W/w6_weave.png" 616
g "a cowboy hat flying through the air as a rider tumbles into thick dust, motion blur, $P60" "$W/w7_fall.png" 617
g "cattle stampeding through the main street, dust everywhere, people diving aside, $P60" "$W/w8_stampede.png" 618
g "small Mars research outpost with twin moons in pink sky, $MARS" "$M/m_a1_outpost.png" 621
g "six-wheeled rover crossing red sand dunes leaving tracks, $MARS" "$M/m_a2_rover.png" 622
g "colossal wall of dust storm on the Martian horizon approaching, ominous, $MARS" "$M/m_a3_stormwall.png" 623
g "astronaut gloved hand brushing red sand off a perfectly smooth metallic sphere half buried, close-up, $MARS" "$M/m_a4_sphere.png" 624
g "smooth metallic sphere half-buried in red sand glowing with a faint blue pulse, $MARS" "$M/m_a5_glow.png" 625
g "astronaut in orange EVA suit sprinting across dunes with massive dust storm wall right behind him, $MARS" "$M/m_a6_sprint.png" 626
g "heavy airlock door with red dust swirling violently outside the closing gap, $MARS" "$M/m_a7_airlock.png" 627
g "metallic sphere sitting on a lab table, room lights flickering, eerie, $MARS" "$M/m_a8_lab.png" 628
g "ghost ship with tattered sails cutting through moonlit fog on dark ocean, $PIR" "$P/p_a1_ship.png" 631
g "enormous storm waves crashing over a wooden ship deck, rigging straining, $PIR" "$P/p_a2_storm.png" 632
g "massive sea serpent coils rising from dark stormy water beside a ship, lightning, $PIR" "$P/p_a3_serpent.png" 633
g "wooden ship threading between a towering natural rock arch in a storm, $PIR" "$P/p_a4_arch.png" 634
g "mysterious island with jagged peaks revealed through clearing mist, dawn light, $PIR" "$P/p_a5_island.png" 635
g "torchlit sea cave filled with mountains of gold treasure, glittering, $PIR" "$P/p_a6_gold.png" 636
g "ship sailing toward brilliant sunrise on calm golden sea, hopeful, $PIR" "$P/p_a7_sunrise.png" 637
echo STILLS_B24_DONE

# ---- western ----
v "$W/w1_street.png" "tumbleweed rolling down the dusty street, heat shimmer, flags fluttering" 831 rr_w1
v "$W/w2_charge.png" "riders galloping hard across the plain, dust clouds billowing behind them" 832 rr_w2
v "$W/w3_wagon.png" "rifle muzzle flashes and smoke, cowboys ducking and firing from behind the wagon" 833 rr_w3
v "$W/w4_rear.png" "the horse rearing high, rider holding on, dust swirling around them" 834 rr_w4
v "$W/w5_saloon.png" "gun smoke drifting from the windows, splinters flying, curtains whipping" 835 rr_w5
v "$W/w6_weave.png" "warriors on horseback weaving fast between the buildings, dust kicking up" 836 rr_w6
v "$W/w7_fall.png" "the hat tumbling through the air, dust cloud erupting where the rider fell" 837 rr_w7
v "$W/w8_stampede.png" "cattle stampeding through the street, dust everywhere, chaos" 838 rr_w8

# ---- mars ----
v "$M/m_a1_outpost.png" "slow drift toward the outpost, dust devils crossing, moons hanging in the sky" 841 rh_a1
v "$M/m_a2_rover.png" "the rover rolling steadily across the dunes, wheels kicking up red dust" 842 rh_a2
v "$M/m_a3_stormwall.png" "the colossal dust storm wall churning and advancing, lightning inside it" 843 rh_a3
v "$M/m_a4_sphere.png" "the gloved hand gently brushing sand away from the metallic sphere" 844 rh_a4
v "$M/m_a5_glow.png" "the sphere pulsing with slow blue light, sand trickling off its surface" 845 rh_a5
v "$M/m_a6_sprint.png" "the astronaut sprinting hard, storm wall surging closer behind him" 846 rh_a6
v "$M/m_a7_airlock.png" "the airlock door sliding shut as red dust blasts through the narrowing gap" 847 rh_a7
v "$M/m_a8_lab.png" "the sphere pulsing on the table, room lights flickering in rhythm" 848 rh_a8

# ---- pirate ----
v "$P/p_a1_ship.png" "the ghost ship gliding through moonlit fog, tattered sails swaying, water rippling" 851 lt_a1
v "$P/p_a2_storm.png" "huge waves crashing over the deck, rigging whipping in the wind, spray flying" 852 lt_a2
v "$P/p_a3_serpent.png" "the sea serpent coils rising higher from the water, lightning flashing" 853 lt_a3
v "$P/p_a4_arch.png" "the ship surging through the rock arch, waves exploding against the stone" 854 lt_a4
v "$P/p_a5_island.png" "mist clearing to reveal the jagged island, birds circling the peaks" 855 lt_a5
v "$P/p_a6_gold.png" "torchlight flickering across mountains of gold, coins trickling down a pile" 856 lt_a6
v "$P/p_a7_sunrise.png" "the ship sailing into the golden sunrise, calm waves, sails full" 857 lt_a7

echo ACTIONS_M5_DONE
