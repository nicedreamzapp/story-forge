#!/usr/bin/env python3
"""assemble_film.py — The Oldest Tree, full cut.
Shot order from film_shots.json; talk shots use clips/<id>_talk.mp4 with their OWN baked
voice at zero offset (never re-laid). Every other clip is silent picture + its MMAudio
foley (sfx/<id>.wav, low). Nia narration is anchored to shots; the score runs under all
of it, ducked by voice. 1080p, 2.5:1 letterboxed, one grade + grain, 0.5s dissolves."""
import json, subprocess, sys
from pathlib import Path
P = Path(__file__).resolve().parent
FF = "/opt/homebrew/bin/ffmpeg"
XF = 0.5
SHOT = 4.0
def dur(f): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(f)]))
spec = json.load(open(P/"film_shots.json"))
order, clips, talk = [], [], set()
for s in spec["shots"]:
    if s.get("cut"): continue
    c = P/"clips"/(f"{s['id']}_talk.mp4" if s.get("talk") else f"{s['id']}_final.mp4")
    if c.exists():
        order.append(s["id"]); clips.append(c)
        if s.get("talk"): talk.add(s["id"])
    else:
        print("MISSING", s["id"])
lens = [dur(c) if sid in talk else min(SHOT, dur(c)) for sid, c in zip(order, clips)]
starts, t = [], 0.0
for L in lens:
    starts.append(t); t += L - XF
total = t + XF
at = dict(zip(order, starts))
# narration anchors: (line, shot, offset into shot)
ANCH = [("n01","s1_descend",0.3),("n02","s2_wide_walk",0.5),("nA","s2_track_behind",0.5),("n03","s2_girl_listen",0.3),
        ("n04","s3_reveal",0.8),("n05","s3_hollow",0.3),("n06","s3_profile",0.3),("n07","s3_heart",0.3),
        ("n08","s4_walkback",0.3),("nB","s4_empty",0.5),("n09","s5_silhouette",0.3),("n10b","s5_storm",0.3),("n11b","s5_firewall",0.3),
        ("n12b","s5_sway",0.3),("n13","s6_black",0.5),("n14","s6_eyes",0.3),("n15","s7_wide",0.5),
        ("n16b","s8_wide",0.8),("n17","s8_pullback",0.5)]
nar, last_end = [], 0.0
for ln, sid, off in ANCH:
    if sid not in at: print("anchor missing", sid); continue
    f = P/"voices"/f"nia_{ln}.wav"
    st = max(at[sid] + off, last_end + 0.4)
    for tsid in talk:                      # never talk over a lip-sync shot
        ts, te = at[tsid], at[tsid] + lens[order.index(tsid)]
        if st < te and st + dur(f) > ts: st = te + 0.2
    nar.append((f, st)); last_end = st + dur(f)
grade = ("scale=1920:768:flags=lanczos,setsar=1,fps=24,eq=contrast=1.06:saturation=0.9:gamma=0.98,"
         "colorbalance=rs=-0.03:bs=0.03:rh=0.04:bh=-0.03,unsharp=5:5:0.4")
OLD = {"s3_seed","s3_sapling","s5_storm","s5_crown","s5_split","s5_firewall","s5_embers","s5_shelter","s5_trunkfire","s5_sway","s5_lean","s5_fallen"}
old = ",colorchannelmixer=.95:.05:0:0:.05:.9:.05:0:0:.1:.8:0,eq=saturation=0.75,vignette=PI/4"
inputs, fc = [], []
for i, (sid, c, L) in enumerate(zip(order, clips, lens)):
    inputs += ["-i", str(c)]
    fc.append(f"[{i}:v]trim=0:{L},setpts=PTS-STARTPTS,{grade}{old if sid in OLD else ''},format=yuv420p[v{i}]")
prev = "v0"
for i in range(1, len(order)):
    fc.append(f"[{prev}][v{i}]xfade=transition=fade:duration={XF}:offset={starts[i]:.3f}[x{i}]"); prev = f"x{i}"
# title card overlay on the opening
title = P/"final"/"title.png"
n = len(order)
if title.exists():
    inputs += ["-loop","1","-t","6","-i",str(title)]
    fc.append(f"[{n}:v]format=rgba,fade=t=in:st=0.5:d=1:alpha=1,fade=t=out:st=4.5:d=1:alpha=1,setpts=PTS+{max(0,at.get('s1_rays',8)):.2f}/TB[tt]")
    fc.append(f"[{prev}][tt]overlay=0:0:eof_action=pass[vt]"); prev = "vt"; n += 1
fc.append(f"[{prev}]noise=alls=5:allf=t,pad=1920:1080:0:156:black,fade=t=in:st=0:d=1.5,fade=t=out:st={total-2:.2f}:d=2[vout]")
# audio
aud = []
inputs += ["-i", str(P/"score_full.wav")]; fc.append(f"[{n}:a]atrim=0:{total},acompressor=threshold=-32dB:ratio=10:attack=40:release=500:makeup=1,volume=0.3,afade=t=in:st=0:d=5,afade=t=out:st={total-4:.2f}:d=4,aformat=channel_layouts=stereo[mus]"); n += 1
vk = []
for k, (f, st) in enumerate(nar):
    inputs += ["-i", str(f)]; fc.append(f"[{n}:a]adelay={int(st*1000)}|{int(st*1000)},aformat=channel_layouts=stereo:sample_rates=48000[n{k}]"); vk.append(f"[n{k}]"); n += 1
for sid in talk:
    i = order.index(sid); st = at[sid]
    fc.append(f"[{i}:a]adelay={int(st*1000)}|{int(st*1000)},volume=1.4,aformat=channel_layouts=stereo:sample_rates=48000[t{i}]"); vk.append(f"[t{i}]")
fk = []
for sid in order:
    f = P/"sfx"/f"{sid}.wav"
    if f.exists() and sid not in talk:
        st = at[sid]; L = lens[order.index(sid)]
        inputs += ["-i", str(f)]; fc.append(f"[{n}:a]atrim=0:{L},afade=t=in:d=0.3,afade=t=out:st={L-0.4:.2f}:d=0.4,volume=0.35,adelay={int(st*1000)}|{int(st*1000)},aformat=channel_layouts=stereo:sample_rates=48000[f{n}]"); fk.append(f"[f{n}]"); n += 1
fc.append("".join(vk) + f"amix=inputs={len(vk)}:normalize=0,volume=2.0,apad[voc2]")
bed = "[mus]"
if fk:
    fc.append("[mus]" + "".join(fk) + f"amix=inputs={len(fk)+1}:normalize=0:duration=first[bed]"); bed = "[bed]"
# Deterministic duck (2026-09-29): a sidechain compressor measured only ~0 dB of duck on some
# lines (music -25 vs voice -25 at 45s). Envelope instead: every voice interval pulls the bed
# down to 20% (-14 dB) with a 0.4s ramp in and 0.6s ramp out.
iv = [(st, st + dur(f)) for f, st in nar] + [(at[s], at[s] + lens[order.index(s)]) for s in talk]
dips = [f"clip((t-{a-0.4:.2f})/0.4,0,1)*clip(({b+0.6:.2f}-t)/0.6,0,1)" for a, b in iv]
duck = dips[0]
for d_ in dips[1:]:
    duck = f"max({duck},{d_})"
fc.append(f"{bed}volume='1-0.8*({duck})':eval=frame[duck]")
fc.append("[duck][voc2]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.9,aresample=48000[aout]")
out = P/"final"/"The_Oldest_Tree.mp4"
Path(P/"final"/"filter.txt").write_text(";\n".join(fc))
cmd = [FF,"-y",*inputs,"-filter_complex_script",str(P/"final"/"filter.txt"),"-map","[vout]","-map","[aout]",
       "-c:v","libx264","-crf","16","-preset","slow","-pix_fmt","yuv420p","-c:a","aac","-b:a","256k","-t",f"{total:.2f}",str(out)]
subprocess.run(cmd, check=True)
# Loudness, pass 2 (2026-09-29): ffmpeg loudnorm in dynamic mode pumped quiet stretches UP —
# the score gaps and the opening came out louder than the narration ("music is too loud at
# times"). Measure once, then apply ONE static gain to the whole mix so nothing gets pumped.
m = subprocess.run([FF, "-i", str(out), "-vn", "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
import re as _re
I = float(_re.findall(r"I:\s+(-?[\d.]+) LUFS", m)[-1])
gain = -19.0 - I   # -19: at -16 the limiter was shaving ~5 dB off voice peaks
tmp = out.with_name("_gain_tmp.mp4")
subprocess.run([FF, "-y", "-i", str(out), "-c:v", "copy", "-af", f"volume={gain:.2f}dB,alimiter=limit=0.89:level=false",
                "-c:a", "aac", "-b:a", "256k", str(tmp)], check=True)
tmp.replace(out)
print(f"static gain {gain:+.1f} dB (measured {I:.1f} LUFS)")
json.dump({"order":order,"starts":starts,"lens":lens,"total":total,"narration":[(f.name,st) for f,st in nar]},open(P/"final"/"timeline.json","w"),indent=1)
print(out, round(total,1))
