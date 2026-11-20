#!/usr/bin/env python3
"""HANK & DOUG'S WILD RESCUE final cut (part 2, 2026-11-01). Writes final/edl_final.json: every cut, its select,
in-point, length, timeline start, section. Selects + whys: stages/04_shots/selects.md (frame-grid look + VL clip gate).
Beat map (script v3): origin 0-6.3 (Doug VO "I picked a side." over the lantern in the ditch), call 6.3-10.3,
THEME HIT on the wagon burst 10.3, stakes, DEAD STOP for Hank's line + Doug's answer (cut to Doug on his first word),
reveal (swell restarts on the moving ground), ramp (fast cuts), smash to black 1.0 s, title 3.0 s, ant-salute button.
Dialogue cut lengths come from the picked voice takes (voices/voice_check.json) when they exist."""
import json
from pathlib import Path
P = Path(__file__).resolve().parent.parent
T = lambda r, n: f"clips/takes/{r}_t{n}.mp4"
V = lambda r: f"clips/previs/{r}_t1.mp4"
pick = json.load(open(P / "stages/04_shots/picks.json")) if (P / "stages/04_shots/picks.json").exists() else {}
R03 = pick.get("R03_eye_contact", T("R03_eye_contact", 2)); R15 = pick.get("R15_bench", T("R15_bench", 1))
dur = {}
vc = P / "voices/voice_check.json"
if vc.exists():
    v = json.load(open(vc)); dur = {l: v["takes"][n]["dur"] for l, n in v["best"].items()}
hank_len = min(2.6, max(2.0, dur.get("hank1", 2.0) + 0.45))
doug_len = min(2.4, max(1.9, dur.get("doug2", 1.6) + 0.5))
cuts = [  # id, src, in, len, section
 ("c01a_hunt",        T("R01_night_hunt", 1),       0.3, 1.5, "origin"),
 ("c01b_bear",        T("R02_bear_hiding", 1),      0.7, 1.0, "origin"),
 ("c01c_eyes",        R03,                          0.5, 1.3, "origin"),
 ("c01d_away",        T("R04_doug_leads_away", 2),  0.1, 1.0, "origin"),
 ("c01e_ditch",       T("R05_lantern_ditch", 1),    0.45, 1.5, "origin"),
 ("c02a_rails",       "clips/blender/T_rails.mp4",  4/24, 0.8, "call"),   # Blender: mechanically correct wheels (Matt 10:45)
 ("c02b_ears",        V("R07_rabbit_ears"),         0.3, 0.9, "call"),
 ("c02c_thump",       V("R08_rabbit_thump"),        0.4, 0.8, "call"),
 ("c02d_hawk",        V("R09_hawk_cry"),            0.1, 0.8, "call"),
 ("c02e_prairie",     V("R10_prairie_whistle"),     1.5, 0.7, "call"),
 ("c03a_burst",       T("R11_wagon_burst", 1),      0.0, 1.5, "theme"),
 ("c03b_wheel",       V("R12_wheel"),               0.6, 0.9, "theme"),
 ("c03c_team",        T("R13_team", 1),             0.6, 1.0, "theme"),
 ("c03d_crew",        T("R14_crew_side", 1),        0.3, 1.2, "theme"),
 ("c03e_bench",       R15,                          0.3, 1.4, "theme"),
 ("c04a_train",       "clips/blender/T_wide.mp4",   4/24, 1.5, "stakes"), # Blender
 ("c04b_gap",         T("R17_tracks_end", 1),       0.6, 1.5, "stakes"),
 ("c05a_hank",        T("R18_hank_line", 1),        0.05, 2.85, "dialogue"),   # mouth_sync: opens 0.12-0.38 ("Doug...") + 1.54-2.83
 ("c05b_doug",        T("R19_doug_line", 3),        0.58, 2.0, "dialogue"),    # mouth_sync: talking 0.62-1.96
 ("c06a_ground",      T("R20_ground_moves", 1),     0.3, 1.2, "reveal"),
 ("c06b_river",       T("R21_ant_river", 3),        0.5, 1.6, "reveal"),
 ("c06c_hero_ant",    T("R22_ant_hero", 1),         0.3, 1.2, "reveal"),
 ("c07a_bridge",      T("R23_ant_bridge", 2),       0.35, 1.2, "ramp"),
 ("c07b_giraffes",    V("R24_giraffes_spot"),       0.1, 0.8, "ramp"),
 ("c07c_trumpet",     T("R25_elephant_trumpet", 1), 0.05, 0.8, "ramp"),
 ("c07d_whistle",     V("R26_whistle"),             1.0, 0.8, "ramp"),
 ("c07e_monkey",      T("R27_monkey_eyes", 1),      0.3, 0.8, "ramp"),
 ("c07f_link",        V("R28_bridge_link"),         1.8, 0.8, "ramp"),
 ("c07g_doug",        T("R29_doug_tense", 2),       0.5, 0.8, "ramp"),
 ("c07h_edge",        "clips/blender/T_edge.mp4",   4/24, 1.2, "ramp"),   # Blender
 ("c07i_rush",        T("R17_tracks_end", 2),       2.2, 0.8, "ramp"),
 ("c08_black",        None,                         0.0, 1.0, "black"),
 ("c09_title",        "final/title/title_card.mp4", 0.0, 3.0, "title"),
 ("c10a_ant_salute",  T("R31_ant_salute", 3),       0.4, 1.8, "button"),
 ("c10b_doug_salute", T("R32_doug_salute", 3),      0.6, 2.0, "button"),
]
FPS = 24
edl, t = [], 0.0
for cid, src, i, ln, sec in cuts:
    nf = round(ln * FPS); ln = nf / FPS
    edl.append({"id": cid, "src": src, "in": i, "len": round(ln, 4), "frames": nf, "start": round(t, 4), "section": sec})
    t += ln
json.dump({"fps": FPS, "size": [832, 480], "duration": round(t, 4), "cuts": edl}, open(P / "final/edl_final.json", "w"), indent=1)
print(f"{len(edl)} cuts, {t:.2f}s; hank {hank_len:.2f}s doug {doug_len:.2f}s; R03={R03} R15={R15}")
