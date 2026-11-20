#!/usr/bin/env python3
"""Camera path for the "v5-dive" shot (uses the same scene.bin as the product shot).

15 s drone-style move: low on the table looking up, rise to the drip tip, dive down the bore with a slow
roll, out through the top cap into the chamber, settle over the ceramic cup while the heater warms and
vapor rises. Writes cameras_dive.txt; per line:
  e0(3) t0(3) e1(3) t1(3) focus_mm focal_mm fstop up(3) heat exposure
"""
import math, sys
import numpy as np

FPS, DUR, SHUTTER = 24, 15.0, 0.5
W, H, SENSOR = 1920, 1080, 36.0

# keyframes: time, eye, target, focal mm, f-stop, roll deg   (V5 axis is x=z=0; tip top y=71.8, cup rim 38.1)
K = [
    (0.0,  (-78.0,  6.0, 118.0), (0.0, 40.0, 0.0), 22.0, 2.8,  0.0),
    (3.5,  (-52.0, 26.0,  70.0), (0.0, 50.0, 0.0), 22.0, 2.8,  4.0),
    (6.5,  (-16.0, 96.0,  26.0), (0.0, 70.0, 0.0), 22.0, 4.0,  8.0),
    (8.6,  ( -0.6, 98.0,   3.0), (0.0, 70.0, 0.0), 18.0, 16.0, 10.0),
    (10.2, ( -0.1, 76.0,   0.3), (0.0, 40.0, 0.0), 16.0, 40.0, 20.0),
    (12.2, (  0.0, 47.5,   0.2), (1.8, 36.0, -1.8), 16.0, 40.0, 40.0),
    (15.0, ( -6.5, 43.6,   6.0), (2.5, 35.0, -2.5), 16.0, 32.0, 30.0),
]


def hermite(t, key_i):
    """Non-uniform Catmull-Rom over keyframe values, zero velocity at both ends."""
    ts = [k[0] for k in K]
    i = max(0, min(len(K) - 2, int(np.searchsorted(ts, t, side='right') - 1)))
    t0, t1 = ts[i], ts[i + 1]
    P = [np.atleast_1d(np.array(k[key_i], float)) for k in K]

    def tangent(j):
        if j == 0 or j == len(K) - 1:
            return np.zeros_like(P[j])
        return (P[j + 1] - P[j - 1]) / (ts[j + 1] - ts[j - 1])
    h = t1 - t0; s = (t - t0) / h
    h00 = 2 * s**3 - 3 * s**2 + 1; h10 = s**3 - 2 * s**2 + s; h01 = -2 * s**3 + 3 * s**2; h11 = s**3 - s**2
    return h00 * P[i] + h10 * h * tangent(i) + h01 * P[i + 1] + h11 * h * tangent(i + 1)


def cam(t):
    t = min(max(t, 0.0), DUR)
    eye, tgt = hermite(t, 1), hermite(t, 2)
    # keep the eye on the bore axis once it is inside the tip (bore radius 4.9 mm, tube 4.2 mm)
    if eye[1] < 74.0 and math.hypot(eye[0], eye[2]) < 8.0:
        k = min(1.0, (74.0 - eye[1]) / 4.0)
        eye[0] *= (1 - 0.8 * k); eye[2] *= (1 - 0.8 * k)
    return eye, tgt, float(hermite(t, 3)[0]), float(hermite(t, 4)[0]), math.radians(float(hermite(t, 5)[0]))


def up_vector(eye, tgt, roll):
    fw = tgt - eye; fw /= np.linalg.norm(fw)
    # blend the reference up from world +y toward -z as the camera tips to look straight down (no flip)
    down = max(0.0, -fw[1])
    w = min(1.0, max(0.0, (down - 0.75) / 0.2))
    ref = (1 - w) * np.array([0, 1.0, 0]) + w * np.array([0, 0, -1.0])
    rt = np.cross(fw, ref); rt /= np.linalg.norm(rt)
    up = np.cross(rt, fw)
    return math.cos(roll) * up + math.sin(roll) * rt


def heat(t):          # heater warms from 9 s to 14 s
    s = min(1.0, max(0.0, (t - 9.0) / 5.0))
    return s * s * (3 - 2 * s)


def main():
    n = int(DUR * FPS)
    with open('cameras_dive.txt', 'w') as f:
        f.write(f"{W} {H} {n} 22.0 {SENSOR} 2.8\n")
        for i in range(n):
            ta = i / FPS; tb = ta + SHUTTER / FPS
            e0, g0, focal, fstop, roll = cam(ta)
            e1, g1, _, _, _ = cam(tb)
            # focus pull: on the V5 surface ahead (outside), then on the far end of the bore / the cup inside
            if ta < 9.0:
                focus = max(20.0, float(np.linalg.norm(g0 - e0)) - 12.0)
            else:
                focus = max(6.0, e0[1] - 33.0)
            up = up_vector(e0, g0, roll)
            expo = 1.0 - 0.5 * heat(ta)   # open up as we go inside
            f.write(' '.join(f'{x:.5f}' for x in (*e0, *g0, *e1, *g1, focus, focal, fstop, *up, heat(ta), expo)) + '\n')
    print(f'dive: {n} cameras')


if __name__ == '__main__':
    main()
