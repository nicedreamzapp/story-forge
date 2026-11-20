"""timeline_p01.json: PART 1 (PART_01.md), 5:00. Reuses teaser/trailer shots (best sources where they exist)."""
import json
from pathlib import Path
P = Path(__file__).resolve().parents[2]
TBEST = {"t13": "00_t13", "t18": "01_t18", "t14": "02_t14"}   # trailer best: only these 3 HQ takes were kept
def tr(i):
    u = TBEST.get(i); f = f"final/segs/up_trailer/{u}.mp4" if u else None
    return f"clip:{f}" if f and (P / f).exists() else f"clip:{i}"
st = lambda n, z=1.12: {"push": [.5, .5, 1.0, .5, .5, z]}
S = [
 ("p01", 6.0, "black", {}), ("s01", 4.0, "clip:final/segs/up/00_s01.mp4", {}), ("p03", 5.0, "clip:p03", {}),
 ("p04", 5.0, "clip:p04", {}), ("p05", 5.0, "clip:p05", {}), ("p06", 4.5, "clip:p06", {}), ("p07", 4.5, "clip:p07", {}),
 ("p08", 3.0, "clip:p08", {}), ("pa1", 5.0, "clip:pa1", {}), ("t01", 4.0, tr("t01"), {}), ("pa2", 4.0, "clip:pa2", {}), ("p10", 4.0, "clip:p10", {}), ("p11", 4.5, "clip:p11", {}),
 ("p12", 5.0, "clip:p12", {}), ("p13", 2.5, "lips:clips/p13.mp4", {}), ("p14", 3.5, "still:p14", st("p14")),
 ("p15", 4.0, "clip:p15", {}), ("p16", 4.0, "clip:p16", {}), ("pa3", 5.0, "clip:pa3", {}), ("s02", 3.0, "push:s02", {}), ("p18", 4.5, "clip:p18", {}),
 ("t03", 1.9, "clip:t03", {"src_range": [0, 46]}), ("t03e", 1.1, "still:t03_end", {"push": [.5, .5, 1.0, .5, .45, 1.04]}), ("pa4", 4.5, "clip:pa4", {}),
 ("p20", 5.0, "clip:p20", {}), ("p21", 3.0, "clip:p21", {}), ("pa5", 4.0, "clip:pa5", {}), ("pa6", 5.0, "clip:pa6", {}), ("p22", 4.0, "clip:p22", {}),
 ("t07", 3.0, "still:t07", {"push": [.5, .55, 1.0, .5, .6, 1.18]}), ("p24", 3.0, "lips:clips/p24.mp4", {}),
 ("p25", 3.5, "still:p25", st("p25", 1.2)), ("p26", 3.0, "clip:p26", {}), ("p27", 4.5, "clip:p27", {}), ("pa7", 4.5, "clip:pa7", {}),
 ("p28", 4.5, "clip:p28", {}), ("p29", 3.0, "still:p29", st("p29", 1.15)), ("p30", 3.0, "clip:p30", {}),
 ("p31", 4.5, "clip:p31", {}), ("pa8", 4.5, "clip:pa8", {}), ("pa9", 4.5, "clip:pa9", {}), ("pa10", 4.0, "clip:pa10", {}), ("pa11", 4.0, "still:pa11", st("pa11", 1.12)), ("pa12", 4.0, "clip:pa12", {}), ("pa13", 4.0, "clip:pa13", {}), ("p32", 3.5, "still:p32", st("p32", 1.1)), ("p33", 4.5, "clip:p33", {}),
 ("p34", 5.0, "clip:p34", {}), ("p35", 2.5, "lips:clips/p35.mp4", {}), ("p36", 4.0, "clip:p36", {}),
 ("p37", 4.5, "clip:p37", {}), ("p38", 3.5, "still:p38", st("p38", 1.1)), ("pa14", 5.0, "clip:pa14", {}), ("pa15", 4.0, "still:pa15", st("pa15", 1.15)), ("p39", 4.0, "clip:p39", {}),
 ("p40", 5.0, "clip:p40", {}), ("t04", 4.0, tr("t04"), {}), ("p42", 4.0, "clip:p42", {}), ("p43", 5.0, "clip:p43", {}),
 ("p44", 4.0, "clip:p44", {}), ("p45", 5.0, "clip:p45", {}), ("p46", 3.5, "clip:p46", {}), ("pa16", 5.0, "clip:pa16", {}), ("pa17", 4.0, "clip:pa17", {}), ("pa18", 5.0, "clip:pa18", {}), ("pa19", 4.0, "clip:pa19", {}), ("pa20", 4.0, "clip:pa20", {}), ("pa21", 4.0, "clip:pa21", {}), ("pa22", 3.0, "clip:pa22", {}), ("p47", 5.0, "clip:p47", {}),
 ("p48", 4.5, "clip:p48", {}), ("p49", 3.0, "still:p49", {"push": [.5, .5, 1.0, .5, .5, 1.1], "flicker": True}),
 ("p50", 1.5, "black", {}), ("card", 6.0, "card", {"text": ["THE THINGS WE REMEMBER", "PART ONE"], "size": 64}),
]
OV = Path(__file__).with_name("overrides.json"); ov = json.load(open(OV)) if OV.exists() else {}
shots, t = [], 0.0
for i, l, src, ex in S:
    ex = {**ex, **ov.get(i, {})}; shots.append({"id": i, "s": round(t, 3), "e": round(t + l, 3), "src": src, **ex}); t += l
at = {s["id"]: s["s"] for s in shots}; end = round(t, 3)
L = lambda sid, off, spk, **k: {"t": round(at[sid] + off, 3), "spk": spk, **k}
lines = {
 "C06": L("p07", .8, "claire"), "R04": L("p11", 1.2, "ruth"), "C07": L("p13", .35, "claire", onscreen="p13"),
 "R05": L("p14", .3, "ruth"), "C08": L("p14", 1.8, "claire"), "L06": L("p22", .4, "lily"), "C02": L("t07", .5, "claire"),
 "L07": L("p24", .35, "lily", onscreen="p24"), "C09": L("p26", .3, "claire"), "T03": L("p30", .8, "tom"),
 "T04": L("p35", .35, "tom", onscreen="p35"), "R06": L("p37", .6, "ruth"), "C10": L("p38", .5, "claire"),
 "C11": L("t04", .6, "claire"), "R02": L("p43", .3, "ruth"), "C12": L("p44", .4, "claire"), "R07": L("p46", .3, "ruth"), "R08": L("pa12", .2, "ruth"), "L08": L("pa12", 2.2, "lily"),
}
score = [
 {"k": "mbox", "t": at["p01"] + .5, "phrases": "P1P2", "beat": .45, "g": .45, "until": at["p04"]},
 {"k": "mbox", "t": at["p06"] + .2, "phrases": "P1P2", "beat": .45, "g": .4, "until": at["p10"] - .5},
 {"k": "mbox", "t": at["p10"], "phrases": "P1", "beat": .5, "g": .3, "until": at["p13"]},
 {"k": "mbox", "t": at["s02"], "phrases": "P1P2", "beat": .48, "g": .35, "until": at["p20"]},
 {"k": "drone", "t0": at["p25"], "t1": at["p28"], "g": .05},
 {"k": "mbox", "t": at["p31"] + .2, "phrases": "P1", "beat": .5, "g": .3, "until": at["pa8"]},
 {"k": "mbox", "t": at["pa9"] + .3, "phrases": "P1P2", "beat": .55, "g": .3, "until": at["pa12"]},
 {"k": "drone", "t0": at["p37"], "t1": at["p40"], "g": .06},
 {"k": "drone", "t0": at["p40"], "t1": at["p47"], "g": .06},
 {"k": "drone", "t0": at["p47"], "t1": at["p50"], "g": .13},
 {"k": "note", "t": at["p49"] + 1.2, "m": 75, "g": .6},
 {"k": "title", "t": at["card"] + .3},
]
sfx = [
 {"f": "rain", "t": at["p03"], "dur": at["pa3"] - at["p03"], "g": .25, "fade": .8},
 {"f": "wipers", "t": at["p05"], "dur": at["t01"] - at["p05"], "g": .3, "fade": .3},
 {"f": "car", "t": at["t01"] + .2, "g": .55, "fade": .3}, {"f": "screen", "t": at["p10"] + .3, "g": .4, "fade": .02},
 {"f": "steps", "t": at["t03"] + .1, "g": .55, "fade": .05},
 {"f": "room", "t": at["p20"], "dur": at["p40"] - at["p20"], "g": .22, "fade": .5},
 {"f": "rain", "t": at["pa8"], "dur": 4.5, "g": .35, "fade": .3},
 {"f": "creak", "t": at["pa21"], "dur": 4, "g": .3, "fade": .3},
 {"f": "creak", "t": at["p22"], "dur": 3, "g": .25, "fade": .3},
 {"f": "rain", "t": at["p40"], "dur": end - at["p40"] - 7, "g": .22, "fade": .8},
 {"f": "drip", "t": at["p48"] + 1.0, "dur": at["p50"] - at["p48"] - 1.0, "g": .55, "fade": .05},
]
tl = {"end": end, "fps": 24, "w": 1920, "h": 1080, "cold_t": at["p47"], "cold_ramp": 3, "shots": shots, "lines": lines,
      "score": score, "sfx": sfx, "silence": [[at["p50"], at["card"]]],
      "scenes": [{"name": "arrival", "start": 0, "end": at["p20"]}, {"name": "unpacking", "start": at["p20"], "end": at["p40"]},
                 {"name": "window", "start": at["p40"], "end": at["p47"]}, {"name": "hook", "start": at["p47"], "end": end}]}
json.dump(tl, open(P / "timeline_p01.json", "w"), indent=1)
json.dump({"texts": [{"id": "card", "text": "THE THINGS WE REMEMBER PART ONE", "rec_in": at["card"], "rec_out": end, "read_in": .4, "read_out": .4}]},
          open(P / "texts_p01.json", "w"), indent=1)
print("end", end, len(shots), "shots")
