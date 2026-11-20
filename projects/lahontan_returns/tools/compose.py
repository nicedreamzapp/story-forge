#!/usr/bin/env python3
"""Picture: every shot from timeline.json at 1080x1920/25 fps, float-coordinate (BICUBIC affine) moves only, graphics on top.
Writes final/picture.mp4 (silent). Renders in parallel segments then concats."""
import json, subprocess, sys, math
from functools import lru_cache
from multiprocessing import Pool
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gfx

P = Path(__file__).resolve().parent.parent
TL = json.load(open(P / "timeline.json"))
W, H, FPS = 1080, 1920, 25
END = TL["end"]; NF = int(round(END * FPS))
G = TL["gfx"]


@lru_cache(maxsize=4)
def frames(path):
    pr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate",
                         "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip().split(",")
    w, h = int(pr[0]), int(pr[1]); a, b = pr[2].split("/"); fps = int(a) / int(b)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3), fps


@lru_cache(maxsize=8)
def still(name):
    return Image.open(P / "stills" / f"{name}.png").convert("RGB")


def view(im, z=1.0, cx=0.5, cy=0.5):
    """crop a 9:16 window of size 1/z centred at (cx, cy) (fractions), sampled at float coords -> W x H"""
    sw, sh = im.size
    s = max(W / sw, H / sh) * z            # output px per source px
    vw, vh = W / s, H / s
    x0 = min(max(cx * sw - vw / 2, 0), sw - vw); y0 = min(max(cy * sh - vh / 2, 0), sh - vh)
    return im.transform((W, H), Image.AFFINE, (1 / s, 0, x0, 0, 1 / s, y0), resample=Image.BICUBIC)


def ease(u): u = min(max(u, 0), 1); return 3 * u * u - 2 * u ** 3


def base(t, sh):
    u = (t - sh["s"]) / max(1e-3, sh["e"] - sh["s"]); src = sh["src"]; mode = sh.get("mode", "")
    z = sh.get("z", 1.0); cy = sh.get("cy", 0.5)
    if src == "map": return gfx.nv_map(t - sh["s"], sh["e"] - sh["s"])
    if src == "evac": return gfx.evac(t - sh["s"])
    if src.startswith("lips:"):
        b = src[5:]; lf = P / "lips" / f"{b}.mp4"
        if not lf.exists(): lf = P / "clips" / f"{TL['blocks'][b]['clip']}.mp4"   # draft only: un-synced source
        fr, fps = frames(lf)
        k = int((t - TL["blocks"][b]["s"]) * fps) % len(fr) if "clips" in str(lf) else min(len(fr) - 1, int((t - TL["blocks"][b]["s"]) * fps))
        zz = z * (1 + 0.025 * ease(u))                     # slow broadcast push on the talking shots
        return view(Image.fromarray(fr[k]), zz, 0.5, cy)
    if src.startswith("clip:"):
        fr, fps = frames(P / "clips" / f"{src[5:]}.mp4")
        n = len(fr); dur = sh["e"] - sh["s"]; off = sh.get("off", 0.0)
        avail = n / fps - off
        rate = min(1.0, avail / dur) if avail < dur else 1.0
        k = int(((t - sh["s"]) * rate + off) * fps)
        if k >= n:  # ping-pong past the end
            k = (n - 1) - (k - n) % (n - 1)
        im = Image.fromarray(fr[min(k, n - 1)])
        if mode == "splash": return view(im, 1.0 + 0.08 * ease(u), 0.5, 0.62)
        if mode == "push": return view(im, 1.0 + 0.10 * ease(u))
        if mode == "pushslow": return view(im, 1.0 + 0.05 * ease(u))
        return view(im, 1.0 + 0.03 * ease(u))
    if src.startswith("still:"):
        im = still(src[6:])
        if mode == "pullback": return view(im, 1.18 - 0.16 * ease(u))
        return view(im, 1.02 + 0.14 * ease(u), 0.5, 0.55)
    raise ValueError(src)


def shot_at(t):
    for sh in TL["shots"]:
        if sh["s"] <= t < sh["e"]: return sh
    return TL["shots"][-1]


def frame(i):
    t = i / FPS; sh = shot_at(t)
    img = base(t, sh).convert("RGBA"); d = ImageDraw.Draw(img, "RGBA")
    if t < G["cold"]:
        gfx.slam(img, d, t, 0.15)
    else:
        for lt in G["lower"]:
            if lt["t"] <= t < lt["e"]: gfx.lower(d, t, lt["t"], lt["top"], lt["sub"], lt["red"])
        for a, b, place in G["live"]:
            if a <= t < b: gfx.live(d, t, place)
        if sh["src"] not in ("evac",): gfx.ticker(img, d, t - G["cold"])
        gfx.end_banner(img, d, t, G["end"])
    gfx.bug(d, t); gfx.parody(d)
    return img.convert("RGB").tobytes()


def seg(args):
    k, a, b = args
    out = P / "final" / f"seg{k:02d}.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    for i in range(a, b): p.stdin.write(frame(i))
    p.stdin.close(); p.wait(); return str(out)


if __name__ == "__main__":
    (P / "final").mkdir(exist_ok=True)
    if len(sys.argv) > 1 and sys.argv[1] == "--still":   # preview single frames: --still t1 t2 ...
        for t in sys.argv[2:]:
            Image.frombytes("RGB", (W, H), frame(int(float(t) * FPS))).save(f"/tmp/lr_f{t}.jpg", quality=85)
        sys.exit()
    # segment boundaries on shot cuts so each worker loads few sources
    cuts = sorted({int(round(s["s"] * FPS)) for s in TL["shots"]} | {NF})
    jobs, cur = [], 0
    step = NF // 8
    for c in cuts[1:]:
        if c - cur >= step or c == NF: jobs.append((len(jobs), cur, c)); cur = c
    with Pool(8) as pool: outs = pool.map(seg, jobs)
    (P / "final/segs.txt").write_text("".join(f"file '{o}'\n" for o in outs))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(P / "final/segs.txt"), "-c", "copy", str(P / "final/picture.mp4")], check=True)
    for o in outs: Path(o).unlink()
    print("PICTURE_DONE", NF, "frames")
