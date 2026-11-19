#!/bin/bash
# run_v5_doug_all.sh — Matt 11/18 9:47 AM: "Just make sure he's the same color." Doug solid russet in EVERY row.
# Audit (3 frames per timeline_v5 row, 11/18 ~9:55 AM): Doug is in rows 1,2,3,5,6,8,9,10,11. run_v5_renders.sh already
# recolours 1,3,6,9,10,11. Row 8 (N_hi) already reads solid russet (no saddle; still measures hue 22, same gate as the
# approved proof) and is left alone so the "Hi." lip-sync timing does not move. Rows 4,7,12-16 have no Doug (the title
# wagon is an empty silhouette). Extra rows done here: 2 (lookback, saddle 51% dark) and 5 (watch, saddle 27% dark).
# Coordination: the simplest correct one. Wait for run_v5_renders.sh (pid 18445) to EXIT (its own finish + gates
# included), then klein-edit the two v4 stills, render the two clips the way v4 made them (LTX-2.5 i2v, 4 s, seed 11,
# the v4 prompts + v5 STYLE/--static), add them as replace_with on rows 2 and 5, and re-run run_v5_renders.sh --from 7
# (the same finish + gates, same guards). Then the Doug gate: continuity_check doug_colour FAIL lines must be 0 and
# the big-Doug rows must measure russet on the final film; only then publish to the VPS and text Matt.
# Usage: nohup tools/run_v5_doug_all.sh > tools/run_v5_doug_all.log 2>&1 &      WAIT_PID=NNN to wait on another pid.
set -u
cd "$(dirname "$0")/.." || exit 1
PROJ=$(pwd)
SF=$HOME/Desktop/PROJECTS/story-forge
LTX=$SF/bin/make-ltx25; MEMGATE=$SF/bin/mem-gate
MFLUX=$HOME/mflux-venv/bin/mflux-generate-flux2-edit
PY=/usr/bin/python3
MEMCLI=$HOME/SongForgeM5/mem_client.py
SF_ENV="${STORY_FORGE_ENV:-$HOME/.config/story-forge/publish.env}"; if [ -f "$SF_ENV" ]; then . "$SF_ENV"; fi; CHAT="${SF_CHAT:-}"
SF_ENV="${STORY_FORGE_ENV:-$HOME/.config/story-forge/publish.env}"; if [ -f "$SF_ENV" ]; then . "$SF_ENV"; fi; VPS="${SF_VPS:?set SF_VPS (user@host) in $SF_ENV}"; VPS_DIR="${SF_VPS_DIR:?set SF_VPS_DIR in $SF_ENV}"; VPS_URL="${SF_VPS_URL:?set SF_VPS_URL in $SF_ENV}"
WAIT_PID=${WAIT_PID:-18445}; MAIN_LOG=tools/run_v5_renders.log
K6=$SF/bin/make-k6
TRAIN_RUN=$HOME/life-model/runs/full2-20261118-1003; TRAIN_PIDF=$TRAIN_RUN/train.pid   # stopped 10:55 (Matt's OK) so the renders fit; restarted at the end
# 10:56 restart: the main run died at step 7 (mix_v5 on a python without librosa, fixed in run_v5_renders.sh) and its
# G_forest_red (LTX) + D_rollout_right (K6, memory refused while training held 60 GB) never landed: both are rendered here first.
LOG=$PROJ/final/run_v5_doug_all.log; mkdir -p final stills/v5 clips/v5 clips/v5/strips
log() { echo "$(date '+%m/%d %H:%M:%S') $*" | tee -a "$LOG"; }
die() { log "STOP: $*"; chat-send "$CHAT" "run_v5_doug_all STOP: $*" >/dev/null 2>&1; exit 1; }

# ---------------------------------------------------------------- the brief (same words as run_v5_renders.sh)
STYLE="Painted oil-on-canvas animation, thick brush strokes stay fixed and do not flicker, the camera is locked off and the background does not slide, no new creatures or objects appear, no lantern, no person, no hands, faces keep their exact shape."
KLEIN_RED="Repaint the dog in the first image as the dog in the second image: a solid russet-red bloodhound, the same red on his back, saddle and ears, no black or tan saddle, same pose, same brushwork, everything else in the first image unchanged"
KLEIN_STEPS=4; KLEIN_GB=45; HUE_TOL=6; DARK_MAX=30
RES=832x480; SEED=11
# v4 prompts for the two rows (tools/run_v4_clips.sh), "the bloodhound" -> "the russet bloodhound" as the v5 prompts say
P_LOOKBACK="Static shot, locked off. Night forest close shot. The warm glow on the trunks behind the russet bloodhound swings hard across them and across his face at about one second; at that moment his head turns back over his shoulder toward the light, ears going back, eyes low; then he holds, breathing. $STYLE"
P_WATCH="Static shot, locked off. Night forest close shot. The russet bloodhound lying low in the ferns watches toward the right; his ears lift, his eyes soften, and his tail begins to wag against the leaves behind him, thumping three times; the ferns stir. $STYLE"
P_G_FOREST="Static shot, locked off. Night forest, moonlight. The russet bloodhound walks slowly along the trail toward the fallen log, nose down on the dirt, sniffing, ears swinging with each step; behind the log the young bear's eyes blink once and his head lowers a little; the ferns at the trail edge stir in a light breeze. Nothing else moves. $STYLE"
P_ROLLOUT="Static shot, locked off, wide clean side profile. The whole team walks to the RIGHT across the frame: the horse, zebra, camel and cow walk in step pulling the red wagon, the big spoked wheels turning, the bear and the russet bloodhound sitting still on the bench, the two giraffes jogging behind and the two elephants walking at the back, all four animals of the team staying in frame, dust drifting behind the wheels, the hills behind not sliding. Thick brush strokes stay fixed, no flicker, the camera does not move or push in."
# measure boxes (full-res 1344x768, picked by eye 11/18 ~10 AM, drawn and checked). Before: close_glow saddle 51% dark, watch 27%.
BOX_LOOK="100 50 1344 768 s 700 420 1200 600"
BOX_WATCH="250 30 1344 760 s 630 380 1130 540"

# ---------------------------------------------------------------- guards (copied from run_v5_renders.sh)
songforge_wait() {
  while :; do
    jr=$(curl -s -m 4 127.0.0.1:8767/api/status | $PY -c "import sys,json; print(json.load(sys.stdin).get('jobs_running',0))" 2>/dev/null || echo 0)
    [ "${jr:-0}" -eq 0 ] && return; log "Song Forge busy (jobs_running=$jr), waiting"; sleep 20; done; }
train_wait() {
  [ "${NO_TRAIN_WAIT:-0}" = 1 ] && return
  while p=$(cat "$TRAIN_PIDF" 2>/dev/null) && [ -n "$p" ] && kill -0 "$p" 2>/dev/null; do
    log "life-model training (pid $p) still holds the memory, waiting 2 min"; sleep 120; done; }
mem_gate() { train_wait; songforge_wait; "$MEMGATE" "$1" || die "mem-gate refused $1"; }
lease() { $PY "$MEMCLI" wait "$1" "$2" --timeout 7200 2>/dev/null | tail -1; }
unlease() { [ -n "${1:-}" ] && $PY "$MEMCLI" release "$1" >/dev/null 2>&1; true; }
PATS="krea_batch.py|make-k6|ltx-2-mlx|make-ltx25|mflux-generate|film_qc.py|continuity_check.py"
pause_watcher() { paused=0; while :; do
    jr=$(curl -s -m 4 127.0.0.1:8767/api/status | $PY -c "import sys,json; print(json.load(sys.stdin).get('jobs_running',0))" 2>/dev/null || echo 0)
    if [ "${jr:-0}" -gt 0 ] && [ $paused = 0 ]; then pkill -STOP -f "$PATS"; paused=1; log "pause watcher: paused renders (jobs_running=$jr)"; fi
    if [ "${jr:-0}" -eq 0 ] && [ $paused = 1 ]; then pkill -CONT -f "$PATS"; paused=0; log "pause watcher: resumed"; fi
    sleep 10; done; }
strip() { bash tools/strip.sh "$1" "clips/v5/strips/$(basename "$1" .mp4).png" 24 2>/dev/null; }
hue() { $PY tools/doug_hue_v5.py "$@" | tee -a "$LOG"; }
hue_ok() { $PY tools/doug_hue_v5.py "$@" | $PY -c "
import re,sys; s=sys.stdin.read(); h=float(re.search(r'hue\s+(-?[\d.]+)',s).group(1)); d=float(re.search(r'dark fraction (\d+)%',s).group(1))
sys.exit(0 if abs(h-20.0)<=$HUE_TOL and d<=$DARK_MAX else 1)"; }
klein() {  # klein OUT IMG   (prompt KLEIN_RED, ref canon/doug_master.png, bf16, seed 1 then 2 if the gate fails)
  local out=$1 img=$2 box=$3
  [ -f "$out" ] && { log "skip $out (exists)"; return 0; }
  for sd in 1 2; do
    mem_gate "klein $(basename "$out")"; local lid; lid=$(lease "klein-$(basename "$out" .png)" $KLEIN_GB)
    log "klein -> $out (seed $sd, ref canon/doug_master.png)"
    "$MFLUX" --model flux2-klein-9b --image-paths "$img" canon/doug_master.png --prompt "$KLEIN_RED" --steps $KLEIN_STEPS --guidance 1.0 --seed $sd --output "$out" >> final/klein_v5.log 2>&1
    local rc=$?; unlease "$lid"
    [ $rc -eq 0 ] && [ -f "$out" ] || { log "klein FAILED rc=$rc for $out"; tail -3 final/klein_v5.log | tee -a "$LOG"; return 1; }
    # shellcheck disable=SC2086
    hue "$out" $box; hue_ok "$out" $box && return 0
    log "seed $sd fails the numeric gate (hue within $HUE_TOL of 20, saddle dark <= $DARK_MAX%)"; [ $sd = 1 ] && mv "$out" "${out%.png}_s1_fail.png"; done
  [ -f "$out" ] || mv "${out%.png}_s1_fail.png" "$out"; log "$out kept although the numeric gate failed (eye check on the final sheet decides)"; return 0; }
ltx() {  # ltx NAME STILL SECONDS PROMPT -> clips/v5/NAME.mp4
  local name=$1 still=$2 secs=$3 prompt=$4
  [ -f "clips/v5/$name.mp4" ] && { log "skip $name (exists)"; return 0; }
  [ -f "$still" ] || { log "no still for $name ($still), skipped"; return 1; }
  train_wait; songforge_wait; log "ltx25 $name from $still ($secs s)"
  # 11/18 11:35: --low-ram (20 GB ask, transformer blocks streamed, same model) because Song Forge is warm: the guard's
  # non-forge budget is 50 GB and headroom ~79 GB, so the normal 82 GB ask can never be seated (the morning clips rendered cold).
  local out; out=$("$LTX" --i2v "$still" --duration "$secs" --res $RES --seed $SEED --label "hd5_$name" --static ${LTX_LOW_RAM:+--low-ram} "$prompt" 2>>final/clips_v5.log | tail -1)
  local src; src=$(echo "$out" | sed -n 's/.*→ \(.*\)$/\1/p'); [ -n "$src" ] && cp "$src" "clips/v5/$name.mp4"
  log "$name $out"
  if [ ! -f "clips/v5/$name.mp4" ] && [ "${_RETRY:-0}" = 0 ]; then   # one retry (11/18: a stale 72 GB training lease made the guard refuse every ask)
    log "$name did not land (tail of final/clips_v5.log): $(tail -2 final/clips_v5.log | tr '\n' ' ' | cut -c1-200)"; sleep 30
    _RETRY=1 ltx "$name" "$still" "$secs" "$prompt"; return; fi
  [ -f "clips/v5/$name.mp4" ] && strip "clips/v5/$name.mp4"; }

# ---------------------------------------------------------------- 0. wait for the main run to exit
log "=== run_v5_doug_all (pid $$): waiting for run_v5_renders.sh pid $WAIT_PID to exit"
while kill -0 "$WAIT_PID" 2>/dev/null; do
  if [ ! -f .doug_all_saw_step7 ] && grep -q -- "--- step 7" "$MAIN_LOG" 2>/dev/null; then touch .doug_all_saw_step7; log "main run reached step 7 (finish); its gates follow, then this run starts"; fi
  sleep 30; done
rm -f .doug_all_saw_step7
log "main run exited. clips/v5 now: $(ls clips/v5/*.mp4 2>/dev/null | xargs -n1 basename | tr '\n' ' ')"
grep -q "run_v5_renders finished" "$MAIN_LOG" 2>/dev/null || log "NOTE: the main log has no 'finished' line (it may have stopped early); continuing, --from 7 re-finishes whatever exists"

restart_training() {  # Matt approved stopping the life-model run for these renders; it auto-resumes from its ckpt
  rm -f "$TRAIN_RUN/STOP"; launchctl kickstart gui/$(id -u)/com.dtribe.graftself-full2 2>>"$LOG"
  for i in $(seq 1 40); do sleep 15; r=$(grep '"event": "resume"' "$TRAIN_RUN/train.log" 2>/dev/null | tail -1); [ -n "$r" ] && [ "$(echo "$r" | sed -n 's/.*"t": \([0-9]*\).*/\1/p')" -ge "$T0" ] && { log "training resumed: $r"; return 0; }; done
  log "training restart: no resume line in $TRAIN_RUN/train.log after 10 min (launchd state: $(launchctl print gui/$(id -u)/com.dtribe.graftself-full2 2>&1 | grep -m1 state))"; }
T0=$(date +%s)
bigjob_start() {  # Matt 11/11: around every big M5 job. Drains, never cuts a customer song, Song Forge moves to the mini.
  [ -f /tmp/hd5_bigjob_on ] && return 0
  for try in 1 2; do out=$(m5-bigjob start 2>&1); rc=$?; log "m5-bigjob start (try $try) rc=$rc: $(echo "$out" | tail -1)"
    [ $rc -eq 0 ] && { touch /tmp/hd5_bigjob_on; return 0; }; sleep 60; done
  die "m5-bigjob start failed twice the same way; not rendering at low memory on my own"; }
bigjob_end() { [ -f /tmp/hd5_bigjob_on ] || return 0; log "m5-bigjob end: $(m5-bigjob end 2>&1 | tail -1)"; rm -f /tmp/hd5_bigjob_on; }
T0=$(date +%s)
pause_watcher & PW=$!; trap 'kill $PW 2>/dev/null; bigjob_end; restart_training' EXIT

# ---------------------------------------------------------------- 0b. the main run's two missing clips (rows 3 and 11)
log "--- main-run clips that never landed: G_forest_red (LTX 4 s) and D_rollout_right (K6 once, else LTX from the red still)"
ltx G_forest_red stills/v5/G_forest_red.png 4 "$P_G_FOREST"
bigjob_start   # from here the M5 is free: full-memory LTX, K6 Pro for the rollout
if [ "${SKIP_K6:-0}" = 1 ] && [ ! -f clips/v5/D_rollout_right.mp4 ]; then log "K6 skipped (SKIP_K6=1: it already failed once, plan D9 rule); LTX i2v from the klein-red still"; ltx D_rollout_right stills/v5/D_rollout_right_red.png 5 "$P_ROLLOUT"; fi
if [ ! -f clips/v5/D_rollout_right.mp4 ] && [ -f stills/v5/D_rollout_right_red.png ]; then
  train_wait; songforge_wait; log "K6 Pro D_rollout_right (about 20 min)"
  out=$("$K6" --i2v stills/v5/D_rollout_right_red.png --duration 5 --res $RES --seed $SEED --static --label hd5_D_rollout_right "$P_ROLLOUT" 2>>final/clips_v5.log | tail -1)
  src=$(echo "$out" | sed -n 's/.*→ \(.*\)$/\1/p'); [ -n "$src" ] && cp "$src" clips/v5/D_rollout_right.mp4; log "D_rollout_right $out"
  if [ -f clips/v5/D_rollout_right.mp4 ]; then strip clips/v5/D_rollout_right.mp4
  else log "K6 failed once; the plan D9 hflip fallback would ship the OLD black-and-tan Doug (row 11), so LTX i2v from the klein-red still instead"
       ltx D_rollout_right stills/v5/D_rollout_right_red.png 5 "$P_ROLLOUT"; fi; fi

# ---------------------------------------------------------------- 1. stills (klein, same edit as the approved proof)
log "--- stills: klein red edit of the two v4 close shots"
# shellcheck disable=SC2086
klein stills/v5/Doug_close_glow_red.png stills/v4/Doug_close_glow_fix.png "$BOX_LOOK"
# shellcheck disable=SC2086
klein stills/v5/Doug_watch_red.png      stills/v4/Doug_watch_fix.png      "$BOX_WATCH"

# ---------------------------------------------------------------- 2. clips (LTX-2.5 i2v, as v4 made them, v5 style)
log "--- clips"
ltx NEW2_lookback_red stills/v5/Doug_close_glow_red.png 4 "$P_LOOKBACK"
ltx NEW4_watch_red    stills/v5/Doug_watch_red.png      4 "$P_WATCH"

# ---------------------------------------------------------------- 3. timeline: rows 2 and 5 take the new clips
$PY - <<'EOF' | tee -a "$LOG"
import json, os
p = "tools/timeline_v5.json"; t = json.load(open(p))
new = {"r02_lookback": ("clips/v5/NEW2_lookback_red.mp4", "Doug colour (Matt 11/18 9:47): klein red edit of Doug_close_glow_fix, v4 motion prompt; cue re-pick: whistle flinch was row 1.0 on NEW2"),
       "r05_watch":    ("clips/v5/NEW4_watch_red.mp4",    "Doug colour (Matt 11/18 9:47): klein red edit of Doug_watch_fix, v4 motion prompt")}
for r in t["rows"]:
    if r["id"] in new:
        c, n = new[r["id"]]
        if os.path.exists(c): r["replace_with"], r["replace_note"] = c, n; print(f"timeline_v5: {r['id']} -> {c}")
        else: print(f"timeline_v5: {r['id']} keeps {r['clip']} (no {c})")
t["note"] += " | 11/18 doug_all: rows 2 and 5 replace_with the klein-red re-renders (Doug the same russet in every row)."
json.dump(t, open(p, "w"), indent=1)
EOF

# ---------------------------------------------------------------- 4. finish + gates again (the main script's own steps 7-8)
log "--- re-finish + gates: tools/run_v5_renders.sh --from 7"
kill $PW 2>/dev/null   # the main script runs its own pause watcher
bash tools/run_v5_renders.sh --from 7 >> tools/run_v5_renders.log 2>&1; log "run_v5_renders --from 7 exit $?"
pause_watcher & PW=$!

# ---------------------------------------------------------------- 5. the Doug gate on the FINAL film
FILM=final/hank_doug_wild_rescue_trailer_v5.mp4; [ -f "$FILM" ] || die "no final film after --from 7"
log "--- Doug gate on $FILM"
# a) Doug-rows sheet for the eye: 3 frames per row where Doug appears (rows 1 2 3 5 6 8 9 10 11), from the final film
$PY - <<'EOF' | tee -a "$LOG"
import json, subprocess
rows = {r["id"]: r for r in json.load(open("tools/timeline_v5.json"))["rows"]}
doug = ["r01_hunt","r02_lookback","r03_found","r05_watch","r06_lead","r08_hi","r09_walkaway","r10_bench","r11_rollout"]
ins, parts = [], []
for i, rid in enumerate(doug):
    r = rows[rid]
    for k, f in enumerate((0.15, 0.5, 0.85)):
        ins += ["-ss", f"{r['start'] + r['dur'] * f:.2f}", "-i", "final/hank_doug_wild_rescue_trailer_v5.mp4"]
    parts.append("".join(f"[{i*3+k}:v]scale=480:-1[s{i*3+k}];" for k in range(3)) + "".join(f"[s{i*3+k}]" for k in range(3)) + f"hstack=3[h{i}]")
fc = ";".join(parts) + ";" + "".join(f"[h{i}]" for i in range(len(doug))) + f"vstack={len(doug)}"
subprocess.run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", fc, "-frames:v", "1", "-q:v", "3", "final/doug_rows_v5.jpg"])
print("doug rows sheet: final/doug_rows_v5.jpg")
EOF
# b) numeric backstop on the rows where Doug fills the frame (auto box; the film is 1920x1080)
bad=0
for spec in "r02_lookback 7.0" "r03_found 11.0" "r05_watch 19.2" "r08_hi 30.6" "r10_bench 37.8"; do
  set -- $spec; ffmpeg -v error -y -ss "$2" -i "$FILM" -frames:v 1 /tmp/doug_gate_$1.png
  m=$($PY tools/doug_box_v5.py /tmp/doug_gate_$1.png); log "gate $1: $m"
  echo "$m" | $PY -c "
import re,sys; s=sys.stdin.read(); h=float(re.search(r'hue\s+(-?[\d.]+)',s).group(1)); d=float(re.search(r'saddle dark\s+([\d.]+)%',s).group(1))
sys.exit(0 if abs(h-20.0)<=8 and d<=30 else 1)" || { bad=$((bad+1)); log "gate $1 FAILS the numeric check"; }; done
# c) continuity_check doug_colour (VL, 3 votes per shot, from the --from 7 gates)
dc_fail=$(grep -c "FAIL\] doug_colour" final/continuity_v5.log 2>/dev/null); dc_fail=${dc_fail:-0}
dc_pass=$(grep -c "PASS\] doug_colour" final/continuity_v5.log 2>/dev/null); dc_pass=${dc_pass:-0}
log "continuity doug_colour: $dc_pass PASS, $dc_fail FAIL (final/continuity_v5.log)"
grep "doug_colour" final/continuity_v5.log >> "$LOG" 2>/dev/null

# ---------------------------------------------------------------- 6. publish + text only when the gate holds
if [ "$bad" -eq 0 ] && [ "${dc_fail:-0}" -eq 0 ] && [ "${dc_pass:-0}" -ge 6 ]; then
  name="hank-doug-v5-$(LC_ALL=C tr -dc a-z0-9 </dev/urandom | head -c 12).mp4"
  if scp -q -o ConnectTimeout=30 "$FILM" "$VPS:$VPS_DIR/$name"; then
    url="$VPS_URL/$name"; log "published $url"
    bash "$HOME/.claude/imessage-send.sh" "Hank & Doug v5 is ready: $url" >/dev/null 2>&1 && log "texted Matt"
    chat-send "$CHAT" "Hank & Doug v5 published: $url. Doug gate: continuity doug_colour $dc_pass PASS / $dc_fail FAIL, numeric rows 2/3/5/8/10 all pass. Eye sheet: final/doug_rows_v5.jpg. Matt texted." >/dev/null 2>&1
  else die "scp to the VPS failed; film is $FILM on the M5 (not texted)"; fi
else
  log "HOLD: Doug gate not clean (numeric fails=$bad, doug_colour FAIL=$dc_fail PASS=$dc_pass). Film NOT published, Matt NOT texted."
  chat-send "$CHAT" "Hank & Doug v5 finished but HELD: Doug gate not clean (numeric fails=$bad, continuity doug_colour $dc_pass PASS / $dc_fail FAIL). Look at final/doug_rows_v5.jpg and final/continuity_v5.log before anything goes out." >/dev/null 2>&1
fi
log "=== run_v5_doug_all finished"
