#!/usr/bin/env python3
"""promo_music.py — promo stage 08: an instrumental bed from the LOCAL Song Forge (ACE-Step).

Posts /api/song with lyrics "[inst]", private + video_only (never lands in Matt's library or the
public page), polls, and downloads AT ONCE (the mini purges private songs after an hour). Song
Forge customer jobs outrank us: it refuses to start while jobs_running > 0. The bed is then
whisper-checked for stray vocals (a lone hallucinated "Thank you" on music is normal; real lyric
lines are not) and the result goes in music/bed.json.

  ~/chatterbox-env/bin/python pipeline-tools/promo_music.py projects/<film> [--seconds 60]
        [--style "..."] [--out music/bed.wav] [--force]
Defaults: promo.json music.style, seconds = the film's length + 15 (edl.json dur when present).
Exit 0 = bed on disk (or already there); 1 = rendered but it has vocals; 2 = could not run.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from promo_common import SONG_FORGE, WHISPER_ID, load_promo, song_forge_busy  # noqa: E402


def call(path, body=None):
    req = urllib.request.Request(SONG_FORGE + path, data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json"}, method="POST" if body else "GET")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("film")
    ap.add_argument("--seconds", type=int, default=None)
    ap.add_argument("--style", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    film = Path(a.film).resolve()
    cfg = load_promo(film)
    out = film / (a.out or cfg["music"].get("bed") or "music/bed.wav")
    if out.exists() and not a.force:
        print(f"[music] bed already on disk: {out.relative_to(film)}")
        return 0
    secs = a.seconds
    if secs is None:
        edl = film / "edl.json"
        secs = int(json.loads(edl.read_text())["dur"] + 15) if edl.exists() else 60
    busy, why = song_forge_busy()
    if busy:
        print(f"[music] Song Forge busy ({why}); customer jobs first. Try again when it is idle.", file=sys.stderr)
        return 2
    style = a.style or cfg["music"]["style"]
    try:
        job = call("/api/song", {"style": style, "lyrics": "[inst]", "title": f"{film.name} promo bed",
                                 "duration": secs, "planner": "off", "private": True, "video_only": True})
    except Exception as e:  # noqa: BLE001
        print(f"[music] Song Forge refused the job: {e}", file=sys.stderr)
        return 2
    jid = job.get("id") or (job.get("ids") or [None])[0]
    print(f"[music] job {jid}: {secs}s '{style}'")
    t0, info = time.time(), {}
    while time.time() - t0 < 900:
        time.sleep(5)
        try:
            info = call(f"/api/song/{jid}")
        except Exception:  # noqa: BLE001
            continue
        if info.get("status") in ("done", "error"):
            break
    if info.get("status") != "done":
        print(f"[music] render did not finish: {info.get('status')}", file=sys.stderr)
        return 2
    url = info.get("audio") or info.get("download") or info.get("url")
    if url and url.startswith("/"):
        url = SONG_FORGE + url
    out.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "curl"}), timeout=120) as r:
        out.write_bytes(r.read())
    print(f"[music] saved {out.relative_to(film)} ({out.stat().st_size // 1024} KB) after {time.time() - t0:.0f}s")
    import mlx_whisper
    text = mlx_whisper.transcribe(str(out), path_or_hf_repo=WHISPER_ID, language="en").get("text", "").strip()
    words = [w for w in text.split() if w.strip(".,!?").lower() not in ("thank", "you", "thanks", "for", "watching")]
    vocal = len(words) > 3
    (out.parent / (out.stem + ".json")).write_text(json.dumps(
        {"style": style, "seconds": secs, "job": jid, "whisper": text, "vocals": vocal}, indent=1))
    if vocal:
        print(f"[music] VOCALS in the bed (whisper: '{text[:120]}'); render another (--force)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
