#!/usr/bin/env python3
"""v2: parametric, INTERPOLATED viseme mouth (smooth morph, no hard cuts) + expressive
head/brow/blink animation. Rhubarb timing underneath. 100% local."""
import os, math
from PIL import Image, ImageDraw, ImageFilter

W = H = 720; FPS = 24; SS = 2  # supersample for smooth edges
HERE = os.path.dirname(os.path.abspath(__file__))
FR = os.path.join(HERE, "frames_v2"); os.makedirs(FR, exist_ok=True)
for f in os.listdir(FR):
    if f.endswith(".png"): os.remove(os.path.join(FR, f))

timeline = [(float(l.split("\t")[0]), l.strip().split("\t")[1]) for l in open(os.path.join(HERE, "visemes.tsv"))]
DUR = timeline[-1][0]; NF = int(DUR * FPS)

# viseme -> (openness, width, round, emphasis)  openness 0..1, width 0..1, round 0..1
VIS = {
 "X": (0.04, 1.0, 0.0, 0.0), "A": (0.06, 1.0, 0.0, 0.0),
 "B": (0.18, 0.92, 0.0, 0.2), "C": (0.46, 0.95, 0.1, 0.5),
 "D": (0.92, 0.86, 0.2, 1.0), "E": (0.52, 0.56, 0.85, 0.6),
 "F": (0.26, 0.42, 0.9, 0.3), "G": (0.20, 0.88, 0.0, 0.3),
 "H": (0.52, 0.82, 0.2, 0.6),
}
def lerp(a, b, t): return a + (b - a) * t
def params_at(t):
    # find bracketing visemes and interpolate (ease) between them
    prev = timeline[0]; nxt = timeline[-1]
    for i, (tt, sh) in enumerate(timeline):
        if tt <= t: prev = (tt, sh); nxt = timeline[min(i+1, len(timeline)-1)]
        else: break
    span = max(nxt[0] - prev[0], 1e-3)
    f = min(max((t - prev[0]) / span, 0), 1)
    f = f * f * (3 - 2 * f)                      # smoothstep ease
    p0, p1 = VIS[prev[1]], VIS[nxt[1]]
    return tuple(lerp(p0[k], p1[k], f) for k in range(4))

TAN=(216,160,107); TAN_D=(190,134,84); BROWN=(150,96,54); BROWN_D=(120,74,40)
NOSE=(52,38,36); DARK=(58,30,28); TEETH=(252,250,243); TONGUE=(206,98,104)
WHITE=(255,255,255); PUP=(44,31,27); SNOUT=(230,182,134)

def bgimg(w,h):
    base=Image.new("RGB",(w,h),(40,52,46)); top=Image.new("RGB",(w,h),(104,128,102))
    m=Image.new("L",(w,h),0); md=ImageDraw.Draw(m)
    for y in range(h): md.line([(0,y),(w,y)], fill=int(165*(1-y/h)))
    return Image.composite(top,base,m)

def ell(d,cx,cy,rx,ry,fill,outline=None,wd=0):
    d.ellipse([cx-rx,cy-ry,cx+rx,cy+ry],fill=fill,outline=outline,width=wd)

def draw_mouth(d, cx, my, p):
    o,w,rnd,emp = p
    base_w = 52*SS
    mw = base_w*(0.5+0.5*w)*(1-0.45*rnd)      # round pulls width in
    mh = (6 + 64*o)*SS                         # height grows with openness
    # dark interior
    d.ellipse([cx-mw, my-mh*0.5, cx+mw, my+mh*0.5], fill=DARK)
    if o < 0.12:                               # essentially closed -> soft smile line
        d.arc([cx-mw, my-12*SS, cx+mw, my+16*SS], 18,162, fill=DARK, width=int(6*SS))
        return
    # upper teeth
    if o > 0.14:
        th = int(min(13*SS, mh*0.4))
        d.rectangle([cx-mw*0.82, my-mh*0.5, cx+mw*0.82, my-mh*0.5+th], fill=TEETH)
    # tongue when wide open
    if o > 0.55:
        ell(d, cx, my+mh*0.32, mw*0.62, mh*0.26, TONGUE)

def frame(i):
    t=i/FPS; p=params_at(t)
    w,h=W*SS,H*SS
    img=bgimg(w,h); d=ImageDraw.Draw(img)
    emp=p[3]
    cx=w//2; cy=h//2+30*SS
    sway=math.radians(5*math.sin(t*1.6))       # head sway (rotate whole head later)
    cy += int(3*SS*math.sin(t*2.0))            # breathe
    head_dx=int(10*SS*math.sin(t*0.9))         # subtle head turn
    cx+=head_dx
    # ears
    for s in (-1,1):
        ex=cx+s*150*SS
        ell(d,ex,cy-0*SS,58*SS,168*SS,BROWN); ell(d,ex,cy+10*SS,40*SS,150*SS,BROWN_D)
    # head
    ell(d,cx,cy,175*SS,186*SS,TAN); ell(d,cx,cy-10*SS,175*SS,176*SS,None,TAN_D,int(4*SS))
    # brows (raise with emphasis)
    br=int(emp*16*SS)
    d.arc([cx-122*SS,cy-120*SS-br,cx-22*SS,cy-30*SS-br],200,350,fill=BROWN_D,width=int(11*SS))
    d.arc([cx+22*SS,cy-120*SS-br,cx+122*SS,cy-30*SS-br],190,340,fill=BROWN_D,width=int(11*SS))
    # eyes (blink)
    blink=(i%52) in (0,1,2)
    for s in (-1,1):
        ex=cx+s*62*SS; ey=cy-60*SS
        ell(d,ex,ey,40*SS,46*SS,WHITE)
        if blink: d.line([ex-34*SS,ey,ex+34*SS,ey],fill=PUP,width=int(8*SS))
        else:
            ell(d,ex+s*4*SS,ey+6*SS,20*SS,24*SS,PUP)
            ell(d,ex+s*4*SS-6*SS,ey-2*SS,6*SS,7*SS,WHITE)
    # snout + nose
    ell(d,cx,cy+74*SS,96*SS,74*SS,SNOUT)
    ell(d,cx,cy+30*SS,34*SS,26*SS,NOSE); ell(d,cx-10*SS,cy+22*SS,7*SS,5*SS,(112,92,90))
    # mouth (interpolated viseme)
    draw_mouth(d, cx, cy+108*SS, p)
    img=img.resize((W,H), Image.LANCZOS)
    return img

for i in range(NF):
    frame(i).save(os.path.join(FR, f"f_{i:04d}.png"))
print(f"rendered {NF} frames at {FPS}fps ({DUR:.1f}s), supersampled x{SS}")
