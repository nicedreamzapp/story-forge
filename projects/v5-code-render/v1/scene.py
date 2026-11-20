#!/usr/bin/env python3
"""Procedural scene for the V5 code-rendered product shot.

Everything here is built from triangles in code: no downloaded models or textures.
Units are millimetres, +Y is up, the V5 stands at the origin on the table top (y=0).

The V5 profile is measured from the ineedhemp.com main product photo
(reference/img0.jpg, 1600x1600, centre line x=810). PX converts photo pixels to mm.
Output: scene.bin  (header + float32 verts/normals + uint32 tris + uint32 material ids)
        cameras.txt (one line per frame: shutter-open and shutter-close camera)
"""
import math, struct, sys
import numpy as np

# ---------------- materials (must match the ids in pt.metal) ----------------
M_STEEL, M_STEEL_POLISH, M_STEEL_DARK, M_GLASS, M_CERAMIC, M_WOOD, M_WALL, M_LIGHT, M_FRAME = range(9)

PX = 0.07          # mm per photo pixel (body = 410 px ~ 28.7 mm across)
Y_BOTTOM_PX = 1300  # bottom of the 510 pin in the photo


def ypx(p):
    return (Y_BOTTOM_PX - p) * PX


def rpx(p):
    return p * PX


class Mesh:
    def __init__(self):
        self.v, self.n, self.t, self.m = [], [], [], []
        self.nv = 0

    def add(self, verts, norms, tris, mat):
        verts = np.asarray(verts, np.float32).reshape(-1, 3)
        norms = np.asarray(norms, np.float32).reshape(-1, 3)
        tris = np.asarray(tris, np.uint32).reshape(-1, 3)
        self.v.append(verts); self.n.append(norms)
        self.t.append(tris + self.nv)
        self.m.append(np.full(len(tris), mat, np.uint32))
        self.nv += len(verts)

    def add_flat(self, tri_verts, mat):
        """tri_verts: (N,3,3) -> faceted triangles with their own normals."""
        tv = np.asarray(tri_verts, np.float32).reshape(-1, 3, 3)
        fn = np.cross(tv[:, 1] - tv[:, 0], tv[:, 2] - tv[:, 0])
        fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
        norms = np.repeat(fn[:, None, :], 3, axis=1)
        self.add(tv.reshape(-1, 3), norms.reshape(-1, 3), np.arange(len(tv) * 3).reshape(-1, 3), mat)

    def quad(self, a, b, c, d, mat):
        self.add_flat([[a, b, c], [a, c, d]], mat)

    def box(self, lo, hi, mat):
        x0, y0, z0 = lo; x1, y1, z1 = hi
        P = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        for f in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 4, 7, 3), (1, 2, 6, 5), (3, 7, 6, 2), (0, 1, 5, 4)]:
            self.quad(*[P[i] for i in f], mat)


# ---------------- lathe (surface of revolution) ----------------
def lathe(mesh, prof, mat, seg=360, cut=None, flip=False):
    """prof: list of (r, y) going around the outline. Smooth normals from the 2D profile.
    cut(theta, y) -> True removes that quad (used for the window openings)."""
    prof = np.asarray(prof, np.float64)
    n = len(prof)
    # 2D tangents -> normals (pointing outward for a profile walked bottom->top on the outside)
    tang = np.zeros_like(prof)
    tang[1:-1] = prof[2:] - prof[:-2]
    tang[0] = prof[1] - prof[0]; tang[-1] = prof[-1] - prof[-2]
    # split normals at sharp corners: duplicate rows per segment instead
    th = np.linspace(0, 2 * math.pi, seg + 1)
    cs, sn = np.cos(th), np.sin(th)
    verts, norms, tris = [], [], []
    vid = 0
    for i in range(n - 1):
        (r0, y0), (r1, y1) = prof[i], prof[i + 1]
        dr, dy = r1 - r0, y1 - y0
        L = math.hypot(dr, dy)
        if L < 1e-9:
            continue
        nr, ny = dy / L, -dr / L
        if flip:
            nr, ny = -nr, -ny
        base = vid
        for j in range(seg + 1):
            for (r, y) in ((r0, y0), (r1, y1)):
                verts.append((r * cs[j], y, r * sn[j]))
                norms.append((nr * cs[j], ny, nr * sn[j]))
                vid += 1
        for j in range(seg):
            if cut is not None:
                tm = 0.5 * (th[j] + th[j + 1]); ym = 0.5 * (y0 + y1)
                if cut(tm, ym):
                    continue
            a = base + 2 * j; b = a + 1; c = a + 3; d = a + 2
            if flip:
                tris += [(a, c, b), (a, d, c)]
            else:
                tris += [(a, b, c), (a, c, d)]
    mesh.add(verts, norms, tris, mat)


def smooth_lathe(mesh, prof, mat, seg=360, flip=False):
    """Like lathe() but with one smooth normal per profile vertex (for rounded parts)."""
    prof = np.asarray(prof, np.float64)
    n = len(prof)
    nrm = np.zeros_like(prof)
    for i in range(n):
        a = prof[max(i - 1, 0)]; b = prof[min(i + 1, n - 1)]
        d = b - a; L = np.hypot(*d) + 1e-12
        nrm[i] = (d[1] / L, -d[0] / L)
    if flip:
        nrm = -nrm
    th = np.linspace(0, 2 * math.pi, seg + 1)
    verts, norms, tris = [], [], []
    for i in range(n):
        for j in range(seg + 1):
            c, s = math.cos(th[j]), math.sin(th[j])
            verts.append((prof[i][0] * c, prof[i][1], prof[i][0] * s))
            norms.append((nrm[i][0] * c, nrm[i][1], nrm[i][0] * s))
    W = seg + 1
    for i in range(n - 1):
        for j in range(seg):
            a = i * W + j; b = (i + 1) * W + j; c = b + 1; d = a + 1
            tris += [(a, b, c), (a, c, d)] if not flip else [(a, c, b), (a, d, c)]
    mesh.add(verts, norms, tris, mat)


def groove_profile(r, y_lo, y_hi, grooves, depth, width):
    """Straight cylinder of radius r from y_lo..y_hi (bottom->top) with V-ish grooves."""
    pts = [(r, y_lo)]
    for gy in sorted(grooves):
        pts += [(r, gy - width / 2), (r - depth, gy - width / 4), (r - depth, gy + width / 4), (r, gy + width / 2)]
    pts.append((r, y_hi))
    return pts


# ---------------- the V5 ----------------
def build_v5(mesh, rot):
    R_BODY = rpx(205)
    # window geometry: two windows 180 deg apart, half-angle 36.5 deg, photo y 600..860, corner r 30px
    WIN_Y0, WIN_Y1 = ypx(860), ypx(600)
    WIN_HALF = math.radians(36.5)
    CORNER = rpx(30)

    def in_window(theta, y):
        for c in (rot, rot + math.pi):
            d = (theta - c + math.pi) % (2 * math.pi) - math.pi
            u = abs(d) * R_BODY            # arc length from the window centre
            hu = WIN_HALF * R_BODY
            if abs(u) <= hu and WIN_Y0 <= y <= WIN_Y1:
                # rounded corners
                cx = hu - CORNER; cy0 = WIN_Y0 + CORNER; cy1 = WIN_Y1 - CORNER
                if u > cx and (y < cy0 or y > cy1):
                    cy = cy0 if y < cy0 else cy1
                    if (u - cx) ** 2 + (y - cy) ** 2 > CORNER ** 2:
                        continue
                return True
        return False

    seg = 720
    # 510 pin (dark threaded steel, threads as many small grooves)
    pin = [(0.0, ypx(1300))] + groove_profile(rpx(42), ypx(1300) + 0.3, ypx(1252),
                                             [ypx(1300) + 0.6 + k * 0.45 for k in range(6)], 0.25, 0.35) + [(rpx(70), ypx(1252)), (rpx(70), ypx(1246))]
    lathe(mesh, pin, M_STEEL_DARK, seg=180)

    # base with four fins (bottom of the photo, y 1135..1246)
    fins = [(rpx(70), ypx(1246)), (rpx(185), ypx(1246))]
    fin_bands = [(1246, 1228), (1220, 1202), (1194, 1176), (1168, 1150)]
    groove_r = rpx(168)
    for k, (yb, yt) in enumerate(fin_bands):
        r = rpx(190)
        fins += [(r - 0.25, ypx(yb)), (r, ypx(yb) + 0.25), (r, ypx(yt) - 0.25), (r - 0.25, ypx(yt))]
        nxt = fin_bands[k + 1][0] if k + 1 < len(fin_bands) else 1142
        fins += [(groove_r, ypx(yt)), (groove_r, ypx(nxt))]
    fins += [(rpx(198), ypx(1142)), (rpx(198), ypx(1136)), (rpx(200), ypx(1136))]
    lathe(mesh, fins, M_STEEL, seg=seg)

    # knurled ring (photo y 948..1136): diamond pyramids
    yk0, yk1 = ypx(1134), ypx(950)
    r_out, depth = rpx(207), 0.5
    n_around = 64
    a = math.pi / n_around                 # half angular width of a diamond
    b = (a * r_out)                         # half height -> 45 deg knurl
    rows = int((yk1 - yk0) / b) + 1
    tv = []
    for j in range(-1, rows + 1):
        yc = yk0 + j * b
        for i in range(n_around):
            tc = (2 * i + (j & 1)) * a
            def P(t, y, r):
                return (r * math.cos(t), y, r * math.sin(t))
            rin = r_out - depth
            L = P(tc - a, yc, rin); Rr = P(tc + a, yc, rin)
            B = P(tc, max(yc - b, yk0), rin)
            T = P(tc, min(yc + b, yk1), rin)
            yA = min(max(yc, yk0), yk1)
            A = P(tc, yA, r_out)
            # clip: skip diamonds whose centre is outside the band
            if yc < yk0 - b * 0.5 or yc > yk1 + b * 0.5:
                continue
            Lc = P(tc - a, min(max(yc, yk0), yk1), rin); Rc = P(tc + a, min(max(yc, yk0), yk1), rin)
            tv += [[Lc, A, T], [A, Rc, T], [Lc, B, A], [A, B, Rc]]
    # orientation: make normals face outward
    tv = np.array(tv, np.float32)
    fn = np.cross(tv[:, 1] - tv[:, 0], tv[:, 2] - tv[:, 0])
    cen = tv.mean(axis=1); outward = cen.copy(); outward[:, 1] = 0
    flip = (fn * outward).sum(1) < 0
    tv[flip] = tv[flip][:, [0, 2, 1]]
    mesh.add_flat(tv, M_STEEL_POLISH)
    # inner core under the knurl (so nothing is see-through) + rims
    lathe(mesh, [(rpx(200), ypx(1136)), (r_out - depth, ypx(1136)), (r_out - depth, yk0)], M_STEEL, seg=seg)
    lathe(mesh, [(r_out - depth, yk1), (r_out - depth, ypx(948)), (rpx(203), ypx(946)), (rpx(198), ypx(946))], M_STEEL, seg=seg)

    # steel top: body tube with two windows, grooves near the top, shoulder, neck grooves, drip tip
    t_wall = 1.2
    body_out = [(rpx(198), ypx(946)), (R_BODY - 0.1, ypx(944)), (R_BODY, ypx(943))]
    body_out += groove_profile(R_BODY, ypx(943), ypx(500), [ypx(542), ypx(558), ypx(574)], 0.4, 0.7)[1:]
    # shoulder (photo y 500 -> 470): a shallow cone up to the neck
    body_out += [(R_BODY - 0.25, ypx(497)), (rpx(150), ypx(474)), (rpx(142), ypx(470))]
    # neck cone with three grooves (photo y 470 -> 395)
    neck = []
    for k, (yy, rr) in enumerate([(468, 140), (452, 133), (432, 127), (412, 121)]):
        neck += [(rpx(rr), ypx(yy))]
        if k < 3:
            gy = yy - 9
            neck += [(rpx(rr - 1), ypx(gy + 4)), (rpx(rr - 9), ypx(gy + 2)), (rpx(rr - 9), ypx(gy - 2)), (rpx(rr - 2), ypx(gy - 4))]
    neck += [(rpx(118), ypx(398)), (rpx(112), ypx(396))]
    body_out += neck
    lathe(mesh, body_out, M_STEEL, seg=seg, cut=lambda t, y: in_window(t, y))

    # drip tip (photo y 396 -> 220), polished, rounded lip, bore inside
    r_tip, r_bore = rpx(112), rpx(70)
    lip = [(r_tip, ypx(396)), (r_tip, ypx(232))]
    for k in range(9):
        ang = k / 8 * math.pi / 2
        lip.append((r_tip - 0.8 + 0.8 * math.cos(ang), ypx(232) + 0.8 * math.sin(ang)))
    lip += [(r_bore + 0.6, ypx(220)), (r_bore, ypx(220) - 0.6), (r_bore, ypx(330))]
    smooth_lathe(mesh, lip, M_STEEL_POLISH, seg=seg)
    lathe(mesh, [(r_bore, ypx(330)), (rpx(40), ypx(345)), (0.0, ypx(345))], M_STEEL_DARK, seg=180, flip=True)

    # inner wall of the steel top (window cut too) + window side walls
    r_in = R_BODY - t_wall
    lathe(mesh, [(r_in, ypx(944)), (r_in, ypx(520))], M_STEEL, seg=seg, cut=lambda t, y: in_window(t, y), flip=True)
    # window side walls: sample the window boundary in (u,y) and extrude radially
    for c in (rot, rot + math.pi):
        hu = WIN_HALF * R_BODY
        pts = []
        cx = hu - CORNER
        # walk the rounded rectangle boundary (counter-clockwise in (u,y))
        def arc(cu, cy, a0, a1, n=10):
            return [(cu + CORNER * math.cos(a0 + (a1 - a0) * k / n), cy + CORNER * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]
        pts += arc(cx, WIN_Y0 + CORNER, -math.pi / 2, 0)
        pts += arc(cx, WIN_Y1 - CORNER, 0, math.pi / 2)
        pts += arc(-cx, WIN_Y1 - CORNER, math.pi / 2, math.pi)
        pts += arc(-cx, WIN_Y0 + CORNER, math.pi, 3 * math.pi / 2)
        pts.append(pts[0])
        tv = []
        for (u0, y0), (u1, y1) in zip(pts[:-1], pts[1:]):
            t0, t1 = c + u0 / R_BODY, c + u1 / R_BODY
            A = (R_BODY * math.cos(t0), y0, R_BODY * math.sin(t0)); B = (R_BODY * math.cos(t1), y1, R_BODY * math.sin(t1))
            C = (r_in * math.cos(t1), y1, r_in * math.sin(t1)); D = (r_in * math.cos(t0), y0, r_in * math.sin(t0))
            tv += [[A, B, C], [A, C, D]]
        mesh.add_flat(tv, M_STEEL)

    # glass tube inside the steel top (the replaceable "window")
    g_out, g_in = r_in - 0.05, r_in - 1.6
    lathe(mesh, [(g_out, ypx(905)), (g_out, ypx(575))], M_GLASS, seg=seg)
    lathe(mesh, [(g_in, ypx(905)), (g_in, ypx(575))], M_GLASS, seg=seg, flip=True)
    lathe(mesh, [(g_out, ypx(575)), (g_in, ypx(575))], M_GLASS, seg=seg)   # top cap, normal +y
    lathe(mesh, [(g_in, ypx(905)), (g_out, ypx(905))], M_GLASS, seg=seg)   # bottom cap, normal -y

    # interior: steel ceiling (chimney) above the window, deck below, white ceramic cup in the middle
    lathe(mesh, [(0.0, ypx(560)), (rpx(60), ypx(560)), (rpx(60), ypx(585)), (g_in, ypx(590))], M_STEEL_DARK, seg=seg)
    lathe(mesh, [(g_in, ypx(895)), (0.0, ypx(895))], M_STEEL, seg=seg)
    # ceramic holder + cup (white). Cup top rim at photo y ~700, outer r ~150 px
    cup_r, cup_in = rpx(150), rpx(128)
    cup = [(rpx(170), ypx(895)), (rpx(170), ypx(840)), (cup_r, ypx(838)), (cup_r, ypx(702))]
    for k in range(5):
        ang = k / 4 * math.pi
        cup.append((0.5 * (cup_r + cup_in) + 0.5 * (cup_r - cup_in) * math.cos(ang), ypx(702) + 0.4 * math.sin(ang)))
    cup += [(cup_in, ypx(790)), (0.0, ypx(790))]
    smooth_lathe(mesh, cup, M_CERAMIC, seg=seg)


# ---------------- room ----------------
def build_room(mesh):
    # wooden table top: 900 x 600 mm, 30 mm thick, top surface at y=0 (subdivided so grain normals stay smooth)
    mesh.box((-450, -30, -350), (450, 0, 250), M_WOOD)
    # back wall far behind (soft, out of focus)
    mesh.quad((-2000, -800, -900), (2000, -800, -900), (2000, 1500, -900), (-2000, 1500, -900), M_WALL)
    # side wall with the window opening on the left (x = -700)
    X = -700.0
    wy0, wy1, wz0, wz1 = 60.0, 900.0, -600.0, 300.0
    # wall pieces around the opening
    for (z0, z1, y0, y1) in [(-900, wz0, -800, 1500), (wz1, 1200, -800, 1500), (wz0, wz1, -800, wy0), (wz0, wz1, wy1, 1500)]:
        mesh.quad((X, y0, z0), (X, y0, z1), (X, y1, z1), (X, y1, z0), M_WALL)
    # window mullions (cross bars) cast soft shadows across the table
    for z in (-150.0,):
        mesh.box((X - 40, wy0, z - 18), (X + 10, wy1, z + 18), M_FRAME)
    mesh.box((X - 40, 470, wz0), (X + 10, 500, wz1), M_FRAME)
    # the window light itself: an emitter just outside the opening (sky/daylight)
    L = X - 60
    mesh.quad((L, wy0, wz0), (L, wy1, wz0), (L, wy1, wz1), (L, wy0, wz1), M_LIGHT)
    return (L, wy0, wz0), (0.0, wy1 - wy0, 0.0), (0.0, 0.0, wz1 - wz0)


# ---------------- camera path ----------------
def camera_at(t, cfg):
    """t in seconds. Slow push-in with a slight orbit and handheld drift."""
    T = cfg['duration']
    s = t / T
    e = s * s * (3 - 2 * s)            # ease in/out
    dist = cfg['dist0'] + (cfg['dist1'] - cfg['dist0']) * e
    az = math.radians(cfg['az0'] + (cfg['az1'] - cfg['az0']) * e)
    h = cfg['h0'] + (cfg['h1'] - cfg['h0']) * e
    tgt = np.array(cfg['target'], float)
    eye = tgt + np.array([dist * math.sin(az), h, dist * math.cos(az)])

    def drift(seed):
        return sum(math.sin(t * f * 2 * math.pi + seed * p) * a for f, a, p in ((0.13, 1.0, 1.7), (0.31, 0.5, 2.9), (0.71, 0.18, 4.1)))
    hd = cfg['handheld']
    eye += hd * np.array([drift(1), drift(2), drift(3)])
    tgt = tgt + 0.4 * hd * np.array([drift(4), drift(5), drift(6)])
    return eye, tgt


def main():
    cfg = dict(width=1920, height=1080, fps=24, duration=10.0,
               dist0=210.0, dist1=170.0, az0=-26.0, az1=-6.0, h0=55.0, h1=38.0,
               target=(0.0, 36.0, 0.0), handheld=0.8,
               focal_mm=35.0, sensor_mm=36.0, fstop=4.0, shutter=0.5)
    for a in sys.argv[1:]:
        k, v = a.split('=')
        cfg[k] = type(cfg[k])(v) if not isinstance(cfg[k], tuple) else tuple(float(x) for x in v.split(','))

    mesh = Mesh()
    build_v5(mesh, rot=math.radians(90 + 8))   # window faces the camera (+z), turned a touch like the photo
    light = build_room(mesh)

    V = np.concatenate(mesh.v); N = np.concatenate(mesh.n)
    T = np.concatenate(mesh.t); Mt = np.concatenate(mesh.m)
    with open('scene.bin', 'wb') as f:
        f.write(struct.pack('<III', len(V), len(T), 0))
        f.write(struct.pack('<9f', *light[0], *light[1], *light[2]))
        f.write(V.astype('<f4').tobytes()); f.write(N.astype('<f4').tobytes())
        f.write(T.astype('<u4').tobytes()); f.write(Mt.astype('<u4').tobytes())

    nframes = int(round(cfg['duration'] * cfg['fps']))
    with open('cameras.txt', 'w') as f:
        f.write(f"{cfg['width']} {cfg['height']} {nframes} {cfg['focal_mm']} {cfg['sensor_mm']} {cfg['fstop']}\n")
        for i in range(nframes):
            t0 = i / cfg['fps']; t1 = t0 + cfg['shutter'] / cfg['fps']
            e0, g0 = camera_at(t0, cfg); e1, g1 = camera_at(t1, cfg)
            fd0 = float(np.linalg.norm(np.array(cfg['target']) - e0)) - 13.0   # focus on the front face, not the axis
            f.write(' '.join(f'{x:.5f}' for x in (*e0, *g0, *e1, *g1, fd0)) + '\n')
    print(f'scene: {len(V)} verts, {len(T)} triangles; {nframes} cameras')


if __name__ == '__main__':
    main()
