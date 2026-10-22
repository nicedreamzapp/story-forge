#!/usr/bin/env python3
"""promo_deliver.py — promo stage 10 prep: the thumbnail and youtube.json next to the final mp4.

Nothing is uploaded here (publishing waits for Matt's OK, then stages/10_deliver/published.md).
  * final/thumbnail.png, 1280x720: the CLEAN source frame of the shot under the title slam + 0.8 s
    (else the middle of line 1), graded down on the left, the brand in big type and promo.json youtube.thumb_text
    (default: the end card tagline) under it.
  * final/youtube.json: title, description, tags, category, language, made_for_kids false, files
    (the Sitka youtube.json shape). Title/description/tags come from promo.json "youtube"; the
    description gets the script's lines appended when promo.json leaves it empty.
Usage:  ~/chatterbox-env/bin/python pipeline-tools/promo_deliver.py projects/<film>
Exit 0 = both written; 2 = no final mp4.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from promo_common import load_promo, parse_script, run  # noqa: E402

FONT = "/System/Library/Fonts/Avenir Next.ttc"


def main() -> int:
    film = Path(sys.argv[1]).resolve()
    cfg = load_promo(film)
    mp4 = film / "final" / f"{film.name}.mp4"
    if not mp4.exists():
        print(f"[deliver] no {mp4.relative_to(film)}", file=sys.stderr)
        return 2
    edl = json.loads((film / "edl.json").read_text())
    words = json.loads((film / "vo" / "words.json").read_text())
    t = (edl["titles"][0]["rec_in"] + 0.8) if edl.get("titles") else \
        (words["lines"][0]["start"] + words["lines"][0]["end"]) / 2
    raw = film / "final" / "_thumb_src.png"
    # the CLEAN source frame of the shot under t (the cut itself has the title, bug and callouts burned in,
    # and the first thumbnail stacked a second SITKA over the slam's own)
    sh = next((x for x in edl["shots"] if x["rec_in"] <= t < x["rec_out"]), edl["shots"][0])
    src_t = float(sh["src_in"]) + (t - float(sh["rec_in"]))
    if sh.get("kind") == "image":
        run(["ffmpeg", "-v", "error", "-y", "-i", film / sh["file"], "-frames:v", "1",
             "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720", raw])
    else:
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{src_t:.3f}", "-i", film / sh["file"], "-frames:v", "1",
             "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720", raw])
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    im = Image.open(raw).convert("RGBA")
    W, H = im.size
    grad = Image.new("L", (W, 1))
    for x in range(W):
        grad.putpixel((x, 0), int(200 * max(0.0, 1 - x / (W * 0.62))))
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    shade.putalpha(grad.resize((W, H)))
    im = Image.alpha_composite(im, shade)
    d = ImageDraw.Draw(im)
    brand = cfg.get("brand") or cfg["endcard"].get("title") or film.name
    sub = cfg["youtube"].get("thumb_text") or cfg["endcard"].get("tagline") or ""
    fb = ImageFont.truetype(FONT, 170, index=8)
    fs = ImageFont.truetype(FONT, 56, index=2)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((64, 196), brand, font=fb, fill=(0, 0, 0, 200))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(im)
    d.text((60, 190), brand, font=fb, fill=(255, 255, 255, 255))
    l, tp, r, b = d.textbbox((60, 190), brand, font=fb)
    d.rectangle([62, b + 18, 62 + (r - l) * 0.55, b + 28], fill=(251, 191, 36, 255))
    if sub:
        d.text((62, b + 48), sub, font=fs, fill=(255, 255, 255, 240))
    thumb = film / "final" / "thumbnail.png"
    im.convert("RGB").save(thumb)
    raw.unlink()
    yt = cfg["youtube"]
    desc = yt.get("description") or "\n\n".join(ln["text"] for ln in parse_script(film / "script.md"))
    meta = {"title": yt.get("title") or cfg.get("title") or brand, "description": desc, "tags": yt.get("tags", []),
            "category": yt.get("category", "Science & Technology"), "language": "en", "made_for_kids": False,
            "files": {"video": mp4.name, "thumbnail": thumb.name}}
    (film / "final" / "youtube.json").write_text(json.dumps(meta, indent=1))
    print(f"[deliver] final/thumbnail.png (frame at {t:.2f}s) + final/youtube.json ('{meta['title'][:60]}')")
    return 0


if __name__ == "__main__":
    sys.exit(main())
