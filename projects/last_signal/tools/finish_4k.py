#!/usr/bin/env python3
"""4K finish for THE LAST SIGNAL. For every picture segment: SeedVR2-3B output (final/segs/up/<seg>.mp4, scope crop
upscaled) -> drop the temporal handles -> exact 3840x1608 (lanczos) -> optional bloom/glare pass on the
light/engine shots -> per-section LUT via the same lut3d bin/grade uses -> pad into a 3840x2160 frame (2.39:1
scope bars, 276 px each) -> grain (bin/grade's noise at the chosen strength, applied before the bars so the bars
stay clean black, all inside bin/grade). Black + title card are added as-is. Concats to final/picture_4k.mp4 (no audio).
Per-section LUT (timeline.json records it): space shots cold_space_teal, everything on/near the planet
teal_orange_blockbuster, title card untouched."""
import json, subprocess, sys
from pathlib import Path
P = Path(__file__).resolve().parent.parent
ROOT = P.parent.parent
e = json.load(open(P / "final/edl_final.json")); FPS = e["fps"]
H = {m["seg"]: m for m in json.load(open(P / "final/segs/handles.json"))}
PREVIEW = "--preview" in sys.argv   # 1080p proxy of the same chain, lanczos everywhere, to check the look while SeedVR2 runs
UP = P / "final/segs/up"; OUT = P / ("final/segs/prev" if PREVIEW else "final/segs/4k"); OUT.mkdir(exist_ok=True)
FW, FH, VH, BAR = (1920, 1080, 804, 138) if PREVIEW else (3840, 2160, 1608, 276)
COLD = {"c01_asteroids", "c01b_asteroids_close"}
BLOOM = {  # strength 0..1 : engine nozzles, ship lights, lightning, glow, fire, sun
 "c01_asteroids": .55, "c01b_asteroids_close": .55, "c03_dive": .7, "c03b_dive_clouds": .6, "c04_arrival": .6,
 "c05_claws": .45, "c07_handwriting": .6, "c07b_captain_face": .35, "c08_lightwave": .7, "c09_welcome": .45,
 "c10_second_sun": .6, "c10b_second_sun": .5, "c12_engines": .75, "c12b_engines": .75, "c13_mountain": .45, "c13b_mountain": .45,
 "c14_boots": .6, "c14c_boots": .6, "c15_grab": .7, "c15b_grab": .6, "c02a_cockpit": .4, "c02b_lever": .5,
}
GRAIN = 0.12   # bin/grade --grain scale (alls = 30 x grain); light, moving footage only
def bloom_chain(s):
    K = 0.5 if PREVIEW else 1
    # highlights -> wide soft glow (screen) + a horizontal anamorphic teal streak (screen)
    return (f"split=3[o][h1][h2];"
            f"[h1]curves=all='0/0 0.70/0 1/1',gblur=sigma={34*K}[g];"
            f"[h2]curves=all='0/0 0.86/0 1/1',gblur=sigma={90*K}:sigmaV=1.5,colorchannelmixer=rr=0.45:gg=0.85:bb=1.0[st];"
            f"[o][g]blend=all_mode=screen:all_opacity={0.55*s:.3f}[ob];[ob][st]blend=all_mode=screen:all_opacity={0.9*s:.3f}")
lst = []
for k, c in enumerate(e["cuts"]):
    name = f"{k:02d}_{c['id']}.mp4"; o = OUT / name
    if c["src"] is None:
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=black:s={FW}x{FH}:r={FPS}", "-frames:v", str(c["frames"])]
    elif c["section"] == "title":
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(P / c["src"]), "-vf", f"scale={FW}:{FH}:flags=lanczos", "-frames:v", str(c["frames"])]
    else:
        m = H[name]; lut = "cold_space_teal" if c["id"] in COLD else "teal_orange_blockbuster"
        src = UP / name if not PREVIEW else P / "final/segs/none"
        LOCK = P / "final/segs/locked" / name   # face_lock (inswapper, canon identity) where face_check failed and the lock held by eye
        sharpen = ""
        if not src.exists():   # sub-0.9 s cuts: lanczos from the scope crop + a light unsharp (no SeedVR2, see seedvr2_batch.py)
            src = P / "final/segs/scope" / name; sharpen = ",unsharp=5:5:0.6:5:5:0.0"
            if c["len"] >= 0.9 and not PREVIEW:
                if "--partial" in sys.argv: print("skip (SeedVR2 pending)", name); continue
                raise SystemExit(f"missing SeedVR2 output for held shot {name}")
        c["upscale"] = "seedvr2-3b 720p + lanczos" if not sharpen else "lanczos + unsharp"
        if LOCK.exists() and not PREVIEW:
            src = LOCK; c["face_lock"] = True
        f = (f"[0:v]trim=start_frame={m['pre']}:end_frame={m['pre']+m['n']},setpts=N/{FPS}/TB,"
             f"scale={FW}:{VH}:flags=lanczos{sharpen},format=gbrp")
        if c["id"] in BLOOM or c["section"] == "strobe":
            f += "," + bloom_chain(BLOOM.get(c["id"], 0.5))
        f += f",format=yuv420p,pad={FW}:{FH}:0:{BAR}:black[v]"
        pre = OUT / ("pre_" + name)
        if not (o.exists() and "--force" not in sys.argv):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-filter_complex", f, "-map", "[v]", "-frames:v", str(m["n"]),
                            "-r", str(FPS), "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", str(pre)], check=True)
            # the grade itself is bin/grade: LUT, grain, 2.39:1 scope bars drawn after the grain so the bars stay clean
            subprocess.run([str(ROOT / "bin/grade"), str(pre), str(o), "--lut", lut, "--grain", str(GRAIN), "--scope"], check=True)
            pre.unlink()
        c["lut"] = lut; c["bloom"] = BLOOM.get(c["id"], 0.5 if c["section"] == "strobe" else 0)
        lst.append(f"file '{o}'"); print(name, flush=True); continue
    cmd += ["-r", str(FPS), "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", str(o)]
    if not (o.exists() and "--force" not in sys.argv):
        subprocess.run(cmd, check=True)
    print(name, flush=True)
    lst.append(f"file '{o}'")
if "--partial" in sys.argv: raise SystemExit("partial pass done (no concat)")
(OUT / "list.txt").write_text("\n".join(lst) + "\n")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(OUT / "list.txt"), "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", str(FPS), str(P / ("final/preview_1080_picture.mp4" if PREVIEW else "final/picture_4k.mp4"))], check=True)
if not PREVIEW: json.dump(e, open(P / "final/edl_final_graded.json", "w"), indent=1)
print("picture_4k done")
