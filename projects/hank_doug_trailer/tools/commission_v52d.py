#!/usr/bin/env python3
"""commission_v52c.py — v5.2 anthem, round 4 (11/18 2:25 PM; round 3 anthem_7 ran out of time before the chorus at 64 s: ~5 s per sung line, so 78 s). Rounds 1-2 (anthem_1..6) taught: ACE-Step sings bracketed stage
directions, ignores long [Instrumental] holds (chorus at 2 s, or silence, or mumble). So this round asks for a NORMAL sung
ballad-anthem (verse, pre-chorus, chorus, outro) and the trailer mix uses its demucs instrumental stem under the narrated
story, bringing the sung chorus in over the rescues so the title line lands on the title card. Three takes, picked by
measurement (hiss floor, no clicks) + whisper hearing "Hank and Doug" in the chorus. Mini's Song Forge via the VPS tunnel."""
import json, subprocess, time, urllib.request, os
from pathlib import Path
P = Path(__file__).resolve().parent.parent
SF = os.getenv("SF_URL", "http://127.0.0.1:18768")
LYR = """[Verse 1]
Down a long dark road with his nose to the ground,
Doug was hunting for something he never found.
Then one night in the trees by a silver stream,
He found a bear who was kinder than any dream.
So he turned right around and he never looked back,
Two best friends and a wagon on a brand new track.

[Pre-Chorus]
When the wild things call, when a little one falls,
Hear the wheels on the hill and the whistle that calls!

[Chorus]
Hank and Doug! (Hank and Doug!)
Over the hills when the wild things call!
Hank and Doug! (Hank and Doug!)
Nobody's too big and nobody's too small!
It's Hank and Doug's Wild Rescue!

[Outro]
Hank and Doug!"""
STYLE = ("adventurous explorer anthem, cinematic folk ballad that builds: a quiet fingerpicked acoustic guitar and a soft low string pad "
         "under the verse, piano and a slow heartbeat drum come in on the pre-chorus, then one huge bright sing-along chorus with big "
         "drums, brass, soaring strings and a choir, warm friendly adult male lead vocal, a kids' choir on the answers, and it ends on one "
         "big final chord that rings out and stops clean; hopeful, brave, wide open; clean dry studio recording, high fidelity, "
         "no tape hiss, no noise, no shaker, no tambourine, 96 BPM, 4/4, D major")
JOBS = {
 "anthem_10": dict(style=STYLE, lyrics=LYR, duration=78, bpm=96),
 "anthem_11": dict(style=STYLE + ", orchestral, french horn and timpani on the chorus", lyrics=LYR, duration=78, bpm=96),
 "anthem_12": dict(style=STYLE.replace("96 BPM", "100 BPM") + ", banjo and fiddle join on the chorus, bluegrass warmth", lyrics=LYR, duration=78, bpm=100),
}
def call(path, body=None, method=None):
    req = urllib.request.Request(SF + path, data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json"}, method=method or ("POST" if body else "GET"))
    with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)
def busy():
    try: return int(call("/api/status").get("jobs_running") or 0) > 0
    except Exception: return False
for name, spec in JOBS.items():
    out = P / f"music/{name}.wav"
    if out.exists(): print("have", out); continue
    while busy(): print("Song Forge busy, waiting 20s", flush=True); time.sleep(20)
    body = {"title": f"hank_doug {name}", "private": True, "video_only": True, **spec}
    job = call("/api/song", body); jid = job.get("id") or (job.get("ids") or [None])[0]
    t0 = time.time(); info = {}; print(f"{name}: job {jid}", flush=True)
    while time.time() - t0 < 900:
        time.sleep(5)
        try: info = call(f"/api/song/{jid}")
        except Exception: continue
        if info.get("status") in ("done", "error"): break
    if info.get("status") != "done": print(f"{name} failed: {info.get('status')} {info.get('error')}", flush=True); continue
    url = info.get("audio") or info.get("download") or info.get("url")
    if url.startswith("/"): url = SF + url
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "curl"}), timeout=120) as r: raw = r.read()
    tmp = out.with_suffix(".src"); tmp.write_bytes(raw)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-ar", "48000", "-ac", "2", str(out)], check=True); tmp.unlink()
    out.with_suffix(".json").write_text(json.dumps({"style": spec["style"], "lyrics": LYR, "job": jid, "secs": round(time.time() - t0),
        "info": {k: info.get(k) for k in ("title", "duration", "bpm", "key")}}, indent=1))
    try: call(f"/api/song/{jid}", method="DELETE"); print(f"{name}: job deleted from Song Forge")
    except Exception as e: print(f"{name}: delete failed {e}")
    print(f"{name}: saved {out.name} after {time.time()-t0:.0f}s", flush=True)
