#!/usr/bin/env python3
"""promo_draft.py — a FIRST DRAFT of selects.json (stage 05) and cues.json (stage 06) when none exist.

Selects and cue words are editorial judgment and belong to the agent (it reads the sentiment per
line and watches the takes). This tool only makes sure a one-command run has something sane to
cut from, and it marks everything it writes `"draft": true` with a why that says so; bin/make-promo
prints a reminder while a draft is in use. It never overwrites a file that exists.

selects draft, per line: candidates of that line that did not FAIL design_check, ranked
  design pass > unchecked, then source trust (blender-render, cad, real, local renders, browser),
  then coverage.json order (the plan's own intent). Whole clip in/out.
cues draft, per line: a `title` cue on the first spoken brand word (promo.json brand), then `cut`
  cues on the longest words so shots run ~2.4 s (never under 1.6 s, never within 1.2 s of the
  line's end), plus promo.json "extra_cues" verbatim (overlays, callouts, xfades the plan asked for).

Usage:  python3 pipeline-tools/promo_draft.py projects/<film> [--selects] [--cues]   (default both)
Exit 0 = written or already there; 2 = inputs missing.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from promo_common import load_promo, norm_words  # noqa: E402

TRUST = ["blender-render", "cad", "real", "ltx25", "wan", "flux-img2img", "manim", "grok-image", "gemini-image",
         "chatgpt-edit", "grok-video", "still-kb", "chatgpt-image"]


def draft_selects(film: Path) -> int:
    out = film / "selects.json"
    if out.exists():
        print("[draft] selects.json exists; left alone")
        return 0
    try:
        man = json.loads((film / "manifest.json").read_text())
        cov = json.loads((film / "coverage.json").read_text())
    except Exception as e:  # noqa: BLE001
        print(f"[draft] need manifest.json + coverage.json ({e})", file=sys.stderr)
        return 2
    order = {}
    for ln in cov["lines"]:
        for k, su in enumerate(ln.get("setups", [])):
            if su.get("file"):
                order[su["file"]] = k
    lines = []
    for ln in cov["lines"]:
        cands = [c for c in man["candidates"] if c.get("line") == ln["line"]
                 and (c.get("checks") or {}).get("design") != "fail"]
        cands.sort(key=lambda c: (0 if (c.get("checks") or {}).get("design") in ("pass", "n/a") else 1,
                                  TRUST.index(c["source"]) if c.get("source") in TRUST else 99,
                                  order.get(c["file"], 99)))
        takes = []
        for r, c in enumerate(cands, 1):
            d = (c.get("checks") or {}).get("design") or "unchecked"
            takes.append({"cid": c["cid"], "rank": r, "in": 0.0,
                          **({"out": c["dur"]} if c.get("kind") == "video" and c.get("dur") else {}),
                          "why": f"DRAFT (promo_draft.py, not yet judged by the agent): {c.get('setup') or c['cid']}; "
                                 f"source {c.get('source')}; design {d}; sentiment to land: {ln.get('sentiment', '')}"})
        lines.append({"line": ln["line"], "takes": takes})
    out.write_text(json.dumps({"draft": True, "lines": lines}, indent=1))
    print(f"[draft] selects.json drafted: " + ", ".join(f"line {x['line']} {len(x['takes'])} takes" for x in lines))
    return 0


def draft_cues(film: Path, cfg: dict) -> int:
    out = film / "cues.json"
    if out.exists():
        print("[draft] cues.json exists; left alone")
        return 0
    try:
        W = json.loads((film / "vo" / "words.json").read_text())
    except Exception as e:  # noqa: BLE001
        print(f"[draft] need vo/words.json ({e})", file=sys.stderr)
        return 2
    brand = norm_words(cfg.get("brand") or "")
    cues, titled = [], False
    for ln in W["lines"]:
        ws = [w for w in W["words"] if w["line"] == ln["line"]]
        if not ws:
            continue
        if brand and not titled:
            for k, w in enumerate(ws):
                if norm_words(w["word"]) == brand[:1]:
                    nth = sum(1 for x in ws[:k + 1] if norm_words(x["word"]) == norm_words(w["word"]))
                    cues.append({"line": ln["line"], "word": w["word"], "nth": nth, "kind": "title",
                                 "text": cfg["brand"], "dur": 1.6})
                    titled = True
                    break
        end = ws[-1]["end"]
        last, picks = ln["start"], []
        while True:
            pool = [w for w in ws if w["start"] - last >= 1.6 and end - w["start"] >= 1.2]
            if not pool:
                break
            target = last + 2.4
            w = min(pool, key=lambda w: (abs(w["start"] - target) - 0.08 * len(norm_words(w["word"])[0] if norm_words(w["word"]) else "")))
            picks.append(w)
            last = w["start"]
        for w in picks:
            nth = sum(1 for x in ws if norm_words(x["word"]) == norm_words(w["word"]) and x["start"] <= w["start"])
            cues.append({"line": ln["line"], "word": w["word"], "nth": nth, "kind": "cut"})
    cues += cfg.get("extra_cues", [])
    out.write_text(json.dumps({"draft": True, "cues": cues}, indent=1))
    print(f"[draft] cues.json drafted: {len(cues)} cues ({sum(c['kind'] == 'cut' for c in cues)} cuts)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("film")
    ap.add_argument("--selects", action="store_true")
    ap.add_argument("--cues", action="store_true")
    a = ap.parse_args()
    film = Path(a.film).resolve()
    both = not (a.selects or a.cues)
    rc = 0
    if a.selects or both:
        rc = max(rc, draft_selects(film))
    if a.cues or both:
        rc = max(rc, draft_cues(film, load_promo(film)))
    return rc


if __name__ == "__main__":
    sys.exit(main())
