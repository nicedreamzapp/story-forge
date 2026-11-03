#!/usr/bin/env python3
"""layouts.py — where text goes and how big it is, per composition (16:9 wide, 9:16 vertical).

WHY THIS EXISTS (2026-11-02): the 9:16 reel used to be the wide film padded onto a blurred copy of
itself, so every title and callout arrived at 56 % of its designed size, in a band across the middle,
fighting the platform's own buttons. A vertical is its own composition: bigger type relative to the
frame, fewer things on screen at once, a top-to-bottom hierarchy, and nothing inside the zones the
phone UI covers (status bar and header at the top, caption + CTA at the bottom, the action rail down
the right). This module is the one place those numbers live; render_edl.py and vertical_compose.py
read it, so the wide film keeps its exact Sitka-recipe sizes and the vertical gets its own.

Numbers are fractions of the frame unless they end in _px (pixels at the composition's own size).
"""
from __future__ import annotations

from dataclasses import dataclass, field

FONT = "/System/Library/Fonts/Avenir Next.ttc"   # index 8 = Heavy, 2 = Demi Bold


@dataclass
class Layout:
    W: int
    H: int
    vertical: bool
    safe: tuple = (0.0, 0.0, 1.0, 1.0)     # x0, y0, x1, y1: text never leaves this box
    title_px: int = 190
    title_y: float = 0.5                   # center of the title block
    callout_px: int = 44
    label_bands: tuple = ()                # vertical: y centers a callout label may sit at
    endcard: dict = field(default_factory=dict)
    bug_px: int = 37
    bug_at: tuple = (0.965, 0.045, "right")
    max_elements: int = 3                  # titles + callouts + overlays on screen at once

    @property
    def safe_px(self) -> tuple:
        x0, y0, x1, y1 = self.safe
        return x0 * self.W, y0 * self.H, x1 * self.W, y1 * self.H

    @property
    def safe_w(self) -> float:
        return (self.safe[2] - self.safe[0]) * self.W


def layout_for(W: int, H: int) -> Layout:
    if H <= W:
        # the wide film: exactly the sizes the Sitka promo shipped with (render_edl.py before 11/02)
        return Layout(W, H, False, safe=(0.035, 0.045, 0.965, 0.955), title_px=round(190 * H / 1080),
                      title_y=0.5, callout_px=round(44 * H / 1080),
                      endcard={"brand_px": round(230 * H / 1080), "brand_y": 0.40, "tag_px": round(58 * H / 1080),
                               "tag_y": 0.64, "url_px": round(38 * H / 1080), "url_y": 0.76},
                      bug_px=round(H * 0.034), bug_at=(0.965, 0.045, "right"), max_elements=3)
    # 9:16 (Reels / Shorts / TikTok). Safe box: top 12 % (status bar, header), bottom 22 % (caption, CTA),
    # left 6 %, right 12 % (like / comment / share rail). Type is sized to the frame WIDTH: a 1080-wide
    # vertical title is ~18 % of the width tall vs ~10 % on the wide film.
    s = W / 1080
    return Layout(W, H, True, safe=(0.06, 0.12, 0.88, 0.78), title_px=round(200 * s), title_y=0.34,
                  callout_px=round(58 * s), label_bands=(0.20, 0.70),
                  endcard={"brand_px": round(210 * s), "brand_y": 0.36, "tag_px": round(64 * s),
                           "tag_y": 0.50, "url_px": round(44 * s), "url_y": 0.60},
                  bug_px=round(W * 0.045), bug_at=(0.06, 0.125, "left"), max_elements=2)


def fit_font(draw, text: str, px: int, max_w: float, index: int = 8, min_px: int = 18):
    """The largest Avenir Next font <= px whose rendering of `text` fits max_w pixels."""
    from PIL import ImageFont
    size = px
    while True:
        f = ImageFont.truetype(FONT, size, index=index)
        l, t, r, b = draw.textbbox((0, 0), text, font=f)
        if r - l <= max_w or size <= min_px:
            return f
        size = max(min_px, int(size * 0.94))


def wrap(draw, text: str, font, max_w: float) -> list:
    """Greedy word wrap to max_w pixels."""
    lines, cur = [], ""
    for w in text.split():
        cand = (cur + " " + w).strip()
        l, t, r, b = draw.textbbox((0, 0), cand, font=font)
        if r - l <= max_w or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines
