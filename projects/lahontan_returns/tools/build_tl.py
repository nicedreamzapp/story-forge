#!/usr/bin/env python3
"""Lay the picked takes on the film clock (untouched, no stretch) and write:
  audio/dlg.wav           dialogue track (48 kHz mono)
  lips/<BLOCK>_a.wav      the audio each lip-sync block is rendered against
  timeline.json           lines (start/end/words), blocks, shots, gfx events
Usage: build_tl.py [--blocks-only]   (blocks are written as soon as their lines are picked)"""
import json, sys
from pathlib import Path
import numpy as np, soundfile as sf, librosa

P = Path(__file__).resolve().parent.parent
V = P / "voice"
LINES = json.load(open(V / "lines.json"))
PICKS = json.load(open(V / "picks.json")) if (V / "picks.json").exists() else {}
SC = json.load(open(V / "scores.json")) if (V / "scores.json").exists() else {}
SR = 48000
COLD = 2.7
# (line, gap before it). Pauses are real silence between untouched takes.
ORDER = [("A01", COLD), ("A02", .35), ("A03", .55), ("A04", .45), ("A05", .3), ("R01", .5), ("R02", .95), ("R03", .3),
         ("H01", .5), ("H02", .4), ("X01", .5), ("X02", .4), ("A06", .5), ("A07", .4), ("A08", .3), ("A09", 1.9), ("A10", .4)]
TAIL = 2.4
# lip-sync blocks: on-camera talking runs (speaker clip, lines)
BLOCKS = {"AN1": ("anchor", ["A01", "A02", "A03"]), "REP": ("reporter", ["R01"]), "SCI": ("sci", ["H01", "H02"]),
          "RES": ("res", ["X01", "X02"]), "AN2": ("anchor", ["A06", "A07"]), "AN3": ("anchor", ["A10"])}


def load(lid):
    y, r = sf.read(V / "trimmed" / PICKS[lid]); y = y.mean(1) if y.ndim > 1 else y
    return librosa.resample(y.astype(np.float32), orig_sr=r, target_sr=SR)


def clock():
    t = 0.0; out = {}
    for lid, gap in ORDER:
        if lid not in PICKS: return out, None
        t += gap; d = SC[PICKS[lid]]["dur"]
        out[lid] = {"s": round(t, 3), "e": round(t + d, 3), "spk": LINES[lid][0], "text": LINES[lid][1],
                    "words": [{"w": w["w"], "s": round(t + w["s"], 3), "e": round(t + w["e"], 3)} for w in SC[PICKS[lid]]["words"]]}
        t += d
    return out, round(t + TAIL, 3)


def word_t(L, lid, word, which="s"):
    for w in L[lid]["words"]:
        if w["w"].lower().strip(".,?!'") == word.lower(): return w[which]
    raise KeyError((lid, word))


def main():
    L, END = clock()
    (P / "lips").mkdir(exist_ok=True)
    # blocks: write audio as soon as all its lines exist on the clock
    blocks = {}
    for b, (clip, ids) in BLOCKS.items():
        if not all(i in L for i in ids): continue
        s0 = L[ids[0]]["s"] - 0.25; s1 = L[ids[-1]]["e"] + 0.3
        a = np.zeros(int((s1 - s0) * SR), np.float32)
        for i in ids:
            y = load(i); k = int((L[i]["s"] - s0) * SR); a[k:k + len(y)] += y[:len(a) - k]
        f = P / "lips" / f"{b}_a.wav"
        if not f.exists(): sf.write(f, a, SR)
        blocks[b] = {"clip": clip, "s": round(s0, 3), "e": round(s1, 3)}
    if END is None or "--blocks-only" in sys.argv:
        print("blocks ready:", list(blocks)); return
    dlg = np.zeros(int(END * SR), np.float32)
    for i in L:
        y = load(i); k = int(L[i]["s"] * SR); dlg[k:k + len(y)] += y
    sf.write(P / "audio/dlg.wav", dlg, SR)
    B = lambda b: ("lips", b)
    # shots: (start, end, source, framing). framing = crop zoom/centre for coverage variety on the same take.
    sh = []
    def add(a, b, src, **kw): sh.append({"s": round(a, 3), "e": round(b, 3), "src": src, **kw})
    add(0, COLD, "clip:aerial", mode="push")
    a02b = word_t(L, "A02", "prehistoric")
    add(COLD, a02b, "lips:AN1", z=1.0)
    add(a02b, L["A02"]["e"] + .2, "still:aerial", mode="pullback")          # "...the prehistoric inland sea..." over the valley
    add(L["A02"]["e"] + .2, L["A04"]["s"] - .15, "lips:AN1", z=1.55, cy=0.30)  # "Tomorrow." punch-in
    add(L["A04"]["s"] - .15, L["R01"]["s"] - .25, "map")
    look = word_t(L, "R01", "look")
    add(L["R01"]["s"] - .25, L["R01"]["e"] + .15, "lips:REP", z=1.0)
    add(L["R01"]["e"] + .15, L["R02"]["s"] - .1, "clip:hwy", mode="splash")    # (splashes)
    add(L["R02"]["s"] - .1, L["R03"]["s"] - .1, "clip:reservoir")
    add(L["R03"]["s"] - .1, L["H01"]["s"] - .3, "clip:sage")
    hon = word_t(L, "H02", "honestly")
    add(L["H01"]["s"] - .3, L["H02"]["s"] - .05, "lips:SCI", z=1.0)
    add(L["H02"]["s"] - .05, hon - .1, "still:rings", mode="pushin")
    add(hon - .1, L["X01"]["s"] - .3, "lips:SCI", z=1.3, cy=0.30)
    alr = word_t(L, "X02", "already")
    add(L["X01"]["s"] - .3, L["X02"]["s"] - .15, "lips:RES", z=1.0)   # X02 mouth barely moves under the beard (film_qc 25%): cut away
    add(L["X02"]["s"] - .15, L["A06"]["s"] - .3, "still:pontoon", mode="pullback")
    add(L["A06"]["s"] - .3, L["A07"]["s"] - .1, "lips:AN2", z=1.0)
    add(L["A07"]["s"] - .1, L["A08"]["s"] - .1, "lips:AN2", z=1.35, cy=0.32)
    add(L["A08"]["s"] - .1, L["A08"]["e"] + .25, "clip:hwy", off=0.8)
    add(L["A08"]["e"] + .25, L["A09"]["s"] - .1, "evac")
    add(L["A09"]["s"] - .1, L["A10"]["s"] - .2, "clip:fish")
    add(L["A10"]["s"] - .2, END, "lips:AN3", z=1.0)
    for x, y in zip(sh, sh[1:]): y["s"] = x["e"]
    gfx = {"lower": [
        {"t": COLD + .4, "e": a02b, "top": "LAKE LAHONTAN RETURNS", "sub": "SILVER SPRINGS UNDER EMERGENCY ALERT", "red": True},
        {"t": L["R01"]["s"] - .1, "e": L["R01"]["e"] + .15, "top": "HIGHWAY 50 UNDER WATER", "sub": "LIVE: SILVER SPRINGS, NEVADA", "red": True},
        {"t": L["H01"]["s"] - .1, "e": L["H02"]["s"] - .05, "top": "DR. HALVERSON", "sub": "DESERT HYDROLOGY INSTITUTE", "red": False},
        {"t": L["X01"]["s"] - .1, "e": L["X02"]["s"] - .15, "top": "SILVER SPRINGS RESIDENT", "sub": "30 YEARS, NO BEACHFRONT", "red": False},
        {"t": L["A06"]["s"] - .1, "e": L["A08"]["s"] - .1, "top": "GET READY NOW, OFFICIALS SAY", "sub": "MOVE VALUABLES TO SECOND FLOOR OR ROOF", "red": True},
        {"t": L["A10"]["s"] - .1, "e": L["A10"]["e"], "top": "DAN ROURKE", "sub": "KSSN 8 NEWS", "red": False}],
        "live": [[L["R01"]["s"] - .25, L["H01"]["s"] - .3, "HIGHWAY 50"]],
        "end": round(L["A10"]["e"] + .25, 3), "cold": COLD}
    json.dump({"end": END, "lines": L, "blocks": blocks, "shots": sh, "gfx": gfx}, open(P / "timeline.json", "w"), indent=1)
    print("END", END, "shots", len(sh))


if __name__ == "__main__":
    main()
