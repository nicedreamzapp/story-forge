#!/usr/bin/env python3
"""reference_analyze.py — turn a reference (a video, or a folder of stills) into a MEASURED style guide.

WHY THIS EXISTS (2026-11-02): "make it feel like this one" used to mean an agent describing a reference in
adjectives and then prompting from the adjectives. Motion-design practice is to break the reference down
into numbers before making anything: the actual palette (hex, share of the frame), how bright and how
contrasty, how saturated, how long the shots are and how the cutting rhythm moves, how much things move
inside a shot, how much text is on screen and where. Those numbers become the target the film is checked
against; the reference's content never enters the film (the DO NOT COPY section says what stays out).

Measures (all local: OpenCV + numpy + scikit-learn, Apple Vision for text):
  palette     k-means (k=6) on Lab pixels across the sampled frames -> hex + share, plus the mean a*/b* cast
  tone        L* mean / p5 / p50 / p95, contrast (L* std, p95-p5), clipped shadows/highlights
  saturation  HSV saturation mean / p90, colourfulness (Hasler-Suesstrunk)
  cuts        (video) a content detector on HSV histograms + frame difference -> shot list, average / median
              shot length, cuts per minute, rhythm (variation, trend of shot length across the piece)
  motion      (video) Farneback optical flow per shot, mean magnitude in frame-widths per second
  text        (Apple Vision text recognition, fast) share of frames with text, typical size and band
  vl          OPTIONAL: three frames described by the local VL model (typography, composition), only when the
              memory broker grants the room; a render may be running, so a refusal just skips it (--no-vl)
Writes  projects/<film>/reference/reference_analysis.json + reference_analysis.md + palette.png
and style_contract.py reads the json as the measured target (style_contract.py --reference).

Usage:
  ~/chatterbox-env/bin/python pipeline-tools/reference_analyze.py REF.mp4|REF_DIR projects/<film> [--no-vl]
        [--fps 2] [--max-frames 240] [--name label]
Exit 0 = written.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}


# ----------------------------------------------------------------------------- frames
def video_meta(f: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(f)],
                       capture_output=True, text=True)
    d = json.loads(r.stdout)
    s = d["streams"][0]
    n, dd = s["r_frame_rate"].split("/")
    return {"w": int(s["width"]), "h": int(s["height"]), "fps": float(n) / float(dd or 1),
            "dur": float(d["format"]["duration"])}


def read_video(f: Path, fps: float, width: int = 320):
    """Decode at `fps` scaled to `width` through an ffmpeg pipe -> (times, uint8 RGB frames)."""
    m = video_meta(f)
    h = int(round(width * m["h"] / m["w"] / 2)) * 2
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-vf", f"fps={fps},scale={width}:{h}",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    buf = np.frombuffer(p.stdout, np.uint8)
    n = buf.size // (width * h * 3)
    frames = buf[: n * width * h * 3].reshape(n, h, width, 3)
    return [k / fps for k in range(n)], frames, m


def read_images(d: Path, width: int = 320):
    from PIL import Image
    files = sorted(p for p in d.iterdir() if p.suffix.lower() in IMG_EXT)
    frames = []
    for p in files:
        im = Image.open(p).convert("RGB")
        im = im.resize((width, int(round(width * im.height / im.width))))
        frames.append(np.asarray(im))
    return files, frames


def strip_bars(frames: list) -> tuple:
    """Letterbox / pillarbox bars are the frame, not the look: rows and columns that stay black in nearly every
    sampled frame are cut off before measuring. Returns (frames, (top, bottom, left, right) px removed)."""
    st = np.stack([f.mean(axis=2) for f in frames[:: max(1, len(frames) // 60)]])
    dark = (st < 8).mean(axis=0)               # share of frames where each pixel is black
    rows, cols = dark.mean(axis=1) > 0.9, dark.mean(axis=0) > 0.9   # 0.9: a title or subtitle may sit in a bar
    def run(mask):
        n = 0
        for v in mask:
            if not v:
                break
            n += 1
        return n
    t, b = run(rows), run(rows[::-1])
    l, r = run(cols), run(cols[::-1])
    h, w = frames[0].shape[:2]
    if t + b >= h * 0.6 or l + r >= w * 0.6 or (t + b + l + r) == 0:
        return frames, (0, 0, 0, 0)
    return [f[t:h - b, l:w - r] for f in frames], (t, b, l, r)


# ----------------------------------------------------------------------------- colour + tone
def to_lab(rgb: np.ndarray) -> np.ndarray:
    import cv2
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32) * np.array([100 / 255, 1, 1], np.float32) \
        - np.array([0, 128, 128], np.float32)


def lab_to_hex(lab) -> str:
    import cv2
    px = np.array([[[lab[0] * 255 / 100, lab[1] + 128, lab[2] + 128]]], np.float32).clip(0, 255).astype(np.uint8)
    r, g, b = cv2.cvtColor(px, cv2.COLOR_LAB2RGB)[0, 0]
    return f"#{r:02x}{g:02x}{b:02x}"


def palette(frames: list, k: int = 6, seed: int = 0) -> list:
    from sklearn.cluster import KMeans
    rng = np.random.default_rng(seed)
    px = np.concatenate([to_lab(f).reshape(-1, 3) for f in frames])
    if len(px) > 120000:
        px = px[rng.choice(len(px), 120000, replace=False)]
    km = KMeans(n_clusters=k, n_init=4, random_state=seed).fit(px)
    counts = np.bincount(km.labels_, minlength=k) / len(px)
    out = [{"hex": lab_to_hex(c), "share": round(float(s), 4), "L": round(float(c[0]), 1), "a": round(float(c[1]), 1),
            "b": round(float(c[2]), 1)} for c, s in zip(km.cluster_centers_, counts)]
    return sorted(out, key=lambda x: -x["share"])


def tone_stats(frames: list) -> dict:
    import cv2
    L = np.concatenate([to_lab(f)[..., 0].ravel() for f in frames])
    labs = np.concatenate([to_lab(f).reshape(-1, 3)[::7] for f in frames])
    hsv = np.concatenate([cv2.cvtColor(f, cv2.COLOR_RGB2HSV)[..., 1].ravel() / 255 for f in frames])
    cf = []
    for f in frames:
        x = f.astype(np.float32)
        rg, yb = x[..., 0] - x[..., 1], 0.5 * (x[..., 0] + x[..., 1]) - x[..., 2]
        cf.append(float(np.sqrt(rg.std() ** 2 + yb.std() ** 2) + 0.3 * np.sqrt(rg.mean() ** 2 + yb.mean() ** 2)))
    p = np.percentile(L, [5, 50, 95])
    key = "low-key" if p[1] < 30 else "high-key" if p[1] > 65 else "mid-key"
    return {"L_mean": round(float(L.mean()), 1), "L_p5": round(float(p[0]), 1), "L_p50": round(float(p[1]), 1),
            "L_p95": round(float(p[2]), 1), "contrast_std": round(float(L.std()), 1),
            "contrast_range": round(float(p[2] - p[0]), 1), "crushed_blacks": round(float((L < 3).mean()), 4),
            "clipped_whites": round(float((L > 97).mean()), 4), "key": key,
            "sat_mean": round(float(hsv.mean()), 3), "sat_p90": round(float(np.percentile(hsv, 90)), 3),
            "colourfulness": round(float(np.mean(cf)), 1),
            "cast_a": round(float(labs[:, 1].mean()), 2), "cast_b": round(float(labs[:, 2].mean()), 2)}


# ----------------------------------------------------------------------------- cuts + motion
def detect_cuts(times: list, frames: np.ndarray, threshold: float = 0.42, min_shot: float = 0.15) -> list:
    """Hard cuts: HSV histogram distance + mean abs difference between consecutive frames, against an
    adaptive floor (so a fast-moving shot is not read as a cut every frame)."""
    import cv2
    hs, prev = [], None
    scores = [0.0]
    for f in frames:
        hsv = cv2.cvtColor(f, cv2.COLOR_RGB2HSV)
        h = cv2.calcHist([hsv], [0, 1, 2], None, [16, 8, 8], [0, 180, 0, 256, 0, 256])
        h = cv2.normalize(h, h).flatten()
        if prev is not None:
            hd = cv2.compareHist(prev[0], h, cv2.HISTCMP_BHATTACHARYYA)
            md = float(np.abs(f.astype(np.int16) - prev[1].astype(np.int16)).mean()) / 255
            scores.append(0.7 * hd + 0.3 * md * 3)
        prev = (h, f)
        hs.append(h)
    s = np.array(scores)
    cuts = []
    for k in range(1, len(s)):
        lo = np.median(s[max(1, k - 8):k + 8])
        if s[k] > threshold and s[k] > 2.5 * lo and (not cuts or times[k] - cuts[-1] >= min_shot):
            cuts.append(times[k])
    return cuts


def motion_per_shot(f: Path, shots: list, width: int = 192, fps: float = 6.0) -> list:
    """Farneback flow, mean magnitude in frame-widths per second, per shot."""
    import cv2
    times, frames, _ = read_video(f, fps, width)
    out = []
    for a, b in shots:
        idx = [k for k, t in enumerate(times) if a + 0.05 <= t <= b - 0.05]
        mags = []
        for i, j in zip(idx, idx[1:]):
            g0 = cv2.cvtColor(frames[i], cv2.COLOR_RGB2GRAY)
            g1 = cv2.cvtColor(frames[j], cv2.COLOR_RGB2GRAY)
            flow = cv2.calcOpticalFlowFarneback(g0, g1, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            mags.append(float(np.linalg.norm(flow, axis=2).mean()) / width * fps)
        out.append(round(float(np.mean(mags)), 4) if mags else None)
    return out


def rhythm(lengths: list) -> dict:
    if not lengths:
        return {}
    L = np.array(lengths)
    trend = float(np.polyfit(np.arange(len(L)), L, 1)[0]) if len(L) >= 3 else 0.0
    cv = float(L.std() / L.mean()) if L.mean() > 0 else 0.0
    feel = ("steady" if cv < 0.35 else "varied" if cv < 0.8 else "syncopated (long holds against bursts)")
    arc = "accelerating" if trend < -0.05 else "decelerating" if trend > 0.05 else "even"
    return {"avg": round(float(L.mean()), 2), "median": round(float(np.median(L)), 2), "min": round(float(L.min()), 2),
            "max": round(float(L.max()), 2), "cv": round(cv, 2), "trend_s_per_shot": round(trend, 3),
            "feel": feel, "arc": arc}


# ----------------------------------------------------------------------------- text + vl
def text_stats(frames: list, td: Path) -> dict:
    from PIL import Image
    import reframe
    pick = frames[:: max(1, len(frames) // 40)][:40]
    paths = []
    for k, f in enumerate(pick):
        p = td / f"txt_{k:03d}.png"
        Image.fromarray(f).resize((f.shape[1] * 2, f.shape[0] * 2)).save(p)
        paths.append(p)
    try:
        dets = reframe.probe(paths)
    except Exception as e:
        return {"error": f"text probe unavailable ({e})"}
    with_text, heights, bands, chars = 0, [], {"top": 0, "middle": 0, "bottom": 0}, []
    for d in dets:
        ts = [t for t in d.get("text", []) if len(t) >= 6 and t[5] >= 3]
        if ts:
            with_text += 1
        for t in ts:
            heights.append(t[3])
            chars.append(t[5])
            cy = t[1] + t[3] / 2
            bands["top" if cy < 0.33 else "middle" if cy < 0.66 else "bottom"] += 1
    n = max(1, len(dets))
    return {"frames_checked": len(dets), "share_with_text": round(with_text / n, 3),
            "median_text_height": round(float(np.median(heights)), 4) if heights else None,
            "median_chars_per_line": int(np.median(chars)) if chars else None, "bands": bands}


def vl_describe(frames: list, td: Path) -> dict:
    """Ask the local VL model about typography and composition on three frames, ONLY with a memory lease."""
    try:
        sys.path.insert(0, str(Path.home() / "SongForgeM5"))
        from mem_client import acquire_ex, release
    except Exception as e:
        return {"skipped": f"memory broker unavailable ({type(e).__name__}); not loading the VL model blind"}
    lid, status, _ = acquire_ex("storyforge reference-vl", 22, timeout=20, ttl=900)
    if status != "granted":
        return {"skipped": f"memory broker said '{status}' (a render or Song Forge job holds the room)"}
    from PIL import Image
    q = ("You are a motion designer analysing ONE frame of a reference video. Do not describe the story or "
         "people. In short labelled lines: TYPE: typeface style, weight, case, size relative to the frame, where "
         "it sits. COMPOSITION: subject placement, negative space, framing (wide/medium/close), symmetry. "
         "GRAPHICS: any UI panels, lines, shapes, their style. If there is no text, say TYPE: none.")
    out = []
    try:
        for k, f in enumerate([frames[len(frames) // 6], frames[len(frames) // 2], frames[(5 * len(frames)) // 6]]):
            p = td / f"vl_{k}.png"
            Image.fromarray(f).resize((f.shape[1] * 3, f.shape[0] * 3)).save(p)
            r = subprocess.run([str(Path.home() / ".local/mlx-server/bin/python"), str(HERE / "vl_ask_cli.py"), str(p), q],
                               capture_output=True, text=True, timeout=600)
            out.append(r.stdout.strip() or f"(no answer: {r.stderr.strip()[-160:]})")
    finally:
        release(lid)
    return {"readings": out}


# ----------------------------------------------------------------------------- main
def measured_paragraph(a: dict) -> str:
    """The measured target in prompt-pasteable words (look only; the edit numbers live in the json)."""
    pal = ", ".join(f"{p['hex']} ({p['share']:.0%})" for p in a["palette"][:5])
    t = a["tone"]
    cast = ("warm" if t["cast_b"] > 4 else "cool" if t["cast_b"] < -4 else "neutral") + \
        (", magenta-leaning" if t["cast_a"] > 4 else ", green-leaning" if t["cast_a"] < -4 else "")
    sat = "muted" if t["sat_mean"] < 0.22 else "rich" if t["sat_mean"] > 0.45 else "moderate"
    return (f"Palette anchored on {pal}; a {cast} cast. {t['key'].capitalize()} exposure (L* median {t['L_p50']}, "
            f"shadows {t['L_p5']}, highlights {t['L_p95']}), contrast spread {t['contrast_range']} L* with "
            f"{'crushed' if t['crushed_blacks'] > 0.02 else 'open'} blacks and "
            f"{'clipped' if t['clipped_whites'] > 0.02 else 'held'} highlights; {sat} saturation "
            f"(mean {t['sat_mean']:.2f}).")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ref")
    ap.add_argument("project")
    ap.add_argument("--fps", type=float, default=2.0, help="sampling rate for palette/tone/text")
    ap.add_argument("--max-frames", type=int, default=240)
    ap.add_argument("--no-vl", action="store_true")
    ap.add_argument("--name", default=None)
    a = ap.parse_args()
    ref, proj = Path(a.ref).resolve(), Path(a.project).resolve()
    out_dir = proj / "reference"
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    res = {"reference": str(ref), "name": a.name or ref.stem, "analysed": time.strftime("%Y-%m-%d %H:%M")}
    with tempfile.TemporaryDirectory() as tds:
        td = Path(tds)
        if ref.is_dir():
            files, frames = read_images(ref)
            res.update(kind="stills", count=len(files))
            if not frames:
                print("[reference] no images in the folder", file=sys.stderr)
                return 2
        else:
            times, fr, meta = read_video(ref, a.fps)
            frames = list(fr)
            if len(frames) > a.max_frames:
                step = len(frames) / a.max_frames
                frames = [frames[int(k * step)] for k in range(a.max_frames)]
            res.update(kind="video", **{k: round(v, 3) if isinstance(v, float) else v for k, v in meta.items()})
            # cuts at a denser rate than the palette sampling
            ctimes, cfr, _ = read_video(ref, 12.0, 160)
            cuts = detect_cuts(ctimes, cfr)
            bounds = [0.0] + cuts + [meta["dur"]]
            shots = [(a_, b_) for a_, b_ in zip(bounds, bounds[1:]) if b_ - a_ > 0.05]
            lens = [b_ - a_ for a_, b_ in shots]
            mot = motion_per_shot(ref, shots)
            res["cuts"] = {"count": len(cuts), "per_minute": round(len(cuts) / max(1e-6, meta["dur"]) * 60, 1),
                           "times": [round(c, 3) for c in cuts], "rhythm": rhythm(lens)}
            res["shots"] = [{"start": round(s[0], 3), "end": round(s[1], 3), "len": round(s[1] - s[0], 3), "motion": m}
                            for s, m in zip(shots, mot)]
            mv = [m for m in mot if m is not None]
            if mv:
                res["motion"] = {"mean": round(float(np.mean(mv)), 4), "p90": round(float(np.percentile(mv, 90)), 4),
                                 "calm_share": round(float(np.mean(np.array(mv) < 0.03)), 3),
                                 "unit": "frame-widths per second (optical flow)"}
        frames, bars = strip_bars(frames)
        if any(bars):
            res["bars_removed"] = {"top_bottom_frac": round((bars[0] + bars[1]) / (frames[0].shape[0] + bars[0] + bars[1]), 3),
                                   "left_right_frac": round((bars[2] + bars[3]) / (frames[0].shape[1] + bars[2] + bars[3]), 3)}
        print(f"[reference] {len(frames)} frames sampled" + (f", letterbox bars removed {bars}" if any(bars) else ""),
              flush=True)
        res["palette"] = palette(frames)
        res["tone"] = tone_stats(frames)
        res["text"] = text_stats(frames, td)
        res["vl"] = {"skipped": "--no-vl"} if a.no_vl else vl_describe(frames, td)
    res["measured_target"] = measured_paragraph(res)
    (out_dir / "reference_analysis.json").write_text(json.dumps(res, indent=1))
    # swatch
    from PIL import Image, ImageDraw, ImageFont
    sw = Image.new("RGB", (900, 160), (12, 14, 18))
    d = ImageDraw.Draw(sw)
    f_ = ImageFont.truetype("/System/Library/Fonts/Avenir Next.ttc", 18, index=2)
    x = 0
    for p in res["palette"]:
        w = max(40, int(900 * p["share"]))
        d.rectangle([x, 0, x + w, 120], fill=p["hex"])
        d.text((x + 6, 130), f"{p['hex']} {p['share']:.0%}", font=f_, fill=(230, 230, 230))
        x += w
    sw.save(out_dir / "palette.png")
    write_md(res, out_dir / "reference_analysis.md")
    print(f"[reference] {out_dir.relative_to(proj)}/reference_analysis.md + .json + palette.png "
          f"({time.time() - t0:.0f}s)")
    print(res["measured_target"])
    return 0


def write_md(r: dict, out: Path) -> None:
    t = r["tone"]
    L = [f"# Reference breakdown: {r['name']}", "",
         f"Measured {r['analysed']} from `{r['reference']}` ({r['kind']}"
         + (f", {r['w']}x{r['h']}, {r['dur']:.1f} s" if r["kind"] == "video" else f", {r['count']} images") + ").",
         "These are measurements, not impressions. They are the TARGET the film is checked against "
         "(`style_contract.py --reference` pastes the measured look into the contract).", "",
         "## Measured target (the look, prompt-ready)", "", r["measured_target"], "",
         "## Palette (k-means in Lab, share of all sampled pixels)", "", "| Hex | Share | L* | a* | b* |", "|---|---|---|---|---|"]
    L += [f"| `{p['hex']}` | {p['share']:.1%} | {p['L']} | {p['a']} | {p['b']} |" for p in r["palette"]]
    L += ["", "## Tone", "",
          f"- L* mean {t['L_mean']}, p5 {t['L_p5']}, median {t['L_p50']}, p95 {t['L_p95']} ({t['key']})",
          f"- contrast: L* std {t['contrast_std']}, p95-p5 range {t['contrast_range']}; crushed blacks "
          f"{t['crushed_blacks']:.1%}, clipped whites {t['clipped_whites']:.1%}",
          f"- saturation mean {t['sat_mean']}, p90 {t['sat_p90']}; colourfulness {t['colourfulness']}",
          f"- cast: a* {t['cast_a']}, b* {t['cast_b']} (positive b* = warm)"]
    if r.get("cuts"):
        c, rh = r["cuts"], r["cuts"]["rhythm"]
        L += ["", "## Cutting", "",
              f"- {c['count']} cuts, {c['per_minute']} per minute; shots average {rh.get('avg')} s "
              f"(median {rh.get('median')}, {rh.get('min')}-{rh.get('max')} s)",
              f"- rhythm: {rh.get('feel')} (variation {rh.get('cv')}), {rh.get('arc')} "
              f"({rh.get('trend_s_per_shot'):+} s per shot across the piece)"]
    if r.get("motion"):
        m = r["motion"]
        L += ["", "## Motion inside shots", "",
              f"- optical flow mean {m['mean']} frame-widths/s, p90 {m['p90']}; {m['calm_share']:.0%} of shots near still",
              "", "| Shot | Start | Length | Motion |", "|---|---|---|---|"]
        L += [f"| {k + 1} | {s['start']:.2f} | {s['len']:.2f} | {s['motion']} |" for k, s in enumerate(r["shots"][:60])]
    tx = r.get("text", {})
    if tx and not tx.get("error"):
        L += ["", "## Text on screen", "",
              f"- {tx['share_with_text']:.0%} of {tx['frames_checked']} checked frames carry text; median line height "
              f"{tx['median_text_height']} of the frame, ~{tx['median_chars_per_line']} characters per line; "
              f"bands {tx['bands']}"]
    vl = r.get("vl", {})
    L += ["", "## Typography and composition (local VL model)", ""]
    L += ([f"- {x}" for x in vl["readings"]] if vl.get("readings") else [f"Skipped: {vl.get('skipped')}"])
    L += ["", "## DO NOT COPY", "",
          "We take the NUMBERS above (palette ratios, tone, rhythm, motion energy, how much text and where). "
          "We never take the reference's content:",
          "- no shot, composition, camera move or edit reproduced beat for beat",
          "- no character, creature, product design, logo, mascot or set from it",
          "- none of its words: titles, taglines, captions, lyrics (the text probe stores sizes and counts, never strings)",
          "- no footage, frames, music or sound from it in the film, not even as a placeholder",
          "- no exact typeface clone of a custom or licensed brand face; match weight, case and scale with our own fonts",
          "- never name the reference in a prompt (\"in the style of <title/studio>\"); prompts get the measured target only"]
    out.write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    sys.exit(main())
