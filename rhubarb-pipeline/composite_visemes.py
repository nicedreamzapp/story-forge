#!/usr/bin/env python3
"""Marry LTX motion + Rhubarb sync: track the nose in each LTX frame, paste the
correctly-timed viseme mouth (feathered crop from the frontal Flux visemes) below it.
Usage: composite_visemes.py LTX.mp4 [scale] [dy] [dx]"""
import os, sys, math, subprocess, glob
import numpy as np, cv2
from PIL import Image

HERE=os.path.dirname(os.path.abspath(__file__)); FPS=24
LTX=sys.argv[1]
SCALE=float(sys.argv[2]) if len(sys.argv)>2 else 1.0   # mouth-overlay scale vs source
DY=int(sys.argv[3]) if len(sys.argv)>3 else 70          # mouth distance below nose center
DX=int(sys.argv[4]) if len(sys.argv)>4 else 0
LEAD=float(sys.argv[5]) if len(sys.argv)>5 else 0.0     # shift visemes earlier (s) for perceived sync
SRC_NOSE=(392,430); SRC_MOUTH=(392,500)                 # source coords in the 768 Flux frames

# 1) extract LTX frames
RAW=os.path.join(HERE,"ltx_raw"); os.makedirs(RAW,exist_ok=True)
for f in os.listdir(RAW):
    if f.endswith(".png"): os.remove(os.path.join(RAW,f))
subprocess.run(["ffmpeg","-y","-i",LTX,os.path.join(RAW,"r_%04d.png")],
               stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
frames=sorted(glob.glob(os.path.join(RAW,"r_*.png")))
NF=len(frames)

# 2) build feathered mouth overlays (RGBA) from each viseme image
def mouth_overlay(v):
    im=Image.open(os.path.join(HERE,f"art/m_{v}.png")).convert("RGBA")
    cx,cy=SRC_MOUTH; rx,ry=92,82
    crop=im.crop((cx-rx,cy-ry,cx+rx,cy+ry))
    mask=Image.new("L",crop.size,0); from PIL import ImageDraw,ImageFilter
    d=ImageDraw.Draw(mask); d.ellipse([10,10,2*rx-10,2*ry-10],fill=255)
    mask=mask.filter(ImageFilter.GaussianBlur(12))
    crop.putalpha(mask)
    return crop
OV={v:mouth_overlay(v) for v in ["X","B","C","D","E","F","G","H"]}; OV["A"]=OV["X"]

# 3) nose template from the SOURCE closed image (high-contrast dark nose)
src=cv2.cvtColor(np.array(Image.open(os.path.join(HERE,"art/m_X.png")).convert("RGB")),cv2.COLOR_RGB2BGR)
nx,ny=SRC_NOSE; tw=110
tmpl=src[ny-70:ny+50, nx-tw//2:nx+tw//2]

# rhubarb timeline
tl=[(float(l.split("\t")[0]),l.strip().split("\t")[1]) for l in open(os.path.join(HERE,"visemes.tsv"))]
DUR=tl[-1][0]
def vis_at(t):
    cur="X"
    for tt,sh in tl:
        if tt<=t: cur=sh
        else: break
    return cur

OUT=os.path.join(HERE,"frames_married"); os.makedirs(OUT,exist_ok=True)
for f in os.listdir(OUT):
    if f.endswith(".png"): os.remove(os.path.join(OUT,f))

# scale template to LTX frame size (LTX is 768x512 vs source 768x768 -> match by template scaling search)
fr0=cv2.cvtColor(np.array(Image.open(frames[0]).convert("RGB")),cv2.COLOR_RGB2BGR)
Hf,Wf=fr0.shape[:2]
best=None
for s in [0.55,0.6,0.65,0.7,0.75,0.8,0.85]:
    t=cv2.resize(tmpl,(int(tmpl.shape[1]*s),int(tmpl.shape[0]*s)))
    if t.shape[0]>=Hf or t.shape[1]>=Wf: continue
    res=cv2.matchTemplate(fr0,t,cv2.TM_CCOEFF_NORMED); _,mx,_,loc=cv2.minMaxLoc(res)
    if best is None or mx>best[0]: best=(mx,s,t)
mscore,mscale,mtmpl=best
th,tw2=mtmpl.shape[:2]
print(f"nose template scale={mscale:.2f} score={mscore:.2f}",flush=True)

for i,fp in enumerate(frames):
    pil=Image.open(fp).convert("RGBA"); cvimg=cv2.cvtColor(np.array(pil.convert("RGB")),cv2.COLOR_RGB2BGR)
    res=cv2.matchTemplate(cvimg,mtmpl,cv2.TM_CCOEFF_NORMED); _,_,_,loc=cv2.minMaxLoc(res)
    nose_cx=loc[0]+tw2//2; nose_cy=loc[1]+th//2
    v=vis_at(i/FPS + LEAD); ov=OV[v]
    osz=(int(ov.width*mscale*SCALE),int(ov.height*mscale*SCALE))
    ovr=ov.resize(osz, Image.LANCZOS)
    mx=nose_cx+DX-osz[0]//2; my=nose_cy+int(DY*mscale)-osz[1]//2
    pil.alpha_composite(ovr,(mx,my))
    pil.convert("RGB").save(os.path.join(OUT,f"m_{i:04d}.png"))
print(f"composited {NF} frames",flush=True)
