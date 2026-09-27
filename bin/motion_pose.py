#!/usr/bin/env python3
"""
motion_pose.py — turn a real video of a person moving into a Wan-Animate pose track.

Stage 1 of the MOTION TRANSFER pipeline (see CLAUDE.md "Motion transfer").
Traces the largest person per frame with DWPose (rtmlib/ONNX, CPU, no CUDA) and
draws an OpenPose skeleton on black, square-cropped and centered on the action.

    ./venv/bin/python bin/motion_pose.py SOURCE.mp4 OUT_pose.mp4 \
        --start 3.3 --dur 8.1 --frames 81

Frame count MUST be 4k+1 (81 = 5s @16fps, 49 = 3s). The script resamples the
source window to exactly that many frames, so a 60fps source plays at natural
speed — do NOT feed slow-motion footage at its recorded rate, the character
hangs inverted and reads as "half a cartwheel" (Matt, 2026-07-25).

Writes OUT_pose.mp4 plus OUT_pose_qc.png (source | skeleton pairs). ALWAYS eyeball
the QC sheet before spending render minutes: confirm the move's full arc is in the
window (wind-up → apex → landing → recovery), not a truncated slice.

Needs a venv with: rtmlib onnxruntime opencv-python-headless numpy
"""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
from rtmlib import Wholebody, draw_skeleton


def main():
    ap = argparse.ArgumentParser(description="Extract a Wan-Animate pose track from real footage.")
    ap.add_argument("source", help="source video of a real person performing the move")
    ap.add_argument("out", help="output pose .mp4")
    ap.add_argument("--start", type=float, default=0.0, help="window start (seconds)")
    ap.add_argument("--dur", type=float, default=0.0, help="window length (seconds, 0 = to end)")
    ap.add_argument("--frames", type=int, default=81, help="output frames, must be 4k+1 (default 81 = 5s)")
    ap.add_argument("--canvas", type=int, default=768, help="square canvas size")
    ap.add_argument("--fps", type=int, default=16, help="output fps (Wan native = 16)")
    ap.add_argument("--zoom", type=float, default=0.0, metavar="PAD",
                    help="tighten the square crop to the action bounding box times PAD "
                         "(e.g. 1.4). Default 0 = full-height crop. Use when the "
                         "performer is small/far in frame, so the character fills the "
                         "shot instead of being a speck.")
    args = ap.parse_args()

    if (args.frames - 1) % 4:
        sys.exit(f"--frames must be 4k+1 (got {args.frames}); try {(args.frames // 4) * 4 + 1}")

    src = Path(args.source).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    if not src.is_file():
        sys.exit(f"source not found: {src}")

    with tempfile.TemporaryDirectory() as td:
        clip = src
        if args.start or args.dur:
            clip = Path(td) / "window.mp4"
            cmd = ["ffmpeg", "-y", "-v", "error", "-ss", str(args.start)]
            if args.dur:
                cmd += ["-t", str(args.dur)]
            cmd += ["-i", str(src), "-an", "-c:v", "libx264", "-crf", "18", str(clip)]
            subprocess.run(cmd, check=True)

        cap = cv2.VideoCapture(str(clip))
        frames = []
        while True:
            ok, f = cap.read()
            if not ok:
                break
            frames.append(f)
        cap.release()
        if not frames:
            sys.exit("no frames decoded from the window")
        print(f"[motion_pose] window: {len(frames)} frames → resampling to {args.frames}")

        wb = Wholebody(to_openpose=True, backend="onnxruntime", device="cpu", mode="balanced")
        idx = np.linspace(0, len(frames) - 1, args.frames).astype(int)

        dets = [wb(frames[i]) for i in idx]
        print("[motion_pose] pose detection done")

        # largest detected person per frame = the performer
        picked, all_pts = [], []
        for kpts, scores in dets:
            best, best_area = None, -1.0
            for p in range(kpts.shape[0]):
                pts = kpts[p][scores[p] > 0.3]
                if len(pts) < 6:
                    continue
                (x0, y0), (x1, y1) = pts.min(0), pts.max(0)
                area = (x1 - x0) * (y1 - y0)
                if area > best_area:
                    best_area, best = area, p
            picked.append(best)
            if best is not None:
                all_pts.append(kpts[best][scores[best] > 0.3])

        if not all_pts:
            sys.exit("no person detected anywhere in the window")

        H, W = frames[0].shape[:2]
        allp = np.vstack(all_pts)
        bx0, by0 = allp.min(0)
        bx1, by1 = allp.max(0)
        cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2

        if args.zoom:
            side = int(min(H, W, max(bx1 - bx0, by1 - by0) * args.zoom))
        else:
            side = H
        left = int(np.clip(cx - side / 2, 0, max(0, W - side)))
        top = int(np.clip(cy - side / 2, 0, max(0, H - side))) if args.zoom else 0
        scale = args.canvas / side
        print(f"[motion_pose] square crop x[{left},{left+side}] y[{top},{top+side}] "
              f"→ {args.canvas}px")

        out.parent.mkdir(parents=True, exist_ok=True)
        vw = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*"mp4v"),
                             args.fps, (args.canvas, args.canvas))
        qc = []
        for n, (i, (kpts, scores), best) in enumerate(zip(idx, dets, picked)):
            canvas = np.zeros((args.canvas, args.canvas, 3), dtype=np.uint8)
            if best is not None:
                k = kpts[best:best + 1].copy()
                k[..., 0] = (k[..., 0] - left) * scale
                k[..., 1] = (k[..., 1] - top) * scale
                canvas = draw_skeleton(canvas, k, scores[best:best + 1],
                                       openpose_skeleton=True, kpt_thr=0.3, line_width=4)
            vw.write(canvas)
            if n % max(1, args.frames // 8) == 0:
                crop = cv2.resize(frames[i][top:top + side, left:left + side], (256, 256))
                qc.append(np.hstack([crop, cv2.resize(canvas, (256, 256))]))
        vw.release()

        qc_path = out.with_name(out.stem + "_qc.png")
        cv2.imwrite(str(qc_path), np.vstack(qc))
        print(f"[motion_pose] wrote {out}")
        print(f"[motion_pose] QC sheet {qc_path} — CHECK the full arc is present before rendering")


if __name__ == "__main__":
    main()
