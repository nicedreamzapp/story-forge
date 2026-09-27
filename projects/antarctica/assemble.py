#!/usr/bin/env python3
"""Assembly — ANTARCTICA: The Continent We Just Met.
Four acts, per-line VO scheduling (vo-shot-alignment rule), one-motif score
crossfaded per act, sidechain duck, PIL title/credits, grade + vignette."""
import json, subprocess, sys, wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PROJ = Path.home() / "Desktop/PROJECTS/story-forge/projects/antarctica"
CLIPS, AUDIO, MUSIC, FINAL = PROJ/"clips", PROJ/"audio", PROJ/"music", PROJ/"final"
PIECES = AUDIO / "vo_pieces"
FINAL.mkdir(exist_ok=True)

def run(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"FFMPEG_FAIL: {' '.join(map(str,args))[:300]}\n{r.stderr[-800:]}")
    return r

def dur(p):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                        "-of","csv=p=0",str(p)], capture_output=True, text=True)
    return float(r.stdout.strip())

data = json.loads((PROJ/"shots.json").read_text())
SCENES = {1:[],2:[],3:[],4:[]}
for sh in data["shots"]:
    SCENES[sh.get("sc") or data["stills"][sh["still"]]["scene"]].append(sh["id"])

# ---- 1. Title + credits PNGs -------------------------------------------------
def text_card(lines, out, size=58, sub_size=26, y0=240):
    img = Image.new("RGBA",(1280,720),(0,0,0,0))
    d = ImageDraw.Draw(img)
    try:
        big = ImageFont.truetype("/System/Library/Fonts/Supplemental/Futura.ttc", size)
        small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Futura.ttc", sub_size)
    except OSError:
        big = ImageFont.truetype("/System/Library/Fonts/Supplemental/Georgia.ttf", size)
        small = big
    y = y0
    for kind, txt in lines:
        f = big if kind=="t" else small
        w = d.textlength(txt, font=f)
        d.text(((1280-w)/2+3, y+3), txt, font=f, fill=(0,0,0,200))
        d.text(((1280-w)/2, y), txt, font=f, fill=(235,245,255,255))
        y += int((size if kind=="t" else sub_size)*1.6)
    img.save(out)

text_card([("t","ANTARCTICA"),("s",""),("s","T H E   C O N T I N E N T   W E   J U S T   M E T")],
          FINAL/"title.png", size=72, sub_size=24, y0=270)
text_card([("t","The age of exploration never ended."),
           ("s",""),
           ("s","a Story Forge documentary"),
           ("s","every discovery real — Bedmap3 · CryoSat · Icefin · Beyond EPICA"),
           ("s","rendered, scored and narrated locally on Matt's Mac"),
           ("s",""),
           ("s","for the explorers still drilling")],
          FINAL/"credits.png", size=40, sub_size=24, y0=210)

# ---- 2. Title on s03, credits on extended s40 --------------------------------
t03 = FINAL/"s03_titled.mp4"
d03 = dur(CLIPS/"s03.mp4")
run(["ffmpeg","-y","-i",CLIPS/"s03.mp4","-loop","1","-t",f"{d03}","-i",FINAL/"title.png",
     "-filter_complex",
     f"[1:v]format=rgba,fade=in:st=0.6:d=1.2:alpha=1,fade=out:st={d03-1.6:.2f}:d=1.4:alpha=1[t];"
     f"[0:v][t]overlay=0:0:format=auto[v]",
     "-map","[v]","-c:v","libx264","-crf","17","-pix_fmt","yuv420p","-r","24",t03])

t40 = FINAL/"s40_credits.mp4"
d40 = dur(CLIPS/"s40.mp4")
ext = 9.0
total40 = d40 + ext
run(["ffmpeg","-y","-i",CLIPS/"s40.mp4","-loop","1","-t",f"{total40}","-i",FINAL/"credits.png",
     "-filter_complex",
     f"[0:v]tpad=stop_mode=clone:stop_duration={ext}[base];"
     f"[1:v]format=rgba,fade=in:st={d40+0.5:.2f}:d=1.5:alpha=1[c];"
     f"[base][c]overlay=0:0:format=auto,fade=out:st={total40-2.0:.2f}:d=2.0[v]",
     "-map","[v]","-c:v","libx264","-crf","17","-pix_fmt","yuv420p","-r","24",t40])

SEG = {"s03": t03, "s40": t40}

def seg_path(i):
    return SEG.get(i, CLIPS/f"{i}.mp4")

# ---- 3. Per-line VO scheduling (vo-shot-alignment rule) -----------------------
MAP = {
 1: ["s01","s02","s04","s05","s05","s06","s07","s08","s09"],
 2: ["s10","s11","s12","s13","s14","s15","s16","s17","s17","s18"],
 3: ["s19","s20","s21","s22","s23","s24","s26","s26","s27"],
 4: ["s28","s29","s31","s32","s33","s34","s35","s36","s37","s38","s40","s40"],
}
GAP, LEAD = 0.35, 0.4
starts = {}
for sc, ids in SCENES.items():
    t = 0.0
    for i in ids:
        starts[(sc,i)] = t
        t += dur(seg_path(i))
    starts[(sc,"_end")] = t

for sc, targets in MAP.items():
    pieces = sorted(PIECES.glob(f"sc{sc}_*.wav"))
    assert len(pieces) == len(targets), f"scene{sc}: {len(pieces)} vs {len(targets)}"
    with wave.open(str(pieces[0])) as w0:
        params = w0.getparams()
    fr, sw, ch = params.framerate, params.sampwidth, params.nchannels
    scene_len = starts[(sc,"_end")]
    buf = bytearray(int(scene_len*fr)*sw*ch)
    prev_end = 0.0
    for piece, tgt in zip(pieces, targets):
        with wave.open(str(piece)) as w:
            frames = w.readframes(w.getnframes())
            pdur = w.getnframes()/fr
        t0 = max(prev_end+GAP, starts[(sc,tgt)]+LEAD)
        t0 = min(t0, max(0.0, scene_len-pdur-0.3))
        off = int(t0*fr)*sw*ch
        end = min(off+len(frames), len(buf))
        buf[off:end] = frames[:end-off]
        at = [i for i in SCENES[sc] if starts[(sc,i)] <= t0][-1]
        print(f"sc{sc} {piece.stem}: {t0:6.1f}s -> {tgt} {'✓' if at==tgt else '≈('+at+')'}", flush=True)
        prev_end = t0+pdur
    with wave.open(str(AUDIO/f"scene{sc}_vo.wav"), "wb") as wout:
        wout.setparams(params)
        wout.writeframes(bytes(buf))

# ---- 4. Per-scene mux, full concat -------------------------------------------
scene_files, scene_durs = [], {}
for sc, ids in SCENES.items():
    lst = FINAL/f"scene{sc}.txt"
    lst.write_text("".join(f"file '{seg_path(i)}'\n" for i in ids))
    vid = FINAL/f"scene{sc}_v.mp4"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,
         "-c:v","libx264","-crf","17","-pix_fmt","yuv420p","-r","24",vid])
    out = FINAL/f"scene{sc}.mp4"
    run(["ffmpeg","-y","-i",vid,"-i",AUDIO/f"scene{sc}_vo.wav","-filter_complex",
         "[1:a]aresample=48000,pan=stereo|c0=c0|c1=c0[vo]",
         "-map","0:v","-map","[vo]","-c:v","copy","-c:a","aac","-b:a","192k",
         "-t",f"{dur(vid):.3f}",out])
    scene_files.append(out)
    scene_durs[sc] = dur(out)
    print(f"scene{sc}: {scene_durs[sc]:.1f}s", flush=True)

lst = FINAL/"film.txt"
lst.write_text("".join(f"file '{f}'\n" for f in scene_files))
pic = FINAL/"film_picture.mp4"
run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,"-c","copy",pic])
T = dur(pic)
print(f"picture: {T:.1f}s", flush=True)

# ---- 5. Score: one cue per act, crossfaded, ducked ----------------------------
spans = [scene_durs[1], scene_durs[2], scene_durs[3], scene_durs[4]]
XF = 2.5
cues = [MUSIC/f"cue{i}_{n}.wav" for i,n in [(1,"veil"),(2,"wonder"),(3,"deeptime"),(4,"edge")]]
for c in cues:
    if not c.exists(): sys.exit(f"missing cue {c}")
fc = []
for i,(c,sp) in enumerate(zip(cues,spans)):
    need = sp + (XF if i < 3 else 0)
    fc.append(f"[{i}:a]aresample=48000,atrim=0:{need:.2f},asetpts=PTS-STARTPTS"
              + (",afade=in:st=0:d=2.0" if i==0 else "") + f"[c{i}]")
chain = "[c0]"
for i in range(1,4):
    nxt = f"[m{i}]" if i<3 else "[bed]"
    fc.append(f"{chain}[c{i}]acrossfade=d={XF}:c1=tri:c2=tri{nxt}")
    chain = nxt
bed = FINAL/"bed.wav"
run(["ffmpeg","-y"]+sum([["-i",str(c)] for c in cues],[])+
    ["-filter_complex",";".join(fc),"-map","[bed]","-t",f"{T:.2f}",bed])

mix = FINAL/"mix.wav"
run(["ffmpeg","-y","-i",pic,"-i",bed,"-filter_complex",
     "[0:a]aresample=48000,asplit=2[vo][key];"
     "[1:a]volume=0.55[m];"
     "[m][key]sidechaincompress=threshold=0.02:ratio=6:attack=150:release=700[duck];"
     "[vo][duck]amix=inputs=2:duration=first:normalize=0,"
     f"afade=out:st={T-3.0:.2f}:d=3.0,loudnorm=I=-16:TP=-1.5:LRA=11[a]",
     "-map","[a]","-t",f"{T:.2f}",mix])

# ---- 6. Grade + vignette + mux -------------------------------------------------
out = FINAL/"ANTARCTICA_The_Continent_We_Just_Met.mp4"
run(["ffmpeg","-y","-i",pic,"-i",mix,
     "-vf","eq=saturation=1.04:contrast=1.04,vignette=PI/4.6:mode=backward,"
           "fade=in:st=0:d=1.2",
     "-map","0:v","-map","1:a","-c:v","libx264","-crf","17","-preset","slow",
     "-pix_fmt","yuv420p","-c:a","aac","-b:a","256k","-movflags","+faststart",out])
print(f"FILM_DONE {out} {dur(out):.1f}s", flush=True)
