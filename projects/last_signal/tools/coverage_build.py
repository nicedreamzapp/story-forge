#!/usr/bin/env python3
"""coverage.json + manifest.json candidates + selects.json for THE LAST SIGNAL (frozen rule 29).
Coverage lines = the script's sections (hook, arrival, reveal, welcome, ramp incl. the strobe); black and the title card
carry no footage. Every take on disk (hq takes, previs drafts, Blender camera moves) is listed as coverage with its
duration; there is no design.json (no real product), so design checks are 'n/a'. Selects rank >= 2 takes per line
(rank 1 = what the cut uses, with in/out; rank 2 = the runner-up) with the builder's why from selects.md."""
import json, subprocess, glob, os
from pathlib import Path
P = Path(__file__).resolve().parent.parent
SEC = {"hook": ["R01", "R02", "R03"], "arrival": ["R04"], "reveal": ["R05", "R06", "R07", "R08", "R09", "R10"],
       "welcome": ["R11"], "ramp": ["R12", "R13", "R14", "R15", "R16", "R17", "R18", "R19", "R20"]}  # script v3: the strobe (beat 16) is part of the 0:25-0:42 RAMP
order = list(SEC)
def dur(f): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]))
files = sorted(glob.glob(str(P / "clips/takes/*.mp4"))) + sorted(glob.glob(str(P / "clips/previs/*.mp4")))
cands = []
for f in files:
    rel = os.path.relpath(f, P); rid = Path(f).stem.rsplit("_t", 1)[0]; pre = rid[:3]
    kind = "previs" if "previs" in rel else "hq"
    line = next((i + 1 for i, s in enumerate(order) if pre in SEC[s]), None)
    cands.append({"cid": f"{kind}_{Path(f).stem}", "file": rel, "line": line, "kind": "video", "dur": round(dur(f), 3),
                  "origin": "coverage", "source": "LTX-2.5 " + ("distilled previs" if kind == "previs" else "hq"), "checks": {"design": "n/a"}})
for f, line in (("ship/renders/anim_04_arrival.mp4", 2), ("ship/renders/anim_15_liftoff.mp4", 5)):
    cands.append({"cid": "blender_" + Path(f).stem, "file": f, "line": line, "kind": "video", "dur": round(dur(str(P / f)), 3),
                  "origin": "coverage", "source": "Blender Cycles camera move", "checks": {"design": "n/a"}})
e = json.load(open(P / "final/edl_final.json"))
sel_lines = []
for i, s in enumerate(order, 1):
    used = [c for c in e["cuts"] if (c["section"] == s or (s == "ramp" and c["section"] == "strobe")) and c["src"] and c["section"] != "title"]
    takes = []
    for c in used:
        cid = ("previs_" if "previs" in c["src"] else "hq_") + Path(c["src"]).stem
        takes.append({"cid": cid, "rank": 1, "cut": c["id"], "in": c["in"], "out": round(c["in"] + c["len"], 4)})
    usedc = {t["cid"] for t in takes}
    alts = [c["cid"] for c in cands if c["line"] == i and c["cid"] not in usedc]
    for a in alts[:max(2, len(alts))]:
        takes.append({"cid": a, "rank": 2})
    sel_lines.append({"line": i, "section": s, "takes": takes})
man = json.load(open(P / "manifest.json"))
man["candidates"] = cands
json.dump(man, open(P / "manifest.json", "w"), indent=1)
json.dump({"target_runtime": round(e["duration"]), "lines": [{"line": i, "section": s, "renders": SEC[s]} for i, s in enumerate(order, 1)]},
          open(P / "coverage.json", "w"), indent=1)
json.dump({"_why": "see stages/04_shots/selects.md", "lines": sel_lines}, open(P / "selects.json", "w"), indent=1)
print(len(cands), "candidates")
