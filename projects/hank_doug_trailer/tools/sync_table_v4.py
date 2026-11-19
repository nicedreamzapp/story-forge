"""sync_table_v4.py: final/sync_v4.md from final/mix_cues_v4.json (action frame vs sound onset, ms, flags) + the mouth rows."""
import json
from pathlib import Path
P = Path(__file__).resolve().parent.parent
d = json.load(open(P / "final/mix_cues_v4.json")); rows = d["sync"]
over = [r for r in rows if r.get("flag")]
out = ["# sync_v4 — action frame vs sound onset (v4 cut), generated 2026-11-18", "",
       "Action frame = the row-relative time I picked by LOOKING at the clip's 2 fps grid (or the code composite's frame); sound onset = the SFX/voice file's first sample above threshold, placed on that frame. Offset = onset minus action, in ms; flagged over 120 ms.", "",
       "| cue | row | action frame (s) | sound onset (s) | offset ms | flag | what I saw |", "|---|---|---|---|---|---|---|"]
for r in rows:
    out.append(f"| {r['cue']} | {r['row']} | {r['action_t']:.2f} | {r['sound_onset_t']:.2f} | {r['offset_ms']:+d} | {r.get('flag','')} | {r.get('note','')} |")
out += ["", f"Cues: {len(rows)}; over 120 ms: {len(over)}" + (": " + ", ".join(r["cue"] for r in over) if over else " (none)"),
        "", "Mouth rows checked by frame: 'Hi.' = N_hi jaw 2.0-2.7 of the clip -> word at row 2.0; bench 'Rolling.' = C_bench mouth opens at clip 2.4 (in 0.4) -> row 2.0;",
        "button 'Rolling.' = K_button_r2 mouth opens at clip 2.0 (in 0.6) -> row 1.4; row 7 'ditch' = N06 spoken from row 0.0, 'ditch' ~1.3 s in, splash frame at row 1.2.",
        "Montage cuts: theme_2 verse words measured by whisper word timestamps (music/theme_2_words.json): 'When a goat's' 9.5, 'turtle' ~11.4, 'kitten' ~13.7, 'drain' ~15.1 from the file; the cuts sit on those onsets (rows 12-15 starts).",
        "UNCHECKED: the sung word onsets inside theme_2 are whisper estimates (segment level in the json; word level only where present); by ear is Matt's."]
(P / "final/sync_v4.md").write_text("\n".join(out)); print("sync_v4.md:", len(rows), "cues,", len(over), "over 120 ms")
