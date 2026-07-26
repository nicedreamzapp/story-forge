#!/usr/bin/env python3
"""Assembly — The Little Robot Who Built Himself.
Per-scene concat with scene-synced VO (adelay+amix per frozen rule 3),
music cues crossfaded per scene-group, sidechain-ducked under narration,
PIL title/credits overlays (drawtext not installed), grade + static vignette."""
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PROJ = Path.home() / "Desktop/PROJECTS/story-forge/projects/little_robot"
CLIPS, AUDIO, MUSIC, FINAL = PROJ/"clips", PROJ/"audio", PROJ/"music", PROJ/"final"
FINAL.mkdir(exist_ok=True)

def run(args, **kw):
    r = subprocess.run(args, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.exit(f"FFMPEG_FAIL: {' '.join(map(str,args))[:300]}\n{r.stderr[-800:]}")
    return r

def dur(p):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                        "-of","csv=p=0",str(p)], capture_output=True, text=True)
    return float(r.stdout.strip())

data = json.loads((PROJ/"shots.json").read_text())
shots = data["shots"]
SCENES = {1:[],2:[],3:[],4:[],5:[]}
for sh in shots:
    sc = data["stills"][sh["still"]]["scene"]
    SCENES[sc].append(sh["id"])

# ---- 1. Title + credits overlay PNGs (PIL, transparent) --------------------
def text_card(lines, out, size=64, sub_size=30, y0=200):
    img = Image.new("RGBA",(1280,720),(0,0,0,0))
    d = ImageDraw.Draw(img)
    try:
        big = ImageFont.truetype("/System/Library/Fonts/Supplemental/Georgia Bold Italic.ttf", size)
        small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Georgia Italic.ttf", sub_size)
    except OSError:
        big = ImageFont.truetype("/System/Library/Fonts/Supplemental/Georgia.ttf", size)
        small = big
    y = y0
    for kind, txt in lines:
        f = big if kind=="t" else small
        w = d.textlength(txt, font=f)
        # soft shadow then warm cream text
        d.text(((1280-w)/2+3, y+3), txt, font=f, fill=(0,0,0,180))
        d.text(((1280-w)/2, y), txt, font=f, fill=(255,242,214,255))
        y += int((size if kind=="t" else sub_size)*1.5)
    img.save(out)

text_card([("t","The Little Robot"),("t","Who Built Himself")], FINAL/"title.png", y0=240)
text_card([("t","Nothing here was broken."),
           ("s",""),
           ("s","a Story Forge film"),
           ("s","made in one night, locally, on Matt's Mac"),
           ("s","story · pictures · music · voice — all homegrown"),
           ("s",""),
           ("s","for June, and everyone still unfinished")],
          FINAL/"credits.png", size=46, sub_size=26, y0=190)

# ---- 2. Special segments: title overlay on s06, credits on extended s48 ----
t06 = FINAL/"s06_titled.mp4"
d06 = dur(CLIPS/"s06.mp4")
run(["ffmpeg","-y","-i",CLIPS/"s06.mp4","-loop","1","-t",f"{d06}","-i",FINAL/"title.png",
     "-filter_complex",
     f"[1:v]format=rgba,fade=in:st=0.8:d=1.2:alpha=1,fade=out:st={d06-1.6:.2f}:d=1.4:alpha=1[t];"
     f"[0:v][t]overlay=0:0:format=auto[v]",
     "-map","[v]","-c:v","libx264","-crf","17","-pix_fmt","yuv420p","-r","24",t06])

t48 = FINAL/"s48_credits.mp4"
d48 = dur(CLIPS/"s48.mp4")
ext = 8.0  # freeze-extend for credits
total48 = d48 + ext
run(["ffmpeg","-y","-i",CLIPS/"s48.mp4","-loop","1","-t",f"{total48}","-i",FINAL/"credits.png",
     "-filter_complex",
     f"[0:v]tpad=stop_mode=clone:stop_duration={ext}[base];"
     f"[1:v]format=rgba,fade=in:st={d48-1.0:.2f}:d=1.5:alpha=1[c];"
     f"[base][c]overlay=0:0:format=auto,fade=out:st={total48-2.0:.2f}:d=2.0[v]",
     "-map","[v]","-c:v","libx264","-crf","17","-pix_fmt","yuv420p","-r","24",t48])

SEG = {"s06": t06, "s48": t48}

# ---- 3. Per-scene concat + scene-synced VO ----------------------------------
VO_DELAY_MS = 0
scene_files, scene_durs = [], {}
for sc, ids in SCENES.items():
    lst = FINAL/f"scene{sc}.txt"
    lst.write_text("".join(f"file '{SEG.get(i, CLIPS/(i+'.mp4'))}'\n" for i in ids))
    vid = FINAL/f"scene{sc}_v.mp4"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,
         "-c:v","libx264","-crf","17","-pix_fmt","yuv420p","-r","24",vid])
    vo = AUDIO/f"scene{sc}_vo.wav"
    out = FINAL/f"scene{sc}.mp4"
    run(["ffmpeg","-y","-i",vid,"-i",vo,"-filter_complex",
         f"[1:a]aresample=48000,pan=stereo|c0=c0|c1=c0,adelay={VO_DELAY_MS}|{VO_DELAY_MS}[vo]",
         "-map","0:v","-map","[vo]","-c:v","copy","-c:a","aac","-b:a","192k",
         "-shortest" if False else "-t", f"{dur(vid):.3f}", out])
    scene_files.append(out)
    scene_durs[sc] = dur(out)
    print(f"scene{sc}: {scene_durs[sc]:.1f}s", flush=True)

# ---- 4. Full picture concat --------------------------------------------------
lst = FINAL/"film.txt"
lst.write_text("".join(f"file '{f}'\n" for f in scene_files))
pic = FINAL/"film_picture.mp4"
run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,"-c","copy",pic])
T = dur(pic)
print(f"picture: {T:.1f}s", flush=True)

# ---- 5. Music bed: cue spans -> trim/crossfade -> duck under VO -------------
# cue1: scene1 | cue2: scenes2+3 | cue3: scene4 | cue4: scene5
spans = [scene_durs[1], scene_durs[2]+scene_durs[3], scene_durs[4], scene_durs[5]]
XF = 2.0
cues = [MUSIC/f"cue{i}_{n}.wav" for i,n in [(1,"bin"),(2,"build"),(3,"storm"),(4,"sunrise")]]
for c in cues:
    if not c.exists(): sys.exit(f"missing cue {c}")
# trim each cue to span+XF (except last: span), fade edges, acrossfade chain
fc, prev = [], None
for i,(c,sp) in enumerate(zip(cues,spans)):
    need = sp + (XF if i < 3 else 0)
    fc.append(f"[{i}:a]aresample=48000,atrim=0:{need:.2f},asetpts=PTS-STARTPTS"
              + (f",afade=in:st=0:d=1.5" if i==0 else "") + f"[c{i}]")
chain = "[c0]"
for i in range(1,4):
    nxt = f"[m{i}]" if i<3 else "[bed]"
    fc.append(f"{chain}[c{i}]acrossfade=d={XF}:c1=tri:c2=tri{nxt}")
    chain = nxt
bed = FINAL/"bed.wav"
run(["ffmpeg","-y"]+sum([["-i",str(c)] for c in cues],[])+
    ["-filter_complex",";".join(fc),"-map","[bed]","-t",f"{T:.2f}",bed])

# duck bed under VO (sidechain ~6dB feel), mix, normalize
mix = FINAL/"mix.wav"
run(["ffmpeg","-y","-i",pic,"-i",bed,"-filter_complex",
     "[0:a]aresample=48000,asplit=2[vo][key];"
     "[1:a]volume=0.50[m];"
     "[m][key]sidechaincompress=threshold=0.02:ratio=6:attack=150:release=700[duck];"
     "[vo][duck]amix=inputs=2:duration=first:normalize=0,"
     f"afade=out:st={T-2.5:.2f}:d=2.5,loudnorm=I=-16:TP=-1.5:LRA=11[a]",
     "-map","[a]","-t",f"{T:.2f}",mix])

# ---- 6. Grade + vignette + mux ----------------------------------------------
out = FINAL/"The_Little_Robot_Who_Built_Himself.mp4"
run(["ffmpeg","-y","-i",pic,"-i",mix,
     "-vf","eq=saturation=1.06:contrast=1.03,vignette=PI/4.4:mode=backward,"
           "fade=in:st=0:d=1.0",
     "-map","0:v","-map","1:a","-c:v","libx264","-crf","17","-preset","slow",
     "-pix_fmt","yuv420p","-c:a","aac","-b:a","256k","-movflags","+faststart",out])
print(f"FILM_DONE {out} {dur(out):.1f}s", flush=True)
