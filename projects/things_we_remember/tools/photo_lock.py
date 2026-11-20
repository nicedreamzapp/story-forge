#!/usr/bin/env python3
"""Make the man in all 8 era photos the SAME man: canon face = the man in s09_1; every adult male face whose top sits
near the highest male face in a photo gets the canon identity (inswapper_128). Originals kept as stills/s09_k_raw.png."""
import cv2, shutil, numpy as np, insightface
from pathlib import Path
from insightface.app import FaceAnalysis
P = Path(__file__).resolve().parent.parent / "stills"
app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"]); app.prepare(ctx_id=0, det_size=(640, 640))
sw = insightface.model_zoo.get_model(str(Path.home() / ".insightface/models/inswapper_128.onnx"), providers=["CPUExecutionProvider"])
src = cv2.imread(str(P / "s09_1.png")); canon = max(app.get(src), key=lambda f: (f.bbox[3] - f.bbox[1]) * (f.gender == 1))
for k in range(2, 9):
    raw = P / f"s09_{k}_raw.png"
    if not raw.exists(): shutil.copy(P / f"s09_{k}.png", raw)
    im = cv2.imread(str(raw)); fs = [f for f in app.get(im) if f.gender == 1 and f.age > 25]
    if not fs: print(k, "no male face"); continue
    top = min(f.bbox[1] for f in fs); H = im.shape[0]; n = 0
    for f in fs:
        if f.bbox[1] - top < .08 * H: im = sw.get(im, f, canon, paste_back=True); n += 1
    cv2.imwrite(str(P / f"s09_{k}.png"), im); print(k, "swapped", n)
