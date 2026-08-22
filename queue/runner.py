from __future__ import annotations   # lazy annotations so type hints work on system python 3.9
"""
runner.py — Story Forge render queue, with HARD safety guards.

This version exists because the previous one CRASHED the machine: it let three
renders run at once (each loads the 27 GB LTX model), exhausted 128 GB of RAM,
and forced a reboot. These guards make that impossible:

  1. ONE render, ever. Before starting, it checks the whole system for any
     running `bin/sf render`. If one exists, it waits. No concurrency, period.
  2. MEMORY GATE. It refuses to start a render unless there's MEM_FLOOR_GB of
     memory available. A single render needs ~30-50 GB; the floor leaves margin.
  3. LIVE WATCHDOG. While a render runs, it polls memory every few seconds and
     KILLS the render if available memory drops below MEM_KILL_GB, swap balloons,
     or the OS reports critical memory pressure — protecting the machine over the
     render.
  4. NO auto-respawn. Not run under launchd KeepAlive anymore. It does not resume
     heavy work after a crash or reboot. It only runs when started deliberately.
  5. Single daemon instance (PID check at startup).
  6. Publishing OFF by default (SF_PUBLISH=1 required to ever upload).
  7. Renders run under `caffeinate` so the machine doesn't fight sleep mid-render.
"""
import json, os, re, signal, subprocess, sys, threading, time
from datetime import datetime
from pathlib import Path

# ── paths ─────────────────────────────────────────────────────────────────
HOME    = Path.home()
QUEUE   = HOME / "story-forge-queue"
INBOX, PROC, DONE, FAILED, LOGS = (QUEUE/"inbox", QUEUE/"processing",
                                   QUEUE/"done", QUEUE/"failed", QUEUE/"logs")
SF_ROOT = HOME / "Desktop/PROJECTS/story-forge"
SF_BIN  = SF_ROOT / "bin/sf"
PUBLISH = QUEUE / "publish.py"
IMSG    = HOME / ".claude/imessage-send.sh"
STATE   = QUEUE / "state.json"
LOCK    = QUEUE / "runner.lock"

POLL_SECS = 20
ENGINE    = os.environ.get("SF_ENGINE", "lean")
PUBLISH_ENABLED = os.environ.get("SF_PUBLISH") == "1"     # OFF unless explicitly enabled

# ── SAFETY GUARD THRESHOLDS (GB) ───────────────────────────────────────────
MEM_FLOOR_GB = float(os.environ.get("SF_MEM_FLOOR", "60"))  # need this much available to START a render
MEM_KILL_GB  = float(os.environ.get("SF_MEM_KILL",  "14"))  # kill the render if available drops below this
SWAP_KILL_GB = float(os.environ.get("SF_SWAP_KILL", "8"))   # kill if swap usage exceeds this
MEM_POLL_SEC = 4                                            # how often the watchdog checks memory
PAGESIZE     = 16384                                        # Apple Silicon page size


def log(msg: str):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S}  {msg}"
    print(line, flush=True)
    try:
        with open(LOGS / "runner.log", "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ── memory / safety probes ─────────────────────────────────────────────────
def _vm_stat() -> dict:
    out = subprocess.run(["vm_stat"], capture_output=True, text=True).stdout
    v = {}
    for ln in out.splitlines():
        if ":" in ln:
            k, val = ln.split(":", 1)
            val = val.strip().rstrip(".")
            if val.isdigit():
                v[k.strip()] = int(val)
    return v


def mem() -> tuple[float, float]:
    """Returns (total_gb, available_gb). Available = reclaimable memory."""
    total = int(subprocess.run(["sysctl", "-n", "hw.memsize"],
                               capture_output=True, text=True).stdout.strip()) / 1e9
    v = _vm_stat()
    avail_pages = (v.get("Pages free", 0) + v.get("Pages inactive", 0)
                   + v.get("Pages speculative", 0) + v.get("Pages purgeable", 0)
                   + v.get("File-backed pages", 0))
    return total, avail_pages * PAGESIZE / 1e9


def swap_used_gb() -> float:
    try:
        s = subprocess.run(["sysctl", "-n", "vm.swapusage"],
                           capture_output=True, text=True).stdout
        m = re.search(r"used = ([\d.]+)([MG])", s)
        if m:
            val = float(m.group(1))
            return val / 1024 if m.group(2) == "M" else val
    except Exception:
        pass
    return 0.0


def pressure_critical() -> bool:
    try:
        lvl = int(subprocess.run(["sysctl", "-n", "kern.memorystatus_vm_pressure_level"],
                                 capture_output=True, text=True).stdout.strip())
        return lvl >= 4   # 1 normal, 2 warning, 4 critical
    except Exception:
        return False


def mem_danger() -> str | None:
    """Returns a reason string if memory is in the danger zone, else None."""
    total, avail = mem()
    if avail < MEM_KILL_GB:
        return f"only {avail:.0f}GB available (floor {MEM_KILL_GB:.0f})"
    sw = swap_used_gb()
    if sw > SWAP_KILL_GB:
        return f"swap at {sw:.0f}GB (limit {SWAP_KILL_GB:.0f})"
    if pressure_critical():
        return "OS reports CRITICAL memory pressure"
    return None


def render_running() -> bool:
    """True if ANY Story Forge render is running anywhere on the system."""
    r = subprocess.run(["pgrep", "-f", "bin/sf render"], capture_output=True, text=True)
    return bool(r.stdout.strip())


def comfyui_up() -> bool:
    """The Flux image server. If it's down, a render half-fails on the first still."""
    r = subprocess.run(["curl", "-s", "-m", "3", "-o", "/dev/null",
                        "-w", "%{http_code}", "http://127.0.0.1:8188/"],
                       capture_output=True, text=True)
    return r.stdout.strip() == "200"


def already_a_daemon() -> bool:
    me = os.getpid()
    r = subprocess.run(["pgrep", "-f", "story-forge-queue/runner.py"],
                       capture_output=True, text=True)
    others = [int(x) for x in r.stdout.split() if x.strip().isdigit() and int(x) != me]
    return len(others) > 0


# ── queue plumbing ─────────────────────────────────────────────────────────
def load_state() -> dict:
    if STATE.exists():
        try: return json.loads(STATE.read_text())
        except Exception: pass
    return {"done": [], "failed": []}

def save_state(s: dict):
    STATE.write_text(json.dumps(s, indent=2))

def notify(text: str):
    if IMSG.exists():
        try: subprocess.run(["bash", str(IMSG), text], timeout=30)
        except Exception as e: log(f"notify failed: {e}")

def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "film"

def title_from(sf_path: Path) -> str:
    try:
        for ln in sf_path.read_text(errors="ignore").splitlines():
            m = re.match(r'\s*film\s+"([^"]+)"', ln)
            if m: return m.group(1).strip()
    except Exception:
        pass
    return sf_path.stem.replace("_", " ").title()

def oldest_job() -> Path | None:
    jobs = sorted(INBOX.glob("*.sf"), key=lambda p: p.stat().st_mtime)
    return jobs[0] if jobs else None


def wait_until_safe():
    """Block until it is safe to start exactly one render."""
    while True:
        if render_running():
            log("hold — a render is already running (hard one-at-a-time limit)")
            time.sleep(POLL_SECS); continue
        total, avail = mem()
        if avail < MEM_FLOOR_GB:
            log(f"hold — {avail:.0f}GB available, need {MEM_FLOOR_GB:.0f}GB to start safely")
            time.sleep(POLL_SECS); continue
        if not comfyui_up():
            log("hold — ComfyUI (Flux image server :8188) is not responding; not starting a render")
            time.sleep(POLL_SECS); continue
        log(f"safe to start: {avail:.0f}GB/{total:.0f}GB available, no other render running, ComfyUI up")
        return


def render(sf_file: Path, out_mp4: Path, job_log: Path) -> tuple[bool, str | None]:
    """Run ONE render under caffeinate, watched by a memory watchdog that kills it
    if memory gets dangerous. Returns (ok, guard_reason)."""
    cmd = ["caffeinate", "-is", "python3", str(SF_BIN), "render",
           str(sf_file), "--out", str(out_mp4), "--engine", ENGINE]
    total, avail = mem()
    log(f"render START  {sf_file.name}  (mem {avail:.0f}/{total:.0f}GB free) -> {out_mp4.name}")
    guard = {"reason": None}
    with open(job_log, "a") as lf:
        lf.write(f"\n==== render {datetime.now():%F %T} ====\ncmd: {' '.join(cmd)}\n\n"); lf.flush()
        proc = subprocess.Popen(cmd, cwd=str(SF_ROOT), stdout=lf,
                                stderr=subprocess.STDOUT, preexec_fn=os.setsid)

        def watchdog():
            while proc.poll() is None:
                reason = mem_danger()
                if reason:
                    guard["reason"] = reason
                    log(f"⚠️  MEMORY GUARD TRIPPED — killing render to protect the machine ({reason})")
                    try: os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    except Exception: pass
                    return
                time.sleep(MEM_POLL_SEC)
        t = threading.Thread(target=watchdog, daemon=True); t.start()
        proc.wait()

    ok = (proc.returncode == 0 and out_mp4.exists() and out_mp4.stat().st_size > 0
          and guard["reason"] is None)
    tail = f"  (guard: {guard['reason']})" if guard["reason"] else ""
    log(f"render {'OK' if ok else 'FAIL'}  {sf_file.name}  rc={proc.returncode}{tail}")
    return ok, guard["reason"]


def process(sf_in: Path, state: dict):
    slug  = slugify(sf_in.stem)
    title = title_from(sf_in)
    job_log = LOGS / f"{slug}.log"
    out_mp4 = DONE / f"{slug}.mp4"

    wait_until_safe()                 # GATE: one render, enough memory
    proc_sf = PROC / sf_in.name
    sf_in.rename(proc_sf)             # claim
    started = time.time()
    ok, guard_reason = render(proc_sf, out_mp4, job_log)
    mins = round((time.time() - started) / 60, 1)

    if not ok:
        proc_sf.rename(FAILED / sf_in.name)
        state["failed"].append({"slug": slug, "at": datetime.now().isoformat(),
                                "guard": guard_reason})
        save_state(state)
        if guard_reason:
            notify(f"Stopped {title} to protect the machine — {guard_reason}. Nothing crashed.")
        else:
            notify(f"Render failed: {title}. See logs/{slug}.log")
        return

    proc_sf.rename(DONE / sf_in.name)
    pub = {"youtube": None}
    if PUBLISH_ENABLED:
        cmd = ["python3", str(PUBLISH), str(out_mp4), "--title", title]
        subprocess.run(cmd)
    rec = {"slug": slug, "title": title, "mp4": str(out_mp4), "render_min": mins,
           "published": PUBLISH_ENABLED, "at": datetime.now().isoformat()}
    (DONE / f"{slug}.json").write_text(json.dumps(rec, indent=2))
    state["done"].append(rec); save_state(state)
    notify(f"Rendered {title} in {mins} min. Saved to done/ (NOT uploaded).")


def main() -> int:
    for d in (INBOX, PROC, DONE, FAILED, LOGS):
        d.mkdir(parents=True, exist_ok=True)
    if already_a_daemon():
        log("another runner is already live; exiting"); return 0

    LOCK.write_text(str(os.getpid()))
    def _bye(*_):
        try: LOCK.unlink()
        except Exception: pass
        sys.exit(0)
    signal.signal(signal.SIGTERM, _bye); signal.signal(signal.SIGINT, _bye)

    total, avail = mem()
    log(f"runner up (GUARDED). one-render-max, mem floor {MEM_FLOOR_GB:.0f}GB, "
        f"kill <{MEM_KILL_GB:.0f}GB. now: {avail:.0f}/{total:.0f}GB free. publish={'ON' if PUBLISH_ENABLED else 'OFF'}")
    try:
        while True:
            job = oldest_job()
            if job is None:
                time.sleep(POLL_SECS); continue
            try:
                process(job, load_state())
            except Exception as e:
                log(f"error on {job.name}: {e}")
                try: (PROC / job.name).rename(FAILED / job.name)
                except Exception: pass
                time.sleep(5)
    finally:
        try: LOCK.unlink()
        except Exception: pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
