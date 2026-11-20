#!/usr/bin/env python3
"""BLACKOUT trailer picture. Run: ~/AI/ComfyUI/venv/bin/python edit_blackout.py [h|v]
h = 1920x1080 master, v = 1080x1920 vertical. Writes final/blackout_picture_{h,v}.mp4 + final/timeline.json
All text is code-rendered (PIL). Audio is mixed by mix_blackout.py from timeline.json."""
import json, math, subprocess, sys
from pathlib import Path
import cv2, numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).resolve().parent
MODE = sys.argv[1] if len(sys.argv) > 1 else "h"
W, H = (1920, 1080) if MODE == "h" else (1080, 1920)
FPS = 24
FF = "/opt/homebrew/bin/ffmpeg"
VERT = MODE == "v"

def font(path, idx, size):
    return ImageFont.truetype(path, int(size), index=idx)
HELV = "/System/Library/Fonts/HelveticaNeue.ttc"
MENLO = "/System/Library/Fonts/Menlo.ttc"
def F(size, bold=False): return font(HELV, 1 if bold else 7, size)   # 7 = Light
def FM(size): return font(MENLO, 0, size)

# ---------------------------------------------------------------- segments (sequential)
SEG = []
def seg(name, dur, **kw):
    t0 = SEG[-1]["end"] if SEG else 0.0
    SEG.append(dict(name=name, start=round(t0, 3), end=round(t0 + dur, 3), dur=dur, **kw))
seg("card1", 4.6)
seg("b2a", 4.0, clip="b2a")
seg("b2b", 4.0, clip="b2b")
seg("b2c", 7.2, clip="b2c")
seg("card3", 3.8)
seg("b4a", 3.2, clip="b4a")
seg("b4b", 1.3, clip="b4b")
seg("scr_ask", 4.6)
seg("scr_reply", 5.8)
seg("a1", 3.6)
seg("card6", 4.2)
seg("u1", 3.4, clip="b7a")
seg("r1", 3.4, real="r1")
seg("r2", 3.0, real="r2")
seg("nar", 3.8, clip="b7b")
seg("sf", 3.2)
seg("rt", 5.4, clip="b7c")
seg("b8a", 3.6, clip="b8a")
seg("a2", 2.5)
seg("b9", 5.0, clip="b9")
seg("gap", 0.6)
seg("title", 8.4, clip="b10")
seg("still", 4.2)
TOTAL = SEG[-1]["end"]
S = {s["name"]: s for s in SEG}

# ---------------------------------------------------------------- sources
def load(path, size=None):
    cap = cv2.VideoCapture(str(path)); out = []
    while True:
        ok, f = cap.read()
        if not ok: break
        out.append(f)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    return out, fps
import os
CD = Path(os.environ.get("CLIPDIR", P / "clips"))
CLIPS = {k: load(CD / f"{k}.mp4")[0] for k in ["b2a","b2b","b2c","b4a","b4b","b7a","b7b","b7c","b8a","b9","b10"]}
REAL = {k: load(P / f"real/{k}.mp4")[0] for k in ("r1", "r2")}
AV = {}
for k in ("a1", "a2"):
    f = P / f"avatar/{k}.mp4"
    if f.exists(): AV[k] = load(f)

def cover(img, w, h, dx=0.5):
    ih, iw = img.shape[:2]; s = max(w / iw, h / ih)
    r = cv2.resize(img, (int(iw * s + .5), int(ih * s + .5)), interpolation=cv2.INTER_LANCZOS4)
    x0 = int((r.shape[1] - w) * dx); y0 = (r.shape[0] - h) // 2
    return r[y0:y0 + h, x0:x0 + w]

def fit(img, w, h, bg=(14, 12, 12)):
    ih, iw = img.shape[:2]; s = min(w / iw, h / ih)
    r = cv2.resize(img, (int(iw * s), int(ih * s)), interpolation=cv2.INTER_AREA)
    out = np.full((h, w, 3), bg, np.uint8)
    y0 = (h - r.shape[0]) // 2; x0 = (w - r.shape[1]) // 2
    out[y0:y0 + r.shape[0], x0:x0 + r.shape[1]] = r
    return out

def clip_frame(frames, lt, dur, fps=24):
    """local time lt in segment of length dur; stretch (slow) when the clip is shorter than dur, never beyond."""
    n = len(frames); src_len = n / fps
    speed = min(1.0, src_len / dur) if dur > src_len else 1.0
    pos = lt * speed * fps
    i = int(pos); a = min(i, n - 1); b = min(i + 1, n - 1); k = pos - i
    if a == b or k < 0.02: return frames[a]
    return cv2.addWeighted(frames[a], 1 - k, frames[b], k, 0)

# ---------------------------------------------------------------- look
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1 - 0.55 * (((xx - W / 2) / (W * .75)) ** 2 + ((yy - H / 2) / (H * .75)) ** 2), 0.3, 1)[..., None]
RNG = np.random.default_rng(5)
def finish(fr, grain=7.0):
    f = fr.astype(np.float32) * VIG
    f += RNG.normal(0, grain, f.shape[:2])[..., None]
    return np.clip(f, 0, 255).astype(np.uint8)

def tracked(s):  # letter-spaced caps for cards
    return " ".join(list(s)) if False else s

def draw_text_center(img, text, cy, size, color=(235, 232, 226), alpha=1.0, bold=False, maxw=0.88, track=0.0, glow=0):
    pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)); lay = Image.new("RGBA", pil.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    fs = size
    while True:
        fo = F(fs, bold)
        lines = [text]
        w_ = lambda s: d.textlength(s, font=fo) + track * fs * (len(s) - 1)
        if w_(text) > W * maxw:
            words = text.split(); a = ""; lines = []
            for wd in words:
                if a and w_(a + " " + wd) > W * maxw: lines.append(a); a = wd
                else: a = (a + " " + wd).strip()
            lines.append(a)
        if max(w_(l) for l in lines) <= W * maxw or fs < 20: break
        fs *= 0.93
    lh = fs * 1.25; y = cy - lh * (len(lines) - 1) / 2
    for l in lines:
        x = (W - w_(l)) / 2
        if glow:
            gl = Image.new("RGBA", pil.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(gl)
            for ch in l:
                gd.text((x, y - fs * .55), ch, font=fo, fill=(*color, int(160 * alpha)))
                x += d.textlength(ch, font=fo) + track * fs
            gl = gl.filter(ImageFilter_blur(glow)); lay = Image.alpha_composite(lay, gl); d = ImageDraw.Draw(lay)
            x = (W - w_(l)) / 2
        for ch in l:
            d.text((x, y - fs * .55), ch, font=fo, fill=(*color, int(255 * alpha)))
            x += d.textlength(ch, font=fo) + track * fs
        y += lh
    return cv2.cvtColor(np.array(Image.alpha_composite(pil.convert("RGBA"), lay).convert("RGB")), cv2.COLOR_RGB2BGR)

from PIL import ImageFilter
def ImageFilter_blur(r): return ImageFilter.GaussianBlur(r)

def fade(lt, a, b, fi=0.3, fo=0.3):
    """alpha for something visible from a to b."""
    if lt < a or lt > b: return 0.0
    return float(min(1, (lt - a) / fi, (b - lt) / fo))

def card(text, lt, a, b, size=None, track=0.12):
    img = np.zeros((H, W, 3), np.uint8)
    al = fade(lt, a, b)
    if al > 0:
        img = draw_text_center(img, text, H / 2, size or (W * (0.05 if not VERT else 0.075)), alpha=al, track=track)
    return img

# ---------------------------------------------------------------- code-rendered screens
AMBER = (120, 185, 245)   # BGR-ish placeholders are converted by draw_text (RGB below)
def screen_base(glow=0.9):
    """near-black laptop screen filling the frame with warm bloom from the middle."""
    d = np.sqrt(((xx - W / 2) / (W * .62)) ** 2 + ((yy - H * .48) / (H * .62)) ** 2)
    g = np.clip(1 - d, 0, 1) ** 1.6 * glow
    img = np.zeros((H, W, 3), np.float32)
    img[..., 0] = 10 + 22 * g; img[..., 1] = 14 + 55 * g; img[..., 2] = 18 + 105 * g
    return img.astype(np.uint8)

def wifi_off(img, cx, cy, r, col=(230, 200, 150), bad=(60, 60, 235)):
    for k, rr in enumerate((r, r * .66, r * .33)):
        cv2.ellipse(img, (int(cx), int(cy)), (int(rr), int(rr)), 0, 225, 315, col, max(3, int(r * .09)), cv2.LINE_AA)
    cv2.circle(img, (int(cx), int(cy)), max(3, int(r * .07)), col, -1, cv2.LINE_AA)
    cv2.line(img, (int(cx - r * .8), int(cy - r * .85)), (int(cx + r * .8), int(cy + r * .25)), bad, max(4, int(r * .12)), cv2.LINE_AA)
    return img

def chat_screen(lines, lt):
    """lines: list of (text, start_time, cps, rgb) ; text typed from start_time at cps chars/s. mono, left aligned, bottom-ish."""
    img = screen_base()
    wifi_off(img, W * (0.5 if VERT else 0.93), H * (0.07 if VERT else 0.10), H * (0.035 if VERT else 0.06))
    pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(pil)
    fs = W * (0.048 if VERT else 0.030); fo = FM(fs)
    x0 = W * (0.08 if VERT else 0.12); y = H * (0.36 if VERT else 0.34)
    last_visible = None
    for text, t0, cps, rgb in lines:
        if lt < t0: continue
        n = min(len(text), int((lt - t0) * cps) + 1)
        shown = text[:n]
        # wrap
        maxc = int((W - 2 * x0) / (fs * 0.6))
        wrapped = []
        cur = ""
        for wd in shown.split(" "):
            if len(cur) + len(wd) + 1 > maxc and cur: wrapped.append(cur); cur = wd
            else: cur = (cur + " " + wd).strip() if cur else wd
        wrapped.append(cur)
        for k, l in enumerate(wrapped):
            d.text((x0, y), l, font=fo, fill=rgb)
            last_visible = (x0 + d.textlength(l, font=fo), y)
            y += fs * 1.5
        y += fs * 0.8
    if last_visible and int(lt * 2) % 2 == 0:
        cx, cy = last_visible
        d.rectangle([cx + 4, cy + fs * .12, cx + 4 + fs * .5, cy + fs * 1.12], fill=(255, 215, 150))
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

def panel_msg(base, icon, text, al, sub=None):
    """centered dark dialog over a picture."""
    out = base.copy()
    pw, ph = (W * (0.82 if VERT else 0.46)), (H * (0.2 if VERT else 0.32))
    x0, y0 = int((W - pw) / 2), int((H - ph) / 2)
    ov = out.copy(); cv2.rectangle(ov, (x0, y0), (int(x0 + pw), int(y0 + ph)), (22, 20, 20), -1)
    cv2.rectangle(ov, (x0, y0), (int(x0 + pw), int(y0 + ph)), (90, 85, 80), 2)
    out = cv2.addWeighted(ov, 0.92 * al, out, 1 - 0.92 * al, 0)
    cx, cy = W / 2, y0 + ph * 0.32
    r = ph * 0.14
    if icon == "warn":
        pts = np.array([[cx, cy - r], [cx - r * 1.1, cy + r * .85], [cx + r * 1.1, cy + r * .85]], np.int32)
        cv2.polylines(out, [pts], True, (60, 170, 255), max(3, int(r * .18)), cv2.LINE_AA)
        cv2.line(out, (int(cx), int(cy - r * .35)), (int(cx), int(cy + r * .25)), (60, 170, 255), max(3, int(r * .16)), cv2.LINE_AA)
        cv2.circle(out, (int(cx), int(cy + r * .55)), max(2, int(r * .1)), (60, 170, 255), -1, cv2.LINE_AA)
    else:
        wifi_off(out, cx, cy + r * .5, r * 1.4)
    out = draw_text_center(out, text, y0 + ph * 0.72, W * (0.05 if VERT else 0.034), alpha=al, bold=True, maxw=0.8 if not VERT else 0.78)
    return out

def phone_inset(base, lt, a, b):
    al = fade(lt, a, b, 0.25, 0.25)
    if al <= 0: return base
    out = base.copy()
    ph = H * (0.62 if not VERT else 0.5); pw = ph * 0.48
    x0 = int(W * (0.5 if VERT else 0.22) - pw / 2); y0 = int(H * (0.55 if VERT else 0.5) - ph / 2)
    ov = out.copy()
    cv2.rectangle(ov, (x0 - 10, y0 - 10), (int(x0 + pw + 10), int(y0 + ph + 10)), (8, 8, 8), -1)
    cv2.rectangle(ov, (x0, y0), (int(x0 + pw), int(y0 + ph)), (26, 22, 20), -1)
    out = cv2.addWeighted(ov, al, out, 1 - al, 0)
    # screen contents
    cx = x0 + pw / 2
    wifi_off(out, cx, y0 + ph * 0.36, pw * 0.2)
    pil = Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(pil)
    fs = pw * 0.115; fo = F(fs, True)
    t = "Can't connect to server"
    # two lines
    for k, l in enumerate(("Can't connect", "to server")):
        w_ = d.textlength(l, font=fo)
        d.text((cx - w_ / 2, y0 + ph * (0.55 + 0.07 * k)), l, font=fo, fill=(int(235 * al + 30 * (1 - al)),) * 3)
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

# song forge waveform of the real score
_sc, _sr = sf.read(P / "music/cand1.wav"); _sc = _sc.mean(1) if _sc.ndim > 1 else _sc
def score_env(n=96):
    hop = len(_sc) // n
    e = np.array([np.sqrt((_sc[i * hop:(i + 1) * hop] ** 2).mean()) for i in range(n)]); return e / e.max()
ENV = score_env(96)
def songforge_frame(lt, dur):
    img = np.zeros((H, W, 3), np.uint8); img[:] = (16, 13, 12)
    n = 96; prog = min(1, lt / (dur - 0.4))
    bw = W * (0.84 if not VERT else 0.86) / n; x0 = W * (0.08 if not VERT else 0.07)
    base = H * 0.52; mx = H * (0.32 if not VERT else 0.18)
    for i in range(n):
        reveal = prog * n
        if i > reveal: continue
        grow = min(1, (reveal - i) / 6)
        h = max(2, ENV[i] ** 0.8 * mx * grow * (0.35 + 0.65 * (i / n) ** 0.7 + 0.12 * math.sin(lt * 9 + i)))
        c = (int(70 + 120 * i / n), int(150 + 60 * i / n), int(245))
        cv2.rectangle(img, (int(x0 + i * bw), int(base - h)), (int(x0 + i * bw + bw * .7), int(base + h)), c, -1)
    img = draw_text_center(img, "SONG FORGE", H * (0.2 if not VERT else 0.3), W * (0.04 if not VERT else 0.075), alpha=min(1, lt / .3), track=0.25)
    return img

def rings_overlay(fr, lt, dur):
    out = fr.copy(); ov = np.zeros_like(out)
    cx, cy = int(W * 0.5), int(H * 0.62)
    amp = 0.5 + 0.5 * abs(math.sin(lt * 7.3) * math.sin(lt * 2.9 + 1))
    for k in range(4):
        r = int((90 + 85 * ((lt * 1.1 + k * .25) % 1)) * (W / 1920 if not VERT else 0.6)); a = 1 - ((lt * 1.1 + k * .25) % 1)
        cv2.circle(ov, (cx, cy), r, (80, 170, 255), 4, cv2.LINE_AA)
        out = cv2.addWeighted(out, 1, (ov * a * amp * 0.6).astype(np.uint8), 1, 0); ov[:] = 0
    return out

# ---------------------------------------------------------------- per-frame picture
def seg_at(t):
    for s in SEG:
        if s["start"] <= t < s["end"]: return s
    return SEG[-1]

def render(t):
    s = seg_at(t); lt = t - s["start"]; n = s["name"]; fr = None; grain = 7.0
    if n == "card1":
        fr = card("NOVEMBER 14. 4:12 AM.", lt, 0.8, 4.5)
    elif n in ("b2a", "b2b"):
        fr = cover(clip_frame(CLIPS[s["clip"]], lt, s["dur"]), W, H)
    elif n == "b2c":
        fr = cover(clip_frame(CLIPS["b2c"], lt, s["dur"]), W, H)
        fr = (fr.astype(np.float32) * (0.55 if 0.2 < lt < 3.5 else 1)).astype(np.uint8) if False else fr
        fr = phone_inset(fr, lt, 0.1, 3.7)
        if 3.7 <= lt:
            al = fade(lt, 3.7, 7.2, 0.25, 0.25)
            fr = panel_msg(fr, "warn", "Something went wrong", al)
    elif n == "card3":
        fr = card("THE CLOUD IS GONE.", lt, 0.2, 3.7)
    elif n in ("b4a", "b4b", "u1", "nar", "rt", "b8a", "b9"):
        fr = cover(clip_frame(CLIPS[s["clip"]], lt, s["dur"]), W, H)
        if n == "u1":
            fr = panel_msg(fr, "warn", "Usage limit reached", fade(lt, 0.05, 3.4, 0.25, 0.25))
        if n == "nar": fr = rings_overlay(fr, lt, s["dur"]); fr = draw_text_center(fr, "NarrateClaude", H * 0.15, W * (0.03 if not VERT else 0.06), alpha=fade(lt, 0.2, 3.7, .3, .3), track=0.2)
        if n == "rt":
            labs = [("Flashlight.", 0.3, 0.30, 0.73), ("Radio.", 1.4, 0.55, 0.45), ("Door... open.", 2.4, 0.78, 0.30)]
            for txt, a_, px, py in labs:
                al = fade(lt, a_, 5.4, .2, .3)
                if al > 0:
                    if VERT: fr = draw_text_center(fr, txt, H * (0.2 + 0.06 * labs.index((txt, a_, px, py))), W * 0.07, alpha=al, color=(150, 215, 255))
                    else: fr = draw_text_center(fr, txt, H * (0.78 + 0.07 * 0) , W * 0.03, alpha=al, color=(150, 215, 255)) if False else draw_text_label(fr, txt, W * px, H * py, al)
    elif n == "scr_ask":
        fr = chat_screen([("> are you there?", 0.3, 12, (255, 214, 160))], lt)
    elif n == "scr_reply":
        fr = chat_screen([("> are you there?", -9, 12, (200, 170, 130)), ("I'm here. I run on this machine.", 0.2, 20, (255, 232, 190))], lt)
    elif n in ("a1", "a2"):
        fr = avatar_frame(n, lt, s["dur"])
    elif n == "card6":
        fr = card("ONE MACHINE. NO SIGNAL.", lt, 0.2, 4.1)
    elif n in ("r1", "r2"):
        fr = fit(clip_frame(REAL[n], lt, s["dur"]), W, H)
        lab = "REAL RUN, OFFLINE" if n == "r1" else "LOCAL MODEL"
        fr = fr if False else fr
        grain = 2.0
    elif n == "sf":
        fr = songforge_frame(lt, s["dur"])
    elif n == "gap":
        fr = np.zeros((H, W, 3), np.uint8)
    elif n == "title":
        fr = title_frame(lt, s)
    elif n == "still":
        fr = chat_screen([("> still here.", 0.0, 1, (0, 0, 0))], 0) if False else still_frame(lt)
    # transitions: dip to black at segment edges for scene changes (short)
    if n not in ("card1", "card3", "card6", "gap", "title"):
        pass
    out = finish(fr, grain)
    # flash on impact moments
    return out

def draw_text_label(fr, txt, cx, cy, al):
    size = W * (0.05 if VERT else 0.036)
    pil = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)); lay = Image.new("RGBA", pil.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    fo = F(size, True); tw = d.textlength(txt, font=fo); cx = min(cx, W - tw - 50)
    d.rounded_rectangle([cx - 20, cy - size * .35, cx + tw + 20, cy + size * 1.2], 10, fill=(10, 10, 10, int(170 * al)), outline=(150, 215, 255, int(220 * al)), width=2)
    d.text((cx, cy), txt, font=fo, fill=(150, 215, 255, int(255 * al)))
    return cv2.cvtColor(np.array(Image.alpha_composite(pil.convert("RGBA"), lay).convert("RGB")), cv2.COLOR_RGB2BGR)

def avatar_frame(n, lt, dur):
    out = np.zeros((H, W, 3), np.uint8); out[:] = (10, 8, 8)
    if n in AV:
        frames, fps = AV[n]
        idx = min(int(lt * fps), len(frames) - 1)
        a = frames[idx]
        if VERT: out = cover(a, W, H)
        else:
            ah = H; aw = int(a.shape[1] * ah / a.shape[0]); r = cv2.resize(a, (aw, ah))
            x0 = (W - aw) // 2; out[:, x0:x0 + aw] = r
            m = np.ones((H, W, 1), np.float32); edge = int(aw * .12)
            ramp = np.clip(np.minimum(xx - x0, x0 + aw - xx) / edge, 0, 1)[..., None]
            out = (out.astype(np.float32) * ramp).astype(np.uint8)
        # slow push
        z = 1 + 0.03 * lt / dur; M = cv2.getRotationMatrix2D((W / 2, H * .4), 0, z); out = cv2.warpAffine(out, M, (W, H))
    return out

def title_frame(lt, s):
    base = cover(clip_frame(CLIPS["b10"], min(lt, 3.0), 3.0), W, H)
    base = (base.astype(np.float32) * 0.55).astype(np.uint8)
    out = base
    if lt < 0.12: out = np.full((H, W, 3), 255, np.uint8)                        # slam flash
    scale = 1.0 + (0.18 * max(0, 1 - lt / 0.25))
    sh = int(6 * max(0, 1 - lt / 0.3))
    # title layer
    lay = np.zeros((H, W, 3), np.uint8)
    lay = draw_text_center(lay, "BLACKOUT", H * (0.42 if not VERT else 0.42), W * (0.11 if not VERT else 0.15), bold=True, track=0.06, color=(240, 236, 228), maxw=0.9)
    if scale != 1.0:
        M = cv2.getRotationMatrix2D((W / 2, H * 0.42), 0, scale); lay = cv2.warpAffine(lay, M, (W, H))
    if sh: lay = np.roll(lay, (np.random.default_rng(int(lt * 100)).integers(-sh, sh + 1), 0), axis=(0, 1)) if False else lay
    m = lay.max(2, keepdims=True) / 255.0
    out = (out.astype(np.float32) * (1 - m) + lay.astype(np.float32)).astype(np.uint8) if lt >= 0.12 else out
    al1 = fade(lt, 2.4, 8.4, .4, .5); al2 = fade(lt, 3.2, 8.4, .4, .4)
    if al1 > 0: out = draw_text_center(out, "Your AI doesn't need the cloud.", H * (0.58 if not VERT else 0.52), W * (0.032 if not VERT else 0.058), alpha=al1, track=0.04)
    if al2 > 0: out = draw_text_center(out, "Claude Code Local. Free and open source.", H * (0.67 if not VERT else 0.60), W * (0.024 if not VERT else 0.046), alpha=al2, color=(190, 205, 215), track=0.03)
    return out

def still_frame(lt):
    typed_at = 0.3
    return chat_screen([("Still here.", typed_at, 12, (255, 226, 180))], lt)

# ---------------------------------------------------------------- encode
if __name__ == "__main__":
    outp = P / f"final/blackout_picture_{MODE}.mp4"; outp.parent.mkdir(exist_ok=True)
    enc = subprocess.Popen([FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-crf", "15", "-preset", "medium", "-pix_fmt", "yuv420p", str(outp)], stdin=subprocess.PIPE)
    N = int(round(TOTAL * FPS))
    for i in range(N):
        t = i / FPS
        fr = render(t)
        # fade to black at the very end
        if t > TOTAL - 0.4: fr = (fr.astype(np.float32) * max(0, (TOTAL - t) / 0.4)).astype(np.uint8)
        enc.stdin.write(fr.tobytes())
    enc.stdin.close(); enc.wait()
    json.dump({"fps": FPS, "duration": TOTAL, "segments": SEG}, open(P / "final/timeline.json", "w"), indent=1)
    print("picture", MODE, N, "frames", TOTAL, "s")
