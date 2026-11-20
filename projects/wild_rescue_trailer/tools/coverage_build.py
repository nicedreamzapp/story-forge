#!/usr/bin/env python3
"""shots.json + coverage.json + manifest.json + selects.json for WILD RESCUE (frozen rules 13, 29; adapted from
last_signal). Coverage lines = the script v3 sections; black and title carry no footage. Every take on disk (hq takes,
previs drafts, Blender camera moves) is listed as coverage with its duration (no design.json: design 'n/a').
Selects rank >= 2 takes per line (rank 1 = what the cut uses with in/out, rank 2 = runners-up; whys in selects.md).
The manifest also carries film_qc's schema: characters, scenes (one per on-screen character run), lines (voice timing)."""
import json, subprocess, glob, os
from pathlib import Path
P = Path(__file__).resolve().parent.parent
SEC = {"origin": ["R01", "R02", "R03", "R04", "R05"], "call": ["R06", "R07", "R08", "R09", "R10"],
       "theme": ["R11", "R12", "R13", "R14", "R15"], "stakes": ["R16", "R17"], "dialogue": ["R18", "R19"],
       "reveal": ["R20", "R21", "R22"], "ramp": ["R23", "R24", "R25", "R26", "R27", "R28", "R29", "R30"], "button": ["R31", "R32"]}
order = list(SEC)
def dur(f): return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]))
renders = json.load(open(P / "renders.json"))["renders"]
json.dump({"_note": "WILD RESCUE renders (one per render; cuts in beats.json map to these). LTX-2.5 bf16 MLX via bin/make-ltx25 "
           "--low-ram; previs distilled, final --hq on used shots only (tools/render_queue.py; R03/R15 re-rendered by tools/redo_queue.py).",
           "defaults": {"engine": "ltx25", "res": "832x480"},
           "shots": [{"id": r["id"], "lock": f"stills/LOCKED_{r['id']}.png", "beat": r["beat"], "clip_beat": r["clip_beat"],
                      "must_not": r["must_not"], "identity": r.get("identity") or [], "animate": r["animate"],
                      "static": bool(r.get("static"))} for r in renders]}, open(P / "shots.json", "w"), indent=1)
files = sorted(glob.glob(str(P / "clips/takes/*.mp4"))) + sorted(glob.glob(str(P / "clips/previs/*.mp4")))
cands = []
for f in files:
    rel = os.path.relpath(f, P); rid = Path(f).stem.rsplit("_t", 1)[0]; pre = rid[:3]
    kind = "previs" if "previs" in rel else "hq"
    line = next((i + 1 for i, s in enumerate(order) if pre in SEC[s]), None)
    cands.append({"cid": f"{kind}_{Path(f).stem}", "file": rel, "line": line, "kind": "video", "dur": round(dur(f), 3),
                  "origin": "coverage", "source": "LTX-2.5 " + ("distilled previs" if kind == "previs" else "hq"), "checks": {"design": "n/a"}})
for f in sorted(glob.glob(str(P / "blender/renders/*.mp4"))):
    nm = Path(f).stem.lower()
    line = 3 if ("wagon" in nm or "team" in nm) else (8 if "salute" in nm else 7 if ("ant" in nm or "bridge" in nm) else 4)
    cands.append({"cid": "blender_" + Path(f).stem, "file": os.path.relpath(f, P), "line": line, "kind": "video", "dur": round(dur(f), 3),
                  "origin": "coverage", "source": "Blender Cycles camera move", "checks": {"design": "n/a"}})
for stem, line in (("T_rails", 2), ("T_wide", 4), ("T_edge", 7)):   # mechanically correct Blender train animations (Matt 10:45)
    f = P / f"clips/blender/{stem}.mp4"
    if f.exists():
        cands.append({"cid": f"hq_{stem}", "file": os.path.relpath(f, P), "line": line, "kind": "video", "dur": round(dur(str(f)), 3),
                      "origin": "coverage", "source": "Blender Cycles animation (rigged wheels)", "checks": {"design": "n/a"}})
e = json.load(open(P / "final/edl_final.json"))
sel_lines = []
for i, s in enumerate(order, 1):
    used = [c for c in e["cuts"] if c["section"] == s and c["src"]]
    takes = []
    for c in used:
        cid = ("previs_" if "previs" in c["src"] else "hq_") + Path(c["src"]).stem
        takes.append({"cid": cid, "rank": 1, "cut": c["id"], "in": c["in"], "out": round(c["in"] + c["len"], 4)})
    usedc = {t["cid"] for t in takes}
    for a in [c["cid"] for c in cands if c["line"] == i and c["cid"] not in usedc]:
        takes.append({"cid": a, "rank": 2})
    sel_lines.append({"line": i, "section": s, "takes": takes})
cut = {c["id"]: c for c in e["cuts"]}
vc = json.load(open(P / "voices/voice_check.json"))
plan = {s["name"]: s for s in json.load(open(P / "sfx/mix_plan.json"))["sources"]}
def line(name, speaker, text, off):
    w = vc["takes"][vc["best"][name]]["words"]; st = plan[name]["start"] + (w[0]["s"] if w else 0)
    return {"t": round(st, 2), "dur": round((w[-1]["e"] - w[0]["s"]) if w else 1.0, 2), "speaker": speaker, "text": text, "offscreen": off}
def sc(name, ids): return {"name": name, "start": cut[ids[0]]["start"], "end": round(cut[ids[-1]]["start"] + cut[ids[-1]]["len"], 3)}
man = {"_note": "Coverage + alternates for WILD RESCUE (frozen rule 13 amended): every file listed survives until Matt approves the "
                "film; unlisted = corpse. characters/scenes/lines are film_qc's schema.",
       "previs": sorted(os.path.relpath(f, P) for f in glob.glob(str(P / "clips/previs/*.mp4"))),
       "takes": "clips/takes/*.mp4 (.done sidecars hold seed/time)", "previs_cut": "final/previs_cut.mp4",
       "candidates": cands,
       "characters": {"doug": "lanky red-brown bloodhound dog with very long droopy ears, wrinkled face and a brown leather collar",
                      "hank": "huge round gentle brown bear"},
       "scenes": [sc("forest_night", ["c01a_hunt", "c01e_ditch"]), sc("wagon_rollout", ["c03a_burst", "c03e_bench"]),
                  sc("canyon_dialogue", ["c05a_hank", "c05b_doug"]), sc("ramp", ["c07a_bridge", "c07i_rush"]),
                  sc("button", ["c10a_ant_salute", "c10b_doug_salute"])],
       "lines": [line("doug1", "doug", "I picked a side.", True), line("hank1", "hank", "Doug... that's a big hole.", False),
                 line("doug2", "doug", "Then we need a lot of help.", False)],
       "_film_qc_note": "Doug's first line is voice-over (low, over the lantern in the ditch); Hank and Doug speak on camera at the rim."}
json.dump(man, open(P / "manifest.json", "w"), indent=1)
json.dump({"target_runtime": round(e["duration"]), "lines": [{"line": i, "section": s, "renders": SEC[s]} for i, s in enumerate(order, 1)]},
          open(P / "coverage.json", "w"), indent=1)
json.dump({"_why": "see stages/04_shots/selects.md", "lines": sel_lines}, open(P / "selects.json", "w"), indent=1)
print(len(cands), "candidates")
