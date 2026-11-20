#!/usr/bin/env python3
"""Composite plates (frozen rule 10 + rule 24): canon master cutouts (rembg u2net) welded onto a set plate,
which Z-Image img2img then relights/integrates. Run in the ComfyUI venv:
  ~/AI/ComfyUI/venv/bin/python tools/make_plates.py [rid ...]
Layout per render: (master, crop box as fractions of the cutout bbox (l,t,r,b), target height px, center x px,
bottom y px, mirror)."""
import sys
from pathlib import Path
from PIL import Image, ImageFilter
P = Path(__file__).resolve().parent.parent
W, H = 1248, 720
CUT = P / "canon/cutouts"; CUT.mkdir(parents=True, exist_ok=True)
OUT = P / "stills/plates"; OUT.mkdir(parents=True, exist_ok=True)

def cutout(name):
    f = CUT / f"{name}.png"
    if not f.exists():
        from rembg import remove, new_session
        im = remove(Image.open(P / f"canon/{name}.png").convert("RGB"), session=new_session("u2net"))
        im.crop(im.getbbox()).save(f)
    return Image.open(f).convert("RGBA")

def place(bg, name, crop, h, cx, by, mirror=False):
    im = cutout(name)
    w0, h0 = im.size
    l, t, r, b = crop
    im = im.crop((int(l * w0), int(t * h0), int(r * w0), int(b * h0)))
    if mirror: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    s = h / im.size[1]
    im = im.resize((max(1, int(im.size[0] * s)), int(h)), Image.LANCZOS)
    a = im.split()[3].filter(ImageFilter.GaussianBlur(1.2))
    im.putalpha(a)
    bg.paste(im, (int(cx - im.size[0] / 2), int(by - im.size[1])), im)

def plate(bgfile):
    return Image.open(P / bgfile).convert("RGBA").resize((W, H), Image.LANCZOS)

LAYOUTS = {
    # rid: (background, [(name, crop, height, cx, bottom, mirror), ...])  -- far subject first
    "R03_eye_contact": ("canon/set_forest.png", [("hank", (0, 0, 1, 0.62), 470, 900, 760, False),
                                                 ("doug", (0, 0, 1, 1), 380, 360, 735, None)]),
    "R15_bench": ("blender/renders/B16_bench.png", [("hank", (0, 0, 1, 0.6), 300, 654, 400, False),
                                                    ("doug", (0, 0, 1, 0.7), 175, 500, 400, None)]),
    "R18_hank_line": ("canon/set_canyon_gap.png", [("hank", (0, 0, 1, 0.62), 600, 560, 780, False)]),
    "R19_doug_line": ("canon/set_canyon_gap.png", [("doug", (0, 0, 1, 0.72), 760, 700, 820, False)]),
    "R29_doug_tense": ("canon/set_canyon_gap.png", [("doug", (0, 0, 1, 0.6), 900, 624, 960, False)]),
}
MIRROR = {}   # filled from canon/ORIENTATION.txt lines "name left|right" (which way the master faces)
of = P / "canon/ORIENTATION.txt"
if of.exists():
    for line in of.read_text().split("\n"):
        if line.strip(): n, d = line.split()[:2]; MIRROR[n] = d

for rid in (sys.argv[1:] or LAYOUTS):
    bgf, items = LAYOUTS[rid]
    bg = plate(bgf)
    for name, crop, h, cx, by, mirror in items:
        if mirror is None:   # face toward frame center: left subject should face right
            mirror = MIRROR.get(name, "right") == "left" if cx < W / 2 else MIRROR.get(name, "left") == "right"
        place(bg, name, crop, h, cx, by, mirror)
    bg.convert("RGB").save(OUT / f"{rid}.png")
    print("plate", rid)
