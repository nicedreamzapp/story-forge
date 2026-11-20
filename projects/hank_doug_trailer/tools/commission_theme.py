#!/usr/bin/env python3
"""Commission the theme song candidates from the M5's Song Forge (ACE-Step 1.5) BEFORE m5-bigjob turns it off.
Private + video_only, downloaded at once, job deleted after. Writes music/theme_N.wav + .json."""
import json, subprocess, sys, time, urllib.request
from pathlib import Path
P = Path(__file__).resolve().parent.parent
SF = "http://127.0.0.1:8767"
LYR_MAIN = """[Pickup]
Who's that coming? (Who's that coming?)
Rollin', rollin', here we go!

[Verse 1]
When a goat's stuck high and a turtle's stuck low,
And a kitten is stuck in a drain,
Some little critter is always gonna know,
And whistle and holler our names!

[Chorus]
Hank and Doug! (Hank and Doug!)
A horse and a zebra, a camel, a cow!
Hank and Doug! (Hank and Doug!)
Giraffes are the ladders, we're coming right now!
Elephants pump and the water goes SPLOOSH!
Nobody's too big and nobody's too small,
Somebody always hears the call...
It's Hank and Doug's Wild Rescue!

[Outro]
Rollin'! (Rollin'!) Here we go!"""
STYLE_MAIN = ("upbeat kids' TV theme song, bluegrass folk-pop, banjo, acoustic guitar, upright bass, hand claps, tambourine, "
              "whistling, tuba hits on the downbeats, warm friendly adult male lead vocal, a group of kids shouting the "
              "call-and-response parts in parentheses, 120 BPM, 4/4, key of G major, bright, bouncy, playful, storybook, "
              "clean mix, no distortion, no electronic drums, no autotune")
STYLE_BOX = ("instrumental, no vocals, no singing, music box and soft humming only, slow, tender, no drums, no words, "
             "60 BPM, half time, warm reverb, lullaby, G major, a gentle storybook melody")
JOBS = {
 "theme_1": dict(style=STYLE_MAIN, lyrics=LYR_MAIN, duration=62, bpm=120),
 "theme_2": dict(style=STYLE_MAIN + ", live acoustic band, fiddle", lyrics=LYR_MAIN, duration=62, bpm=120),
 "breakdown_1": dict(style=STYLE_BOX, lyrics="[instrumental]", duration=30, planner="off"),
}
def call(path, body=None, method=None):
    req = urllib.request.Request(SF + path, data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json"}, method=method or ("POST" if body else "GET"))
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)
def busy():
    try: return int(call("/api/status").get("jobs_running") or 0) > 0
    except Exception: return False
for name, spec in JOBS.items():
    out = P / f"music/{name}.wav"
    if out.exists(): print("have", out); continue
    while busy(): print("Song Forge busy, waiting 20s", flush=True); time.sleep(20)
    body = {"title": f"hank_doug {name}", "private": True, "video_only": True, **spec}
    job = call("/api/song", body)
    jid = job.get("id") or (job.get("ids") or [None])[0]
    t0 = time.time(); info = {}
    print(f"{name}: job {jid}", flush=True)
    while time.time() - t0 < 900:
        time.sleep(5)
        try: info = call(f"/api/song/{jid}")
        except Exception: continue
        if info.get("status") in ("done", "error"): break
    if info.get("status") != "done":
        print(f"{name} failed: {info.get('status')} {info.get('error')}", flush=True); continue
    url = info.get("audio") or info.get("download") or info.get("url")
    if url.startswith("/"): url = SF + url
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "curl"}), timeout=120) as r:
        raw = r.read()
    tmp = out.with_suffix(".src"); tmp.write_bytes(raw)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-ar", "48000", "-ac", "2", str(out)], check=True)
    tmp.unlink()
    out.with_suffix(".json").write_text(json.dumps({"style": spec["style"], "job": jid, "secs": round(time.time() - t0),
        "info": {k: info.get(k) for k in ("title", "duration", "bpm", "key", "lyrics")}}, indent=1))
    try: call(f"/api/song/{jid}", method="DELETE"); print(f"{name}: job deleted from Song Forge")
    except Exception as e: print(f"{name}: delete failed {e}")
    print(f"{name}: saved {out.name} after {time.time()-t0:.0f}s", flush=True)
