"""KSSN 8 NEWS graphics, drawn in code at 1080x1920 (bug, PARODY tag, breaking banner, lower thirds, ticker,
Nevada map with Lake Lahontan spreading from Pyramid Lake, EVACUATION ROUTE - UP card, end banner)."""
import math
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
SUP = "/System/Library/Fonts/Supplemental/"
F_DIN = SUP + "DIN Condensed Bold.ttf"
F_AB = SUP + "Arial Bold.ttf"
F_BLK = SUP + "Arial Black.ttf"
F_NAR = SUP + "Arial Narrow Bold.ttf"
RED = (206, 17, 38)
DRED = (140, 8, 22)
NAVY = (12, 28, 64)
BLUE = (20, 80, 170)
GOLD = (255, 196, 0)
WHITE = (255, 255, 255)

cl = lambda x, a=0.0, b=1.0: max(a, min(b, x))
def e_out(u): return 1 - (1 - cl(u)) ** 3
def e_io(u): u = cl(u); return 3 * u * u - 2 * u ** 3


@lru_cache(maxsize=128)
def font(path, px): return ImageFont.truetype(path, int(px))


def tw(d, s, f): b = d.textbbox((0, 0), s, font=f); return b[2] - b[0]


def bug(d, t):
    """station bug, top right: KSSN | 8 NEWS"""
    x1, y0 = W - 40, 70
    f1, f2 = font(F_BLK, 46), font(F_DIN, 50)
    a = tw(d, "KSSN", f1); b = tw(d, "8 NEWS", f2)
    x0 = x1 - (a + b + 70)
    d.rounded_rectangle([x0, y0, x1, y0 + 78], 10, fill=(255, 255, 255, 215))
    d.rounded_rectangle([x0 + a + 34, y0 + 6, x1 - 6, y0 + 72], 8, fill=BLUE + (255,))
    d.text((x0 + 16, y0 + 12), "KSSN", font=f1, fill=NAVY + (255,))
    d.text((x0 + a + 44, y0 + 14), "8 NEWS", font=f2, fill=WHITE + (255,))


def parody(d):
    f = font(F_AB, 30); s = "PARODY"; w = tw(d, s, f)
    d.rounded_rectangle([40, 80, 40 + w + 30, 80 + 52], 8, fill=(0, 0, 0, 150), outline=(255, 255, 255, 230), width=3)
    d.text((55, 88), s, font=f, fill=(255, 255, 255, 240))


def live(d, t, place):
    f = font(F_DIN, 46); y = 170
    d.rounded_rectangle([40, y, 150, y + 58], 6, fill=RED + (240,))
    if int(t * 1.5) % 2 == 0: d.ellipse([54, y + 20, 72, y + 38], fill=WHITE + (255,))
    d.text((80, y + 8), "LIVE", font=f, fill=WHITE + (255,))
    w = tw(d, place, f)
    d.rectangle([156, y, 156 + w + 30, y + 58], fill=(0, 0, 0, 160))
    d.text((171, y + 8), place, font=f, fill=WHITE + (255,))


TICK = ("LAKE LAHONTAN RETURNS  •  SILVER SPRINGS EXPECTED UNDER 400 FT OF WATER BY 3 PM TOMORROW  •  HIGHWAY 50 UNDER WATER EAST OF "
        "SILVER SPRINGS  •  OFFICIALS: MOVE VALUABLES TO SECOND FLOOR OR ROOF  •  FERNLEY AND DAYTON: WATERFRONT BY SUNDAY  •  "
        "DO NOT APPROACH PREHISTORIC FISH  •  SAGEBRUSH FLOATING SINCE NOON  •  ")


@lru_cache(maxsize=2)
def tick_strip():
    f = font(F_AB, 40); im = Image.new("RGBA", (1, 1)); d = ImageDraw.Draw(im)
    w = tw(d, TICK, f); s = Image.new("RGBA", (w, 70), (0, 0, 0, 0)); ImageDraw.Draw(s).text((0, 10), TICK, font=f, fill=WHITE + (255,))
    return s, w


def ticker(img, d, t, clock="5:01"):
    y = H - 170
    d.rectangle([0, y, W, y + 72], fill=NAVY + (235,))
    s, w = tick_strip(); x = -int((t * 170) % w)
    img.alpha_composite(s, (x, y + 1)); img.alpha_composite(s, (x + w, y + 1))
    d.rectangle([0, y, 190, y + 72], fill=RED + (255,))
    d.text((20, y + 12), "KSSN 8", font=font(F_DIN, 52), fill=WHITE + (255,))
    f = font(F_DIN, 50); d.rectangle([W - 150, y, W, y + 72], fill=(0, 0, 0, 255))
    d.text((W - 135, y + 12), clock, font=f, fill=WHITE + (255,))


def lower(d, t, t0, top, sub, red=True):
    """breaking-news lower third: red BREAKING tab + white headline bar + navy sub bar; slides in from left at t0."""
    u = e_out((t - t0) / 0.45); y = H - 470
    off = int((1 - u) * -W)
    if red:
        d.rectangle([40 + off, y, 360 + off, y + 64], fill=RED + (255,))
        d.text((58 + off, y + 6), "BREAKING NEWS", font=font(F_DIN, 56), fill=WHITE + (255,))
    d.rectangle([40 + off, y + 64, W - 40 + off, y + 170], fill=(250, 250, 250, 245))
    ft = font(F_BLK, 58)
    while tw(d, top, ft) > W - 130: ft = font(F_BLK, ft.size - 2)
    d.text((62 + off, y + 80), top, font=ft, fill=NAVY + (255,))
    d.rectangle([40 + off, y + 170, W - 40 + off, y + 232], fill=NAVY + (240,))
    fs = font(F_AB, 36)
    while tw(d, sub, fs) > W - 130: fs = font(F_AB, fs.size - 1)
    d.text((62 + off, y + 180), sub, font=fs, fill=WHITE + (255,))


def slam(img, d, t, t0=0.0):
    """cold open: full-width red BREAKING NEWS slab slams in with a flash"""
    u = cl((t - t0) / 0.35)
    if t < t0: return
    flash = max(0.0, 1 - (t - t0) / 0.25)
    if flash > 0: d.rectangle([0, 0, W, H], fill=(255, 255, 255, int(170 * flash)))
    sc = 1.6 - 0.6 * e_out(u)
    slab = Image.new("RGBA", (W, 520), (0, 0, 0, 0)); sd = ImageDraw.Draw(slab)
    sd.rectangle([0, 0, W, 520], fill=RED + (235,))
    for k in range(0, W, 60): sd.polygon([(k, 0), (k + 30, 0), (k - 20, 40), (k - 50, 40)], fill=DRED + (255,))
    for k in range(0, W, 60): sd.polygon([(k, 480), (k + 30, 480), (k - 20, 520), (k - 50, 520)], fill=DRED + (255,))
    f = font(F_BLK, 150); a = "BREAKING"; b = "NEWS"
    sd.text(((W - tw(sd, a, f)) // 2, 50), a, font=f, fill=WHITE + (255,))
    sd.text(((W - tw(sd, b, f)) // 2, 230), b, font=f, fill=GOLD + (255,))
    if sc != 1: slab = slab.resize((int(W * sc), int(520 * sc)), Image.BICUBIC)
    img.alpha_composite(slab, ((W - slab.width) // 2, (H - slab.height) // 2 - 120))
    if t - t0 > 0.5:
        f2 = font(F_DIN, 64); s = "EMERGENCY ALERT: SILVER SPRINGS, NV"
        d.rectangle([0, H // 2 + 200, W, H // 2 + 290], fill=(0, 0, 0, 200))
        d.text(((W - tw(d, s, f2)) // 2, H // 2 + 212), s, font=f2, fill=WHITE + (255,))


# ---------------- Nevada map ----------------
NV = [(42.0, -120.0), (42.0, -114.04), (36.2, -114.04), (36.1, -114.15), (36.02, -114.74), (35.5, -114.67), (35.0, -114.63),
      (35.0, -114.63), (39.0, -120.0)]
PLACES = {"PYRAMID LAKE": (40.03, -119.57), "RENO": (39.53, -119.81), "FALLON": (39.47, -118.78), "SILVER SPRINGS": (39.41, -119.22)}
LAT0, LAT1, LON0, LON1 = 34.6, 42.4, -120.6, -113.6
MX0, MY0, MX1, MY1 = 70, 330, 1010, 1430


def ll(lat, lon):
    x = MX0 + (lon - LON0) / (LON1 - LON0) * (MX1 - MX0)
    y = MY0 + (LAT1 - lat) / (LAT1 - LAT0) * (MY1 - MY0)
    return x, y


@lru_cache(maxsize=1)
def map_base():
    im = Image.new("RGBA", (W, H), (226, 214, 190, 255)); d = ImageDraw.Draw(im)
    rng = np.random.default_rng(7)
    for _ in range(140):  # faint terrain hatching
        x, y = rng.uniform(0, W), rng.uniform(MY0, MY1); r = rng.uniform(20, 70)
        d.ellipse([x - r, y - r * .4, x + r, y + r * .4], fill=(205, 190, 160, 90))
    poly = [ll(a, b) for a, b in NV]
    d.polygon(poly, fill=(196, 170, 126, 255), outline=(90, 70, 40, 255), width=5)
    # Pyramid Lake (existing) small blue body
    px, py = ll(40.03, -119.57); d.ellipse([px - 14, py - 34, px + 14, py + 34], fill=(40, 110, 200, 255))
    return im.filter(ImageFilter.GaussianBlur(0.6)), poly


def lake_mask(u):
    """Lahontan extent grown from Pyramid Lake: radius ramps with u, noisy edge, clipped to the NW basin."""
    base, poly = map_base()
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    cx, cy = ll(40.0, -119.4)
    R = 30 + 400 * e_io(u)
    pts = []
    for k in range(180):
        a = 2 * math.pi * k / 180
        n = 1 + .18 * math.sin(3 * a + 1) + .12 * math.sin(7 * a + 2.3) + .07 * math.sin(13 * a + .4)
        sx = 1.0 if math.cos(a) > 0 else 0.55        # spreads east toward Fallon, not into California
        pts.append((cx + R * n * math.cos(a) * sx, cy + R * n * math.sin(a) * 1.05))
    d.polygon(pts, fill=255)
    st = Image.new("L", (W, H), 0); ImageDraw.Draw(st).polygon(poly, fill=255)
    return Image.fromarray(np.minimum(np.array(m), np.array(st))).filter(ImageFilter.GaussianBlur(3))


def nv_map(t, dur):
    base, poly = map_base(); im = base.copy(); d = ImageDraw.Draw(im)
    u = cl((t - 0.4) / max(0.5, dur - 1.2))
    mk = lake_mask(u)
    water = Image.new("RGBA", (W, H), (30, 105, 205, 225))
    im.paste(water, (0, 0), mk)
    edge = mk.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(2))
    im.paste(Image.new("RGBA", (W, H), (170, 220, 255, 255)), (0, 0), edge)
    for name, (la, lo) in PLACES.items():
        x, y = ll(la, lo); hot = name == "SILVER SPRINGS"
        r = 13 if hot else 8
        if hot and int(t * 3) % 2 == 0: d.ellipse([x - 26, y - 26, x + 26, y + 26], outline=RED + (255,), width=5)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(RED if hot else (30, 30, 30)) + (255,), outline=WHITE + (255,), width=3)
        f = font(F_DIN, 46 if hot else 36)
        dx = {"RENO": -tw(d, "RENO", f) - 20, "DAYTON": -tw(d, "DAYTON", f) - 20, "PYRAMID LAKE": 24}.get(name, 22)
        dy = {"SILVER SPRINGS": 22, "PYRAMID LAKE": -60, "FALLON": -52}.get(name, -18)
        sx, sy = x + dx, y + dy
        d.text((sx + 2, sy + 2), name, font=f, fill=(0, 0, 0, 160)); d.text((sx, sy), name, font=f, fill=WHITE + (255,))
    f = font(F_DIN, 120); s = "NEVADA"; x, y = ll(37.6, -117.5)
    d.text((x - tw(d, s, f) // 2, y), s, font=f, fill=(120, 95, 60, 150))
    # header
    d.rectangle([0, 150, W, 300], fill=NAVY + (255,))
    d.text((50, 160), "LAKE LAHONTAN", font=font(F_BLK, 76), fill=WHITE + (255,))
    d.text((50, 245), "PROJECTED SHORELINE  •  BY 3 PM TOMORROW", font=font(F_DIN, 46), fill=GOLD + (255,))
    # legend
    d.rectangle([50, MY1 + 30, 100, MY1 + 70], fill=(30, 105, 205, 255)); d.text((115, MY1 + 28), "PREHISTORIC LAKE, RETURNING", font=font(F_DIN, 44), fill=NAVY + (255,))
    return im.convert("RGB")


def evac(t):
    """EVACUATION ROUTE - UP: green highway-style sign, the arrow points to the sky, blinks."""
    im = Image.new("RGBA", (W, H), (18, 22, 30, 255)); d = ImageDraw.Draw(im)
    for k in range(0, H, 6): d.line([(0, k), (W, k)], fill=(28, 34, 46, 255))
    u = e_out(t / 0.4); sc = 0.8 + 0.2 * u
    sw, sh = int(860 * sc), int(1260 * sc); x0, y0 = (W - sw) // 2, (H - sh) // 2 - 60
    d.rounded_rectangle([x0, y0, x0 + sw, y0 + sh], 40, fill=(0, 110, 60, 255), outline=WHITE + (255,), width=14)
    f = font(F_BLK, int(92 * sc))
    for i, s in enumerate(["EVACUATION", "ROUTE"]):
        d.text((W // 2 - tw(d, s, f) // 2, y0 + int((70 + i * 110) * sc)), s, font=f, fill=WHITE + (255,))
    on = (t % 0.8) < 0.55 or t < 0.8
    if on:
        cx = W // 2; top = y0 + int(330 * sc); bot = y0 + int(980 * sc); hw = int(210 * sc); sw2 = int(80 * sc)
        d.polygon([(cx, top), (cx + hw, top + hw), (cx + sw2, top + hw), (cx + sw2, bot), (cx - sw2, bot), (cx - sw2, top + hw), (cx - hw, top + hw)], fill=WHITE + (255,))
    f2 = font(F_BLK, int(190 * sc)); s = "UP"
    d.text((W // 2 - tw(d, s, f2) // 2, y0 + int(1010 * sc)), s, font=f2, fill=GOLD + (255,))
    return im.convert("RGB")


def end_banner(img, d, t, t0):
    if t < t0: return
    u = e_out((t - t0) / 0.5); y = int(H * 0.36)
    off = int((1 - u) * W)
    d.rectangle([0 + off, y, W + off, y + 330], fill=RED + (240,))
    d.rectangle([0 + off, y + 330, W + off, y + 420], fill=NAVY + (245,))
    f = font(F_BLK, 104)
    for i, s in enumerate(["LAKE LAHONTAN:", "THE RETURN"]):
        d.text((W // 2 - tw(d, s, f) // 2 + off, y + 25 + i * 140), s, font=f, fill=WHITE + (255,))
    f2 = font(F_DIN, 76); s = "— DAY 1 —"
    d.text((W // 2 - tw(d, s, f2) // 2 + off, y + 340), s, font=f2, fill=GOLD + (255,))
