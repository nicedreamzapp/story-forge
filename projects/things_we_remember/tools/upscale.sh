#!/bin/bash
# 1080p upscale of the HQ takes: Refine-Details on faces (s04, s07, s11), SeedVR2 on s01 and s08 (upscale-route, Matt's 11/02 rule).
P=~/Desktop/PROJECTS/story-forge/projects/things_we_remember; cd $P
python3 - <<'PY'
import json, shutil
cuts = [("s01", "seedvr2"), ("s04", "refine"), ("s07", "refine"), ("s08", "seedvr2"), ("s11", "refine")]
for k, (sid, u) in enumerate(cuts): shutil.copy(f"clips/hq/{sid}.mp4", f"final/segs/hq/{k:02d}_{sid}.mp4")
json.dump({"cuts": [{"id": s, "shot": s, "len": 4.0, "upscale": u} for s, u in cuts]}, open("final/edl_hq.json", "w"), indent=1)
PY
date +%T > tools/t_up_start
~/Desktop/PROJECTS/story-forge/bin/upscale-route $P --edl final/edl_hq.json --segs final/segs/hq --out final/segs/up > upscale.log 2>&1
date +%T > tools/t_up_end; echo UP_DONE >> upscale.log
