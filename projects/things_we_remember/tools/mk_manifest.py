#!/usr/bin/env python3
"""manifest.json for film_qc + final/timeline.json for continuity_check, from timeline.json + trimmed line lengths."""
import json, soundfile as sf
from pathlib import Path
P = Path(__file__).resolve().parent.parent; TL = json.load(open(P / "timeline.json"))
TEXT = json.load(open(P / "voice/lines.json"))
lines = []
for lid, L in TL["lines"].items():
    y, r = sf.read(str(P / "voice/trimmed" / f"{lid}.wav")); e = {"t": L["t"], "dur": round(len(y) / r, 2), "speaker": L["spk"], "text": TEXT[lid][1], "id": lid}
    if not L.get("onscreen"): e["offscreen"] = True
    lines.append(e)
M = {"characters": {"claire": "a woman in her late thirties with wavy chestnut-brown hair, freckles, a faded blue cardigan",
                    "ruth": "an old woman in her seventies with curled silver-white hair, wire glasses, a lavender cardigan",
                    "lily": "a seven-year-old girl with blonde hair in two braids, a pale yellow dress",
                    "daniel": "a small boy, only ever seen from behind under a quilt (voice is a whisper)",
                    "rememberer": "a man in an old gray suit, only ever seen in shadow, out of focus or in a reflection"},
     "scenes": [{"name": "warm", "start": 0, "end": 14.5}, {"name": "wrong", "start": 14.5, "end": 31.7}, {"name": "end", "start": 32.7, "end": TL["end"]}],
     "lines": lines,
     "shots": [{"name": s["id"] + "_" + s["src"].replace(":", "_"), "start": s["s"], "end": s["e"]} for s in TL["shots"]],
     "spec": {"width": 1920, "height": 1080, "fps": 24, "lufs": -14}}
import glob, os
M["coverage"] = {"note": "every kept take per shot; alternates survive until the film is approved (frozen rule 13)",
                 "takes": sorted(os.path.relpath(f, P) for f in glob.glob(str(P / "clips/**/*.mp4"), recursive=True) + glob.glob(str(P / "final/segs/up/*.mp4")))}
json.dump(M, open(P / "manifest.json", "w"), indent=1)
json.dump({"order": [s["id"] for s in TL["shots"]], "starts": [s["s"] for s in TL["shots"]], "lens": [round(s["e"] - s["s"], 3) for s in TL["shots"]],
           "narration": [[f"{lid}", L["t"]] for lid, L in TL["lines"].items()]}, open(P / "final/timeline.json", "w"), indent=1)
print(len(lines), "lines")
