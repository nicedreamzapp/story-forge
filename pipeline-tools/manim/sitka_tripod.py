#!/usr/bin/env python3
"""sitka_tripod.py — the sit-balance diagram as an ALPHA clip for the promo edit.

WHY THIS EXISTS (promo format, 2026-10-22): line 6 of the Sitka promo ("each side stands on
three points... your weight lands inside that triangle, with almost a foot of room behind
you") is a physics claim. A CAD orbit with a dot on it didn't explain it. A clean diagram
does: side view of a seated figure, the three ground points per side, the support triangle on
the ground, the center of mass dropping a plumb line that lands INSIDE the triangle, and the
margin to the rear edge dimensioned. Rendered with transparency (ProRes 4444 .mov) so
Remotion/ffmpeg can lay it over footage or a dark card.

GENERIC ON PURPOSE: the Sitka design is still changing (backrest, modular hub, 10/22), so
every number is an argument. Ground points are plan-view (x forward, y sideways) in inches;
heights are inches above the ground. The margin label defaults to the measured distance from
the CoM's ground point back to the rear foot, unless --margin-text overrides it.
The drawing is a diagram, not a physics proof: the physics check comes first (memory note
"Physics check BEFORE CAD"); this only illustrates numbers someone already verified.

Usage (Manim CE lives in ~/manim-env, never the system python):
  ~/manim-env/bin/python pipeline-tools/manim/sitka_tripod.py --out /tmp/tripod.mov
      [--heel 0,0] [--toe 9,2] [--rear -22,5] [--com -11,2.5,24]
      [--hip -14,20] [--knee 2,20] [--margin-text "almost a foot of room behind you"]
      [--fps 30] [--size 1920x1080] [--secs 9] [--opaque] [--preview-png /tmp/f.png]
Exit 0 = rendered (and the plumb point is inside the triangle); 1 = rendered but the CoM
lands OUTSIDE the triangle (the diagram would show a fall; check the numbers); 2 = could not
render. NEVER treat 2 as a pass.
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

WHITE = "#F5F7FA"
TEAL = "#2DD4BF"
AMBER = "#FBBF24"
GREY = "#94A3B8"
RED = "#F87171"


def pair(s):
    return tuple(float(v) for v in s.split(","))


def inside(p, tri):
    (x, y), (a, b, c) = p, tri

    def s(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
    d1, d2, d3 = s((x, y), a, b), s((x, y), b, c), s((x, y), c, a)
    neg = d1 < 0 or d2 < 0 or d3 < 0
    pos = d1 > 0 or d2 > 0 or d3 > 0
    return not (neg and pos)


def build_scene(a):
    from manim import (DOWN, LEFT, RIGHT, UP, Arrow, Circle, Create, Dot, DoubleArrow, FadeIn,
                       Flash, GrowFromCenter, Line, Polygon, Scene, Text, VGroup, Write)

    heel, toe, rear = pair(a.heel), pair(a.toe), pair(a.rear)
    cx, cy, ch = pair(a.com)
    hip, knee = pair(a.hip), pair(a.knee)
    xs = [heel[0], toe[0], rear[0], hip[0], knee[0], cx]
    S = a.scale
    mid_x = (min(xs) + max(xs)) / 2
    k_dx, k_dy = 0.55, 0.65  # oblique depth: plan-y pushes right and up

    def P(x, y=0.0, h=0.0):
        """inches (forward, sideways, up) -> scene point, ground near the bottom of frame"""
        return [(x - mid_x + k_dx * y) * S, (h + k_dy * y) * S - 2.3, 0]

    class Tripod(Scene):
        def construct(self):
            ground = Line(P(min(xs) - 10), P(max(xs) + 10), color=GREY, stroke_width=3)
            # seated figure (side view, facing right)
            ankle = (heel[0] + 1.0, 3.5)
            shoulder = (hip[0] + 2.5, hip[1] + 22)
            head_c = (shoulder[0] + 0.8, shoulder[1] + 6.5)
            elbow = (shoulder[0] + 6, shoulder[1] - 10)
            hand = (knee[0] - 5, hip[1] + 3)
            rear_top = (hip[0] + 0.45 * (knee[0] - hip[0]), hip[1] - 1)
            body = VGroup(
                Line(P(hip[0], 0, hip[1]), P(*shoulder[:1], 0, shoulder[1]), color=WHITE, stroke_width=7),
                Circle(radius=3.6 * S, color=WHITE, stroke_width=6).move_to(P(head_c[0], 0, head_c[1])),
                Line(P(shoulder[0], 0, shoulder[1]), P(elbow[0], 0, elbow[1]), color=WHITE, stroke_width=6),
                Line(P(elbow[0], 0, elbow[1]), P(hand[0], 0, hand[1]), color=WHITE, stroke_width=6),
                Line(P(hip[0], 0, hip[1]), P(knee[0], 0, knee[1]), color=WHITE, stroke_width=7),
                Line(P(knee[0], 0, knee[1]), P(ankle[0], 0, ankle[1]), color=WHITE, stroke_width=7),
                Line(P(heel[0], heel[1]), P(toe[0], toe[1]), color=WHITE, stroke_width=7),
                Line(P(ankle[0], 0, ankle[1]), P(heel[0], heel[1]), color=WHITE, stroke_width=6),
            )
            strut = Line(P(rear_top[0], 0, rear_top[1]), P(rear[0], rear[1]), color=TEAL, stroke_width=7)
            self.play(Create(ground), run_time=0.5)
            self.play(Create(body), run_time=1.2)
            self.play(Create(strut), run_time=0.6)

            # the three ground points, one at a time
            pts = [("Heel", heel), ("Toes", toe), ("Rear foot", rear)]
            dots = []
            for name, (x, y) in pts:
                d = Dot(P(x, y), radius=0.09, color=TEAL)
                lab = Text(name, font="Avenir Next", weight="SEMIBOLD", font_size=26, color=WHITE)
                lab.next_to(d, LEFT if name == "Rear foot" else DOWN, buff=0.18)
                self.play(GrowFromCenter(d), FadeIn(lab, shift=0.1 * UP), run_time=0.35)
                dots.append(d)
            tri = Polygon(P(*heel), P(*toe), P(*rear), color=TEAL, stroke_width=4,
                          fill_color=TEAL, fill_opacity=0.28)
            self.play(Create(tri), run_time=0.8)

            # center of mass + plumb line
            com = Dot(P(cx, cy, ch), radius=0.13, color=AMBER)
            com_lab = Text("center of mass", font="Avenir Next", weight="SEMIBOLD", font_size=26, color=AMBER)
            com_lab.next_to(com, LEFT, buff=0.2)
            self.play(GrowFromCenter(com), FadeIn(com_lab), run_time=0.5)
            ok = inside((cx, cy), (heel, toe, rear))
            land = P(cx, cy)
            plumb = Line(com.get_center(), land, color=AMBER, stroke_width=4)
            self.play(Create(plumb), run_time=0.7)
            hit = Dot(land, radius=0.1, color=AMBER if ok else RED)
            self.play(GrowFromCenter(hit), Flash(hit, color=AMBER if ok else RED, line_length=0.18), run_time=0.5)

            # margin back to the rear foot
            gap_in = cx - rear[0]
            text = a.margin_text or f"{gap_in:.0f} in of room behind you"
            y_dim = min(heel[1], toe[1], rear[1], cy) - 7
            dim = DoubleArrow(P(rear[0], y_dim), P(cx, y_dim), color=WHITE, stroke_width=3,
                              buff=0, tip_length=0.16)
            ticks = VGroup(Line(P(rear[0], rear[1]), P(rear[0], y_dim - 1), color=GREY, stroke_width=2),
                           Line(land, P(cx, y_dim - 1), color=GREY, stroke_width=2))
            lab = Text(text, font="Avenir Next", weight="SEMIBOLD", font_size=30, color=WHITE)
            lab.next_to(dim, DOWN, buff=0.15)
            self.play(Create(ticks), GrowFromCenter(dim), run_time=0.6)
            self.play(Write(lab), run_time=0.8)
            used = 0.5 + 1.2 + 0.6 + 3 * 0.35 + 0.8 + 0.5 + 0.7 + 0.5 + 0.6 + 0.8
            self.wait(max(0.5, a.secs - used))

    return Tripod, inside((cx, cy), (heel, toe, rear))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, help=".mov (ProRes 4444 alpha) or .webm (VP9 alpha)")
    ap.add_argument("--heel", default="0,0")
    ap.add_argument("--toe", default="9,2")
    ap.add_argument("--rear", default="-22,8")
    ap.add_argument("--com", default="-11,5,24", help="x,y,height (inches)")
    ap.add_argument("--hip", default="-14,20", help="x,height")
    ap.add_argument("--knee", default="2,20", help="x,height")
    ap.add_argument("--margin-text", default="almost a foot of room behind you")
    ap.add_argument("--scale", type=float, default=0.1, help="scene units per inch")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--secs", type=float, default=9.0)
    ap.add_argument("--opaque", action="store_true", help="dark background instead of alpha")
    ap.add_argument("--preview-png", default=None, help="also write the last frame as PNG")
    a = ap.parse_args()
    try:
        from manim import tempconfig
    except Exception as e:
        print(f"[sitka_tripod] manim not importable ({e}); run with ~/manim-env/bin/python", file=sys.stderr)
        sys.exit(2)
    w, h = (int(v) for v in a.size.split("x"))
    out = Path(a.out).resolve()
    tmp = Path(tempfile.mkdtemp(prefix="manim_"))
    alpha = not a.opaque
    cfg = {"media_dir": str(tmp), "pixel_width": w, "pixel_height": h, "frame_rate": a.fps,
           "transparent": alpha, "format": "mov" if alpha else "mp4", "output_file": "tripod",
           "background_color": "#0B1220", "disable_caching": True, "verbosity": "WARNING",
           "progress_bar": "none"}
    try:
        Tripod, ok = build_scene(a)
        with tempconfig(cfg):
            Tripod().render()
        made = sorted(tmp.rglob("tripod.mov" if alpha else "tripod.mp4"))
        if not made:
            raise RuntimeError(f"manim wrote nothing under {tmp}")
        src = made[0]
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.suffix == ".webm" and alpha:
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-c:v", "libvpx-vp9",
                            "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "24", str(out)], check=True)
        elif out.suffix == ".mov" and alpha:
            # re-wrap as ProRes 4444 with alpha whatever codec manim chose
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-c:v", "prores_ks",
                            "-profile:v", "4444", "-pix_fmt", "yuva444p10le", str(out)], check=True)
        else:
            shutil.copy2(src, out)
        if a.preview_png:
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-sseof", "-0.2", "-i", str(out),
                            "-frames:v", "1", a.preview_png], check=True)
    except Exception as e:
        print(f"[sitka_tripod] render failed: {e}", file=sys.stderr)
        sys.exit(2)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"[sitka_tripod] wrote {out}; CoM plumb point {'INSIDE' if ok else 'OUTSIDE'} the triangle")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
