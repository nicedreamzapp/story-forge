#!/usr/bin/env python3
"""Rebuild the Sitka design-check calibration stills from the CAD renders.

PASS stills are untouched CAD frames (plus a horizontal mirror: a mirrored side view is the
other side of the same correct device, NOT a design error, so it is a control the judge must
pass). FAIL stills are PLANTED-WRONG edits of the seated side view (rearleg_deploy.mp4 end):
rear legs erased, a rear leg painted in front of the knee, a duplicated rear leg, the frame
flipped upside down (legs ending in the air), wheels painted on the feet of the legs.

  ~/.local/mlx-server/bin/python pipeline-tools/calibration/design/sitka/make_planted.py
"""
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageOps

HERE = Path(__file__).resolve().parent
SRC = Path.home() / "Desktop/PROJECTS/sitka-video/footage"
OUT = HERE / "stills"


def grab(clip, t, out, from_end=False):
    args = ["ffmpeg", "-v", "error", "-y"] + (["-sseof", f"-{t}"] if from_end else ["-ss", str(t)])
    subprocess.run(args + ["-i", str(SRC / clip), "-frames:v", "1", str(out)], check=True)
    return out


def rod_mask(size):
    """The two rear legs in the 1920x1080 seated side view (near rod + far rod)."""
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    d.line([(870, 625), (770, 957)], fill=255, width=30)     # near rear leg
    d.ellipse([(745, 940), (800, 970)], fill=255)            # its foot
    d.line([(842, 690), (800, 890)], fill=255, width=26)     # far rear leg
    d.ellipse([(785, 875), (820, 900)], fill=255)
    return m


def erase(img, mask):
    a = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    out = cv2.inpaint(a, np.array(mask), 9, cv2.INPAINT_TELEA)
    return Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base_p = grab("rearleg_deploy.mp4", 4.6, OUT / "pass_side_seated.png")
    grab("chair_orbit_overlay.mp4", 7.6, OUT / "pass_side_orbit.png")
    grab("chair_orbit_overlay.mp4", 1.0, OUT / "pass_threequarter_orbit.png")
    base = Image.open(base_p).convert("RGB")
    ImageOps.mirror(base).save(OUT / "pass_mirror_h.png")

    mask = rod_mask(base.size)
    no_leg = erase(base, mask)
    no_leg.save(OUT / "fail_no_rear_leg.png")

    front = no_leg.copy()
    d = ImageDraw.Draw(front)
    d.line([(1100, 700), (1215, 958)], fill=(22, 22, 26), width=16)   # rod from the knee, forward
    d.ellipse([(1190, 945), (1245, 970)], fill=(30, 30, 34))
    d.ellipse([(1092, 692), (1112, 712)], fill=(120, 120, 128))
    front.save(OUT / "fail_leg_in_front_of_knee.png")

    dup = base.copy()
    near = Image.new("L", base.size, 0)
    ImageDraw.Draw(near).line([(870, 625), (770, 957)], fill=255, width=22)
    ImageDraw.Draw(near).ellipse([(745, 940), (800, 970)], fill=255)
    dup.paste(base.crop((0, 0, *base.size)), (-130, 0), near)          # rod copy 130 px back
    dup.save(OUT / "fail_duplicate_rear_leg.png")

    ImageOps.flip(base).save(OUT / "fail_upside_down.png")

    wheels = base.copy()
    d = ImageDraw.Draw(wheels)
    for cx, cy, r in [(772, 945, 34), (803, 880, 28)]:
        d.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=(25, 25, 25), outline=(150, 150, 150), width=5)
        d.ellipse([(cx - 8, cy - 8), (cx + 8, cy + 8)], fill=(170, 170, 170))
    wheels.save(OUT / "fail_wheels_on_legs.png")
    print("\n".join(sorted(p.name for p in OUT.iterdir())))


if __name__ == "__main__":
    main()
