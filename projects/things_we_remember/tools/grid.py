import subprocess, sys
from PIL import Image, ImageDraw
out, ids = sys.argv[1], sys.argv[2:]; W, H = 320, 180; sheet = Image.new("RGB", (W * 4, H * len(ids)))
for r, f in enumerate(ids):
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout)
    for c, t in enumerate([0.1, d * .35, d * .7, d - 0.15]):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", f, "-frames:v", "1", "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        im = Image.frombytes("RGB", (W, H), raw); ImageDraw.Draw(im).text((4, 4), f"{f.split('/')[-1]} {t:.1f}", fill=(255, 255, 0)); sheet.paste(im, (c * W, r * H))
sheet.save(out, quality=78)
