"""
videopipe.core — Thin client around ComfyUI + workflow builders for Wan 2.2.

Design:
- Talk to ComfyUI HTTP API (default http://127.0.0.1:8188).
- Build API-format workflow dicts programmatically (no fragile JSON templates).
- Poll until done, download outputs, return local paths.
"""

from __future__ import annotations
import json
import os
import sys
import time
import uuid
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from typing import Any

COMFY_URL = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")
OUT_DIR = Path(os.environ.get("VIDEOPIPE_OUT", str(Path.home() / "AI/videopipe/outputs")))
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ───────────────────── ComfyUI HTTP client ─────────────────────

def _post(path: str, body: dict) -> dict:
    req = urllib.request.Request(
        f"{COMFY_URL}{path}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def _get(path: str) -> dict:
    with urllib.request.urlopen(f"{COMFY_URL}{path}", timeout=30) as r:
        return json.loads(r.read())


def _download(path: str, dest: Path) -> Path:
    with urllib.request.urlopen(f"{COMFY_URL}{path}", timeout=300) as r:
        dest.write_bytes(r.read())
    return dest


def queue_prompt(workflow: dict, client_id: str | None = None) -> str:
    """Submit workflow, return prompt_id. Passes the memory gate first —
    queue_prompt is the ONE choke point every render path shares (run_workflow,
    server.py jobs, ad-hoc scripts), so the gate lives here.

    Order matters: never start a render on top of a customer's song, then evict
    what this workflow cannot coexist with, and only then let mem-gate judge what
    is left. The dam runs before the mop."""
    wait_for_customers()
    prepare_for_stage(_workflow_model_gb(workflow), "queue_prompt")
    memory_gate("queue_prompt")
    client_id = client_id or str(uuid.uuid4())
    resp = _post("/prompt", {"prompt": workflow, "client_id": client_id})
    if "prompt_id" not in resp:
        raise RuntimeError(f"ComfyUI rejected prompt: {resp}")
    return resp["prompt_id"]


def wait_for(prompt_id: str, poll_s: float = 2.0, timeout_s: float = 3600) -> dict:
    """Poll /history until the prompt finishes. Returns the history entry.

    Also watches Song Forge: a customer job arriving mid-render interrupts this
    render rather than fighting it for the GPU (CLAUDE.md — customer jobs
    outrank renders). Raises CustomerJobPreempted so the caller can re-queue."""
    deadline = time.time() + timeout_s
    next_customer_check = time.time() + CUSTOMER_POLL_S
    while time.time() < deadline:
        hist = _get(f"/history/{prompt_id}")
        entry = hist.get(prompt_id)
        if entry and entry.get("status", {}).get("completed"):
            return entry
        if entry and entry.get("status", {}).get("status_str") == "error":
            raise RuntimeError(f"Workflow error: {entry['status']}")
        if time.time() >= next_customer_check:
            next_customer_check = time.time() + CUSTOMER_POLL_S
            if songforge_busy():
                _comfy_interrupt()
                raise CustomerJobPreempted(
                    "a Song Forge customer job arrived — this render yielded the GPU"
                )
        time.sleep(poll_s)
    raise TimeoutError(f"Prompt {prompt_id} timed out after {timeout_s}s")


def collect_outputs(history_entry: dict, label: str) -> list[Path]:
    """Download all files the workflow produced. Returns local paths."""
    saved = []
    outs = history_entry.get("outputs", {})
    for node_id, node_out in outs.items():
        for kind in ("images", "videos", "gifs", "audio"):
            for item in node_out.get(kind, []) or []:
                fname = item["filename"]
                subfolder = item.get("subfolder", "")
                ftype = item.get("type", "output")
                params = urllib.parse.urlencode(
                    {"filename": fname, "subfolder": subfolder, "type": ftype}
                )
                dest = OUT_DIR / f"{label}_{fname}"
                _download(f"/view?{params}", dest)
                saved.append(dest)
    return saved


def upload_image(local_path: Path, name: str | None = None) -> str:
    """POST image to /upload/image so a LoadImage node can reference it."""
    import email.generator
    import email.mime.multipart
    import email.mime.base

    name = name or local_path.name
    # Use urllib with manual multipart assembly to avoid requests dep
    boundary = uuid.uuid4().hex
    body = bytearray()
    body += f"--{boundary}\r\n".encode()
    body += f'Content-Disposition: form-data; name="image"; filename="{name}"\r\n'.encode()
    body += b"Content-Type: application/octet-stream\r\n\r\n"
    body += local_path.read_bytes()
    body += f"\r\n--{boundary}\r\n".encode()
    body += b'Content-Disposition: form-data; name="overwrite"\r\n\r\ntrue\r\n'
    body += f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{COMFY_URL}/upload/image",
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.loads(r.read())
    return out["name"]


# ───────────────────── Memory gate (added 2026-07-23) ─────────────────────
# Born from the 2026-07-23 kernel panic: an overnight queue kept submitting
# fp16 Wan shots while the machine was already swap-thrashing (110 s/step),
# WindowServer starved, macOS panicked mid-film. Every render now passes this
# gate first. Rules-in-docs get skipped at 3am; a gate in the code path doesn't.

MEM_GATE_MIN_FREE_PCT = int(os.environ.get("SF_MEM_GATE_MIN_FREE", "30"))
MEM_GATE_MAX_SWAP_GB = float(os.environ.get("SF_MEM_GATE_MAX_SWAP_GB", "8"))
MEM_GATE_MAX_WAIT_S = float(os.environ.get("SF_MEM_GATE_MAX_WAIT", "900"))
COMFY_START_CMD = os.environ.get(
    "SF_COMFY_START_CMD",
    f"cd {Path.home()}/Desktop/PROJECTS/AI/ComfyUI 2>/dev/null || cd {Path.home()}/AI/ComfyUI; "
    "nohup ./venv/bin/python main.py --listen >> /tmp/comfyui_overnight.log 2>&1 &",
)


def _mem_snapshot() -> dict:
    """free%, swap-used GB, and macOS pressure level (1=normal 2=warn 4=critical)."""
    import re
    import subprocess
    snap = {"free_pct": None, "swap_gb": None, "pressure": None}
    try:
        out = subprocess.run(["memory_pressure", "-Q"], capture_output=True, text=True, timeout=10).stdout
        m = re.search(r"free percentage:\s*(\d+)", out)
        if m:
            snap["free_pct"] = int(m.group(1))
    except Exception:
        pass
    try:
        out = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True, text=True, timeout=10).stdout
        m = re.search(r"used\s*=\s*([\d.]+)M", out)
        if m:
            snap["swap_gb"] = float(m.group(1)) / 1024
    except Exception:
        pass
    try:
        out = subprocess.run(["sysctl", "-n", "kern.memorystatus_vm_pressure_level"],
                             capture_output=True, text=True, timeout=10).stdout.strip()
        if out.isdigit():
            snap["pressure"] = int(out)
    except Exception:
        pass
    return snap


def _mem_ok(snap: dict) -> bool:
    # Swap SIZE is deliberately not a hard-fail: macOS never shrinks swap after
    # the pressure passes (74GB parked post-render with the box perfectly
    # healthy, first live run 2026-07-23). Big swap instead triggers the
    # ComfyUI bounce below, which actually releases those pages.
    if snap["pressure"] is not None and snap["pressure"] > 1:
        return False
    if snap["free_pct"] is not None and snap["free_pct"] < MEM_GATE_MIN_FREE_PCT:
        return False
    return True


def _swap_heavy(snap: dict) -> bool:
    return snap["swap_gb"] is not None and snap["swap_gb"] > MEM_GATE_MAX_SWAP_GB


def _comfy_rss_gb() -> float:
    import subprocess
    try:
        pids = subprocess.run(["pgrep", "-f", "main.py --listen"],
                              capture_output=True, text=True, timeout=10).stdout.split()
        if not pids:
            return 0.0
        out = subprocess.run(["ps", "-o", "rss=", "-p", ",".join(pids)],
                             capture_output=True, text=True, timeout=10).stdout
        return sum(int(x) for x in out.split()) / 1048576
    except Exception:
        return 0.0


def _comfy_busy() -> bool:
    """True if ComfyUI is mid-render — never restart it out from under a job."""
    try:
        q = _get("/queue")
        return bool(q.get("queue_running") or q.get("queue_pending"))
    except Exception:
        return False  # unreachable = not busy


def _restart_comfy() -> None:
    import subprocess
    print("[mem-gate] restarting ComfyUI to release cached models", flush=True)
    subprocess.run(["pkill", "-f", "main.py --listen"], capture_output=True)
    time.sleep(8)
    subprocess.run(COMFY_START_CMD, shell=True)
    deadline = time.time() + 120
    while time.time() < deadline:
        try:
            _get("/system_stats")
            print("[mem-gate] ComfyUI back up", flush=True)
            return
        except Exception:
            time.sleep(5)
    raise RuntimeError("mem-gate restarted ComfyUI but it did not come back within 120s")


def memory_gate(label: str = "clip") -> None:
    """Block until the machine can afford another render; raise rather than
    start a shot that would swap-thrash or panic the box. SF_MEM_GATE=0 disables
    (don't — that's how the 2026-07-23 crash happened)."""
    if os.environ.get("SF_MEM_GATE", "1") == "0":
        print("[mem-gate] DISABLED via SF_MEM_GATE=0 — you are on your own", flush=True)
        return
    restarted = False
    deadline = time.time() + MEM_GATE_MAX_WAIT_S
    while True:
        snap = _mem_snapshot()
        if _mem_ok(snap):
            # Healthy — but if a prior render parked a mountain in swap and an
            # idle ComfyUI is holding cache, bounce it once so the next heavy
            # load starts from a clean slate instead of on top of the mountain.
            if (not restarted and _swap_heavy(snap) and _comfy_rss_gb() > 5
                    and not _comfy_busy()):
                print(f"[mem-gate] healthy but {snap['swap_gb']:.0f}GB parked in swap — "
                      "bouncing idle ComfyUI to release it", flush=True)
                _restart_comfy()
                restarted = True
            return
        desc = (f"free={snap['free_pct']}% swap={0 if snap['swap_gb'] is None else round(snap['swap_gb'], 1)}GB "
                f"pressure={snap['pressure']}")
        if not restarted and _comfy_rss_gb() > 20 and not _comfy_busy():
            print(f"[mem-gate] low memory before '{label}' ({desc}) and ComfyUI holds "
                  f"{_comfy_rss_gb():.0f}GB of cached models — bouncing it", flush=True)
            _restart_comfy()
            restarted = True
            time.sleep(5)
            continue
        if time.time() > deadline:
            raise RuntimeError(
                f"mem-gate: refusing to start '{label}' — machine still short after "
                f"{int(MEM_GATE_MAX_WAIT_S)}s ({desc}). Free memory (quit heavy apps, "
                f"wait for training/downloads to finish) and re-run."
            )
        print(f"[mem-gate] waiting for memory before '{label}' ({desc})", flush=True)
        time.sleep(30)


# ───────────────────── The dam: evict BEFORE, don't mop after ─────────────────────
# 2026-07-27 kernel panic. mem-gate bounced ComfyUI 100 times in one day, every
# bounce triggered by 10-19GB ALREADY parked in swap — it reacts to a mountain
# instead of refusing to build one. The box finally could not page a swapped-out
# page back in, handed SIGBUS/KERN_MEMORY_ERROR to two node processes and an MLX
# server, then to launchd, and pid 1 dying is an automatic kernel panic.
#
# So: before a render is submitted, work out what it is about to load, compare it
# to what is genuinely available, and EVICT what it cannot coexist with. Song
# Forge's ACE-Step (:8001) and gemma (:9420) are the paid App Store product and
# are NEVER evicted — this M5 is the primary node and losing them is a customer
# outage. See CLAUDE.md rule 16.

STAGE_HEADROOM_GB = float(os.environ.get("SF_STAGE_HEADROOM_GB", "12"))
MODEL_OVERHEAD = float(os.environ.get("SF_MODEL_OVERHEAD", "1.2"))
MODEL_SUFFIXES = (".safetensors", ".gguf", ".ckpt", ".pt", ".sft", ".bin")
MODEL_SUBDIRS = ("diffusion_models", "unet", "checkpoints", "vae", "text_encoders",
                 "clip", "clip_vision", "loras", "LLM", "audio_encoders", "")


def _available_gb() -> float:
    """RAM that can be handed out without pushing anything to swap: free +
    inactive + speculative + purgeable. free% alone is deceptive when tens of GB
    are already swapped (feedback_watch_memory_before_heavy_ml)."""
    import re
    import subprocess
    try:
        out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=10).stdout
        page = int(re.search(r"page size of (\d+) bytes", out).group(1))
        want = ("Pages free", "Pages inactive", "Pages speculative", "Pages purgeable")
        total = 0
        for line in out.splitlines():
            k, _, v = line.partition(":")
            if k.strip() in want:
                total += int(v.strip().rstrip("."))
        return total * page / 1024 ** 3
    except Exception:
        return float("inf")  # can't measure → don't block the render


def _workflow_model_gb(workflow: dict) -> float:
    """What this workflow is about to load, from the on-disk size of every model
    file it references. Reading the actual files means new models and new quants
    are costed correctly the day they appear — no table to forget to update."""
    names: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, str) and node.lower().endswith(MODEL_SUFFIXES):
            names.add(node)

    walk(workflow)
    total = 0
    for name in names:
        for sub in MODEL_SUBDIRS:
            p = COMFY_ROOT / "models" / sub / name
            try:
                if p.is_file():
                    total += p.stat().st_size
                    break
            except OSError:
                continue
    return total / 1024 ** 3 * MODEL_OVERHEAD


def _rss_gb(pattern: str) -> float:
    import subprocess
    try:
        pids = subprocess.run(["pgrep", "-f", pattern],
                              capture_output=True, text=True, timeout=10).stdout.split()
        if not pids:
            return 0.0
        out = subprocess.run(["ps", "-o", "rss=", "-p", ",".join(pids)],
                             capture_output=True, text=True, timeout=10).stdout
        return sum(int(x) for x in out.split()) / 1048576
    except Exception:
        return 0.0


def _evict_comfy_cache() -> float:
    """Drop ComfyUI's cached model weights. Never while it is mid-render."""
    held = _comfy_rss_gb()
    if held < 5 or _comfy_busy():
        return 0.0
    print(f"[dam] evicting {held:.0f}GB of ComfyUI cached models before the next stage",
          flush=True)
    _restart_comfy()
    return held


def _evict_picture_eyes() -> float:
    """Drop the Picture Eyes VL server (:8181). It reloads on demand; a 32B VL
    model and Wan weights must never be resident together (rule: storyforge runs
    smart memory). Only when it is idle."""
    import subprocess
    held = _rss_gb("picture_eyes|picture-eyes")
    if held < 5:
        return 0.0
    try:
        import urllib.request as _u
        with _u.urlopen(f"{PICTURE_EYES_URL}/status", timeout=3) as r:
            if json.loads(r.read()).get("busy"):
                return 0.0
    except Exception:
        pass
    print(f"[dam] evicting the {held:.0f}GB Picture Eyes VL server — it reloads on demand",
          flush=True)
    subprocess.run(["pkill", "-f", "picture_eyes"], capture_output=True)
    time.sleep(5)
    return held


PICTURE_EYES_URL = os.environ.get("PE_URL", "http://127.0.0.1:8181")
EVICTORS = (_evict_comfy_cache, _evict_picture_eyes)


def prepare_for_stage(need_gb: float, label: str = "stage") -> None:
    """THE DAM. Evict what the coming stage cannot coexist with, BEFORE it runs.
    Never touches Song Forge. Falls through quietly if it cannot free enough —
    memory_gate still gets its say and will wait or refuse."""
    if os.environ.get("SF_MEM_GATE", "1") == "0" or need_gb <= 0:
        return
    target = need_gb + STAGE_HEADROOM_GB
    avail = _available_gb()
    if avail >= target:
        return
    print(f"[dam] '{label}' wants {need_gb:.0f}GB + {STAGE_HEADROOM_GB:.0f}GB headroom "
          f"but only {avail:.0f}GB is available without swapping — evicting", flush=True)
    for evict in EVICTORS:
        try:
            if evict():
                avail = _available_gb()
        except Exception as e:  # an evictor must never take the render down with it
            print(f"[dam] evictor {evict.__name__} failed: {e}", flush=True)
        if avail >= target:
            print(f"[dam] {avail:.0f}GB available — clear to run '{label}'", flush=True)
            return
    print(f"[dam] still only {avail:.0f}GB available for '{label}' after eviction "
          f"— handing over to mem-gate", flush=True)


# ───────────────────── Customer jobs preempt renders ─────────────────────
# CLAUDE.md: "Song Forge customer jobs outrank renders." That was one check
# before the i2v step and nothing during the 20 minutes it ran. Now a customer
# job interrupts the render in flight, and the render re-queues once they are done.

SONGFORGE_URL = os.environ.get("SONGFORGE_URL", "http://127.0.0.1:8767")
CUSTOMER_POLL_S = float(os.environ.get("SF_CUSTOMER_POLL_S", "20"))


class CustomerJobPreempted(RuntimeError):
    """A Song Forge customer job arrived; the render was interrupted for it."""


def songforge_busy() -> bool:
    try:
        with urllib.request.urlopen(f"{SONGFORGE_URL}/api/status", timeout=6) as r:
            return int(json.loads(r.read()).get("jobs_running", 0)) > 0
    except Exception:
        return False  # forge unreachable = no customer to protect


def wait_for_customers() -> None:
    announced = False
    while songforge_busy():
        if not announced:
            print("[customer] Song Forge has a paying job running — renders hold", flush=True)
            announced = True
        time.sleep(CUSTOMER_POLL_S)
    if announced:
        print("[customer] customer job finished — renders resume", flush=True)


def _comfy_interrupt() -> None:
    try:
        req = urllib.request.Request(f"{COMFY_URL}/interrupt", data=b"{}",
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=15).read()
        print("[customer] interrupted the ComfyUI render to free the GPU", flush=True)
    except Exception as e:
        print(f"[customer] could not interrupt ComfyUI: {e}", flush=True)


def run_workflow(workflow: dict, label: str = "clip", timeout_s: float = 3600) -> list[Path]:
    """One-call helper: submit, wait, download outputs. If a Song Forge customer
    job lands mid-render the render is interrupted, waits its turn, and re-queues
    — the paying job never queues behind a 20-minute animate."""
    for attempt in range(1, 4):
        pid = queue_prompt(workflow)
        print(f"[videopipe] queued {pid}", flush=True)
        try:
            entry = wait_for(pid, timeout_s=timeout_s)
        except CustomerJobPreempted:
            wait_for_customers()
            if attempt < 3:
                print(f"[videopipe] re-queueing '{label}' after the customer job "
                      f"(attempt {attempt + 1}/3)", flush=True)
            continue
        files = collect_outputs(entry, label)
        print(f"[videopipe] saved: {[str(f) for f in files]}", flush=True)
        return files
    raise RuntimeError(
        f"'{label}' was preempted by Song Forge customer jobs 3 times running — "
        "the render is yielding as designed, but this shot needs a quieter window."
    )


# ───────────────────── Workflow builders ─────────────────────

# Model filenames (as they live in ComfyUI/models/…)
WAN22_T2V_HIGH = "wan2.2_t2v_high_noise_14B_fp16.safetensors"
WAN22_T2V_LOW = "wan2.2_t2v_low_noise_14B_fp16.safetensors"
WAN22_I2V_HIGH = "wan2.2_i2v_high_noise_14B_fp16.safetensors"
WAN22_I2V_LOW = "wan2.2_i2v_low_noise_14B_fp16.safetensors"
UMT5_XXL = "umt5_xxl_fp16.safetensors"
WAN_VAE = "wan_2.1_vae.safetensors"
LIGHTX2V_T2V_HIGH = "wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors"
LIGHTX2V_T2V_LOW = "wan2.2_t2v_lightx2v_4steps_lora_v1.1_low_noise.safetensors"
LIGHTX2V_I2V_HIGH = "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors"
LIGHTX2V_I2V_LOW = "wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors"

# GGUF Q6_K quants — half the RAM of FP16 (≈12GB each instead of 27GB), unlocks 1280×720 6s
WAN22_T2V_HIGH_GGUF = "gguf/Wan2.2-T2V-A14B-HighNoise-Q6_K.gguf"
WAN22_T2V_LOW_GGUF = "gguf/Wan2.2-T2V-A14B-LowNoise-Q6_K.gguf"
WAN22_I2V_HIGH_GGUF = "gguf/Wan2.2-I2V-A14B-HighNoise-Q6_K.gguf"
WAN22_I2V_LOW_GGUF = "gguf/Wan2.2-I2V-A14B-LowNoise-Q6_K.gguf"

FLUX_MODEL = "flux1-dev-fp8.safetensors"
FLUX_CLIP_L = "clip_l.safetensors"
FLUX_T5 = "t5xxl_fp16.safetensors"
FLUX_VAE = "flux/ae.safetensors"

HUNYUAN_MODEL = "hunyuan/hunyuan_video_720_fp8_e4m3fn.safetensors"
HUNYUAN_VAE = "hunyuan/hunyuan_video_vae_bf16.safetensors"


# ───────────────────── Readiness detection ─────────────────────

COMFY_ROOT = Path.home() / "AI/ComfyUI"


def _has(relpath: str) -> bool:
    """Check a file exists in ComfyUI/models/ (diffusion_models, vae, etc.)."""
    for sub in ("diffusion_models", "vae", "text_encoders", "loras", "LLM", ""):
        if (COMFY_ROOT / "models" / sub / relpath).is_file():
            return True
    return False


def wan22_ready(mode: str = "t2v") -> bool:
    keys = {
        "t2v": [WAN22_T2V_HIGH, WAN22_T2V_LOW],
        "i2v": [WAN22_I2V_HIGH, WAN22_I2V_LOW],
    }[mode]
    need = keys + [UMT5_XXL, WAN_VAE]
    return all(_has(f) for f in need)


def wan22_gguf_ready() -> bool:
    """True if the GGUF Q6_K T2V quants are FULLY downloaded (Big Video Mode).
    Q6_K weights are ~12GB each — partial downloads return False to avoid
    surfacing the toggle before files are usable."""
    if not all(_has(f) for f in [UMT5_XXL, WAN_VAE]):
        return False
    min_size = 11_000_000_000  # 11 GB — well below Q6_K full size of ~12 GB
    for f in [WAN22_T2V_HIGH_GGUF, WAN22_T2V_LOW_GGUF]:
        for sub in ("diffusion_models",):
            p = COMFY_ROOT / "models" / sub / f
            if p.is_file() and p.stat().st_size >= min_size:
                break
        else:
            return False
    return True


def wan22_i2v_gguf_ready() -> bool:
    """True if the Q6_K I2V quants are FULLY downloaded. These are the DEFAULT i2v
    path — the fp16 pair OOM-kills ComfyUI at 832x480x81 with Song Forge resident."""
    if not all(_has(f) for f in [UMT5_XXL, WAN_VAE]):
        return False
    min_size = 11_000_000_000  # ~12GB full size; partials must not enable the path
    for f in [WAN22_I2V_HIGH_GGUF, WAN22_I2V_LOW_GGUF]:
        p = COMFY_ROOT / "models" / "diffusion_models" / f
        if not (p.is_file() and p.stat().st_size >= min_size):
            return False
    return True


HUNYUAN_MAIN = "hunyuan/hunyuan_video_720_cfgdistill_bf16.safetensors"


def hunyuan_ready() -> bool:
    return (
        (COMFY_ROOT / "models/diffusion_models" / HUNYUAN_MAIN).is_file()
        and (COMFY_ROOT / "models/diffusion_models/hunyuan/hunyuan_video_vae_bf16.safetensors").is_file()
        and (COMFY_ROOT / "models/LLM/llava-llama-3-8b/config.json").is_file()
    )


def ltx_ready() -> bool:
    return (COMFY_ROOT / "models/diffusion_models/ltx/ltxv-13b-0.9.8-distilled.safetensors").is_file()


def ltx2_ready() -> bool:
    """LTX-2 (MLX) is ready when its venv exists AND a model repo is cached.
    Runs through ~/ai-video-bench/mlxvid-venv, NOT ComfyUI — so we don't look
    under COMFY_ROOT here. Its unique trick: video + synced audio (talking).
    """
    from pathlib import Path
    venv_py = Path.home() / "ai-video-bench/mlxvid-venv/bin/python"
    hub = Path.home() / ".cache/huggingface/hub"
    cached = (hub / "models--prince-canuma--LTX-2-distilled").is_dir() or \
             (hub / "models--Lightricks--LTX-2").is_dir()
    return venv_py.is_file() and cached


def pick_best_t2v() -> str:
    """Return 'wan22' or 'ltx' or 'hunyuan' or raise if nothing ready.
    Order: Wan 2.2 (best quality) > LTX (known-good on MPS) > Hunyuan (flaky on Mac).
    NOTE: LTX-2 is NOT in this default chain — it's a special-purpose engine for
    realistic talking shots, selected explicitly or by render-route's classifier,
    not the general fallback.
    """
    if wan22_ready("t2v"):
        return "wan22"
    if ltx_ready():
        return "ltx"
    if hunyuan_ready():
        return "hunyuan"
    raise RuntimeError("No T2V model ready yet — downloads still in progress.")


def pick_best_i2v() -> str:
    if wan22_ready("i2v"):
        return "wan22"
    # HunyuanVideo I2V needs extra weights we didn't pull — skip for now
    raise RuntimeError("No I2V model ready yet — downloads still in progress.")

DEFAULT_NEG = (
    "blurry, out of focus, low quality, jittery camera, excessive shake, "
    "warped, deformed, extra limbs, bad anatomy, watermark, logo, text, "
    "noise, banding, flicker, oversaturated"
)


def build_wan22_t2v(
    prompt: str,
    negative: str = DEFAULT_NEG,
    width: int = 720,
    height: int = 480,
    length: int = 81,       # frames: 81 @ 16fps ≈ 5s
    seed: int = 0,
    fps: int = 16,
    fast: bool = True,       # use Lightx2v 4-step LoRA (10x speedup)
) -> dict:
    """Wan 2.2 14B T2V workflow (two-stage MoE: high noise → low noise)."""
    if seed == 0:
        seed = int(time.time()) & 0x7fffffff

    steps = 4 if fast else 20
    cfg = 1.0 if fast else 3.5
    split = steps // 2  # where to hand off from high to low noise

    w: dict[str, Any] = {}

    def node(nid: str, class_type: str, inputs: dict):
        w[nid] = {"class_type": class_type, "inputs": inputs}

    node("1", "UNETLoader", {"unet_name": WAN22_T2V_HIGH, "weight_dtype": "default"})
    node("2", "UNETLoader", {"unet_name": WAN22_T2V_LOW, "weight_dtype": "default"})
    node("3", "CLIPLoader", {"clip_name": UMT5_XXL, "type": "wan", "device": "default"})
    node("4", "VAELoader", {"vae_name": WAN_VAE})

    hi = ["1", 0]
    lo = ["2", 0]
    if fast:
        node("1L", "LoraLoaderModelOnly", {
            "model": hi, "lora_name": LIGHTX2V_T2V_HIGH, "strength_model": 1.0,
        })
        node("2L", "LoraLoaderModelOnly", {
            "model": lo, "lora_name": LIGHTX2V_T2V_LOW, "strength_model": 1.0,
        })
        hi = ["1L", 0]
        lo = ["2L", 0]

    # Sampling shift (Wan-specific)
    node("1S", "ModelSamplingSD3", {"model": hi, "shift": 8.0})
    node("2S", "ModelSamplingSD3", {"model": lo, "shift": 8.0})

    node("5", "CLIPTextEncode", {"clip": ["3", 0], "text": prompt})
    node("6", "CLIPTextEncode", {"clip": ["3", 0], "text": negative})
    node("7", "EmptyHunyuanLatentVideo", {
        "width": width, "height": height, "length": length, "batch_size": 1,
    })

    # High-noise stage (first half of denoising)
    node("10", "KSamplerAdvanced", {
        "model": ["1S", 0], "add_noise": "enable", "noise_seed": seed,
        "steps": steps, "cfg": cfg, "sampler_name": "euler", "scheduler": "simple",
        "positive": ["5", 0], "negative": ["6", 0], "latent_image": ["7", 0],
        "start_at_step": 0, "end_at_step": split,
        "return_with_leftover_noise": "enable",
    })
    # Low-noise stage (second half)
    node("11", "KSamplerAdvanced", {
        "model": ["2S", 0], "add_noise": "disable", "noise_seed": seed,
        "steps": steps, "cfg": cfg, "sampler_name": "euler", "scheduler": "simple",
        "positive": ["5", 0], "negative": ["6", 0], "latent_image": ["10", 0],
        "start_at_step": split, "end_at_step": steps,
        "return_with_leftover_noise": "disable",
    })

    node("12", "VAEDecode", {"samples": ["11", 0], "vae": ["4", 0]})
    node("13", "VHS_VideoCombine", {
        "images": ["12", 0], "frame_rate": fps, "loop_count": 0,
        "filename_prefix": "wan22_t2v", "format": "video/h264-mp4",
        "pix_fmt": "yuv420p", "crf": 19, "save_metadata": False, "pingpong": False, "save_output": True,
    })

    return w


def build_wan22_i2v_gguf(
    prompt: str,
    image_filename: str,       # must already exist in ComfyUI/input (use upload_image)
    negative: str = DEFAULT_NEG,
    width: int = 832,
    height: int = 480,
    length: int = 81,
    seed: int = 0,
    fps: int = 16,
    fast: bool = True,
) -> dict:
    """Wan 2.2 I2V via Q6_K GGUF quants — the memory-safe twin of build_wan22_i2v.

    WHY THIS EXISTS (2026-07-25): the fp16 I2V path loads TWO ~27GB MoE stages. With
    Song Forge's ~45GB resident that swap-storms the machine and macOS kills the render
    mid-way — it killed ComfyUI twice in one day (Doug's reaction shot, then the Scene 2
    'the call' final at 832x480x81, where step time jumped 47s → 135s before the kill).
    The Q6_K quants are ~12GB each, so the same job fits. Prefer this for ALL i2v work;
    reach for the fp16 builder only when the machine is otherwise idle.
    """
    if seed == 0:
        seed = int(time.time()) & 0x7fffffff

    steps = 4 if fast else 20
    cfg = 1.0 if fast else 3.5
    split = steps // 2

    w: dict[str, Any] = {}

    def node(nid: str, class_type: str, inputs: dict):
        w[nid] = {"class_type": class_type, "inputs": inputs}

    node("1", "UnetLoaderGGUF", {"unet_name": WAN22_I2V_HIGH_GGUF})
    node("2", "UnetLoaderGGUF", {"unet_name": WAN22_I2V_LOW_GGUF})
    node("3", "CLIPLoader", {"clip_name": UMT5_XXL, "type": "wan", "device": "default"})
    node("4", "VAELoader", {"vae_name": WAN_VAE})
    node("Img", "LoadImage", {"image": image_filename})

    hi, lo = ["1", 0], ["2", 0]
    if fast:
        node("1L", "LoraLoaderModelOnly", {
            "model": hi, "lora_name": LIGHTX2V_I2V_HIGH, "strength_model": 1.0,
        })
        node("2L", "LoraLoaderModelOnly", {
            "model": lo, "lora_name": LIGHTX2V_I2V_LOW, "strength_model": 1.0,
        })
        hi, lo = ["1L", 0], ["2L", 0]

    node("1S", "ModelSamplingSD3", {"model": hi, "shift": 8.0})
    node("2S", "ModelSamplingSD3", {"model": lo, "shift": 8.0})

    node("5", "CLIPTextEncode", {"clip": ["3", 0], "text": prompt})
    node("6", "CLIPTextEncode", {"clip": ["3", 0], "text": negative})
    node("7", "WanImageToVideo", {
        "positive": ["5", 0], "negative": ["6", 0], "vae": ["4", 0],
        "width": width, "height": height, "length": length, "batch_size": 1,
        "start_image": ["Img", 0],
    })

    node("10", "KSamplerAdvanced", {
        "model": ["1S", 0], "add_noise": "enable", "noise_seed": seed,
        "steps": steps, "cfg": cfg, "sampler_name": "euler", "scheduler": "simple",
        "positive": ["7", 0], "negative": ["7", 1], "latent_image": ["7", 2],
        "start_at_step": 0, "end_at_step": split,
        "return_with_leftover_noise": "enable",
    })
    node("11", "KSamplerAdvanced", {
        "model": ["2S", 0], "add_noise": "disable", "noise_seed": seed,
        "steps": steps, "cfg": cfg, "sampler_name": "euler", "scheduler": "simple",
        "positive": ["7", 0], "negative": ["7", 1], "latent_image": ["10", 0],
        "start_at_step": split, "end_at_step": steps,
        "return_with_leftover_noise": "disable",
    })

    node("12", "VAEDecode", {"samples": ["11", 0], "vae": ["4", 0]})
    node("13", "VHS_VideoCombine", {
        "images": ["12", 0], "frame_rate": fps, "loop_count": 0,
        "filename_prefix": "wan22_i2v_gguf", "format": "video/h264-mp4",
        "pix_fmt": "yuv420p", "crf": 19, "save_metadata": False,
        "pingpong": False, "save_output": True,
    })
    return w


def build_wan22_t2v_gguf(
    prompt: str,
    negative: str = DEFAULT_NEG,
    width: int = 1280,
    height: int = 720,
    length: int = 97,
    seed: int = 0,
    fps: int = 16,
    fast: bool = True,
) -> dict:
    """Wan 2.2 T2V via Q6_K GGUF quants. Same two-stage MoE flow as build_wan22_t2v
    but loads the unets through ComfyUI-GGUF (city96), cutting per-model RAM
    from ~27GB to ~12GB. Frees ~30GB for activations — unlocks 1280×720 at 6s."""
    if seed == 0:
        seed = int(time.time()) & 0x7fffffff

    steps = 4 if fast else 20
    cfg = 1.0 if fast else 3.5
    split = steps // 2

    w: dict[str, Any] = {}

    def node(nid: str, class_type: str, inputs: dict):
        w[nid] = {"class_type": class_type, "inputs": inputs}

    node("1", "UnetLoaderGGUF", {"unet_name": WAN22_T2V_HIGH_GGUF})
    node("2", "UnetLoaderGGUF", {"unet_name": WAN22_T2V_LOW_GGUF})
    node("3", "CLIPLoader", {"clip_name": UMT5_XXL, "type": "wan", "device": "default"})
    node("4", "VAELoader", {"vae_name": WAN_VAE})

    hi = ["1", 0]
    lo = ["2", 0]
    if fast:
        node("1L", "LoraLoaderModelOnly", {
            "model": hi, "lora_name": LIGHTX2V_T2V_HIGH, "strength_model": 1.0,
        })
        node("2L", "LoraLoaderModelOnly", {
            "model": lo, "lora_name": LIGHTX2V_T2V_LOW, "strength_model": 1.0,
        })
        hi = ["1L", 0]
        lo = ["2L", 0]

    node("1S", "ModelSamplingSD3", {"model": hi, "shift": 8.0})
    node("2S", "ModelSamplingSD3", {"model": lo, "shift": 8.0})

    node("5", "CLIPTextEncode", {"clip": ["3", 0], "text": prompt})
    node("6", "CLIPTextEncode", {"clip": ["3", 0], "text": negative})
    node("7", "EmptyHunyuanLatentVideo", {
        "width": width, "height": height, "length": length, "batch_size": 1,
    })

    node("10", "KSamplerAdvanced", {
        "model": ["1S", 0], "add_noise": "enable", "noise_seed": seed,
        "steps": steps, "cfg": cfg, "sampler_name": "euler", "scheduler": "simple",
        "positive": ["5", 0], "negative": ["6", 0], "latent_image": ["7", 0],
        "start_at_step": 0, "end_at_step": split,
        "return_with_leftover_noise": "enable",
    })
    node("11", "KSamplerAdvanced", {
        "model": ["2S", 0], "add_noise": "disable", "noise_seed": seed,
        "steps": steps, "cfg": cfg, "sampler_name": "euler", "scheduler": "simple",
        "positive": ["5", 0], "negative": ["6", 0], "latent_image": ["10", 0],
        "start_at_step": split, "end_at_step": steps,
        "return_with_leftover_noise": "disable",
    })

    node("12", "VAEDecode", {"samples": ["11", 0], "vae": ["4", 0]})
    node("13", "VHS_VideoCombine", {
        "images": ["12", 0], "frame_rate": fps, "loop_count": 0,
        "filename_prefix": "wan22_t2v_gguf", "format": "video/h264-mp4",
        "pix_fmt": "yuv420p", "crf": 19, "save_metadata": False, "pingpong": False, "save_output": True,
    })

    return w


def build_wan22_i2v(
    prompt: str,
    image_filename: str,       # must already exist in ComfyUI/input (use upload_image)
    negative: str = DEFAULT_NEG,
    width: int = 720,
    height: int = 480,
    length: int = 81,
    seed: int = 0,
    fps: int = 16,
    fast: bool = True,
    distill_lora: str | None = None,  # trained 2-step distill LoRA, stacked on lightx2v
    steps_override: int | None = None,  # e.g. 2 when using the distill LoRA
    distill_stage: str | None = None,  # "high" (default) | "both" | "low"
    distill_strength: float | None = None,  # LoRA strength (default 1.0)
) -> dict:
    """Wan 2.2 14B I2V workflow (image → video)."""
    if seed == 0:
        seed = int(time.time()) & 0x7fffffff
    steps = 4 if fast else 20
    if steps_override:
        steps = steps_override
    cfg = 1.0 if fast else 3.5
    split = steps // 2

    w: dict[str, Any] = {}

    def node(nid: str, class_type: str, inputs: dict):
        w[nid] = {"class_type": class_type, "inputs": inputs}

    node("1", "UNETLoader", {"unet_name": WAN22_I2V_HIGH, "weight_dtype": "default"})
    node("2", "UNETLoader", {"unet_name": WAN22_I2V_LOW, "weight_dtype": "default"})
    node("3", "CLIPLoader", {"clip_name": UMT5_XXL, "type": "wan", "device": "default"})
    node("4", "VAELoader", {"vae_name": WAN_VAE})
    node("Img", "LoadImage", {"image": image_filename})

    hi, lo = ["1", 0], ["2", 0]
    if fast:
        node("1L", "LoraLoaderModelOnly", {
            "model": hi, "lora_name": LIGHTX2V_I2V_HIGH, "strength_model": 1.0,
        })
        node("2L", "LoraLoaderModelOnly", {
            "model": lo, "lora_name": LIGHTX2V_I2V_LOW, "strength_model": 1.0,
        })
        hi, lo = ["1L", 0], ["2L", 0]

    # Stack our trained 2-step distill LoRA. It was TRAINED on the high-noise
    # stage only, so apply it there only — applying it to the low-noise stage
    # (different weights) caused a visible color/detail drift (LPIPS 0.11).
    # distill_stage: "high" (default, matches training) | "both" | "low".
    if distill_lora:
        ds = (distill_stage or "high").lower()
        strength = float(distill_strength) if distill_strength is not None else 1.0
        if ds in ("high", "both"):
            node("1D", "LoraLoaderModelOnly", {
                "model": hi, "lora_name": distill_lora, "strength_model": strength,
            })
            hi = ["1D", 0]
        if ds in ("low", "both"):
            node("2D", "LoraLoaderModelOnly", {
                "model": lo, "lora_name": distill_lora, "strength_model": strength,
            })
            lo = ["2D", 0]

    node("1S", "ModelSamplingSD3", {"model": hi, "shift": 8.0})
    node("2S", "ModelSamplingSD3", {"model": lo, "shift": 8.0})

    node("5", "CLIPTextEncode", {"clip": ["3", 0], "text": prompt})
    node("6", "CLIPTextEncode", {"clip": ["3", 0], "text": negative})

    # Wan 2.2 native I2V uses WanImageToVideo for conditioning
    node("7", "WanImageToVideo", {
        "positive": ["5", 0], "negative": ["6", 0], "vae": ["4", 0],
        "width": width, "height": height, "length": length, "batch_size": 1,
        "start_image": ["Img", 0],
    })

    node("10", "KSamplerAdvanced", {
        "model": ["1S", 0], "add_noise": "enable", "noise_seed": seed,
        "steps": steps, "cfg": cfg, "sampler_name": "euler", "scheduler": "simple",
        "positive": ["7", 0], "negative": ["7", 1], "latent_image": ["7", 2],
        "start_at_step": 0, "end_at_step": split,
        "return_with_leftover_noise": "enable",
    })
    node("11", "KSamplerAdvanced", {
        "model": ["2S", 0], "add_noise": "disable", "noise_seed": seed,
        "steps": steps, "cfg": cfg, "sampler_name": "euler", "scheduler": "simple",
        "positive": ["7", 0], "negative": ["7", 1], "latent_image": ["10", 0],
        "start_at_step": split, "end_at_step": steps,
        "return_with_leftover_noise": "disable",
    })

    node("12", "VAEDecode", {"samples": ["11", 0], "vae": ["4", 0]})
    node("13", "VHS_VideoCombine", {
        "images": ["12", 0], "frame_rate": fps, "loop_count": 0,
        "filename_prefix": "wan22_i2v", "format": "video/h264-mp4",
        "pix_fmt": "yuv420p", "crf": 19, "save_metadata": False, "pingpong": False, "save_output": True,
    })
    return w


def build_hunyuan_t2v(
    prompt: str,
    negative: str = "low quality, blurry",
    width: int = 960,
    height: int = 544,
    length: int = 73,       # ~3 sec at 24fps
    steps: int = 30,
    cfg: float = 6.0,
    flow_shift: float = 9.0,
    seed: int = 0,
    fps: int = 24,
) -> dict:
    """HunyuanVideo 13B T2V workflow (Kijai wrapper nodes)."""
    if seed == 0:
        seed = int(time.time()) & 0x7fffffff
    w: dict[str, Any] = {}

    def node(nid: str, class_type: str, inputs: dict):
        w[nid] = {"class_type": class_type, "inputs": inputs}

    node("ml", "HyVideoModelLoader", {
        "model": HUNYUAN_MAIN,
        "base_precision": "bf16",
        "quantization": "disabled",
        "load_device": "offload_device",
        "attention_mode": "sdpa",
    })
    node("vae", "HyVideoVAELoader", {
        "model_name": "hunyuan_video_vae_bf16.safetensors",
        "precision": "bf16",
    })
    node("te", "DownloadAndLoadHyVideoTextEncoder", {
        "llm_model": "Kijai/llava-llama-3-8b-text-encoder-tokenizer",
        "clip_model": "openai/clip-vit-large-patch14",
        "precision": "fp16",
        "apply_final_norm": False,
        "hidden_state_skip_layer": 2,
        "quantization": "disabled",
    })
    node("enc", "HyVideoTextEncode", {
        "text_encoders": ["te", 0],
        "prompt": prompt,
        "negative_prompt": negative,
        "prompt_template": "video",
    })
    node("smp", "HyVideoSampler", {
        "model": ["ml", 0],
        "hyvid_embeds": ["enc", 0],
        "width": width, "height": height, "num_frames": length,
        "steps": steps, "embedded_guidance_scale": cfg, "flow_shift": flow_shift,
        "seed": seed, "force_offload": True,
        "scheduler": "FlowMatchDiscreteScheduler",
        "denoise_strength": 1.0,
        "riflex_freq_index": 0,
    })
    node("dec", "HyVideoDecode", {
        "vae": ["vae", 0], "samples": ["smp", 0],
        "enable_vae_tiling": True, "temporal_tiling_sample_size": 64,
        "spatial_tile_sample_min_size": 256, "auto_tile_size": True,
    })
    node("out", "VHS_VideoCombine", {
        "images": ["dec", 0], "frame_rate": fps, "loop_count": 0,
        "filename_prefix": "hunyuan_t2v", "format": "video/h264-mp4",
        "pix_fmt": "yuv420p", "crf": 19, "save_metadata": False, "pingpong": False, "save_output": True,
    })
    return w


def build_flux_image(
    prompt: str,
    width: int = 1280,
    height: int = 720,
    seed: int = 0,
    steps: int = 20,
) -> dict:
    """FLUX.1 Dev image generation workflow."""
    if seed == 0:
        seed = int(time.time()) & 0x7fffffff
    w: dict[str, Any] = {}

    def node(nid: str, class_type: str, inputs: dict):
        w[nid] = {"class_type": class_type, "inputs": inputs}

    node("1", "UNETLoader", {"unet_name": FLUX_MODEL, "weight_dtype": "fp8_e4m3fn"})
    node("2", "DualCLIPLoader", {
        "clip_name1": FLUX_T5, "clip_name2": FLUX_CLIP_L, "type": "flux",
    })
    node("3", "VAELoader", {"vae_name": FLUX_VAE})
    node("4", "CLIPTextEncode", {"clip": ["2", 0], "text": prompt})
    node("5", "EmptyLatentImage", {"width": width, "height": height, "batch_size": 1})
    node("6", "ModelSamplingFlux", {
        "model": ["1", 0], "max_shift": 1.15, "base_shift": 0.5,
        "width": width, "height": height,
    })
    node("7", "FluxGuidance", {"conditioning": ["4", 0], "guidance": 3.5})
    node("8", "KSampler", {
        "model": ["6", 0], "seed": seed, "steps": steps, "cfg": 1.0,
        "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
        "positive": ["7", 0], "negative": ["7", 0], "latent_image": ["5", 0],
    })
    node("9", "VAEDecode", {"samples": ["8", 0], "vae": ["3", 0]})
    node("10", "SaveImage", {"images": ["9", 0], "filename_prefix": "flux"})
    return w


# ───────────────────── ffmpeg helpers ─────────────────────

def concat_mp4s(paths: list[Path], dest: Path, crossfade_s: float = 0.0) -> Path:
    """Stitch multiple MP4s into one. No crossfade by default (fast concat demuxer)."""
    import subprocess
    if crossfade_s <= 0 and len(paths) > 1:
        concat_list = dest.parent / f".concat_{uuid.uuid4().hex}.txt"
        concat_list.write_text("\n".join(f"file '{p}'" for p in paths))
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
             "-c", "copy", str(dest)],
            check=True, capture_output=True,
        )
        concat_list.unlink()
        return dest
    # single or crossfade path
    if len(paths) == 1:
        subprocess.run(["cp", str(paths[0]), str(dest)], check=True)
        return dest
    # crossfade: build complex filter
    inputs = []
    for p in paths:
        inputs += ["-i", str(p)]
    # Build xfade chain
    filters = []
    last = "[0:v]"
    offset = 0.0
    # approximate durations from ffprobe
    import subprocess as sp
    durs = []
    for p in paths:
        out = sp.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(p)]
        ).decode().strip()
        durs.append(float(out))
    for i in range(1, len(paths)):
        offset += durs[i-1] - crossfade_s
        tag = f"[x{i}]"
        filters.append(
            f"{last}[{i}:v]xfade=transition=fade:duration={crossfade_s}:offset={offset:.3f}{tag}"
        )
        last = tag
    subprocess.run(
        ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters),
         "-map", last, "-c:v", "libx264", "-pix_fmt", "yuv420p", str(dest)],
        check=True, capture_output=True,
    )
    return dest


def add_audio(video: Path, audio: Path, dest: Path) -> Path:
    import subprocess
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video), "-i", str(audio),
         "-c:v", "copy", "-c:a", "aac", "-shortest", str(dest)],
        check=True, capture_output=True,
    )
    return dest


def extract_frames(video: Path, dest_dir: Path, every_s: float = 1.0) -> list[Path]:
    """Pull keyframes from a video for remix workflows."""
    import subprocess
    dest_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video), "-vf", f"fps=1/{every_s}",
         str(dest_dir / "frame_%04d.png")],
        check=True, capture_output=True,
    )
    return sorted(dest_dir.glob("frame_*.png"))


if __name__ == "__main__":
    # quick self-check
    try:
        stats = _get("/system_stats")
        print(f"✓ ComfyUI alive: {stats.get('system', {}).get('os', '?')}")
    except Exception as e:
        print(f"✗ cannot reach ComfyUI at {COMFY_URL}: {e}")
        sys.exit(1)
