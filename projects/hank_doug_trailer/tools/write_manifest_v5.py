import json, os
from pathlib import Path
P = Path(__file__).resolve().parent.parent
rows = json.load(open(P / "tools/timeline_v5.json"))["rows"]; cues = json.load(open(P / "final/mix_cues_v5.json"))["placed"]
lines, narr, tl_n = [], [], []
for c in cues:
    if c["label"].startswith("line:"):
        tag, who, text = c["label"].split(":", 1)[1].split(" ", 2); lines.append({"t": c["t"], "speaker": who, "text": text})
        stem = {"L1": "L1_hank_rolling", "L4": "L4_younghank_hi", "L6": "L6_hank_rolling2"}.get(tag, "v4_" + tag)
        f = P / f"voices/nia_{stem}.wav"
        if not f.exists(): os.symlink(("v4/" + tag + ".wav") if tag.startswith("N") else ("v4/D01_s303.wav" if tag == "D01" else f"{stem.replace('v4_','')}.wav"), f)
        narr.append({"id": stem, "text": text}); tl_n.append([f"nia_{stem}.wav", c["t"]])
m = json.load(open(P / "manifest.json"))
m["characters"]["fox"] = "small red fox with a white chest and a black-tipped tail"
m["scenes"] = [{"name": r["id"], "start": r["start"], "end": round(r["start"] + r["dur"], 3)} for r in rows]
m["shots"] = [{"name": r["id"], "start": r["start"], "end": round(r["start"] + r["dur"], 3), "note": r["clip"]} for r in rows]
m["lines"] = lines; m["spec"]["duration"] = 57.4
json.dump(m, open(P / "manifest_v5.json", "w"), indent=1)
tl = json.load(open(P / "final/timeline.json"))
tl.update({"version": "v5 (script_v4 words, plan_v5 fixes, ending A no button)", "renderer": "tools/finish_v5.py", "order": [r["id"] for r in rows], "starts": [r["start"] for r in rows], "lens": [r["dur"] for r in rows],
           "narration": tl_n, "audio": "final/mix_v5.wav (tools/mix_v5.py), cues final/mix_cues_v5.json, sync final/sync_v5.md", "score": "music/breakdown_1.wav 0-36 (box from 0:00, one crossfade), stopdown 51.30-51.70, theme_2 build+verse+title line, theme_1 sting",
           "beats": [{"id": r["id"], "start": r["start"], "end": round(r["start"] + r["dur"], 3), "clip": r["clip"], "in": r["in"]} for r in rows]})
json.dump(tl, open(P / "final/timeline.json", "w"), indent=1); json.dump(narr, open(P / "narration.json", "w"), indent=1)
print("manifest_v5 + timeline + narration:", len(lines), "lines")
