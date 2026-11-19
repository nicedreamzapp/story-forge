#!/usr/bin/env python3
"""sbs_v5.py — plan_v5 B1 side-by-side: before | after | master, same height, labelled. Usage: sbs_v5.py BEFORE AFTER MASTER OUT"""
import sys
from PIL import Image, ImageDraw, ImageFont
b, a, m, out = sys.argv[1:5]
H = 768
ims = [Image.open(p).convert("RGB") for p in (b, a, m)]
ims = [im.resize((round(im.width * H / im.height), H), Image.LANCZOS) for im in ims]
gap = 16; bar = 56
W = sum(im.width for im in ims) + gap * 2
canvas = Image.new("RGB", (W, H + bar), (18, 18, 20)); d = ImageDraw.Draw(canvas)
try: font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 30)
except Exception: font = ImageFont.load_default()
x = 0
for im, lab in zip(ims, ("BEFORE (v4 still)", "AFTER (klein edit)", "MASTER (canon)")):
    canvas.paste(im, (x, bar)); d.text((x + 14, 12), lab, fill=(240, 236, 228), font=font); x += im.width + gap
canvas.save(out); print(out, canvas.size)
