#!/usr/bin/env python3
"""Talking + MOVING: organic head/body motion (sway, bob, drift, breathe) applied
to the active viseme frame each step, pivoted at the body base so it rocks naturally.
Mouth stays aligned because it's baked into each viseme image. 100% local."""
import os, math
from PIL import Image

HERE=os.path.dirname(os.path.abspath(__file__)); FPS=24
FR=os.path.join(HERE,"frames_move"); os.makedirs(FR,exist_ok=True)
for f in os.listdir(FR):
    if f.endswith(".png"): os.remove(os.path.join(FR,f))

IMG={v:Image.open(os.path.join(HERE,f"art/m_{v}.png")).convert("RGB") for v in ["X","B","C","D","E","F","G","H"]}
IMG["A"]=IMG["X"]
W,Hh=IMG["X"].size
bg=IMG["X"].getpixel((6,6))
PAD=120                                  # padding so motion never reveals hard edges

tl=[(float(l.split("\t")[0]),l.strip().split("\t")[1]) for l in open(os.path.join(HERE,"visemes.tsv"))]
DUR=tl[-1][0]; NF=int(DUR*FPS)
VOPEN={"X":0,"A":0,"B":.2,"G":.2,"F":.3,"E":.4,"C":.6,"H":.6,"D":1.0}
def vis_at(t):
    cur="X"
    for tt,sh in tl:
        if tt<=t: cur=sh
        else: break
    return cur

prev_open=0.0
for i in range(NF):
    t=i/FPS; v=vis_at(t)
    o=VOPEN.get(v,0); prev_open=prev_open*0.6+o*0.4      # smoothed mouth energy
    # organic motion (layered sines = non-repetitive feel)
    ang = 2.6*math.sin(t*2.1) + 1.1*math.sin(t*4.7+1) + 1.4*prev_open*math.sin(t*3.3)
    dx  = 7*math.sin(t*1.4) + 3*math.sin(t*3.1)
    dy  = 8*math.sin(t*2.5) - 10*prev_open                 # lifts/leans in when talking
    sc  = 1.0 + 0.02*math.sin(t*2.9) + 0.025*prev_open     # breathe + emphasis
    frame=IMG.get(v,IMG["X"])
    # scale
    nw,nh=int(W*sc),int(Hh*sc)
    f2=frame.resize((nw,nh), Image.LANCZOS)
    # rotate about lower-body pivot
    f2=f2.rotate(ang, resample=Image.BICUBIC, center=(nw//2,int(nh*0.9)), fillcolor=bg, expand=False)
    canv=Image.new("RGB",(W,Hh),bg)
    ox=(W-nw)//2 + int(dx); oy=(Hh-nh)//2 + int(dy)
    canv.paste(f2,(ox,oy))
    canv.save(os.path.join(FR,f"f_{i:04d}.png"))
print(f"rendered {NF} frames ({DUR:.1f}s) with motion")
