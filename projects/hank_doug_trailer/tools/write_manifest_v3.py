import json, os
from pathlib import Path
P = Path(__file__).resolve().parent.parent
cuts = json.load(open(P / "final/cuts_v3.json"))["cuts"]; cues = json.load(open(P / "final/mix_cues_v3.json"))["placed"]
lines = []; narr = []; tl_n = []
for c in cues:
    if c["label"].startswith("line:"):
        tag, who, text = c["label"].split(":", 1)[1].split(" ", 2)
        lines.append({"t": c["t"], "speaker": who, "text": text})
        stem = {"L1": "L1_hank_rolling", "N1": "N1_narrator_heart", "L2": "L2_doug_longago", "L3": "L3_doug_metone", "L4": "L4_younghank_hi", "L5": "L5_doug_samenose", "L6": "L6_hank_rolling2"}[tag]
        narr.append({"id": stem, "text": text}); tl_n.append([f"nia_{stem}.wav", c["t"]])
m = json.load(open(P / "manifest.json"))
m["scenes"] = [{"name": c["id"], "start": c["start"], "end": round(c["start"] + c["dur"], 3)} for c in cuts]
m["shots"] = [{"name": c["id"], "start": c["start"], "end": round(c["start"] + c["dur"], 3), "note": c["clip"]} for c in cuts]
m["lines"] = lines; m["spec"]["duration"] = round(sum(c["dur"] for c in cuts), 2)
json.dump(m, open(P / "manifest_v3.json", "w"), indent=1)
tl = json.load(open(P / "final/timeline.json"))
tl.update({"version": "v3 fix pass", "renderer": "tools/finish_v3.py (straight cuts, no code paint layers)", "order": [c["id"] for c in cuts], "starts": [c["start"] for c in cuts], "lens": [c["dur"] for c in cuts],
           "narration": tl_n, "audio": "final/mix_v3.wav (tools/mix_v3.py), cue list final/mix_cues_v3.json", "score": "music/theme_2.wav (sung sections) + music/breakdown_1.wav + theme_1 sting",
           "beats": [{"id": c["id"], "start": c["start"], "end": round(c["start"] + c["dur"], 3), "clip": c["clip"]} for c in cuts]})
json.dump(tl, open(P / "final/timeline.json", "w"), indent=1); json.dump(narr, open(P / "narration.json", "w"), indent=1)
# continuity_check's beat ids changed (b00_goat etc): map continuity rules' shot ids to the v3 ids where names differ
print("manifest_v3 + timeline + narration written:", len(lines), "lines,", len(cuts), "cuts")
