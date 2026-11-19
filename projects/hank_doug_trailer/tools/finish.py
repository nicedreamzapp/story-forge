#!/usr/bin/env python3
"""finish.py — render the one-canvas trailer picture (silent) as a pure function of time, 1920x1080 24 fps.
Timeline per script_v2.md beats 0-14. Stills + clips are the only model work; everything else is paintlib.
  finish.py --out final/picture.mp4 [--t0 0 --t1 60] [--preview 4]   (preview = render every Nth frame to a grid)
Point coordinates (mouths, noses, feet) live in tools/points.json in 1344x768 still pixels.
"""
from __future__ import annotations
import argparse, json, math, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
import paintlib as pl
from paintlib import PW, PH, OW, OH, FPS, ease, lerp

P = Path(__file__).resolve().parent.parent
PTS = json.load(open(P / "tools/points.json"))
CLIPS = json.load(open(P / "tools/clips.json"))      # beat -> clip path (the select)


def pp(name):
    """still-pixel point -> plate coords (1344x768 centre-cropped to 16:9 then scaled to the plate)."""
    x, y = PTS[name]
    return (x * PW / 1344.0, (y - 6) * PH / 756.0)


# ----------------------------------------------------------------------------- assets (loaded once, shared by fork)
A = {}
def load():
    for k, f in {"A": "A_ledge_goat", "B": "B_marmot", "C": "C_bench", "E": "E_turtle", "F": "F_drain", "G": "G_forest",
                 "H1": "H1_ditch", "H2": "H2_lantern", "I": "I_walkaway", "J": "J_title_hill"}.items():
        A[k] = pl.load_plate(P / f"stills/{f}.png")
    A["Ag"] = pl.unpainted(A["A"]); A["Bg"] = pl.unpainted(A["B"]); A["Cg"] = pl.unpainted(A["C"]); A["Fg"] = pl.unpainted(A["F"])
    A["Iold"] = pl.old_paint(A["I"]); A["H1old"] = pl.old_paint(A["H1"], 0.85)
    A["lantern"] = pl.cutout(A["H2"])
    xc = P / "stills/X_chipmunk.png"
    A["chipmunk"] = pl.cutout(pl.load_plate(xc)) if xc.exists() else None
    for k in ("D", "L", "E", "M", "N", "K"):
        f = P / CLIPS[k]
        A["clip_" + k] = pl.load_clip(f) if f.exists() else []
        if not A["clip_" + k]:
            print(f"  WARNING clip {k} missing ({f}); its beat renders from the still", flush=True)
            still = {"D": "D_rollout", "L": "L_airlift", "E": "E_turtle", "M": "M_otters", "N": "N_nose", "K": "K_sleeping"}[k]
            sp = P / f"stills/{still}.png"
            A["clip_" + k] = [(pl.load_plate(sp) * 255).astype(np.uint8)] if sp.exists() else [(pl.linen() * 255).astype(np.uint8)]
    pl.linen(); pl.brush(); pl.craquelure(); pl.edge_noise(); pl.title_layer()


def clip_frame(k, t_local, fps_src=24.0):
    fr = A["clip_" + k]
    i = int(round(t_local * fps_src)); i = max(0, min(len(fr) - 1, i))
    return fr[i].astype(np.float32) / 255.0


C0 = (PW / 2, PH / 2, 1.0)   # rest view: centre, zoom 1 (1920x1080 window of the 2304x1296 plate)


def sview(plate, cx=PW / 2, cy=PH / 2, z=1.0):
    return pl.view(plate, cx, cy, z)


# ----------------------------------------------------------------------------- beats
def render(t: float) -> np.ndarray:
    # ---- 0 THE LINEN 0-3 : pencil goat on linen, bleat ring paints the mountain
    if t < 3.6:
        gm = pp("A_goat_mouth")
        r = (t - 0.9) * 950.0
        fr = pl.ring_reveal(A["Ag"], A["A"], gm[0], gm[1], r, width=46)
        fr = pl.pebbles(fr, [(gm[0] - 60 + i * 30, gm[1] + 120) for i in range(4)], t, 1.3)
        cy = PH / 2 + 380 * ease((t - 3.0) / 0.6) if t > 3.0 else PH / 2
        return sview(fr, cy=cy)
    # ---- 1 ripple runs down the mountain 3-6 : whip A->B, colour front arrives at the marmot
    if t < 4.4:
        u = (t - 3.6) / 0.8
        gm = pp("A_goat_mouth")
        fa = pl.ring_reveal(A["Ag"], A["A"], gm[0], gm[1], (t - 0.9) * 950.0, width=46)
        fb = pl.ring_reveal(A["Bg"], A["B"], PW / 2, -2600, 0, width=0, strength=0)   # B still grey
        return pl.whip(fa, fb, u, (PW / 2, PH / 2 + 380, 1.0), (PW / 2, PH / 2, 1.0), axis="y", sign=1)
    if t < 6.0:
        mm = pp("B_marmot_mouth")
        r = 2600 + (t - 4.4) * 1100.0          # front descends from the top, reaches the marmot ~5.3
        fr = pl.ring_reveal(A["Bg"], A["B"], PW / 2, -2600, r, width=60, feather=40)
        return sview(fr)
    # ---- 2 THE WHISTLE 6-9 : two big rings, whip B->C
    if t < 7.4:
        mm = pp("B_marmot_mouth")
        fr = A["B"]
        fr = pl.ring_reveal(fr, fr, mm[0], mm[1], (t - 6.3) * 1500.0, width=80, strength=1.2)
        fr = pl.ring_reveal(fr, fr, mm[0], mm[1], (t - 6.8) * 1500.0, width=80, strength=1.2)
        z = lerp(1.0, 1.15, ease((t - 6.0) / 1.2))
        return sview(fr, cx=lerp(PW / 2, mm[0], ease((t - 6.0) / 1.2)), cy=lerp(PH / 2, mm[1] + 120, ease((t - 6.0) / 1.2)), z=z)
    if t < 8.2:
        u = (t - 7.4) / 0.8
        mm = pp("B_marmot_mouth")
        fa = pl.ring_reveal(A["B"], A["B"], mm[0], mm[1], (t - 6.3) * 1500.0, width=80, strength=1.2)
        fb = A["Cg"]
        return pl.whip(fa, fb, u, (mm[0], mm[1] + 120, 1.15), (PW / 2, PH / 2, 1.0), axis="x", sign=1)
    # ---- 3 THE BENCH 9-13 : the rings arrive, paint floods the wagon, push in on paw + reins
    if t < 13.0:
        r = (t - 8.2) * 1700.0
        fr = pl.ring_reveal(A["Cg"], A["C"], -600, PH * 0.3, r, width=70, feather=50)
        fr2 = pl.ring_reveal(fr, fr, -600, PH * 0.3, r - 420, width=70, strength=0.9)
        paw = pp("C_paw")
        e = ease((t - 10.0) / 3.0)
        return sview(fr2, cx=lerp(PW / 2, paw[0], e), cy=lerp(PH / 2, paw[1], e), z=lerp(1.0, 1.28, e))
    # ---- 4 ROLLOUT 13-18 : clip D, the world paints in just ahead of the horse's nose (leading edge)
    if t < 17.5:
        tl = t - 13.0
        fr = clip_frame("D", tl)
        # leading edge dropped on this beat (2026-11-17): the horse's nose sits at the frame edge in every D render, so "the world
        # ahead of the nose" is outside the frame; the wet edge lives on beat 12 instead. Listed in known_defects.md.
        return sview(fr)
    if t < 18.2:   # tilt up into the airlift: the goose flock crossing the top of the tilt is the join
        u = (t - 17.5) / 0.7
        fa = clip_frame("D", 4.5); fb = clip_frame("L", 0.0)
        return pl.whip(fa, fb, u, C0, C0, axis="y", sign=-1)
    # ---- 5 GOAT AIRLIFT 18-22 : clip L
    if t < 21.6:
        return sview(clip_frame("L", t - 18.2))
    if t < 22.2:   # down off the mountain onto the pond
        u = (t - 21.6) / 0.6
        return pl.whip(clip_frame("L", 3.4), A["E"], u, C0, C0, axis="y", sign=1)
    # ---- 6 TURTLE 22-27 : hold 1.5 s, then clip E (trunks spray), wet strokes hang in the air, spray fills frame = join
    if t < 23.5:
        return sview(A["E"])
    if t < 27.0:
        tl = t - 23.5
        fr = clip_frame("E", tl)
        tp = pp("E_turtle")
        # the LTX clip paints its own water arcs; the code arc strokes were doubling them, so they are off (2026-11-17)
        if tl > 3.0:   # the second spray fills the frame
            w = ease((tl - 3.0) / 0.5)
            fr = fr * (1 - 0.6 * w) + np.array([0.80, 0.86, 0.92], np.float32) * 0.6 * w
        return sview(fr)
    # ---- 7 KITTEN 27-30 : the tiniest ring, from the bottom of a drain
    if t < 30.0:
        km = pp("F_kitten_mouth")
        w = 1 - ease((t - 27.0) / 0.5)
        r = (t - 27.8) * 420.0
        fr = pl.ring_reveal(A["Fg"], A["F"], km[0], km[1], r, width=14, feather=70, wobble=40, strength=1.3)
        if w > 0: fr = fr * (1 - 0.6 * w) + np.array([0.80, 0.86, 0.92], np.float32) * 0.6 * w
        e = ease((t - 27.5) / 2.5)
        return sview(fr, cx=lerp(PW / 2, km[0], e), cy=lerp(PH / 2, km[1], e), z=lerp(1.0, 1.25, e))
    # ---- 8 OTTER CHAIN 30-34 : clip M, then a dark trunk wipes the frame = join into the old paint
    if t < 34.2:
        tl = t - 30.0
        fr = clip_frame("M", min(tl, 3.9))
        cx = PW / 2 + 160 * ease((tl - 3.0) / 1.0)
        out = sview(fr, cx=cx)
        if t >= 33.4:
            out = pl.trunk_wipe(out, (t - 33.4) / 0.8)
        return out
    # ---- 9 THE OLD PAINT 34-39 : the same road, older, cracked, cold; push along Doug's trail
    if t < 39.0:
        amt = ease((t - 34.2) / 1.3)
        fr = pl.old_paint(A["G"], amt)
        log = pp("G_log")
        e = ease((t - 34.2) / 4.8)
        out = sview(fr, cx=lerp(PW / 2, log[0], e), cy=lerp(PH / 2, log[1], e), z=lerp(1.0, 1.2, e))
        if t < 34.2 + 0.8:
            out = pl.trunk_wipe(out, (t - 33.4) / 0.8)
        return out
    # ---- 10 "HI." 39-43 : talk clip N, colour blooms from the two noses, cracks heal
    if t < 43.0:
        tl = t - 39.0
        fr = clip_frame("N", tl)
        old = pl.old_paint(fr, 1.0)
        n1, n2 = pp("N_nose_doug"), pp("N_nose_hank")
        cx, cy = (n1[0] + n2[0]) / 2, (n1[1] + n2[1]) / 2
        r = (t - 41.3) * 900.0
        fr2 = pl.reveal_only(old, fr, cx, cy, r, feather=90, wobble=70)
        if 0 < t - 41.3 < 0.6:   # one warm flash as the colour arrives
            fr2 = fr2 + 0.12 * (1 - (t - 41.3) / 0.6) * np.array([1.0, 0.8, 0.5], np.float32)
        return sview(np.clip(fr2, 0, 1))
    # ---- 11 THE DITCH 43-46 : drift right off the pair, the lantern tumbles in, splash, the light goes out
    if t < 43.6:
        u = (t - 43.0) / 0.6
        fa = clip_frame("N", 3.9)
        return pl.whip(fa, A["H1"], u, C0, C0, axis="x", sign=1)
    if t < 46.0:
        tl = t - 43.6
        glow = 1.0 if tl < 1.35 else max(0.0, 1 - (tl - 1.35) / 0.5)
        base = A["H1"] * np.array([1.0 + 0.07 * glow, 1.0 + 0.02 * glow, 1.0 - 0.06 * glow], np.float32)
        base = np.clip(base + 0.02 * glow, 0, 1)
        fr = base
        land = pp("H1_land")
        sp, al = A["lantern"]
        if tl < 1.2:
            u = tl / 1.2
            x = lerp(PW + 200, land[0], u); y = land[1] - 1100 * (1 - u) * (1 - u) - 80 * u * (1 - u) * 4 + 0
            y = land[1] - (1100 * (1 - u) ** 2)
            ang = -40 + 400 * u
            fr = pl.paste(fr, sp, al, x, y, 0.42, ang, tint=(1.0, 1.0, 1.0))
        else:
            k = int((tl - 1.2) * FPS)
            fr = pl.paste(fr, sp, al, land[0], land[1] + 30, 0.42, 95, tint=(0.55 + 0.45 * glow,) * 3)
            fr = pl.splash(fr, land[0], land[1], k)
        return sview(fr)
    # ---- 12 WALKING AWAY 46-49 : pull back and rise, fresh colour runs up the road ahead of their feet
    if t < 48.8:
        tl = t - 46.0
        feet = pp("I_feet")
        r = tl * 1000.0
        fr = pl.reveal_only(A["Iold"], A["I"], feet[0], feet[1], r, feather=120, wobble=90)
        e = ease(tl / 2.8)
        return sview(fr, cx=PW / 2, cy=lerp(feet[1] - 120, PH / 2 - 60, e), z=lerp(1.25, 1.0, e))
    if t < 49.2:   # the rise clears the last trees onto the sunset
        u = (t - 48.8) / 0.4
        return pl.whip(A["I"], A["J"], u, (PW / 2, PH / 2 - 60, 1.0), C0, axis="y", sign=-1)
    # ---- 13 TITLE 49-54 : the title paints itself in, stroke by stroke
    if t < 53.7:
        tl = t - 49.2
        fr = A["J"]
        fr = pl.title_reveal(fr, min(1.0, (t - 49.0) / 1.2))
        return sview(fr, cy=PH / 2 - 40 * ease(tl / 2.0))
    if t < 54.2:   # down the hill to under the oak
        u = (t - 53.7) / 0.5
        fa = pl.title_reveal(A["J"], 1.0)
        return pl.whip(fa, clip_frame("K", 0.0), u, (PW / 2, PH / 2 - 40, 1.0), C0, axis="y", sign=1)
    # ---- 14 BUTTON 54-60 : clip K, the chipmunk's tiny ring, "Rolling." with eyes shut, cut to black
    if t < 60.0:
        tl = t - 54.2
        fr = clip_frame("K", min(tl, 5.95))
        cm = pp("K_chipmunk_mouth")
        if A["chipmunk"] is not None and t >= 56.6:
            sp, al = A["chipmunk"]
            pop = ease((t - 56.6) / 0.3)
            fr = pl.paste(fr, sp, al, cm[0] + 40, cm[1] + 20 + 90 * (1 - pop), 0.24 * (0.6 + 0.4 * pop), 0)
        fr = pl.ring_reveal(fr, fr, cm[0], cm[1], (t - 57.0) * 260.0, width=10, feather=10, wobble=6, strength=1.3) if t > 57.0 and t < 58.2 else fr
        return sview(fr)
    return np.zeros((OH, OW, 3), np.float32)


def frame_u8(i):
    t = i / FPS
    f = render(t)
    return (np.clip(f, 0, 1) * 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(P / "final/picture.mp4"))
    ap.add_argument("--t0", type=float, default=0.0); ap.add_argument("--t1", type=float, default=60.0)
    ap.add_argument("--preview", type=int, default=0, help="write a contact grid of every Nth second instead of a video")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    t0 = time.time(); load(); print(f"assets loaded in {time.time()-t0:.0f}s", flush=True)
    if a.preview:
        ts = list(np.arange(a.t0, a.t1, a.preview))
        tiles = [cv2.resize(frame_u8(int(t * FPS)), (480, 270)) for t in ts]
        cols = 5; rows = math.ceil(len(tiles) / cols)
        grid = np.zeros((rows * 290, cols * 480, 3), np.uint8)
        for k, tile in enumerate(tiles):
            r, c = divmod(k, cols); grid[r * 290:r * 290 + 270, c * 480:(c + 1) * 480] = tile
            cv2.putText(grid, f"{ts[k]:.0f}s", (c * 480 + 6, r * 290 + 286), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.imwrite(a.out, cv2.cvtColor(grid, cv2.COLOR_RGB2BGR)); print("preview ->", a.out); return
    i0, i1 = int(a.t0 * FPS), int(a.t1 * FPS)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", a.out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    cv2.setNumThreads(2)
    with ThreadPoolExecutor(a.workers) as pool:   # cv2/numpy release the GIL; fork hangs under macOS Accelerate threads
        for k, fr in enumerate(pool.map(frame_u8, range(i0, i1))):
            ff.stdin.write(fr.tobytes())
            if k % 120 == 0: print(f"  frame {i0+k} ({(i0+k)/FPS:.1f}s) {time.time()-t0:.0f}s", flush=True)
    ff.stdin.close(); ff.wait()
    print(f"picture -> {a.out} in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
