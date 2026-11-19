#!/usr/bin/env python3
"""doug_hue_v5.py — plan_v5 B1 colour measure. Median coat hue (degrees, HSV) of saturated, not-dark pixels in a Doug box,
plus the dark-saddle fraction. Usage: doug_hue_v5.py IMG x0 y0 x1 y1 [saddle x0 y0 x1 y1]"""
import sys, numpy as np, cv2
a = sys.argv; img = cv2.imread(a[1]); x0, y0, x1, y1 = map(int, a[2:6])
hsv = cv2.cvtColor(img[y0:y1, x0:x1], cv2.COLOR_BGR2HSV).astype(np.float32)
H, S, V = hsv[..., 0] * 2, hsv[..., 1] / 255, hsv[..., 2] / 255
coat = (S > 0.35) & (V > 0.30) & ((H < 50) | (H > 340))
h = np.where(H[coat] > 180, H[coat] - 360, H[coat])
out = f"median coat hue {np.median(h):5.1f} deg  (n={coat.sum()}, {coat.mean()*100:.0f}% of box)  median S {np.median(S[coat]):.2f} V {np.median(V[coat]):.2f}"
if len(a) > 6:
    s0, t0, s1, t1 = map(int, a[7:11]); hs = cv2.cvtColor(img[t0:t1, s0:s1], cv2.COLOR_BGR2HSV).astype(np.float32)
    dark = (hs[..., 2] / 255 < 0.28).mean(); out += f"  saddle dark fraction {dark*100:.0f}%"
print(out)
