"""Code-rendered motion for the model_review_h3 promo (Manim CE 0.22).

Every scene LnnA / LnnB is timed to the narration: t = 0 is the line's picture boundary on the
final timeline (line 1: 0.0, else the line's voice start, vo/words.json), and each beat waits for
its word onset. A = the setup for the line's first sentence(s), B = the alternate setup the cut
switches to on a later sentence's first word (selects.json "in" = that word's time - boundary).
Render: tools/render_all.sh. Pure function of words.json, no randomness.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from manim import *  # noqa: F401,F403

FILM = Path(__file__).resolve().parent.parent
W = json.loads((FILM / "vo" / "words.json").read_text())
PROMO = json.loads((FILM / "promo.json").read_text())
LINES = W["lines"]
WORDS = W["words"]
LAST_END = WORDS[-1]["end"]
SLAM = LAST_END + PROMO["endcard"].get("slam_after", 0.15)

BG = "#0B0F14"
PANEL = "#151B23"
EDGE = "#2A3441"
INK = "#E6EDF3"
MUTED = "#8B98A5"
TEAL = "#2DD4BF"
AMBER = "#F5B841"
RED = "#F0524F"
GREEN = "#3FB950"
BLUE = "#58A6FF"
SANS = "Helvetica Neue"
MONO = "Menlo"

config.background_color = BG


def norm(w):
    return re.sub(r"[^a-z0-9']", "", str(w).lower()).strip("'")


def bound(L):
    return 0.0 if L == 1 else next(l for l in LINES if l["line"] == L)["start"]


def span(L):
    nxt = [l for l in LINES if l["line"] == L + 1]
    return (nxt[0]["start"] if nxt else SLAM) - bound(L)


def T(L, word, nth=1):
    """onset of the nth `word` in line L, relative to the line's boundary"""
    for alt in str(word).split("|"):
        hits = [w for w in WORDS if w["line"] == L and norm(w["word"]) == norm(alt)]
        if len(hits) >= nth:
            return hits[nth - 1]["start"] - bound(L)
    raise KeyError(f"line {L}: word {word!r} (nth {nth}) not spoken")


def txt(s, size=36, color=INK, font=SANS, weight=NORMAL):
    return Text(s, font=font, font_size=size, color=color, weight=weight)


def card(w, h, fill=PANEL, edge=EDGE, r=0.25):
    light = fill.upper().startswith("#F")      # the license page stays solid paper; dark cards are glass
    return RoundedRectangle(width=w, height=h, corner_radius=r, fill_color=fill, fill_opacity=1 if light else 0.86,
                            stroke_color=edge, stroke_width=2)


def pill(s, color=TEAL, size=26, fill_op=0.15):
    t = txt(s, size, color, weight=BOLD)
    p = RoundedRectangle(width=t.width + 0.5, height=t.height + 0.3, corner_radius=(t.height + 0.3) / 2,
                         stroke_color=color, stroke_width=2, fill_color=color, fill_opacity=fill_op)
    return VGroup(p, t)


def red_x(mob, buff=0.1, width=10):
    a = Line(mob.get_corner(UL) + (UL * buff), mob.get_corner(DR) + (DR * buff), color=RED, stroke_width=width)
    b = Line(mob.get_corner(UR) + (UR * buff), mob.get_corner(DL) + (DL * buff), color=RED, stroke_width=width)
    return a, b


def check(color=GREEN, s=0.35):
    return VMobject(color=color, stroke_width=8).set_points_as_corners(
        [LEFT * s * 0.9 + UP * s * 0.05, DOWN * s * 0.55 + LEFT * s * 0.25, UP * s * 0.75 + RIGHT * s * 0.9])


def pop(m, rt=0.45):
    return GrowFromCenter(m, rate_func=rate_functions.ease_out_back, run_time=rt)


class Beat(MovingCameraScene):
    L = 1
    drift = 0.05           # the camera always drifts 2-4% (technique library: explainer cadence)
    pan = ORIGIN

    def setup(self):
        super().setup()
        self.dur = span(self.L) + 1.5
        fr = self.camera.frame
        self._t0 = 0.0
        k = (1 - self.drift) ** (1 / self.dur)
        v = np.array(self.pan) / self.dur
        fr.add_updater(lambda m, dt: m.scale(k ** dt).shift(v * dt))
        self.add(fr)   # 11/03: updaters only run on mobjects in the scene; without this the drift never ran
        # ambient layer (11/03, film_qc spec): a soft centre glow so no frame reads as black, and a faint
        # dot grid drifting diagonally so no hold is ever a frozen frame (explainer cadence, technique library)
        glow = VGroup(*[Circle(radius=7.0 - 0.25 * i, stroke_width=0, fill_color="#2A3646", fill_opacity=0.026)
                        for i in range(24)]).set_z_index(-10)
        grid = VGroup(*[Dot([x * 0.62, y * 0.62, 0], radius=0.032, color="#2C3846")
                        for x in range(-17, 18) for y in range(-10, 11)]).set_z_index(-9)
        gv = np.array([0.42, 0.24, 0])
        grid.add_updater(lambda m, dt: m.shift(gv * dt))
        self.add(glow, grid)

    @property
    def now(self):
        return self.renderer.time

    def at(self, t):
        d = t - self.now
        if d > 1 / 30:
            self.wait(d, frozen_frame=False)   # 11/03: a frozen wait skipped the camera drift (film_qc froze)

    def go(self, t, *anims, rt=0.5, **kw):
        self.at(t)
        self.play(*anims, run_time=rt, **kw)

    def finish(self):
        self.at(self.dur)

    def T(self, word, nth=1):
        return T(self.L, word, nth)


def hf_card(w=9.5, typed=False):
    c = card(w, 3.3)
    head = txt("Hugging Face", 24, AMBER, weight=BOLD).move_to(c.get_corner(UL) + RIGHT * 1.35 + DOWN * 0.45)
    repo = txt("OliviaRossi / Minimax-H3-Hybrid-DMAD-PDMD", 34, INK, font=MONO)
    repo.scale_to_fit_width(min(repo.width, w - 0.8)).next_to(head, DOWN, aligned_edge=LEFT, buff=0.35)
    pills = VGroup(pill("video model", BLUE, 22), pill("merge", TEAL, 22), pill("new today", AMBER, 22)) \
        .arrange(RIGHT, buff=0.25).next_to(repo, DOWN, aligned_edge=LEFT, buff=0.45)
    return VGroup(c, head, repo, pills)


# ---------------------------------------------------------------- line 1
class L01A(Beat):
    L = 1
    drift = 0.10
    pan = LEFT * 0.2

    def construct(self):
        phone = RoundedRectangle(width=3.6, height=7.0, corner_radius=0.45, stroke_color=EDGE, stroke_width=5,
                                 fill_color="#0F141A", fill_opacity=1)
        notch = RoundedRectangle(width=1.1, height=0.28, corner_radius=0.14, fill_color=BLACK, fill_opacity=1,
                                 stroke_width=0).move_to(phone.get_top() + DOWN * 0.35)
        clock = txt("Nov 3", 54, INK, weight=BOLD).move_to(phone.get_top() + DOWN * 1.3)
        g = VGroup(phone, notch, clock).shift(LEFT * 3.2)
        self.add(g)
        bub = card(3.35, 2.3, fill="#1F2933", r=0.3).move_to(phone.get_center() + UP * 0.3)
        who = txt("new-model-watch", 26, TEAL, weight=BOLD).move_to(bub.get_corner(UL) + RIGHT * 1.45 + DOWN * 0.35)
        msg = VGroup(txt("New video model on", 26, INK), txt("Hugging Face:", 26, INK),
                     txt("Minimax-H3-Hybrid", 24, AMBER, font=MONO)).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        msg.scale_to_fit_width(min(msg.width, bub.width - 0.45))
        who.scale_to_fit_width(min(who.width, bub.width - 0.45))
        who.align_to(bub, LEFT).shift(RIGHT * 0.22)
        msg.next_to(who, DOWN, aligned_edge=LEFT, buff=0.15)
        bubble = VGroup(bub, who, msg)
        side = VGroup(txt("from the mini", 30, MUTED), txt("this morning", 44, INK, weight=BOLD)) \
            .arrange(DOWN, aligned_edge=LEFT, buff=0.15).shift(RIGHT * 2.6 + UP * 1.4)
        self.go(self.T("morning") - 0.1, FadeIn(side, shift=UP * 0.3), rt=0.4)
        self.go(self.T("texted") - 0.05, pop(bubble), rt=0.45)
        self.play(phone.animate.set_stroke(TEAL, width=8), run_time=0.15)
        self.play(phone.animate.set_stroke(EDGE, width=5), run_time=0.35)
        card_ = hf_card(6.8).scale(0.85).next_to(side, DOWN, aligned_edge=LEFT, buff=0.6)
        self.go(self.T("A") - 0.1, FadeIn(card_, shift=LEFT * 0.6), rt=0.45)
        self.finish()


class L01B(Beat):
    L = 1
    drift = 0.10

    def construct(self):
        c = hf_card(11.5)
        repo = c[2]
        self.add(c[0], c[1])
        toast = pill("new-model-watch: a new video model", TEAL, 26).to_edge(UP, buff=0.6)
        self.go(max(0.2, self.T("texted") - 0.1), FadeIn(toast, shift=DOWN * 0.3), rt=0.35)
        self.at(max(self.now, self.T("A") - 0.05))
        self.play(AddTextLetterByLetter(repo), run_time=1.2)
        self.go(self.T("Hugging") - 0.05, LaggedStart(*[pop(p, 0.35) for p in c[3]], lag_ratio=0.25), rt=0.8)
        self.finish()


# ---------------------------------------------------------------- line 2
class L02A(Beat):
    L = 2

    def construct(self):
        h = txt("On paper", 64, INK, weight=BOLD).to_edge(UP, buff=1.0)
        big = txt("it's a dream", 96, TEAL, weight=BOLD)
        self.add(h)
        self.go(self.T("dream") - 0.15, FadeIn(big, scale=1.22), rt=0.25)
        sparks = VGroup(*[Dot(radius=0.06, color=c).move_to(big.get_center() + DOWN * 0.9)
                          for c in (TEAL, AMBER, BLUE, TEAL, AMBER, BLUE, TEAL, AMBER)])
        dirs = [np.array([np.cos(a), np.sin(a), 0]) for a in np.linspace(0, TAU, 8, endpoint=False)]
        self.play(*[s.animate.shift(d * 3.6).set_opacity(0) for s, d in zip(sparks, dirs)], run_time=0.6)
        self.go(self.T("Two") + 0.3, big.animate.scale(0.6).to_edge(UP, buff=1.6), FadeOut(h), rt=0.5)
        self.finish()


def blend_diagram():
    ax = Axes(x_range=[0, 50, 10], y_range=[0, 1, 0.5], x_length=9.5, y_length=3.6,
              axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": True},
              tips=False)
    xl = txt("block 0", 20, MUTED).next_to(ax.c2p(0, 0), DOWN, buff=0.2)
    xr = txt("block 50", 20, MUTED).next_to(ax.c2p(50, 0), DOWN, buff=0.2)
    curve = ax.plot(lambda x: 1 / (1 + np.exp(-(x - 25) / 4.5)), x_range=[0, 50], color=TEAL, stroke_width=7)
    a = pill("FL2VA", BLUE, 26).next_to(ax.c2p(0, 0.15), RIGHT, buff=0.3)
    b = pill("Ref2VA", AMBER, 26).next_to(ax.c2p(50, 0.88), LEFT, buff=0.3)
    return ax, xl, xr, curve, a, b


class L02B(Beat):
    L = 2

    def construct(self):
        ax, xl, xr, curve, a, b = blend_diagram()
        g = VGroup(ax, xl, xr, curve, a, b).shift(DOWN * 0.5)
        title = txt("two MiniMax H3 models, one S-curve", 34, INK, weight=BOLD).to_edge(UP, buff=0.8)
        self.add(ax)
        self.go(self.T("Two") - 0.05, FadeIn(title, shift=DOWN * 0.2), pop(a), pop(b), rt=0.45)
        self.go(self.T("blended") - 0.05, Create(curve), rt=1.0)
        self.go(self.T("fifty") - 0.1, FadeIn(xl), FadeIn(xr), Indicate(xr, color=TEAL), rt=0.5)
        badge = pill("33B parameters", TEAL, 34, 0.25).next_to(ax, UP, buff=-0.6).shift(LEFT * 2.2)
        self.go(self.T("thirty|thirtythree") - 0.1, pop(badge), rt=0.45)
        self.finish()


# ---------------------------------------------------------------- line 3
class L03A(Beat):
    L = 3
    pan = RIGHT * 0.2

    def construct(self):
        core = card(4.2, 2.6, fill="#12202A", edge=TEAL)
        core_t = txt("H3 merge", 40, INK, weight=BOLD).move_to(core)
        g = VGroup(core, core_t)
        self.add(g)
        l1 = pill("DMAD LoRA", BLUE, 30).move_to(LEFT * 5 + UP * 2.4)
        l2 = pill("PDMD LoRA", AMBER, 30).move_to(RIGHT * 5 + UP * 2.4)
        self.go(self.T("distillation") - 0.1, FadeIn(l1, shift=RIGHT), FadeIn(l2, shift=LEFT), rt=0.4)
        self.go(self.T("folded") - 0.05, l1.animate.next_to(core, UP, buff=0.3).shift(LEFT * 1.75),
                l2.animate.next_to(core, UP, buff=0.3).shift(RIGHT * 1.75), rt=0.45,
                rate_func=rate_functions.ease_out_back)
        steps = txt("4-8 steps", 64, TEAL, weight=BOLD).next_to(core, DOWN, buff=0.6)
        self.go(self.T("four") - 0.1, FadeIn(steps, scale=1.22), rt=0.3)
        self.finish()


class L03B(Beat):
    L = 3

    def construct(self):
        lab = txt("download size", 30, MUTED).to_edge(UP, buff=1.2).to_edge(LEFT, buff=1.3)
        full = Rectangle(width=11.0, height=1.0, fill_color=EDGE, fill_opacity=1, stroke_width=0) \
            .next_to(lab, DOWN, aligned_edge=LEFT, buff=0.4)
        bar = Rectangle(width=11.0, height=1.0, fill_color=AMBER, fill_opacity=1, stroke_width=0).move_to(full)
        n1 = txt("over 61 GB  bf16", 40, INK, weight=BOLD).next_to(full, DOWN, aligned_edge=LEFT, buff=0.3)
        self.add(lab, full)
        self.go(max(0.2, self.T("Squeezed") - 0.6), GrowFromEdge(bar, LEFT), rt=0.5)
        self.go(self.T("sixty") - 0.1, FadeIn(n1), rt=0.3)
        small = Rectangle(width=11.0 * 19 / 61.5, height=1.0, fill_color=TEAL, fill_opacity=1, stroke_width=0) \
            .align_to(full, LEFT).align_to(full, UP)
        n2 = txt("~19 GB  int8", 56, TEAL, weight=BOLD).next_to(n1, DOWN, aligned_edge=LEFT, buff=0.4)
        self.go(self.T("down") - 0.15, Transform(bar, small), rt=0.6, rate_func=rate_functions.ease_in_out_cubic)
        self.go(self.T("nineteen") - 0.05, FadeIn(n2, scale=1.22), n1.animate.set_color(MUTED), rt=0.3)
        self.finish()


# ---------------------------------------------------------------- line 4
def rank_card():
    c = card(9.0, 2.4, fill="#1A1A10", edge=AMBER)
    one = txt("#1", 110, AMBER, weight=BOLD).move_to(c.get_left() + RIGHT * 1.4)
    name = txt("MiniMax H3", 54, INK, weight=BOLD).next_to(one, RIGHT, buff=0.6).shift(UP * 0.3)
    sub = txt("our local video consensus research", 26, MUTED).next_to(name, DOWN, aligned_edge=LEFT, buff=0.2)
    return VGroup(c, one, name, sub)


class L04A(Beat):
    L = 4

    def construct(self):
        head = txt("our own local video research", 52, INK, weight=BOLD).to_edge(UP, buff=1.1)
        rc = rank_card()
        self.add(head)
        self.go(self.T("H3") - 0.1, pop(rc[0], 0.4), FadeIn(rc[2]), rt=0.4)
        self.go(self.T("number") - 0.1, FadeIn(rc[1], scale=1.3), rt=0.3)
        self.go(self.T("research") - 0.15, FadeIn(rc[3], shift=UP * 0.2), rt=0.3)
        self.play(Circumscribe(rc[0], color=AMBER, time_width=0.6), run_time=0.8)
        self.finish()


class L04B(Beat):
    L = 4
    drift = 0.04

    def construct(self):
        tro = VGroup(Polygon([-1.2, 0.8, 0], [1.2, 0.8, 0], [0.7, -0.6, 0], [-0.7, -0.6, 0],
                             fill_color=AMBER, fill_opacity=1, stroke_width=0),
                     Rectangle(width=0.4, height=0.6, fill_color=AMBER, fill_opacity=1, stroke_width=0).shift(DOWN * 0.9),
                     Rectangle(width=1.6, height=0.35, fill_color=AMBER, fill_opacity=1, stroke_width=0).shift(DOWN * 1.35)) \
            .shift(LEFT * 3.5)
        one = txt("1", 72, BG, weight=BOLD).move_to(tro[0])
        name = VGroup(txt("MiniMax H3", 64, INK, weight=BOLD), txt("ranked first in our local video research", 28, MUTED)) \
            .arrange(DOWN, aligned_edge=LEFT, buff=0.25).next_to(tro, RIGHT, buff=0.9)
        self.go(max(0.05, self.T("H3") - 0.1), FadeIn(name[0], shift=LEFT * 0.4), rt=0.35)
        self.go(self.T("number") - 0.1, GrowFromEdge(tro, DOWN), rt=0.45)
        self.play(FadeIn(one, scale=1.3), run_time=0.2)
        self.go(self.T("research") - 0.2, FadeIn(name[1]), rt=0.3)
        self.finish()


# ---------------------------------------------------------------- line 5
class L05A(Beat):
    L = 5

    def construct(self):
        s1 = txt("STEP 1", 44, TEAL, weight=BOLD)
        lic = txt("LICENSE", 140, INK, weight=BOLD)
        g = VGroup(s1, lic).arrange(DOWN, buff=0.2)
        pre = txt("every new model starts at", 60, INK, weight=BOLD).next_to(g, UP, buff=0.6)
        self.add(pre)
        self.go(self.T("step") - 0.05, FadeIn(s1, scale=1.22), rt=0.25)
        self.go(self.T("license") - 0.05, FadeIn(lic, scale=1.22), rt=0.25)
        self.play(Flash(lic.get_center(), color=WHITE, line_length=1.2, num_lines=16, flash_radius=4.2), run_time=0.4)
        self.finish()


def doc(title="LICENSE", w=6.0, h=7.2, lines=11):
    page = card(w, h, fill="#F2F4F7", edge="#C9D1D9", r=0.12)
    t = txt(title, 34, "#1F2328", font=MONO, weight=BOLD).move_to(page.get_top() + DOWN * 0.6)
    rows = VGroup(*[Rectangle(width=(w - 1.2) * (0.6 + 0.4 * ((k * 7) % 5) / 4), height=0.12,
                              fill_color="#AEB7C2", fill_opacity=1, stroke_width=0) for k in range(lines)]) \
        .arrange(DOWN, aligned_edge=LEFT, buff=0.38).next_to(t, DOWN, buff=0.55).align_to(page, LEFT).shift(RIGHT * 0.6)
    return VGroup(page, t, rows)


class L05B(Beat):
    L = 5

    def construct(self):
        tag = pill("license tag on the page", MUTED, 30, 0.1).shift(LEFT * 3.6 + UP * 1.0)
        d = doc().scale(0.85).shift(RIGHT * 3.0)
        self.add(tag)
        self.go(max(0.1, self.T("The", 2) - 0.4), FadeIn(d, shift=UP * 0.4), rt=0.4)
        self.go(self.T("actual") - 0.05, Indicate(d[1], color=TEAL, scale_factor=1.15), rt=0.5)
        a, b = red_x(tag[0], 0.05, 8)
        self.go(self.T("tag") - 0.15, Create(a), rt=0.12)
        self.play(Create(b), run_time=0.12)
        self.play(tag.animate.set_opacity(0.35), run_time=0.3)
        self.finish()


# ---------------------------------------------------------------- line 6
class L06A(Beat):
    L = 6

    def construct(self):
        child = pill("Minimax-H3-Hybrid-DMAD-PDMD", AMBER, 30).shift(UP * 2.3)
        arrow = Arrow(UP * 1.6, DOWN * 0.6, color=MUTED, stroke_width=6, buff=0)
        lab = txt("base_model", 26, MUTED, font=MONO).next_to(arrow, RIGHT, buff=0.3)
        par = pill("MiniMax H3", BLUE, 44).shift(DOWN * 1.4)
        lic = txt("its license comes along", 30, TEAL).next_to(par, DOWN, buff=0.5)
        self.add(child)
        self.go(self.T("inherits") - 0.1, GrowArrow(arrow), FadeIn(lab), rt=0.45)
        self.go(self.T("base") - 0.1, pop(par), rt=0.4)
        self.go(self.T("license") - 0.15, FadeIn(lic, shift=UP * 0.2), rt=0.3)
        self.finish()


class L06B(Beat):
    L = 6
    pan = DOWN * 0.3

    def construct(self):
        nodes = VGroup(pill("the hybrid merge", AMBER, 30), pill("FL2VA + Ref2VA", TEAL, 30),
                       pill("MiniMax H3", BLUE, 40)).arrange(DOWN, buff=1.0)
        arrows = VGroup(*[Arrow(nodes[k].get_bottom(), nodes[k + 1].get_top(), color=MUTED, buff=0.1, stroke_width=5)
                          for k in range(2)])
        lic = doc("LICENSE", 3.2, 3.6, 5).scale(0.8).next_to(nodes[2], RIGHT, buff=1.0)
        self.add(nodes[0])
        self.go(max(0.1, self.T("So") - 0.3), GrowArrow(arrows[0]), FadeIn(nodes[1]), rt=0.4)
        self.go(self.T("followed") - 0.05, GrowArrow(arrows[1]), rt=0.35)
        self.go(self.T("MiniMax") - 0.1, pop(nodes[2]), rt=0.4)
        self.go(self.T("H3") + 0.1, FadeIn(lic, shift=LEFT * 0.4), rt=0.35)
        self.finish()


# ---------------------------------------------------------------- line 7
CLAUSE1 = ['"Excluded Territories" means the', 'European Union, the United Kingdom,', 'the Republic of Korea and the',
           'United States of America']
CLAUSE2 = ['You may not use, reproduce, modify,', 'distribute, or display the MiniMax H3', 'Works or any of their Outputs or results',
           'outside the Applicable Territory.']


def clause(rows, size=34):
    return VGroup(*[txt(r, size, "#1F2328", font=SANS) for r in rows]).arrange(DOWN, aligned_edge=LEFT, buff=0.22)


def hl(mob, color=AMBER, op=0.45):
    return Rectangle(width=mob.width + 0.2, height=mob.height + 0.12, fill_color=color, fill_opacity=op,
                     stroke_width=0).move_to(mob)


class L07A(Beat):
    L = 7
    drift = 0.10

    def construct(self):
        page = card(12.4, 6.6, fill="#F2F4F7", edge="#C9D1D9", r=0.12)
        src = txt("MiniMax H3 license", 24, "#57606A", font=MONO).move_to(page.get_corner(UL) + RIGHT * 1.9 + DOWN * 0.45)
        cl = clause(CLAUSE1, 44).move_to(page).shift(DOWN * 0.2).set_z_index(2)
        self.add(page, src)
        self.go(self.T("there") - 0.1, FadeIn(cl, shift=UP * 0.3), rt=0.4)
        h0 = hl(cl[0]).set_z_index(1)
        self.go(self.T("Excluded") - 0.05, GrowFromEdge(h0, LEFT), rt=0.3)
        h1 = hl(cl[1]).set_z_index(1)
        self.go(self.T("European") - 0.05, GrowFromEdge(h1, LEFT), rt=0.4)
        h2 = hl(cl[2]).set_z_index(1)
        self.go(self.T("Korea") - 0.5, GrowFromEdge(h2, LEFT), rt=0.4)
        h3 = hl(cl[3], RED, 0.55).set_z_index(1)
        self.go(self.T("United", 2) - 0.05, GrowFromEdge(h3, LEFT), rt=0.3)
        self.play(cl[3].animate.set_color("#8B0000"), run_time=0.3)
        self.finish()


class L07B(Beat):
    L = 7
    drift = 0.10

    def construct(self):
        page = card(12.4, 6.6, fill="#F2F4F7", edge="#C9D1D9", r=0.12)
        src = txt("MiniMax H3 license", 24, "#57606A", font=MONO).move_to(page.get_corner(UL) + RIGHT * 1.9 + DOWN * 0.45)
        cl = clause(CLAUSE2, 44).move_to(page).shift(DOWN * 0.2).set_z_index(2)
        self.add(page, src, cl)
        self.at(max(0.0, self.T("Outputs") - 0.05))
        # highlight the "Outputs" phrase row and the territory row
        h = hl(cl[2], RED, 0.5).set_z_index(1)
        h2 = hl(cl[3], AMBER, 0.45).set_z_index(1)
        self.play(GrowFromEdge(h, LEFT), run_time=0.3)
        self.play(GrowFromEdge(h2, LEFT), run_time=0.3)
        stamp = pill("outputs included", RED, 40, 0.2).set_z_index(3).rotate(-0.08).next_to(page, DOWN, buff=-0.9).shift(RIGHT * 3.4)
        self.go(self.T("included") - 0.05, pop(stamp, 0.35), rt=0.35)
        self.finish()


# ---------------------------------------------------------------- line 8
def california():
    # a simple stylised outline of California (not to scale), drawn as a polygon
    pts = [[-1.05, 2.0], [0.15, 2.0], [0.15, 0.6], [1.6, -0.9], [1.55, -1.35], [1.25, -1.85], [0.55, -1.95],
           [0.3, -1.4], [-0.25, -1.0], [-0.55, -0.5], [-0.85, 0.2], [-1.05, 0.9], [-1.2, 1.5]]
    return Polygon(*[[x, y, 0] for x, y in pts], color=TEAL, fill_color="#12202A", fill_opacity=1, stroke_width=5)


class L08A(Beat):
    L = 8

    def construct(self):
        ca = california().scale(1.35).shift(LEFT * 3.0)
        pin = VGroup(Dot(radius=0.18, color=AMBER), txt("us", 28, AMBER, weight=BOLD).shift(RIGHT * 0.45)) \
            .move_to(ca.get_center() + LEFT * 0.4 + UP * 0.9)
        lab = txt("California", 52, INK, weight=BOLD).shift(RIGHT * 3.0 + UP * 1.2)
        out = txt("outside the licensed territory", 30, MUTED).next_to(lab, DOWN, buff=0.3)
        self.add(lab, ca.copy().set_fill(opacity=0))
        self.go(0.03, DrawBorderThenFill(ca), rt=0.6)
        self.play(FadeIn(pin, scale=1.4), Indicate(lab, color=TEAL, scale_factor=1.05), run_time=0.3)
        a, b = red_x(ca, -0.3, 14)
        self.go(self.T("so") - 0.1, Create(a), rt=0.12)
        self.play(Create(b), run_time=0.12)
        self.go(self.T("out") - 0.1, FadeIn(out), rt=0.3)
        self.finish()


class L08B(Beat):
    L = 8

    def construct(self):
        steps = VGroup(pill("convert to MLX", BLUE, 32), pill("upload to Hugging Face", AMBER, 32),
                       pill("= distribution", RED, 32)).arrange(RIGHT, buff=0.9).shift(UP * 0.8)
        steps.scale_to_fit_width(min(steps.width, 11.8))
        ar = VGroup(*[Arrow(steps[k].get_right(), steps[k + 1].get_left(), buff=0.1, color=MUTED, stroke_width=5)
                      for k in range(2)])
        head = txt("an MLX port on Hugging Face?", 56, INK, weight=BOLD).to_edge(UP, buff=0.9)
        self.add(head)
        self.go(max(0.05, self.T("MLX") - 0.3), pop(steps[0]), rt=0.35)
        self.go(self.T("Hugging") - 0.2, GrowArrow(ar[0]), pop(steps[1]), rt=0.4)
        self.go(self.T("distributing") - 0.1, GrowArrow(ar[1]), pop(steps[2]), rt=0.4)
        no = txt("NO", 150, RED, weight=BOLD).shift(DOWN * 1.8)
        self.go(self.T("no") - 0.1, FadeIn(no, scale=1.4), rt=0.2)
        self.finish()


# ---------------------------------------------------------------- line 9
class L09A(Beat):
    L = 9

    def construct(self):
        head = txt("does it fit how we build?", 60, INK, weight=BOLD).to_edge(UP, buff=1.0)
        c1 = pill("int8 only", AMBER, 48).shift(LEFT * 3.0)
        c2 = pill("ComfyUI only", AMBER, 48).shift(RIGHT * 3.0)
        self.add(head)
        self.go(self.T("int8|eight") - 0.1, pop(c1), rt=0.4)
        self.go(self.T("ComfyUI|Comfy") - 0.1, pop(c2), rt=0.4)
        x1, y1 = red_x(c1, 0.05, 8)
        x2, y2 = red_x(c2, 0.05, 8)
        self.play(Create(x1), Create(x2), run_time=0.12)
        self.play(Create(y1), Create(y2), run_time=0.12)
        self.finish()


class L09B(Beat):
    L = 9

    def construct(self):
        we = txt("we run", 40, MUTED).shift(UP * 1.4)
        bf = txt("bf16", 150, TEAL, weight=BOLD)
        sub = txt("full precision, on Apple Silicon", 32, INK).shift(DOWN * 1.5)
        self.add(we)
        self.go(max(0.05, self.T("We") - 0.05), FadeIn(bf, scale=1.22), rt=0.25)
        self.go(self.T("precision") - 0.1, FadeIn(sub, shift=UP * 0.2), rt=0.3)
        self.finish()


# ---------------------------------------------------------------- line 10
def k6_card(w=8.0):
    c = card(w, 5.6, fill="#101A17", edge=GREEN)
    name = txt("Kandinsky 6 Pro", 54, INK, weight=BOLD).move_to(c.get_top() + DOWN * 0.75)
    rows = [("MIT license", GREEN), ("29B parameters, bf16", INK), ("~12 min per 3 s clip", INK), ("M5 Max 128 GB", MUTED)]
    rr = VGroup(*[txt(s, 36, col) for s, col in rows]).arrange(DOWN, aligned_edge=LEFT, buff=0.35) \
        .next_to(name, DOWN, buff=0.55)
    return VGroup(c, name, rr)


class L10A(Beat):
    L = 10

    def construct(self):
        q = txt("So what do we use?", 80, INK, weight=BOLD)
        self.add(q)
        self.go(self.T("Kandinsky") - 0.2, q.animate.scale(0.5).to_edge(UP, buff=0.8).set_color(MUTED), rt=0.3)
        k = k6_card().scale(0.8).shift(DOWN * 0.5)
        self.play(pop(k[0], 0.35), FadeIn(k[1]), run_time=0.35)
        self.finish()


class L10B(Beat):
    L = 10
    drift = 0.10
    pan = LEFT * 0.15

    def construct(self):
        k = k6_card(9.0)
        self.add(k[0], k[1])
        self.go(max(0.05, self.T("Kandinsky") - 0.05), Indicate(k[1], color=GREEN, scale_factor=1.08), rt=0.4)
        cues = ["MIT", "twenty", "twelve", "M5"]
        for row, wd in zip(k[2], cues):
            self.go(self.T(wd) - 0.1, FadeIn(row, shift=RIGHT * 0.3), rt=0.3)
        self.play(Indicate(k[2][0], color=GREEN, scale_factor=1.06), run_time=0.5)
        self.finish()


# ---------------------------------------------------------------- line 11
class L11A(Beat):
    L = 11

    def construct(self):
        mark = txt("“", 200, GREEN, weight=BOLD).shift(LEFT * 5.2 + UP * 1.6)
        q = VGroup(txt("That's the best", 76, INK, weight=BOLD), txt("I've ever seen.", 76, INK, weight=BOLD)) \
            .arrange(DOWN, aligned_edge=LEFT, buff=0.2).shift(UP * 0.2)
        who = txt("Matt, on Kandinsky 6's first clip", 40, TEAL, weight=BOLD).next_to(q, DOWN, aligned_edge=LEFT, buff=0.5)
        self.add(who, mark)
        self.go(self.T("that's") - 0.05, FadeIn(q[0], shift=UP * 0.2), rt=0.3)
        self.go(self.T("ever") - 0.25, FadeIn(q[1], shift=UP * 0.2), rt=0.3)
        self.finish()


class L11B(Beat):
    L = 11
    drift = 0.10

    def construct(self):
        head = txt("what we use now", 34, MUTED).to_edge(UP, buff=0.7)
        k = k6_card(6.3).scale(0.95).shift(LEFT * 3.4 + DOWN * 0.3)
        k[2].scale(0.8).next_to(k[1], DOWN, buff=0.5)
        k[1].scale(0.85)
        l = card(6.3, 5.6, fill="#101827", edge=BLUE).scale(0.95).shift(RIGHT * 3.4 + DOWN * 0.3)
        ln = txt("LTX-2.5", 52, INK, weight=BOLD).move_to(l.get_top() + DOWN * 0.75)
        lr = VGroup(txt("quick previews", 34, INK), txt("lip sync", 34, INK)).arrange(DOWN, aligned_edge=LEFT, buff=0.4) \
            .next_to(ln, DOWN, buff=0.6)
        everything = VGroup(head, k, l, ln, lr).scale(0.86).shift(UP * 0.15)
        self.add(head, k)
        self.go(max(0.05, self.T("And") - 0.05), pop(l, 0.4), FadeIn(ln), rt=0.4)
        self.go(self.T("LTX") - 0.1, Indicate(ln, color=BLUE, scale_factor=1.1), rt=0.5)
        self.go(self.T("previs|quick") - 0.15, FadeIn(lr[0], shift=RIGHT * 0.3), rt=0.3)
        self.go(self.T("lip") - 0.1, FadeIn(lr[1], shift=RIGHT * 0.3), rt=0.3)
        self.finish()


# ---------------------------------------------------------------- line 12
STEPS = ["License", "Fit", "Compare", "Test", "Convert", "Verdict", "Review video"]
STEP_WORDS = ["License", "fit", "compare", "test", "convert", "verdict", "review"]


def checklist(size=40):
    rows = VGroup()
    for k, s in enumerate(STEPS):
        box = RoundedRectangle(width=0.62, height=0.62, corner_radius=0.1, stroke_color=MUTED, stroke_width=3)
        n = txt(f"{k + 1}", 26, MUTED, weight=BOLD)
        lab = txt(s, size, INK)
        r = VGroup(box, n, lab)
        n.next_to(box, RIGHT, buff=0.3)
        lab.next_to(box, RIGHT, buff=0.85)
        rows.add(r)
    rows.arrange(DOWN, aligned_edge=LEFT, buff=0.24)
    return rows


class L12A(Beat):
    L = 12

    def construct(self):
        a = txt("every new model", 72, INK, weight=BOLD)
        b = txt("the same 7 steps", 96, INK, weight=BOLD)
        g = VGroup(a, b).arrange(DOWN, buff=0.3)
        self.add(a)
        self.go(self.T("seven") - 0.1, FadeIn(b, scale=1.22), rt=0.25)
        self.finish()


class L12B(Beat):
    L = 12
    drift = 0.03

    def construct(self):
        cl = checklist().move_to(LEFT * 1.2)
        head = txt("new model vetting", 30, TEAL, weight=BOLD).next_to(cl, UP, buff=0.4, aligned_edge=LEFT)
        self.add(head, cl)
        for row, wd in zip(cl, STEP_WORDS):
            self.at(self.T(wd) - 0.05)
            ck = check().move_to(row[0]).shift(UP * 0.04)
            self.play(Create(ck), row[0].animate.set_stroke(GREEN), row[2].animate.set_color(GREEN),
                      run_time=0.18, rate_func=rate_functions.ease_out_cubic)
        self.finish()


# ---------------------------------------------------------------- line 13
class L13A(Beat):
    L = 13

    def construct(self):
        now = pill("MiniMax H3 license", MUTED, 40, 0.1).shift(LEFT * 3.3 + UP * 1.2)
        ar = Arrow(now.get_right(), RIGHT * 1.4 + UP * 1.2, color=MUTED, buff=0.2, stroke_width=5)
        ap = pill("Apache-2.0 ?", GREEN, 48).next_to(ar, RIGHT, buff=0.2)
        quote = txt("“maybe, no promises”", 44, INK).shift(DOWN * 0.6)
        who = txt("MiniMax team", 28, MUTED).next_to(quote, DOWN, buff=0.25)
        port = pill("then we port it", TEAL, 44, 0.25).shift(DOWN * 2.5)
        self.add(now)
        self.go(self.T("relicenses|changes") - 0.1, GrowArrow(ar), pop(ap), rt=0.45)
        self.go(self.T("maybe") - 0.1, FadeIn(quote, shift=UP * 0.2), FadeIn(who), rt=0.3)
        self.go(self.T("port") - 0.25, pop(port, 0.4), rt=0.4)
        self.finish()


class L13B(Beat):
    L = 13
    drift = 0.04

    def construct(self):
        door = Rectangle(width=2.6, height=4.6, stroke_color=TEAL, stroke_width=6).shift(LEFT * 3.2)
        light = Polygon(door.get_corner(UR), door.get_corner(DR), [1.2, -2.8, 0], [1.2, 2.8, 0],
                        stroke_width=0, fill_color=TEAL, fill_opacity=0.12)
        leaf = Polygon(door.get_corner(UL), door.get_corner(DL), door.get_corner(DL) + RIGHT * 1.1 + DOWN * 0.3,
                       door.get_corner(UL) + RIGHT * 1.1 + UP * 0.3, fill_color="#12202A", fill_opacity=1,
                       stroke_color=TEAL, stroke_width=4)
        t = VGroup(txt("door stays open", 52, INK, weight=BOLD), txt("if H3 is relicensed, we port it", 32, MUTED)) \
            .arrange(DOWN, aligned_edge=LEFT, buff=0.25).shift(RIGHT * 2.6)
        self.add(door)
        self.go(max(0.05, self.T("relicenses|changes") - 0.2), FadeIn(leaf), FadeIn(light), rt=0.5)
        self.go(self.T("maybe") - 0.1, FadeIn(t[0], shift=LEFT * 0.3), rt=0.3)
        self.go(self.T("port") - 0.2, FadeIn(t[1], shift=LEFT * 0.3), rt=0.3)
        self.finish()


# ---------------------------------------------------------------- line 14
class L14A(Beat):
    L = 14
    drift = 0.05

    def construct(self):
        cl = checklist(36).scale(0.9).shift(LEFT * 3.0)
        for row in cl:
            row[0].set_stroke(GREEN)
            row[2].set_color(GREEN)
            row.add(check().move_to(row[0]).shift(UP * 0.04))
        how = VGroup(txt("how we pick", 60, INK, weight=BOLD), txt("our tools", 60, TEAL, weight=BOLD)) \
            .arrange(DOWN, aligned_edge=LEFT, buff=0.2).shift(RIGHT * 3.2)
        self.add(cl)
        self.go(max(0.05, self.T("how") - 0.1), FadeIn(how[0], shift=LEFT * 0.3), rt=0.3)
        self.go(self.T("tools") - 0.15, FadeIn(how[1], shift=LEFT * 0.3), rt=0.3)
        self.finish()


class L14B(Beat):
    L = 14
    drift = 0.03

    def construct(self):
        a = txt("Read the license first,", 76, INK, weight=BOLD)
        b = txt("then build.", 96, TEAL, weight=BOLD)
        g = VGroup(a, b).arrange(DOWN, buff=0.35)
        self.go(max(0.05, self.T("Read") - 0.05), FadeIn(a, shift=UP * 0.2), rt=0.3)
        self.go(self.T("build") - 0.15, FadeIn(b, scale=1.22), rt=0.25)
        self.finish()
