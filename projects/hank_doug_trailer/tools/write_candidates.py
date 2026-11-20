import json, glob, subprocess
from pathlib import Path
still2beat = {"A_": ["b00_linen", "b01_ripple"], "B_": ["b01_ripple", "b02_whistle"], "C_": ["b03_bench"], "D_": ["b04_rollout"], "L_": ["b05_airlift"], "E_": ["b06_turtle"],
              "F_": ["b07_kitten"], "M_": ["b08_otters"], "G_": ["b09_oldpaint"], "N_": ["b10_hi"], "H1": ["b11_ditch"], "H2": ["b11_ditch"], "I_": ["b12_walkaway"], "J_": ["b13_title"], "K_": ["b14_button"], "X_": ["b14_button"]}
cands = []
for p in sorted(glob.glob("stills/*.png")):
    for b in still2beat.get(Path(p).name[:2], []):
        cands.append({"cid": Path(p).stem + ":" + b, "line": b, "kind": "image", "file": p, "checks": {"design": "n/a"}})
for p in sorted(glob.glob("clips/**/*.mp4", recursive=True)):
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip() or 0)
    for b in still2beat.get(Path(p).name[:2], []):
        cands.append({"cid": Path(p).stem + ":" + b, "line": b, "kind": "video", "dur": d, "file": p, "checks": {"design": "n/a"}})
m = json.load(open("manifest.json")); m["candidates"] = cands; json.dump(m, open("manifest.json", "w"), indent=1); print(len(cands), "candidates")
