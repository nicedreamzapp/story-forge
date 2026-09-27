#!/usr/bin/env python3
"""Score via ACE-Step direct API (bypasses Song Forge library — no cleanup needed).
Four instrumental cues, polled to completion, copied to music/."""
import json, time, sys, shutil
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse, parse_qs

ACE = "http://127.0.0.1:8001"
PROJ = Path.home() / "Desktop/PROJECTS/story-forge/projects/little_robot"
MUSIC = PROJ / "music"
MUSIC.mkdir(exist_ok=True)

CUES = [
    ("cue1_bin", 65, "delicate music box lullaby, celesta and soft warm strings, lonely but hopeful, gentle night ambience, slow 70 bpm, instrumental film score, no vocals"),
    ("cue2_build", 100, "playful pizzicato strings, light woodblock percussion, warm acoustic guitar, curious tinkering workshop energy, building optimism, 110 bpm, instrumental Pixar-style film score, no vocals"),
    ("cue3_storm", 62, "low tense cinematic strings, melancholy solo cello melody turning tender and brave, sparse piano notes, rain mood, 60 bpm, instrumental film score, no vocals"),
    ("cue4_sunrise", 80, "warm uplifting cinematic orchestra, acoustic guitar and glockenspiel, gentle triumphant joy, golden sunrise feeling, soaring but soft finale, 90 bpm, instrumental film score, no vocals"),
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
        print(f"FAIL {name}: no task_id {resp}", flush=True)
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
            print(f"FAIL {name}: path not found {audio_path}", flush=True)
print("MUSIC_DONE", flush=True)
