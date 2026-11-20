#!/usr/bin/env python3
"""The Heading — 30 s trailer edit: painted -> real breaking in -> flicker -> real.

Picture is composited frame by frame from the kept clips and their paintify twins (same motion,
so flickers never jump). Run with the ComfyUI venv (opencv-contrib + PIL):
  ~/AI/ComfyUI/venv/bin/python projects/the_heading/edit_trailer.py
Writes final/heading_trailer_picture.mp4, final/timeline.json; the audio mix is the ffmpeg step at the end.
"""
import json
import math
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).resolve().parent
FPS, W, H = 24, 1280, 544
FF = "/opt/homebrew/bin/ffmpeg"
(P / "final").mkdir(exist_ok=True)


def frames(path):
    cap = cv2.VideoCapture(str(path))
    out = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        out.append(cv2.resize(f, (W, H)) if f.shape[:2] != (H, W) else f)
    return out


def still(path):
    return cv2.resize(cv2.imread(str(path)), (W, H))


C = {k: frames(P / f"clips/{k}_final.mp4") for k in ("t1_hand", "t2_bluff", "t3_window", "t4_road_real", "t5_level")}
T = {k: frames(P / f"twins/{k}_painted.mp4") for k in ("t3_window", "t4_road_real", "t5_level")}
REAL_BLUFF = still(P / "stills/LOCKED_t2_bluff_real.png")


def at(lst, i):
    return lst[min(i, len(lst) - 1)]


def ramp_x(x0, x1):
    """horizontal soft mask: 1 left of x0, 0 right of x1"""
    xs = np.arange(W, dtype=np.float32)
    m = np.clip((x1 - xs) / max(x1 - x0, 1), 0, 1)
    return np.repeat(m[None, :], H, 0)[..., None]


def ramp_y(y0, y1):
    """vertical soft mask: 1 above y0, 0 below y1"""
    ys = np.arange(H, dtype=np.float32)
    m = np.clip((y1 - ys) / max(y1 - y0, 1), 0, 1)
    return np.repeat(m[:, None], W, 1)[..., None]


WIN = ramp_x(0.36 * W, 0.44 * W)        # t3: the window side of the room
SKY = ramp_y(0.66 * H, 0.74 * H)        # t4: everything outside the windshield (above the dashboard)


def mix(a, b, m):
    return (a.astype(np.float32) * m + b.astype(np.float32) * (1 - m)).astype(np.uint8)


def zoom(img, s):
    M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, s)
    return cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)


def tilt(img, deg=4.0):
    M = cv2.getRotationMatrix2D((W / 2, H / 2), deg, 1.10)
    return cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)


def in_any(t, spans):
    return any(a <= t < b for a, b in spans)


# flicker schedules (seconds, absolute)
BLUFF_FLASH = [(9.40, 9.48), (10.55, 10.64), (11.30, 11.42)]                        # real breaks in
T3_REAL = [(13.6, 13.68), (14.4, 14.55), (15.1, 15.35), (15.7, 16.1), (16.4, 17.2)]  # faster, longer
T4_REAL = [(21.0, 22.2), (22.4, 24.0)]                                              # wipe up, snap back, real
T5_FLASH = [(26.4, 26.48)]
GLITCH_AT = [9.40, 10.55, 11.30, 13.6, 14.4, 15.1, 15.7, 16.4, 22.2, 26.4]

font = None
for f in ("/System/Library/Fonts/Supplemental/Georgia.ttf", "/System/Library/Fonts/Supplemental/Times New Roman.ttf"):
    if Path(f).is_file():
        font = ImageFont.truetype(f, 64)
        break


def title(img, alpha):
    pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).convert("RGBA")
    layer = Image.new("RGBA", pil.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    txt = "T H E   H E A D I N G"
    bw = d.textlength(txt, font=font)
    d.text(((W - bw) / 2 + 2, H * 0.44 + 2), txt, font=font, fill=(0, 0, 0, int(160 * alpha)))
    d.text(((W - bw) / 2, H * 0.44), txt, font=font, fill=(236, 230, 218, int(255 * alpha)))
    return cv2.cvtColor(np.array(Image.alpha_composite(pil, layer).convert("RGB")), cv2.COLOR_RGB2BGR)


enc = subprocess.Popen([FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                        "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p",
                        str(P / "final/heading_trailer_picture.mp4")], stdin=subprocess.PIPE)
N = 30 * FPS
for n in range(N):
    t = n / FPS
    if t < 6:                                   # painted
        fr = at(C["t1_hand"], n)
    elif t < 12:                                # painted, real starts breaking in
        i = n - 6 * FPS
        fr = at(C["t2_bluff"], i)
        if in_any(t, BLUFF_FLASH):
            fr = zoom(REAL_BLUFF, 1.0 + 0.04 * i / (6 * FPS))
    elif t < 18:                                # hybrid (painted window) <-> fully real
        i = n - 12 * FPS
        real, paint = at(C["t3_window"], i), at(T["t3_window"], i)
        # starts fully painted (continuing from t2); the real room breaks in more and more,
        # the window stays painted (her footage), ending on the hybrid
        fr = mix(paint, real, WIN) if (in_any(t, T3_REAL) or t >= 17.2) else paint
    elif t < 24:                                # tilted road: painted sky -> wipe to real -> snap -> real
        i = n - 18 * FPS
        real, paint = at(C["t4_road_real"], i), at(T["t4_road_real"], i)
        if t < 21.0:
            fr = mix(paint, real, SKY)
        elif t < 21.6:                          # real wipes up from the road to the sky
            k = (t - 21.0) / 0.6
            line = H * (0.74 - 0.80 * k)
            fr = mix(paint, real, ramp_y(line - 0.06 * H, line))
        elif in_any(t, T4_REAL):
            fr = real
        else:
            fr = mix(paint, real, SKY)
        fr = tilt(fr, 4.0)
    else:                                       # painted dissolves into real, holds real for the title
        i = n - 24 * FPS
        real, paint = at(C["t5_level"], i), at(T["t5_level"], i)
        k = float(np.clip((t - 25.5) / 1.5, 0, 1))
        k = k * k * (3 - 2 * k)
        fr = mix(paint, real, np.float32(1 - k))
        if in_any(t, T5_FLASH):
            fr = paint
        if t >= 27.3:
            fr = title(fr, min((t - 27.3) / 0.4, 1.0))
        if t >= 29.6:
            fr = (fr.astype(np.float32) * (30 - t) / 0.4).astype(np.uint8)
    enc.stdin.write(fr.tobytes())
enc.stdin.close()
enc.wait()

timeline = {
    "fps": FPS, "duration": 30.0,
    "shots": [{"id": "t1_hand", "start": 0, "end": 6, "look": "painted"},
              {"id": "t2_bluff", "start": 6, "end": 12, "look": "painted + real flashes"},
              {"id": "t3_window", "start": 12, "end": 18, "look": "painted <-> hybrid (real room, painted window) flicker"},
              {"id": "t4_road_real", "start": 18, "end": 24, "look": "tilted hybrid (painted outside, real cab) -> wipe -> real"},
              {"id": "t5_level", "start": 24, "end": 30, "look": "painted dissolves to real, title"}],
    "voice": [{"line": "v1", "speaker": "nia", "start": 1.0, "text": "He has never missed a morning."},
              {"line": "v2", "speaker": "nia", "start": 7.2, "text": "The last house in the county with no signal."},
              {"line": "v3", "speaker": "nia", "start": 13.0, "text": "Then my footage started coming back painted."},
              {"line": "v4", "speaker": "wes", "start": 19.4, "text": "They've all been counting on me. Haven't they."},
              {"line": "v5", "speaker": "nia", "start": 24.6, "text": "Three hundred people. And the mornings are running out."}],
    "title": {"text": "THE HEADING", "start": 27.3, "end": 30.0},
    "glitch_at": GLITCH_AT,
}
(P / "final/timeline.json").write_text(json.dumps(timeline, indent=1))
print("picture done", N, "frames")
