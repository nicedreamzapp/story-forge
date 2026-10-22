#!/usr/bin/env python3
"""callout_check.py — does each callout arrow actually point at the part it names?

Promo stage 07_callouts (pipeline/formats/promo/SCHEMAS.md, callouts.json). A "Knee motor" label whose
arrow lands on the thigh strap teaches the viewer the wrong product. For every callout:
  1. the frame at the callout's midpoint is pulled from the rendered film
     (final/<film>.mp4), or — before a render exists — from the EDL source shot under that
     time, with a red dot drawn at the tip (declared as "simulated overlay" in the report);
  2. TIP VISIBLE: the tip lies inside the frame (2% margin) and the VL model, shown a crop
     around the tip, says an arrow tip / pointer / red dot is visible there;
  3. BLIND: on the same crop, "what part of the device is at the arrow tip / red dot?"
     with no label in the prompt (frozen rule 14) — saved;
  4. JUDGE: on the same crop, "does the marker sit on <part>?" yes/no, the blind answer given as
     context it may overrule (the blind answer is saved for the report).
Unreadable answers are UNCHECKED, never a pass (RULES 7).

Usage:
  ~/.local/mlx-server/bin/python pipeline-tools/callout_check.py projects/<film>
        [--film final/x.mp4 | --edl] [--votes 1]
Writes callout_report.json + callout_report.md. Exit 0 = every callout hits its part;
1 = a miss or unchecked; 2 = could not run (no callouts, no film/edl, Song Forge busy,
memory guard critical).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from design_check import Ballots, parse_yesno, run_with_vl  # noqa: E402

CROP = 0.32          # crop box = 32% of the frame's width/height, centred on the tip
# the rendered callouts are a white leader line ending in a teal dot (render_edl / Remotion); the
# simulated one is a red dot. Name both, or the judge says "a line ending in a circle, not an arrow".
VISIBLE_Q = ("Is there a pointer marker visible in this image: an arrow tip, a leader line ending in a dot "
             "or circle (any colour, e.g. teal), or a small red dot? Answer yes or no first, then one short reason.")
BLIND_Q = ("This is a close-up of a product or machine. A pointer marker (an arrow tip, a leader line ending in "
           "a coloured dot, or a small red dot; the marker itself is NOT part of the product) marks one spot near the "
           "CENTRE of the image. What part of the product, machine or person "
           "is directly under that marker? Answer in a few words (the part's name only).")
# 2026-10-22 (sitka_demo): "do both describe the same part?" made the judge answer about the two
# WORDINGS. It said "No. The marker is on a thin gold cable, which is a tendon cable" for a tip that
# sat on the tendon the label named, because the blind observer had called it a "joint connector".
# The judge now looks at the image itself; the blind answer is context it may overrule.
JUDGE_Q = ("This is a close-up with a marker near the centre. Look at the image yourself: does the marker "
           "sit on {part}? (A first observer called that spot \"{desc}\"; they may be wrong.) "
           "Answer yes or no first, then one short reason.")


def tip_at(tip, t: float):
    """tip is [x, y] or a list of [t, x, y] keyframes (linear interpolation)."""
    if tip and isinstance(tip[0], (int, float)):
        return float(tip[0]), float(tip[1])
    kf = sorted(tip, key=lambda k: k[0])
    if t <= kf[0][0]:
        return kf[0][1], kf[0][2]
    for a, b in zip(kf, kf[1:]):
        if a[0] <= t <= b[0]:
            f = (t - a[0]) / ((b[0] - a[0]) or 1)
            return a[1] + f * (b[1] - a[1]), a[2] + f * (b[2] - a[2])
    return kf[-1][1], kf[-1][2]


def grab(video: Path, t: float, out: Path) -> bool:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{max(0.0, t):.3f}", "-i", str(video),
                    "-frames:v", "1", str(out)], capture_output=True)
    return out.exists() and out.stat().st_size > 1000


def frame_from_edl(film: Path, edl: dict, t: float, out: Path):
    """Source frame under final-timeline time t, or None."""
    from PIL import Image
    for s in edl.get("shots", []):
        if s["rec_in"] <= t < s["rec_out"]:
            src = film / s["file"]
            st = s["src_in"] + (t - s["rec_in"]) * float(s.get("speed", 1.0) or 1.0)
            if src.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                Image.open(src).convert("RGB").save(out)
                return s["cid"]
            return s["cid"] if grab(src, st, out) else None
    return None


def draw_dot(img_path: Path, x: float, y: float) -> None:
    from PIL import Image, ImageDraw
    im = Image.open(img_path).convert("RGB")
    d = ImageDraw.Draw(im)
    r = max(6, im.width // 120)
    cx, cy = x * im.width, y * im.height
    d.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=(255, 30, 30), outline=(255, 255, 255), width=2)
    im.save(img_path)


def draw_ring(img_path: Path, x: float, y: float) -> None:
    """A hollow red ring AROUND the tip: the part under it stays visible (a filled dot, or the film's own
    teal dot, covers a thin part like a tendon cable; sitka_demo 2026-10-22)."""
    from PIL import Image, ImageDraw
    im = Image.open(img_path).convert("RGB")
    d = ImageDraw.Draw(im)
    r = max(14, im.width // 60)
    cx, cy = x * im.width, y * im.height
    d.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=(255, 30, 30), width=max(3, im.width // 480))
    im.save(img_path)


def crop_tip(img_path: Path, x: float, y: float, out: Path) -> Path:
    from PIL import Image
    im = Image.open(img_path).convert("RGB")
    W, H = im.size
    cw, ch = int(W * CROP), int(H * CROP)
    l = min(max(0, int(x * W - cw / 2)), W - cw)
    t = min(max(0, int(y * H - ch / 2)), H - ch)
    c = im.crop((l, t, l + cw, t + ch))
    c = c.resize((768, int(768 * ch / cw)), Image.LANCZOS)
    c.save(out)
    return out


def check(film: Path, video: Path | None, edl: dict | None, votes: int, B: Ballots, tmp: Path) -> list:
    co = json.loads((film / "callouts.json").read_text()).get("callouts", [])
    recs = []
    for c in co:
        a, b = float(c["rec_in"]), float(c["rec_out"])
        n = max(1, votes)
        ts = [(a + b) / 2] if n == 1 else [a + (b - a) * (0.2 + 0.6 * i / (n - 1)) for i in range(n)]
        rec = {"id": c["id"], "part": c.get("part"), "label": c.get("label"), "ballots": [],
               "verdict": "unchecked", "why": ""}
        hits, misses, unread, novis = 0, 0, 0, 0
        for t in ts:
            x, y = tip_at(c["tip"], t)
            bal = {"t": round(t, 2), "tip": [round(x, 3), round(y, 3)]}
            fr = tmp / f"{c['id']}_{t:07.2f}.png"
            if video is not None:
                ok, bal["from"] = grab(video, t, fr), "film"
            else:
                cid = frame_from_edl(film, edl, t, fr)
                ok, bal["from"] = cid is not None, f"edl:{cid} (simulated overlay: red dot drawn)"
                if ok:
                    draw_dot(fr, x, y)
            if not ok:
                bal.update(result="unchecked", why="no frame at this time")
                unread += 1
                rec["ballots"].append(bal)
                continue
            inside = 0.02 <= x <= 0.98 and 0.02 <= y <= 0.98
            crop = crop_tip(fr, x, y, tmp / f"{fr.stem}_crop.png")
            bal["visible_raw"] = B.ask(crop, VISIBLE_Q)
            vis = parse_yesno(bal["visible_raw"])
            # the PART is judged on the clean source frame with a hollow ring round the tip, so the
            # marker never hides what it points at; the rendered frame only proves the marker is there
            part_crop = crop
            if video is not None and edl is not None:
                clean = tmp / f"{c['id']}_{t:07.2f}_clean.png"
                if frame_from_edl(film, edl, t, clean):
                    draw_ring(clean, x, y)
                    part_crop = crop_tip(clean, x, y, tmp / f"{clean.stem}_crop.png")
                    bal["part_from"] = "clean source frame, hollow ring at the tip"
            bal["blind"] = B.ask(part_crop, BLIND_Q.replace("CENTRE", "CENTRE (inside the red ring)"))
            bal["judge_raw"] = B.ask(part_crop, JUDGE_Q.format(desc=bal["blind"][:200], part=c.get("part")))
            same = parse_yesno(bal["judge_raw"])
            if not inside or vis == "no":
                bal["result"], bal["why"] = "tip-not-visible", ("tip outside frame" if not inside
                                                                else "no marker seen at the tip")
                novis += 1
            elif same is None or vis is None:
                bal["result"] = "unchecked"
                unread += 1
            else:
                bal["result"] = "hit" if same == "yes" else "miss"
                hits += same == "yes"
                misses += same == "no"
            rec["ballots"].append(bal)
        k = len(ts)
        if misses * 2 > k:
            rec["verdict"], rec["why"] = "miss", f"tip is on '{rec['ballots'][0].get('blind', '')[:60]}', not {c.get('part')}"
        elif novis * 2 > k:
            rec["verdict"], rec["why"] = "miss", "arrow tip not visible"
        elif hits * 2 > k:
            rec["verdict"], rec["why"] = "pass", f"{hits}/{k} frames: tip on {c.get('part')}"
        else:
            rec["why"] = f"no majority ({hits} hit, {misses} miss, {novis} not visible, {unread} unread)"
        recs.append(rec)
        print(f"[{rec['verdict'].upper():9}] {c['id']}: {rec['why'][:140]}", flush=True)
    return recs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("film_dir")
    ap.add_argument("--film", default=None, help="rendered film (default final/<dirname>.mp4)")
    ap.add_argument("--edl", action="store_true", help="judge source frames via edl.json, dot simulated")
    ap.add_argument("--votes", type=int, default=1, help="frames per callout (1 = midpoint)")
    a = ap.parse_args()
    film = Path(a.film_dir).resolve()
    if not (film / "callouts.json").exists():
        print("[callout_check] no callouts.json", file=sys.stderr)
        return 2
    video = None if a.edl else (Path(a.film) if a.film else film / "final" / f"{film.name}.mp4")
    if video is not None and not video.is_absolute() and not video.exists():
        video = film / video   # a --film relative to the film folder
    edl = None
    if video is not None and not video.exists():
        print(f"[callout_check] no rendered film at {video} — falling back to edl.json (simulated dot)")
        video = None
    if (film / "edl.json").exists():   # with a film too: the part is judged on the clean source frame
        try:
            edl = json.loads((film / "edl.json").read_text())
        except Exception:                                     # noqa: BLE001
            edl = None
    if video is None and edl is None:
        try:
            edl = json.loads((film / "edl.json").read_text())
        except Exception as e:                               # noqa: BLE001
            print(f"[callout_check] no film and no readable edl.json ({e})", file=sys.stderr)
            return 2

    def body() -> int:
        B, tmp = Ballots(), Path(tempfile.mkdtemp(prefix="callout_check_"))
        recs = check(film, video, edl, a.votes, B, tmp)
        (film / "callout_report.json").write_text(json.dumps(
            {"ran": time.strftime("%Y-%m-%dT%H:%M:%S"), "from": str(video or "edl.json"),
             "callouts": recs}, indent=1))
        L = [f"# Callout check — {film.name}", "", f"_from {video or 'edl.json (simulated red dot)'}_", "",
             "| id | part | verdict | why |", "|---|---|---|---|"]
        L += [f"| {r['id']} | {r['part']} | **{r['verdict'].upper()}** | {r['why'][:150]} |" for r in recs]
        for r in recs:
            L += ["", f"## {r['id']} — {r['verdict'].upper()}"]
            for b in r["ballots"]:
                L.append(f"- t={b['t']} tip={b['tip']} {b.get('from', '')}: **{b.get('result')}** — "
                         f"visible: {b.get('visible_raw', '')[:80]} / blind: {b.get('blind', '')[:80]} / "
                         f"judge: {b.get('judge_raw', '')[:80]}")
        (film / "callout_report.md").write_text("\n".join(L) + "\n")
        print(f"[callout_check] VL calls {B.calls}, cache hits {B.hits} → callout_report.md")
        return 0 if all(r["verdict"] == "pass" for r in recs) else 1

    return run_with_vl("callout_check", body)


if __name__ == "__main__":
    sys.exit(main())
