"""fix_still_v4.py SRC DST --paint x0 y0 x1 y1 sx0 [--paint ...] --doug x0 y0 x1 y1 nx ny [cx0 cy0 cx1 cy1]
--paint: clone the same-height strip starting at column sx0 over the box (lantern paint-out, soft left edge)
--doug: gentle hue-only recolor (no saturation boost) inside the box, nose point kept, optional collar box kept"""
import sys, cv2, numpy as np
a = sys.argv; src, dst = a[1], a[2]; im = cv2.imread(src)
i = 3
while i < len(a):
    if a[i] == "--paint":
        x0, y0, x1, y1, sx0 = map(int, a[i+1:i+6]); w = x1 - x0
        s = im[y0:y1, sx0:sx0+w].astype(np.float32); d = im[y0:y1, x0:x1].astype(np.float32)
        m = np.ones((y1-y0, w, 1), np.float32); m[:, :10] = np.linspace(0, 1, 10)[None, :, None]
        if x1 < im.shape[1]: m[:, -10:] = np.linspace(1, 0, 10)[None, :, None]
        im[y0:y1, x0:x1] = (d*(1-m) + s*m).astype(np.uint8); i += 6
    elif a[i] == "--doug":
        x0, y0, x1, y1, nx, ny = map(int, a[i+1:i+7]); i += 7
        collar = None
        if i < len(a) and a[i] != "--paint" and a[i] != "--doug": collar = tuple(map(int, a[i:i+4])); i += 4
        hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(np.float32); H, S, V = hsv[...,0], hsv[...,1], hsv[...,2]
        reg = np.zeros(im.shape[:2], np.float32); reg[y0:y1, x0:x1] = 1; reg = cv2.GaussianBlur(reg, (0,0), 6)
        yy, xx = np.mgrid[0:im.shape[0], 0:im.shape[1]]; reg *= 1 - np.exp(-(((xx-nx)**2 + (yy-ny)**2)/(2*22.0**2)))
        if collar: reg[collar[1]:collar[3], collar[0]:collar[2]] = 0
        tan = np.clip((S-40)/60,0,1)*np.clip((V-60)/60,0,1)*np.clip(1-np.abs(H-19)/14,0,1)*reg
        blk = np.clip((70-V)/40,0,1)*np.clip((140-S)/100,0,1)*reg
        H2 = H*(1-tan)+11*tan; S2 = S*(1-tan)+np.minimum(255,S*1.08)*tan; V2 = V*(1-tan)+V*0.93*tan
        H2 = H2*(1-blk)+11*blk; S2 = S2*(1-blk)+150*blk; V2 = V2*(1-blk)+np.clip(V*1.5+35,0,110)*blk
        im = cv2.cvtColor(np.stack([H2%180, np.clip(S2,0,255), np.clip(V2,0,255)],-1).astype(np.uint8), cv2.COLOR_HSV2BGR)
    else: i += 1
cv2.imwrite(dst, im); print("->", dst)
