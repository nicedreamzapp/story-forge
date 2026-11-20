"""timeline_trailer_best.json = the trailer timeline with the kept HQ+SeedVR2 takes swapped in (t13, t18, t14)."""
import json, subprocess
from pathlib import Path
P = Path(__file__).resolve().parents[2]
subprocess.run(["python3", str(P / "tools/trailer/mk_tl.py")], check=True, capture_output=True)
tl = json.load(open(P / "timeline_trailer.json"))
SW = {"t13": "clip:final/segs/up_trailer/00_t13.mp4", "t18": "clip:final/segs/up_trailer/01_t18.mp4", "t14": "lips:final/segs/up_trailer/02_t14.mp4"}
for s in tl["shots"]:
    if s["id"] in SW and (P / SW[s["id"]].split(":", 1)[1]).exists(): s["src"] = SW[s["id"]]
json.dump(tl, open(P / "timeline_trailer_best.json", "w"), indent=1); print([s["src"] for s in tl["shots"] if s["id"] in SW])
