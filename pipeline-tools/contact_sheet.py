#!/usr/bin/env python3
"""contact_sheet.py — one frame per shot of a FINISHED composition, labelled, on one JPEG.

Every composition gets its own sheet (2026-11-02): the 16:9 film and the 9:16 vertical are different
pictures, so looking at one sheet says nothing about the other. Frames come from the rendered mp4
itself (titles, callouts and crops included), at the middle of each shot's window on the timeline.

Usage:
  contact_sheet.py VIDEO --edl projects/<film>/edl.json --out sheet.jpg [--plan final/vertical/plan.json]
  contact_sheet.py VIDEO --every 2.0 --out sheet.jpg          # no EDL: a frame every 2 s
With --plan, each tile carries its reframe verdict (static / pan / native / center / FLAGGED in red).
Exit 0 = written.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

FONT = "/System/Library/Fonts/Avenir Next.ttc"
TAG_COLORS = {"static": (45, 212, 191), "pan": (96, 165, 250), "native": (163, 230, 53),
              "center": (251, 191, 36), "flagged": (248, 113, 113), "": (148, 163, 184)}


def duration(f: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def make_sheet(video: Path, items: list, out: Path, title: str = "") -> Path:
    """items: [{"t": seconds, "label": str, "tag": verdict or ""}]"""
    from PIL import Image, ImageDraw, ImageFont
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", str(video)], capture_output=True, text=True)
    w, h = (int(x) for x in r.stdout.strip().split(",")[:2])
    vertical = h > w
    tw = 200 if vertical else 384
    th = round(tw * h / w)
    cols = 8 if vertical else 4
    rows = (len(items) + cols - 1) // cols
    pad, lab = 10, 46
    head = 54 if title else 0
    sheet = Image.new("RGB", (cols * (tw + pad) + pad, head + rows * (th + lab + pad) + pad), (12, 14, 18))
    d = ImageDraw.Draw(sheet)
    f_lab = ImageFont.truetype(FONT, 15, index=2)
    f_tag = ImageFont.truetype(FONT, 13, index=8)
    if title:
        d.text((pad, 14), title, font=ImageFont.truetype(FONT, 24, index=8), fill=(240, 240, 240))
    with tempfile.TemporaryDirectory() as td:
        for k, it in enumerate(items):
            p = Path(td) / f"{k:03d}.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0.0, it['t']):.3f}", "-i", str(video),
                            "-frames:v", "1", "-vf", f"scale={tw}:{th}", str(p)], capture_output=True)
            x = pad + (k % cols) * (tw + pad)
            y = head + pad + (k // cols) * (th + lab + pad)
            if p.exists():
                sheet.paste(Image.open(p).convert("RGB"), (x, y))
            tag = (it.get("tag") or "").lower()
            col = TAG_COLORS.get(tag, TAG_COLORS[""])
            if tag:
                d.rectangle([x, y, x + tw - 1, y + th - 1], outline=col, width=3)
                txt = tag.upper()
                l, t, r_, b = d.textbbox((0, 0), txt, font=f_tag)
                d.rectangle([x + 4, y + 4, x + 12 + r_ - l, y + 10 + b - t], fill=col)
                d.text((x + 8 - l, y + 7 - t), txt, font=f_tag, fill=(10, 10, 10))
            label = f"{it['t']:.1f}s  {it.get('label', '')}"
            while d.textbbox((0, 0), label, font=f_lab)[2] > tw and len(label) > 8:
                label = label[:-2]
            d.text((x, y + th + 5), label, font=f_lab, fill=(220, 220, 220))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=88)
    return out


def items_from_edl(edl: dict, plan: dict | None = None) -> list:
    by_cid = {p["cid"]: p for p in (plan or {}).get("shots", [])}
    out = []
    for k, s in enumerate(edl["shots"]):
        cid = s.get("cid", f"shot{k}")
        pl = by_cid.get(cid, {})
        out.append({"t": (float(s["rec_in"]) + float(s["rec_out"])) / 2, "label": cid, "tag": pl.get("verdict", "")})
    if edl.get("endcard"):
        ec = edl["endcard"]
        out.append({"t": float(ec["rec_in"]) + 1.2, "label": "end card", "tag": ""})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("video")
    ap.add_argument("--edl")
    ap.add_argument("--plan")
    ap.add_argument("--every", type=float, default=2.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="")
    a = ap.parse_args()
    v = Path(a.video)
    if a.edl:
        plan = json.loads(Path(a.plan).read_text()) if a.plan else None
        items = items_from_edl(json.loads(Path(a.edl).read_text()), plan)
    else:
        dur = duration(v)
        items = [{"t": t * a.every + a.every / 2, "label": ""} for t in range(int(dur / a.every))]
    make_sheet(v, items, Path(a.out), a.title)
    print(f"[contact_sheet] {a.out} ({len(items)} tiles)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
