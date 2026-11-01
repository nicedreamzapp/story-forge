#!/usr/bin/env python3
"""THE LAST SIGNAL motion queue — detached, resumable, one model (LTX-2.5 bf16 MLX via bin/make-ltx25).
Run:  nohup ~/.local/mlx-server/bin/python tools/render_queue.py >> logs/render.log 2>&1 &
Order: take 1 of every render, then take 2, then take 3 (heroes), so coverage exists early.
Each finished take -> clips/takes/<rid>_t<n>.mp4 + <rid>_t<n>.done (json: seed, secs, cmd). Skips done takes.
Song Forge first: waits while jobs_running > 0 before every clip. make-ltx25 runs mem-gate + forge_guard lease."""
import json, os, re, shutil, subprocess, sys, time, urllib.request
from pathlib import Path
P = Path(__file__).resolve().parent.parent
SF = P.parent.parent
TAKES = P / "clips/takes"; TAKES.mkdir(parents=True, exist_ok=True)
SEEDS = [1101, 2202, 3303]
STOP = P / "logs/STOP_RENDER"   # touch this file to stop after the current clip

def log(m): print(time.strftime("%H:%M:%S"), m, flush=True)

def wait_songforge():
    while True:
        try:
            s = json.load(urllib.request.urlopen("http://127.0.0.1:8767/api/status", timeout=5))
            if s.get("jobs_running", 0) == 0: return
            log(f"Song Forge busy ({s['jobs_running']} running) - waiting")
        except Exception as e:
            log(f"Song Forge status unreachable ({e}) - continuing"); return
        time.sleep(30)

import argparse
ap = argparse.ArgumentParser()
ap.add_argument("--mode", choices=["previs", "final"], default="previs")
ap.add_argument("--plan", default=str(P / "final_plan.json"), help="final mode: [{id, takes, seconds}]")
A = ap.parse_args()
renders = json.load(open(P / "renders.json"))["renders"]
queue = []
if A.mode == "previs":
    # one LTX-2.5 distilled draft per render (Matt 4:43 AM: previs first, decide the cut, then render only what is used)
    TAKES = P / "clips/previs"; TAKES.mkdir(parents=True, exist_ok=True)
    queue = [(r, 1) for r in renders]
else:
    plan = {x["id"]: x for x in json.load(open(A.plan))}
    rs = []
    for r in renders:
        if r["id"] in plan:
            r = dict(r); r["takes"] = plan[r["id"]]["takes"]; r["duration"] = plan[r["id"]]["seconds"]; rs.append(r)
    for n in range(3):
        for r in rs:
            if n < r["takes"]:
                queue.append((r, n + 1))
log(f"queue: {len(queue)} takes over {len(renders)} renders")
fails = {}
for r, n in queue:
    if STOP.exists(): log("STOP file present - exiting"); break
    rid = r["id"]; tag = f"{rid}_t{n}"
    done = TAKES / f"{tag}.done"
    if done.exists(): continue
    still = P / "stills" / f"LOCKED_{rid}.png"
    if not still.exists():
        log(f"SKIP {tag}: no locked still {still.name}"); continue
    if fails.get(rid, 0) >= 2:
        log(f"SKIP {tag}: {rid} failed twice the same way - needs a look"); continue
    wait_songforge()
    cmd = [sys.executable, str(SF / "bin/make-ltx25"), "--i2v", str(still), "--res", r.get("res", "832x480"),
           "--duration", str(r.get("duration", 5.0)), "--seed", str(SEEDS[n - 1]), "--label", f"ls_{A.mode}_{tag}",
           "--low-ram", r["animate"]]
    if A.mode == "final":
        cmd.insert(-1, "--hq")   # dev transformer + CFG two-stage for the shots that make the cut
    log(f"START {tag} seed {SEEDS[n-1]}")
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True)
    secs = time.time() - t0
    m = re.search(r"done in [\d.]+s → (\S+)", p.stdout)
    if p.returncode != 0 or not m or not Path(m.group(1)).exists():
        fails[rid] = fails.get(rid, 0) + 1
        log(f"FAIL {tag} rc={p.returncode} after {secs:.0f}s :: {(p.stderr or '')[-600:]!r}")
        continue
    out = TAKES / f"{tag}.mp4"
    shutil.move(m.group(1), out)
    info = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                          capture_output=True, text=True).stdout.strip()
    done.write_text(json.dumps({"seed": SEEDS[n-1], "secs": round(secs), "duration": info, "still": str(still),
                                "animate": r["animate"], "finished": time.strftime("%Y-%m-%d %H:%M:%S"),
                                "engine_log": (p.stderr or "")[-300:]}))
    left = sum(1 for rr, nn in queue if not (TAKES / f"{rr['id']}_t{nn}.done").exists())
    log(f"DONE {tag} in {secs:.0f}s ({info}s clip) - {left} takes left, ~{left*secs/60:.0f} min at this pace")
log("queue finished")
(P / f"logs/RENDER_QUEUE_FINISHED_{A.mode}").write_text(time.strftime("%Y-%m-%d %H:%M:%S"))
