"""Track path, canyon terrain function, train placement and train-scene shot list (shared by build_train.py and shots.py)."""
import math
from mathutils import Vector, noise

RAIL_END_X = -0.3       # near rails stop here (rim is at x = 0 on the track line)
FAR_RAIL_X = 28.3       # far rails start here (far rim at x = 28)
S1, R_ARC, PHI = 170.0, 260.0, math.radians(70)
RAIL_Y = 0.754          # rail head centre lateral offset
RAIL_TOP = 0.56
MACRO = Vector((-35.0, 28.0))


def ss(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def heading(s):
    if s <= S1:
        return Vector((1.0, 0.0))
    phi = min(s - S1, R_ARC * PHI) / R_ARC
    return Vector((math.cos(phi), -math.sin(phi)))


def P(s):
    """near-track centreline at distance s back from the rail end (s<0 extrapolates over the gap)"""
    if s <= S1:
        return Vector((RAIL_END_X - s, 0.0))
    if s <= S1 + R_ARC * PHI:
        phi = (s - S1) / R_ARC
        cx, cy = RAIL_END_X - S1, R_ARC
        return Vector((cx - R_ARC * math.sin(phi), cy - R_ARC * math.cos(phi)))
    se = S1 + R_ARC * PHI
    return P(se) - heading(se) * (s - se)


def track_dist(x, y):
    d = 1e9
    if RAIL_END_X - S1 <= x <= 2.0 or x >= FAR_RAIL_X - 2:
        d = abs(y)
    cx, cy = RAIL_END_X - S1, R_ARC
    phi = math.atan2(-(x - cx), -(y - cy))
    if 0 <= phi <= PHI:
        d = min(d, abs(math.hypot(x - cx, y - cy) - R_ARC))
    se = S1 + R_ARC * PHI
    pe, hd = P(se), heading(se)
    v = Vector((x, y)) - pe
    t = -v.dot(hd)
    if t >= 0:
        d = min(d, abs(v.x * hd.y - v.y * hd.x))
    return d


def rims(y):
    f = ss(8, 60, abs(y))
    wide = ss(70, 320, abs(y)) * 25
    xn = -f * (4.0 + 4.0 * noise.noise(Vector((y / 37.0, 0.5, 0.0))) + wide)
    xf = 28.0 + f * (4.0 + 4.0 * noise.noise(Vector((y / 33.0, 4.5, 0.0))) + wide)
    return xn, xf


def dunes(x, y, amp=1.0):
    return amp * (0.9 * noise.noise(Vector((x / 45.0, y / 45.0, 0.3))) + 0.18 * noise.noise(Vector((x / 9.0, y / 9.0, 1.7))))


def h_train(x, y):
    base = dunes(x, y, 1.5) * ss(3.0, 40.0, track_dist(x, y)) * ss(2.0, 25.0, abs(x - 14) - 14)
    xn, xf = rims(y)
    if xn < x < xf:
        d = min(x - xn, xf - x)
        t = min(1.0, d / 9.0)
        depth = 115.0 * (t ** 0.45) + 5.0 * math.sin(t * math.pi * 5) * t * (1 - t)
        return base - depth + 3.0 * t * noise.noise(Vector((x / 6.0, y / 6.0, 9.0)))
    return base


# ------------------------------------------------------------------ train placement
VEHICLES = [("loco", 0.0, 1.9), ("tender", -6.3, 1.5)] + [(f"car{k + 1}", -14.3 - 10.4 * k, 3.5) for k in range(4)]


def place_train(s0):
    import bpy
    for name, off, wb in VEHICLES:
        ob = bpy.data.objects[name]
        sc_ = s0 - off
        pf, pr = P(sc_ - wb), P(sc_ + wb)
        c = (pf + pr) / 2
        ob.location = (c.x, c.y, RAIL_TOP)
        ob.rotation_euler = (0, 0, math.atan2(pf.y - pr.y, pf.x - pr.x))


# ------------------------------------------------------------------ shots
def train_shots():
    T = ("ants_river", "ants_bridge", "ants_macro")
    sh = {}
    sh["B07_train_wheels"] = dict(cam=(-59.2, -2.55, 0.5), tgt=(-61.0, -0.6, 0.95), lens=28, fstop=4.0, focus=2.4,
                                  hide=T, setup=lambda: place_train(60.0))
    sh["B17_train_wide"] = dict(cam=(-248, -40, 18), tgt=(-200, 10, 0), lens=30, hide=T, setup=lambda: place_train(215.0))
    sh["B18_track_end"] = dict(cam=(-3.2, 0.0, 4.6), tgt=(14.0, 0.0, -7.5), lens=14, hide=T + ("train",))
    sh["B31_wheels_edge"] = dict(cam=(-3.6, -3.4, 2.2), tgt=(1.0, 0.4, -0.8), lens=20, fstop=8.0, focus=4.2,
                                 hide=T, setup=lambda: place_train(4.3))
    sh["B27_whistle"] = dict(cam=(-61.9, -0.55, 4.55), tgt=(-60.0, 0.05, 4.45), lens=24, fstop=4.0, focus=1.0,
                             hide=T, setup=lambda: place_train(60.0))
    mx, my = MACRO
    sh["B21_ground"] = dict(cam=(mx - 0.95, my + 0.05, 0.3 + h_train(mx - 0.95, my)), tgt=(mx + 0.35, my + 0.1, h_train(mx, my) + 0.02),
                            lens=40, fstop=2.8, focus=1.05, hide=("ants_river", "ants_bridge", "train"))
    sh["B22_ant_river"] = dict(cam=(-16.0, 10.0, 7.0), tgt=(-10.0, -5.0, -0.5), lens=24, hide=("ants_macro", "train"))
    sh["B23_ant_macro"] = dict(cam=(mx - 0.62, my + 1.92, 0.2 + h_train(mx - 0.62, my + 1.9)), tgt=(mx + 0.9, my + 1.5, h_train(mx, my + 1.6) + 0.03),
                               lens=30, fstop=3.2, focus=0.72, hide=("ants_river", "ants_bridge", "train"))
    sh["B24_ant_bridge"] = dict(cam=(10.0, -24, 5.0), tgt=(13.0, 0, -1.4), lens=28, hide=("ants_macro", "train"))
    return sh
