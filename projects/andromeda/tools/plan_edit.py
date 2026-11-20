"""plan_edit.py — the sitka_v3 edit, written once: per line, the cut words and the take for each span
(in the order they play), plus ranked alternates. Writes cues.json and selects.json (no "draft").
Span lengths come from vo/words.json, so a select's out = in + exactly what the span needs (+1 frame)."""
import json, re
from pathlib import Path
film = Path(__file__).resolve().parent.parent
W = json.loads((film / "vo/words.json").read_text())
P = json.loads((film / "promo.json").read_text())
words, lines = W["words"], W["lines"]
norm = lambda w: re.sub(r"[^a-z0-9']", "", w.lower()).strip("'")


def wt(line, word, nth=1):
    hits = [w for w in words if w["line"] == line and norm(w["word"]) == norm(word)]
    return hits[nth - 1]["start"]


def cid(line, stem, src="cad"):
    return f"l{line:02d}_{src}_{re.sub(r'[^a-z0-9]+', '_', stem.lower()).strip('_')[:40]}"


# where each footage file was ingested (its first coverage line)
cov = json.loads((film / "coverage.json").read_text())
home = {}
for ln in cov["lines"]:
    for su in ln["setups"]:
        f = su.get("file")
        if f and f not in home:
            home[f] = (ln["line"], su["source"])


def C(stem):
    if stem.startswith("bl:"):
        return stem[3:] + "_1"                                   # blender-render provenance id_n
    f = f"footage/{stem}.mp4"
    l, s = home[f]
    return cid(l, stem, s)


# line: [(cut word or None, nth, take stem, src_in, why)], alternates: [(stem, in, out, why)]
PLAN = {
 1: ([(None, 1, "v1_s01_knee_macro", 0.0, "cold open on the knee joint flexing: 'fight your body' needs the machine up close"),
      ("fight", 1, "v1_s22_clutch_walk", 0.5, "the knee hinge and clutch working at walking pace under MOTORS. METAL."),
      ("Sitka", 1, "v1_s02_hero_reveal", 0.3, "the reveal lands on 'Sitka works with it'")],
     [("n01_hero_orbit", 0.0, 3.0, "alternate reveal, studio orbit"), ("bl:l01_bl_hero_orbit", 0.0, 4.0, "GLB orbit alternate")]),
 2: ([(None, 1, "n01_hero_orbit", 1.5, "the standing wearer under the SITKA title slam"),
      ("Named", 1, "n02_bluff_walk", 0.5, "he walks the Trinidad bluff while the name is explained: sense of place"),
      ("Strong", 1, "n07_run_low", 0.4, "low running shot carries STRONG and LIGHT"),
      ("bends", 1, "n04_sit_med", 1.0, "the knees bend as he sits, the springs take it: 'bends without breaking'")],
     [("v1_s03_bluff", 0.0, 4.3, "v1 bluff orbit alternate"), ("bl:l02_bl_bluff_push", 0.0, 3.0, "GLB bluff push alternate")]),
 3: ([(None, 1, "n03_ghost_walk", 0.0, "ghosted body walking: the bones carry the weight, the frame adds the muscle"),
      ("springs", 1, "v1_s20_walk_bands", 1.0, "the legs walking, springs and clutches at work under SPRINGS / CLUTCHES"),
      ("cables", 1, "v1_s09_tendon_glow", 0.0, "the tendons glow on 'cables that work like tendons'")],
     [("v1_s06_ghost_walk", 0.0, 2.9, "v1 ghost walk"), ("bl:l03_bl_walk_truck", 0.0, 3.0, "GLB truck alternate")]),
 4: ([(None, 1, "v1_s10_sit_wide", 0.0, "sits down outdoors, the poles swing down and take the weight; card on the right"),
      ("A", 2, "v1_s12_knee_sit_close", 0.0, "knee close: the carbon spring loads as he sits and gives it back as he stands")],
     [("n04_sit_med", 0.0, 6.0, "medium sit from the other side")]),
 5: ([(None, 1, "v1_s13_lean_back", 0.0, "leans back and the two straps take him"),
      ("camp", 1, "n05_lean_front", 3.0, "front three-quarter on 'camp chair you wear'")],
     [("bl:l05_bl_chair_orbit", 0.0, 3.0, "GLB orbit to the straps")]),
 6: ([(None, 1, "n06_lift_front", 0.3, "from behind he bends to the box"),
      ("tendon", 1, "v1_s16_tendon_back", 0.6, "the back tendon glows as it stores energy"),
      ("A", 2, "v1_s15_lift_side", 1.6, "the lift itself, side on, with the 15 / 12 / no-motor card on the right")],
     [("v1_s17_lift_34", 0.0, 2.3, "three-quarter lift")]),
 7: ([(None, 1, "n07_walk_track", 0.2, "smooth walk on the bluff (clinical gait, no stop-start)"),
      ("elastic", 1, "n07_walk_bands", 0.0, "studio walk, the bands glow teal, the band diagram on the right")],
     [("n07_run_track", 0.0, 5.0, "smooth run"), ("n07_run_bands_34", 0.0, 5.0, "run with bands glowing")]),
 8: ([(None, 1, "bl:l01_bl_hero_orbit", 1.0, "'Want more?' over the GLB hero orbit"),
      ("Smart", 1, "n08_clutch_walk", 0.0, "the knee clutch flicks on in early stance"),
      ("And", 1, "v1_s23_motor_back", 0.0, "orbit in to the one motor on the back"),
      ("on", 3, "n08_stairs_side", 0.4, "a real stair climb on bluff steps under STAIRS and HILLS"),
      ("heavy", 1, "v1_s17_lift_34", 0.4, "the heavy lift")],
     [("n08_stairs_front", 0.0, 6.0, "stairs front"), ("n08_hills_walk", 0.0, 6.0, "toward the hills"),
      ("bl:l08_bl_stoop_crane", 0.0, 3.0, "GLB crane up the back")]),
 9: ([(None, 1, "n01_hero_orbit", 0.0, "the whole system on the wearer on 'fully modular'"),
      ("seat", 1, "n09_starter_orbit", 0.0, "only the seat + back starter kit on the wearer while the card gives about 14 lb and ~$2,000 a set"),
      ("Then", 1, "n02_bluff_front", 4.0, "the full system (hips, ankles, shoulders, power) walking toward camera while the card docks them on their words"),
      ("all", 1, "n01_hero_orbit", 3.5, "the complete kit, every module on the one hub")],
     [("v1_s18_walk_track", 0.0, 1.8, "full system walking")]),
 10: ([(None, 1, "n10_print_close", 0.8, "a seat cup printing layer by layer on a desktop printer"),
       ("printer", 1, "n10_knoll_top", 1.4, "every part flies off and lands in PRINTED / METAL / BOUGHT"),
       ("price", 1, "parts_list_scroll", 0.3, "the real parts list scrolls, every part with its price; GitHub pill on 'GitHub'")],
      [("n10_print_wide", 0.0, 5.0, "the whole printer"), ("n10_knoll_low", 0.0, 5.0, "low dolly over the layout")]),
 11: ([(None, 1, "bl:l01_bl_hero_orbit", 2.2, "the GLB orbit of the whole design on 'completely open'"),
       ("design", 1, "n10_knoll_low", 1.6, "every part laid out under THE DESIGN / THE MATH / EVERY PART"),
       ("Come", 1, "n11_finale_crane", 2.6, "the camera cranes up and away from him on the bluff on 'Come build one with us'; the end card slams after 'us'")],
      [("v1_s26_finale", 0.0, 2.7, "v1 bluff finale"), ("n11_walk_away", 0.0, 8.0, "walks away along the bluff")]),
}
ln_by = {l["line"]: l for l in lines}
last_end = words[-1]["end"]
slam = last_end + P["endcard"]["slam_after"]
starts = [l["start"] for l in lines]
cues, sel = [], []
for L, (spans, alts) in PLAN.items():
    lo = 0.0 if L == 1 else ln_by[L]["start"]
    hi = ln_by[L + 1]["start"] if L + 1 in ln_by else slam
    pts = [lo if w is None else wt(L, w, nth) for w, nth, *_ in spans]
    takes = []
    for k, (w, nth, stem, tin, why) in enumerate(spans):
        if w is not None:
            cues.append({"line": L, "word": w, "nth": nth, "kind": "cut"})
        s0 = pts[k]; s1 = pts[k + 1] if k + 1 < len(pts) else hi
        takes.append({"cid": C(stem), "rank": k + 1, "in": round(tin, 3), "out": round(tin + (s1 - s0) + 0.04, 3), "why": why})
    for j, (stem, tin, tout, why) in enumerate(alts):
        takes.append({"cid": C(stem), "rank": len(spans) + 1 + j, "in": tin, "out": tout, "why": "alternate: " + why})
    sel.append({"line": L, "takes": takes})
# title + overlays
cues.append({"line": 2, "word": "Sitka", "nth": 1, "kind": "title", "text": "SITKA"})
for L in range(1, 12):
    first = [w for w in words if w["line"] == L][0]["word"]
    f = film / f"overlays/l{L:02d}.mov"
    if f.exists():
        cues.append({"line": L, "word": re.sub(r"[^A-Za-z0-9']", "", first), "nth": 1, "kind": "overlay", "file": f"overlays/l{L:02d}.mov",
                     "x": 0.5, "y": 0.5, "w": 1.0, "opacity": 1.0, "whoosh": False})
(film / "cues.json").write_text(json.dumps({"cues": cues}, indent=1))
(film / "selects.json").write_text(json.dumps({"lines": sel}, indent=1))
print(len(cues), "cues;", sum(len(s["takes"]) for s in sel), "takes; slam", round(slam, 2))
