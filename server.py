"""
videopipe.server — Flask UI backend for the MakeVideo app.

Endpoints:
  GET  /                 — HTML UI
  POST /api/render       — start a render job  {prompt, duration, quality, resolution} -> {job_id}
  GET  /api/status/<id>  — poll progress        -> {state, step, total_steps, eta, mp4}
  POST /api/cancel/<id>  — kill in-progress
  GET  /api/output/<name>— serve a produced mp4
  GET  /api/estimate     — time estimate for params
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, send_from_directory, send_file, Response

sys.path.insert(0, str(Path(__file__).resolve().parent))
from core import (
    build_wan22_t2v, build_wan22_t2v_gguf, build_wan22_i2v, upload_image,
    queue_prompt, wait_for, collect_outputs,
    wan22_ready, wan22_gguf_ready, pick_best_t2v, pick_best_i2v,
    _post, _get, OUT_DIR, COMFY_URL,
)

app = Flask(__name__, static_folder=None)
UI_DIR = Path(__file__).resolve().parent / "ui"


# ───────────────────── Job tracking ─────────────────────

JOBS: dict[str, dict[str, Any]] = {}
JOB_LOCK = threading.Lock()


def _update_job(job_id: str, **fields):
    with JOB_LOCK:
        if job_id in JOBS:
            JOBS[job_id].update(fields)


def _progress_watcher(job_id: str, prompt_id: str, expected_steps: int):
    """Poll ComfyUI /history and track stages: loading → sampling → decoding → saving."""
    t0 = time.time()
    dead_polls = 0  # consecutive unreachable-ComfyUI polls; ~60s of them = it crashed
    while True:
        with JOB_LOCK:
            job = JOBS.get(job_id, {})
        if job.get("state") in ("cancelled", "error", "done"):
            return
        try:
            hist = _get(f"/history/{prompt_id}")
            dead_polls = 0
            entry = hist.get(prompt_id)
            if entry and entry.get("status", {}).get("completed"):
                files = collect_outputs(entry, job_id[:8])
                mp4 = str(files[0]) if files else None
                mp4_name = Path(mp4).name if mp4 else None
                _update_job(job_id, state="done", step=expected_steps,
                            stage="done", pct=100,
                            mp4=mp4, mp4_name=mp4_name,
                            elapsed=time.time() - t0, eta=0)
                return
            if entry and entry.get("status", {}).get("status_str") == "error":
                _update_job(job_id, state="error", stage="error",
                            error=str(entry.get("status", {})))
                return

            dt = time.time() - t0
            total_est = job.get("total_s", 300)
            sec_per_step = job.get("sec_per_step", 60)
            load_s = job.get("load_s", 50)
            setup_s = job.get("setup_s", 20)
            vae_s = job.get("vae_decode_s", 45)

            sampling_start = load_s + setup_s
            sampling_end = sampling_start + expected_steps * sec_per_step
            decode_end = sampling_end + vae_s

            # Determine current stage + fractional progress
            if dt < sampling_start:
                stage = "warming up"
                step = 0
            elif dt < sampling_end:
                stage = "sampling"
                step = min(expected_steps,
                           int((dt - sampling_start) / max(1, sec_per_step)) + 1)
            elif dt < decode_end:
                stage = "decoding video"
                step = expected_steps
            else:
                stage = "saving"
                step = expected_steps

            pct = min(99, int(dt / max(1, total_est) * 100))
            eta = max(0, int(total_est - dt))
            _update_job(job_id, step=step, stage=stage, pct=pct,
                        elapsed=int(dt), eta=eta)
        except Exception:
            # ComfyUI unreachable. A model load can stall the HTTP thread for a
            # bit, but a full minute of silence means the process died — fail the
            # job instead of reporting "running" forever (2026-07-22).
            dead_polls += 1
            if dead_polls >= 40:
                _update_job(job_id, state="error", stage="error",
                            error="ComfyUI stopped responding mid-render "
                                  "(likely crashed) — check logs/comfyui.log")
                return
        time.sleep(1.5)


def _ensure_comfyui() -> bool:
    import urllib.request, urllib.error
    try:
        urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=2)
        return True
    except Exception:
        pass
    comfy_log = open(Path(__file__).resolve().parent / "logs" / "comfyui.log", "a")
    subprocess.Popen(
        ["bash", str(Path.home() / "AI/ComfyUI/start.sh")],
        stdout=comfy_log, stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    for _ in range(120):
        try:
            urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


def _estimate(duration: float, quality: str, resolution: str, big_mode: bool = False) -> dict:
    """Return seconds estimate for all stages on M5 Max MPS, including a
    feasibility check based on memory headroom.

    Two memory profiles:
      Standard (FP16): ~82 GB baseline, ~45 GB for activations
      Big mode (GGUF Q6_K): ~52 GB baseline, ~75 GB for activations
    """
    fps = 16
    length = max(1, int(duration * fps))
    length = (length // 4) * 4 + 1
    w, h = (int(x) for x in resolution.lower().split("x"))

    pix = w * h * length
    base_pix = 720 * 480 * 49
    ratio = pix / base_pix

    # GGUF dequant adds ~15% per-step overhead but the freed memory is the win
    step_factor = 1.15 if big_mode else 1.0
    sec_per_step = 50.0 * ratio * step_factor
    vae_decode_s = 45.0 * ratio
    load_s = 60.0 if big_mode else 50.0
    setup_s = 20.0

    steps = 4 if quality == "fast" else (20 if quality == "hq" else 10)
    total = steps * sec_per_step + vae_decode_s + load_s + setup_s

    # Empirical feasibility matrix:
    #   FP16 standard mode: 720×480 × 81f confirmed works, 145f exhausts mem
    #     → ~46 GB available for activations
    #   GGUF Q6_K big mode: model RAM drops 54→24 GB
    #     → ~76 GB available for activations = 1.65× more headroom
    safe_limit_std = 720 * 480 * 81
    safe_limit_big = int(safe_limit_std * 1.65)
    safe_limit = safe_limit_big if big_mode else safe_limit_std
    warn_limit = safe_limit * 0.85
    feasible = pix <= safe_limit * 1.02
    warning = None
    if not feasible:
        max_frames_here = int(safe_limit / (w * h))
        max_secs = round(max_frames_here / fps, 1)
        if big_mode:
            warning = (f"Even Big Video Mode caps {w}×{h} at ~{max_secs}s. "
                       f"Drop the resolution or duration.")
        else:
            warning = (f"Too big for standard mode — max at {w}×{h} is ~{max_secs}s. "
                       f"Try Big Video Mode (GGUF) for longer/larger clips.")
    elif pix >= warn_limit:
        warning = "Cutting it close — close Chrome tabs + other heavy apps before rendering."

    if big_mode:
        mem_peak_gb = 47.0 + 22.0 * (pix / base_pix)
    else:
        mem_peak_gb = 72.0 + 22.0 * (pix / base_pix)

    return {
        "steps": steps,
        "sec_per_step": sec_per_step,
        "vae_decode_s": int(vae_decode_s),
        "load_s": int(load_s),
        "setup_s": int(setup_s),
        "total_s": int(total),
        "length_frames": length,
        "width": w, "height": h,
        "mem_peak_gb": round(mem_peak_gb, 1),
        "feasible": feasible,
        "warning": warning,
        "big_mode": big_mode,
        "big_mode_available": wan22_gguf_ready(),
    }


# ───────────────────── Routes ─────────────────────

@app.route("/")
def index():
    # The Director (chat + storyboard) is the front door now; the old
    # single-clip MakeVideo page lives on at /classic.
    return send_from_directory(UI_DIR, "director.html")


@app.route("/classic")
def classic_page():
    return send_from_directory(UI_DIR, "index.html")


@app.route("/story")
def story_page():
    return send_from_directory(UI_DIR, "story.html")


@app.route("/story-classic")
def story_classic_page():
    """Legacy form-driven Story Forge UI (pre-DSL era).

    The new DSL-first UI lives at /story; this route preserves the old form
    workflow for anyone still wired to it.
    """
    return send_from_directory(UI_DIR, "story-classic.html")


@app.route("/static/<path:p>")
def static_files(p):
    return send_from_directory(UI_DIR, p)


@app.route("/api/story", methods=["POST"])
def api_story():
    """Spawn the story pipeline with the posted JSON config.
    Pipeline writes status to /tmp/mks-status.json, output to ~/Desktop/AI Videos/<slug>/<slug>.mp4."""
    import json as _json
    import subprocess as _sp
    import tempfile as _tmp
    from pathlib import Path as _P
    cfg = request.get_json(force=True, silent=True)
    if not cfg:
        return jsonify({"error": "no JSON config"}), 400
    slug = cfg.get("slug", "untitled-story")
    scenes = cfg.get("scenes", [])
    if not scenes:
        return jsonify({"error": "no scenes"}), 400

    # Write config to a temp file so the subprocess can read it
    cfg_file = _P(_tmp.gettempdir()) / f"story_{slug}.json"
    cfg_file.write_text(_json.dumps(cfg))

    pipeline = _P(__file__).resolve().parent / "story_pipeline.py"
    log = _P(_tmp.gettempdir()) / f"story_{slug}.log"

    # Detach so the request returns immediately
    proc = _sp.Popen(
        ["python3", str(pipeline), "--config", str(cfg_file)],
        stdout=open(log, "w"), stderr=_sp.STDOUT,
        start_new_session=True,
    )
    output = str(_P.home() / "Desktop" / "AI Videos" / slug / f"{slug}.mp4")
    return jsonify({"pid": proc.pid, "output": output, "log": str(log)})


@app.route("/api/estimate")
def api_estimate():
    duration = float(request.args.get("duration", 5))
    quality = request.args.get("quality", "fast")
    resolution = request.args.get("resolution", "720x480")
    big_mode = request.args.get("big_mode", "0") in ("1", "true", "True")
    return jsonify(_estimate(duration, quality, resolution, big_mode))


@app.route("/api/upload", methods=["POST"])
def api_upload():
    """Receive an image from the browser and forward it to ComfyUI.
    Returns the ComfyUI-side filename a LoadImage node can reference.
    """
    f = request.files.get("image")
    if not f:
        return jsonify({"error": "no image"}), 400
    if not _ensure_comfyui():
        return jsonify({"error": "could not start ComfyUI"}), 500

    suffix = Path(f.filename or "upload.png").suffix or ".png"
    tmp = OUT_DIR / f"_upload_{uuid.uuid4().hex[:8]}{suffix}"
    f.save(str(tmp))
    try:
        comfy_name = upload_image(tmp)
    except Exception as e:
        return jsonify({"error": f"upload failed: {e}"}), 500
    finally:
        try: tmp.unlink()
        except Exception: pass
    return jsonify({"name": comfy_name})


@app.route("/api/render", methods=["POST"])
def api_render():
    data = request.get_json(force=True)
    # If the payload carries a .sf script, dispatch to the DSL render path.
    # Otherwise fall through to the legacy single-clip prompt path.
    if isinstance(data, dict) and (data.get("sf") or "").strip():
        return _api_render_sf(data)
    prompt = (data.get("prompt") or "").strip()
    image_name = (data.get("image_name") or "").strip() or None
    if not prompt:
        return jsonify({"error": "prompt required"}), 400
    duration = float(data.get("duration", 5))
    quality = data.get("quality", "fast")
    resolution = data.get("resolution", "720x480")
    big_mode = bool(data.get("big_mode", False))

    if not _ensure_comfyui():
        return jsonify({"error": "could not start ComfyUI"}), 500

    if big_mode and not wan22_gguf_ready():
        return jsonify({"error": "Big Video Mode weights still downloading — try again in a few minutes."}), 400

    try:
        if image_name:
            pick_best_i2v()
        else:
            pick_best_t2v()
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 400

    est = _estimate(duration, quality, resolution, big_mode)
    if not est["feasible"]:
        return jsonify({
            "error": f"Won't fit in memory (projected {est['mem_peak_gb']}GB peak). "
                     "Reduce duration or resolution and try again.",
            "estimate": est,
        }), 400
    w = est["width"]; h = est["height"]; length = est["length_frames"]

    if image_name:
        wf = build_wan22_i2v(
            prompt=prompt, image_filename=image_name,
            width=w, height=h, length=length,
            fast=(quality != "hq"),
        )
    elif big_mode:
        wf = build_wan22_t2v_gguf(
            prompt=prompt, width=w, height=h, length=length,
            fast=(quality != "hq"),
        )
    else:
        wf = build_wan22_t2v(
            prompt=prompt, width=w, height=h, length=length,
            fast=(quality != "hq"),
        )

    try:
        prompt_id = queue_prompt(wf)
    except Exception as e:
        return jsonify({"error": f"submit failed: {e}"}), 500

    job_id = uuid.uuid4().hex[:12]
    with JOB_LOCK:
        JOBS[job_id] = {
            "state": "running", "stage": "warming up", "prompt": prompt,
            "duration": duration, "quality": quality, "resolution": resolution,
            "step": 0, "total_steps": est["steps"], "pct": 0,
            "eta": est["total_s"], "elapsed": 0,
            "sec_per_step": est["sec_per_step"],
            "vae_decode_s": est["vae_decode_s"],
            "load_s": est["load_s"], "setup_s": est["setup_s"],
            "total_s": est["total_s"],
            "prompt_id": prompt_id, "started_at": time.time(),
            "mp4": None, "mp4_name": None, "error": None,
        }
    threading.Thread(
        target=_progress_watcher,
        args=(job_id, prompt_id, est["steps"]),
        daemon=True,
    ).start()

    return jsonify({"job_id": job_id, "estimate_s": est["total_s"]})


@app.route("/api/status/<job_id>")
def api_status(job_id):
    with JOB_LOCK:
        job = JOBS.get(job_id)
        if not job:
            return jsonify({"error": "not found"}), 404
        return jsonify({k: v for k, v in job.items() if k != "prompt_id"})


@app.route("/api/cancel/<job_id>", methods=["POST"])
def api_cancel(job_id):
    with JOB_LOCK:
        job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "not found"}), 404
    # Try to delete from ComfyUI queue
    try:
        _post("/queue", {"delete": [job["prompt_id"]]})
    except Exception:
        pass
    # Interrupt current
    try:
        _post("/interrupt", {})
    except Exception:
        pass
    _update_job(job_id, state="cancelled")
    return jsonify({"ok": True})


@app.route("/api/output/<name>")
def api_output(name):
    # prevent directory traversal
    if "/" in name or ".." in name:
        return "no", 400
    p = OUT_DIR / name
    if not p.is_file():
        return "not found", 404
    return send_file(str(p), mimetype="video/mp4")


@app.route("/api/kill_all", methods=["POST"])
def api_kill_all():
    """Nuclear option: kill ComfyUI to free memory."""
    subprocess.run(["pkill", "-9", "-f", "main.py"], check=False)
    return jsonify({"ok": True})


@app.route("/api/reveal/<name>", methods=["POST"])
def api_reveal(name):
    """Open Finder with the mp4 highlighted."""
    if "/" in name or ".." in name:
        return "no", 400
    p = OUT_DIR / name
    if not p.is_file():
        return "not found", 404
    subprocess.run(["open", "-R", str(p)], check=False)
    return jsonify({"ok": True})


# ───────────────────── make-short-video live status ─────────────────────

MKS_STATUS_PATH = Path("/tmp/mks-status.json")


@app.route("/short")
def short_status_page():
    """Serve the make-short-video live status page."""
    return send_file(UI_DIR / "short-status.html")


@app.route("/build_status/live.json")
def build_status_live():
    """Expose the build_status ticker json to the Story Forge UI."""
    p = Path(__file__).resolve().parent / "build_status" / "live.json"
    if not p.is_file():
        return jsonify({}), 404
    return send_file(str(p), mimetype="application/json")


@app.route("/api/recent_renders")
def api_recent_renders():
    """List recent finished films from ~/Desktop/AI Videos/<slug>/<slug>.mp4.
    Returns [{slug, mp4_path, mtime, duration_s}] newest first, capped at 24."""
    import glob as _glob
    base = Path.home() / "Desktop" / "AI Videos"
    out = []
    if base.is_dir():
        for d in sorted(base.iterdir(), key=lambda x: x.stat().st_mtime if x.exists() else 0, reverse=True):
            if not d.is_dir():
                continue
            mp4 = d / f"{d.name}.mp4"
            if not mp4.is_file():
                cands = sorted(d.glob("*.mp4"), key=lambda x: x.stat().st_mtime, reverse=True)
                if not cands:
                    continue
                mp4 = cands[0]
            dur = 0.0
            try:
                r = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "default=noprint_wrappers=1:nokey=1", str(mp4)],
                    capture_output=True, text=True, timeout=4)
                dur = float((r.stdout or "0").strip() or 0)
            except Exception:
                pass
            out.append({
                "slug": d.name,
                "mp4_path": str(mp4),
                "mtime": int(mp4.stat().st_mtime),
                "duration_s": round(dur, 2),
            })
            if len(out) >= 24:
                break
    return jsonify(out)


@app.route("/api/sf_render", methods=["POST"])
def api_sf_render():
    """Compile a posted .sf DSL script to a storyplan and kick off Story Forge render.

    Body: {"script": "<.sf text>", "slug": "optional override"}
    """
    import json as _json
    import subprocess as _sp
    import tempfile as _tmp
    from pathlib import Path as _P
    data = request.get_json(force=True, silent=True) or {}
    script = data.get("script", "").strip()
    if not script:
        return jsonify({"error": "empty script"}), 400

    try:
        from story_forge.parser import parse as _sf_parse
        from story_forge.resolver import resolve as _sf_resolve
    except Exception as e:
        return jsonify({"error": f"story_forge import failed: {e}"}), 500

    try:
        ast = _sf_parse(script)
        plan = _sf_resolve(ast)
    except Exception as e:
        return jsonify({"error": f"parse/resolve failed: {e}"}), 400

    slug = data.get("slug") or plan.get("slug") or "untitled-sf"
    tmp_plan = _P(_tmp.gettempdir()) / f"sf_{slug}.storyplan.json"
    tmp_plan.write_text(_json.dumps(plan))

    runner = _P(__file__).resolve().parent / "story_forge" / "run.py"
    log = _P(_tmp.gettempdir()) / f"sf_{slug}.log"
    proc = _sp.Popen(
        ["python3", str(runner), str(tmp_plan)],
        stdout=open(log, "w"), stderr=_sp.STDOUT,
        start_new_session=True,
    )
    return jsonify({
        "pid": proc.pid,
        "slug": slug,
        "plan_path": str(tmp_plan),
        "log": str(log),
    })


@app.route("/api/short-status")
def api_short_status():
    """Return the current make-short-video pipeline status plus live ComfyUI
    sampler progress (so the page can render a real % bar for the active clip)."""
    if MKS_STATUS_PATH.is_file():
        try:
            state = json.loads(MKS_STATUS_PATH.read_text())
        except Exception:
            state = {"phase": "unknown"}
    else:
        state = {"phase": "idle"}

    # Bolt on live ComfyUI queue info (helps for ai_broll Wan jobs).
    try:
        q = _get("/queue")
        state["comfy_queue"] = {
            "running": len(q.get("queue_running") or []),
            "pending": len(q.get("queue_pending") or []),
        }
    except Exception:
        state["comfy_queue"] = {"running": 0, "pending": 0, "unreachable": True}

    return jsonify(state)


# ───────────────────── .sf DSL render jobs (new UI) ─────────────────────

SF_JOBS: dict[str, dict[str, Any]] = {}
SF_LOCK = threading.Lock()
SF_EXAMPLES_DIR = Path(__file__).resolve().parent / "story_forge" / "examples"
SF_BIN = Path(__file__).resolve().parent / "bin" / "sf"


def _sf_estimate(sf_text: str, overrides: dict) -> dict:
    """Mirror of the in-browser ETA formula.

    Per-scene engine cost (seconds):
      ltx                                : 120
      wan + metal_flash (toggle on)      : 300
      wan (default)                      : 600
      any scene when mini_q4 toggle on   : 2400
    """
    import re
    scenes = len(re.findall(r"^scene\s+\w+", sf_text, flags=re.M))
    motion_engines = re.findall(r"^\s*motion\s+(\w+)\s*:", sf_text, flags=re.M)
    use_mini = bool(overrides.get("mini_q4"))
    use_metal = bool(overrides.get("metal_flash", True))
    total = 0
    for i in range(scenes):
        eng = motion_engines[i] if i < len(motion_engines) else "wan"
        if use_mini:
            total += 2400
        elif eng == "ltx":
            total += 120
        elif eng == "ltx2":
            total += 240  # MLX LTX-2 distilled; video+audio, heavier than old LTX
        elif eng == "wan" and use_metal:
            total += 300
        else:
            total += 600
    return {"total_s": int(total), "scenes": scenes}


def _sf_log_tail(log_path: Path, n: int = 12) -> str:
    if not log_path.is_file():
        return ""
    try:
        with open(log_path, "rb") as f:
            try:
                f.seek(-4096, 2)
            except OSError:
                f.seek(0)
            data = f.read().decode("utf-8", errors="replace")
        lines = [l for l in data.splitlines() if l.strip()]
        return "\n".join(lines[-n:])
    except Exception:
        return ""


def _sf_runner(job_id: str, sf_path: Path, out_path: Path, log_path: Path, env: dict):
    """Background thread: run `bin/sf render <sf> --out <mp4>` and track status."""
    import subprocess as _sp
    t0 = time.time()
    full_env = os.environ.copy()
    full_env.update(env)
    try:
        with open(log_path, "w") as logf:
            proc = _sp.Popen(
                [sys.executable, str(SF_BIN), "render", str(sf_path), "--out", str(out_path)],
                stdout=logf, stderr=_sp.STDOUT, env=full_env,
                start_new_session=True,
            )
            with SF_LOCK:
                SF_JOBS[job_id]["pid"] = proc.pid
            rc = proc.wait()
        elapsed = int(time.time() - t0)
        with SF_LOCK:
            j = SF_JOBS.get(job_id)
            if j is not None:
                j["elapsed_s"] = elapsed
                if rc == 0 and out_path.is_file():
                    j["state"] = "done"
                    j["mp4"] = str(out_path)
                    j["mp4_name"] = out_path.name
                else:
                    j["state"] = "error"
                    j["error"] = f"sf render exited with code {rc}"
    except Exception as e:
        with SF_LOCK:
            j = SF_JOBS.get(job_id)
            if j is not None:
                j["state"] = "error"
                j["error"] = str(e)


def _api_render_sf(data: dict):
    """Handler for POST /api/render when payload carries a .sf script."""
    sf_text = (data.get("sf") or "").strip()
    overrides = data.get("overrides") or {}
    if not sf_text:
        return jsonify({"error": ".sf body empty"}), 400
    if not SF_BIN.is_file():
        return jsonify({"error": f"sf CLI missing at {SF_BIN}"}), 500

    job_id = uuid.uuid4().hex[:12]
    sf_path = Path(f"/tmp/sf_run_{job_id}.sf")
    out_path = Path(f"/tmp/sf_out_{job_id}.mp4")
    log_path = Path(f"/tmp/sf_run_{job_id}.log")
    sf_path.write_text(sf_text)

    est = _sf_estimate(sf_text, overrides)

    # Wire engine toggles into env vars the sf CLI / render-route honor.
    env = {}
    if overrides.get("metal_flash", True):
        env["WAN_METAL_FUSED"] = "1"
    else:
        env["WAN_METAL_FUSED"] = "0"
    if overrides.get("mini_q4"):
        env["SF_USE_MINI_Q4"] = "1"
    if overrides.get("quality_gate", True):
        env["SF_QUALITY_GATE"] = "1"
    if overrides.get("voice_clone", True):
        env["SF_VOICE_CLONE"] = "1"

    with SF_LOCK:
        SF_JOBS[job_id] = {
            "state": "running",
            "sf_path": str(sf_path),
            "out_path": str(out_path),
            "log_path": str(log_path),
            "eta_s": est["total_s"],
            "scenes": est["scenes"],
            "started_at": time.time(),
            "mp4": None,
            "mp4_name": None,
            "error": None,
            "elapsed_s": 0,
        }

    threading.Thread(
        target=_sf_runner,
        args=(job_id, sf_path, out_path, log_path, env),
        daemon=True,
    ).start()

    return jsonify({"job_id": job_id, "eta_s": est["total_s"], "scenes": est["scenes"]})


@app.route("/api/render/<job_id>/status")
def api_render_sf_status(job_id):
    with SF_LOCK:
        j = SF_JOBS.get(job_id)
        if not j:
            return jsonify({"error": "not found"}), 404
        snapshot = dict(j)
    snapshot["elapsed_s"] = int(time.time() - snapshot["started_at"]) if snapshot["state"] == "running" else snapshot.get("elapsed_s", 0)
    snapshot["tail"] = _sf_log_tail(Path(snapshot["log_path"]))
    return jsonify(snapshot)


@app.route("/api/example/<name>")
def api_example(name):
    if "/" in name or ".." in name:
        return "no", 400
    p = SF_EXAMPLES_DIR / name
    if not p.is_file():
        return "not found", 404
    return Response(p.read_text(), mimetype="text/plain")


@app.route("/api/packs")
def api_packs():
    """Style + format packs, straight from story_forge/packs.py (one source of
    truth). The UI fetches this to populate the Styles & Formats picker, so a
    new pack added in packs.py shows up in the editor automatically."""
    try:
        from story_forge import packs as _packs
    except Exception as e:  # pragma: no cover - import guard
        return jsonify({"error": f"packs import failed: {e}"}), 500
    return jsonify({"styles": _packs.list_styles(),
                    "formats": _packs.list_formats()})


@app.route("/api/live")
def api_live():
    """Serve the build_status/live.json ticker payload to the Story Forge UI."""
    live_path = Path(__file__).resolve().parent / "build_status" / "live.json"
    if not live_path.is_file():
        return jsonify({"error": "ticker not running"}), 503
    try:
        return Response(live_path.read_text(), mimetype="application/json")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


_DURATION_CACHE: dict[str, tuple[float, float]] = {}


def _probe_duration(p: Path) -> float:
    """Best-effort ffprobe duration in seconds, cached by (path, mtime)."""
    try:
        mtime = p.stat().st_mtime
    except Exception:
        return 0.0
    cached = _DURATION_CACHE.get(str(p))
    if cached and cached[0] == mtime:
        return cached[1]
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
            capture_output=True, text=True, timeout=4,
        )
        dur = float((r.stdout or "0").strip() or 0)
    except Exception:
        dur = 0.0
    _DURATION_CACHE[str(p)] = (mtime, dur)
    return dur


@app.route("/api/recent")
def api_recent():
    """List the last 6 .mp4 files in OUT_DIR with size, mtime, and film
    duration (so the UI can render film length in MM:SS, not raw seconds)."""
    if not OUT_DIR.is_dir():
        return jsonify({"items": []})
    mp4s = sorted(OUT_DIR.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)[:6]
    now = time.time()
    items = []
    for p in mp4s:
        st = p.stat()
        age_s = int(now - st.st_mtime)
        if age_s < 60:
            age = f"{age_s}s ago"
        elif age_s < 3600:
            age = f"{age_s // 60}m ago"
        elif age_s < 86400:
            age = f"{age_s // 3600}h ago"
        else:
            age = f"{age_s // 86400}d ago"
        items.append({
            "name": p.name,
            "size_mb": st.st_size / 1024 / 1024,
            "mtime": st.st_mtime,
            "age": age,
            "duration_s": round(_probe_duration(p), 2),
        })
    return jsonify({"items": items})


THUMB_CACHE = Path("/tmp/story_forge_thumbs")
THUMB_CACHE.mkdir(exist_ok=True)


@app.route("/thumb/<name>.jpg")
def api_thumb(name):
    """Extract frame at t=1.0s from OUT_DIR/<name> via ffmpeg, cache as JPEG."""
    if "/" in name or ".." in name:
        return "no", 400
    src = OUT_DIR / name
    if not src.is_file():
        return "not found", 404
    thumb = THUMB_CACHE / (name + ".jpg")
    if not thumb.is_file() or thumb.stat().st_mtime < src.stat().st_mtime:
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-ss", "1.0", "-i", str(src),
                 "-frames:v", "1", "-vf", "scale=480:-2", "-q:v", "5", str(thumb)],
                check=True, capture_output=True, timeout=20,
            )
        except Exception:
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-i", str(src),
                     "-frames:v", "1", "-vf", "scale=480:-2", "-q:v", "5", str(thumb)],
                    check=True, capture_output=True, timeout=20,
                )
            except Exception:
                return "thumb failed", 500
    return send_file(str(thumb), mimetype="image/jpeg")


import director
director.register(app, UI_DIR)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 17600))
    print(f"MakeVideo UI → http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
