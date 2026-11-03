#!/usr/bin/env python3
"""stabilize — two-pass vid.stab stabilization for REAL camera footage (phone, handheld).

Never for AI shots: a generated shot's camera move is the motion the model was asked for,
and "stabilizing" it crops the frame and fights the move. So this refuses anything that
looks generated (a path under clips/, renders/ or acquired AI takes whose sidecar names a
generator) unless --force, and acts only on footage flagged real: --real on the command
line, or a <file>.json sidecar with "kind": "real" | "handheld" | "phone" or "handheld": true.

Pass 1 vidstabdetect writes the camera path, pass 2 vidstabtransform smooths it, then a
light unsharp gives back the softness the resample costs. The ffmpeg used is our own build
with libvidstab (~/.local/ffmpeg-vidstab/bin/ffmpeg, built from source 2026-11-02; the
Homebrew ffmpeg on PATH has no vidstab and is left untouched). Override: $FFMPEG_VIDSTAB.

    ~/.local/finish-env/bin/python pipeline-tools/stabilize.py IN.mov [OUT.mp4] --real
        [--smooth-seconds 0.5] [--zoom 0] [--optzoom 1] [--shakiness 6] [--tripod]
    --project projects/<film>    stabilize every flagged-real take in acquired/ or footage/
                                 into <that dir>/stabilized/<name>_stab.mp4 (+ sidecar copy)

Prints camera jitter before and after (phase-correlation of consecutive frames, px of
residual shake per frame after removing the intended move: the path smoothed over 1 s).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

FF = os.environ.get("FFMPEG_VIDSTAB", str(Path.home() / ".local/ffmpeg-vidstab/bin/ffmpeg"))
REAL_KINDS = {"real", "handheld", "phone", "camera"}
AI_HINTS = ("grok", "sora", "veo", "kling", "runway", "pika", "wan", "ltx", "k6", "kandinsky",
            "flux", "chatgpt", "still-kb", "zoompan", "blender", "comfy", "seedvr")
VID_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".webm"}


def probe(path: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(path)],
                       capture_output=True, text=True)
    d = json.loads(r.stdout or "{}")
    s = (d.get("streams") or [{}])[0]
    n, _, den = s.get("r_frame_rate", "30/1").partition("/")
    return {"w": s.get("width", 0), "h": s.get("height", 0), "fps": float(n) / float(den or 1),
            "dur": float(d.get("format", {}).get("duration", 0) or 0)}


def classify(path: Path) -> tuple[str, str]:
    """('real'|'ai'|'unknown', why)"""
    side = path.with_name(path.name + ".json")
    if side.is_file():
        try:
            d = json.loads(side.read_text())
        except ValueError:
            d = {}
        kind = str(d.get("kind", "")).lower()
        if kind in REAL_KINDS or d.get("handheld") is True:
            return "real", f"sidecar kind={kind or 'handheld'}"
        blob = " ".join(str(d.get(k, "")) for k in ("tool", "backend", "kind", "origin")).lower()
        hit = next((h for h in AI_HINTS if h in blob), None)
        if hit:
            return "ai", f"sidecar names a generator ({hit})"
    parts = {p.lower() for p in path.parts}
    if parts & {"clips", "renders", "takes", "previs", "segs", "alternates"}:
        return "ai", "path is a render folder"
    return "unknown", "no flag"


# ---------------------------------------------------------------- shake metric
def gray_frames(path: Path, fps: float, w: int = 320, max_s: float = 60.0) -> np.ndarray:
    cmd = ["ffmpeg", "-v", "error", "-t", f"{max_s}", "-i", str(path), "-vf",
           f"scale={w}:-2:flags=area,format=gray", "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    info = probe(path)
    h = int(round(info["h"] * w / info["w"] / 2) * 2) if info["w"] else 0
    n = len(raw) // (w * h)
    return np.frombuffer(raw[: n * w * h], np.uint8).reshape(n, h, w).astype(np.float32)


def phase_shift(a: np.ndarray, b: np.ndarray, win: np.ndarray) -> tuple[float, float]:
    A = np.fft.fft2(a * win); B = np.fft.fft2(b * win)
    R = A * np.conj(B); R /= np.abs(R) + 1e-9
    c = np.fft.ifft2(R).real
    y, x = np.unravel_index(np.argmax(c), c.shape)
    h, w = c.shape

    def sub(m1, m0, p1):                                     # parabolic sub-pixel peak
        den = m1 - 2 * m0 + p1
        return 0.0 if abs(den) < 1e-12 else 0.5 * (m1 - p1) / den
    fx = x + sub(c[y, (x - 1) % w], c[y, x], c[y, (x + 1) % w])
    fy = y + sub(c[(y - 1) % h, x], c[y, x], c[(y + 1) % h, x])
    if fy > h / 2: fy -= h
    if fx > w / 2: fx -= w
    return float(fx), float(fy)


def jitter(path: Path) -> dict:
    """Residual shake: frame-to-frame translation, minus the path smoothed over ~1 s.
    Measured on the centre 60% so a stabilizer's border fill does not count as motion."""
    info = probe(path)
    fr = gray_frames(path, info["fps"])
    if len(fr) < 3:
        return {"jitter_px": None}
    h, w = fr.shape[1:]
    fr = fr[:, int(h * .2):int(h * .8), int(w * .2):int(w * .8)]
    win = np.outer(np.hanning(fr.shape[1]), np.hanning(fr.shape[2])).astype(np.float32)
    d = np.array([phase_shift(fr[i], fr[i + 1], win) for i in range(len(fr) - 1)])
    path_xy = np.cumsum(d, 0)
    k = max(3, int(round(info["fps"])) | 1)
    pad = np.pad(path_xy, ((k // 2, k // 2), (0, 0)), mode="edge")
    smooth = np.stack([np.convolve(pad[:, i], np.ones(k) / k, mode="valid") for i in range(2)], 1)
    resid = path_xy - smooth
    scale = info["w"] / 320.0                                # report in source pixels
    return {"jitter_px": round(float(np.sqrt((resid ** 2).sum(1)).mean() * scale), 2),
            "step_px": round(float(np.sqrt((np.diff(resid, axis=0) ** 2).sum(1)).mean() * scale), 2),
            "frames": int(len(fr))}


# ---------------------------------------------------------------- stabilize
def stabilize(src: Path, out: Path, a) -> None:
    info = probe(src)
    smoothing = 0 if a.tripod else max(1, int(round(a.smooth_seconds * info["fps"])))
    with tempfile.TemporaryDirectory() as d:
        trf = Path(d) / "motion.trf"
        det = f"vidstabdetect=shakiness={a.shakiness}:accuracy=15:stepsize=6:result='{trf}'"
        if a.tripod:
            det += ":tripod=1"
        r = subprocess.run([FF, "-v", "error", "-y", "-i", str(src), "-vf", det, "-f", "null", "-"],
                           capture_output=True, text=True)
        if r.returncode or not trf.is_file():
            sys.exit(f"vidstabdetect failed: {r.stderr[-600:]}")
        tf = (f"vidstabtransform=input='{trf}':smoothing={smoothing}:zoom={a.zoom}:optzoom={a.optzoom}"
              f":interpol=bicubic" + (":tripod=1" if a.tripod else "") + ",unsharp=5:5:0.6:3:3:0.3")
        r = subprocess.run([FF, "-v", "error", "-y", "-i", str(src), "-vf", tf, "-map", "0:v:0", "-map", "0:a:0?",
                            "-c:v", "libx264", "-crf", str(a.crf), "-preset", "medium", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)],
                           capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"vidstabtransform failed: {r.stderr[-600:]}")
    print(f"[stabilize] {src.name}: smoothing {smoothing} frames ({'tripod' if a.tripod else f'{a.smooth_seconds}s'}),"
          f" zoom {a.zoom}%, optzoom {a.optzoom} -> {out}")


def one(src: Path, out: Path, a) -> dict:
    kind, why = classify(src)
    if kind == "ai" and not a.force:
        print(f"[stabilize] skip {src.name}: looks generated ({why}); --force to override")
        return {"file": str(src), "skipped": why}
    if kind != "real" and not (a.real or a.force):
        print(f"[stabilize] skip {src.name}: not flagged real ({why}); pass --real or add a sidecar "
              f'{{"kind": "handheld"}}')
        return {"file": str(src), "skipped": why}
    before = jitter(src) if not a.no_measure else {}
    stabilize(src, out, a)
    after = jitter(out) if not a.no_measure else {}
    if before:
        print(f"  jitter {before['jitter_px']} px -> {after['jitter_px']} px · "
              f"step {before['step_px']} -> {after['step_px']} px/frame")
    return {"file": str(src), "out": str(out), "before": before, "after": after}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", nargs="?")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--project")
    ap.add_argument("--real", action="store_true", help="the caller vouches this is real camera footage")
    ap.add_argument("--force", action="store_true", help="stabilize even a shot that looks generated")
    ap.add_argument("--smooth-seconds", type=float, default=0.5, help="camera path smoothing window")
    ap.add_argument("--zoom", type=float, default=0.0, help="extra zoom %% (negative = zoom out)")
    ap.add_argument("--optzoom", type=int, default=1, choices=[0, 1, 2],
                    help="0 none (black borders), 1 one static zoom for no borders, 2 adaptive")
    ap.add_argument("--shakiness", type=int, default=6, choices=range(1, 11))
    ap.add_argument("--tripod", action="store_true", help="lock to the first frame (virtual tripod)")
    ap.add_argument("--crf", type=int, default=14)
    ap.add_argument("--no-measure", action="store_true")
    ap.add_argument("--report")
    a = ap.parse_args()
    if not Path(FF).exists():
        sys.exit(f"no vidstab ffmpeg at {FF} (see docstring; set $FFMPEG_VIDSTAB)")
    rows = []
    if a.project:
        cands = [p for d in ("acquired", "footage") if (Path(a.project) / d).is_dir()
                 for p in sorted((Path(a.project) / d).iterdir())]
        for p in cands:
            if p.suffix.lower() in VID_EXT and classify(p)[0] == "real":
                dest = p.parent / "stabilized"
                dest.mkdir(exist_ok=True)
                o = dest / f"{p.stem}_stab.mp4"
                rows.append(one(p, o, a))
                side = p.with_name(p.name + ".json")
                if side.is_file() and o.is_file():
                    d = json.loads(side.read_text()); d.update(stabilized_from=str(p.name), file=str(o.relative_to(a.project)))
                    o.with_name(o.name + ".json").write_text(json.dumps(d, indent=1))
        if not rows:
            print("[stabilize] no take in acquired/ or footage/ is flagged real/handheld; nothing to do")
    else:
        if not a.src:
            ap.error("give IN or --project")
        src = Path(a.src).expanduser().resolve()
        out = Path(a.out).expanduser().resolve() if a.out else src.with_name(src.stem + "_stab.mp4")
        if out == src:
            sys.exit("refusing to overwrite the input")
        rows.append(one(src, out, a))
    if a.report:
        Path(a.report).write_text(json.dumps(rows, indent=1))
    return 0 if all("skipped" not in r for r in rows) or a.project else 3


if __name__ == "__main__":
    raise SystemExit(main())
