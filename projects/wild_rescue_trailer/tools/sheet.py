#!/usr/bin/env python3
"""contact sheet: sheet.py OUT.jpg img1 img2 ... (labels = file stems), 3 per row, 416 px wide tiles"""
import sys
from PIL import Image, ImageDraw
out, files = sys.argv[1], sys.argv[2:]
tw = 416; tiles = []
for f in files:
    im = Image.open(f).convert("RGB"); im = im.resize((tw, int(im.size[1] * tw / im.size[0])))
    ImageDraw.Draw(im).text((6, 6), f.split("/")[-1][:-4], fill=(255, 255, 0)); tiles.append(im)
th = max(t.size[1] for t in tiles); cols = 3; rows = (len(tiles) + cols - 1) // cols
S = Image.new("RGB", (cols * tw, rows * th), (0, 0, 0))
for i, t in enumerate(tiles): S.paste(t, ((i % cols) * tw, (i // cols) * th))
S.save(out, quality=85)
