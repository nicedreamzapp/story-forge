#!/usr/bin/env python3
"""Cut every EDL segment out of its select at source res (832x448, 24 fps), exact frame counts, near-lossless,
into final/segs/. Also writes handle versions (+/-4 frames where the source has them) for SeedVR2 temporal
context, and final/cut_480.mp4 (the picture-only cut at source res, black + title included) for timing work."""
import json, subprocess
from pathlib import Path
P = Path(__file__).resolve().parent.parent
e = json.load(open(P / "final/edl_final.json")); FPS = e["fps"]
S = P / "final/segs"; S.mkdir(exist_ok=True); (S / "h").mkdir(exist_ok=True)
def nfr(src):
    return int(subprocess.check_output(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v", "-show_entries",
                                        "stream=nb_read_frames", "-of", "csv=p=0", str(src)]).strip())
lst = []; meta = []
for k, c in enumerate(e["cuts"]):
    o = S / f"{k:02d}_{c['id']}.mp4"
    if c["src"] is None:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=black:s=832x448:r={FPS}", "-frames:v", str(c["frames"]),
                        "-c:v", "libx264", "-crf", "4", "-pix_fmt", "yuv420p", str(o)], check=True)
    elif c["section"] == "title":
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(P / c["src"]), "-vf", "scale=832:448:flags=lanczos", "-frames:v", str(c["frames"]),
                        "-c:v", "libx264", "-crf", "4", "-pix_fmt", "yuv420p", str(o)], check=True)
    else:
        f0 = round(c["in"] * FPS); n = c["frames"]; tot = nfr(P / c["src"])
        assert f0 + n <= tot, (c["id"], f0, n, tot)
        vf = f"select='between(n\\,{f0}\\,{f0+n-1})',setpts=N/{FPS}/TB"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(P / c["src"]), "-vf", vf, "-frames:v", str(n), "-an",
                        "-c:v", "libx264", "-crf", "4", "-pix_fmt", "yuv420p", str(o)], check=True)
        h0 = max(0, f0 - 4); h1 = min(tot - 1, f0 + n - 1 + 4)
        ho = S / "h" / o.name
        vf = f"select='between(n\\,{h0}\\,{h1})',setpts=N/{FPS}/TB"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(P / c["src"]), "-vf", vf, "-an",
                        "-c:v", "libx264", "-crf", "4", "-pix_fmt", "yuv420p", str(ho)], check=True)
        meta.append({"seg": o.name, "pre": f0 - h0, "n": n, "post": h1 - (f0 + n - 1)})
    lst.append(f"file '{o}'")
(S / "list.txt").write_text("\n".join(lst) + "\n")
json.dump(meta, open(S / "handles.json", "w"), indent=1)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(S / "list.txt"), "-c:v", "libx264", "-crf", "10",
                "-pix_fmt", "yuv420p", "-r", str(FPS), str(P / "final/cut_480.mp4")], check=True)
d = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(P / "final/cut_480.mp4")]).decode().strip()
print("cut_480", d, "expected", e["duration"])
