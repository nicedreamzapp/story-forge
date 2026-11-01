#!/usr/bin/env python3
"""THE LAST SIGNAL final cut plan (part 2, 2026-10-31). Writes final/edl_final.json (every cut, its select,
in-point, length and timeline start), from the builder's frame-grid selects (stages/04_shots/selects.md).
Beat map (script v3): hook 0-7.0, arrival 7.0-11.4, reveal 11.4-21.5, welcome 21.5-25.3 (beat stops dead),
ramp 25.3-35.4, strobe 35.4-41.0, black 41.0-43.6 (1 s silence, whisper at 42.0), title slam 43.6-46.6."""
import json
from pathlib import Path
P = Path(__file__).resolve().parent.parent
T = lambda r, n: f"clips/takes/{r}_t{n}.mp4"
V = lambda r: f"clips/previs/{r}_t1.mp4"
cuts = [  # id, src, in, len, section
 ("c01_asteroids",       V("R01_asteroids"),        0.4, 1.5, "hook"),
 ("c02a_cockpit",        T("R02_cockpit_alarm", 2), 0.2, 1.0, "hook"),
 ("c02b_lever",          T("R02_cockpit_alarm", 2), 1.6, 0.9, "hook"),
 ("c01b_asteroids_close",V("R01_asteroids"),        2.6, 0.9, "hook"),
 ("c03_dive",            T("R03_dive", 1),          0.3, 1.5, "hook"),
 ("c03b_dive_clouds",    T("R03_dive", 1),          1.9, 1.2, "hook"),
 ("c04_arrival",         T("R04_arrival", 1),       0.15, 4.4, "arrival"),
 ("c05_claws",           T("R05_claws", 1),         0.15, 1.2, "reveal"),
 ("c06_monolith_reveal", T("R06_monolith_reveal", 2), 0.2, 1.6, "reveal"),
 ("c06b_crew_walk",      T("R07_crew_walk", 1),     0.2, 1.3, "reveal"),
 ("c07_handwriting",     T("R08_handwriting_glow", 1), 0.3, 2.0, "reveal"),
 ("c07b_captain_face",   T("R09_captain_face", 2),  0.4, 1.4, "reveal"),
 ("c08_lightwave",       T("R10_lightwave", 1),     0.4, 2.6, "reveal"),
 ("c09_welcome",         T("R11_captain_welcome", 2), 0.2, 3.8, "welcome"),
 ("c10_second_sun",      T("R12_second_sun", 1),    0.3, 1.0, "ramp"),
 ("c11_yanked",          T("R13_crewmate_yanked", 1), 0.05, 0.9, "ramp"),
 ("c12_engines",         T("R14_engines_fire", 1),  0.1, 0.9, "ramp"),
 ("c13_mountain",        T("R15_mountain_shape", 1), 0.3, 1.0, "ramp"),
 ("c14_boots",           T("R16_boots_crack", 1),   0.2, 0.7, "ramp"),
 ("c14b_sprint",         T("R17_captain_sprint", 2), 0.3, 0.7, "ramp"),
 ("c15_grab",            T("R18_ship_grab", 2),     0.3, 0.9, "ramp"),
 ("c11b_yanked",         T("R13_crewmate_yanked", 2), 0.1, 0.6, "ramp"),
 ("c12b_engines",        V("R14_engines_fire"),     0.5, 0.6, "ramp"),
 ("c13b_mountain",       T("R15_mountain_shape", 3), 1.8, 0.7, "ramp"),
 ("c14c_boots",          T("R16_boots_crack", 1),   1.2, 0.5, "ramp"),
 ("c15b_grab",           T("R18_ship_grab", 3),     1.6, 0.6, "ramp"),
 ("c15c_sprint",         T("R17_captain_sprint", 1), 1.2, 0.5, "ramp"),
 ("c10b_second_sun",     T("R12_second_sun", 1),    2.2, 0.5, "ramp"),
]
strobe = [  # light, eye, claw, fire, monolith, scream ... accelerating
 ("light", V("R12_second_sun"), 1.5), ("eye", V("R19_giant_eye"), 0.5), ("claw", T("R18_ship_grab", 1), 2.2),
 ("fire", T("R14_engines_fire", 1), 1.8), ("monolith", T("R10_lightwave", 3), 2.0), ("scream", V("R20_crewmate_scream"), 0.5),
 ("eye", V("R19_giant_eye"), 1.6), ("mountain", T("R15_mountain_shape", 3), 2.6), ("claws", V("R05_claws"), 2.2),
 ("scream", V("R20_crewmate_scream"), 2.0), ("fire", V("R14_engines_fire"), 2.5), ("eye", V("R19_giant_eye"), 3.0),
 ("light", V("R12_second_sun"), 3.2), ("monolith", T("R10_lightwave", 2), 2.5), ("mountain", V("R15_mountain_shape"), 3.5),
 ("scream", V("R20_crewmate_scream"), 3.5), ("claw", V("R18_ship_grab"), 1.0), ("eye", V("R19_giant_eye"), 4.0),
 ("fire", T("R14_engines_fire", 1), 2.4), ("scream", V("R20_crewmate_scream"), 4.2), ("light", V("R12_second_sun"), 4.0),
 ("eye", V("R19_giant_eye"), 4.5),
]
FPS = 24
edl, t = [], 0.0
def add(cid, src, i, ln, sec):
    global t
    nf = round(ln * FPS); ln = nf / FPS
    edl.append({"id": cid, "src": src, "in": i, "len": round(ln, 4), "frames": nf, "start": round(t, 4), "section": sec})
    t += ln
for c in cuts: add(*c)
lens = [0.46, 0.42, 0.42, 0.38, 0.38, 0.33, 0.33, 0.29, 0.29, 0.25, 0.25, 0.25, 0.21, 0.21, 0.21, 0.21, 0.17, 0.17, 0.17, 0.17]
for k, ((name, src, i), ln) in enumerate(zip(strobe, lens)):
    add(f"c16_{k:02d}_{name}", src, i, ln, "strobe")
strobe_end = t
add("c17_black", None, 0.0, 2.625, "black")
add("c18_title", "final/title/title_card.mp4", 0.0, 3.0, "title")
json.dump({"fps": FPS, "size": [832, 448], "duration": round(t, 4), "strobe_end": round(strobe_end, 4), "cuts": edl},
          open(P / "final/edl_final.json", "w"), indent=1)
print(f"{len(edl)} cuts, {t:.2f}s, strobe ends {strobe_end:.2f}")
