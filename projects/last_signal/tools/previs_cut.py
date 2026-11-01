#!/usr/bin/env python3
"""Rough previs edit from clips/previs/ against the v3 cut list (beats.json), plus final_plan.json.
Cuts from the same render take successive windows of the clip (0.4s in, then onward) so repeats differ.
Writes final/previs_cut.mp4, final/previs_edl.json, final_plan.json."""
import json, subprocess, tempfile
from pathlib import Path
P = Path(__file__).resolve().parent.parent
FF = "/opt/homebrew/bin/ffmpeg"
beats = json.load(open(P / "beats.json"))["shots"]
renders = {r["id"]: r for r in json.load(open(P / "renders.json"))["renders"]}
cursor, edl, segs = {}, [], []
tmp = Path(tempfile.mkdtemp())
for i, s in enumerate(beats):
    out = tmp / f"{i:02d}.mp4"
    if not s.get("render"):
        subprocess.run([FF, "-v", "error", "-y", "-f", "lavfi", "-i", f"color=black:s=832x448:r=24:d={s['seconds']}",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)], check=True)
        edl.append({"id": s["id"], "src": None, "in": 0, "len": s["seconds"]})
    else:
        rid = s["render"]; src = P / f"clips/previs/{rid}_t1.mp4"
        t = cursor.get(rid, 0.4)
        if t + s["seconds"] > 4.9: t = 0.4
        cursor[rid] = t + s["seconds"] + 0.3
        subprocess.run([FF, "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(src), "-t", f"{s['seconds']:.2f}",
                        "-vf", "scale=832:448,fps=24", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)], check=True)
        edl.append({"id": s["id"], "render": rid, "src": str(src.relative_to(P)), "in": round(t, 2), "len": s["seconds"]})
    segs.append(out)
lst = tmp / "list.txt"; lst.write_text("".join(f"file '{x}'\n" for x in segs))
subprocess.run([FF, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(P / "final/previs_cut.mp4")], check=True)
json.dump(edl, open(P / "final/previs_edl.json", "w"), indent=1)
# final plan: what the cut uses, at cut length + handles
use = {}
for e in edl:
    if e.get("render"):
        u = use.setdefault(e["render"], {"cuts": [], "need": 0.0})
        u["cuts"].append(e["id"]); u["need"] = max(u["need"], e["in"] + e["len"])
STROBE_ONLY = {rid for rid, u in use.items() if all(c.startswith("c16") for c in u["cuts"])}
SPINE2 = {"R02_cockpit_alarm", "R09_captain_face", "R11_captain_welcome", "R13_crewmate_yanked", "R17_captain_sprint"}
plan = []
for rid, u in use.items():
    if rid in STROBE_ONLY: continue
    r = renders[rid]
    takes = 3 if r["hero"] else (2 if rid in SPINE2 else 1)
    plan.append({"id": rid, "takes": takes, "seconds": round(min(5.0, u["need"] + 0.5), 2), "cuts": u["cuts"]})
json.dump(plan, open(P / "final_plan.json", "w"), indent=1)
print(f"previs_cut: {len(edl)} cuts, {sum(e['len'] for e in edl):.1f}s; final plan {len(plan)} renders, "
      f"{sum(p['takes'] for p in plan)} takes, {sum(p['takes']*p['seconds'] for p in plan):.1f}s of footage; previs kept as-is: {sorted(STROBE_ONLY)}")
