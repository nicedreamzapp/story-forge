#!/usr/bin/env python3
"""paintlib — the code-rendered layers of the one-canvas trailer (script_v2.md "How the one-shot is built").
Pure functions of time over existing frames: unpainted state, ripple + reveal, whip-pan joins, old paint,
leading edge, lantern cutout, title strokes. No model. Frozen rule 12: every camera move is float-coord
affine sampling (cv2.warpAffine, bilinear), never whole-pixel zoompan.
Plate space: every still is scaled to PW x PH (overscan of the 1920x1080 output) so pushes and whips stay inside.
"""
from __future__ import annotations
import sys, math
from pathlib import Path
import numpy as np, cv2

SF = Path.home() / "Desktop/PROJECTS/story-forge"
sys.path.insert(0, str(SF / "pipeline-tools"))
from motion_tokens import camera_ease  # quintic smootherstep

OW, OH = 1920, 1080
PW, PH = 2304, 1296          # plate (1.2x overscan)
FPS = 24
rng = np.random.default_rng(7)


def ease(u): return camera_ease(min(1.0, max(0.0, u)))


def lerp(a, b, u): return a + (b - a) * u


# ----------------------------------------------------------------------------- loading
def load_plate(path: str | Path) -> np.ndarray:
    """Still -> float32 RGB plate PWxPH (center crop to 16:9 then resize, LANCZOS)."""
    im = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if im is None:
        raise FileNotFoundError(path)
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    h, w = im.shape[:2]
    th = int(round(w * 9 / 16))
    if th <= h:
        y0 = (h - th) // 2; im = im[y0:y0 + th]
    else:
        tw = int(round(h * 16 / 9)); x0 = (w - tw) // 2; im = im[:, x0:x0 + tw]
    im = cv2.resize(im, (PW, PH), interpolation=cv2.INTER_LANCZOS4)
    return im.astype(np.float32) / 255.0


def frame_to_plate(fr_rgb_u8: np.ndarray) -> np.ndarray:
    im = fr_rgb_u8
    h, w = im.shape[:2]
    th = int(round(w * 9 / 16))
    if th <= h:
        y0 = (h - th) // 2; im = im[y0:y0 + th]
    im = cv2.resize(im, (PW, PH), interpolation=cv2.INTER_CUBIC)
    return im.astype(np.float32) / 255.0


def load_clip(path: str | Path) -> list[np.ndarray]:
    """mp4 -> list of RGB uint8 frames (plate-sized), loaded once."""
    cap = cv2.VideoCapture(str(path)); out = []
    while True:
        ok, fr = cap.read()
        if not ok: break
        fr = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
        h, w = fr.shape[:2]; th = int(round(w * 9 / 16))
        if th <= h: y0 = (h - th) // 2; fr = fr[y0:y0 + th]
        out.append(cv2.resize(fr, (PW, PH), interpolation=cv2.INTER_CUBIC))
    cap.release()
    return out


# ----------------------------------------------------------------------------- textures (made once)
def _noise(shape, scale, seed):
    r = np.random.default_rng(seed)
    small = r.random((max(2, shape[0] // scale), max(2, shape[1] // scale))).astype(np.float32)
    return cv2.resize(small, (shape[1], shape[0]), interpolation=cv2.INTER_CUBIC)


def fbm(shape, seed, octaves=(256, 128, 64, 32, 16), weights=(1, .5, .25, .125, .06)):
    acc = np.zeros(shape, np.float32)
    for o, w, k in zip(octaves, weights, range(99)):
        acc += w * _noise(shape, o, seed + k)
    acc -= acc.min(); acc /= (acc.max() + 1e-6)
    return acc


_LINEN = None
def linen() -> np.ndarray:
    """Raw linen canvas, PWxPH RGB float. Two fine gratings (warp/weft) + slub noise, warm off-white."""
    global _LINEN
    if _LINEN is None:
        y, x = np.mgrid[0:PH, 0:PW].astype(np.float32)
        weave = 0.5 + 0.5 * np.sin(x * 2 * math.pi / 3.1) * np.sin(y * 2 * math.pi / 3.3)
        slub = fbm((PH, PW), 11, octaves=(64, 16, 4), weights=(1, .5, .3))
        tone = 0.80 + 0.10 * weave + 0.10 * slub
        base = np.array([0.90, 0.86, 0.78], np.float32)
        _LINEN = np.clip(tone[..., None] * base[None, None, :], 0, 1).astype(np.float32)
    return _LINEN


_BRUSH = None
def brush() -> np.ndarray:
    """Streaky brush texture 0..1 for ring strokes and the title (horizontal bristle streaks)."""
    global _BRUSH
    if _BRUSH is None:
        n = fbm((PH, PW), 23, octaves=(96, 24, 6), weights=(1, .6, .4))
        streak = _noise((PH, PW), 3, 29)
        streak = cv2.resize(cv2.resize(streak, (PW // 24, PH), interpolation=cv2.INTER_AREA), (PW, PH), interpolation=cv2.INTER_LINEAR)
        _BRUSH = np.clip(0.6 * n + 0.6 * streak, 0, 1).astype(np.float32)
    return _BRUSH


_CRACK = None
def craquelure() -> np.ndarray:
    """Crack network alpha 0..1 (thin dark lines): ridges of two noise fields."""
    global _CRACK
    if _CRACK is None:
        a = fbm((PH, PW), 41, octaves=(140, 70, 35), weights=(1, .5, .25))
        b = fbm((PH, PW), 43, octaves=(90, 45, 22), weights=(1, .5, .25))
        ca = np.exp(-((a - 0.5) ** 2) / (2 * 0.0035 ** 2))
        cb = np.exp(-((b - 0.5) ** 2) / (2 * 0.0035 ** 2))
        c = np.clip(ca + cb, 0, 1)
        c = cv2.GaussianBlur(c, (0, 0), 0.8)
        _CRACK = (c * 0.45).astype(np.float32)
    return _CRACK


_DIST = {}
def dist_from(cx, cy) -> np.ndarray:
    key = (int(cx), int(cy))
    if key not in _DIST:
        y, x = np.mgrid[0:PH, 0:PW].astype(np.float32)
        _DIST[key] = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        if len(_DIST) > 6: _DIST.pop(next(iter(_DIST)))
    return _DIST[key]


_EDGE = None
def edge_noise() -> np.ndarray:
    global _EDGE
    if _EDGE is None:
        _EDGE = (fbm((PH, PW), 57, octaves=(48, 16, 6), weights=(1, .5, .3)) - 0.5).astype(np.float32)
    return _EDGE


# ----------------------------------------------------------------------------- layers
def unpainted(plate: np.ndarray, pencil=0.45) -> np.ndarray:
    """Desaturate, multiply by linen, edge-detect as faint pencil. Same pixels as the colour state."""
    g = cv2.cvtColor((plate * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
    e = cv2.Canny(cv2.GaussianBlur(g, (0, 0), 1.6), 40, 110).astype(np.float32) / 255.0
    e = cv2.GaussianBlur(e, (0, 0), 1.1)
    gf = g.astype(np.float32) / 255.0
    tone = 0.88 + 0.12 * gf
    out = linen() * tone[..., None]
    out = out * (1 - pencil * e[..., None]) + pencil * e[..., None] * np.array([0.30, 0.28, 0.26], np.float32)
    return np.clip(out, 0, 1).astype(np.float32)


def ring_reveal(grey: np.ndarray, color: np.ndarray, cx: float, cy: float, r: float, width=46.0,
                feather=28.0, wobble=40.0, strength=1.0) -> np.ndarray:
    """A ring of wet paint of radius r from (cx,cy); inside it the colour state, outside the grey one.
    r < 0 = nothing happened yet. Ring edge is noisy (wobble px) so it reads as a stroke, not a circle."""
    if r < 0:
        return grey
    d = dist_from(cx, cy) + wobble * edge_noise()
    m = np.clip((r - d) / feather + 0.5, 0, 1)
    out = grey * (1 - m[..., None]) + color * m[..., None]
    if strength > 0 and width > 0:
        ring = np.clip(1 - np.abs(d - r) / width, 0, 1)
        ring = ring * ring * (0.55 + 0.6 * brush())
        ochre = np.array([0.86, 0.66, 0.30], np.float32)
        white = np.array([0.97, 0.95, 0.90], np.float32)
        mix = brush()[..., None]
        paint = ochre * (1 - mix) + white * mix
        a = (strength * ring)[..., None]
        out = out * (1 - a) + paint * a
    return out


def reveal_only(grey, color, cx, cy, r, feather=60.0, wobble=50.0):
    return ring_reveal(grey, color, cx, cy, r, width=0, feather=feather, wobble=wobble, strength=0)


def old_paint(plate: np.ndarray, amount=1.0) -> np.ndarray:
    """Varnish-yellow, cooler and darker, craquelure. amount 0..1."""
    if amount <= 0: return plate
    g = cv2.cvtColor((plate * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
    cold = np.stack([g * 0.62, g * 0.68, g * 0.80], -1)
    varnish = np.array([1.0, 0.93, 0.74], np.float32)
    aged = (plate * 0.45 + cold * 0.55) * varnish * 0.80
    c = craquelure()[..., None]
    aged = aged * (1 - c) + c * np.array([0.12, 0.10, 0.09], np.float32)
    return np.clip(plate * (1 - amount) + aged * amount, 0, 1).astype(np.float32)


def grade(plate, mult=(1, 1, 1), lift=0.0, sat=1.0):
    out = plate * np.array(mult, np.float32) + lift
    if sat != 1.0:
        g = out.mean(-1, keepdims=True); out = g + (out - g) * sat
    return np.clip(out, 0, 1).astype(np.float32)


def leading_edge(color: np.ndarray, grey: np.ndarray, x_edge: float, t: float, band=140.0, mirror=False) -> np.ndarray:
    """Everything right of x_edge is still linen; the edge is a wet noisy band that crawls with t."""
    y, x = np.mgrid[0:PH, 0:PW].astype(np.float32) if False else (None, None)
    xs = np.arange(PW, dtype=np.float32)[None, :]
    wob = 70.0 * edge_noise() + 25.0 * np.sin(np.arange(PH, dtype=np.float32)[:, None] * 0.05 + t * 6.0)
    m = np.clip((x_edge + wob - xs) / band + 0.5, 0, 1)
    if mirror: m = 1 - m
    out = grey * (1 - m[..., None]) + color * m[..., None]
    ring = np.clip(1 - np.abs(xs + wob - x_edge) / 30.0, 0, 1) * (0.4 + 0.6 * brush())
    ochre = np.array([0.86, 0.66, 0.30], np.float32)
    a = (0.7 * ring)[..., None]
    return out * (1 - a) + ochre * a


def pebbles(frame: np.ndarray, pts, t, t0):
    """Hand-painted 3-frame flicker of pebbles trickling off the ledge: small dabs fall from pts for 1.2 s."""
    out = frame.copy()
    k = int((t - t0) * FPS)
    if k < 0: return out
    for i, (px, py) in enumerate(pts):
        age = (t - t0) - i * 0.12
        if age < 0 or age > 1.2: continue
        step = int(age * FPS) // 3 * 3 / FPS   # hold every 3 frames (painted flicker, not a smooth fall)
        y = int(py + 900 * step * step + 40 * step); x = int(px + 25 * step * (1 if i % 2 else -1))
        if 0 <= y < PH - 8 and 0 <= x < PW - 8:
            cv2.circle(out, (x, y), 6 + (i % 3), (0.35, 0.33, 0.30), -1)
    return out


# ----------------------------------------------------------------------------- camera
def view(plate: np.ndarray, cx: float, cy: float, zoom: float) -> np.ndarray:
    """Output 1920x1080 window centred on (cx,cy) of the plate, zoom 1 = 1920 px of plate across. Float affine."""
    s = zoom * OW / PW * (PW / 1920.0)          # output px per plate px
    s = zoom
    # keep the window inside the plate (no replicated-edge streaks)
    cx = min(max(cx, OW / 2 / s), PW - OW / 2 / s); cy = min(max(cy, OH / 2 / s), PH - OH / 2 / s)
    M = np.array([[s, 0, OW / 2 - s * cx], [0, s, OH / 2 - s * cy]], np.float32)
    return cv2.warpAffine(plate, M, (OW, OH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def whip(plate_a, plate_b, u, va, vb, blur_samples=6, axis="y", sign=1):
    """Whip-pan join a->b over u 0..1: a accelerates off along `axis`, b decelerates in; motion blur by sub-frame
    averaging; the cut sits at u=0.5 inside the blur. va/vb = (cx, cy, zoom) rest views. sign -1 = up / left."""
    acc = np.zeros((OH, OW, 3), np.float32)
    for k in range(blur_samples):
        uu = min(1.0, max(0.0, u + (k - blur_samples / 2) / blur_samples * 0.12))
        e = ease(uu)
        travel = 700.0 * sign
        if uu < 0.5:
            cx, cy, z = va
            off = travel * e
            fr = view(plate_a, cx + (off if axis == "x" else 0), cy + (off if axis == "y" else 0), z)
        else:
            cx, cy, z = vb
            off = travel * (1 - e)
            fr = view(plate_b, cx - (off if axis == "x" else 0), cy - (off if axis == "y" else 0), z)
        acc += fr
    out = acc / blur_samples
    # streak the blur along the axis at the peak of the whip
    k = int(60 * math.sin(math.pi * u))
    if k > 2:
        ker = np.zeros((k, k), np.float32)
        if axis == "y": ker[:, k // 2] = 1.0 / k
        else: ker[k // 2, :] = 1.0 / k
        out = cv2.filter2D(out, -1, ker)
    return out


# ----------------------------------------------------------------------------- lantern cutout + title
def cutout(plate: np.ndarray, bg_dark=0.22) -> tuple[np.ndarray, np.ndarray]:
    """Key the lantern off its plain dark background: alpha from luminance distance to the corner colour."""
    # H2 came back with a pale painted blotch behind the lantern, so the key is the OBJECT, not the background:
    # warm saturated brass/flame, or dark metal, inside the centre third of the frame.
    hsv = cv2.cvtColor((plate * 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    Hh, S, V = hsv[..., 0], hsv[..., 1] / 255.0, hsv[..., 2] / 255.0
    warm = np.clip((S - 0.30) / 0.15, 0, 1) * np.clip(1 - np.abs(Hh - 18) / 22, 0, 1)
    dark = np.clip((0.30 - V) / 0.10, 0, 1)
    a = np.clip(warm + dark, 0, 1)
    box = np.zeros_like(a); box[:, int(PW * 0.36):int(PW * 0.64)] = 1.0
    a = a * box
    a = cv2.morphologyEx(a, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    # fill the holes (pale glass, highlights): flood the outside, everything not reached is inside the object
    solid = (a > 0.5).astype(np.uint8)
    ff = solid.copy(); mask = np.zeros((PH + 2, PW + 2), np.uint8)
    cv2.floodFill(ff, mask, (0, 0), 1)
    holes = (ff == 0).astype(np.uint8)
    # only the small holes (glass panes, highlights); the big gap inside the handle loop stays open
    n, lab, stats, _ = cv2.connectedComponentsWithStats(holes)
    small = np.zeros_like(holes)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] < 12000: small[lab == i] = 1
    a = np.clip(a + small.astype(np.float32), 0, 1)
    a = cv2.GaussianBlur(a, (0, 0), 1.2)
    # keep the biggest blob only
    m8 = (a > 0.5).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m8)
    if n > 1:
        big = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA]); a = a * (lab == big)
    ys, xs = np.where(a > 0.5)
    if len(xs) == 0: return plate, a
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    return plate[y0:y1 + 1, x0:x1 + 1], a[y0:y1 + 1, x0:x1 + 1]


def paste(frame, sprite, alpha, cx, cy, scale, angle_deg, tint=None):
    """Composite sprite (RGB float) with alpha at centre (cx,cy) in plate px, scaled + rotated (float affine)."""
    h, w = sprite.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle_deg, scale)
    M[0, 2] += cx - w / 2; M[1, 2] += cy - h / 2
    sp = cv2.warpAffine(sprite, M, (PW, PH), flags=cv2.INTER_LINEAR, borderValue=0)
    al = cv2.warpAffine(alpha, M, (PW, PH), flags=cv2.INTER_LINEAR, borderValue=0)[..., None]
    if tint is not None: sp = sp * np.array(tint, np.float32)
    return frame * (1 - al) + sp * al


def arc_stroke(frame, x0, y0, x1, y1, u, fade=1.0):
    """A wet slate-blue brush stroke arcing from (x0,y0) to (x1,y1), drawn up to u 0..1, hanging in the air (fade)."""
    if fade <= 0 or u <= 0: return frame
    out = frame.copy()
    n = 40; pts = []
    for i in range(int(n * u) + 1):
        s = i / n
        x = lerp(x0, x1, s); y = lerp(y0, y1, s) - 220 * math.sin(math.pi * s)
        pts.append((int(x), int(y)))
    if len(pts) > 1:
        layer = frame.copy()
        cv2.polylines(layer, [np.array(pts, np.int32)], False, (0.50, 0.62, 0.78), 44, cv2.LINE_AA)
        cv2.polylines(layer, [np.array(pts, np.int32)], False, (0.82, 0.88, 0.94), 16, cv2.LINE_AA)
        layer = layer * (0.8 + 0.4 * brush()[..., None])
        a = 0.85 * fade
        out = out * (1 - a) + layer * a
    return out


def trunk_wipe(out_frame, u):
    """A dark painted tree trunk sweeps across the 1920x1080 output right->left over u 0..1 (full-frame join)."""
    if u <= 0 or u >= 1.4: return out_frame
    x = int(OW * 1.25 - OW * 1.6 * ease(u / 1.0))
    w = int(OW * 0.55)
    b = cv2.resize(cv2.resize(brush(), (48, OH)), (OW, OH), interpolation=cv2.INTER_LINEAR)   # vertical bark streaks
    b2 = cv2.resize(brush(), (OW, OH))
    trunk = np.stack([0.10 + 0.16 * b + 0.05 * b2, 0.07 + 0.11 * b + 0.04 * b2, 0.05 + 0.07 * b + 0.03 * b2], -1).astype(np.float32)
    m = np.zeros((OH, OW), np.float32)
    x0, x1 = max(0, x), min(OW, x + w)
    if x1 > x0: m[:, x0:x1] = 1.0
    m = cv2.GaussianBlur(m, (0, 0), 18)[..., None]
    return out_frame * (1 - m) + trunk * m


def splash(frame, cx, cy, k):
    """4-frame painted splash: radial slate-blue strokes, k = frame index 0..3."""
    if k < 0 or k > 3: return frame
    out = frame.copy()
    r = 60 + 70 * k
    for i in range(14):
        a = math.pi + (i / 13.0) * math.pi + 0.15 * math.sin(i * 7.0)
        x1 = int(cx + math.cos(a) * r * 0.4); y1 = int(cy + math.sin(a) * r * 0.4)
        x2 = int(cx + math.cos(a) * r); y2 = int(cy + math.sin(a) * r * 0.8)
        cv2.line(out, (x1, y1), (x2, y2), (0.55, 0.65, 0.78), 5 + (i % 3) * 3)
    return out


_TITLE = None
def title_layer():
    """Two-line hand-lettered title as RGB + alpha, PWxPH. Marker Felt Wide (hand-lettered storybook), ochre-cream."""
    global _TITLE
    if _TITLE is None:
        from PIL import Image, ImageDraw, ImageFont
        im = Image.new("L", (PW, PH), 0); d = ImageDraw.Draw(im)
        font_path = "/System/Library/Fonts/MarkerFelt.ttc"
        f1 = ImageFont.truetype(font_path, 170, index=1); f2 = ImageFont.truetype(font_path, 230, index=1)
        lines = [("HANK & DOUG'S", f1, PH * 0.13), ("WILD RESCUE", f2, PH * 0.29)]
        for txt, f, y in lines:
            w = d.textlength(txt, font=f)
            d.text(((PW - w) / 2, y), txt, font=f, fill=255)
        a = np.array(im).astype(np.float32) / 255.0
        # rough the edges like a loaded brush
        a = np.clip(a + 0.25 * (brush() - 0.5) * (a > 0.02), 0, 1)
        a = cv2.GaussianBlur(a, (0, 0), 0.9)
        col = np.array([0.95, 0.86, 0.60], np.float32)[None, None, :] * (0.85 + 0.3 * brush()[..., None])
        _TITLE = (np.clip(col, 0, 1).astype(np.float32), a.astype(np.float32))
    return _TITLE


def title_reveal(frame, u, shadow=True):
    """Stroke reveal: line 1 wipes left->right over u 0..0.5, line 2 over 0.45..1 with a bristly edge."""
    col, a = title_layer()
    xs = np.arange(PW, dtype=np.float32)[None, :]
    ys = np.arange(PH, dtype=np.float32)[:, None]
    wob = 60 * edge_noise()
    u1 = ease(u / 0.55); u2 = ease((u - 0.45) / 0.55)
    line1 = ys < PH * 0.26
    w1 = np.clip((PW * 1.1 * u1 - 60 - xs + wob) / 40, 0, 1)
    w2 = np.clip((PW * 1.1 * u2 - 60 - xs + wob) / 40, 0, 1)
    wipe = np.where(line1, w1, w2)
    aa = (a * wipe)[..., None]
    out = frame
    if shadow:
        sh = np.roll(aa, (6, 6), (0, 1))
        out = out * (1 - 0.55 * sh)
    return out * (1 - aa) + col * aa
