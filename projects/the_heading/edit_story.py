#!/usr/bin/env python3
"""The Heading — 30 s story trailer v3 (Matt 11/07 10:55: "it should not repeat itself", "the people look weird").
Every shot is a new beat; the look moves cartoon -> real across the CUTS, never by replaying one shot in two looks.
Crowds are silhouettes or phone lights, so there are no crowd faces.

Cartoon home (hand, bluff) -> cartoon stadium, music kicks in at 14.0 s and the real world flickers in ->
the controls appear and the crowd signals him (cartoon -> real) -> real: he answers with a gesture, no words.
  ~/AI/ComfyUI/venv/bin/python projects/the_heading/edit_concert.py
Writes final/story_picture.mp4 and final/story_timeline.json; mix_concert.py adds the sound.
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


C = {k: frames(P / f"clips/{k}_final.mp4") for k in ("c1_hand", "c2_bluff", "n3_backlit", "n4_lights", "n5_face")}
# the cartoon world snaps back for a frame or two as the real one takes over (forward-moving, never a replay)
BACK_TO_TOON = [(18.25, 18.33), (18.7, 18.75)]
GLITCH_AT = [14.0, 18.0, 18.25, 18.7]

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
                        str(P / "final/story_picture.mp4")], stdin=subprocess.PIPE)
for n in range(30 * FPS):
    t = n / FPS
    if t < 6:
        fr = at(C["c1_hand"], n)
    elif t < 12:
        fr = at(C["c2_bluff"], n - 6 * FPS)
    elif t < 18:
        fr = at(C["n3_backlit"], n - 12 * FPS)
    elif t < 24:
        # push in toward Wes in his pool of light (he is tiny in the wide frame)
        k = (t - 18) / 6
        k = k * k * (3 - 2 * k)
        src = at(C["n4_lights"], n - 18 * FPS)
        M = cv2.getRotationMatrix2D((0.49 * W, 0.60 * H), 0, 1.0 + 0.55 * k)
        fr = cv2.warpAffine(src, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        if in_any(t, BACK_TO_TOON):
            fr = at(C["n3_backlit"], len(C["n3_backlit"]) - 1)
    else:
        # only the calm first 2.4 s of the clip, slowed to fill the shot (his mouth falls open after that)
        pos = (t - 24) / 6 * 2.4 * FPS
        a, b = int(pos), min(int(pos) + 1, len(C["n5_face"]) - 1)
        w = pos - int(pos)
        fr = cv2.addWeighted(at(C["n5_face"], a), 1 - w, at(C["n5_face"], b), w, 0)
        if t >= 27.3:
            fr = title(fr, min((t - 27.3) / 0.4, 1.0))
        if t >= 29.6:
            fr = (fr.astype(np.float32) * (30 - t) / 0.4).astype(np.uint8)
    enc.stdin.write(fr.tobytes())
enc.stdin.close()
enc.wait()

(P / "final/story_timeline.json").write_text(json.dumps({
    "fps": FPS, "duration": 30.0, "drop": DROP,
    "shots": [{"id": "c1_hand", "start": 0, "end": 6, "look": "cartoon"},
              {"id": "c2_bluff", "start": 6, "end": 12, "look": "cartoon"},
              {"id": "n3_backlit", "start": 12, "end": 18, "look": "cartoon, stadium from behind, music kicks in at 14.0"},
              {"id": "n4_lights", "start": 18, "end": 24, "look": "real: phone lights all turn to him, controls rise"},
              {"id": "n5_face", "start": 24, "end": 30, "look": "real close-up: he nods; title"}],
    "voice": [{"line": "v1", "speaker": "matt", "start": 1.0, "text": "He has never missed a morning.", "file": "voices/matt/v1.wav"},
              {"line": "v2", "speaker": "matt", "start": 7.2, "text": "The last house in the county with no signal.", "file": "voices/matt/v2.wav"},
              {"line": "w3", "speaker": "matt", "start": 12.0, "text": "Then the music started.", "file": "voices/matt/w3.wav"},
              {"line": "x5", "speaker": "matt", "start": 25.0, "text": "Every one of them waiting on him.", "file": "voices/matt/x5.wav"}],
    "title": {"text": "THE HEADING", "start": 27.3, "end": 30.0},
    "glitch_at": GLITCH_AT}, indent=1))
print("story picture done")
