#!/usr/bin/env python3
"""coverage_lint.py — does the P2 plan shoot COVERAGE, or one clip per line?

Promo rule (2026-10-22, the Sitka diagnosis): "shoot coverage and cut to the best". One
clip per narration beat leaves the editor nothing to choose from, so every narration line
in coverage.json must plan >= 3 setups from >= 2 distinct sources, and carry a sentiment
(what the viewer should feel), before a single take is acquired.

Usage:  python pipeline-tools/coverage_lint.py projects/<film>   (or a coverage.json path)
Exit 0 = plan is coverage; 1 = a line falls short (table printed); 2 = file missing/broken.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# every source SCHEMAS.md names (blender-render is the primary one for a physical product)
SOURCES = {"blender-render", "cad", "real", "grok-image", "gemini-image", "chatgpt-edit", "grok-video",
           "chatgpt-image", "flux-img2img", "ltx25", "wan", "still-kb", "manim"}
MIN_SETUPS, MIN_SOURCES = 3, 2


def lint(cov: dict) -> tuple[bool, list]:
    rows, ok = [], True
    problems_global = []
    tr = cov.get("target_runtime")
    if not isinstance(tr, (int, float)) or tr <= 0:
        problems_global.append("target_runtime missing or not > 0")
    lines = cov.get("lines") or []
    if not lines:
        problems_global.append("no lines")
    for ln in lines:
        su = ln.get("setups") or []
        srcs = {s.get("source") for s in su}
        bad_src = sorted(str(s) for s in srcs if s not in SOURCES)
        why = []
        if len(su) < MIN_SETUPS:
            why.append(f"{len(su)} setups (< {MIN_SETUPS})")
        if len(srcs - {None}) < MIN_SOURCES:
            why.append(f"{len(srcs - {None})} source(s) (< {MIN_SOURCES})")
        if not str(ln.get("sentiment") or "").strip():
            why.append("no sentiment")
        if not str(ln.get("text") or "").strip():
            why.append("no text")
        if bad_src:
            why.append("unknown source " + ",".join(bad_src))
        if not all(str(s.get("setup") or "").strip() for s in su):
            why.append("a setup has no description")
        ok &= not why
        rows.append((ln.get("line"), len(su), ",".join(sorted(str(s) for s in srcs)),
                     "yes" if str(ln.get("sentiment") or "").strip() else "NO",
                     "OK" if not why else "SHORT: " + "; ".join(why)))
    out = [f"coverage plan: {len(lines)} lines, target_runtime {tr}s"]
    out += [f"  PROBLEM: {p}" for p in problems_global]
    out.append(f"  {'line':>4}  {'setups':>6}  {'sources':<34} {'sent':<4}  status")
    for r in rows:
        out.append(f"  {str(r[0]):>4}  {r[1]:>6}  {r[2][:34]:<34} {r[3]:<4}  {r[4]}")
    ok &= not problems_global
    out.append("COVERAGE PLAN OK" if ok else
               f"COVERAGE PLAN SHORT — every line needs >= {MIN_SETUPS} setups from >= {MIN_SOURCES} "
               "sources and a sentiment (frozen rule 29)")
    return ok, out


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    p = Path(sys.argv[1])
    p = p / "coverage.json" if p.is_dir() else p
    try:
        cov = json.loads(p.read_text())
    except Exception as e:                                   # noqa: BLE001
        print(f"[coverage_lint] cannot read {p}: {e}", file=sys.stderr)
        return 2
    ok, out = lint(cov)
    print("\n".join(out))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
