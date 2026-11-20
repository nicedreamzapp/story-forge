#!/usr/bin/env python3
"""The Heading — 30 s concert trailer (Matt 11/07): cartoon -> the music starts -> it turns real.

Cartoon home (hand, bluff) -> cartoon stadium, music kicks in at 14.0 s and the real world flickers in ->
the controls appear and the crowd signals him (cartoon -> real) -> real: he answers with a gesture, no words.
  ~/AI/ComfyUI/venv/bin/python projects/the_heading/edit_concert.py
Writes final/concert_picture.mp4 and final/concert_timeline.json; mix_concert.py adds the sound.
"""
import json
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).resolve().parent
FPS, W, H = 24, 1280, 544
FF = "/opt/homebrew/bin/ffmpeg"
DROP = 14.0   # the music kicks in here (mix_concert.py aligns the score's onset to it)


def frames(path):
    cap, out = cv2.VideoCapture(str(path)), []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        out.append(cv2.resize(f, (W, H)) if f.shape[:2] != (H, W) else f)
    return out


def at(lst, i):
    return lst[max(0, min(i, len(lst) - 1))]


def push(img, k, s0=1.0, s1=1.08, bob=0.0, t=0.0):
    s = s0 + (s1 - s0) * k
    M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, s)
    M[1, 2] += bob * np.sin(t * 2 * np.pi * 2.0)   # a little dance bounce
    return cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)


def in_any(t, spans):
    return any(a <= t < b for a, b in spans)


C = {k: frames(P / f"clips/{k}_final.mp4") for k in ("c1_hand", "c2_bluff", "r3_dance", "c4_signal", "r4_signal", "r5_answer")}
C3 = cv2.resize(cv2.imread(str(P / "stills/LOCKED_c3_dance.png")), (W, H))

# real breaks in on the beat, faster and longer, until it stays
DANCE_REAL = [(14.0, 14.12), (14.35, 14.5), (14.75, 15.0), (15.2, 15.6)]   # real from 15.8
SIGNAL_REAL = [(19.6, 19.7), (20.1, 20.3), (20.6, 21.0)]                   # real from 21.3
ANSWER_TOON = []   # cut 11/07: a one-frame flash of the signal shot read as a mistake
GLITCH_AT = [14.0, 14.35, 14.75, 15.2, 19.6, 20.1, 20.6]

font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Georgia.ttf", 64)


def title(img, alpha):
    pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).convert("RGBA")
    layer = Image.new("RGBA", pil.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    txt = "T H E   H E A D I N G"
    bw = d.textlength(txt, font=font)
    d.text(((W - bw) / 2 + 2, H * 0.10 + 2), txt, font=font, fill=(0, 0, 0, int(170 * alpha)))
    d.text(((W - bw) / 2, H * 0.10), txt, font=font, fill=(240, 232, 214, int(255 * alpha)))
    return cv2.cvtColor(np.array(Image.alpha_composite(pil, layer).convert("RGB")), cv2.COLOR_RGB2BGR)


enc = subprocess.Popen([FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                        "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p",
                        str(P / "final/concert_picture.mp4")], stdin=subprocess.PIPE)
for n in range(30 * FPS):
    t = n / FPS
    if t < 6:
        fr = at(C["c1_hand"], n)
    elif t < 12:
        fr = at(C["c2_bluff"], n - 6 * FPS)
    elif t < 18:
        i = n - 12 * FPS
        # the real dance clip runs from the drop; before it the cartoon still bounces to the quiet intro
        real = at(C["r3_dance"], n - int(DROP * FPS) + 24)
        toon = push(C3, (t - 12) / 6, 1.0, 1.06, bob=3.0 if t >= DROP else 1.0, t=t)
        if t < DROP:
            fr = toon
        elif in_any(t, DANCE_REAL) or t >= 15.8:
            fr = real
        else:
            fr = toon
    elif t < 24:
        i = n - 18 * FPS
        real, toon = at(C["r4_signal"], i), at(C["c4_signal"], i)
        fr = real if (in_any(t, SIGNAL_REAL) or t >= 21.3) else toon
    else:
        i = n - 24 * FPS
        fr = at(C["r5_answer"], i)
        if in_any(t, ANSWER_TOON):
            fr = at(C["c4_signal"], len(C["c4_signal"]) - 1)
        if t >= 27.3:
            fr = title(fr, min((t - 27.3) / 0.4, 1.0))
        if t >= 29.6:
            fr = (fr.astype(np.float32) * (30 - t) / 0.4).astype(np.uint8)
    enc.stdin.write(fr.tobytes())
enc.stdin.close()
enc.wait()

(P / "final/concert_timeline.json").write_text(json.dumps({
    "fps": FPS, "duration": 30.0, "drop": DROP,
    "shots": [{"id": "c1_hand", "start": 0, "end": 6, "look": "cartoon"},
              {"id": "c2_bluff", "start": 6, "end": 12, "look": "cartoon"},
              {"id": "dance", "start": 12, "end": 18, "look": "cartoon still, music kicks in at 14.0, real flickers in, real from 15.8"},
              {"id": "signal", "start": 18, "end": 24, "look": "cartoon controls + crowd signal, real from 21.3"},
              {"id": "r5_answer", "start": 24, "end": 30, "look": "real: palm raised in answer, nod, hands on the controls; title"}],
    "voice": [{"line": "v1", "speaker": "matt", "start": 1.0, "text": "He has never missed a morning.", "file": "voices/matt/v1.wav"},
              {"line": "v2", "speaker": "matt", "start": 7.2, "text": "The last house in the county with no signal.", "file": "voices/matt/v2.wav"},
              {"line": "w3", "speaker": "matt", "start": 12.0, "text": "Then the music started.", "file": "voices/matt/w3.wav"},
              {"line": "w5", "speaker": "matt", "start": 24.3, "text": "Three hundred people. All of them waiting on him.", "file": "voices/matt/w5.wav"}],
    "title": {"text": "THE HEADING", "start": 27.3, "end": 30.0},
    "glitch_at": GLITCH_AT}, indent=1))
print("concert picture done")
