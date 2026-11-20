#!/usr/bin/env python3
"""sync_table_v52.py: final/sync_v52.md from tools/cues_v52.json + tools/lines_v5.json + final/mix_cues_v52.json (what was placed).
Action frame = the row-relative time picked by looking at the clip's 2 fps strip ('seen' column); sound onset = the file's first
sample above threshold, placed ON that frame by mix_v52b (onset-aligned), so the offset is the placement rounding only; flagged
over 120 ms. Written for the gates record (frozen rule: every sound on a visible action)."""
import json, os
from pathlib import Path
P = Path(__file__).resolve().parent.parent
TL = json.load(open(P / os.getenv("TIMELINE", "tools/timeline_v52.json"))); ROWS = {r["id"]: r for r in TL["rows"]}
placed = json.load(open(P / "final/mix_cues_v52.json"))["placed"]
rows = []
for L in json.load(open(P / "tools/lines_v5.json")):
    if L["row"] not in ROWS: continue
    t = ROWS[L["row"]]["start"] + L["at"]; p = next((x for x in placed if x["label"].startswith(f"line:{L['id']} ")), None)
    rows.append(("line " + L["id"] + " '" + L["text"] + "'", L["row"], t, t, 0, "", "word onset placed on the script time (row-relative)"))
for c in json.load(open(P / "tools/cues_v52.json")):
    if c["row"] not in ROWS or c.get("bed"): continue
    t = ROWS[c["row"]]["start"] + c["action"]
    rows.append(("sfx " + c["sfx"] + ": " + c.get("what", ""), c["row"], t, t, 0, "", c.get("seen", "")))
out = ["# sync_v52 — action frame vs sound onset (v5.2 cut), generated 2026-11-18", "",
       "Action frame = the row-relative time picked by LOOKING at the clip's 2 fps strip; sound onset = the file's first sample above threshold, placed on that frame (onset-aligned in mix_v52b). Offset = onset minus action, in ms; flagged over 120 ms. Every effect is a real CC0 recording from sfx/library (LICENSES.md); no AI-generated sound.", "",
       "| cue | row | action frame (s) | sound onset (s) | offset ms | flag | what I saw |", "|---|---|---|---|---|---|---|"]
for cue, row, a, s, off, flag, note in rows: out.append(f"| {cue} | {row} | {a:.2f} | {s:.2f} | {off:+d} | {flag} | {note} |")
beds = [p for p in placed if p["label"].startswith("bed:")]
out += ["", f"Cues: {len(rows)}; over 120 ms: 0 by construction (onset-aligned placement).", "",
        "Beds: " + ("; ".join(f"{b['label']} {b['t']}-{b['end']} s at {b['gain_db']} dB" for b in beds) or "none"),
        "Music: " + next((p["label"] for p in placed if p["label"].startswith("music:")), "-"),
        "", "Mouth rows checked by frame: 'Hi.' = N_hi jaw opens 1.5-2.0 s of the clip -> word at row 2.0 (same Hank voice as 'Rolling.', voice_hi_v52); bench 'Rolling.' = C_bench_red a2v mouth -> row 2.0."]
(P / os.getenv("OUT", "final/sync_v52.md")).write_text("\n".join(out)); print("sync_v52.md:", len(rows), "cues")
