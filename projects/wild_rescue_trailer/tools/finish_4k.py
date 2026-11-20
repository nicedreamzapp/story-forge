#!/usr/bin/env python3
"""4K finish for HANK & DOUG'S WILD RESCUE (adapted from last_signal). Full-frame 16:9, no scope bars (animated family
trailers play full frame). Per picture segment: SeedVR2-3B output (final/segs/up/<seg>.mp4, 1280x720 from the 16:9
crop) -> drop the temporal handles -> exact 3840x2160 (lanczos) -> light bloom on the glowing shots (lantern, sparks,
sun glints, metal plates) -> per-section LUT through bin/grade (no grain: clean CG look). Sub-0.9 s cuts: lanczos from
the 16:9 crop + a light unsharp. Black + title card as-is. Concats to final/picture_4k.mp4 (no audio).
LUTs (timeline.json records them): the night origin moonlit_feature (cool, lantern stays amber), every day shot
warm_feature_pop (warm, saturated animated-feature), title untouched. --preview = 1080p proxy, lanczos everywhere."""
import json, subprocess, sys
from pathlib import Path
P = Path(__file__).resolve().parent.parent
ROOT = P.parent.parent
e = json.load(open(P / "final/edl_final.json")); FPS = e["fps"]
H = {m["seg"]: m for m in json.load(open(P / "final/segs/handles.json"))}
PREVIEW = "--preview" in sys.argv
UP = P / "final/segs/up"; OUT = P / ("final/segs/prev" if PREVIEW else "final/segs/4k"); OUT.mkdir(exist_ok=True)
FW, FH = (1920, 1080) if PREVIEW else (3840, 2160)
BLOOM = {"c01a_hunt": .45, "c01b_bear": .3, "c01c_eyes": .3, "c01d_away": .2, "c01e_ditch": .55, "c02a_rails": .45,
         "c07h_edge": .45, "c06b_river": .3, "c06a_ground": .25, "c07a_bridge": .25, "c07f_link": .2, "c07d_whistle": .3,
         "c03a_burst": .2, "c10b_doug_salute": .2, "c10a_ant_salute": .25}
def bloom_chain(s):
    K = 0.5 if PREVIEW else 1
    return (f"split=2[o][h1];[h1]curves=all='0/0 0.72/0 1/1',gblur=sigma={30*K},colorchannelmixer=rr=1.0:gg=0.82:bb=0.55[g];"
            f"[o][g]blend=all_mode=screen:all_opacity={0.6*s:.3f}")
lst = []
for k, c in enumerate(e["cuts"]):
    name = f"{k:02d}_{c['id']}.mp4"; o = OUT / name
    force = "--force" in sys.argv or (("--only" in sys.argv) and c["id"] in sys.argv)
    if c["src"] is None:
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=black:s={FW}x{FH}:r={FPS}", "-frames:v", str(c["frames"])]
    elif c["section"] == "title":
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(P / c["src"]), "-vf", f"scale={FW}:{FH}:flags=lanczos", "-frames:v", str(c["frames"])]
    else:
        m = H[name]; lut = "moonlit_feature" if c["section"] == "origin" else "warm_feature_pop"
        src = UP / name if not PREVIEW else P / "final/segs/none"; sharpen = ""
        if not src.exists():
            src = P / "final/segs/c169" / name; sharpen = ",unsharp=5:5:0.6:5:5:0.0"
            if c["len"] >= 0.9 and not PREVIEW:
                if "--partial" in sys.argv: print("skip (SeedVR2 pending)", name); continue
                raise SystemExit(f"missing SeedVR2 output for held shot {name}")
        c["upscale"] = ("blender cycles 2x render + lanczos" if "blender" in c["src"] else "seedvr2-3b 720p + lanczos") if not sharpen else "lanczos + unsharp"
        f = (f"[0:v]trim=start_frame={m['pre']}:end_frame={m['pre']+m['n']},setpts=N/{FPS}/TB,"
             f"scale={FW}:{FH}:flags=lanczos{sharpen},format=gbrp")
        if "blender" in c["src"]:   # match the painted LTX shots: Cycles renders read flatter and paler (checked 12:40)
            f += ",eq=saturation=1.28:contrast=1.08:gamma=0.97,colorbalance=rm=0.05:gm=0.01:bm=-0.05:rh=0.03:bh=-0.03"; c["match_grade"] = True
        if c["id"] in BLOOM: f += "," + bloom_chain(BLOOM[c["id"]])
        f += ",format=yuv420p[v]"
        pre = OUT / ("pre_" + name)
        if not o.exists() or force:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-filter_complex", f, "-map", "[v]", "-frames:v", str(m["n"]),
                            "-r", str(FPS), "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", str(pre)], check=True)
            subprocess.run([str(ROOT / "bin/grade"), str(pre), str(o), "--lut", lut], check=True, capture_output=True)
            pre.unlink()
        c["lut"] = lut; c["bloom"] = BLOOM.get(c["id"], 0)
        lst.append(f"file '{o}'"); print(name, flush=True); continue
    cmd += ["-r", str(FPS), "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", str(o)]
    if not o.exists() or force: subprocess.run(cmd, check=True)
    print(name, flush=True); lst.append(f"file '{o}'")
if "--partial" in sys.argv: raise SystemExit("partial pass done (no concat)")
(OUT / "list.txt").write_text("\n".join(lst) + "\n")
dst = P / ("final/preview_1080_picture.mp4" if PREVIEW else "final/picture_4k.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(OUT / "list.txt"), "-c:v", "libx264", "-crf", "14",
                "-preset", "medium", "-pix_fmt", "yuv420p", "-r", str(FPS), str(dst)], check=True)
if not PREVIEW: json.dump(e, open(P / "final/edl_final_graded.json", "w"), indent=1)
print(dst.name, "done")
