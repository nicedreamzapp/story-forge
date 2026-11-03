#!/usr/bin/env python3
"""poster_frame.py — a poster.jpg for every deliverable: the best frame of the final beat.

WHY THIS EXISTS (2026-11-02): platforms show a still before anyone presses play, and each deliverable
(16:9, 9:16) is its own composition, so each gets its own poster from its own pixels. The thumbnail
(promo_deliver's branded 1280x720) is a designed card; the poster is a real frame, full size, that a
player, a site embed or a Reel cover can use as is.

Where the frame comes from, first match wins:
  1. a QC jury pick: any final/*.json (film_qc / harsh jury report) carrying "poster", "poster_t" or
     "poster_candidate" ({"t": seconds} or a bare number, on THIS video's timeline; a "video" key, when
     present, must name this file)
  2. the best frame of the FINAL BEAT: promo = the last narration line (vo/words.json), before the end
     card; film = the last 25 % of the cut, minus black and title/credit cards; else the last 25 % of the
     video minus its last second. ~24 candidates, never within 2 frames of a cut, scored on sharpness
     (Laplacian variance), exposure, contrast, colour and a face bonus (Apple Vision, when the probe exists).
Usage:
  ~/chatterbox-env/bin/python pipeline-tools/poster_frame.py VIDEO --out poster.jpg [--film projects/<film>]
        [--edl edl.json] [--window A B]
Writes the jpg and <out>.json (the time, where it came from, the scores). Exit 0 = written, 2 = no frame.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def duration(f: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def qc_pick(film: Path | None, video: Path) -> float | None:
    if not film or not (film / "final").exists():
        return None
    for j in sorted((film / "final").rglob("*.json")):
        try:
            d = json.loads(j.read_text())
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        for k in ("poster", "poster_candidate", "poster_t"):
            v = d.get(k)
            if v is None:
                continue
            if isinstance(v, dict):
                if v.get("video") and Path(v["video"]).name != video.name:
                    continue
                v = v.get("t")
            try:
                return float(v)
            except (TypeError, ValueError):
                continue
    return None


def final_beat(film: Path | None, edl: dict | None, dur: float) -> tuple:
    """(start, end, cut times, why) of the last beat on this video's timeline."""
    cuts = []
    if edl and edl.get("shots"):
        cuts = [float(s["rec_in"]) for s in edl["shots"]]
        texty = re.compile(r"(title|credit|card|black)", re.I)
        ok = [s for s in edl["shots"] if s.get("kind") != "black" and s.get("file") and not s.get("fit") == "pad"
              and not texty.search(str(s.get("section", ""))) and not texty.search(str(s.get("cid", "")))]
        if film and (film / "vo" / "words.json").exists():
            lines = json.loads((film / "vo" / "words.json").read_text()).get("lines", [])
            if lines:
                a, b = float(lines[-1]["start"]), float(lines[-1]["end"])
                if edl.get("endcard"):
                    b = min(b, float(edl["endcard"]["rec_in"]) - 0.05)
                return a, b, cuts, f"the last narration line ({a:.2f}-{b:.2f}s)"
        if ok:
            end = max(float(s["rec_out"]) for s in ok)
            start = max(0.0, end - 0.25 * end)
            return start, end, cuts, f"the last 25 % of the cut ({start:.2f}-{end:.2f}s)"
    return max(0.0, dur * 0.75), max(0.0, dur - 1.0), cuts, "the last 25 % of the video"


def score_frames(pngs: list) -> list:
    import numpy as np
    from PIL import Image
    try:
        import cv2
    except Exception:
        cv2 = None
    rows = []
    for p in pngs:
        im = np.asarray(Image.open(p).convert("RGB")).astype("float32") / 255
        g = im.mean(axis=2)
        if cv2 is not None:
            sharp = float(cv2.Laplacian((g * 255).astype("uint8"), cv2.CV_64F).var())
        else:
            sharp = float(np.var(np.diff(g, axis=0)) + np.var(np.diff(g, axis=1))) * 1e4
        rg, yb = im[..., 0] - im[..., 1], 0.5 * (im[..., 0] + im[..., 1]) - im[..., 2]
        colour = float(np.sqrt(rg.std() ** 2 + yb.std() ** 2) + 0.3 * np.sqrt(rg.mean() ** 2 + yb.mean() ** 2))
        rows.append({"sharp": sharp, "exposure": 1 - min(1.0, abs(float(g.mean()) - 0.42) * 2.2),
                     "contrast": float(g.std()), "colour": colour, "clipped": float((g > 0.98).mean() + (g < 0.02).mean())})
    faces = [0.0] * len(pngs)
    try:
        import reframe
        for k, d in enumerate(reframe.probe(pngs)):
            fs = [f for f in d.get("faces", []) if f[4] >= 0.5]
            faces[k] = min(1.0, max((f[2] * f[3] for f in fs), default=0.0) * 12)
    except Exception:
        pass
    mx = {k: max(r[k] for r in rows) or 1.0 for k in ("sharp", "contrast", "colour")}
    for r, f in zip(rows, faces):
        r["face"] = f
        r["score"] = round(0.40 * r["sharp"] / mx["sharp"] + 0.20 * r["exposure"] + 0.15 * r["contrast"] / mx["contrast"]
                           + 0.10 * r["colour"] / mx["colour"] + 0.15 * f - 0.5 * r["clipped"], 4)
    return rows


def grab(video: Path, t: float, out: Path, scale: str | None = None) -> bool:
    vf = ["-vf", f"scale={scale}"] if scale else []
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1"] + vf
                   + ["-q:v", "2", str(out)], capture_output=True)
    return out.exists() and out.stat().st_size > 0


def make_poster(video: Path, out: Path, film: Path | None = None, edl: dict | None = None,
                window: tuple | None = None) -> dict:
    dur = duration(video)
    fps = float((edl or {}).get("fps", 30))
    t_qc = qc_pick(film, video)
    if t_qc is not None and 0 <= t_qc <= dur:
        if not grab(video, t_qc, out):
            raise RuntimeError("could not grab the QC jury's poster frame")
        meta = {"t": round(t_qc, 3), "source": "qc jury pick", "video": video.name}
    else:
        a, b, cuts, why = final_beat(film, edl, dur)
        if window:
            a, b, why = window[0], window[1], f"the given window ({window[0]:.2f}-{window[1]:.2f}s)"
        a, b = max(0.0, a), min(dur - 1 / fps, b)
        if b <= a:
            a, b = max(0.0, dur * 0.75), max(0.0, dur - 1.0)
        n = 24
        ts = [a + (b - a) * (k + 0.5) / n for k in range(n)]
        ts = [t for t in ts if all(abs(t - c) > 2 / fps for c in cuts)] or ts
        with tempfile.TemporaryDirectory() as td:
            pngs, keep = [], []
            for k, t in enumerate(ts):
                p = Path(td) / f"{k:02d}.png"
                if grab(video, t, p, "480:-2"):
                    pngs.append(p)
                    keep.append(t)
            if not pngs:
                raise RuntimeError("no frames in the final beat")
            rows = score_frames(pngs)
        best = max(range(len(rows)), key=lambda k: rows[k]["score"])
        if not grab(video, keep[best], out):
            raise RuntimeError("could not grab the poster frame")
        meta = {"t": round(keep[best], 3), "source": f"best frame of {why}", "video": video.name,
                "score": rows[best], "candidates": len(rows)}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1))
    return meta


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("video")
    ap.add_argument("--out", required=True)
    ap.add_argument("--film")
    ap.add_argument("--edl")
    ap.add_argument("--window", nargs=2, type=float)
    a = ap.parse_args()
    film = Path(a.film).resolve() if a.film else None
    edl = None
    if film and not a.edl:   # the project's own timeline: promo edl.json, film final/edl_final.json
        try:
            from vertical_compose import load_timeline
            edl = load_timeline(film)[1]
        except Exception:
            edl = None
    if a.edl:
        ep = Path(a.edl)
        edl = json.loads((ep if ep.is_absolute() or not film else film / ep).read_text())
    try:
        m = make_poster(Path(a.video), Path(a.out), film, edl, tuple(a.window) if a.window else None)
    except Exception as e:
        print(f"[poster] {e}", file=sys.stderr)
        return 2
    print(f"[poster] {a.out}: {m['t']:.2f}s, {m['source']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
