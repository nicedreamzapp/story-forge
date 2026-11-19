#!/bin/bash
# run_v5_renders.sh — plan_v5 steps 4-8 as one push-button run (prepped 2026-11-18 3 AM, nothing rendered yet).
#   4  Doug colour proof: FLUX.2 klein 9B reference edit of G_forest_v3 against canon/doug_master.png, numeric gate,
#      side-by-side published to the VPS, then STOP until tools/DOUG_APPROVED exists (tools/DOUG_REJECTED = stop).
#   5  stills: the klein edits (G_hunt, I_walkaway, C_bench, D_rollout flipped, H3 lantern unlit), the two new Krea
#      stills (FOX_fence_v5, ROAD_lead_v5, seeds 1101 + 1102 alternate), then the klein edit of ROAD_lead_v5.
#   6  clips (LTX-2.5 i2v, one keyframe clip, one a2v, one K6 Pro), cheapest and most certain first.
#   7  finish: re-mix, picture (finish_v5.py detached), mux, final_audio_gate in place, manifest/sync, 2 fps sheet.
#   8  gates: audio_check + film_qc + continuity_check; reports under final/*_v5*.
# Every heavy step: Song Forge health check (127.0.0.1:8767/api/status, wait while jobs_running > 0), bin/mem-gate,
# a forge_guard lease for the two tools that do not lease themselves (mflux klein, ltx-2-mlx keyframe), and an inline
# pause watcher that SIGSTOPs renders while a customer job runs. Outputs are skipped when they already exist (resumable).
# Usage:  tools/run_v5_renders.sh            # whole run (stops after step 4 for the approval flag)
#         tools/run_v5_renders.sh --check    # CPU only: verify every input and tool, print the time budget, exit
#         tools/run_v5_renders.sh --from 5   # resume from a step (4-8)
#         KLEIN_Q=8 ...                      # 8-bit klein only if bf16 truly cannot fit (Matt's no-quant rule)
#         NO_TRAIN_WAIT=1 ...                # skip the "life-model training still running" wait
set -u
cd "$(dirname "$0")/.." || exit 1
PROJ=$(pwd)
SF=$HOME/Desktop/PROJECTS/story-forge
LTX=$SF/bin/make-ltx25; K6=$SF/bin/make-k6; MEMGATE=$SF/bin/mem-gate
MFLUX=$HOME/mflux-venv/bin/mflux-generate-flux2-edit
LTXCLI=$HOME/Desktop/PROJECTS/ltx-2-mlx/.venv/bin/ltx-2-mlx
PACK=$(ls -d "$HOME"/.cache/huggingface/hub/models--dgrauet--ltx-2.5-mlx/snapshots/* 2>/dev/null | tail -1)
KLEIN_DIR=$HOME/.cache/huggingface/hub/models--black-forest-labs--FLUX.2-klein-9B
PY=/usr/bin/python3                      # has cv2 + numpy + soundfile + librosa (checked 11/18)
QC_PY=$HOME/.local/mlx-server/bin/python  # film_qc + continuity_check
AC_PY=$HOME/chatterbox-env/bin/python     # audio_check
MEMCLI=$HOME/SongForgeM5/mem_client.py
TRAIN_PIDF=$HOME/life-model/runs/full2-20261118-1003/train.pid   # 11/18 10:03 restart of the life-model run
CHAT=m5~07c0f0f4
VPS=root@5.252.55.128; VPS_DIR=/var/www/v; VPS_URL=https://hq.nicedreamzwholesale.com/v
LOG=$PROJ/final/run_v5.log; mkdir -p final stills/v5 clips/v5 clips/v5/strips
FROM=4; CHECK=0
while [ $# -gt 0 ]; do case "$1" in --check) CHECK=1;; --from) FROM=$2; shift;; esac; shift; done
log() { echo "$(date '+%m/%d %H:%M:%S') $*" | tee -a "$LOG"; }
die() { log "STOP: $*"; exit 1; }

# ---------------------------------------------------------------- prompts and settings (the whole brief lives here)
STYLE="Painted oil-on-canvas animation, thick brush strokes stay fixed and do not flicker, the camera is locked off and the background does not slide, no new creatures or objects appear, no lantern, no person, no hands, faces keep their exact shape."
# klein colour edit (plan B1/C1). Two images: the still first, the canon master second. bf16, 4 steps (distilled).
KLEIN_RED="Repaint the dog in the first image as the dog in the second image: a solid russet-red bloodhound, the same red on his back, saddle and ears, no black or tan saddle, same pose, same brushwork, everything else in the first image unchanged"
KLEIN_UNLIT="Same painting, same brushwork, same composition: the brass lantern lies in the ditch water with its flame OUT, dark glass, no glow, no warm light anywhere, the reeds, water and road lit by cold blue moonlight only, everything else unchanged"
KLEIN_STEPS=4; KLEIN_SEEDS="1 2"; KLEIN_GB=45
# Doug measure boxes (full-res pixels, picked by eye 11/18 3 AM; doug_hue_v5.py IMG box s saddlebox). Before numbers:
#   G_forest_v3  box 640 380 1240 670  saddle 800 395 1020 470  -> hue 26.0 deg, saddle dark 60%   (master 20.0 deg, 24%)
#   G_hunt       box 320 330 900 660   saddle 460 340 700 430   -> 26.0 deg, 56%
#   I_walkaway   box 510 450 650 710   saddle 540 460 640 540   -> 24.0 deg, 42%
#   C_bench      box 580 110 780 510   saddle 600 200 740 340   -> 22.0 deg, 33%
#   D_rollout_flip box 364 260 434 380 saddle 374 270 424 320   -> 24.0 deg, 7%
# PASS (step 4 gate) = |hue - 20| <= 6 AND saddle dark <= 30% (well under the 60% before; the master measures 24%).
HUE_TOL=6; DARK_MAX=30
# LTX-2.5 clips: 832x480, 24 fps, distilled i2v, seed 11, --static (locked off, frozen rule 31). Short clips, one
# acting beat per character, subject + camera + secondary motion named. Night half travels camera-LEFT, day half RIGHT.
RES=832x480; SEED=11
P_G_FOREST="Static shot, locked off. Night forest, moonlight. The russet bloodhound walks slowly along the trail toward the fallen log, nose down on the dirt, sniffing, ears swinging with each step; behind the log the young bear's eyes blink once and his head lowers a little; the ferns at the trail edge stir in a light breeze. Nothing else moves. $STYLE"
P_G_HUNT="Static shot, locked off. Night forest trail, moonlight. The russet bloodhound walks slowly to the LEFT along the trail, nose down on the ground, dipping his nose to the dirt three times, tail low; the warm amber glow on the trunks behind him sways slowly from side to side as if a lantern were swinging out of frame. Nothing else moves. $STYLE"
P_I_WALK="Static shot, locked off. Dawn hills, seen from behind. The young bear and the russet bloodhound walk away from the camera up the dirt road, side by side, shrinking slowly into the distance, the bear's shoulders rolling, the dog's tail swinging; the moon above the hills brightens a little. Nothing else moves. $STYLE"
P_FOX="Static shot, locked off. Night forest edge, moonlight. The small red fox hanging by one hind leg from the top wire kicks its free legs and yips, mouth opening; the young bear up on his hind legs hooks both front paws into the wire and pulls the strands apart, the fence sagging and springing; the fox drops free, lands on all fours, shakes once and bolts out of frame to the RIGHT. The bear stays where he is. $STYLE"
P_ROAD="Static shot, locked off. Night forest road, moonlight. The russet bloodhound, small in frame, runs AWAY from the camera down the road toward the bend, paws pounding the dirt, barking back over his shoulder twice; the warm amber glow on the trunks behind him surges forward along the trunks after him. The ditch at the bend stays dark and still. $STYLE"
P_DITCH="Static shot, locked off. Night ditch, moonlight. The brass lantern lies on its side in the ditch water; ripples spread and settle around it, its flame flickers, gutters, shrinks and goes out, and the warm light drains out of the reeds and the water until only cold blue moonlight is left. Nothing else moves. $STYLE"
P_BENCH="Hank the bear in profile on the wagon bench says one word, his jaw opening wide on it and closing; beside him the russet bloodhound's ears flip up and his head turns toward the bear. Static shot, locked off. $STYLE"
P_ROLLOUT="Static shot, locked off, wide clean side profile. The whole team walks to the RIGHT across the frame: the horse, zebra, camel and cow walk in step pulling the red wagon, the big spoked wheels turning, the bear and the russet bloodhound sitting still on the bench, the two giraffes jogging behind and the two elephants walking at the back, all four animals of the team staying in frame, dust drifting behind the wheels, the hills behind not sliding. Thick brush strokes stay fixed, no flicker, the camera does not move or push in."
# keyframe clip (D6): 3.4 s -> 81 frames (8k+1); dev transformer + CFG 3.0 is REQUIRED by ltx-2-mlx keyframe (the
# distilled model hallucinates there); the distilled LoRA for stage 2 is resolved from the pack.
KF_FRAMES=81; KF_GB=82

# ---------------------------------------------------------------- guards
songforge_wait() {
  while :; do
    jr=$(curl -s -m 4 127.0.0.1:8767/api/status | $PY -c "import sys,json; print(json.load(sys.stdin).get('jobs_running',0))" 2>/dev/null || echo 0)
    [ "${jr:-0}" -eq 0 ] && return; log "Song Forge busy (jobs_running=$jr), waiting"; sleep 20; done; }
train_wait() {
  [ "${NO_TRAIN_WAIT:-0}" = 1 ] && return
  while p=$(cat "$TRAIN_PIDF" 2>/dev/null) && [ -n "$p" ] && kill -0 "$p" 2>/dev/null; do
    log "life-model training (pid $p) still holds the memory, waiting 2 min"; sleep 120; done; }
mem_gate() { train_wait; songforge_wait; "$MEMGATE" "$1" || die "mem-gate refused $1"; }
lease() { $PY "$MEMCLI" wait "$1" "$2" --timeout 7200 2>/dev/null | tail -1; }   # prints the lease id ("" = no guard)
unlease() { [ -n "${1:-}" ] && $PY "$MEMCLI" release "$1" >/dev/null 2>&1; true; }
PATS="krea_batch.py|make-k6|ltx-2-mlx|make-ltx25|mflux-generate|film_qc.py|continuity_check.py"
pause_watcher() { paused=0; while :; do
    jr=$(curl -s -m 4 127.0.0.1:8767/api/status | $PY -c "import sys,json; print(json.load(sys.stdin).get('jobs_running',0))" 2>/dev/null || echo 0)
    if [ "${jr:-0}" -gt 0 ] && [ $paused = 0 ]; then pkill -STOP -f "$PATS"; paused=1; log "pause watcher: paused renders (jobs_running=$jr)"; fi
    if [ "${jr:-0}" -eq 0 ] && [ $paused = 1 ]; then pkill -CONT -f "$PATS"; paused=0; log "pause watcher: resumed"; fi
    sleep 10; done; }
strip() { bash tools/strip.sh "$1" "clips/v5/strips/$(basename "$1" .mp4).png" 24 2>/dev/null; }
hue() { $PY tools/doug_hue_v5.py "$@" | tee -a "$LOG"; }
hue_pass() {  # hue_pass IMG box(4) saddle(4) -> 0 when the gate passes
  $PY tools/doug_hue_v5.py "$@" | $PY -c "
import re,sys; s=sys.stdin.read(); h=float(re.search(r'hue\s+(-?[\d.]+)',s).group(1)); d=float(re.search(r'dark fraction (\d+)%',s).group(1))
sys.exit(0 if abs(h-20.0)<=$HUE_TOL and d<=$DARK_MAX else 1)"; }

# ---------------------------------------------------------------- render helpers
klein() {  # klein OUT PROMPT IMG [REF] [extra mflux args...]
  local out=$1 prompt=$2 img=$3; shift 3; local ref=""; [ $# -gt 0 ] && [ -f "$1" ] && { ref=$1; shift; }
  [ -f "$out" ] && { log "skip $out (exists)"; return 0; }
  mem_gate "klein $(basename "$out")"; local lid; lid=$(lease "klein-$(basename "$out" .png)" $KLEIN_GB)
  local q=(); [ -n "${KLEIN_Q:-}" ] && q=(-q "$KLEIN_Q")
  log "klein -> $out (seed ${KSEED:-1}${ref:+, ref $ref})"
  "$MFLUX" --model flux2-klein-9b ${q[@]+"${q[@]}"} --image-paths "$img" ${ref:+"$ref"} --prompt "$prompt" --steps $KLEIN_STEPS --guidance 1.0 --seed "${KSEED:-1}" --output "$out" "$@" >> final/klein_v5.log 2>&1
  local rc=$?; unlease "$lid"; [ $rc -eq 0 ] && [ -f "$out" ] || { log "klein FAILED rc=$rc for $out (tail of final/klein_v5.log):"; tail -3 final/klein_v5.log | tee -a "$LOG"; return 1; }; }
ltx() {  # ltx NAME STILL SECONDS PROMPT [extra make-ltx25 args]  -> clips/v5/NAME.mp4
  local name=$1 still=$2 secs=$3 prompt=$4; shift 4
  [ -f "clips/v5/$name.mp4" ] && { log "skip $name (exists)"; return 0; }
  [ -f "$still" ] || { log "no still for $name ($still), skipped"; return 1; }
  train_wait; songforge_wait; log "ltx25 $name from $still ($secs s)"
  local out; out=$("$LTX" --i2v "$still" --duration "$secs" --res $RES --seed $SEED --label "hd5_$name" --static "$@" "$prompt" 2>>final/clips_v5.log | tail -1)
  local src; src=$(echo "$out" | sed -n 's/.*→ \(.*\)$/\1/p'); [ -n "$src" ] && cp "$src" "clips/v5/$name.mp4"
  log "$name $out"; [ -f "clips/v5/$name.mp4" ] && strip "clips/v5/$name.mp4"; }
keyframe() {  # keyframe NAME START END SECONDS PROMPT -> clips/v5/NAME.mp4 (silent)
  local name=$1 s=$2 e=$3 prompt=$5
  [ -f "clips/v5/$name.mp4" ] && { log "skip $name (exists)"; return 0; }
  [ -f "$s" ] && [ -f "$e" ] || { log "keyframe $name: missing $s or $e, skipped"; return 1; }
  mem_gate "ltx25 keyframe $name"; local lid; lid=$(lease "ltx25-kf-$name" $KF_GB)
  local raw=$HOME/AI/videopipe/outputs/hd5_${name}_$(date +%Y%m%d_%H%M%S)_kf_raw.mp4
  log "ltx25 keyframe $name: $s -> $e, $KF_FRAMES f"
  "$LTXCLI" keyframe --model "$PACK" --start "$s" --end "$e" -p "$prompt" -H 480 -W 832 -f $KF_FRAMES --frame-rate 24 --seed $SEED \
      --dev-transformer transformer-dev.safetensors --cfg-scale 3.0 -o "$raw" >> final/clips_v5.log 2>&1
  local rc=$?; unlease "$lid"
  if [ $rc -eq 0 ] && [ -s "$raw" ]; then ffmpeg -v error -y -i "$raw" -an -c:v copy "clips/v5/$name.mp4" && rm -f "$raw"; strip "clips/v5/$name.mp4"; log "$name done -> clips/v5/$name.mp4"
  else log "keyframe $name FAILED rc=$rc; row 7 falls back to clips/v3/H_ditch.mp4 + light-out ramp (timeline_v5 fallback), no cutout"; return 1; fi; }

# ---------------------------------------------------------------- --check: CPU only
if [ $CHECK = 1 ]; then
  ok=0; miss=0
  for f in "$LTX" "$K6" "$MEMGATE" "$MFLUX" "$LTXCLI" "$PACK/transformer-dev.safetensors" "$PY" "$QC_PY" "$AC_PY" "$MEMCLI" \
           tools/doug_hue_v5.py tools/sbs_v5.py tools/strip.sh tools/krea_batch.py tools/mix_v5.py tools/finish_v5.py tools/write_manifest_v5.py tools/sync_table_v5.py \
           stills/G_forest_v3.png canon/doug_master.png stills/v4/G_hunt.png stills/I_walkaway_s1101.png stills/C_bench_v3.png stills/v5/D_rollout_flip.png stills/v5/H3_ditch_lit.png \
           stills/v5/jobs_v5.json stills/v5/jobs_v5_alt.json voices/L1_hank_rolling.wav clips/v5/J_title_flip.mp4 clips/v3/H_ditch.mp4 clips/D_rollout_k6.mp4 \
           tools/timeline_v5.json tools/cues_v5.json final/mix_v5.wav final/timeline.json manifest.json continuity.json music/theme_2.wav \
           "$SF/pipeline-tools/film_qc.py" "$SF/pipeline-tools/continuity_check.py" "$SF/pipeline-tools/audio_check.py" "$SF/pipeline-tools/final_audio_gate.py"; do
    if [ -e "$f" ]; then ok=$((ok+1)); else miss=$((miss+1)); echo "MISSING $f"; fi; done
  kb=$(du -skL "$KLEIN_DIR"/snapshots/*/transformer "$KLEIN_DIR"/snapshots/*/text_encoder 2>/dev/null | awk '{s+=$1} END{print int(s/1024/1024)}')
  [ "${kb:-0}" -ge 30 ] && echo "klein 9B weights on disk: ${kb} GB" || { echo "MISSING klein 9B weights (${kb:-0} GB under $KLEIN_DIR)"; miss=$((miss+1)); }
  echo "inputs ok=$ok missing=$miss"
  echo "time budget (measured v3/v4 speeds, after the memory frees): step 4 klein x2 seeds ~4 min | step 5 klein x6 ~9 min + Krea x4 ~3 min"
  echo "  step 6: G_forest 4 + G_hunt 5 + I_walk 4 + fox 5 (+5 retry) + road 4 + ditch keyframe 5 + bench a2v ~13 + rollout K6 ~20 = ~65 min"
  echo "  step 7 ~5 min CPU | step 8 ~20 min (film_qc 7, continuity 11, audio 1) | total ~1 h 50 min of machine time + Matt's approval wait"
  exit $miss; fi

# ---------------------------------------------------------------- run
[ -n "$PACK" ] || die "no LTX-2.5 pack"
pause_watcher & PW=$!; trap 'kill $PW 2>/dev/null' EXIT
log "=== run_v5_renders from step $FROM (pid $$)"

if [ "$FROM" -le 4 ]; then
  log "--- step 4: Doug colour proof (klein 9B bf16, G_forest_v3 vs canon master)"
  best=""; for sd in $KLEIN_SEEDS; do
    out=stills/v5/G_forest_red_s$sd.png; KSEED=$sd klein "$out" "$KLEIN_RED" stills/G_forest_v3.png canon/doug_master.png || continue
    if hue_pass "$out" 640 380 1240 670 s 800 395 1020 470; then best=$out; log "step 4 PASS on seed $sd"; break; else log "seed $sd fails the numeric gate"; fi; done
  if [ -z "$best" ]; then
    log "both seeds failed: fallback 1, same edit with DOUG_LORA_V2 at 0.8 (single LoRA, frozen rule 24)"
    out=stills/v5/G_forest_red_lora.png; KSEED=1 klein "$out" "$KLEIN_RED" stills/G_forest_v3.png canon/doug_master.png --lora-paths "$HOME/.hankdoug_seeds/DOUG_LORA_V2.safetensors" --lora-scales 0.8
    [ -f "$out" ] && { hue_pass "$out" 640 380 1240 670 s 800 395 1020 470 && log "LoRA edit PASSES the numeric gate" || log "LoRA edit also fails the numeric gate; publishing it anyway for Matt's eye"; best=$out; }
    [ -f "$best" ] || { best=$(ls stills/v5/G_forest_red_s*.png 2>/dev/null | head -1); }; fi
  [ -f "${best:-}" ] || die "step 4: no klein output at all, read final/klein_v5.log"
  cp "$best" stills/v5/G_forest_red.png
  $PY tools/sbs_v5.py stills/G_forest_v3.png stills/v5/G_forest_red.png canon/doug_master.png stills/v5/doug_sbs_v5.jpg >> "$LOG" 2>&1
  nums=$(hue stills/v5/G_forest_red.png 640 380 1240 670 s 800 395 1020 470)
  name="doug-sbs-v5-$(LC_ALL=C tr -dc a-z0-9 </dev/urandom | head -c 12).jpg"
  if scp -q -o ConnectTimeout=20 stills/v5/doug_sbs_v5.jpg "$VPS:$VPS_DIR/$name"; then url="$VPS_URL/$name"; else url="(scp failed; file is stills/v5/doug_sbs_v5.jpg on the M5)"; fi
  log "step 4 side-by-side: $url | after: $nums"
  chat-send "$CHAT" "Doug colour test done (from $best). Side-by-side: $url. After: $nums. Before: hue 26.0, saddle dark 60%; master 20.0. Pass = hue within 6 deg of 20 and saddle under 30%. Waiting on tools/DOUG_APPROVED to run steps 5-8 (touch tools/DOUG_REJECTED to stop)." >/dev/null 2>&1
  bash "$HOME/.claude/imessage-send.sh" "Doug colour test is up: $url
Hue $(echo "$nums" | sed -n 's/.*hue *\([-0-9.]*\) deg.*/\1/p') deg (target 20), saddle dark $(echo "$nums" | sed -n 's/.*fraction \([0-9]*\)%.*/\1/p')% (was 60%). Reply in the trailer chat: approve or redo." >/dev/null 2>&1
  log "waiting for tools/DOUG_APPROVED"
  while [ ! -f tools/DOUG_APPROVED ]; do [ -f tools/DOUG_REJECTED ] && die "Doug edit rejected (tools/DOUG_REJECTED); nothing after step 4 ran"; sleep 30; done
  log "approved, continuing"
fi

if [ "$FROM" -le 5 ]; then
  log "--- step 5: stills"
  [ -f stills/v5/G_forest_red.png ] || die "step 5 needs stills/v5/G_forest_red.png from step 4"
  KSEED=1 klein stills/v5/G_hunt_red.png "$KLEIN_RED" stills/v4/G_hunt.png canon/doug_master.png && hue stills/v5/G_hunt_red.png 320 330 900 660 s 460 340 700 430
  KSEED=1 klein stills/v5/I_walkaway_red.png "$KLEIN_RED" stills/I_walkaway_s1101.png canon/doug_master.png && hue stills/v5/I_walkaway_red.png 510 450 650 710 s 540 460 640 540
  KSEED=1 klein stills/v5/C_bench_red.png "$KLEIN_RED" stills/C_bench_v3.png canon/doug_master.png && hue stills/v5/C_bench_red.png 580 110 780 510 s 600 200 740 340
  [ -f stills/v5/D_rollout_flip.png ] || ffmpeg -v error -y -i stills/D_rollout_s1102.png -vf hflip stills/v5/D_rollout_flip.png
  KSEED=1 klein stills/v5/D_rollout_right_red.png "$KLEIN_RED" stills/v5/D_rollout_flip.png canon/doug_master.png && hue stills/v5/D_rollout_right_red.png 364 260 434 380 s 374 270 424 320
  KSEED=1 klein stills/v5/H3_unlit.png "$KLEIN_UNLIT" stills/v5/H3_ditch_lit.png
  # the two new Krea stills (krea_batch gates itself: Song Forge + mem-gate + lease), main seed then the alternate seed
  train_wait; songforge_wait; log "Krea 2: FOX_fence_v5 + ROAD_lead_v5 (seed 1101), then the 1102 alternates"
  $PY tools/krea_batch.py stills/v5/jobs_v5.json >> final/krea_v5.log 2>&1 || log "krea main batch rc=$? (see final/krea_v5.log)"
  $PY tools/krea_batch.py stills/v5/jobs_v5_alt.json >> final/krea_v5.log 2>&1 || log "krea alt batch rc=$?"
  [ -f stills/v5/ROAD_lead_v5.png ] && KSEED=1 klein stills/v5/ROAD_lead_v5_red.png "$KLEIN_RED" stills/v5/ROAD_lead_v5.png canon/doug_master.png
  log "step 5 done: $(ls stills/v5/*.png | wc -l | tr -d ' ') pngs in stills/v5 (pick: FOX_fence_v5.png / ROAD_lead_v5.png are the defaults; copy a _s1102 over them to swap)"
fi

if [ "$FROM" -le 6 ]; then
  log "--- step 6: clips (order: cheapest and most certain first)"
  ltx G_forest_red   stills/v5/G_forest_red.png     4   "$P_G_FOREST"                       # D1 row 3 (Doug approaches the log as the still faces)
  ltx G_hunt_red     stills/v5/G_hunt_red.png       5   "$P_G_HUNT"                         # D2 row 1, camera-left
  ltx I_walkaway_red stills/v5/I_walkaway_red.png   3.7 "$P_I_WALK"                         # D3 row 9, tail-away
  ltx FOX_fence_v5   stills/v5/FOX_fence_v5.png     4.2 "$P_FOX" || { SEED=12 ltx FOX_fence_v5 stills/v5/FOX_fence_v5.png 4.2 "$P_FOX"; }   # D4 row 4 (+1 retry seed)
  ltx ROAD_lead_v5   stills/v5/ROAD_lead_v5_red.png 4   "$P_ROAD"                           # D5 row 6, tail-away toward the bend
  keyframe H3_ditch_key stills/v5/H3_ditch_lit.png stills/v5/H3_unlit.png 3.4 "$P_DITCH"   # D6 row 7, lit -> unlit
  # D8 row 10 bench, a2v driven by Hank's "Rolling." wav (make-ltx25 pads the wav to the clip length; no --static on a2v)
  if [ ! -f clips/v5/C_bench_red.mp4 ] && [ -f stills/v5/C_bench_red.png ]; then
    train_wait; songforge_wait; log "ltx25 a2v C_bench_red"
    out=$("$LTX" --i2v stills/v5/C_bench_red.png --audio voices/L1_hank_rolling.wav --res $RES --seed $SEED --label hd5_C_bench_red "$P_BENCH" 2>>final/clips_v5.log | tail -1)
    src=$(echo "$out" | sed -n 's/.*→ \(.*\)$/\1/p'); [ -n "$src" ] && cp "$src" clips/v5/C_bench_red.mp4; log "C_bench_red $out"; [ -f clips/v5/C_bench_red.mp4 ] && strip clips/v5/C_bench_red.mp4; fi
  # D9 row 11 rollout, K6 Pro (self-gated: Song Forge wait + mem-gate + lease), 5 s, team walks camera-RIGHT
  if [ ! -f clips/v5/D_rollout_right.mp4 ] && [ -f stills/v5/D_rollout_right_red.png ]; then
    train_wait; log "K6 Pro D_rollout_right (about 20 min)"
    out=$("$K6" --i2v stills/v5/D_rollout_right_red.png --duration 5 --res $RES --seed $SEED --static --label hd5_D_rollout_right "$P_ROLLOUT" 2>>final/clips_v5.log | tail -1)
    src=$(echo "$out" | sed -n 's/.*→ \(.*\)$/\1/p'); [ -n "$src" ] && cp "$src" clips/v5/D_rollout_right.mp4; log "D_rollout_right $out"; [ -f clips/v5/D_rollout_right.mp4 ] && strip clips/v5/D_rollout_right.mp4
    [ -f clips/v5/D_rollout_right.mp4 ] || log "K6 fallback available by hand: ffmpeg hflip of clips/D_rollout_k6.mp4, 0.0-4.3 s, bench row +0.7 s (plan D9)"; fi
  log "step 6 done: $(ls clips/v5/*.mp4 | wc -l | tr -d ' ') clips in clips/v5, strips in clips/v5/strips (eye pass + cue re-pick for rows 1/3/6/7/9/11 before trusting the mix)"
fi

if [ "$FROM" -le 7 ]; then
  log "--- step 7: finish"
  $AC_PY tools/mix_v5.py >> final/render_v5.log 2>&1 || die "mix_v5 failed (final/render_v5.log)"
  nohup $PY tools/finish_v5.py --out final/picture_v5.mp4 >> final/render_v5.log 2>&1 & FP=$!; wait $FP || die "finish_v5 failed (final/render_v5.log)"
  FILM=final/hank_doug_wild_rescue_trailer_v5.mp4
  ffmpeg -v error -y -i final/picture_v5.mp4 -i final/mix_v5.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -shortest "$FILM" || die "mux failed"
  $PY "$SF/pipeline-tools/final_audio_gate.py" "$FILM" --in-place --lufs -14.5 --tp -1.9 --report final/final_audio_gate_v5.md >> final/render_v5.log 2>&1 || log "final_audio_gate rc=$? (final/final_audio_gate_v5.md)"
  $PY tools/write_manifest_v5.py >> "$LOG" 2>&1; $PY tools/sync_table_v5.py >> "$LOG" 2>&1
  ffmpeg -v error -y -i "$FILM" -vf "fps=2,scale=320:-1,tile=12x10" -frames:v 1 final/contact_sheet_v5_2fps.jpg
  log "step 7 done: $FILM ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$FILM") s), sheet final/contact_sheet_v5_2fps.jpg"
fi

if [ "$FROM" -le 8 ]; then
  log "--- step 8: gates"
  FILM=$PROJ/final/hank_doug_wild_rescue_trailer_v5.mp4; [ -f "$FILM" ] || die "no v5 film to gate"
  train_wait; songforge_wait; "$MEMGATE" "gates v5" || die "mem-gate refused the gates"
  ( cd "$SF" && "$AC_PY" pipeline-tools/audio_check.py "$FILM" --score "$PROJ/music/theme_2.wav" --timeline "$PROJ/final/timeline.json" --narration "$PROJ/narration.json" > "$PROJ/final/audio_check_v5_report.md" 2> "$PROJ/final/audio_check_v5.err" ) & AC=$!
  ( cd "$SF" && "$QC_PY" pipeline-tools/film_qc.py "$FILM" "$PROJ/manifest_v5.json" --report "$PROJ/final/film_qc_v5_report.md" > "$PROJ/final/film_qc_v5.log" 2>&1 ); log "film_qc exit $?"
  ( cd "$SF" && "$QC_PY" pipeline-tools/continuity_check.py "$PROJ" "$FILM" > "$PROJ/final/continuity_v5.log" 2>&1 ); log "continuity_check exit $?"
  wait $AC   # 11/18 12:30: a bare wait also waited on the pause watcher (an endless loop) and hung step 8 forever
  summary="gates v5 done: film_qc $(grep -ci 'fail' final/film_qc_v5_report.md 2>/dev/null) lines mention fail, continuity $(grep -ci 'FAIL' final/continuity_v5.log 2>/dev/null) FAIL lines, audio_check written. Reports: final/film_qc_v5_report.md, final/continuity_v5.log, final/audio_check_v5_report.md, final/final_audio_gate_v5.md. Read them in full before anything is called checked."
  log "$summary"; chat-send "$CHAT" "$summary" >/dev/null 2>&1
fi
log "=== run_v5_renders finished"
