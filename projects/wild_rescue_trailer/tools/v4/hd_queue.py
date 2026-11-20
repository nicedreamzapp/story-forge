#!/usr/bin/env python3
"""HANK & DOUG'S WILD RESCUE rebuild v4: the M5 picture queue (2026-11-01 evening). Detached, resumable, one model
loaded at a time. Normally launched by tools/v4/hd_waiter.sh the moment THE LAST SIGNAL v2 redo frees the M5 GPU.

  stage stills : Krea 2 Turbo bf16 (tools/v4/krea_batch.py, one load): start-still candidates (stills/cand), prompts
                 from tools/v4/bible_v4.py word for word (v4/jobs_stills.json). The canon masters (canon/cand, for
                 Matt's stage-03 approval; nothing downstream reads them) render after take 1 of every shot.
  stage gate   : Qwen3-VL beat_gate on every start-still candidate (house checks in must_not: no humans, Doug a
                 long-eared bloodhound not a beagle, the team = horse/zebra/camel/cow one each, no trucks/tires)
  stage lock   : per render, the first PASS in seed order -> stills/LOCKED_<rid>.png (832x480, chmod 444)
  stage reroll : renders with no PASS get 2 new Krea seeds + the gate once more; still nothing -> the first candidate
                 is locked and flagged GATE-FAIL-KEPT in v4/locks.json (a declared exception for review)
  stage motion : Kandinsky 6 Pro i2v (bin/make-k6, 832x480, 10 steps) from the locked stills at cut length + 0.5 s
                 handles (floor 1.5 s); LTX-2.5 a2v (bin/make-ltx25 --audio --hq --low-ram) only for the two
                 lip-sync close-ups. Breadth first: take 1 of everything, then take 2, then take 3, then the K6
                 alternates of the Blender-primary ant shots. Blender owns every wheel shot (clips/blender/).
Outputs: clips/v4/<rid>_t<n>.mp4 + .done (json). Progress: v4/logs/queue.log (one line per item, with an ETA).
Control: touch v4/logs/STOP to stop after the current item (a re-launch resumes). Finished: v4/logs/HD_QUEUE_FINISHED.
  hd_queue.py            run (detached via the waiter)
  hd_queue.py --dry-run  print every stage, item and command with the time projection; runs nothing"""
import argparse, json, os, re, shutil, subprocess, sys, time, urllib.request
from pathlib import Path

P = Path(__file__).resolve().parents[2]
SF = P.parent.parent
V4 = P / "v4"; LOGS = V4 / "logs"; CLIPS = P / "clips/v4"
STOP = LOGS / "STOP"; FIN = LOGS / "HD_QUEUE_FINISHED"
HOME = Path.home()
KREA_PY = HOME / "AI/krea2/venv/bin/python"
MLX_PY = HOME / ".local/mlx-server/bin/python"
K6_SEEDS = [1101, 2202, 3303]
REROLL_SEEDS = [51, 67]
FPS = 24

ap = argparse.ArgumentParser()
ap.add_argument("--dry-run", action="store_true")
A = ap.parse_args()
DRY = A.dry_run
if not DRY:
    for d in (LOGS, CLIPS, P / "stills/cand", P / "canon/cand"):
        d.mkdir(parents=True, exist_ok=True)

def log(m):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {'[DRY] ' if DRY else ''}{m}"
    print(line, flush=True)
    if not DRY:
        with open(LOGS / "queue.log", "a") as f: f.write(line + "\n")

def stopped():
    if STOP.exists():
        log("STOP file present - exiting after the current item (re-launch resumes)"); return True
    return False

def run(cmd, logfile, tries=3, wait=120, what=""):
    """run a model step; mem-gate/forge_guard refusals exit non-zero, so wait and retry, then give up loudly"""
    for k in range(1, tries + 1):
        if DRY:
            log(f"would run ({what}): {' '.join(map(str, cmd))[:260]} >> {logfile.name}"); return 0
        t = time.time()
        with open(logfile, "a") as f:
            rc = subprocess.run(list(map(str, cmd)), stdout=f, stderr=subprocess.STDOUT, cwd=str(P)).returncode
        log(f"{what}: rc={rc} after {(time.time()-t)/60:.1f} min (try {k}/{tries})")
        if rc == 0: return 0
        if stopped(): return rc
        time.sleep(wait)
    return rc

plan = json.load(open(V4 / "plan.json"))
PL = {e["id"]: e for e in plan}
needs_still = [e for e in plan if e.get("still")]

def mark(name): return LOGS / f"STAGE_DONE_{name}"
def done_stage(name):
    if not DRY: mark(name).write_text(time.strftime("%Y-%m-%d %H:%M:%S"))

# ---------------- stills (Krea 2 Turbo) ----------------
def krea(jobs, tag):
    todo = [j for j in jobs if not Path(j["out"]).exists()]
    log(f"[{tag}] Krea 2 Turbo: {len(todo)}/{len(jobs)} images to render (~{25*len(todo)/60+1.5:.0f} min at ~25 s each + load)")
    if not todo: return 0
    jf = V4 / f"jobs_run_{tag}.json"
    if not DRY: json.dump(jobs, open(jf, "w"), indent=1)
    rc = run([KREA_PY, P / "tools/v4/krea_batch.py", jf], LOGS / f"krea_{tag}.log", what=f"krea {tag}")
    missing = [j["out"] for j in jobs if not Path(j["out"]).exists()]
    if missing and not DRY: log(f"[{tag}] WARNING {len(missing)} images missing after the batch (rc={rc}): {missing[:4]}")
    return rc

# ---------------- gate (Qwen3-VL beat_gate) ----------------
VERD = re.compile(r"^\[(PASS|FAIL|ERR )\] (\S+):", re.M)
def verdicts():
    txt = "".join(f.read_text() for f in sorted(LOGS.glob("gate_*.log"))) if LOGS.exists() else ""
    return {m.group(2): m.group(1).strip() for m in VERD.finditer(txt)}

def gate(cands, tag):
    v = verdicts()
    shots = []
    for rid, f in cands:
        if f.stem in v and v[f.stem] != "ERR": continue
        e = PL[rid]
        shots.append({"id": f.stem, "image": str(f), "beat": e["beat"], "must_not": e["must_not"]})
    log(f"[{tag}] beat_gate (Qwen3-VL): {len(shots)} candidates to judge (~{12*len(shots)/60+1:.0f} min at ~12 s each + load)")
    if not shots: return 0
    gf = V4 / f"gate_{tag}.json"
    if not DRY: json.dump({"set_masters": {}, "shots": shots}, open(gf, "w"), indent=1)
    # --votes 1: a still is the same image every vote and the VL decode is greedy, so 3 votes were always unanimous
    # (71/71 on 10/31-11/1: 39x "0 of 3", 32x "3 of 3"); one vote = the same verdict in a third of the time
    rc = run([MLX_PY, SF / "pipeline-tools/beat_gate.py", gf, "--votes", "1", "--report", V4 / f"gate_{tag}_report.md"],
             LOGS / f"gate_{tag}.log", tries=2, what=f"gate {tag}")
    return 0 if rc in (0, 1) else rc   # 1 = some FAIL (normal); 2 = the gate could not run

def cand_files(rid, seeds):
    return [(rid, P / f"stills/cand/{rid}_s{s}.png") for s in seeds]

def lock(rid, src, flag, votes):
    out = P / f"stills/LOCKED_{rid}.png"
    if DRY: log(f"would lock {rid} <- {src.name} ({flag})"); return
    from PIL import Image
    if out.exists(): os.chmod(out, 0o644)
    im = Image.open(src).convert("RGB")
    if PL[rid].get("crop"): im = im.crop(tuple(PL[rid]["crop"]))   # e.g. R14: cut the wheel line out of frame
    im.resize((832, 480), Image.LANCZOS).save(out)
    os.chmod(out, 0o444)
    locks = json.load(open(V4 / "locks.json")) if (V4 / "locks.json").exists() else {}
    locks[rid] = {"from": str(src.relative_to(P)), "gate": flag, "votes": votes, "at": time.strftime("%H:%M:%S")}
    json.dump(locks, open(V4 / "locks.json", "w"), indent=1)

def lock_pass(rids, seeds_for, final=False):
    v = verdicts(); unresolved = []
    for rid in rids:
        if (P / f"stills/LOCKED_{rid}.png").exists() and not DRY: continue
        cands = [f for _, f in cand_files(rid, seeds_for(rid)) if f.exists() or DRY]
        votes = {f.stem: v.get(f.stem, "UNCHECKED") for f in cands}
        win = next((f for f in cands if v.get(f.stem) == "PASS"), None)
        if win: lock(rid, win, "PASS", votes)
        elif final and cands: lock(rid, cands[0], "GATE-FAIL-KEPT", votes)
        else: unresolved.append(rid)
    return unresolved

# ---------------- motion ----------------
def pad_voice(src, rid):
    """a2v: 0.25 s of silence before and after the line = the handles (make-ltx25 pads to the clip length itself)"""
    out = V4 / f"a2v/{rid}.wav"
    if DRY: return out
    out.parent.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", "adelay=250|250,apad=pad_dur=0.25",
                    "-ar", "48000", str(out)], check=True)
    return out

def k6_minutes(seconds):
    f = max(17, min(121, round(seconds * FPS / 4) * 4 + 1))
    return (50 + 671 * f / 73) / 60, f       # measured 11/1: load+encode ~50 s, denoise+decode ~671 s per 73 frames

def motion_queue():
    q = []
    k6 = [e for e in plan if e["engine"] == "k6"]; ltx = [e for e in plan if e["engine"] == "ltx_a2v"]
    for n in (1, 2, 3):
        q += [(e, n) for e in k6 if n <= e["takes"]]
        q += [(e, n) for e in ltx if n <= e["takes"]]
        if n == 1:
            q.append(({"id": "CANON", "engine": "krea_canon", "clip_seconds": 0}, 1))   # canon masters for Matt's approval
    q += [(e, 1) for e in plan if e["engine"] == "blender_alt_k6"]
    return q

def motion():
    q = motion_queue(); fails = {}; t_sum = 0.0; p_sum = 0.0
    def est_of(e): return 14.0 if e["engine"] == "krea_canon" else 9.0 if e["engine"] == "ltx_a2v" else k6_minutes(e["clip_seconds"])[0]
    est_total = sum(est_of(e) for e, _ in q)
    log(f"[motion] {len(q)-1} takes: {sum(e['engine'] in ('k6','blender_alt_k6') for e,_ in q)} K6 + {sum(e['engine']=='ltx_a2v' for e,_ in q)} LTX a2v (+ canon masters after take 1), "
        f"projected ~{est_total/60:.1f} h (K6 ~{k6_minutes(1.5)[0]:.1f} min per 1.5 s clip, ~12 min per 3 s)")
    # two sweeps: the second picks up anything skipped the first time (an a2v voice or a still that arrived late)
    for e, n in q + [(e, n) for e, n in q if e["engine"] != "krea_canon"]:
        if stopped(): return False
        if e["engine"] == "krea_canon":
            if not mark("canon").exists() or DRY:
                t = time.time(); krea(json.load(open(V4 / "jobs_canon.json")), "canon")
                log(f"--- canon masters done in {(time.time()-t)/60:.1f} min (canon/cand, Matt approves the masters)"); done_stage("canon")
            continue
        rid = e["id"]; tag = f"{rid}_t{n}"; done = CLIPS / f"{tag}.done"
        if done.exists(): continue
        still = P / f"stills/LOCKED_{rid}.png"
        if not still.exists() and not DRY:
            log(f"SKIP {tag}: no locked still"); continue
        if fails.get(rid, 0) >= 2:
            log(f"SKIP {tag}: {rid} failed twice the same way - needs a look"); continue
        seed = K6_SEEDS[n - 1]
        if e["engine"] == "ltx_a2v":
            voice = P / e["voice"]
            if not voice.exists() and not DRY:
                log(f"SKIP {tag}: voice {e['voice']} not delivered yet"); continue
            cmd = [MLX_PY, SF / "bin/make-ltx25", "--i2v", still, "--audio", pad_voice(voice, rid), "--seed", seed,
                   "--label", f"wr4_{tag}", "--hq", "--low-ram", e["animate"]]
            est = 9.0
        else:
            est, frames = k6_minutes(e["clip_seconds"])
            cmd = [sys.executable, SF / "bin/make-k6", "--i2v", still, "--res", "832x480", "--duration", e["clip_seconds"],
                   "--seed", seed, "--label", f"wr4_{tag}"] + (["--static"] if e.get("static") else []) + [e["animate"]]
        if DRY:
            log(f"would render {tag} ({e['engine']}, {e['clip_seconds']} s, ~{est:.1f} min): {' '.join(map(str, cmd))[:200]}")
            continue
        log(f"START {tag} ({e['engine']}, {e['clip_seconds']} s clip for {e['cut_seconds']} s of cut, seed {seed})")
        t0 = time.time()
        p = subprocess.run(list(map(str, cmd)), capture_output=True, text=True, cwd=str(P))
        secs = time.time() - t0
        m = re.search(r"done in [\d.]+s → (\S+)", p.stdout)
        if p.returncode != 0 or not m or not Path(m.group(1)).exists():
            fails[rid] = fails.get(rid, 0) + 1
            log(f"FAIL {tag} rc={p.returncode} after {secs:.0f}s :: {((p.stderr or '') + (p.stdout or ''))[-500:]!r}")
            continue
        out = CLIPS / f"{tag}.mp4"; shutil.move(m.group(1), out)
        dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                             capture_output=True, text=True).stdout.strip()
        done.write_text(json.dumps({"engine": e["engine"], "seed": seed, "secs": round(secs), "duration": dur,
                                    "still": str(still), "animate": e["animate"], "feeds_cuts": e["feeds_cuts"],
                                    "finished": time.strftime("%Y-%m-%d %H:%M:%S"), "engine_log": (p.stderr or "")[-300:]}))
        t_sum += secs / 60; p_sum += est          # actual vs projected minutes so far -> pace factor
        left = [(ee, nn) for ee, nn in q if ee["engine"] != "krea_canon" and not (CLIPS / f"{ee['id']}_t{nn}.done").exists()]
        eta = sum(est_of(ee) for ee, _ in left)
        eta *= t_sum / max(0.1, p_sum)
        log(f"DONE {tag} in {secs/60:.1f} min ({dur}s clip) - {len(left)} takes left, ~{eta/60:.1f} h at the projected pace "
            f"(ETA {time.strftime('%I:%M %p', time.localtime(time.time() + eta*60))})")
    return True

# ---------------- main ----------------
log(f"=== HANK & DOUG v4 queue start (Krea 2 stills -> Qwen3-VL gate -> K6 motion) in {P}")
stills = json.load(open(V4 / "jobs_stills.json"))
if not mark("stills").exists() or DRY:
    t = time.time(); log("--- stage stills")
    krea(stills, "stills")                  # start stills only: canon masters wait until take 1 of every shot is done
    log(f"--- stage stills done in {(time.time()-t)/60:.1f} min"); done_stage("stills")
if stopped(): sys.exit(0)
rids = [e["id"] for e in needs_still]
if not mark("lock").exists() or DRY:
    t = time.time(); log("--- stage gate + lock")
    rc = gate([c for e in needs_still for c in cand_files(e["id"], e["seeds"]) if c[1].exists() or DRY], "stills")
    if rc != 0:
        # the gate could not run at all (rc 2 twice): don't burn a re-roll on nothing; lock seed 1, flagged for review
        log(f"gate could not run (rc={rc}); locking the first candidate of each render, flagged GATE-UNCHECKED")
        for r in rids:
            c = [f for _, f in cand_files(r, PL[r]["seeds"]) if f.exists()]
            if c and not (P / f"stills/LOCKED_{r}.png").exists(): lock(r, c[0], "GATE-UNCHECKED", {})
    unresolved = lock_pass(rids, lambda r: PL[r]["seeds"])
    log(f"locked {len(rids)-len(unresolved)}/{len(rids)} on a gate PASS; no PASS yet: {unresolved}")
    if unresolved and not stopped():
        rr = [{"out": str(P / f"stills/cand/{r}_s{s}.png"), "prompt": PL[r]["still"], "w": 1248, "h": 720, "seed": s}
              for r in unresolved for s in REROLL_SEEDS]
        krea(rr, "reroll")
        gate([c for r in unresolved for c in cand_files(r, REROLL_SEEDS) if c[1].exists() or DRY], "reroll")
    left = lock_pass(rids, lambda r: PL[r]["seeds"] + REROLL_SEEDS, final=True)
    log(f"--- stage gate + lock done in {(time.time()-t)/60:.1f} min; GATE-FAIL-KEPT: "
        f"{[r for r, v in (json.load(open(V4/'locks.json')).items() if (V4/'locks.json').exists() else []) if v['gate'] != 'PASS']}")
    done_stage("lock")
if stopped(): sys.exit(0)
t = time.time(); log("--- stage motion")
finished = motion()
log(f"--- stage motion {'finished' if finished else 'stopped'} after {(time.time()-t)/60:.1f} min")
if finished and not DRY:
    FIN.write_text(time.strftime("%Y-%m-%d %H:%M:%S"))
    log(f"=== DONE. Clips in {CLIPS}; Blender wheel/ant shots in {P/'clips/blender'} "
        f"({'BLENDER_DONE present' if (P/'clips/blender/BLENDER_DONE').exists() else 'BLENDER_DONE MISSING'})")
