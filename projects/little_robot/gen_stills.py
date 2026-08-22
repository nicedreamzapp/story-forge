#!/usr/bin/env python3
"""Flux stills runner — sequential, crash-resumable (skips existing), watchdogged.
Each render is a subprocess; one failure logs and continues (overnight rule)."""
import json, subprocess, sys, time, zlib
from pathlib import Path

HOME = Path.home()
PROJ = HOME / "Desktop/PROJECTS/story-forge/projects/little_robot"
FLUX = HOME / "Scripts/flux_t2i.py"
STILLS = PROJ / "stills"
STILLS.mkdir(exist_ok=True)

data = json.loads((PROJ / "shots.json").read_text())
blocks = data["blocks"]

def expand(p):
    for k, v in blocks.items():
        p = p.replace("{" + k + "}", v)
    return p

# optional: only render specific ids passed as args (used for re-rolls)
only = set(sys.argv[1:])
items = [(sid, st) for sid, st in data["stills"].items() if not only or sid in only]

done = fail = skip = 0
for sid, st in items:
    out = STILLS / f"{sid}.png"
    if out.exists() and not only:
        skip += 1
        continue
    prompt = expand(st["p"])
    seed = zlib.crc32(sid.encode()) % 100000 + (int(time.time()) % 7 if only else 0)
    t = time.time()
    try:
        r = subprocess.run(
            ["python3", str(FLUX), prompt, "--out", str(out),
             "--w", "1152", "--h", "768", "--seed", str(seed)],
            capture_output=True, text=True, timeout=600)
        if r.returncode == 0 and out.exists():
            done += 1
            print(f"OK {sid} ({time.time()-t:.0f}s)", flush=True)
        else:
            fail += 1
            print(f"FAIL {sid}: {r.stderr.strip().splitlines()[-1] if r.stderr else 'no output'}", flush=True)
    except subprocess.TimeoutExpired:
        fail += 1
        print(f"TIMEOUT {sid}", flush=True)
    time.sleep(2)  # let MPS settle between renders

print(f"STILLS_DONE ok={done} fail={fail} skip={skip}", flush=True)
