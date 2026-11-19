#!/usr/bin/env python3
"""recolor_box_v52.py SRC OUT x0 y0 x1 y1 [target_hue=20] — still-stage recolour of Doug's coat inside ONE box: warm saturated
pixels (his tan/orange coat) are pulled to the master's russet hue, saturated a little and darkened a little; nothing outside the box
or outside the coat mask changes; the mask is feathered. Done on the STILL before LTX (the v4 per-frame recolour went olive in motion;
a one-time recolour of the keyframe keeps one colour through the clip). Three klein attempts on this shot repainted the cow/bear instead."""
import sys, numpy as np, cv2
src, out = sys.argv[1], sys.argv[2]; x0, y0, x1, y1 = map(int, sys.argv[3:7]); TH = float(sys.argv[7]) if len(sys.argv) > 7 else 20.0
img = cv2.imread(src); hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
H, S, V = hsv[..., 0] * 2, hsv[..., 1] / 255, hsv[..., 2] / 255
m = np.zeros(H.shape, np.float32); sub = (S[y0:y1, x0:x1] > 0.30) & (V[y0:y1, x0:x1] > 0.28) & (H[y0:y1, x0:x1] > 8) & (H[y0:y1, x0:x1] < 48)
m[y0:y1, x0:x1] = sub.astype(np.float32); m = cv2.GaussianBlur(m, (0, 0), 2.5)
H2 = TH + 0.25 * (H - TH); S2 = np.clip(S * 1.3 + 0.05, 0, 1); V2 = V * 0.78
hsv2 = np.stack([np.clip(H2 / 2, 0, 179), S2 * 255, V2 * 255], -1).astype(np.uint8); bgr2 = cv2.cvtColor(hsv2, cv2.COLOR_HSV2BGR).astype(np.float32)
res = img.astype(np.float32) * (1 - m[..., None]) + bgr2 * m[..., None]; cv2.imwrite(out, res.astype(np.uint8)); print("->", out, "coat pixels", int(sub.sum()))
