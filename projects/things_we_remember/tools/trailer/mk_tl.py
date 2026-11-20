"""timeline_trailer.json: the 90 s trailer cut (TRAILER_90.md). R shots use the APPROVED teaser best sources."""
import json
from pathlib import Path
P = Path(__file__).resolve().parents[2]
S = [  # id, len, src, extra
 ("t01", 4.0, "clip:t01", {}),
 ("s01", 4.0, "clip:final/segs/up/00_s01.mp4", {}),
 ("t03", 1.9, "clip:t03", {"src_range": [0, 46]}),
 ("t03e", 1.1, "still:t03_end", {"push": [.5, .5, 1.0, .5, .45, 1.04]}),
 ("t04", 4.0, "clip:t04", {}),
 ("s02", 3.0, "push:s02", {}),
 ("s03", 4.8, "push:s03", {}),
 ("s04", 2.7, "clip:final/segs/up/01_s04.mp4", {}),
 ("s05", 4.0, "clip:s05_code", {}),
 ("t07", 3.0, "still:t07", {"push": [.5, .55, 1.0, .5, .6, 1.18]}),
 ("s06", 3.5, "clip:s06_code", {}),
 ("s07", 2.0, "lips:clips/s07.mp4", {}),
 ("s08", 4.5, "clip:final/segs/up/03_s08.mp4", {}),
 ("t10", 1.6, "clip:t10", {"src_range": [0, 40]}),
 ("t10e", 1.4, "still:t10e", {"push": [.5, .55, 1.0, .5, .55, 1.06]}),
 ("t11", 4.2, "lips:clips/t11.mp4", {}),
 ("t12", 5.8, "cassette:t12", {"push": [.5, .5, 1.0, .5, .5, 1.15], "reels": [[450, 465, 31], [612, 470, 64]]}),
 ("t13", 3.5, "clip:t13", {}),
 ("t14", 4.5, "lips:clips/t14.mp4", {"vhs": True}),
 ("t15", 2.0, "whip:t15", {"push": [.12, .5, 1.6, .85, .5, 1.6], "whip_t": .2, "whip_len": .35}),
 ("s09", 3.2, "photos:s09", {}),
 ("t17", 2.3, "clip:t17", {"blur_man": [[1110, 520], [1500, 560], 170, 420], "dim": 0.8}),
 ("t18", 2.5, "clip:t18", {}),
 ("t20", 0.6, "still:t20", {"push": [.5, .5, 1.05, .5, .5, 1.08], "soft": 7, "flash": True, "flicker": True}),
 ("s10", 1.0, "black", {}),
 ("s11", 5.3, "clip:final/segs/up/04_s11.mp4", {"hide_man": True}),
 ("s12", 4.5, "title", {}),
 ("s13", 5.1, "credits", {}),
]
shots, t = [], 0.0
for i, l, src, ex in S:
    shots.append({"id": i, "s": round(t, 3), "e": round(t + l, 3), "src": src, **ex}); t += l
at = {s["id"]: s["s"] for s in shots}; end = round(t, 3)
lines = {
 "R02": {"t": at["t04"] + .5, "spk": "ruth"},
 "C01": {"t": at["s03"] + .4, "spk": "claire"},
 "R01": {"t": at["s03"] + 3.35, "spk": "ruth"},
 "C02": {"t": at["t07"] + .5, "spk": "claire"},
 "L01": {"t": at["s07"] + .35, "spk": "lily", "onscreen": "s07"},
 "D01": {"t": at["s08"] + 1.4, "spk": "daniel"},
 "L02": {"t": at["t11"] + .35, "spk": "lily", "onscreen": "t11"},
 "D02t": {"t": at["t12"] + 3.0, "spk": "daniel", "wav": "D02", "tape": True, "g": .8},
 "L03": {"t": at["t14"] + .35, "spk": "lily3", "onscreen": "t14", "tape": True},
 "T01": {"t": at["t18"] + .5, "spk": "tom"},
 "M01": {"t": at["s11"] + .9, "spk": "rememberer"},
 "D02": {"t": at["s13"] + 1.8, "spk": "daniel"},
}
for v in lines.values(): v["t"] = round(v["t"], 3)
glass = round(at["s05"] + 1.583, 3); cold = at["s05"]
score = [
 {"k": "mbox", "t": .3, "phrases": "P1P2P1P2", "beat": .45, "until": at["s04"] - 2.0},
 {"k": "wrong", "t": at["s04"] + .2},
 {"k": "drone", "t0": cold, "t1": at["t10"], "g": .16},
 {"k": "drone", "t0": at["t10"], "t1": at["t14"], "g": .11},
 {"k": "piano", "t0": at["t14"], "t1": at["s10"], "g": .22, "beat": .7, "accel": .93},
 {"k": "heart", "t0": at["t14"] + .3, "t1": at["s10"], "bpm0": 55, "bpm1": 150},
 {"k": "drone", "t0": at["s11"], "t1": at["s12"], "g": .10},
 {"k": "title", "t": at["s12"] + .2},
]
sfx = [
 {"f": "rain", "t": 0.0, "dur": glass, "g": .25, "fade": .005},
 {"f": "car", "t": .2, "g": .55, "fade": .3},
 {"f": "birds", "t": at["s01"], "dur": at["s02"] - at["s01"], "g": .16, "fade": .8},
 {"f": "steps", "t": at["t03"] + .1, "g": .55, "fade": .05},
 {"f": "room", "t": at["s03"], "dur": glass - at["s03"], "g": .3, "fade": .005},
 {"f": "glass", "t": glass, "g": .9, "fade": .005},
 {"f": "laugh", "t": at["s06"], "dur": 6, "g": .45, "fade": .6, "proc": "rev|slow|lp"},
 {"f": "fork", "t": at["s06"] + 1.0, "dur": 1.6, "g": .6, "fade": .25, "proc": "hp"},
 {"f": "creak", "t": at["s08"] + .5, "dur": 3, "g": .35, "fade": .3},
 {"f": "quilt", "t": at["t10"] + .9, "g": .6, "fade": .02},
 {"f": "party", "t": at["t10"] + 1.0, "dur": 4.5, "g": .22, "fade": .8, "proc": "rev|lp"},
 {"f": "click", "t": at["t12"] + .05, "g": .6, "fade": .01},
 {"f": "party", "t": at["t12"] + .4, "dur": 5.4, "g": .45, "fade": .3, "proc": "tape"},
 {"f": "garden", "t": at["t14"], "dur": at["s09"] - at["t14"], "g": .35, "fade": .05, "proc": "tape"},
 {"f": "creak", "t": at["t17"], "dur": 2.3, "g": .3, "fade": .2},
]
tl = {"end": end, "fps": 24, "w": 1920, "h": 1080, "cold_t": cold, "cold_ramp": 6, "shots": shots, "lines": lines,
      "score": score, "sfx": sfx, "silence": [[at["s10"], at["s11"]]]}
json.dump(tl, open(P / "timeline_trailer.json", "w"), indent=1)
json.dump({"texts": [
 {"id": "title", "text": "THE THINGS WE REMEMBER", "rec_in": at["s12"], "rec_out": at["s13"], "read_in": .5},
 {"id": "coming_soon", "text": "COMING SOON", "rec_in": at["s12"] + 1.0, "rec_out": at["s13"], "read_in": .4},
 {"id": "studio", "text": "NICE DREAMZ PICTURES A STORY FORGE PRODUCTION", "rec_in": at["s13"], "rec_out": end, "read_in": .15, "read_out": .3}]},
 open(P / "texts_trailer.json", "w"), indent=1)
print("end", end, {k: v["t"] for k, v in lines.items()})
