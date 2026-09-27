#!/usr/bin/env python3
"""Rhubarb visemes -> clean flat-design cartoon dog talking. 100% local."""
import os, math
from PIL import Image, ImageDraw, ImageFilter

W = H = 720
FPS = 24
HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, "visemes.tsv")
FR_DIR = os.path.join(HERE, "frames"); os.makedirs(FR_DIR, exist_ok=True)
for f in os.listdir(FR_DIR):
    if f.endswith(".png"): os.remove(os.path.join(FR_DIR, f))

# ---- load viseme timeline ----
timeline = []
for line in open(TSV):
    t, shape = line.strip().split("\t")
    timeline.append((float(t), shape))
DUR = timeline[-1][0]
NF = int(DUR * FPS)

def viseme_at(t):
    cur = "X"
    for tt, sh in timeline:
        if tt <= t: cur = sh
        else: break
    return cur

# ---- palette ----
TAN   = (214, 158, 105); TAN_D = (188, 132, 82)
BROWN = (150, 96, 54);   BROWN_D=(120, 74, 40)
NOSE  = (54, 40, 38);    DARK  = (60, 32, 30)
TEETH = (250, 248, 240); TONGUE=(207, 96, 102)
WHITE = (255,255,255);   PUP   = (45, 32, 28)

def bg():
    img = Image.new("RGB", (W, H), (44, 54, 48))
    top = Image.new("RGB", (W, H), (96, 120, 96))
    mask = Image.new("L", (W, H), 0); md = ImageDraw.Draw(mask)
    for y in range(H):
        md.line([(0, y), (W, y)], fill=int(150 * (1 - y / H)))
    img = Image.composite(top, img, mask)
    return img

def ellipse(d, cx, cy, rx, ry, fill, outline=None, w=0):
    d.ellipse([cx-rx, cy-ry, cx+rx, cy+ry], fill=fill, outline=outline, width=w)

def draw_mouth(d, cx, my, shape):
    """9 Preston-Blair-ish mouth shapes."""
    if shape in ("X", "A"):            # rest / closed (M,B,P)
        d.arc([cx-46, my-22, cx+46, my+26], 18, 162, fill=DARK, width=7)
    elif shape == "B":                 # teeth-together / ee
        ellipse(d, cx, my, 40, 14, DARK)
        d.rectangle([cx-34, my-12, cx+34, my-1], fill=TEETH)
    elif shape == "C":                 # eh (medium open)
        ellipse(d, cx, my+2, 44, 26, DARK)
        d.rectangle([cx-36, my-22, cx+36, my-10], fill=TEETH)
    elif shape == "D":                 # ah (wide open)
        ellipse(d, cx, my+6, 50, 42, DARK)
        d.rectangle([cx-40, my-34, cx+40, my-20], fill=TEETH)
        ellipse(d, cx, my+30, 30, 16, TONGUE)
    elif shape == "E":                 # oh (rounded)
        ellipse(d, cx, my+4, 34, 34, DARK)
        d.rectangle([cx-24, my-28, cx+24, my-18], fill=TEETH)
    elif shape == "F":                 # oo / w (pucker)
        ellipse(d, cx, my+2, 20, 20, DARK)
        ellipse(d, cx, my+2, 24, 22, None, outline=BROWN_D, w=5)
    elif shape == "G":                 # F,V (teeth on lip)
        d.arc([cx-44, my-18, cx+44, my+24], 18, 162, fill=DARK, width=6)
        d.rectangle([cx-30, my-10, cx+30, my+1], fill=TEETH)
    elif shape == "H":                 # L (tongue)
        ellipse(d, cx, my+4, 42, 30, DARK)
        d.rectangle([cx-32, my-24, cx+32, my-13], fill=TEETH)
        ellipse(d, cx, my+2, 16, 18, TONGUE)

def draw_frame(shape, blink=False, bob=0):
    img = bg()
    d = ImageDraw.Draw(img)
    cx = W // 2; cy = H // 2 + 30 + bob
    # droopy ears (behind head)
    for sgn in (-1, 1):
        ex = cx + sgn * 150
        d.ellipse([ex-58, cy-150, ex+58, cy+170], fill=BROWN)
        d.ellipse([ex-40, cy-130, ex+40, cy+150], fill=BROWN_D)
    # head
    ellipse(d, cx, cy, 175, 185, TAN)
    ellipse(d, cx, cy-10, 175, 175, None, outline=TAN_D, w=4)
    # brow ridge / eyebrows
    d.arc([cx-120, cy-120, cx-20, cy-30], 200, 350, fill=BROWN_D, width=10)
    d.arc([cx+20, cy-120, cx+120, cy-30], 190, 340, fill=BROWN_D, width=10)
    # eyes
    for sgn in (-1, 1):
        ex = cx + sgn * 62; ey = cy - 60
        ellipse(d, ex, ey, 40, 46, WHITE)
        if blink:
            d.line([ex-34, ey, ex+34, ey], fill=PUP, width=8)
        else:
            ellipse(d, ex+sgn*4, ey+6, 20, 24, PUP)
            ellipse(d, ex+sgn*4-6, ey-2, 6, 7, WHITE)   # highlight
    # snout
    ellipse(d, cx, cy+74, 96, 74, (226, 176, 128))
    ellipse(d, cx, cy+30, 34, 26, NOSE)                  # nose
    ellipse(d, cx-10, cy+22, 7, 5, (110, 90, 88))        # nose highlight
    # mouth (viseme)
    draw_mouth(d, cx, cy + 104, shape)
    return img.filter(ImageFilter.SMOOTH)

# ---- render ----
for i in range(NF):
    t = i / FPS
    sh = viseme_at(t)
    blink = (i % 48) in (0, 1, 2)              # occasional blink
    bob = int(2 * math.sin(t * 2 * math.pi))   # gentle idle bob
    draw_frame(sh, blink=blink, bob=bob).save(os.path.join(FR_DIR, f"f_{i:04d}.png"))
print(f"rendered {NF} frames at {FPS}fps ({DUR:.1f}s)")
