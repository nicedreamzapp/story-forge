#!/usr/bin/env python3
"""Picture for the teaser: every shot from timeline.json -> 1920x1080 24 fps frames, one grade pass
(film grain, gate weave, vignette, warm -> cold as the Rememberer arrives), piped to ffmpeg -> final/picture.mp4.
Code shots: slow pushes on stills, the 8-photo montage, the scratched-film title and the credit card."""
import json, subprocess, sys, numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
P = Path(__file__).resolve().parent.parent
import os
TL = json.load(open(P / os.environ.get("TWR_TL", "timeline.json"))); PICK = json.load(open(P / "tools/picks.json"))
W, H, FPS = 1920, 1080, 24
rng = np.random.default_rng(3)
def still(name): return Image.open(P / "stills" / f"{name}.png").convert("RGB")
def crop_zoom(im, cx, cy, z):
    w, h = im.size; cw, ch = w / z, h / z
    x0 = min(max(0, cx * w - cw / 2), w - cw); y0 = min(max(0, cy * h - ch / 2), h - ch)
    return np.asarray(im.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch)))
def ease(k): return k * k * (3 - 2 * k)
def clip_frames(path, n, rng_=None):
    r = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries", "stream=nb_read_packets",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True); total = int(r.stdout.strip())
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"scale={W}:{H}:flags=lanczos", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    if rng_: fr = fr[rng_[0]:rng_[1]]
    idx = np.linspace(0, len(fr) - 1, n) if len(fr) < n else np.arange(n)   # slow-mo only when the take is short
    return [fr[int(round(i))] for i in idx]
def blur_man(f, k, b):
    (x0, y0), (x1, y1), rx, ry = b; cx, cy = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
    im = Image.fromarray(f); bl = im.filter(ImageFilter.GaussianBlur(14))
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    return np.asarray(Image.composite(bl, im, m.filter(ImageFilter.GaussianBlur(50))))
TRACK = json.load(open(P / "tools/s11_track.json")) if (P / "tools/s11_track.json").exists() else None
def hide_man(f, src_k):
    """The Rememberer in the reflection: heavy blur, ~1.5 stops darker, cooler and desaturated. Mask = his head ellipse +
    shoulders, cut off before Claire's reflection, from a face track smoothed with a quadratic fit (no shimmer)."""
    j = min(TRACK["n"] - 1, max(0, src_k)); j0 = int(j); a = j - j0; j1 = min(TRACK["n"] - 1, j0 + 1)
    g = lambda key, q: (TRACK[key][q][j0] * (1 - a) + TRACK[key][q][j1] * a)
    x0, y0, x1, y1 = [g("man", q) for q in range(4)]; cx0, cy0, cx1, cy1 = [g("claire", q) for q in range(4)]
    bw, bh = (x1 - x0) * W, (y1 - y0) * H; cx, cy = (x0 + x1) / 2 * W, (y0 + y1) / 2 * H
    right = (cx0 - .45 * (cx1 - cx0)) * W - 8
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    d.ellipse((cx - .95 * bw, cy - .9 * bh, min(right, cx + .95 * bw), cy + .9 * bh), fill=255)
    d.polygon([(cx - .55 * bw, y1 * H + .1 * bh), (min(right, cx + .55 * bw), y1 * H + .1 * bh), (min(right, cx + 1.7 * bw), H), (cx - 1.8 * bw, H)], fill=255)
    m = np.asarray(m.filter(ImageFilter.GaussianBlur(30))).astype(np.float32)[..., None] / 255
    im = Image.fromarray(f); bl = np.asarray(im.filter(ImageFilter.GaussianBlur(26))).astype(np.float32)
    gr = bl.mean(2, keepdims=True); bl = bl * .5 + gr * .5; bl *= .35; bl[..., 0] *= .9; bl[..., 2] *= 1.08
    return (f.astype(np.float32) * (1 - m) + bl * m).clip(0, 255).astype(np.uint8)
FONT = "/System/Library/Fonts/Supplemental/Baskerville.ttc"
def eaten_text(txt, size, spacing=14):
    f = ImageFont.truetype(FONT, size)
    w = int(sum(f.getlength(c) + spacing for c in txt)) + 40; im = Image.new("L", (w, int(size * 1.5)), 0); d = ImageDraw.Draw(im); x = 20
    for c in txt: d.text((x, 10), c, fill=255, font=f); x += f.getlength(c) + spacing
    a = np.asarray(im).astype(float) / 255
    nz = np.asarray(Image.fromarray((rng.random(a.shape) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6))).astype(float) / 255
    return np.clip(a * (nz > .36) * 1.0 + a * .25, 0, 1)        # edges eaten, like burned film
def place(canvas, mask, cx, cy, col=(225, 215, 195), dx=0, dy=0):
    h, w = mask.shape; x0 = int(cx - w / 2 + dx); y0 = int(cy - h / 2 + dy)
    sub = canvas[y0:y0 + h, x0:x0 + w]; m = mask[: sub.shape[0], : sub.shape[1], None]
    canvas[y0:y0 + h, x0:x0 + w] = sub * (1 - m) + np.array(col) * m
def scratches(canvas, k):
    for _ in range(rng.integers(0, 3)):
        x = int(rng.uniform(0, W)); canvas[:, x:x + rng.integers(1, 3)] = np.clip(canvas[:, x:x + 2] + rng.uniform(40, 120), 0, 255)[:, :1] if False else 200
    for _ in range(rng.integers(0, 6)):
        x, y, r = int(rng.uniform(0, W)), int(rng.uniform(0, H)), int(rng.uniform(1, 4)); canvas[max(0, y-r):y+r, max(0, x-r):x+r] = rng.choice([10, 230])
    return canvas
T_W = eaten_text("THE THINGS WE REMEMBER", 88, 10); T_H = eaten_text("THE THINGS HE REMEMBERS", 88, 10)
C_SOON = eaten_text("COMING SOON", 46, 10)
C1 = eaten_text("NICE DREAMZ PICTURES", 72, 12); C2 = eaten_text("A STORY FORGE PRODUCTION", 40, 9)
DAN = eaten_text("and DANIEL as himself", 54, 8)
def frames_for(shot):
    n = int(round((shot["e"] - shot["s"]) * FPS)); kind, _, name = shot["src"].partition(":")
    if kind in ("clip", "lips"):
        src = P / ("lips" if kind == "lips" else "clips") / f"{name}.mp4"
        if "/" in name: src = P / name
        if not src.exists(): src = P / "clips" / f"{name}.mp4"
        fr = clip_frames(src, n, shot.get('src_range'))
        if shot.get('hide_man') and TRACK:
            L = TRACK['n']; fr = [hide_man(f, i * (L - 1) / max(1, n - 1)) for i, f in enumerate(fr)]
        elif shot.get('blur_man'): fr = [blur_man(f, i / max(1, n - 1), shot['blur_man']) for i, f in enumerate(fr)]
        return fr
    if kind == "push":
        im = still(PICK[name]); a = PICK.get(name + "_push", [.5, .5, 1.0, .5, .5, 1.12])
        return [crop_zoom(im, a[0] + (a[3] - a[0]) * ease(i / n), a[1] + (a[4] - a[1]) * ease(i / n), a[2] + (a[5] - a[2]) * ease(i / n)) for i in range(n)]
    if kind == "photos":
        ims = [still(f"s09_{k}") for k in range(1, 9)]; per = n / 8; out = []
        for i in range(n):
            k = min(7, int(i / per)); j = (i - k * per) / per
            f = crop_zoom(ims[k], .5, .5, 1.04 + .10 * j).astype(float)
            if j < .12: f = f * .4 + 255 * .6 * (1 - j / .12) * 0 + f * .6 * (j / .12)
            out.append(f.astype(np.uint8))
        return out
    if kind == "black": return [np.zeros((H, W, 3), np.uint8)] * n
    out = []
    for i in range(n):
        c = np.zeros((H, W, 3), float); fl = rng.uniform(.75, 1.0); jx, jy = rng.normal(0, 1.5, 2)
        if kind == "title":
            t = i / FPS; m = T_H if 2.0 <= t < 2.5 else T_W
            if rng.random() < .04: m = m * (rng.random(m.shape) > .5)
            place(c, m * fl, W / 2, H / 2 - 40, dx=jx, dy=jy)
            if t >= 1.0: place(c, C_SOON * fl * min(1, (t - 1.0) / .4), W / 2, H / 2 + 120, dx=jx, dy=jy)
            c *= min(1, t / .5)
        else:
            t = i / FPS
            if 1.6 <= t < 1.6 + 6 / FPS: place(c, DAN * fl, W / 2, H / 2 + 110, col=(205, 40, 30), dx=jx, dy=jy)
            place(c, C1 * fl, W / 2, H / 2 - 40, dx=jx, dy=jy); place(c, C2 * fl, W / 2, H / 2 + 50, dx=jx, dy=jy)
            c *= min(1, t / .15) * min(1, (n / FPS - t) / .3)
        out.append(scratches(c, i).clip(0, 255).astype(np.uint8))
    return out
yy, xx = np.mgrid[0:H, 0:W]; VIG = 1 - .55 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) ** 1.3 * .6
def grade(f, t, kind):
    f = f.astype(np.float32)
    cold = 0 if t < 14.5 else min(1, (t - 14.5) / 6)
    if kind not in ("title", "credits", "black", "photos"):
        g = f.mean(2, keepdims=True); f = f * (1 - .35 * cold) + g * .35 * cold
        f[..., 0] *= 1.04 - .10 * cold; f[..., 2] *= .96 + .12 * cold; f *= 1 - .18 * cold
        f *= VIG[..., None]
    f += rng.normal(0, 7, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1)
    return np.clip(f, 0, 255).astype(np.uint8)
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", str(P / os.environ.get("TWR_PIC", "final/picture.mp4"))], stdin=subprocess.PIPE)
for shot in TL["shots"]:
    kind = shot["src"].split(":")[0]; fr = frames_for(shot)
    for i, f in enumerate(fr):
        ff.stdin.write(grade(f, shot["s"] + i / FPS, kind).tobytes())
    print("shot", shot["id"], len(fr), flush=True)
ff.stdin.close(); ff.wait(); print("PICTURE_DONE")
