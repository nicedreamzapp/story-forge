"""make_callouts.py — callouts.json from the Blender engine's own part tracking (track.json: every named part
projected to the frame with an occlusion ray, per rendered frame). For each callout: find the EDL shot that
plays its take at the cue word, map final-timeline time -> source frame -> the part's pixel, and write
[t, x, y] keyframes (normalized). A part that is occluded or off-frame in any keyframe is refused (said out loud).
Then add the callout cues to cues.json (idempotent)."""
import json, re, sys
from pathlib import Path
film = Path(__file__).resolve().parent.parent
V1 = Path.home() / "Desktop/PROJECTS/sitka-video/renders"
V3 = Path.home() / "Desktop/PROJECTS/sitka-video/v3/renders"
V4 = Path.home() / "Desktop/PROJECTS/sitka-video/v4/renders"
edl = json.loads((film / "edl.json").read_text())
words = json.loads((film / "vo/words.json").read_text())["words"]
norm = lambda w: re.sub(r"[^a-z0-9']", "", w.lower())
# (id, label, line, word, nth, end_word, end_nth, end_pad, take stem, part, text offset px)
SPEC = [
 ("sit_spring", "Carbon sit spring", 4, "spring", 1, "catches", 1, 0.5, "v1_s12_knee_sit_close", "sit_leaf_l", (-330, -170)),
 ("lift_tendon", "Lift tendon", 6, "tendon", 1, "energy", 1, 0.6, "v1_s16_tendon_back", "t3_tendon_l", (-300, -150)),
 ("one_motor", "One small motor", 8, "motor", 1, "need", 1, 0.0, "v1_s23_motor_back", "p1_motor", (260, -170)),
]


DESC = {"t3_tendon_l": "the lift tendon: the thin cream-coloured cable running down the back, where it passes through its metal guide ring",
        "ea_clutch_l": "the smart clutch: the round dark clutch housing on the thigh cuff",
        "sit_leaf_l": "the black carbon sit spring (the leaf spring) on the side of the thigh", "p1_motor": "the round motor hub on the back panel"}


def wt(line, word, nth):
    return [w for w in words if w["line"] == line and norm(w["word"]) == norm(word)][nth - 1]


out, cues_add, problems = [], [], []
for cid_, label, line, word, nth, ew, en, pad, stem, part, (dx, dy) in SPEC:
    t0 = wt(line, word, nth)["start"]; t1 = wt(line, ew, en)["start"] + pad
    sh = next((s for s in edl["shots"] if stem in s["cid"] and s["rec_in"] - 1e-3 <= t0 < s["rec_out"]), None)
    if sh is None:
        problems.append(f"{cid_}: no shot of {stem} under '{word}' at {t0:.2f}"); continue
    t1 = min(t1, sh["rec_out"] - 0.05)
    rd = V4 / ("v4_" + stem.replace("v1_", "") + "_final")       # v4 (mocap + look) renders, absolute frame numbers
    tr = json.loads((rd / "track.json").read_text())
    first = min(int(p.stem[1:]) for p in rd.glob("f*.png"))
    keys, bad = [], 0
    t = t0
    while t <= t1 + 1e-6:
        src = sh["src_in"] + (t - sh["rec_in"])
        f = int(round(src * 30))
        p = tr.get(str(f), {}).get(part)
        if p is None or p[3] == 0 or not (40 < p[0] < 1880 and 40 < p[1] < 1040):
            bad += 1
        else:
            keys.append([round(t, 3), round(p[0] / 1920, 4), round(p[1] / 1080, 4)])
        t += 1 / 15
    if bad > len(keys) * 0.2 or not keys:
        problems.append(f"{cid_}: {part} occluded/off-frame in {bad} of {bad + len(keys)} samples in {stem}; not used"); continue
    x0, y0 = keys[0][1], keys[0][2]
    out.append({"id": cid_, "label": label, "rec_in": round(t0, 3), "rec_out": round(t1, 3), "tip": keys,
                "text_at": [round(min(0.9, max(0.1, x0 + dx / 1920)), 3), round(min(0.88, max(0.12, y0 + dy / 1080)), 3)],
                "cid": sh["cid"], "part": DESC.get(part, part), "track_part": part})
    cues_add.append({"line": line, "word": word, "nth": nth, "kind": "callout", "callout": cid_})
(film / "callouts.json").write_text(json.dumps({"callouts": out}, indent=1))
cj = json.loads((film / "cues.json").read_text())
cj["cues"] = [c for c in cj["cues"] if c["kind"] != "callout"] + cues_add
(film / "cues.json").write_text(json.dumps(cj, indent=1))
print(f"{len(out)} callouts written:", [c["id"] for c in out])
for p in problems:
    print("REFUSED", p)
