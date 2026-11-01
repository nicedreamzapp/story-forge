#!/usr/bin/env python3
"""Commission the 3 trailer score candidates from the local Song Forge (ACE-Step), instrumental only.
Private + video_only, downloaded at once. Waits while customer jobs run (they always win).
Writes music/candidates/score_N.wav + score_N.json (style, job id, whisper text)."""
import json, sys, time, urllib.request
from pathlib import Path
P = Path(__file__).resolve().parent.parent
SF = "http://127.0.0.1:8767"
BASE = ("instrumental, no vocals, no choir, epic cinematic sci-fi movie trailer score, 48 seconds, "
        "opens with a low pulsing synth drone and a ticking pulse, then a giant low brass BRAAAM, "
        "rising string ostinato and building orchestral percussion, a sudden dead stop, then "
        "accelerating taiko and trailer drums with a horn hit on every bar, ending on one final massive hit")
STYLES = {
 1: BASE + ", hybrid orchestral, Hans Zimmer style, deep sub bass, distorted brass, dark and huge",
 2: BASE + ", dark synth-orchestral, pulsing analog synth bass, metallic percussion, cold and ominous, Blade Runner meets Dune",
 3: BASE + ", full symphonic orchestra, massive French horns and trombones, taiko ensemble, strings tremolo, heroic dread",
}
def call(path, body=None):
    req = urllib.request.Request(SF + path, data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json"}, method="POST" if body else "GET")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)
def busy():
    try: return int(call("/api/status").get("jobs_running") or 0) > 0
    except Exception: return False
for n, style in STYLES.items():
    out = P / f"music/candidates/score_{n}.wav"
    if out.exists(): print("have", out); continue
    while busy():
        print("Song Forge busy, waiting 20s", flush=True); time.sleep(20)
    job = call("/api/song", {"style": style, "lyrics": "[instrumental]", "title": f"last_signal score {n}",
                             "duration": 50, "planner": "off", "private": True, "video_only": True})
    jid = job.get("id") or (job.get("ids") or [None])[0]
    t0 = time.time(); info = {}
    print(f"score {n}: job {jid}", flush=True)
    while time.time() - t0 < 900:
        time.sleep(5)
        try: info = call(f"/api/song/{jid}")
        except Exception: continue
        if info.get("status") in ("done", "error"): break
    if info.get("status") != "done":
        print(f"score {n} failed: {info.get('status')} {info.get('error')}", flush=True); continue
    url = info.get("audio") or info.get("download") or info.get("url")
    if url.startswith("/"): url = SF + url
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "curl"}), timeout=120) as r:
        raw = r.read()
    tmp = out.with_suffix(".src")
    tmp.write_bytes(raw)
    import subprocess
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-ar", "48000", "-ac", "2", str(out)], check=True)
    tmp.unlink()
    (out.with_suffix(".json")).write_text(json.dumps({"style": style, "job": jid, "secs": time.time() - t0,
                                                      "info": {k: info.get(k) for k in ("title", "duration", "bpm", "key")}}, indent=1))
    print(f"score {n}: saved {out.name} after {time.time()-t0:.0f}s", flush=True)
