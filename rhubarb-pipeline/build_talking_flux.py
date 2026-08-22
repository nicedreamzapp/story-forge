#!/usr/bin/env python3
"""Assemble Flux viseme images into a talking clip on the Rhubarb timeline.
Closed/rest pose is painted (Flux won't close a mouth); open visemes are inpaints.
Crossfades between visemes for smooth morph + gentle idle motion."""
import os, math
from PIL import Image, ImageDraw, ImageFilter

HERE=os.path.dirname(os.path.abspath(__file__))
FPS=24
FR=os.path.join(HERE,"frames_flux"); os.makedirs(FR,exist_ok=True)
for f in os.listdir(FR):
    if f.endswith(".png"): os.remove(os.path.join(FR,f))

base=Image.open(os.path.join(HERE,"art/base.png")).convert("RGB")
W,Hh=base.size

# --- paint a convincing CLOSED muzzle over the base mouth ---
def make_closed():
    im=base.copy(); d=ImageDraw.Draw(im)
    cx,cy=392,478
    # sample snout tones above the mouth for a natural fill gradient
    top=base.getpixel((cx,cy-46)); bot=base.getpixel((cx,cy+30))
    fill=Image.new("RGB",(W,Hh)); fd=ImageDraw.Draw(fill)
    for yy in range(cy-58,cy+62):
        f=(yy-(cy-58))/120
        col=tuple(int(top[k]*(1-f)+bot[k]*f) for k in range(3))
        fd.line([(cx-90,yy),(cx+90,yy)],fill=col)
    mask=Image.new("L",(W,Hh),0); md=ImageDraw.Draw(mask)
    md.ellipse([cx-72,cy-50,cx+72,cy+56],fill=255); mask=mask.filter(ImageFilter.GaussianBlur(9))
    im=Image.composite(fill,im,mask)
    d=ImageDraw.Draw(im)
    # gentle closed-mouth line + soft lower-lip shadow
    d.arc([cx-50,cy-16,cx+50,cy+30],18,162,fill=(70,40,38),width=5)
    d.arc([cx-50,cy-10,cx+50,cy+40],20,160,fill=(150,96,70),width=3)
    return im.filter(ImageFilter.SMOOTH)

IMG={"X":make_closed()}
IMG["A"]=IMG["X"]
for v in ["B","C","D","E","F","G","H"]:
    IMG[v]=Image.open(os.path.join(HERE,f"art/m_{v}.png")).convert("RGB")

tl=[(float(l.split("\t")[0]),l.strip().split("\t")[1]) for l in open(os.path.join(HERE,"visemes.tsv"))]
DUR=tl[-1][0]; NF=int(DUR*FPS)
def smooth(x): x=max(0,min(1,x)); return x*x*(3-2*x)

bgcol=base.getpixel((6,6))
def frame(i):
    t=i/FPS
    k=0
    for j,(tt,_) in enumerate(tl):
        if tt<=t: k=j
    t0,v0=tl[k]; t1,v1=tl[min(k+1,len(tl)-1)]
    prog=(t-t0)/max(t1-t0,1e-3)
    f=smooth((prog-0.4)/0.5)                 # hold then quick morph
    a=IMG.get(v0,IMG["X"]); b=IMG.get(v1,IMG["X"])
    img=Image.blend(a,b,f)
    # gentle idle: vertical bob + micro sway
    dy=int(3*math.sin(t*2.0)); dx=int(4*math.sin(t*0.7))
    canv=Image.new("RGB",(W,Hh),bgcol); canv.paste(img,(dx,dy));
    return canv

for i in range(NF):
    frame(i).save(os.path.join(FR,f"f_{i:04d}.png"))
print(f"rendered {NF} frames ({DUR:.1f}s)")
