#!/usr/bin/env python3
"""Part-2 hero re-render (2026-11-01): R03 eye contact + R15 bench were LOCKED on stills whose Doug is a tricolor
beagle-like hound (black saddle, white legs), not canon Doug; the VL clip gate also called R03 'beagle-like'.
New stills were re-rolled from the canon plates at lower img2img strength (tools/jobs_redo7.json) and locked;
this renders 2 LTX-2.5 --hq takes each at cut length + handles (t4, t5), same animate prompts, one model.
Run: nohup ~/.local/mlx-server/bin/python tools/redo_queue.py >> logs/render_redo.log 2>&1 &"""
import json, re, shutil, subprocess, sys, time, urllib.request
from pathlib import Path
P = Path(__file__).resolve().parent.parent; SF = P.parent.parent; TAKES = P / "clips/takes"
R = {r["id"]: r for r in json.load(open(P / "renders.json"))["renders"]}
plan = {x["id"]: x for x in json.load(open(P / "final_plan.json"))}
def log(m): print(time.strftime("%H:%M:%S"), m, flush=True)
def wait_sf():
    while True:
        try:
            if json.load(urllib.request.urlopen("http://127.0.0.1:8767/api/status", timeout=5)).get("jobs_running", 0) == 0: return
            log("Song Forge busy - waiting")
        except Exception: return
        time.sleep(30)
for n, seed in ((4, 4404), (5, 5505)):
    for rid in ("R03_eye_contact", "R15_bench"):
        tag = f"{rid}_t{n}"; done = TAKES / f"{tag}.done"
        if done.exists(): continue
        r = R[rid]; still = P / f"stills/LOCKED_{rid}.png"; wait_sf()
        cmd = [sys.executable, str(SF / "bin/make-ltx25"), "--i2v", str(still), "--res", r.get("res", "832x480"),
               "--duration", str(plan[rid]["seconds"]), "--seed", str(seed), "--label", f"wr_redo_{tag}", "--low-ram", "--hq", r["animate"]]
        log(f"START {tag}"); t0 = time.time()
        p = subprocess.run(cmd, capture_output=True, text=True); secs = time.time() - t0
        m = re.search(r"done in [\d.]+s → (\S+)", p.stdout)
        if p.returncode != 0 or not m or not Path(m.group(1)).exists():
            log(f"FAIL {tag} rc={p.returncode} {secs:.0f}s {(p.stderr or '')[-500:]!r}"); continue
        out = TAKES / f"{tag}.mp4"; shutil.move(m.group(1), out)
        dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout.strip()
        done.write_text(json.dumps({"seed": seed, "secs": round(secs), "duration": dur, "still": str(still), "animate": r["animate"]}))
        log(f"DONE {tag} in {secs:.0f}s ({dur}s)")
(P / "logs/REDO_FINISHED").write_text(time.strftime("%H:%M:%S"))
log("redo finished")
