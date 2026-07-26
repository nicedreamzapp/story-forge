#!/usr/bin/env python3
"""Royal Gold title cards — premium royal-seal medallion on deep-green/gold field."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PROJ = Path.home() / "Desktop/PROJECTS/story-forge/projects/royal_gold"
LOGO = PROJ / "assets/logo.png"
W, H = 1280, 720
GOLD = (212, 175, 75)
GOLD_BRIGHT = (245, 214, 120)
CREAM = (244, 236, 216)

def bg():
    """deep green radial -> dark, warm gold glow center."""
    base = Image.new("RGB", (W, H), (8, 20, 12))
    # vertical gradient
    top, bot = (14, 34, 20), (4, 10, 6)
    g = Image.new("RGB", (1, H))
    for y in range(H):
        t = y / H
        g.putpixel((0, y), tuple(int(top[i]*(1-t)+bot[i]*t) for i in range(3)))
    base = g.resize((W, H))
    # warm radial glow
    glow = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(glow)
    cx, cy = W//2, H//2
    for r in range(420, 0, -8):
        a = int(70 * (1 - r/420))
        gd.ellipse([cx-r, cy-r*0.78, cx+r, cy+r*0.78], fill=a)
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    gold_layer = Image.new("RGB", (W, H), (150, 110, 40))
    base = Image.composite(gold_layer, base, glow)
    return base

def medallion(diam):
    """cream circle with the crest + double gold ring."""
    sup = 3
    d = diam * sup
    m = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    md = ImageDraw.Draw(m)
    # outer dark ring
    md.ellipse([0, 0, d-1, d-1], fill=(20, 30, 22, 255))
    # gold ring
    pad1 = int(d*0.018)
    md.ellipse([pad1, pad1, d-1-pad1, d-1-pad1], fill=GOLD)
    # cream face
    pad2 = int(d*0.055)
    md.ellipse([pad2, pad2, d-1-pad2, d-1-pad2], fill=CREAM+(255,))
    # paste logo inside cream face
    logo = Image.open(LOGO).convert("RGBA")
    face = d - 2*pad2
    ls = int(face*0.96)
    logo = logo.resize((ls, ls), Image.LANCZOS)
    # logo bg is white -> blend onto cream by making near-white transparent
    px = logo.load()
    for y in range(ls):
        for x in range(ls):
            r, g, b, a = px[x, y]
            if r > 236 and g > 236 and b > 236:
                px[x, y] = (r, g, b, 0)
    off = (d - ls)//2
    m.alpha_composite(logo, (off, off))
    # thin inner gold hairline
    md.ellipse([pad2, pad2, d-1-pad2, d-1-pad2], outline=GOLD, width=int(d*0.006))
    return m.resize((diam, diam), Image.LANCZOS)

def font(path, size, idx=0):
    return ImageFont.truetype(path, size, index=idx)

CP = "/System/Library/Fonts/Supplemental/Copperplate.ttc"
DIDOT = "/System/Library/Fonts/Supplemental/Didot.ttc"

def ctext(draw, cy, text, fnt, fill, ls=0):
    # centered text with optional letter spacing
    if ls:
        widths = [draw.textbbox((0,0), ch, font=fnt)[2] for ch in text]
        total = sum(widths) + ls*(len(text)-1)
        x = (W-total)//2
        for ch, w in zip(text, widths):
            draw.text((x, cy), ch, font=fnt, fill=fill)
            x += w + ls
    else:
        b = draw.textbbox((0,0), text, font=fnt)
        draw.text(((W-(b[2]-b[0]))//2 - b[0], cy), text, font=fnt, fill=fill)

# ---- INTRO card: medallion centered ----
intro = bg()
med = medallion(440)
intro.paste(med, ((W-440)//2, (H-440)//2 - 10), med)
intro.save(PROJ/"stills/card_intro.png")

# ---- OUTRO card: medallion up, tagline + web below ----
outro = bg()
med2 = medallion(360)
outro.paste(med2, ((W-360)//2, 70), med2)
d = ImageDraw.Draw(outro)
ctext(d, 470, "THE GOLD STANDARD IN GARDENING", font(CP, 40), GOLD_BRIGHT, ls=4)
# thin gold rule
d.line([(W//2-220, 540), (W//2+220, 540)], fill=GOLD, width=2)
ctext(d, 565, "royalgoldcoco.com", font(DIDOT, 38), CREAM)
outro.save(PROJ/"stills/card_outro.png")
print("cards saved: card_intro.png, card_outro.png")
