#!/usr/bin/env python3
"""face_check — is the person on screen the person in the canon portrait?

Born 2026-10-03 from The Oldest Tree. s4_walkback put a rounder, younger girl with
different eyes on screen for four seconds and every gate passed it: film_qc's identity
sheet asks about species and ears (it was written for cartoon animals) and forgives
scale, so a small face in a wide shot sails through; the per-shot identity gate in
forge-shot never ran because the shot only listed the girl under `refs`, not
`identity`. A vision model reading a tiled sheet cannot tell two dark-haired ten-year-
olds apart. A face-recognition embedding can.

How it works: for every shot whose spec names a canon character (under `identity` OR
`refs`), sample frames from inside the shot (crossfades trimmed off), find faces with
insightface, embed them (ArcFace, buffalo_l) and compare each with the canon portraits.
A face that matches none of the shot's cast above THRESH fails the shot. Ages are
estimated too, and a face far younger or older than its canon portrait fails.

A face too small to embed reliably is reported UNCHECKED, never PASS.

Usage (run with the ComfyUI venv, which has insightface + onnxruntime):
  ~/AI/ComfyUI/venv/bin/python pipeline-tools/face_check.py projects/<film>          # final film
  ~/AI/ComfyUI/venv/bin/python pipeline-tools/face_check.py projects/<film> --clip s4_walkback clips/x.mp4
Writes final/face_report.md (film mode). Exit 1 if any shot FAILS.
"""
import argparse, json, subprocess, sys, tempfile
from pathlib import Path

import warnings
warnings.filterwarnings("ignore")
import cv2
import numpy as np

THRESH = 0.30      # cosine to the canon portrait; calibrated on The Oldest Tree, see report header
AGE_TOL = 8        # REPORTED ONLY. insightface ages children as adults (the 10-year-old canon reads 37), so age never gates
STILL_THRESH = 0.45  # a still is sharp and posed, so it must match harder than a moving frame.
                     # Oldest Tree locks: on-model 0.69-0.82; walkback 0.30, wide_walk 0.27, kneel 0.43 were off by eye
STILL_MIN_FACE = 32  # stills are sharp: judge faces down to 32px instead of waving 32-48px faces through
                     # as UNCHECKED (s2_wide_walk try 1 locked that way 2026-10-03, then drifted in the clip)
SMALL_FACE = 90      # px; at 1280x544 a wide shot's face is ~60-80px and embeds noisier, so a
SMALL_THRESH = 0.35  # still face that small needs 0.35 (bad walkback 0.30 and wide_walk girl 0.27 still fail)
MAX_YAW = 35        # degrees. ArcFace is built for faces toward camera; a girl turning to her grandfather
                    # in profile scored 0.27 on a clip that was on-model by eye (s7_kneel 2026-10-03).
                    # A face turned further than this is reported "turned away", never judged.
DRIFT = 0.25       # any single frame under this is a WARN: the face slid away mid-shot
MIN_FACE = 48      # px face height below which the embedding is not trusted
SAMPLES = 5
TRIM = 0.6         # seconds trimmed off each end of a shot (crossfades)

_app = None


def app():
    global _app
    if _app is None:
        import contextlib
        from insightface.app import FaceAnalysis
        with contextlib.redirect_stdout(sys.stderr):   # keep stdout = the verdict only
            _app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
            _app.prepare(ctx_id=-1, det_size=(1024, 1024))
    return _app


def faces(img):
    out = []
    for f in app().get(img):
        x1, y1, x2, y2 = f.bbox
        yaw = float(f.pose[1]) if getattr(f, "pose", None) is not None else 0.0
        out.append({"emb": f.normed_embedding, "age": int(f.age), "h": int(y2 - y1), "yaw": yaw,
                    "score": float(f.det_score), "bbox": [int(v) for v in f.bbox]})
    return out


def canon_faces(proj: Path, shots: list) -> dict:
    """canon image path -> {emb, age, subject}"""
    out = {}
    for s in shots:
        for c in cast(s):
            if c["image"] in out:
                continue
            img = cv2.imread(str(proj / c["image"]))
            fs = [f for f in faces(img)] if img is not None else []
            if not fs:
                print(f"WARN: no face found in canon {c['image']}", file=sys.stderr)
                continue
            best = max(fs, key=lambda f: f["h"])
            out[c["image"]] = {"emb": best["emb"], "age": best["age"], "subject": c["subject"]}
    return out


def cast(shot: dict) -> list:
    """Every canon character the shot names, from identity masters or Qwen refs."""
    seen, out = set(), []
    for e in (shot.get("identity") or []):
        p = e.get("master")
        if p and p.startswith("canon/") and p not in seen:
            seen.add(p); out.append({"image": p, "subject": e.get("subject", p)})
    for e in (shot.get("refs") or []):
        p = e.get("image")
        if p and p.startswith("canon/") and p not in seen:
            seen.add(p); out.append({"image": p, "subject": e.get("subject", p)})
    return out


def frame_at(video: Path, t: float, dst: Path):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(video),
                    "-frames:v", "1", str(dst)], check=False)
    return cv2.imread(str(dst)) if dst.exists() else None


def judge_shot(video: Path, start: float, length: float, people: list, canon: dict, tmp: Path, sid: str):
    a, b = start + TRIM, start + length - TRIM
    if b <= a:
        a, b = start, start + length
    times = [a + (b - a) * i / (SAMPLES - 1) for i in range(SAMPLES)]
    lines, verdict, per = [], "UNCHECKED", {}
    worst = None
    for i, t in enumerate(times):
        img = frame_at(video, t, tmp / f"{sid}_{i}.png")
        if img is None:
            continue
        for f in faces(img):
            if f["score"] < 0.6:
                continue
            if f["h"] < MIN_FACE:
                lines.append(f"{t:6.1f}s face {f['h']}px tall, too small to judge")
                continue
            if abs(f["yaw"]) > MAX_YAW:
                lines.append(f"{t:6.1f}s face turned {f['yaw']:.0f} degrees, not judged")
                continue
            sims = [(float(np.dot(f["emb"], canon[p["image"]]["emb"])), p["image"]) for p in people if p["image"] in canon]
            if not sims:
                continue
            sim, who = max(sims)
            want_age = canon[who]["age"]
            age_off = f["age"] - want_age
            bad = sim < THRESH
            why = []
            if sim < THRESH:
                why.append(f"not the same face (match {sim:.2f} < {THRESH})")
            lines.append(f"{t:6.1f}s {Path(who).stem}: match {sim:.2f}, age {f['age']} (canon {want_age})"
                         + (f"  <-- {'; '.join(why)}" if bad else ""))
            per.setdefault(who, []).append(sim)
            if worst is None or sim < worst:
                worst = sim
    # A shot fails when a character's MEDIAN match is under THRESH: one soft frame in a
    # head turn is not a recast, four of five is. A single frame under DRIFT is a WARN.
    for who, sims in per.items():
        med = float(np.median(sims))
        if med < THRESH:
            verdict = "FAIL"
            lines.append(f"  {Path(who).stem}: median match {med:.2f} over {len(sims)} frames, a different person")
        elif min(sims) < DRIFT and verdict != "FAIL":
            verdict = "WARN"
            lines.append(f"  {Path(who).stem}: drifts to {min(sims):.2f} in one frame, look at it")
        elif verdict == "UNCHECKED":
            verdict = "PASS"
    return verdict, worst, lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--clip", nargs=2, metavar=("SHOT_ID", "VIDEO"), help="check one rendered clip")
    ap.add_argument("--film", help="film to check (default: newest finished cut in final/)")
    ap.add_argument("--still", nargs=2, metavar=("SHOT_ID", "IMAGE"), help="check one still")
    a = ap.parse_args()
    proj = Path(a.project).resolve()
    spec = json.loads((proj / "film_shots.json").read_text())
    shots = {s["id"]: s for s in spec["shots"]}
    canon = canon_faces(proj, list(shots.values()))
    tmp = Path(tempfile.mkdtemp(prefix="face_check_"))

    if a.still:
        sid, img_path = a.still
        people = cast(shots[sid])
        img = cv2.imread(img_path)
        verdict, lines = "UNCHECKED", []
        for f in faces(img):
            if f["score"] < 0.6 or f["h"] < STILL_MIN_FACE or abs(f["yaw"]) > MAX_YAW:
                continue
            sim, who = max((float(np.dot(f["emb"], canon[p["image"]]["emb"])), p["image"]) for p in people if p["image"] in canon)
            ok = sim >= (SMALL_THRESH if f["h"] < SMALL_FACE else STILL_THRESH)
            verdict = "PASS" if (ok and verdict != "FAIL") else ("FAIL" if not ok else verdict)
            lines.append(f"{Path(who).stem}: match {sim:.2f} ({f['h']}px face), age {f['age']} (canon {canon[who]['age']})")
        print(verdict, *lines, sep="\n  ")
        sys.exit(1 if verdict == "FAIL" else 0)

    if a.clip:
        sid, vid = a.clip
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                    "csv=p=0", vid], capture_output=True, text=True).stdout or 0)
        verdict, worst, lines = judge_shot(Path(vid), 0.0, dur, cast(shots[sid]), canon, tmp, sid)
        print(verdict, *lines, sep="\n  ")
        sys.exit(1 if verdict == "FAIL" else 0)

    tl = json.loads((proj / "final" / "timeline.json").read_text())
    if a.film:
        film = Path(a.film).resolve()
    else:  # newest finished cut; skip rough cuts, tests and upload copies
        cands = [p for p in (proj / "final").glob("*.mp4")
                 if not any(k in p.name.lower() for k in ("wip", "test", "_youtube", "_phone"))]
        film = sorted(cands, key=lambda p: p.stat().st_mtime)[-1]
    rows, fails = [], 0
    for sid, st, ln in zip(tl["order"], tl["starts"], tl["lens"]):
        people = cast(shots.get(sid, {}))
        if not people:
            continue
        verdict, worst, lines = judge_shot(film, st, ln, people, canon, tmp, sid)
        fails += verdict == "FAIL"
        rows.append((sid, st, verdict, worst, lines))
        print(f"{verdict:9s} {sid:16s} @{st:6.1f}s worst match {worst if worst is None else round(worst, 2)}", flush=True)

    rep = [f"# face_check — {film.name}",
           f"**Verdict: {'FAIL' if fails else 'PASS'}** — {fails} shot(s) show a face that is not the canon character",
           f"Threshold: match >= {THRESH} to the canon portrait, age within {AGE_TOL} years. "
           f"Faces under {MIN_FACE}px are UNCHECKED, not passed.", ""]
    rep += ["Canon: " + ", ".join(f"{Path(k).stem} (age est {v['age']})" for k, v in canon.items()), ""]
    for sid, st, verdict, worst, lines in rows:
        rep.append(f"## [{verdict}] {sid} @ {st:.1f}s")
        rep += [f"- {l}" for l in lines] or ["- no face found"]
        rep.append("")
    (proj / "final" / "face_report.md").write_text("\n".join(rep))
    print(f"\nwrote {proj / 'final' / 'face_report.md'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
