#!/usr/bin/env python3
"""Current-cut gate files from TWR_TL (+ TWR_TEXTS): manifest.json (film_qc), final/timeline.json (continuity/face
checks) and texts.json (read-time). Teaser originals are kept as manifest_teaser.json / final/timeline_teaser.json /
texts_teaser.json. Coverage lists EVERY kept take in the project (all cuts share one take pool)."""
import json, os, glob, shutil, soundfile as sf
from pathlib import Path
P = Path(__file__).resolve().parent.parent; TL = json.load(open(P / os.environ["TWR_TL"]))
TEXT = json.load(open(P / "voice/lines.json"))
CH = {"claire": "a woman in her late thirties with wavy chestnut-brown hair, freckles, a faded blue cardigan",
      "ruth": "an old woman in her seventies with curled silver-white hair, wire glasses, a lavender cardigan",
      "lily": "a seven-year-old girl with blonde hair in two braids, a pale yellow dress",
      "lily3": "the same girl at three years old in old home-video footage: blonde pigtails, a white sundress",
      "tom": "a man in his early forties with short sandy-brown hair and a short beard, a gray henley shirt",
      "daniel": "a small boy, only ever seen from behind under a quilt (voice is a whisper)",
      "rememberer": "a man in an old gray suit, only ever seen in shadow, out of focus or in a reflection"}
lines = []
for lid, L in sorted(TL["lines"].items(), key=lambda kv: kv[1]["t"]):
    w = L.get("wav", lid); y, r = sf.read(str(P / "voice/trimmed" / f"{w}.wav"))
    e = {"t": L["t"], "dur": round(len(y) / r, 2), "speaker": L["spk"], "text": TEXT[w][1], "id": lid}
    if not L.get("onscreen"): e["offscreen"] = True
    lines.append(e)
M = {"characters": CH, "scenes": TL.get("scenes", [{"name": "all", "start": 0, "end": TL["end"]}]), "lines": lines,
     "shots": [{"name": s["id"] + "_" + s["src"].replace(":", "_").replace("/", "_"), "start": s["s"], "end": s["e"]} for s in TL["shots"]],
     "spec": {"width": 1920, "height": 1080, "fps": 24, "lufs": -14}, "cut": os.environ["TWR_TL"]}
M["coverage"] = {"note": "every kept take per shot, all cuts; alternates survive until the film is approved (frozen rule 13)",
                 "takes": sorted(os.path.relpath(f, P) for f in glob.glob(str(P / "clips/**/*.mp4"), recursive=True) + glob.glob(str(P / "final/segs/up/*.mp4")))}
json.dump(M, open(P / "manifest.json", "w"), indent=1)
json.dump({"order": [s["id"] for s in TL["shots"]], "starts": [s["s"] for s in TL["shots"]], "lens": [round(s["e"] - s["s"], 3) for s in TL["shots"]],
           "narration": [[lid, L["t"]] for lid, L in TL["lines"].items()]}, open(P / "final/timeline.json", "w"), indent=1)
if os.environ.get("TWR_TEXTS"): shutil.copy(P / os.environ["TWR_TEXTS"], P / "texts.json")
print(len(lines), "lines,", len(M["coverage"]["takes"]), "takes")
