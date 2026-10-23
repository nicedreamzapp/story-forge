#!/usr/bin/env python3
"""ingest_acquired.py — every take the film could cut to, probed, in one manifest.

Promo stage 04_footage → 05_selects (pipeline/formats/promo/SCHEMAS.md, manifest.json). Sources:
  * projects/<film>/acquired/provenance.json takes (browser AI tools: ChatGPT images, Grok video)
  * any other media file in acquired/ (its <file>.json sidecar if present, else the
    `<id>_<n>` name, with the line read from an `lNN_` prefix)
  * every coverage.json setup that names a `file` (CAD renders, local clips)
Each is probed (ffprobe dur/w/h/fps; images are kind=image) and video gets PySceneDetect
cuts (`shots`). Idempotent: an unchanged file keeps its probe and its checks; a changed file
(bytes or mtime differ) has its checks reset to null, because a verdict on the old file is
not a verdict on the new one.

Extra manifest fields beyond SCHEMAS.md (added 2026-10-22): `bytes`, `mtime` (change
detection), `origin` ("acquired" | "coverage"), `id`/`n` when known.

Usage:  python pipeline-tools/ingest_acquired.py projects/<film> [--threshold 27]
Exit 0 = manifest written; 1 = written but some listed takes were missing on disk;
2 = could not run.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}
VID_EXT = {".mp4", ".mov", ".webm", ".m4v", ".mkv"}
# PySceneDetect is not in the mlx venv; the LatentSync venv carries it (0.6.1).
SCENE_PYS = [Path.home() / "AI_Models/LatentSync/.venv/bin/python",
             Path.home() / ".local/mlx-server/bin/python"]
SCENE_SNIPPET = r"""
import json, sys
from scenedetect import detect, ContentDetector
out = {}
for p in sys.argv[2:]:
    try:
        sc = detect(p, ContentDetector(threshold=float(sys.argv[1])))
        out[p] = [[round(a.get_seconds(), 3), round(b.get_seconds(), 3)] for a, b in sc]
    except Exception as e:
        out[p] = {"error": str(e)}
print("@@" + json.dumps(out))
"""


def probe(path: Path) -> dict:
    if path.suffix.lower() in IMG_EXT:
        try:
            from PIL import Image
            with Image.open(path) as im:
                w, h = im.size
        except Exception:                                    # noqa: BLE001
            r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                "stream=width,height", "-of", "json", str(path)],
                               capture_output=True, text=True)
            s = (json.loads(r.stdout or "{}").get("streams") or [{}])[0]
            w, h = s.get("width"), s.get("height")
        return {"kind": "image", "dur": None, "w": w, "h": h, "fps": None}
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(path)],
                       capture_output=True, text=True)
    j = json.loads(r.stdout or "{}")
    s = (j.get("streams") or [{}])[0]
    num, _, den = (s.get("r_frame_rate") or "0/1").partition("/")
    fps = round(float(num) / float(den or 1), 3) if float(den or 1) else None
    try:
        dur = round(float(j.get("format", {}).get("duration")), 3)
    except (TypeError, ValueError):
        dur = None
    return {"kind": "video", "dur": dur, "w": s.get("width"), "h": s.get("height"),
            "fps": int(fps) if fps and fps == int(fps) else fps}


def scene_cuts(paths: list, threshold: float) -> dict:
    """{path: [[start, end], ...]} via PySceneDetect in whichever venv has it."""
    if not paths:
        return {}
    for py in SCENE_PYS:
        if not py.exists():
            continue
        r = subprocess.run([str(py), "-c", SCENE_SNIPPET, str(threshold)] + [str(p) for p in paths],
                           capture_output=True, text=True, timeout=1800)
        for line in r.stdout.splitlines():
            if line.startswith("@@"):
                return json.loads(line[2:])
    print("[ingest] WARNING: PySceneDetect not found in any venv — shots = whole file",
          file=sys.stderr)
    return {}


def line_from(name: str):
    m = re.match(r"^l(\d+)[_-]", name)
    return int(m.group(1)) if m else None


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40]


def gather(film: Path) -> tuple[list, list]:
    """Candidate stubs (no probe yet) from provenance, loose acquired files and coverage."""
    stubs, missing, seen = [], [], set()
    acq = film / "acquired"
    prov = acq / "provenance.json"
    if prov.exists():
        for t in json.loads(prov.read_text()).get("takes", []):
            rel = t["file"]
            if not (film / rel).exists():
                missing.append(rel)
                continue
            seen.add(rel)
            # cid = <id>_<n> (a blender take's file is acquired/blender/<id>/beauty.mp4: the stem alone collides)
            cid = f"{t['id']}_{t['n']}" if t.get("id") and t.get("n") else Path(rel).stem
            stubs.append({"cid": cid, "file": rel, "source": t.get("backend"),
                          "line": t.get("line"), "setup": t.get("setup"), "id": t.get("id"),
                          "n": t.get("n"), "origin": "acquired"})
    if acq.is_dir():
        for p in sorted(acq.iterdir()):
            if p.suffix.lower() not in IMG_EXT | VID_EXT:
                continue
            rel = str(p.relative_to(film))
            if rel in seen:
                continue
            side = p.with_name(p.name + ".json")
            meta = json.loads(side.read_text()) if side.exists() else {}
            m = re.match(r"^(.*)_(\d+)$", p.stem)
            seen.add(rel)
            stubs.append({"cid": p.stem, "file": rel,
                          "source": meta.get("backend") or ("chatgpt-image" if p.suffix.lower() in IMG_EXT
                                                            else "grok-video"),
                          "line": meta.get("line", line_from(p.stem)), "setup": meta.get("setup"),
                          "id": meta.get("id", m.group(1) if m else p.stem),
                          "n": meta.get("n", int(m.group(2)) if m else None), "origin": "acquired",
                          **({} if meta else {"source_guessed": True})})
    cov = film / "coverage.json"
    if cov.exists():
        for ln in json.loads(cov.read_text()).get("lines", []):
            for k, su in enumerate(ln.get("setups", [])):
                rel = su.get("file")
                if not rel or rel in seen:
                    continue
                if not (film / rel).exists():
                    missing.append(rel)
                    continue
                seen.add(rel)
                stubs.append({"cid": f"l{int(ln['line']):02d}_{su.get('source', 'x')}_{slug(Path(rel).stem)}",
                              "file": rel, "source": su.get("source"), "line": ln["line"],
                              "setup": su.get("setup"), "origin": "coverage",
                              "design_profile": su.get("design")})
    return stubs, missing


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("film")
    ap.add_argument("--threshold", type=float, default=27.0, help="ContentDetector threshold")
    a = ap.parse_args()
    film = Path(a.film).resolve()
    if not film.is_dir():
        print(f"[ingest] no film dir {film}", file=sys.stderr)
        return 2
    man_path = film / "manifest.json"
    prior = json.loads(man_path.read_text()) if man_path.exists() else {}
    old = {c["file"]: c for c in prior.get("candidates", [])}

    stubs, missing = gather(film)
    cands, to_scan = [], []
    for s in stubs:
        p = film / s["file"]
        st = p.stat()
        o = old.get(s["file"])
        fresh = o and o.get("bytes") == st.st_size and o.get("mtime") == int(st.st_mtime)
        c = dict(o) if fresh else {}
        c.update({k: v for k, v in s.items() if v is not None or k not in c})
        if not fresh:
            c.update(probe(p))
            c["bytes"], c["mtime"] = st.st_size, int(st.st_mtime)
            c["checks"] = {"design": None, "faces": None}
            c["shots"] = [] if c["kind"] == "image" else None
            if o:
                print(f"[ingest] {s['file']} changed on disk — checks reset", file=sys.stderr)
        c.setdefault("checks", {"design": None, "faces": None})
        if c["kind"] == "video" and not c.get("shots"):
            to_scan.append(str(p))
        cands.append(c)

    cuts = scene_cuts(to_scan, a.threshold)
    for c in cands:
        key = str(film / c["file"])
        if key in to_scan:
            got = cuts.get(key)
            if isinstance(got, list) and got:
                c["shots"] = got
            else:
                c["shots"] = [[0.0, c.get("dur") or 0.0]]   # one shot, no internal cut found

    order = ["cid", "file", "kind", "source", "line", "setup", "dur", "w", "h", "fps", "shots",
             "checks"]
    cands = [{**{k: c.get(k) for k in order}, **{k: v for k, v in c.items() if k not in order}}
             for c in sorted(cands, key=lambda c: ((c.get("line") or 999), c["cid"]))]
    man = {"fps": prior.get("fps", 30), "w": prior.get("w", 1920), "h": prior.get("h", 1080),
           "candidates": cands}
    tmp = man_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(man, indent=1))
    tmp.replace(man_path)

    vids = [c for c in cands if c["kind"] == "video"]
    secs = sum(c.get("dur") or 0 for c in vids)
    print(f"[ingest] {len(cands)} candidates ({len(vids)} video, {len(cands) - len(vids)} still), "
          f"{secs:.1f}s of video, {len(to_scan)} scanned for cuts → {man_path}")
    for c in cands:
        if c.get("line") is None:
            print(f"[ingest] WARNING {c['cid']}: no narration line (name it lNN_... or add provenance)")
    for m in missing:
        print(f"[ingest] MISSING on disk: {m}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
