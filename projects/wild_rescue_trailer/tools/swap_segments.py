#!/usr/bin/env python3
"""Re-cut only the named EDL segments (segs, 16:9 handle crop, handles.json) without touching the others (SeedVR2 is
reading final/segs/c169 while it runs), rebuild final/cut_480.mp4, and for Blender-sourced cuts write the SeedVR2
up/ file straight from the 2x render (1664x896 -> 16:9 crop 1592x896, same handle frames) so the queue skips them.
Usage: swap_segments.py c02a_rails c04a_train c07h_edge"""
import json, subprocess, sys
from pathlib import Path
P = Path(__file__).resolve().parent.parent
e = json.load(open(P / "final/edl_final.json")); FPS = e["fps"]; S = P / "final/segs"
H = {m["seg"]: m for m in json.load(open(S / "handles.json"))}
def nfr(src):
    return int(subprocess.check_output(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v", "-show_entries",
                                        "stream=nb_read_frames", "-of", "csv=p=0", str(src)]).strip())
for k, c in enumerate(e["cuts"]):
    if c["id"] not in sys.argv[1:]: continue
    name = f"{k:02d}_{c['id']}.mp4"; src = P / c["src"]
    f0 = round(c["in"] * FPS); n = c["frames"]; tot = nfr(src); assert f0 + n <= tot, (name, f0, n, tot)
    h0 = max(0, f0 - 4); h1 = min(tot - 1, f0 + n - 1 + 4)
    sel = lambda a, b: f"select='between(n\\,{a}\\,{b})',setpts=N/{FPS}/TB"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", sel(f0, f0 + n - 1), "-frames:v", str(n), "-an", "-c:v", "libx264", "-crf", "4", "-pix_fmt", "yuv420p", str(S / name)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", sel(h0, h1) + ",crop=796:448:18:0", "-an", "-c:v", "libx264", "-crf", "4", "-pix_fmt", "yuv420p", str(S / "c169" / name)], check=True)
    H[name] = {"seg": name, "pre": f0 - h0, "n": n, "post": h1 - (f0 + n - 1)}
    big = src.with_name(src.stem + "_2x.mp4")
    if big.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(big), "-vf", sel(h0, h1) + ",crop=1592:896:36:0", "-an", "-c:v", "libx264", "-crf", "8", "-pix_fmt", "yuv420p", str(S / "up" / name)], check=True)
    print("swapped", name, H[name])
json.dump(sorted(H.values(), key=lambda m: m["seg"]), open(S / "handles.json", "w"), indent=1)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(S / "list.txt"), "-c:v", "libx264", "-crf", "10", "-pix_fmt", "yuv420p", "-r", str(FPS), str(P / "final/cut_480.mp4")], check=True)
print("cut_480 rebuilt")
