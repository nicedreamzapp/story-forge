#!/usr/bin/env python3
"""v2 assembler: HARD-CUT viseme images on the Rhubarb timeline (no ghosting),
all mouths are 3D-style Flux inpaints (incl. closed). Gentle idle motion."""
import os, math
from PIL import Image

HERE=os.path.dirname(os.path.abspath(__file__)); FPS=24
FR=os.path.join(HERE,"frames_flux2"); os.makedirs(FR,exist_ok=True)
for f in os.listdir(FR):
    if f.endswith(".png"): os.remove(os.path.join(FR,f))

IMG={}
for v in ["X","B","C","D","E","F","G","H"]:
    IMG[v]=Image.open(os.path.join(HERE,f"art/m_{v}.png")).convert("RGB")
IMG["A"]=IMG["X"]
W,Hh=IMG["X"].size
bgcol=IMG["X"].getpixel((6,6))

tl=[(float(l.split("\t")[0]),l.strip().split("\t")[1]) for l in open(os.path.join(HERE,"visemes.tsv"))]
DUR=tl[-1][0]; NF=int(DUR*FPS)
def vis_at(t):
    cur="X"
    for tt,sh in tl:
        if tt<=t: cur=sh
        else: break
    return cur

for i in range(NF):
    t=i/FPS
    img=IMG.get(vis_at(t),IMG["X"])
    dy=int(3*math.sin(t*2.0)); dx=int(4*math.sin(t*0.7))   # gentle idle
    canv=Image.new("RGB",(W,Hh),bgcol); canv.paste(img,(dx,dy))
    canv.save(os.path.join(FR,f"f_{i:04d}.png"))
print(f"rendered {NF} frames ({DUR:.1f}s), hard-cut")
