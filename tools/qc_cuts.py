#!/usr/bin/env python3
"""qc_cuts — look at EVERY frame of EVERY cut, not one frame per 1.5 s.

Born 2026-11-02 from Last Signal v2. A review that sampled one frame per 1.5 s missed a
sub-second sprint cut where the captain's face changed identity frame to frame and she ran
in place. This tool walks every cut in the EDL at 12 fps (all frames when the cut is shorter
than 12 frames), writes one labeled strip per cut, and flags two things with plain code:

  1. FACE DRIFT   insightface (buffalo_l, the same ArcFace model face_check / face_lock use) embeds the
                  main face in each frame. A frame is flagged when its cosine to the cut's median
                  embedding OR to the reference face falls under a threshold.
  2. RUN IN PLACE cuts tagged running/sprint/walk (by id or EDL prompt words): the main person's height
                  (face bbox, else HOG person box) must change by more than MIN_MOTION across the cut.

CPU only (onnxruntime CPUExecutionProvider), safe to run next to a big GPU job.
Read every strip before calling a render done; the flags only tell you where to look first.

Usage (ComfyUI venv has insightface + onnxruntime):
  ~/AI/ComfyUI/venv/bin/python tools/qc_cuts.py <final_video.mp4> <edl.json> [--out DIR] [--ref canon/captain.png]
Writes DIR/strips/<k>_<id>.jpg, DIR/index.jpg, DIR/qc_report.json, DIR/qc_summary.txt. Exit 1 if any cut is flagged.
"""
import argparse, json, re, subprocess, sys, tempfile
from pathlib import Path

import warnings
warnings.filterwarnings("ignore")
import cv2
import numpy as np

FPS_SAMPLE = 12
THRESH_MEDIAN = 0.72  # worst frame vs the cut's own median face. Tuned on Last Signal v2 (24 fps, 832x480 upscaled):
                      # BAD c14b_sprint 0.70, c15c_sprint 0.68; GOOD face-locked c07b 0.87, c09 0.98, c06b 0.97;
                      # every other steady cut 0.76-0.97. A moving face drifting between frames lands under 0.72.
THRESH_REF = 0.10     # worst frame vs the reference portrait; only counted when the cut is ALSO unstable
                      # (median sim under REF_GATE). A steady non-captain face (screams, crew) is far from the
                      # captain reference by design, so reference distance alone is reported, never flagged.
REF_GATE = 0.75
MIN_FACE = 24         # px in the 1080p frame; smaller faces are skipped (not trusted)
MIN_FACE_FRAMES = 3   # a cut needs this many face frames to be judged
MIN_MOTION = 0.08     # a mover's height must change more than 8% across the cut
MOVE_WORDS = re.compile(r"sprint|run|running|runs|walk|walking|dash|jog|flee|chase", re.I)
THUMB_H = 200

_app = None
_hog = None


def app():
    global _app
    if _app is None:
        import contextlib
        from insightface.app import FaceAnalysis
        with contextlib.redirect_stdout(sys.stderr):
            _app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
            _app.prepare(ctx_id=-1, det_size=(640, 640))
    return _app


def main_face(img):
    fs = app().get(img)
    fs = [f for f in fs if (f.bbox[3] - f.bbox[1]) >= MIN_FACE]
    if not fs:
        return None
    f = max(fs, key=lambda f: (f.bbox[3] - f.bbox[1]) * float(f.det_score))
    return {"emb": f.normed_embedding, "h": float(f.bbox[3] - f.bbox[1])}


def person_height(img):
    """Tallest HOG person box height (px), or None."""
    global _hog
    if _hog is None:
        _hog = cv2.HOGDescriptor()
        _hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    s = 480.0 / img.shape[0]
    small = cv2.resize(img, None, fx=s, fy=s)
    rects, w = _hog.detectMultiScale(small, winStride=(8, 8), scale=1.05)
    if len(rects) == 0:
        return None
    i = int(np.argmax(w))
    return float(rects[i][3]) / s


def extract(video, start, length, vfps, tmp):
    """Consecutive frames of one cut: all frames if < 12, else 12 fps. Returns list of BGR images."""
    n_all = max(1, int(round(length * vfps)))
    vf = ["fps=%d" % FPS_SAMPLE] if n_all > FPS_SAMPLE else []
    for p in tmp.glob("*.png"):
        p.unlink()
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.4f}", "-i", str(video), "-t", f"{length:.4f}"]
    if vf:
        cmd += ["-vf", ",".join(vf)]
    cmd += ["-frames:v", str(min(n_all, max(FPS_SAMPLE, int(length * FPS_SAMPLE) + 1))), str(tmp / "f%03d.png")]
    subprocess.run(cmd, check=False)
    return [cv2.imread(str(p)) for p in sorted(tmp.glob("f*.png"))]


def cos(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def label(img, text):
    cv2.rectangle(img, (0, 0), (img.shape[1], 22), (0, 0, 0), -1)
    cv2.putText(img, text, (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    return img


def strip(frames, text, sims, col_w=None):
    th = []
    for i, f in enumerate(frames):
        t = cv2.resize(f, (int(f.shape[1] * THUMB_H / f.shape[0]), THUMB_H))
        if sims and sims[i] is not None:
            bad = sims[i] < THRESH_MEDIAN
            cv2.putText(t, f"{sims[i]:.2f}", (4, THUMB_H - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0, 0, 255) if bad else (0, 255, 0), 1, cv2.LINE_AA)
        th.append(t)
    rows, per = [], 8        # wrap at 8 frames per row so a 12-frame cut stays readable
    for i in range(0, len(th), per):
        r = th[i:i + per]
        pad = per * th[0].shape[1] - sum(x.shape[1] for x in r)
        rows.append(np.hstack(r + ([np.zeros((THUMB_H, pad, 3), np.uint8)] if pad else [])))
    body = np.vstack(rows)
    head = np.zeros((24, body.shape[1], 3), np.uint8)
    return np.vstack([label(head, text), body])


def find_ref(edl_path: Path, ref_arg):
    if ref_arg:
        return Path(ref_arg)
    for d in [edl_path.resolve().parent] + list(edl_path.resolve().parents):
        if (d / "canon" / "captain.png").exists():
            return d / "canon" / "captain.png"
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("video"); ap.add_argument("edl")
    ap.add_argument("--out", default=None, help="default: ./qc_cuts_<video stem>")
    ap.add_argument("--ref", default=None, help="reference face image (default: canon/captain.png of the project)")
    ap.add_argument("--thresh", type=float, default=THRESH_MEDIAN, help="min cosine vs the cut's median face")
    ap.add_argument("--thresh-ref", type=float, default=THRESH_REF, help="min cosine vs the reference face")
    a = ap.parse_args()
    video, edl_path = Path(a.video), Path(a.edl)
    out = Path(a.out or f"qc_cuts_{video.stem}")
    (out / "strips").mkdir(parents=True, exist_ok=True)
    edl = json.loads(edl_path.read_text())
    cuts = edl["cuts"] if isinstance(edl, dict) else edl
    cap = cv2.VideoCapture(str(video)); vfps = cap.get(cv2.CAP_PROP_FPS) or edl.get("fps", 24); cap.release()

    ref_emb, ref_path = None, find_ref(edl_path, a.ref)
    if ref_path and ref_path.exists():
        r = main_face(cv2.imread(str(ref_path)))
        ref_emb = r["emb"] if r else None
    if ref_emb is None:
        print("WARN: no usable reference face; checking vs cut median only", file=sys.stderr)

    report, tiles = [], []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for k, c in enumerate(cuts):
            cid, start, length = c["id"], float(c["start"]), float(c["len"])
            frames = [f for f in extract(video, start, length, vfps, tmp) if f is not None]
            faces = [main_face(f) for f in frames]
            have = [i for i, f in enumerate(faces) if f]
            flags, row = [], {"k": k, "id": cid, "start": start, "len": length, "frames": len(frames),
                              "face_frames": len(have)}
            sims = [None] * len(frames)
            if len(have) >= MIN_FACE_FRAMES:
                embs = np.array([faces[i]["emb"] for i in have])
                med = np.median(embs, axis=0)
                sm = [cos(faces[i]["emb"], med) for i in have]
                for i, s in zip(have, sm):
                    sims[i] = s
                row["min_sim_median"] = round(min(sm), 3)
                if min(sm) < a.thresh:
                    flags.append(f"face identity drifts inside the cut (worst frame {min(sm):.2f} vs the cut's median face, "
                                 f"limit {a.thresh:.2f}; {sum(s < a.thresh for s in sm)} of {len(sm)} frames)")
                if ref_emb is not None:
                    sr = [cos(faces[i]["emb"], ref_emb) for i in have]
                    row["min_sim_ref"] = round(min(sr), 3); row["mean_sim_ref"] = round(float(np.mean(sr)), 3)
                    if min(sr) < a.thresh_ref and min(sm) < REF_GATE:
                        flags.append(f"face is unstable AND off the reference (worst frame {min(sr):.2f}, limit {a.thresh_ref:.2f})")
            text = " ".join(str(c.get(k2, "")) for k2 in ("id", "prompt", "motion_prompt", "desc", "note"))
            if MOVE_WORDS.search(text) and len(frames) >= 4:
                hs = [faces[i]["h"] for i in have] if len(have) >= MIN_FACE_FRAMES else \
                     [h for h in (person_height(f) for f in frames) if h]
                if len(hs) >= MIN_FACE_FRAMES:
                    change = (max(hs) - min(hs)) / max(float(np.median(hs)), 1e-6)
                    row["height_change"] = round(change, 3)
                    if change < MIN_MOTION:
                        flags.append(f"tagged as moving but the person's height changes only {change*100:.1f}% "
                                     f"(under {MIN_MOTION*100:.0f}%): running in place?")
                else:
                    row["height_change"] = None
            row["flags"] = flags
            lab = f"#{k} {cid}  t={start:.2f}-{start+length:.2f}s  {len(frames)}f" + ("  FLAG" if flags else "")
            img = strip(frames, lab, sims) if frames else np.zeros((60, 400, 3), np.uint8)
            cv2.imwrite(str(out / "strips" / f"{k:02d}_{cid}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 88])
            first = frames[len(frames) // 2] if frames else np.zeros((90, 160, 3), np.uint8)
            t = cv2.resize(first, (240, 135))
            if flags:
                cv2.rectangle(t, (0, 0), (239, 134), (0, 0, 255), 4)
            tiles.append(label(t, f"{k} {cid}"[:34]))
            report.append(row)
            print(f"[{k+1}/{len(cuts)}] {cid}: {'FLAG' if flags else 'ok'}", file=sys.stderr)

    cols = 5
    while len(tiles) % cols:
        tiles.append(np.zeros((135, 240, 3), np.uint8))
    sheet = np.vstack([np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)])
    cv2.imwrite(str(out / "index.jpg"), sheet, [cv2.IMWRITE_JPEG_QUALITY, 85])
    flagged = [r for r in report if r["flags"]]
    (out / "qc_report.json").write_text(json.dumps(
        {"video": str(video), "edl": str(edl_path), "ref": str(ref_path) if ref_path else None,
         "thresh_median": a.thresh, "thresh_ref": a.thresh_ref, "min_motion": MIN_MOTION,
         "flagged": [r["id"] for r in flagged], "cuts": report}, indent=1))
    lines = [f"qc_cuts: {len(report)} cuts checked, {len(flagged)} flagged  ({video.name})"]
    for r in flagged:
        lines.append(f"  {r['id']} @ {r['start']:.2f}s: " + "; ".join(r["flags"]))
    lines.append(f"Read every strip in {out/'strips'} before calling this render done.")
    (out / "qc_summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(1 if flagged else 0)


if __name__ == "__main__":
    main()
