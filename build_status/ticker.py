#!/usr/bin/env python3
"""ticker.py — runs in background, refreshes status.json + live_log.json
every 30 seconds with current state of M5 + mini + any active jobs.

Pointed at by index.html dashboard which auto-refreshes every 20s.

Launch:
    nohup python3 ticker.py > /tmp/ticker.log 2>&1 &
"""
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATUS_JSON = HERE / "status.json"
LIVE_JSON = HERE / "live.json"
TICK_SECONDS = 30


def safe(cmd: str, timeout: int = 8) -> str:
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout,
        )
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return f"err: {e}"


def poll_m5_comfy() -> dict:
    """Get ComfyUI :8188 (M5) queue state."""
    out = safe("curl -fs http://127.0.0.1:8188/queue 2>/dev/null")
    if not out or not out.startswith("{"):
        return {"alive": False, "running": 0, "pending": 0}
    try:
        q = json.loads(out)
        return {
            "alive": True,
            "running": len(q.get("queue_running", [])),
            "pending": len(q.get("queue_pending", [])),
        }
    except json.JSONDecodeError:
        return {"alive": False, "running": 0, "pending": 0}


def poll_mini_comfy() -> dict:
    """Get ComfyUI :8189 (mini) queue state via mini cli (slow, capped at 12s)."""
    out = safe("~/.local/bin/mini -t 12 \"curl -fs http://127.0.0.1:8189/queue 2>/dev/null\"", timeout=15)
    if not out or "{" not in out:
        return {"alive": False, "running": 0, "pending": 0}
    try:
        # mini cli wraps the output; find JSON
        json_part = out[out.find("{") : out.rfind("}") + 1]
        q = json.loads(json_part)
        return {
            "alive": True,
            "running": len(q.get("queue_running", [])),
            "pending": len(q.get("queue_pending", [])),
        }
    except json.JSONDecodeError:
        return {"alive": False, "running": 0, "pending": 0}


def poll_local_pythons() -> list:
    """List active long-running Python processes related to this build."""
    out = safe(
        "ps -axo pid,etime,command | grep -E 'make-ltx|make-video|bench_wan|mini_wan|sf render|story_pipeline|make-ltx-lightricks' | grep -v grep | head -8"
    )
    procs = []
    for line in out.splitlines():
        parts = line.split(None, 2)
        if len(parts) >= 3:
            procs.append({"pid": parts[0], "elapsed": parts[1], "cmd": parts[2][:120]})
    return procs


def poll_disk_growth(paths: list) -> list:
    """File sizes for files matching glob patterns (track download progress)."""
    out = []
    for p in paths:
        size = safe(f"stat -f '%z' {p} 2>/dev/null")
        if size and size.isdigit():
            out.append({"path": p, "mb": round(int(size) / 1e6, 1)})
    return out


def tail_log(path: str, n: int = 8) -> list:
    """Last n non-empty lines of a log file."""
    out = safe(f"tail -n {n*2} {path} 2>/dev/null | tail -n {n}")
    return [l for l in out.splitlines() if l.strip()][-n:]


def gather() -> dict:
    return {
        "ticker_updated_at": datetime.now().isoformat(timespec="seconds"),
        "m5_comfy": poll_m5_comfy(),
        "mini_comfy": poll_mini_comfy(),
        "active_python_procs": poll_local_pythons(),
        "key_files": poll_disk_growth([
            "~/AI/videopipe/outputs",
        ]),
        "log_tails": {
            "bench_wan_e2e": tail_log("/tmp/bench_wan_e2e.log", 12),
            "m5_comfy": tail_log("/tmp/m5_comfy.log", 6),
            "ticker": tail_log("/tmp/ticker.log", 4),
        },
    }


def main():
    print(f"[ticker] starting, writing {LIVE_JSON} every {TICK_SECONDS}s")
    while True:
        try:
            data = gather()
            LIVE_JSON.write_text(json.dumps(data, indent=2))
            print(
                f"[ticker] tick {data['ticker_updated_at']}  "
                f"m5_running={data['m5_comfy']['running']}  "
                f"mini_running={data['mini_comfy']['running']}  "
                f"procs={len(data['active_python_procs'])}"
            )
        except Exception as e:
            print(f"[ticker] error: {e}")
        time.sleep(TICK_SECONDS)


if __name__ == "__main__":
    main()
