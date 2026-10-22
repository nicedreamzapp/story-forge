#!/usr/bin/env python3
"""coverage_gate.py — blocks the EDIT until there is enough correct footage to cut from.

Promo rule (2026-10-22): shoot coverage and cut to the best. Before P4/P5 may run:
  * every coverage.json line has >= 3 ingested candidates in manifest.json, and
  * >= 2 of them have checks.design == "pass" (or "n/a" when the film has no design.json —
    no product, nothing to get wrong), and
  * total acquired footage (video seconds; a still counts 4 s) >= 3.0 x target_runtime.
When selects.json exists, also:
  * (acquired + clips seconds) / selected seconds >= 3.0,
  * every line ranks >= 2 takes (no line with only one candidate to choose from),
  * every selected cid exists in the manifest and did not FAIL the design check.

Importable:  from coverage_gate import gate;  ok, report_lines = gate(film_dir)
CLI:         python pipeline-tools/coverage_gate.py projects/<film>
Exit 0 = may edit; 1 = blocked (table printed); 2 = could not run (missing/broken files).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

MIN_CANDS, MIN_DESIGN_OK, RATIO = 3, 2, 3.0
STILL_SECS = 4.0


def _secs(c: dict) -> float:
    return STILL_SECS if c.get("kind") == "image" else float(c.get("dur") or 0.0)


def gate(film_dir) -> tuple[bool, list]:
    """(ok, report lines). Raises nothing: unreadable inputs are a block with the reason."""
    film = Path(film_dir)
    try:
        cov = json.loads((film / "coverage.json").read_text())
    except Exception as e:                                   # noqa: BLE001
        return False, [f"COVERAGE GATE BLOCKED: cannot read coverage.json ({e})"]
    try:
        man = json.loads((film / "manifest.json").read_text())
    except Exception as e:                                   # noqa: BLE001
        return False, [f"COVERAGE GATE BLOCKED: cannot read manifest.json ({e}) — run ingest_acquired.py"]
    has_design = (film / "design.json").exists()
    good = {"pass"} | (set() if has_design else {"n/a", None})
    cands = man.get("candidates", [])
    by_line: dict = {}
    for c in cands:
        by_line.setdefault(c.get("line"), []).append(c)

    ok, out = True, []
    tr = float(cov.get("target_runtime") or 0)
    out.append(f"  {'line':>4}  {'cands':>5}  {'design ok':>9}  {'fail':>4}  {'unchk':>5}  "
               f"{'secs':>6}  status")
    for ln in cov.get("lines", []):
        n = ln.get("line")
        cs = by_line.get(n, [])
        d = [(c.get("checks") or {}).get("design") for c in cs]
        n_ok = sum(v in good for v in d)
        n_fail = sum(v == "fail" for v in d)
        n_unc = sum(v == "unchecked" or (has_design and v is None) for v in d)
        why = []
        if len(cs) < MIN_CANDS:
            why.append(f"{len(cs)} candidates (< {MIN_CANDS})")
        if n_ok < MIN_DESIGN_OK:
            why.append(f"{n_ok} design-pass (< {MIN_DESIGN_OK})" +
                       (f", {n_unc} not yet judged/unchecked" if n_unc else ""))
        ok &= not why
        out.append(f"  {str(n):>4}  {len(cs):>5}  {n_ok:>9}  {n_fail:>4}  {n_unc:>5}  "
                   f"{sum(map(_secs, cs)):>6.1f}  {'OK' if not why else 'SHORT: ' + '; '.join(why)}")
    orphans = [c["cid"] for c in cands if c.get("line") not in {l.get("line") for l in cov.get("lines", [])}]
    if orphans:
        out.append(f"  (not on any coverage line, ignored for per-line counts: {', '.join(orphans[:6])}"
                   f"{' …' if len(orphans) > 6 else ''})")

    acq = sum(_secs(c) for c in cands if c.get("origin", "acquired") == "acquired")
    clips = sum(_secs(c) for c in cands if c.get("origin") == "coverage")
    total = acq + clips
    need = RATIO * tr
    footage_ok = tr > 0 and total >= need
    ok &= footage_ok
    out.append(f"  footage: {total:.1f}s ({acq:.1f}s acquired + {clips:.1f}s clips) vs "
               f"{RATIO:.1f} x {tr:.0f}s target = {need:.1f}s → {'OK' if footage_ok else 'SHORT'}")

    sel_path = film / "selects.json"
    if sel_path.exists():
        try:
            sel = json.loads(sel_path.read_text())
        except Exception as e:                               # noqa: BLE001
            return False, out + [f"COVERAGE GATE BLOCKED: cannot read selects.json ({e})"]
        idx = {c["cid"]: c for c in cands}
        sel_secs, problems = 0.0, []
        for ln in sel.get("lines", []):
            takes = ln.get("takes", [])
            if len(takes) < 2:
                problems.append(f"line {ln.get('line')} ranks {len(takes)} take(s) (< 2)")
            for t in takes:
                c = idx.get(t.get("cid"))
                if c is None:
                    problems.append(f"select {t.get('cid')} not in manifest")
                    continue
                if (c.get("checks") or {}).get("design") == "fail":
                    problems.append(f"select {t['cid']} FAILED the design check")
                if t.get("rank") == 1:
                    sel_secs += max(0.0, float(t.get("out", 0)) - float(t.get("in", 0)))
        ratio = total / sel_secs if sel_secs else 0.0
        if ratio < RATIO:
            problems.append(f"shooting ratio {ratio:.2f} (< {RATIO:.1f})")
        ok &= not problems
        out.append(f"  selects: {sel_secs:.1f}s of rank-1 takes, ratio {ratio:.2f}:1"
                   + ("" if not problems else " — " + "; ".join(problems)))
    out.insert(0, "COVERAGE GATE " + ("OK — the edit may start" if ok else "BLOCKED"))
    return ok, out


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    film = Path(sys.argv[1])
    if not (film / "coverage.json").exists() or not (film / "manifest.json").exists():
        ok, out = gate(film)
        print("\n".join(out))
        return 2
    ok, out = gate(film)
    print("\n".join(out))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
