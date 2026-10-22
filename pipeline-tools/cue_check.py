#!/usr/bin/env python3
"""cue_check.py — prove every cue landed on its word: the EDL gate for the promo format.

WHY THIS EXISTS (promo format, 2026-10-22; frozen rule 17 "the EDL is a shot nobody gates"):
the Sitka promo's cuts were 0.5 s dissolves wherever a clip ran out, and nothing checked that
the picture changed when the voice said the word. This gate reads the cut you are about to
render and asks one question per cue: did the event (cut / xfade / callout / title) happen
within --tol (100 ms, about 3 frames) of that word's onset in vo/words.json? A string-and-
number compare, no model, so it runs before every render.

Checks, per cue in cues.json:
  cut      a shot with transition "cut" whose rec_in is within tol of the word onset
  xfade    a shot with transition "xfade" whose rec_in (the 50% point) is within tol
  callout  the callouts.json entry named by the cue: its rec_in within tol
  title    an edl.json "titles" entry on that word: its rec_in within tol
  overlay  the edl.json "overlays" entry with the cue's file: its rec_in within tol
Also: shots tile the timeline with no gaps/overlaps, none under 0.8 s, no shot plays past its
source clip, and dissolves appear only where an xfade cue asked.

Usage:
  python3 pipeline-tools/cue_check.py projects/<film> [--tol 0.1] [--lines 1-3]
Exit 0 = every cue hit; 1 = misses (table printed); 2 = could not run (missing/broken files).
NEVER treat 2 as a pass.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit_to_words import resolve_cue  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("film")
    ap.add_argument("--tol", type=float, default=0.1)
    ap.add_argument("--min-shot", type=float, default=0.8)
    ap.add_argument("--lines", default=None, help="only check cues on these lines, e.g. 1-3")
    a = ap.parse_args()
    film = Path(a.film).resolve()
    try:
        W = json.loads((film / "vo/words.json").read_text())
        cues = json.loads((film / "cues.json").read_text())["cues"]
        edl = json.loads((film / "edl.json").read_text())
        cpath = film / edl.get("callouts", "callouts.json")
        callouts = json.loads(cpath.read_text())["callouts"] if cpath.exists() else []
    except Exception as e:
        print(f"[cue_check] could not read inputs: {e}", file=sys.stderr)
        sys.exit(2)
    if a.lines:
        lo, _, hi = a.lines.partition("-")
        keep = set(range(int(lo), int(hi or lo) + 1))
        cues = [c for c in cues if c["line"] in keep]

    shots = edl["shots"]
    rows, misses = [], 0
    xfade_times = []
    for c in cues:
        w = resolve_cue(c, W["words"])
        kind = c["kind"]
        label = f"L{c['line']} '{c['word']}'" + (f"#{c['nth']}" if c.get("nth", 1) != 1 else "")
        if w is None:
            rows.append((label, kind, None, None, None, "MISS: word not in vo/words.json"))
            misses += 1
            continue
        t = w["start"]
        if kind in ("cut", "xfade"):
            cand = [s["rec_in"] for s in shots if s["transition"] == kind]
            if kind == "xfade":
                xfade_times.append(t)
        elif kind == "callout":
            cand = [co["rec_in"] for co in callouts if co.get("id") == c.get("callout")]
        elif kind == "title":
            cand = [tt["rec_in"] for tt in edl.get("titles", [])]
        elif kind == "overlay":
            cand = [ov["rec_in"] for ov in edl.get("overlays", []) if ov.get("file") == c.get("file")]
        else:
            rows.append((label, kind, t, None, None, f"MISS: unknown cue kind '{kind}'"))
            misses += 1
            continue
        if not cand:
            rows.append((label, kind, t, None, None, "MISS: no such event in the EDL"))
            misses += 1
            continue
        got = min(cand, key=lambda x: abs(x - t))
        err = got - t
        ok = abs(err) <= a.tol
        misses += 0 if ok else 1
        rows.append((label, kind, t, got, err, "ok" if ok else f"MISS: {err * 1000:+.0f} ms"))

    # structural checks on the cut itself
    struct = []
    for p, n in zip(shots, shots[1:]):
        if abs(p["rec_out"] - n["rec_in"]) > 1e-3:
            struct.append(f"gap/overlap between {p['cid']} (out {p['rec_out']:.3f}) and {n['cid']} (in {n['rec_in']:.3f})")
    for s in shots:
        d = s["rec_out"] - s["rec_in"]
        if d < a.min_shot - 1e-3:
            struct.append(f"{s['cid']} at {s['rec_in']:.2f} is {d:.2f}s (< {a.min_shot}s)")
        if s.get("kind") != "image" and s.get("src_dur") and s["src_out"] + s.get("tail", 0) > s["src_dur"] + 1e-3:
            struct.append(f"{s['cid']} plays to {s['src_out'] + s.get('tail', 0):.2f}s of a {s['src_dur']:.2f}s clip")
        if abs(float(s.get("speed", 1.0)) - 1.0) > 1e-6:
            struct.append(f"{s['cid']} has speed {s['speed']} (frozen rule 4: never stretch a take)")
        if s["transition"] == "xfade" and not any(abs(s["rec_in"] - t) <= a.tol for t in xfade_times):
            if not a.lines or s["line"] in keep:
                struct.append(f"dissolve into {s['cid']} at {s['rec_in']:.2f} with no xfade cue asking for it")
    ec = edl.get("endcard")
    pic_end = ec["rec_in"] if ec else edl["dur"]
    if shots and abs(shots[-1]["rec_out"] - pic_end) > 1e-3:
        struct.append(f"last shot ends {shots[-1]['rec_out']:.2f}, picture should end at {pic_end:.2f}"
                      + (" (the end-card slam)" if ec else ""))
    if ec:
        # the slam must land AFTER the last word, never on it (Sitka: the hit masked "Come")
        lw = max((w["end"] for w in W["words"]), default=0.0)
        if ec["rec_in"] < lw - 1e-3:
            struct.append(f"end-card slam at {ec['rec_in']:.2f} lands before the last word ends ({lw:.2f}): it masks the word")
        if abs(ec["rec_out"] - edl["dur"]) > 1e-3:
            struct.append(f"end card ends {ec['rec_out']:.2f}, edl dur {edl['dur']:.2f}")

    print(f"{'cue':28} {'kind':8} {'word at':>8} {'event':>8} {'err ms':>7}  result")
    for label, kind, t, got, err, res in rows:
        fmt = lambda v: f"{v:8.3f}" if v is not None else "       -"
        e = f"{err * 1000:+7.0f}" if err is not None else "      -"
        print(f"{label:28} {kind:8} {fmt(t)} {fmt(got)} {e}  {res}")
    for s in struct:
        print(f"STRUCT: {s}")
    n = len(rows)
    print(f"[cue_check] {n} cues: {n - misses} hit, {misses} missed (tol {a.tol * 1000:.0f} ms); "
          f"{len(struct)} structural problem(s)")
    sys.exit(1 if (misses or struct) else 0)


if __name__ == "__main__":
    main()
