"""timeline_short.json: the 3-minute short (SHORT_3MIN.md). Reused shots take their best kept source when one exists."""
import json, os
from pathlib import Path
P = Path(__file__).resolve().parents[2]
TBEST = {"t13": "00_t13", "t18": "01_t18", "t14": "02_t14"}   # trailer best: only these 3 HQ takes were kept
def tr(i):   # trailer shot: upscaled best take if it exists, else the fast take
    u = TBEST.get(i); f = f"final/segs/up_trailer/{u}.mp4" if u else None
    return f"clip:{f}" if f and (P / f).exists() else f"clip:{i}"
S = [
 ("t01", 5.0, tr("t01"), {}), ("s01", 4.5, "clip:final/segs/up/00_s01.mp4", {}),
 ("t03", 1.9, "clip:t03", {"src_range": [0, 46]}), ("t03e", 1.5, "still:t03_end", {"push": [.5, .5, 1.0, .5, .45, 1.04]}),
 ("t04", 5.0, tr("t04"), {}), ("s02", 3.5, "push:s02", {}),
 ("sh06", 4.0, "clip:sh06", {}), ("sh07", 3.5, "still:sh07", {"push": [.5, .5, 1.0, .5, .5, 1.12]}),
 ("s03", 4.8, "push:s03", {}), ("s04", 2.7, "clip:final/segs/up/01_s04.mp4", {}),
 ("sh10", 3.5, "clip:sh10", {}), ("sh11", 3.5, "still:sh11", {"push": [.5, .5, 1.0, .5, .5, 1.08], "wipe_close": 1.6}),
 ("sh12", 4.0, "clip:sh12", {}),
 ("s05", 4.0, "clip:s05_code", {}),
 ("sh13", 5.0, "clip:sh13", {}), ("sh13b", 3.0, "clip:sh13b", {}), ("sh14", 3.5, "clip:sh14", {}), ("sh15", 3.5, "clip:sh15", {}), ("sh16", 3.5, "clip:sh16", {}),
 ("s07", 2.0, "lips:clips/s07.mp4", {}), ("sh18", 4.0, "clip:sh18", {}), ("s06", 3.5, "clip:s06_code", {}),
 ("t20", 0.6, "still:t20", {"push": [.5, .5, 1.05, .5, .5, 1.08], "soft": 7, "flash": True, "flicker": True}),
 ("sh21", 4.5, "clip:sh21", {}),
 ("sh22", 4.0, "clip:sh22", {}),
 ("s08", 4.5, "clip:final/segs/up/03_s08.mp4", {}),
 ("t10", 1.6, "clip:t10", {"src_range": [0, 40]}), ("t10e", 2.0, "still:t10e", {"push": [.5, .55, 1.0, .5, .55, 1.06]}),
 ("t11", 4.2, "lips:clips/t11.mp4", {}),
 ("t17", 2.3, "clip:t17", {"blur_man": [[1110, 520], [1500, 560], 170, 420], "dim": 0.8}),
 ("s09", 3.2, "photos:s09", {}),
 ("s11", 5.3, "clip:final/segs/up/04_s11.mp4", {"hide_man": True}),
 ("s10", 1.5, "black", {}),
 ("later", 3.9, "card", {"text": ["MONTHS LATER"], "size": 54}),
 ("sh29", 5.0, "clip:sh29", {}), ("sh30", 5.0, "clip:sh30", {}), ("sh31", 4.0, "clip:sh31", {}),
 ("sh32", 3.5, "lips:clips/sh32.mp4", {}),
 ("sh33", 5.4, "still:sh33", {"push": [.5, .5, 1.0, .5, .5, 1.15]}),
 ("sh34", 5.5, "clip:sh34", {}),
 ("sh35", 3.0, "still:sh33", {"push": [.5, .5, 1.6, .5, .5, 1.9]}),
 ("sh36", 3.5, "lips:clips/sh36.mp4", {}),
 ("sh37", 4.0, "clip:sh37", {}),
 ("sh38", 6.0, "clip:sh38", {"blur_man": [[960, 400], [960, 400], 200, 330]}),
 ("end_black", 4.0, "black", {}),
 ("thanks", 4.5, "card", {"text": ["Thank you for remembering."], "size": 56}),
 ("s12", 4.5, "title", {"no_soon": True}), ("s13", 5.6, "credits", {}),
]
OV = Path(__file__).with_name("overrides.json")
ov = json.load(open(OV)) if OV.exists() else {}
shots, t = [], 0.0
for i, l, src, ex in S:
    ex = {**ex, **ov.get(i, {})}; shots.append({"id": i, "s": round(t, 3), "e": round(t + l, 3), "src": src, **ex}); t += l
at = {s["id"]: s["s"] for s in shots}; end = round(t, 3)
L = lambda sid, off, spk, **k: {"t": round(at[sid] + off, 3), "spk": spk, **k}
lines = {
 "R02": L("t04", .5, "ruth"), "C03": L("sh06", .6, "claire"), "R03": L("sh07", .8, "ruth"),
 "C01": L("s03", .4, "claire"), "R01": L("s04", .4, "ruth"),
 "T02": L("sh14", .5, "tom"), "C04": L("sh15", 1.2, "claire"),
 "L01": L("s07", .35, "lily", onscreen="s07"), "D01": L("s08", 1.4, "daniel"),
 "L02": L("t11", .35, "lily", onscreen="t11"), "M01": L("s11", .9, "rememberer"),
 "C05": L("sh31", .4, "claire"), "L04": L("sh32", .35, "lily", onscreen="sh32"),
 "L05": L("sh36", .35, "lily", onscreen="sh36"), "M02": L("thanks", .3, "rememberer"),
 "D02": L("s13", 1.8, "daniel"),
}
glass = round(at["s05"] + 1.583, 3)
score = [
 {"k": "mbox", "t": .3, "phrases": "P1P2P1P2P1P2", "beat": .45, "until": at["s04"] - 1.5},
 {"k": "wrong", "t": at["s04"] + .2},
 {"k": "drone", "t0": at["s05"], "t1": at["s08"], "g": .12},
 {"k": "drone", "t0": at["s08"], "t1": at["s10"], "g": .16},
 {"k": "heart", "t0": at["s08"] + .3, "t1": at["s11"], "bpm0": 55, "bpm1": 140},
 {"k": "piano", "t0": at["t17"], "t1": at["s11"], "g": .22, "beat": .55, "accel": .9},
 {"k": "mbox", "t": at["sh29"] + .2, "phrases": "P1P2", "beat": .45, "g": .4, "until": at["sh33"] + 2},
 {"k": "wrong", "t": at["sh34"] + .6},
 {"k": "drone", "t0": at["sh38"], "t1": at["end_black"], "g": .12},
 {"k": "right", "t": at["end_black"] + .2, "g": .5, "beat": .5},
 {"k": "title", "t": at["s12"] + .2},
]
sfx = [
 {"f": "rain", "t": 0.0, "dur": glass, "g": .25, "fade": .005}, {"f": "car", "t": .2, "g": .55, "fade": .3},
 {"f": "birds", "t": at["s01"], "dur": 8.0, "g": .16, "fade": .8}, {"f": "steps", "t": at["t03"] + .1, "g": .55, "fade": .05},
 {"f": "room", "t": at["sh06"], "dur": glass - at["sh06"], "g": .3, "fade": .005},
 {"f": "drawer", "t": at["sh11"] + 2.0, "g": .6, "fade": .01},
 {"f": "glass", "t": glass, "g": .9, "fade": .005},
 {"f": "room", "t": at["sh13"], "dur": at["sh15"] + 1.2 - at["sh13"], "g": .3, "fade": .4},
 {"f": "plate", "t": at["sh14"] + .9, "g": .5, "fade": .01},
 {"f": "laugh", "t": at["s07"], "dur": 7, "g": .4, "fade": .6, "proc": "rev|slow|lp"},
 {"f": "fork", "t": at["s06"] + 1.0, "dur": 1.6, "g": .6, "fade": .25, "proc": "hp"},
 {"f": "creak", "t": at["s08"] + .5, "dur": 3, "g": .35, "fade": .3}, {"f": "quilt", "t": at["t10"] + .9, "g": .6, "fade": .02},
 {"f": "creak", "t": at["t17"], "dur": 2.3, "g": .3, "fade": .2},
 {"f": "birds", "t": at["sh29"], "dur": at["sh34"] - at["sh29"], "g": .18, "fade": .8},
 {"f": "crayon", "t": at["sh30"] + .3, "dur": 3.0, "g": .35, "fade": .2},
 {"f": "giggle", "t": at["sh35"] + .3, "g": .35, "fade": .1, "proc": "lp"},
]
tl = {"end": end, "fps": 24, "w": 1920, "h": 1080, "cold_t": at["s05"], "cold_ramp": 6,
      "warm_again": [[at["later"], at["sh38"]]], "shots": shots, "lines": lines, "score": score, "sfx": sfx,
      "silence": [[at["s10"], at["later"]]],
      "scenes": [{"name": "arrival", "start": 0, "end": at["sh06"]}, {"name": "photo", "start": at["sh06"], "end": at["sh13"]},
                 {"name": "dinner", "start": at["sh13"], "end": at["s08"]}, {"name": "night", "start": at["s08"], "end": at["later"]},
                 {"name": "drawing", "start": at["later"], "end": end}]}
json.dump(tl, open(P / "timeline_short.json", "w"), indent=1)
txt = [{"id": "later", "text": "MONTHS LATER", "rec_in": at["later"], "rec_out": at["sh29"], "read_in": .4, "read_out": .4},
       {"id": "thanks", "text": "Thank you for remembering.", "rec_in": at["thanks"], "rec_out": at["s12"], "read_in": .4, "read_out": .4},
       {"id": "title", "text": "THE THINGS WE REMEMBER", "rec_in": at["s12"], "rec_out": at["s13"], "read_in": .5},
       {"id": "studio", "text": "NICE DREAMZ PICTURES A STORY FORGE PRODUCTION", "rec_in": at["s13"], "rec_out": end, "read_in": .15, "read_out": .3}]
json.dump({"texts": txt}, open(P / "texts_short.json", "w"), indent=1)
print("end", end, len(shots), "shots")
