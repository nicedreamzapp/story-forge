#!/usr/bin/env python3
"""doug_box_v5.py — push-button Doug colour measure for the v5 klein gate (CPU only).
Finds Doug automatically: the largest blob of warm saturated pixels (his russet coat), pads it, measures the median
coat hue (same formula as doug_hue_v5.py) and the dark fraction of the saddle box (upper middle of the Doug box).
Usage: doug_box_v5.py IMG [--box x0 y0 x1 y1] [--json]   -> prints hue, dark %, box; --json for the runner."""
import sys, json, numpy as np, cv2
a = sys.argv[1:]; img = cv2.imread(a[0]); H0, W0 = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
H, S, V = hsv[..., 0] * 2, hsv[..., 1] / 255, hsv[..., 2] / 255
warm = ((S > 0.35) & (V > 0.30) & ((H < 45) | (H > 340))).astype(np.uint8)
if "--box" in a:
    i = a.index("--box"); x0, y0, x1, y1 = map(int, a[i + 1:i + 5])
else:
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    m = cv2.morphologyEx(cv2.morphologyEx(warm, cv2.MORPH_OPEN, k), cv2.MORPH_CLOSE, k)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n < 2: print(json.dumps({"error": "no warm blob"})); sys.exit(1)
    j = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    x, y, w, h = st[j, :4]; px, py = int(w * 0.06), int(h * 0.06)
    x0, y0, x1, y1 = max(0, x - px), max(0, y - py), min(W0, x + w + px), min(H0, y + h + py)
box = (slice(y0, y1), slice(x0, x1))
coat = warm[box].astype(bool)
hh = H[box][coat]; hh = np.where(hh > 180, hh - 360, hh)
sx0, sx1 = x0 + int((x1 - x0) * 0.15), x0 + int((x1 - x0) * 0.85)
sy0, sy1 = y0, y0 + int((y1 - y0) * 0.45)
dark = float((V[sy0:sy1, sx0:sx1] < 0.28).mean())
out = {"img": a[0], "box": [int(x0), int(y0), int(x1), int(y1)], "saddle_box": [sx0, sy0, sx1, sy1],
       "hue": round(float(np.median(hh)), 1) if hh.size else None, "coat_px": int(coat.sum()), "coat_pct": round(float(coat.mean() * 100), 1),
       "sat": round(float(np.median(S[box][coat])), 2) if hh.size else None, "dark_pct": round(dark * 100, 1)}
print(json.dumps(out) if "--json" in a else f"{a[0]}: hue {out['hue']} deg  coat {out['coat_pct']}% of box  S {out['sat']}  saddle dark {out['dark_pct']}%  box {out['box']}")
