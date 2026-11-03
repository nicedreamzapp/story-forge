#!/usr/bin/env python3
"""motion_tokens.py — one shared motion vocabulary for everything we render with code.

WHY THIS EXISTS (2026-11-02): titles, callouts, Manim diagrams and Blender camera moves each
carried their own easing (an ease_out_back here, a smoothstep there, a hand-tuned 0.35 s pop),
so two pieces of the same film moved like two different studios made them. Motion design
practice is to give each CLASS of object one rule and reuse it everywhere:

  micro     UI ticks, blips, a dot landing, a counter step: a fast snap, no overshoot (~0.12 s)
  panel     cards, label pills, lower thirds: a critically-under-damped spring that settles
            with one small overshoot (~8 %, ~0.5 s to rest)
  camera    pans, pushes, orbits, the vertical reframe's follow: slow ease in AND out, never
            overshoots, never snaps (a camera has mass)
  headline  big type: fast in (fully readable by 0.15 s), HOLD dead still, quick fade out (0.30 s).
            Those numbers are the ones text_readtime_check.py budgets for titles.
  mascot    characters and playful props: a bouncy settle plus a small seeded idle wobble
            (squash/stretch, tilt), different per seed and identical every render

Every function is a pure function of time (seconds, or 0..1 where it says so) and an optional seed:
no state, no frame counter, so any frame can be rendered alone, out of order, on any machine, and
it is the same frame (seekable + deterministic, which Remotion, ffmpeg PNG overlays and Blender
frame-by-frame rendering all need). No numpy, no imports beyond math, so it also runs inside
Blender's Python and Manim (`rate(name)` adapts a token to a Manim rate_func).

Usage:
    from motion_tokens import headline, panel, camera_ease, micro_snap, mascot, TOKENS
    a = headline(t, dur=1.6)          # {"alpha", "scale", "dy"} for a title up for 1.6 s
    s = panel(t)                      # 0 -> ~1.06 -> 1.0 spring progress
    x = camera_ease(t / 2.0)          # 0..1 eased progress of a 2 s move
The doc is _shared/composition-and-motion.md ("Motion tokens").
"""
from __future__ import annotations

import math

# The numbers live in ONE place. Change a feel here and every renderer follows.
TOKENS = {
    "micro":    {"dur": 0.12},
    "panel":    {"freq": 2.2, "zeta": 0.62, "fade_in": 0.10, "fade_out": 0.25},
    "camera":   {"min_dur": 0.6},
    "headline": {"t_in": 0.15, "t_out": 0.30, "scale_from": 1.22, "flash": 0.20, "dy": 0.0},
    "mascot":   {"freq": 2.6, "zeta": 0.35, "wobble_hz": 0.9, "wobble_deg": 4.0, "squash": 0.06},
}


def clamp01(x: float) -> float:
    return 0.0 if x <= 0 else 1.0 if x >= 1 else x


def smoothstep(u: float) -> float:
    u = clamp01(u)
    return u * u * (3 - 2 * u)


def ease_out_expo(u: float) -> float:
    u = clamp01(u)
    return 1.0 if u >= 1 else 1 - 2 ** (-10 * u)


def ease_out_cubic(u: float) -> float:
    u = clamp01(u)
    return 1 - (1 - u) ** 3


# ----------------------------------------------------------------------------- micro
def micro_snap(t: float, dur: float | None = None) -> float:
    """0 -> 1 in `dur` seconds (default 0.12), ease-out-cubic, no overshoot. For blips and ticks."""
    d = dur or TOKENS["micro"]["dur"]
    return ease_out_cubic(t / d)


# ----------------------------------------------------------------------------- spring (closed form)
def spring(t: float, freq: float = 2.2, zeta: float = 0.62) -> float:
    """Unit step response of a damped harmonic oscillator, closed form (so it is seekable).

    freq = natural frequency in Hz, zeta = damping ratio (< 1 overshoots once or twice, 1 = critical).
    Returns 0 at t <= 0 and settles to 1.
    """
    if t <= 0:
        return 0.0
    w = 2 * math.pi * freq
    if zeta >= 1.0:   # critically damped (or over): no overshoot
        return 1 - (1 + w * t) * math.exp(-w * t)
    wd = w * math.sqrt(1 - zeta * zeta)
    return 1 - math.exp(-zeta * w * t) * (math.cos(wd * t) + (zeta / math.sqrt(1 - zeta * zeta)) * math.sin(wd * t))


def panel(t: float) -> float:
    """Panel settle: spring progress with one small overshoot (~8 %), at rest by ~0.5 s."""
    p = TOKENS["panel"]
    return spring(t, p["freq"], p["zeta"])


def panel_alpha(t: float, dur: float | None = None) -> float:
    """Opacity for a panel up `dur` seconds: >= 0.9 by ~0.09 s, fades over the last 0.25 s."""
    p = TOKENS["panel"]
    a = smoothstep(t / (p["fade_in"] * 1.25))
    if dur is not None:
        left = dur - t
        if left < p["fade_out"]:
            a *= smoothstep(left / p["fade_out"])
    return a


# ----------------------------------------------------------------------------- camera
def camera_ease(u: float) -> float:
    """Slow ease in and out for camera moves, u = 0..1 of the move. Quintic smootherstep:
    zero velocity AND zero acceleration at both ends, so a move never starts or stops with a jolt."""
    u = clamp01(u)
    return u * u * u * (u * (u * 6 - 15) + 10)


def camera_path(keys: list, t: float) -> float:
    """Value of a camera path at time t. `keys` = [[t, value], ...] sorted by t; between two keys the
    value travels with camera_ease (equal values = a hold). Outside the keys it holds the end value."""
    if not keys:
        return 0.0
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            if t1 - t0 <= 1e-9:
                return v1
            return v0 + (v1 - v0) * camera_ease((t - t0) / (t1 - t0))
    return keys[-1][1]


def camera_path_ffmpeg(keys: list, var: str = "t") -> str:
    """The same path as an ffmpeg expression in `var` (crop x/y, overlay x/y are evaluated per frame).
    Nested if() over the segments; each segment is v0 + (v1 - v0) * smootherstep(u)."""
    if not keys:
        return "0"
    if len(keys) == 1:
        return f"{keys[0][1]:.6f}"
    expr = f"{keys[-1][1]:.6f}"
    for (t0, v0), (t1, v1) in reversed(list(zip(keys, keys[1:]))):
        if abs(v1 - v0) < 1e-9 or t1 - t0 <= 1e-9:
            seg = f"{v1:.6f}"
        else:
            u = f"clip(({var}-{t0:.5f})/{t1 - t0:.5f},0,1)"
            seg = f"({v0:.6f}+{v1 - v0:.6f}*pow({u},3)*({u}*({u}*6-15)+10))"
        expr = f"if(lt({var},{t1:.5f}),{seg},{expr})"
    return f"if(lt({var},{keys[0][0]:.5f}),{keys[0][1]:.6f},{expr})"


# ----------------------------------------------------------------------------- headline
def headline(t: float, dur: float) -> dict:
    """Big type: fast in, hold, quick out. Returns alpha (0..1), scale (1.22 -> 1.0), flash (0..1 white
    slam that decays in 0.2 s) and bar (0..1, the underline growing in after the type lands).
    Fully readable (alpha >= 0.9) by t_in = 0.15 s; leaves over the last t_out = 0.30 s."""
    h = TOKENS["headline"]
    a_in = ease_out_expo(t / h["t_in"]) / ease_out_expo(1.0)
    left = dur - t
    a_out = smoothstep(left / h["t_out"]) if left < h["t_out"] else 1.0
    scale = 1.0 + (h["scale_from"] - 1.0) * (1 - ease_out_expo(t / (h["t_in"] * 2.2)))
    flash = (1 - t / h["flash"]) ** 2 if 0 <= t < h["flash"] else 0.0
    bar = camera_ease((t - h["t_in"]) / 0.40)
    return {"alpha": clamp01(a_in) * a_out, "scale": scale, "flash": flash, "bar": bar}


# ----------------------------------------------------------------------------- mascot
def _seeded(seed: int, k: int) -> float:
    """A deterministic 0..1 number from (seed, k): sine hash, no RNG state."""
    x = math.sin((seed + 1) * 12.9898 + k * 78.233) * 43758.5453
    return x - math.floor(x)


def mascot(t: float, seed: int = 0) -> dict:
    """Playful entrance + idle: a bouncy spring in (more overshoot than a panel), then a small wobble
    whose phase and rate depend on the seed. Returns pop (0..~1.2..1), rot (degrees), sx, sy (squash /
    stretch, volume-preserving)."""
    m = TOKENS["mascot"]
    pop = spring(t, m["freq"], m["zeta"])
    vel = spring(t + 1 / 240, m["freq"], m["zeta"]) - pop
    ph = _seeded(seed, 1) * 2 * math.pi
    hz = m["wobble_hz"] * (0.8 + 0.4 * _seeded(seed, 2))
    settle = clamp01(t / 0.6)
    rot = m["wobble_deg"] * settle * math.sin(2 * math.pi * hz * t + ph)
    st = max(-1.0, min(1.0, vel * 60)) * m["squash"] + 0.02 * settle * math.sin(4 * math.pi * hz * t + ph * 0.5)
    sy = 1 + st
    return {"pop": pop, "rot": rot, "sx": 1 / sy, "sy": sy}


# ----------------------------------------------------------------------------- adapters
def rate(name: str, dur: float = 1.0):
    """A 0..1 -> 0..1 rate function for Manim (`rate_func=rate("camera")`). Spring tokens are sampled
    over `dur` seconds so the overshoot survives."""
    if name == "camera":
        return camera_ease
    if name == "micro":
        return ease_out_cubic
    if name == "panel":
        return lambda u: panel(u * dur)
    if name == "headline":
        return lambda u: ease_out_expo(u)
    if name == "mascot":
        return lambda u: mascot(u * dur)["pop"]
    raise KeyError(f"unknown motion token '{name}' (have: {', '.join(TOKENS)})")


def sample(name: str, t: float, **kw):
    """Generic entry: sample('panel', t), sample('headline', t, dur=1.6), sample('mascot', t, seed=3)."""
    if name == "micro":
        return micro_snap(t, kw.get("dur"))
    if name == "panel":
        return panel(t)
    if name == "camera":
        return camera_ease(t / kw.get("dur", 1.0))
    if name == "headline":
        return headline(t, kw.get("dur", 1.6))
    if name == "mascot":
        return mascot(t, kw.get("seed", 0))
    raise KeyError(name)


if __name__ == "__main__":
    # self-check: determinism, seekability and the readable-by budgets text_readtime_check assumes
    assert headline(0.15, 2.0)["alpha"] >= 0.9, "headline must be readable by 0.15 s"
    assert panel_alpha(0.17, 2.0) >= 0.9, "panel must be readable by 0.17 s"
    assert abs(panel(3.0) - 1.0) < 1e-3 and max(panel(k / 100) for k in range(100)) < 1.12
    assert camera_ease(0) == 0 and camera_ease(1) == 1 and camera_ease(0.5) == 0.5
    assert mascot(1.234, 7) == mascot(1.234, 7) and mascot(1.234, 7) != mascot(1.234, 8)
    keys = [[0.0, 0.3], [1.0, 0.3], [2.0, 0.6]]
    assert abs(camera_path(keys, 1.5) - 0.45) < 1e-9
    peak = max(panel(k / 200) for k in range(200))
    print(f"motion_tokens OK: panel overshoot {100 * (peak - 1):.1f} %, headline alpha@0.15 "
          f"{headline(0.15, 2)['alpha']:.2f}, panel alpha@0.17 {panel_alpha(0.17, 2):.2f}")
