#!/usr/bin/env python3
"""Antarctica score — ACE-Step direct API. One musical identity across four
cues: every prompt shares the same motif language so the film ties together."""
import json, time, shutil
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse, parse_qs

ACE = "http://127.0.0.1:8001"
PROJ = Path.home() / "Desktop/PROJECTS/story-forge/projects/antarctica"
MUSIC = PROJ / "music"
MUSIC.mkdir(exist_ok=True)

MOTIF = "built around one slow rising four-note string motif that repeats like a heartbeat"
CUES = [
    ("cue1_veil", 70, f"glacial ambient orchestral film score, vast and mysterious, deep sustained strings and distant French horn, icy shimmering textures, {MOTIF}, 60 bpm, instrumental documentary score, no vocals"),
    ("cue2_wonder", 65, f"luminous orchestral film score of discovery and wonder, warm swelling strings and soft piano over icy ambient textures, {MOTIF} growing brighter, 70 bpm, instrumental documentary score, no vocals"),
    ("cue3_deeptime", 65, f"awe-filled slow orchestral film score, deep cello and choir-like pads, ancient and timeless mood, glassy harmonics, {MOTIF} stretched long and reverent, 56 bpm, instrumental documentary score, no vocals"),
    ("cue4_edge", 90, f"urgent then resolving orchestral film score, pulsing low strings and ticking percussion building tension, easing into a vast hopeful horn finale, {MOTIF} returning triumphant at the end, 80 bpm, instrumental documentary score, no vocals"),
]

def post(path, payload, timeout=30):
    req = Request(ACE + path, data=json.dumps(payload).encode(),
                  headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

for name, dur, prompt in CUES:
    out = MUSIC / f"{name}.wav"
    if out.exists():
        print(f"SKIP {name}", flush=True)
        continue
    resp = post("/release_task", {
        "prompt": prompt, "lyrics": "[inst]", "vocal_language": "en",
        "task_type": "text2music", "inference_steps": 27,
        "guidance_scale": 7.0, "audio_format": "wav", "audio_duration": dur})
    tid = (resp.get("data") or {}).get("task_id")
    if not tid:
        print(f"FAIL {name}: no task_id", flush=True)
        continue
    t0 = time.time()
    audio_path = None
    while time.time() - t0 < 600:
        time.sleep(5)
        res = post("/query_result", {"task_id_list": json.dumps([tid])}, 15)
        dl = res.get("data") or []
        if not dl:
            continue
        env = dl[0]
        inner = json.loads(env.get("result") or "[]")
        first = inner[0] if inner else {}
        status = first.get("status", env.get("status", 0))
        ap = first.get("file") or first.get("wave") or ""
        if status == 1 or (ap and float(first.get("progress") or 0) >= 0.999):
            audio_path = ap
            break
        if status in (-1, 2, 3):
            print(f"FAIL {name}: ace status {status}", flush=True)
            break
    if audio_path:
        src = None
        if audio_path.startswith("/v1/audio"):
            q = parse_qs(urlparse(audio_path).query)
            if q.get("path"):
                src = Path(q["path"][0])
        elif audio_path.startswith("/"):
            src = Path(audio_path)
        if src and src.is_file():
            shutil.copyfile(src, out)
            print(f"OK {name} ({time.time()-t0:.0f}s)", flush=True)
        else:
            print(f"FAIL {name}: path not found", flush=True)
print("MUSIC_DONE", flush=True)
