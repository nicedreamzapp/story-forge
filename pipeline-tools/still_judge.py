#!/usr/bin/env python3
"""still_judge.py STILL.png --prompt "what it must show" --json out.json
Judges a K6 FIRST FRAME before any K6 time is spent on it (shared tool since 11/24; same judge, same rules as pipeline-tools/clip_judge.py, one
image instead of a 2x2 grid). Lachish data: most clip FAILs ("all frames: paved road / modern tower / wrong layout")
were already in the first frame, and each cost ~15 min of K6. Exit 0 PASS, 1 FAIL, 2 could not run (never a pass)."""
import argparse, json, re, shutil, subprocess, sys
from pathlib import Path
CLAUDE = shutil.which("claude") or str(Path.home() / "Scripts/claude")
Q = """You are a STRICT quality judge for the FIRST FRAME of an AI image-to-video film shot. Read the image {png} with
the Read tool. It is supposed to show: "{prompt}"
FAIL it if ANY of these is visible: readable text, letters, numbers or logos anywhere; a hand with the wrong number of
fingers or melted parts; a person or face (none are wanted); fire or flames where they do not belong; the wrong subject
or framing; obvious AI garbage (fused objects, warped geometry). Otherwise PASS. It should look like a real film frame.
Answer with ONLY one line of JSON and nothing else: {{"verdict": "PASS" or "FAIL", "defects": "short reason or none"}}"""
ap = argparse.ArgumentParser(); ap.add_argument("png"); ap.add_argument("--prompt", required=True); ap.add_argument("--json")
a = ap.parse_args()
png = str(Path(a.png).resolve())
try:
    # 11/24 fix: the prompt used to sit after "--allowedTools Read", which takes a LIST, so the prompt was eaten as a
    # tool name and claude answered "Input must be provided either through stdin or as a prompt argument" on every
    # still (all 8 captcha stills went unjudged). The prompt now goes in on stdin.
    r = subprocess.run([CLAUDE, "-p", "--model", "opus", "--allowedTools", "Read", "--add-dir", str(Path(png).parent),
                        "--output-format", "text"], input=Q.format(png=png, prompt=a.prompt),
                       capture_output=True, text=True, timeout=300, cwd=str(Path(png).parent))
    m = re.search(r"\{[^{}]*\"verdict\"[^{}]*\}", r.stdout or "")
    v = json.loads(m.group(0)) if m else {"verdict": "ERROR", "defects": "judge gave no verdict: " + (r.stdout or r.stderr)[-200:]}
except Exception as e:
    v = {"verdict": "ERROR", "defects": str(e)[:200]}
print(json.dumps(v))
if v.get("verdict") not in ("PASS", "FAIL"):   # never silent: an unrun judge is shouted, and exits 2 (never a pass)
    print(f"STILL_JUDGE_UNRUN {png}: {v.get('defects')}", file=sys.stderr)
if a.json:
    json.dump(v, open(a.json, "w"))
sys.exit({"PASS": 0, "FAIL": 1}.get(v.get("verdict"), 2))
