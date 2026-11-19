#!/usr/bin/env python3
"""sfx_fetch_v52.py — real CC0 sound effects for v5.2 (Matt 1:55 PM: real clean effects, not AI noise; Freesound CC0 approved).
Searches freesound.org with the "Creative Commons 0" licence filter (public HTML, no login), takes the top results by downloads,
confirms the licence on each sound page, downloads the 128 kbps preview (-hq.mp3; originals need a login), converts to 48 kHz wav
in sfx/library/<query>_<id>.wav, and records id, title, author, licence, URL and duration in sfx/library/LICENSES.md + library.json.
Measures each: HF (>8 kHz) floor in the quietest 10% of 50 ms frames, overall RMS, clicks. Pick by ear-by-number afterwards."""
import re, json, subprocess, urllib.request, urllib.parse, time, sys
from pathlib import Path
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfiltfilt
P = Path(__file__).resolve().parent.parent; LIB = P / "sfx/library"; LIB.mkdir(exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) story-forge sfx fetch"}
QUERIES = {  # key: (query, max dur s, how many)
 "dog_sniff":   ("dog sniffing", 12, 3), "leaves_steps": ("footsteps leaves walking", 20, 3), "whistle_dog": ("whistle calling dog", 6, 3),
 "wire_twang":  ("wire fence twang", 8, 3), "fence_rattle": ("fence rattle metal wire", 8, 2), "fox_bark": ("fox bark", 8, 2),
 "boots_dirt":  ("footsteps dirt boots walking", 20, 3), "slip_fall": ("body fall thud grass", 5, 2), "splash_big": ("splash water big", 6, 3),
 "dog_bark":    ("dog bark single", 4, 3), "birds_dawn": ("birds morning forest ambience", 40, 3), "hooves_walk": ("horse hooves walking dirt", 20, 3),
 "wagon_wheels": ("wooden wagon wheels", 20, 3), "wings_flap": ("goose wings flapping", 8, 3), "water_pour": ("water pouring splash", 8, 3),
 "wire_twang2": ("wire twang", 6, 3), "barbed_wire": ("barbed wire", 8, 2), "fence_spring": ("fence wire spring", 6, 2),
 "hooves2": ("horse walking hooves", 20, 3), "hooves3": ("horse walk", 20, 2), "wings2": ("wings flapping", 8, 3), "wings3": ("bird wings flap", 6, 2),
 "fall_water": ("falling into water", 6, 3), "stumble": ("stumble fall", 5, 2), "lantern2": ("lantern", 5, 2), "otter2": ("otter", 8, 2),
 "crickets": ("crickets night quiet", 40, 3), "night_forest": ("night forest ambience", 40, 2),
 "kitten_mew":  ("kitten meow", 4, 3), "otter":   ("otter squeak", 6, 2), "water_lap": ("water small splash", 5, 2), "lantern_clank": ("lantern metal clank", 4, 2),
}
def get(url):
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r: return r.read()
        except Exception as e: err = e; time.sleep(2)
    raise err
def measure(wav):
    y, sr = sf.read(wav); y = y.mean(1) if y.ndim > 1 else y
    hf = sosfiltfilt(butter(4, 8000, btype="high", fs=sr, output="sos"), y); FR = int(0.05 * sr); n = max(1, len(y) // FR)
    r = np.sqrt((y[:n*FR].reshape(n, FR) ** 2).mean(1) + 1e-18); rh = np.sqrt((hf[:n*FR].reshape(n, FR) ** 2).mean(1) + 1e-18)
    k = max(1, n // 10); floor = 20 * np.log10(np.sort(rh)[:k].mean()); rms = 20 * np.log10(r.mean()); clicks = int((np.abs(np.diff(y)) > 0.25).sum())
    return round(float(floor), 1), round(float(rms), 1), clicks
lib = json.load(open(LIB / "library.json")) if (LIB / "library.json").exists() else {}
only = sys.argv[1:]
for key, (q, maxdur, n) in QUERIES.items():
    if only and key not in only: continue
    url = "https://freesound.org/search/?" + urllib.parse.urlencode({"q": q, "f": f'license:"Creative Commons 0" duration:[0.3 TO {maxdur}]', "s": "downloads_desc"})
    html = get(url).decode("utf8", "ignore")
    hits = re.findall(r'data-sound-id="(\d+)"\s+data-username="([^"]+)".*?data-mp3="([^"]+)".*?data-title="([^"]*)"\s+data-duration="([\d.]+)"', html, re.S)
    got = 0
    for sid, user, mp3, title, dur in hits:
        if got >= n: break
        out = LIB / f"{key}_{sid}.wav"
        if out.exists(): got += 1; continue
        page = get(f"https://freesound.org/people/{user}/sounds/{sid}/").decode("utf8", "ignore")
        lic = "Creative Commons 0" if ("Creative Commons 0" in page or "creativecommons.org/publicdomain/zero" in page) else "UNKNOWN"
        if lic != "Creative Commons 0": print(f"  skip {sid} {title}: licence not CC0 on the page"); continue
        hq = mp3.replace("-lq.mp3", "-hq.mp3"); raw = LIB / f"{key}_{sid}.mp3"
        try: raw.write_bytes(get(hq))
        except Exception: raw.write_bytes(get(mp3)); hq = mp3
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-ar", "48000", "-ac", "1", str(out)], check=True); raw.unlink()
        floor, rms, clicks = measure(out)
        lib[out.name] = {"query": q, "id": int(sid), "title": title, "author": user, "licence": "CC0 1.0 (Creative Commons 0)", "url": f"https://freesound.org/s/{sid}/",
                         "preview": hq, "duration": float(dur), "hf_floor_db": floor, "rms_db": rms, "clicks": clicks}
        print(f"{key}: {sid} {title[:50]!r} by {user} {float(dur):.1f}s floor {floor} rms {rms} clicks {clicks}", flush=True); got += 1
    if not got: print(f"{key}: NOTHING for {q!r}")
json.dump(lib, open(LIB / "library.json", "w"), indent=1)
with open(LIB / "LICENSES.md", "w") as f:
    f.write("# sfx/library — every file's source and licence (v5.2, fetched 2026-11-18)\nAll files: Freesound, licence CC0 1.0 (Creative Commons 0, no attribution required; recorded anyway). 128 kbps preview renders converted to 48 kHz mono wav.\n\n| file | title | author | licence | source |\n|---|---|---|---|---|\n")
    for k, v in sorted(lib.items()): f.write(f"| {k} | {v['title']} | {v['author']} | {v['licence']} | {v['url']} |\n")
print("library:", len(lib), "files")
