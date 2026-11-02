#!/usr/bin/env python3
"""THE LAST SIGNAL v2 redo (2026-11-01, Matt-approved): same story, same cut, same sound, new picture models.
  stills  : Krea 2 Turbo for every text-to-image still (tools/zimage_batch.py), same prompt + seed as the locked
            original. The img2img stills (ship polish R03/R04/R05/R14, creature guide R15, ship grab R18) stay on
            Z-Image-Turbo with the identical job, so they are copied from stills/locked_full (re-rendering the same
            model/seed/strength gives the same frame); --rerun-i2i renders them again. R01 is the Blender hero render.
  motion  : Kandinsky 6 Pro i2v (bin/make-k6, 832x480, 10 steps), ONE clip per render, 73 frames (3.04 s). Two
            renders hold a single cut longer than 73 frames allow and get longer clips: R04 arrival (4.4 s cut ->
            113 frames) and R11 welcome (3.8 s cut -> 97 frames). If a long clip fails it falls back to 73 frames and
            the cut is slowed to fit (logged). Cuts that used different LTX takes of one render now share its one K6
            clip at non-overlapping in-points where the clip has room.
  upscale : SeedVR2-3B 720p on every cut held >= 0.9 s, lanczos for the rest (same as tools/seedvr2_batch.py).
  finish  : face_lock on the same 4 captain/crewmate cuts, bloom + bin/grade + scope bars (tools/finish_4k.py),
            original title card, original mix (sfx/mix_plan.json via bin/surround-mix), deliver.py's three muxes.
Everything goes to renders_v2_krea_k6/; the original trailer and stills are only read. Resumable: every stage
skips outputs that exist. Touch renders_v2_krea_k6/logs/STOP to stop after the current item.
Run (detached, normally via tools/redo_v2_wait.sh):
  ~/AI/ComfyUI/venv/bin/python tools/redo_v2.py >> renders_v2_krea_k6/logs/redo_v2.log 2>&1
Progress (one line per item, per-stage counts): renders_v2_krea_k6/logs/progress.log"""
import json, math, re, shutil, subprocess, sys, time, urllib.request
from pathlib import Path
import numpy as np
from PIL import Image

P = Path(__file__).resolve().parent.parent
SF = P.parent.parent
V2 = P / "renders_v2_krea_k6"
for d in ("logs", "stills/full", "stills/locked", "clips", "final/segs/h", "final/segs/scope", "final/segs/up",
          "final/segs/locked", "final/segs/4k"):
    (V2 / d).mkdir(parents=True, exist_ok=True)
HOME = Path.home()
KREA_PY = HOME / "AI/krea2/venv/bin/python"
COMFY = HOME / "AI/ComfyUI"; COMFY_PY = COMFY / "venv/bin/python"
FPS = 24
K6_FRAMES = 73; K6_SEEDS = (1101, 2202)
LONG = {"R04_arrival": 4.6, "R11_captain_welcome": 4.0}   # seconds -> make-k6 frames_for: 113 / 97
FACE_LOCK = ("c06b_crew_walk", "c09_welcome", "c14b_sprint", "c15c_sprint")   # the original's face-locked cuts
STOP = V2 / "logs/STOP"
PROG = V2 / "logs/progress.log"
T0 = time.time()

def log(m):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {m}"
    print(line, flush=True)
    with open(PROG, "a") as f: f.write(line + "\n")

def stop_check():
    if STOP.exists(): log("STOP file present - exiting"); sys.exit(0)

def nfr(f):
    return int(subprocess.check_output(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v", "-show_entries",
                                        "stream=nb_read_frames", "-of", "csv=p=0", str(f)]).strip())

def ff(*a): subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, a)], check=True)

renders = {r["id"]: r for r in json.load(open(P / "renders.json"))["renders"]}
RIDS = sorted(renders)

# ---------------- 1+2. stills: Krea 2 verify frame, then every still ----------------
def still_jobs():
    src = json.load(open(P / "stills/locked_sources.json")); byout = {}
    for f in sorted((P / "tools").glob("jobs_*.json")):
        for j in json.load(open(f)): byout[j["out"].split("last_signal/")[-1]] = j
    t2i, copy = [], []
    for rid in RIDS:
        j = byout.get(src[rid])
        if j and not j.get("init"):
            t2i.append({"out": str(V2 / f"stills/full/{rid}.png"), "prompt": j["prompt"], "w": j.get("w", 1248),
                        "h": j.get("h", 720), "seed": j.get("seed", 1)})
        elif j and "--rerun-i2i" in sys.argv:
            copy.append((rid, dict(j, out=str(V2 / f"stills/full/{rid}.png"))))
        else:
            copy.append((rid, None))   # Z-Image img2img (identical job) or the Blender R01 render
    return t2i, copy

def run_stills():
    t2i, copy = still_jobs()
    log(f"[stills] {len(t2i)} Krea 2 text-to-image + {len(copy)} img2img/Blender ({'re-rendered on Z-Image' if '--rerun-i2i' in sys.argv else 'copied from the original'})")
    batch = lambda jobs, name, tmo: subprocess.run([str(KREA_PY), str(P / "tools/zimage_batch.py"), str(_dump(jobs, name))],
                                                   timeout=tmo).returncode
    v = t2i[0]
    if not Path(v["out"]).exists():   # fail fast: one frame proves the Krea 2 path before 13 stills + 20 clips
        log(f"[verify] Krea 2 frame {Path(v['out']).name}")
        t = time.time()
        try: rc = batch([v], "jobs_verify.json", 25 * 60)
        except subprocess.TimeoutExpired: rc = "timeout 25 min"
        if rc != 0 or not Path(v["out"]).exists():
            log(f"[verify] FAILED rc={rc} after {time.time()-t:.0f}s - stopping before any other stage"); sys.exit(2)
        log(f"[verify] OK in {time.time()-t:.0f}s")
    stop_check()
    todo = [j for j in t2i if not Path(j["out"]).exists()]
    if todo:
        t = time.time()
        try: rc = batch(t2i, "jobs_stills_krea.json", 60 * 60)
        except subprocess.TimeoutExpired: rc = "timeout 60 min"
        log(f"[stills] Krea batch rc={rc}, {len(todo)} stills in {time.time()-t:.0f}s")
    i2i = [j for _, j in copy if j]
    if i2i:
        subprocess.run([str(KREA_PY), str(P / "tools/zimage_batch.py"), str(_dump(i2i, "jobs_stills_i2i.json"))], timeout=60 * 60)
    for rid, j in copy:
        o = V2 / f"stills/full/{rid}.png"
        if not o.exists() and not j: shutil.copy2(P / f"stills/locked_full/{rid}.png", o)
    n = 0
    for rid in RIDS:   # LOCKED = the full still, lanczos to the motion res (832x480), as the original
        f, o = V2 / f"stills/full/{rid}.png", V2 / f"stills/locked/LOCKED_{rid}.png"
        if f.exists() and not o.exists(): Image.open(f).convert("RGB").resize((832, 480), Image.LANCZOS).save(o)
        n += o.exists()
    log(f"[stills] {n}/{len(RIDS)} locked stills ready")
    if n < len(RIDS): log("[stills] missing stills - stopping"); sys.exit(3)

def _dump(jobs, name):
    f = V2 / "logs" / name; json.dump(jobs, open(f, "w"), indent=1); return f

# ---------------- 3. motion: one Kandinsky 6 Pro clip per render ----------------
def run_clips():
    order = sorted(RIDS, key=lambda r: r in LONG)   # 73-frame clips first, the two long ones last
    done = lambda r: (V2 / f"clips/{r}.mp4").exists()
    log(f"[clips] {sum(map(done, RIDS))}/{len(RIDS)} done, K6 i2v 832x480")
    fails = 0   # consecutive failed make-k6 calls; 2 in a row stops the stage instead of burning the whole list
    for rid in order:
        stop_check()
        if done(rid): continue
        r = renders[rid]; still = V2 / f"stills/locked/LOCKED_{rid}.png"
        tries = [(LONG.get(rid, K6_FRAMES / FPS), K6_SEEDS[0]), (K6_FRAMES / FPS, K6_SEEDS[1])]
        while tries:
            dur, seed = tries.pop(0)
            cmd = [str(KREA_PY), str(SF / "bin/make-k6"), "--i2v", str(still), "--res", "832x480", "--duration", f"{dur:.3f}",
                   "--seed", str(seed), "--label", f"ls_v2_{rid}", r["animate"]]
            t = time.time()
            try: p = subprocess.run(cmd, capture_output=True, text=True, timeout=90 * 60); rc = p.returncode; out, err = p.stdout, p.stderr
            except subprocess.TimeoutExpired: rc, out, err = "timeout", "", ""
            m = re.search(r"done in [\d.]+s → (\S+)", out or "")
            secs = time.time() - t
            if rc == 0 and m and Path(m.group(1)).exists():
                o = V2 / f"clips/{rid}.mp4"; shutil.move(m.group(1), o)
                (V2 / f"clips/{rid}.done").write_text(json.dumps({"seed": seed, "secs": round(secs), "frames": nfr(o), "duration_arg": dur,
                    "still": str(still), "animate": r["animate"], "finished": time.strftime("%Y-%m-%d %H:%M:%S"), "engine_log": (err or "")[-400:]}))
                left = sum(not done(x) for x in RIDS)
                log(f"[clips] DONE {rid} ({nfr(o)} frames, seed {seed}) in {secs/60:.1f} min - {len(RIDS)-left}/{len(RIDS)}, {left} left")
                fails = 0; break
            fails += 1
            # 2026-11-01: a forge_guard / mem-gate refusal is "no room yet", not a bad seed: retry the same take
            held = "refused" in (err or "")
            if held: tries.insert(0, (dur, seed))
            log(f"[clips] FAIL {rid} dur {dur:.2f}s seed {seed} rc={rc} after {secs:.0f}s{' (memory guard held it)' if held else ''} :: {(err or '')[-2000:]!r}")
            if fails >= 2:
                log(f"[clips] {fails} make-k6 failures in a row - stopping the clips stage"); sys.exit(4)
    missing = [r for r in RIDS if not done(r)]
    if missing: log(f"[clips] missing {missing} - stopping"); sys.exit(4)

# ---------------- 4. edit: the original EDL re-pointed at the K6 clips ----------------
def run_edit():
    e = json.load(open(P / "final/edl_final.json"))
    tot = {r: nfr(V2 / f"clips/{r}.mp4") for r in RIDS}
    placed = {}
    for c in e["cuts"]:
        c["orig_src"], c["orig_in"] = c["src"], c["in"]
        if not c["src"] or c["section"] == "title":
            if c["src"]: c["src"] = str(P / c["src"])
            continue
        rid = re.search(r"(R\d\d_[a-z_]+)_t\d", c["src"]).group(1); n = c["frames"]; T = tot[rid]
        src = V2 / f"clips/{rid}.mp4"
        if n > T:   # only if a long clip fell back to 73 frames: slow the clip to cover the cut
            k = (n + 1) / T; src = V2 / f"clips/{rid}_stretch.mp4"
            if not src.exists(): ff("-i", V2 / f"clips/{rid}.mp4", "-vf", f"setpts={k:.4f}*PTS,fps={FPS}", "-an", "-c:v", "libx264", "-crf", "6", "-pix_fmt", "yuv420p", src)
            T = nfr(src); c["stretch"] = round(k, 3); log(f"[edit] {c['id']}: {n} frames > {rid}'s clip, slowed x{k:.2f}")
        want = min(round(c["in"] * FPS), T - n)
        if c["section"] != "strobe":   # distinct frames for cuts that shared one render (were different LTX takes)
            busy = placed.setdefault(rid, [])
            ov = lambda f0: sum(max(0, min(f0 + n, b) - max(f0, a)) for a, b in busy)
            want = min(range(0, T - n + 1), key=lambda f0: (ov(f0), abs(f0 - want)))
            busy.append((want, want + n))
        c["src"], c["in"], c["clip_frames"] = str(src), round(want / FPS, 4), T
    e["size"] = [832, 480]; e["engine"] = "Kandinsky 6 Pro i2v (bin/make-k6), stills Krea 2 Turbo"
    json.dump(e, open(V2 / "final/edl_v2.json", "w"), indent=1)
    # cut every segment (+ temporal handles) and the 2.39:1 scope crop SeedVR2 + the 4K finish read
    S = V2 / "final/segs"; meta, lst = [], []
    for k, c in enumerate(e["cuts"]):
        o = S / f"{k:02d}_{c['id']}.mp4"; lst.append(f"file '{o}'")
        if o.exists() and (c["src"] is None or c["section"] == "title" or (S / "scope" / o.name).exists()):
            if c["src"] and c["section"] != "title": meta.append(json.load(open(S / "scope" / (o.stem + ".json"))))
            continue
        if c["src"] is None:
            ff("-f", "lavfi", "-i", f"color=black:s=832x480:r={FPS}", "-frames:v", c["frames"], "-c:v", "libx264", "-crf", "4", "-pix_fmt", "yuv420p", o); continue
        if c["section"] == "title":
            ff("-i", c["src"], "-vf", "scale=832:480:flags=lanczos", "-frames:v", c["frames"], "-c:v", "libx264", "-crf", "4", "-pix_fmt", "yuv420p", o); continue
        f0, n, T = round(c["in"] * FPS), c["frames"], c["clip_frames"]
        ff("-i", c["src"], "-vf", f"select='between(n\\,{f0}\\,{f0+n-1})',setpts=N/{FPS}/TB", "-frames:v", n, "-an",
           "-c:v", "libx264", "-crf", "4", "-pix_fmt", "yuv420p", o)
        h0, h1 = max(0, f0 - 4), min(T - 1, f0 + n - 1 + 4)
        ff("-i", c["src"], "-vf", f"select='between(n\\,{h0}\\,{h1})',setpts=N/{FPS}/TB", "-an", "-c:v", "libx264", "-crf", "4", "-pix_fmt", "yuv420p", S / "h" / o.name)
        ff("-i", S / "h" / o.name, "-vf", "crop=832:348:0:66", "-c:v", "libx264", "-crf", "4", "-pix_fmt", "yuv420p", S / "scope" / o.name)
        m = {"seg": o.name, "pre": f0 - h0, "n": n, "post": h1 - (f0 + n - 1)}
        json.dump(m, open(S / "scope" / (o.stem + ".json"), "w")); meta.append(m)
    (S / "list.txt").write_text("\n".join(lst) + "\n")
    json.dump(meta, open(S / "handles.json", "w"), indent=1)
    ff("-f", "concat", "-safe", "0", "-i", S / "list.txt", "-c:v", "libx264", "-crf", "10", "-pix_fmt", "yuv420p", "-r", FPS, V2 / "final/cut_480.mp4")
    log(f"[edit] {len(e['cuts'])} cuts, {e['duration']:.2f}s, {len(meta)} picture segments, cut_480 {nfr(V2 / 'final/cut_480.mp4')} frames")

# ---------------- 5. SeedVR2-3B upscale (same recipe as tools/seedvr2_batch.py) ----------------
def _thumbs(f, w=208, h=87):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3).astype(np.float32)

def bad_frames(src, up):
    a, b = _thumbs(src), _thumbs(up); k = min(len(a), len(b))
    if len(a) != len(b): return list(range(k, max(len(a), len(b)))) or [0]
    return [int(i) for i in np.where(np.abs(a[:k] - b[:k]).mean(axis=(1, 2, 3)) > 12)[0]]

def songforge_busy():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8767/api/status", timeout=5) as r: return int(json.load(r).get("jobs_running", 0)) > 0
    except Exception: return False

def seedvr(src, out, b, seed):
  try:
    return subprocess.run([str(COMFY_PY), str(P / "tools/seedvr2_run.py"), str(src), "--output", str(out), "--resolution", "720",
                           "--batch_size", str(b), "--uniform_batch_size", "--model_dir", str(COMFY / "models/SEEDVR2"),
                           "--dit_model", "seedvr2_ema_3b_fp16.safetensors", "--video_backend", "ffmpeg", "--color_correction", "lab",
                           "--seed", str(seed)], cwd=str(COMFY), capture_output=True, text=True, timeout=90 * 60)
  except subprocess.TimeoutExpired:
    return subprocess.CompletedProcess([], 124, "", "seedvr2 timeout after 90 min")

def run_upscale():
    sys.path.insert(0, str(HOME / "SongForgeM5"))
    from mem_client import reserve
    e = json.load(open(V2 / "final/edl_v2.json")); S = V2 / "final/segs"
    todo = [(f"{k:02d}_{c['id']}.mp4") for k, c in enumerate(e["cuts"]) if c["src"] and c["section"] != "title" and c["len"] >= 0.9]
    frames = {nm: nfr(S / "scope" / nm) for nm in todo}
    log(f"[upscale] {sum((S / 'up' / nm).exists() for nm in todo)}/{len(todo)} done, {sum(frames.values())} frames total")
    with reserve("seedvr2-3b", 60):
        for i, nm in enumerate(todo, 1):
            stop_check()
            out, src, n = S / "up" / nm, S / "scope" / nm, frames[nm]
            if out.exists(): continue
            while songforge_busy(): print("Song Forge job running, waiting 30s", flush=True); time.sleep(30)
            t = time.time()
            for seed in (42, 7, 1234):
                k = math.ceil(n / 37)   # 11/2: a 49-frame batch on 13_c09_welcome hit ~111 GB and rebooted the M5; 37 is the largest proven batch
                if k >= 3:   # 3 temporal batches came back grey/smeared twice on 10/31 (c04): run as single-batch chunks of <= 57
                    parts = math.ceil(n / 37); per = math.ceil(n / parts); chunks = []
                    for j in range(parts):
                        a, z = j * per, min(n, (j + 1) * per); cs, co = S / "up" / f"chunk{j}_{nm}", S / "up" / f"chunkup{j}_{nm}"
                        ff("-i", src, "-vf", f"select='between(n\\,{a}\\,{z-1})',setpts=N/{FPS}/TB", "-c:v", "libx264", "-crf", "4", "-pix_fmt", "yuv420p", cs)
                        r = seedvr(cs, co, 4 * math.ceil((z - a - 1) / 4) + 1, seed); chunks.append(co); cs.unlink()
                        if r.returncode != 0: print(r.stdout[-1500:], r.stderr[-1500:], flush=True); break
                    if all(x.exists() for x in chunks):
                        (S / "up/chunks.txt").write_text("".join(f"file '{x}'\n" for x in chunks))
                        ff("-f", "concat", "-safe", "0", "-i", S / "up/chunks.txt", "-c:v", "libx264", "-crf", "8", "-pix_fmt", "yuv420p", out)
                    for x in chunks: x.unlink(missing_ok=True)
                    rc = 0 if out.exists() else 1
                else:
                    per = math.ceil(n / k); b = 4 * math.ceil((per - 1) / 4) + 1
                    r = seedvr(src, out, b, seed); rc = r.returncode
                    if rc != 0: print(r.stdout[-1500:], r.stderr[-1500:], flush=True)
                bad = bad_frames(src, out) if rc == 0 and out.exists() else ["no output"]
                log(f"[upscale] {nm}: {n} frames, seed {seed}, rc {rc}, {time.time()-t:.0f}s, bad frames {len(bad)} - {i}/{len(todo)}")
                if not bad: break
                if out.exists(): out.rename(out.with_suffix(f".bad{seed}.mp4"))
    missing = [nm for nm in todo if not (S / "up" / nm).exists()]
    if missing: log(f"[upscale] missing {missing} - stopping"); sys.exit(5)
    # the same captain/crewmate cuts the original face-locked (canon identity, inswapper)
    for k, c in enumerate(e["cuts"]):
        nm = f"{k:02d}_{c['id']}.mp4"
        if c["id"] in FACE_LOCK and (S / "up" / nm).exists() and not (S / "locked" / nm).exists():
            r = subprocess.run([str(COMFY_PY), str(SF / "pipeline-tools/face_lock.py"), str(P), c["id"], str(S / "up" / nm), str(S / "locked" / nm)],
                               capture_output=True, text=True, cwd=str(SF))
            log(f"[face_lock] {c['id']} rc {r.returncode} :: {(r.stdout or r.stderr).strip()[-200:]}")

# ---------------- 6. 4K finish (tools/finish_4k.py recipe) ----------------
COLD = {"c01_asteroids", "c01b_asteroids_close"}
BLOOM = {
 "c01_asteroids": .55, "c01b_asteroids_close": .55, "c03_dive": .7, "c03b_dive_clouds": .6, "c04_arrival": .6,
 "c05_claws": .45, "c07_handwriting": .6, "c07b_captain_face": .35, "c08_lightwave": .7, "c09_welcome": .45,
 "c10_second_sun": .6, "c10b_second_sun": .5, "c12_engines": .75, "c12b_engines": .75, "c13_mountain": .45, "c13b_mountain": .45,
 "c14_boots": .6, "c14c_boots": .6, "c15_grab": .7, "c15b_grab": .6, "c02a_cockpit": .4, "c02b_lever": .5,
}
GRAIN = 0.12
FW, FH, VH, BAR = 3840, 2160, 1608, 276

def bloom_chain(s):
    return (f"split=3[o][h1][h2];"
            f"[h1]curves=all='0/0 0.70/0 1/1',gblur=sigma=34[g];"
            f"[h2]curves=all='0/0 0.86/0 1/1',gblur=sigma=90:sigmaV=1.5,colorchannelmixer=rr=0.45:gg=0.85:bb=1.0[st];"
            f"[o][g]blend=all_mode=screen:all_opacity={0.55*s:.3f}[ob];[ob][st]blend=all_mode=screen:all_opacity={0.9*s:.3f}")

def run_finish():
    e = json.load(open(V2 / "final/edl_v2.json")); S = V2 / "final/segs"; OUT = S / "4k"
    H = {m["seg"]: m for m in json.load(open(S / "handles.json"))}
    lst = []
    for k, c in enumerate(e["cuts"]):
        stop_check()
        nm = f"{k:02d}_{c['id']}.mp4"; o = OUT / nm; lst.append(f"file '{o}'")
        if c["src"] is None or c["section"] == "title":
            if not o.exists():
                inp = ["-f", "lavfi", "-i", f"color=black:s={FW}x{FH}:r={FPS}"] if c["src"] is None else ["-i", c["src"], "-vf", f"scale={FW}:{FH}:flags=lanczos"]
                ff(*inp, "-frames:v", c["frames"], "-r", FPS, "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", o)
            continue
        m = H[nm]; lut = "cold_space_teal" if c["id"] in COLD else "teal_orange_blockbuster"
        src, sharpen = S / "up" / nm, ""
        if not src.exists():
            src, sharpen = S / "scope" / nm, ",unsharp=5:5:0.6:5:5:0.0"
        c["upscale"] = "seedvr2-3b 720p + lanczos" if not sharpen else "lanczos + unsharp"
        if (S / "locked" / nm).exists(): src = S / "locked" / nm; c["face_lock"] = True
        c["lut"] = lut; c["bloom"] = BLOOM.get(c["id"], 0.5 if c["section"] == "strobe" else 0)
        if o.exists(): continue
        f = (f"[0:v]trim=start_frame={m['pre']}:end_frame={m['pre']+m['n']},setpts=N/{FPS}/TB,"
             f"scale={FW}:{VH}:flags=lanczos{sharpen},format=gbrp")
        if c["id"] in BLOOM or c["section"] == "strobe": f += "," + bloom_chain(BLOOM.get(c["id"], 0.5))
        f += f",format=yuv420p,pad={FW}:{FH}:0:{BAR}:black[v]"
        pre = OUT / ("pre_" + nm)
        ff("-i", src, "-filter_complex", f, "-map", "[v]", "-frames:v", m["n"], "-r", FPS, "-c:v", "libx264", "-crf", "12",
           "-preset", "medium", "-pix_fmt", "yuv420p", pre)
        subprocess.run([str(SF / "bin/grade"), str(pre), str(o), "--lut", lut, "--grain", str(GRAIN), "--scope"], check=True)
        pre.unlink()
        log(f"[finish] {nm} ({c['upscale']}{', face-locked' if c.get('face_lock') else ''}) - {k+1}/{len(e['cuts'])}")
    (OUT / "list.txt").write_text("\n".join(lst) + "\n")
    ff("-f", "concat", "-safe", "0", "-i", OUT / "list.txt", "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", FPS, V2 / "final/picture_4k.mp4")
    json.dump(e, open(V2 / "final/edl_v2_graded.json", "w"), indent=1)
    log(f"[finish] picture_4k {nfr(V2 / 'final/picture_4k.mp4')} frames")

# ---------------- 7. deliver (tools/deliver.py muxes, original mix) ----------------
def run_deliver():
    F = V2 / "final"; pic = F / "picture_4k.mp4"; mix = SF / "bin/surround-mix"; plan = P / "sfx/mix_plan.json"
    subprocess.run([str(mix), str(plan), "--out", str(F / "mix_51.wav"), "--stereo", str(F / "mix_stereo.wav"), "--no-loudnorm"], check=True)
    ff("-i", pic, "-i", F / "mix_stereo.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
       "-movflags", "+faststart", "-metadata", "title=THE LAST SIGNAL", F / "LAST_SIGNAL_v2.mp4")
    subprocess.run([str(mix), str(plan), "--out", str(F / "mix_51.wav"), "--stereo", str(F / "mix_stereo.wav"), "--no-loudnorm",
                    "--codec", "eac3", "--video", str(F / "LAST_SIGNAL_v2.mp4"), "--mux", str(F / "LAST_SIGNAL_v2_51.mp4")], check=True)
    ff("-i", F / "LAST_SIGNAL_v2.mp4", "-vf", "scale=1920:1080:flags=lanczos", "-c:v", "libx264", "-crf", "17", "-preset", "slow",
       "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", F / "LAST_SIGNAL_v2_1080p.mp4")
    for f in ("LAST_SIGNAL_v2.mp4", "LAST_SIGNAL_v2_51.mp4", "LAST_SIGNAL_v2_1080p.mp4"):
        o = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name,width,height,channels",
                                     "-of", "compact", str(F / f)]).decode()
        log(f"[deliver] {f} {o.strip().replace(chr(10), ' | ')}")

STAGES = [("stills", run_stills), ("clips", run_clips), ("edit", run_edit), ("upscale", run_upscale), ("finish", run_finish), ("deliver", run_deliver)]
if __name__ == "__main__":
    log(f"=== THE LAST SIGNAL v2 redo start (Krea 2 stills, K6 motion, SeedVR2-3B) -> {V2}")
    for name, fn in STAGES:
        mark = V2 / f"logs/STAGE_DONE_{name}"
        if mark.exists() and name not in ("stills", "clips"): continue
        t = time.time(); log(f"--- stage {name}")
        fn(); mark.write_text(time.strftime("%Y-%m-%d %H:%M:%S"))
        log(f"--- stage {name} done in {(time.time()-t)/60:.1f} min (total {(time.time()-T0)/60:.0f} min)")
    (V2 / "logs/REDO_V2_FINISHED").write_text(time.strftime("%Y-%m-%d %H:%M:%S"))
    log(f"=== DONE: {V2 / 'final/LAST_SIGNAL_v2.mp4'} in {(time.time()-T0)/3600:.2f} h")
