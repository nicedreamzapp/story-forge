#!/usr/bin/env python3
"""finish_v3.py — the fix-pass cut (Matt 9:55 PM 11/17): straight cuts between real clips, no code paint effects.
Every beat is a clip trimmed to its real length; the flashback beats get a simple cool grade; the title fades in over J.
A short dissolve only where listed in XFADE. 1920x1080 24 fps, 60 s. Run in ~/chatterbox-env.
  finish_v3.py --out final/picture_v3.mp4
"""
from __future__ import annotations
import argparse, json, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
import paintlib as pl
from paintlib import PW, PH, OW, OH, FPS, ease

P = Path(__file__).resolve().parent.parent
# beat order, clip, planned seconds (the clip's real length caps it; the cut list is written from what is actually used)
PLAN = [("b00_goat", "clips/v3/A_goat.mp4", 4.0), ("b02_marmot", "clips/v3/B_marmot.mp4", 4.0), ("b03_bench", "clips/v3/C_bench.mp4", 4.0),
        ("b04_rollout", "clips/D_rollout_k6.mp4", 5.0), ("b05_airlift", "clips/previs/L_airlift.mp4", 4.0), ("b06_turtle", "clips/v3/E_turtle_r2.mp4", 4.0),
        ("b07_kitten", "clips/v3/F_kitten.mp4", 4.0), ("b08_otters", "clips/previs/M_otters.mp4", 4.0), ("b09_forest", "clips/v3/G_forest_r2.mp4", 5.0),
        ("b10_hi", "clips/previs/N_hi.mp4", 4.0), ("b11_ditch", "clips/v3/H_ditch.mp4", 3.0), ("b12_walkaway", "clips/v3/I_walkaway_r2.mp4", 4.0),
        ("b13_title", "clips/v3/J_title.mp4", 5.0), ("b14_button", "clips/v3/K_button_r2.mp4", 5.0)]
COOL = {"b09_forest", "b10_hi", "b11_ditch"}          # flashback: simple cool grade, nothing on top
XFADE = {"b09_forest": 0.5, "b12_walkaway": 0.4}        # dissolve INTO these beats (into the past, out of the ditch)
TITLE_IN = 1.0                                           # title fades in over the first second of b13 and holds


def clip_len(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip()
    return float(out or 0)


CUTS = []   # (id, path, start, dur)
def build_cuts():
    t = 0.0
    for bid, rel, want in PLAN:
        f = P / rel
        if not f.exists():
            print(f"  MISSING {rel} for {bid}; beat dropped from the cut", flush=True); continue
        d = min(want, clip_len(f))
        CUTS.append((bid, f, t, d)); t += d
    return t


FR = {}
def load():
    for bid, f, st, d in CUTS:
        FR[bid] = pl.load_clip(f)
    pl.title_layer()


def cool(fr):
    g = fr.mean(-1, keepdims=True)
    out = (fr * 0.75 + g * 0.25) * np.array([0.86, 0.93, 1.08], np.float32) * 0.92
    return np.clip(out, 0, 1).astype(np.float32)


def beat_frame(i, t_local):
    bid, f, st, d = CUTS[i]
    frs = FR[bid]; k = max(0, min(len(frs) - 1, int(round(t_local * 24))))
    fr = frs[k].astype(np.float32) / 255.0
    if bid in COOL: fr = cool(fr)
    if bid == "b11_ditch":   # the light goes out: a plain grade ramp over the last second (cooler, darker), nothing drawn on top
        u = ease((t_local - (d - 1.0)) / 0.8)
        fr = np.clip(fr * (1 - 0.35 * u) * np.array([1 - 0.12 * u, 1 - 0.05 * u, 1 + 0.04 * u], np.float32), 0, 1).astype(np.float32)
    if bid == "b13_title":
        col, a = pl.title_layer()
        aa = (a * ease(t_local / TITLE_IN))[..., None]
        sh = np.roll(aa, (6, 6), (0, 1)); fr = fr * (1 - 0.5 * sh)
        fr = fr * (1 - aa) + col * aa
    return fr


def render(t):
    for i, (bid, f, st, d) in enumerate(CUTS):
        if st <= t < st + d or (i == len(CUTS) - 1 and t >= st):
            fr = beat_frame(i, min(t - st, d - 1 / FPS))
            x = XFADE.get(bid, 0.0)
            if x and i > 0 and t - st < x:   # dissolve from the tail of the previous beat
                u = (t - st) / x; pb, pf, pst, pd = CUTS[i - 1]
                prev = beat_frame(i - 1, min(pd - 1 / FPS, pd - x + (t - st)))
                fr = prev * (1 - u) + fr * u
            return pl.view(fr, PW / 2, PH / 2, 1.0)
    return np.zeros((OH, OW, 3), np.float32)


def frame_u8(i):
    return (np.clip(render(i / FPS), 0, 1) * 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(P / "final/picture_v3.mp4")); ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    total = build_cuts(); load()
    json.dump({"cuts": [{"id": b, "clip": str(f.relative_to(P)), "start": round(st, 3), "dur": round(d, 3)} for b, f, st, d in CUTS], "total": round(total, 3),
               "xfade": XFADE, "cool_grade": sorted(COOL)}, open(P / "final/cuts_v3.json", "w"), indent=1)
    print(f"cut list: {len(CUTS)} beats, {total:.2f} s", flush=True)
    n = int(round(total * FPS))
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", a.out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE); t0 = time.time(); cv2.setNumThreads(2)
    with ThreadPoolExecutor(a.workers) as pool:
        for fr in pool.map(frame_u8, range(n)): ff.stdin.write(fr.tobytes())
    ff.stdin.close(); ff.wait(); print(f"picture -> {a.out} ({total:.2f} s) in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
