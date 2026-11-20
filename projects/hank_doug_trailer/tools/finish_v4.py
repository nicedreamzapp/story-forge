#!/usr/bin/env python3
"""finish_v4.py — script_v4 cut: straight cuts from tools/timeline_v4.json (start, dur, clip, in-point per row).
Row 7 = the lantern cutout flown on a parabola over the ditch plate + 4-frame painted splash (1.4 s), then the lit-lantern clip with
the light-out grade ramp (script v4 row 7, as written). Row 16 = title painted in by brush strokes (title_in/title_dur). Row 17 =
chipmunk cutout pops onto the wheel rim at chipmunk_pop, black from black_at. No rings, no held frames. Run detached (nohup).
  finish_v4.py --out final/picture_v4.mp4
"""
from __future__ import annotations
import argparse, json, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
import paintlib as pl
from paintlib import PW, PH, OW, OH, FPS, ease, lerp

P = Path(__file__).resolve().parent.parent
TL = json.load(open(P / "tools/timeline_v4.json"))
ROWS = TL["rows"]
FR = {}; A = {}


def clip_len(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip() or 0)


def load():
    for r in ROWS:
        c = r["clip"].split("code:lantern+")[-1]
        f = P / c
        if not f.exists():
            sys.exit(f"MISSING {c} for {r['id']}")
        FR[r["id"]] = pl.load_clip(f)
        need = r["in"] + r["dur"] - (1.4 if r["clip"].startswith("code:") else 0)
        if clip_len(f) + 0.05 < need:
            print(f"  WARNING {r['id']}: clip {clip_len(f):.2f}s shorter than in+dur {need:.2f}s; last frame would hold", flush=True)
    A["H1"] = pl.load_plate(P / "stills/H1_ditch.png")
    A["lantern"] = pl.cutout(pl.load_plate(P / "stills/H2_lantern.png"))
    A["chipmunk"] = pl.cutout(pl.load_plate(P / "stills/X_chipmunk.png"))
    pl.title_layer()


def land():
    return (560 * PW / 1344.0, (560 - 6) * PH / 756.0)


def row_frame(r, tl):
    rid = r["id"]
    if r["clip"].startswith("code:lantern+"):
        if tl < 1.4:   # the lantern tumbles in and lands (splash at 1.2 s of the row)
            fr = A["H1"].copy(); sp, al = A["lantern"]; lx, ly = land()
            if tl < 1.2:
                u = tl / 1.2
                x = lerp(PW + 200, lx, u); y = ly - 1100 * (1 - u) ** 2; ang = -40 + 420 * u
                fr = pl.paste(fr, sp, al, x, y, 0.42, ang)
            else:
                k = int((tl - 1.2) * FPS)
                fr = pl.paste(fr, sp, al, lx, ly + 20, 0.42, 95)
                fr = pl.splash(fr, lx, ly, k)
            return fr
        # then the lit lantern in the ditch, flame flickering; the light goes out over the last 0.6 s of the row
        frs = FR[rid]; k = max(0, min(len(frs) - 1, int(round((r["in"] + tl - 1.4) * 24))))
        fr = frs[k].astype(np.float32) / 255.0
        u = ease((tl - (r["dur"] - 0.6)) / 0.6)
        if u > 0:
            fr = np.clip(fr * (1 - 0.4 * u) * np.array([1 - 0.14 * u, 1 - 0.06 * u, 1 + 0.04 * u], np.float32), 0, 1).astype(np.float32)
        return fr
    frs = FR[rid]; k = max(0, min(len(frs) - 1, int(round((r["in"] + tl) * 24))))
    fr = frs[k].astype(np.float32) / 255.0
    if "title_in" in r:
        u = (tl - r["title_in"]) / r["title_dur"]
        if u > 0: fr = pl.title_reveal(fr, min(1.0, u))
    if "chipmunk_pop" in r and tl >= r["chipmunk_pop"] and A["chipmunk"] is not None:
        sp, al = A["chipmunk"]; pop = ease((tl - r["chipmunk_pop"]) / 0.3)
        cx, cy = 690 * PW / 1344.0 + 40, (470 - 6) * PH / 756.0 + 20
        fr = pl.paste(fr, sp, al, cx, cy + 90 * (1 - pop), 0.24 * (0.6 + 0.4 * pop), 0)
    if "black_at" in r and tl >= r["black_at"]:
        return np.zeros((PH, PW, 3), np.float32)
    return fr


def render(t):
    for i, r in enumerate(ROWS):
        if r["start"] <= t < r["start"] + r["dur"] or (i == len(ROWS) - 1 and t >= r["start"]):
            return pl.view(row_frame(r, t - r["start"]), PW / 2, PH / 2, 1.0)
    return np.zeros((OH, OW, 3), np.float32)


def frame_u8(i): return (np.clip(render(i / FPS), 0, 1) * 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(P / "final/picture_v4.mp4")); ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args(); load()
    total = ROWS[-1]["start"] + ROWS[-1]["dur"]; n = int(round(total * FPS)); print(f"cut: {len(ROWS)} rows, {total:.2f} s", flush=True)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", a.out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE); t0 = time.time(); cv2.setNumThreads(2)
    with ThreadPoolExecutor(a.workers) as pool:
        for fr in pool.map(frame_u8, range(n)): ff.stdin.write(fr.tobytes())
    ff.stdin.close(); ff.wait(); print(f"picture -> {a.out} ({total:.2f} s) in {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
