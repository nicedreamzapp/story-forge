#!/usr/bin/env python3
"""v5.1 (11/18 1:15 PM, Matt: "nice music not some lame hissing static"): the ACE-Step themes carry a broadband noise bed
~25 dB under the notes in every window (tools/audio_audit_v51.py); denoise and low-pass cannot remove it without dulling.
Regenerate cleaner candidates: no claps/tambourine/whistling/shaker (the noise-like layers), clean dry studio tags.
Original docstring: Commission the theme song candidates from the M5's Song Forge (ACE-Step 1.5) BEFORE m5-bigjob turns it off.
Private + video_only, downloaded at once, job deleted after. Writes music/theme_N.wav + .json."""
import json, subprocess, sys, time, urllib.request
from pathlib import Path
P = Path(__file__).resolve().parent.parent
import os
SF = os.getenv("SF_URL", "http://127.0.0.1:18768")   # v5.1: the mini's Song Forge through the VPS tunnel (M5 Song Forge is off for the training)
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
# v5.2 (Matt 1:53 PM: "maybe a ballad... anthem... explorer"): ONE ~60 s song for the whole trailer. Quiet, sparse, mostly
# instrumental under the narrated story, building through the rescues into a big sung anthem chorus with the title line,
# ending on a clean final chord. Three takes, picked by hiss measurement + whisper hearing "Hank and Doug" in the chorus.
# take 1 lesson (2:05 PM): ACE-Step SANG the long bracketed stage directions and left a 9 s hole. Standard short tags only;
# the arc lives in the style text.
LYR_ANTHEM = """[Instrumental]

[Instrumental]

[Chorus]
Hank and Doug! (Hank and Doug!)
Over the hills when the wild things call!
Hank and Doug! (Hank and Doug!)
Nobody's too big and nobody's too small!
It's Hank and Doug's Wild Rescue!

[Outro]"""
STYLE_ANTHEM = ("adventurous explorer anthem for a kids' film trailer, cinematic folk, the first thirty seconds quiet and sparse: one warm "
                "fingerpicked acoustic guitar and a soft low string pad, no drums, no vocals; then slowly building with piano, a slow "
                "heartbeat drum and swelling strings into one huge bright sing-along anthem chorus with big drums and brass, warm friendly "
                "adult male lead vocal, a choir of kids on the answers, ending on one big final chord that rings out; hopeful, brave, wide "
                "open; clean dry studio recording, high fidelity, no tape hiss, no noise, no shaker, no tambourine, 96 BPM, 4/4, D major")
JOBS = {
 "anthem_4": dict(style=STYLE_ANTHEM, lyrics=LYR_ANTHEM, duration=60, bpm=96),
 "anthem_5": dict(style=STYLE_ANTHEM + ", orchestral, french horn and timpani on the chorus", lyrics=LYR_ANTHEM, duration=60, bpm=96),
 "anthem_6": dict(style=STYLE_ANTHEM.replace("96 BPM", "104 BPM") + ", banjo and fiddle join on the chorus, bluegrass warmth", lyrics=LYR_ANTHEM, duration=60, bpm=104),
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
