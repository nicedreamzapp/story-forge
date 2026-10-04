#!/usr/bin/env python3
"""face_lock — put the canon face back on every frame of an animated clip.

Born 2026-10-03 from The Oldest Tree. LTX-2.5 redraws a small child's face as soon as
she moves: s2_wide_walk and s4_walkback failed face_check on six seeds each, the girl
sliding from a 0.35-0.42 match on the locked still to 0.14-0.22 within half a second of
animation. Re-rolling does not converge, and the fallback (a camera push on the still)
throws the motion away. This keeps the motion and fixes the face: every frame, every
detected face is assigned to a cast member of the shot and re-rendered with that cast
member's canon identity (insightface inswapper_128, ArcFace identity).

Faces turned past MAX_YAW are left alone (a swapped profile looks pasted on), and so are
faces under MIN_FACE px. The output is then judged by face_check like any other clip.

Usage (ComfyUI venv, which has insightface + onnxruntime):
  ~/AI/ComfyUI/venv/bin/python pipeline-tools/face_lock.py projects/<film> SHOT_ID IN.mp4 OUT.mp4
"""
import contextlib, json, subprocess, sys, tempfile, warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import face_check as fc  # noqa: E402

MAX_YAW = 60
MIN_FACE = 24
SWAPPER = Path.home() / ".insightface/models/inswapper_128.onnx"


def main():
    proj, sid, src, dst = Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3], sys.argv[4]
    spec = json.loads((proj / "film_shots.json").read_text())
    shot = next(s for s in spec["shots"] if s["id"] == sid)
    people = fc.cast(shot)
    if not people:
        sys.exit(f"{sid}: no canon cast, nothing to lock")

    import insightface
    with contextlib.redirect_stdout(sys.stderr):
        swapper = insightface.model_zoo.get_model(str(SWAPPER), providers=["CPUExecutionProvider"])
    app = fc.app()

    # canon source faces (full insightface Face objects, needed by the swapper)
    canon = {}
    for p in people:
        img = cv2.imread(str(proj / p["image"]))
        fs = app.get(img)
        if fs:
            canon[p["image"]] = max(fs, key=lambda f: f.bbox[3] - f.bbox[1])
    if not canon:
        sys.exit("no face found in any canon portrait")

    fps = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=r_frame_rate", "-of", "csv=p=0", src],
                         capture_output=True, text=True).stdout.strip() or "24"
    tmp = Path(tempfile.mkdtemp(prefix="face_lock_"))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, str(tmp / "f%05d.png")], check=True)
    frames = sorted(tmp.glob("f*.png"))
    swapped = skipped = 0
    for fp in frames:
        img = cv2.imread(str(fp))
        for f in app.get(img):
            h = f.bbox[3] - f.bbox[1]
            yaw = float(f.pose[1]) if getattr(f, "pose", None) is not None else 0.0
            if f.det_score < 0.65 or h < MIN_FACE or abs(yaw) > MAX_YAW:   # 0.5 let a bark shape at the frame edge (score 0.54) get the girl's face in s7_run
                skipped += 1
                continue
            # assign this face to a cast member: identity first, gender as the tiebreak
            # that matters most (a drifted girl can match nobody well, but she is still
            # not the old man)
            best, best_score = None, -9.0
            for path, cf in canon.items():
                score = float(np.dot(f.normed_embedding, cf.normed_embedding))
                if getattr(f, "gender", None) is not None and getattr(cf, "gender", None) is not None \
                        and int(f.gender) != int(cf.gender):
                    score -= 0.5
                if score > best_score:
                    best, best_score = path, score
            img = swapper.get(img, f, canon[best], paste_back=True)
            swapped += 1
        cv2.imwrite(str(fp), img)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", fps, "-i", str(tmp / "f%05d.png"),
                    "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", dst], check=True)
    for fp in frames:
        fp.unlink()
    tmp.rmdir()
    print(f"{sid}: {len(frames)} frames, {swapped} faces locked to canon, {skipped} left alone (profile/tiny) -> {dst}")


if __name__ == "__main__":
    main()
