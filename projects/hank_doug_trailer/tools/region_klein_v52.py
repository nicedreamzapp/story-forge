#!/usr/bin/env python3
"""region_klein_v52.py SRC.png OUT.png x0 y0 x1 y1 "PROMPT" [REF.png] — klein edit of ONE region of a still, pasted back with a
feathered edge (the 11/18 2:35 PM lesson: a full-frame klein 'repaint only the dog' bled red onto the cow). The crop is padded to a
multiple of 16, edited by FLUX.2 klein 9B (mflux), then blended back over 24 px. Still-stage work, before animation; not a cutout in motion."""
import sys, subprocess, numpy as np
from PIL import Image
src, out, x0, y0, x1, y1, prompt = sys.argv[1], sys.argv[2], *map(int, sys.argv[3:7]), sys.argv[7]; ref = sys.argv[8] if len(sys.argv) > 8 else None
im = Image.open(src).convert("RGB"); W, H = im.size
w, h = x1 - x0, y1 - y0; w16, h16 = (w + 15) // 16 * 16, (h + 15) // 16 * 16; x1, y1 = min(W, x0 + w16), min(H, y0 + h16); x0, y0 = x1 - w16, y1 - h16
crop = im.crop((x0, y0, x1, y1)); crop.save("/tmp/rk_crop.png")
cmd = [f"{__import__('os').environ['HOME']}/mflux-venv/bin/mflux-generate-flux2-edit", "--model", "flux2-klein-9b", "--image-paths", "/tmp/rk_crop.png"] + ([ref] if ref else []) + ["--prompt", prompt, "--steps", "4", "--guidance", "1.0", "--seed", "1", "--output", "/tmp/rk_edit.png"]
subprocess.run(cmd, check=True, capture_output=True)
ed = Image.open("/tmp/rk_edit.png").convert("RGB").resize((w16, h16), Image.LANCZOS)
a = np.array(crop, np.float32); b = np.array(ed, np.float32); f = 24
m = np.ones((h16, w16), np.float32); r = np.linspace(0, 1, f)
m[:f] *= r[:, None]; m[-f:] *= r[::-1][:, None]; m[:, :f] *= r[None, :]; m[:, -f:] *= r[::-1][None, :]
blend = a * (1 - m[..., None]) + b * m[..., None]
res = im.copy(); res.paste(Image.fromarray(blend.astype(np.uint8)), (x0, y0)); res.save(out); print("->", out, (x0, y0, x1, y1))
