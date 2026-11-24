#!/bin/bash
# runner_lib.sh — shared pieces every Story Forge render runner sources (11/24, learned on the captcha film).
#   . "$HOME/Desktop/PROJECTS/story-forge/pipeline-tools/runner_lib.sh"
#   bigjob_protect <project>      # FIRST line of any runner that renders (stills, K6, LTX, voice)
#   cliche_gate_or_stop <project_dir>   # before any still is drawn
#   judge_or_stop <rc> <what>     # after a still/clip judge: rc 2 (could not run) stops the run, loudly
# Rules it enforces (_shared/gates-and-qc.md "RUNNER RULES"):
#  * m5-bigjob end skips killing renders while ~/.local/bigjob-protect/<project> holds a live pid. Another job's
#    "end" killed two captcha clips mid-render. The pid is written at start and removed on exit (a nested runner
#    keeps its parent's pid and never removes it).
#  * A judge that could not run (usage limit, empty answer) is never a pass and never a reason to borrow a
#    fallback crop or an unjudged still: the run stops and says why.
#  * The cliche gate passes before a single still is drawn.
SF_ROOT="${SF_ROOT:-$HOME/Desktop/PROJECTS/story-forge}"
BIGJOB_PROTECT_DIR="$HOME/.local/bigjob-protect"

bigjob_protect() {
  local name=$1 f old
  [ -n "$name" ] || { echo "bigjob_protect: give the project name" >&2; return 2; }
  mkdir -p "$BIGJOB_PROTECT_DIR"; f="$BIGJOB_PROTECT_DIR/$name"
  old=$(cat "$f" 2>/dev/null)
  if [ -n "$old" ] && [ "$old" != "$$" ] && kill -0 "$old" 2>/dev/null; then
    echo "[runner] render protect already held by pid $old for $name (parent runner), keeping it"
    return 0
  fi
  echo $$ > "$f"
  _BIGJOB_FILE=$f
  trap '_bigjob_release' EXIT
  echo "[runner] render protect on: $f (pid $$)"
}
_bigjob_release() {
  [ -n "${_BIGJOB_FILE:-}" ] && [ "$(cat "$_BIGJOB_FILE" 2>/dev/null)" = "$$" ] && rm -f "$_BIGJOB_FILE"
}

cliche_gate_or_stop() {
  local proj=$1 py=${PY3:-/opt/homebrew/bin/python3}
  "$py" "$SF_ROOT/pipeline-tools/cliche_gate.py" "$proj" || {
    echo "[runner] STOP: the cliche gate failed (above). No still or render runs until the shot list passes."
    return 1; }
}

judge_or_stop() {   # judge_or_stop RC "what was judged" -> returns RC; RC 2 prints a loud STOP line
  local rc=$1 what=$2
  if [ "$rc" -eq 2 ]; then
    echo "[runner] STOP: the judge could not run on $what (usage limit or no answer). Nothing unjudged is used and"
    echo "[runner]       no fallback is borrowed. Re-run when the judge is back, or tell Matt."
  fi
  return "$rc"
}
