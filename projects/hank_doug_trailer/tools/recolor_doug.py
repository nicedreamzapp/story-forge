#!/usr/bin/env python3
"""recolor_doug.py — code colour-lock for Doug (continuity: one solid russet-red coat, no black saddle).
Krea paints the bloodhound caramel with a black saddle no matter how the string is worded (look test r1, r2, and
C_bench s1102/s1103). Rather than more prompt words, the finished still is corrected in place: inside a hand-named
region, caramel/tan pixels are pulled to russet red and the black saddle to dark russet; the nose (a named point) and
the collar stay. Brushwork is untouched (hue/sat/value only), so the grey and colour states stay the same pixels.
  recolor_doug.py STILL.png OUT.png x0 y0 x1 y1 nose_x nose_y [--collar x0 y0 x1 y1]   (pixel coords of the still)
"""
import sys, numpy as np, cv2
from pathlib import Path

def recolor(img, box, nose, collar=None, russet_h=8.0):
    x0, y0, x1, y1 = box
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)   # H 0..180, S 0..255, V 0..255
    H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    region = np.zeros(img.shape[:2], np.float32); region[y0:y1, x0:x1] = 1.0
    region = cv2.GaussianBlur(region, (0, 0), 6)
    # keep the nose black and the collar as it is
    yy, xx = np.mgrid[0:img.shape[0], 0:img.shape[1]]
    keep = np.exp(-(((xx - nose[0]) ** 2 + (yy - nose[1]) ** 2) / (2 * 22.0 ** 2)))
    if collar:
        cx0, cy0, cx1, cy1 = collar; keep[cy0:cy1, cx0:cx1] = 1.0
    region = region * (1 - keep)
    # caramel / tan: hue 8..30 (OpenCV units), some saturation, not too dark -> russet red
    tan = np.clip((S - 40) / 60, 0, 1) * np.clip((V - 60) / 60, 0, 1) * np.clip(1 - np.abs(H - 19) / 14, 0, 1)
    # black saddle: dark and unsaturated (or bluish-dark) -> dark russet
    blk = np.clip((70 - V) / 40, 0, 1) * np.clip((140 - S) / 100, 0, 1)
    a_tan = tan * region; a_blk = blk * region
    H2 = H * (1 - a_tan) + russet_h * a_tan
    S2 = S * (1 - a_tan) + np.minimum(255, S * 1.35 + 30) * a_tan
    V2 = V * (1 - a_tan) + V * 0.88 * a_tan
    H2 = H2 * (1 - a_blk) + russet_h * a_blk
    S2 = S2 * (1 - a_blk) + 190 * a_blk
    V2 = V2 * (1 - a_blk) + np.clip(V * 1.9 + 45, 0, 150) * a_blk
    out = cv2.cvtColor(np.stack([H2 % 180, np.clip(S2, 0, 255), np.clip(V2, 0, 255)], -1).astype(np.uint8), cv2.COLOR_HSV2BGR)
    return out

if __name__ == "__main__":
    a = sys.argv
    src, dst = a[1], a[2]
    box = tuple(int(v) for v in a[3:7]); nose = (int(a[7]), int(a[8]))
    collar = None
    if "--collar" in a:
        i = a.index("--collar"); collar = tuple(int(v) for v in a[i + 1:i + 5])
    img = cv2.imread(src)
    out = recolor(img, box, nose, collar)
    cv2.imwrite(dst, out)
    print("recolored ->", dst)
