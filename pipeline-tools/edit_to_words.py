#!/usr/bin/env python3
"""edit_to_words.py — cut the picture to the narration's WORDS: words + cues + selects -> edl.json.

WHY THIS EXISTS (promo format, 2026-10-22): the first Sitka promo laid the narration over
the shots and never cut to the words. Every shot change was a 0.5 s xfade wherever a clip
happened to run out, and the motion was drift. An editor cuts ON the word ("a motor at each
KNEE" — the knee shot lands on "knee"). So:
  * every shot change lands on a word onset (a `cut`/`xfade` cue in cues.json) or on a line
    boundary; nothing else creates a cut, except a select running short (said out loud);
  * hard cuts by default; a dissolve ONLY where a cue says `xfade`;
  * min shot 0.8 s; a cue that would make a shorter shot is refused, not nudged;
  * the top-ranked select of a line is used first, further selects fill the line's later
    spans in rank order; a take is never looped and never stretched with setpts (frozen
    rule 4); if a select is shorter than its span, it cuts to the next select on a word
    onset inside the span and SAYS SO; if no word onset fits, the short select is skipped.
  * J-cuts (`--jcut 0.5`): the picture of a line may lead its voice by up to 0.5 s (never
    earlier than the previous line's last word ending).

Reads (in projects/<film>/): vo/words.json, cues.json, selects.json, manifest.json
(file paths, kinds and durations by cid), callouts.json (optional).
Writes: edl.json (schema: pipeline/formats/promo/SCHEMAS.md) and edl.txt (human summary).
If callouts.json exists, every callout named by a `callout` cue gets its rec_in moved onto
the cue's word onset (duration kept) so cue_check passes for the right reason.

Schema additions (fields added, nothing renamed): shots carry "head"/"tail" (dissolve
handles, s), "kind" (video|image), "anchor_text"; the EDL carries "overlays" (see SCHEMAS.md), "titles"
[{"text","rec_in","rec_out","line","word"}], "events" (every resolved cue with its time),
"tail" and "notes". An `xfade` of d seconds is CENTERED on the word onset: the incoming shot
is 50% mixed at its rec_in, fading over [rec_in - d/2, rec_in + d/2]; both shots need d/2 of
source handle there (src_in - head >= 0, src_out + tail <= clip dur), and a missing handle
is shrunk and noted rather than invented.

Usage:
  python3 pipeline-tools/edit_to_words.py projects/<film> [--jcut 0.5] [--min-shot 0.8]
          [--tail 0.6] [--title-dur 1.6]
Exit 0 = edl.json written; 1 = the cut can't be made as asked (a cue too close, a line
without enough coverage, an unknown word) — read the messages; 2 = inputs missing/broken.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_XFADE = 0.4


def norm(w):
    return re.sub(r"[^a-z0-9']", "", str(w).lower()).strip("'")


def load(film, name, required=True):
    p = film / name
    if not p.exists():
        if required:
            print(f"[edit_to_words] missing {p}", file=sys.stderr)
            sys.exit(2)
        return None
    try:
        return json.loads(p.read_text())
    except Exception as e:
        print(f"[edit_to_words] {p} is not valid JSON: {e}", file=sys.stderr)
        sys.exit(2)


def resolve_cue(cue, words):
    """Return the words.json word dict a cue points at, or None."""
    want = norm(cue.get("word", ""))
    nth = int(cue.get("nth", 1))
    hits = [w for w in words if w["line"] == cue["line"] and norm(w["word"]) == want]
    if len(hits) < nth:
        return None
    return hits[nth - 1]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("film")
    ap.add_argument("--jcut", type=float, default=0.0,
                    help="let a line's picture lead its voice by up to this many seconds (try 0.5)")
    ap.add_argument("--min-shot", type=float, default=0.8)
    ap.add_argument("--tail", type=float, default=0.6, help="picture after the last word ends")
    ap.add_argument("--title-dur", type=float, default=1.6)
    ap.add_argument("--lines", default=None, help="only cut these lines, e.g. 1-3 (for tests)")
    a = ap.parse_args()
    film = Path(a.film).resolve()

    W = load(film, "vo/words.json")
    cues = load(film, "cues.json").get("cues", [])
    sel = load(film, "selects.json").get("lines", [])
    man = load(film, "manifest.json")
    callouts = load(film, "callouts.json", required=False)
    cands = {c["cid"]: c for c in man.get("candidates", [])}
    fps = int(man.get("fps", 30))
    words = W["words"]
    lines = W["lines"]
    if a.lines:
        lo, _, hi = a.lines.partition("-")
        keep = set(range(int(lo), int(hi or lo) + 1))
        lines = [ln for ln in lines if ln["line"] in keep]
        cues = [c for c in cues if c["line"] in keep]
    if not lines:
        print("[edit_to_words] no lines", file=sys.stderr)
        sys.exit(2)

    errors, notes, events = [], [], []
    frame = 1.0 / fps

    def q(t):  # quantize to the frame grid so renderers and checks agree
        return round(round(t * fps) / fps, 4)

    # ---- resolve every cue to its word onset
    resolved = []
    for c in cues:
        w = resolve_cue(c, words)
        if w is None:
            errors.append(f"cue {c} names a word not spoken in line {c['line']} "
                          f"(see vo/words.json; the audio is the truth)")
            continue
        resolved.append((c, w))
        events.append({"kind": c["kind"], "line": c["line"], "word": c["word"],
                       "nth": c.get("nth", 1), "i": w["i"], "t": q(w["start"]),
                       **({"callout": c["callout"]} if c.get("callout") else {}),
                       **({"dur": c["dur"]} if c.get("dur") else {})})

    # ---- line picture spans: boundary of line L = its voice start, or earlier with --jcut
    def last_word_end(line_no):
        ws = [w for w in words if w["line"] == line_no]
        return ws[-1]["end"] if ws else None

    bounds = []
    for k, ln in enumerate(lines):
        if k == 0:
            bounds.append(0.0)
            continue
        b = ln["start"]
        if a.jcut > 0:
            prev_end = last_word_end(lines[k - 1]["line"]) or lines[k - 1]["end"]
            b = max(prev_end + 2 * frame, ln["start"] - a.jcut)
        bounds.append(q(b))
    last_end = last_word_end(lines[-1]["line"]) or lines[-1]["end"]
    total = q(max(lines[-1]["end"], last_end + a.tail))
    # END CARD (promo.json "endcard", the Sitka recipe): the title slam lands AFTER the last
    # word ends (slam_after, default 0.15 s) so the hit never masks it; the shots stop at the
    # slam and the card holds for endcard.dur while the music sting rings out.
    endcard = None
    pj = film / "promo.json"
    if pj.exists() and not a.lines:
        ec = (json.loads(pj.read_text()).get("endcard") or {})
        if float(ec.get("dur", 0) or 0) > 0:
            slam = q(last_end + float(ec.get("slam_after", 0.15)))
            total = q(slam + float(ec["dur"]))
            endcard = {"rec_in": slam, "rec_out": total, "title": ec.get("title", ""),
                       "tagline": ec.get("tagline", ""), "url": ec.get("url", ""),
                       "after_word": (words[-1]["word"] if words else None), "last_word_end": round(last_end, 4)}
    bounds.append(endcard["rec_in"] if endcard else total)

    sel_by_line = {s["line"]: sorted(s.get("takes", []), key=lambda t: t.get("rank", 99)) for s in sel}
    shots, titles = [], []
    for k, ln in enumerate(lines):
        L = ln["line"]
        lo, hi = bounds[k], bounds[k + 1]
        # cut points inside this line's span, from cut/xfade cues
        cps = {}
        for c, w in resolved:
            if c["line"] != L or c["kind"] not in ("cut", "xfade"):
                continue
            t = q(w["start"])
            if abs(t - lo) < 0.05 or (k == 0 and t < a.min_shot):
                # a cue on the line's first word IS the line boundary: move the boundary there
                if k > 0 and abs(t - lo) >= frame / 2:
                    notes.append(f"line {L}: boundary moved {lo:.2f}->{t:.2f} onto cued word '{w['word']}'")
                    lo = t
                    bounds[k] = t
                    if shots:
                        shots[-1]["rec_out"] = t
                cps[lo] = (c, w)
                continue
            if t <= lo or t >= hi:
                errors.append(f"line {L}: cue on '{w['word']}' at {t:.2f}s is outside the line's picture span {lo:.2f}-{hi:.2f}")
                continue
            cps[t] = (c, w)
        pts = sorted(set([lo] + [t for t in cps if t > lo]))
        spans = list(zip(pts, pts[1:] + [hi]))
        for s0, s1 in spans:
            if s1 - s0 < a.min_shot - 1e-6:
                errors.append(f"line {L}: shot {s0:.2f}-{s1:.2f} is {s1 - s0:.2f}s, under the {a.min_shot}s minimum; "
                              f"move or drop the cue there")
        line_words = [w for w in words if w["line"] == L]
        first_i = line_words[0]["i"] if line_words else None
        pool = list(sel_by_line.get(L, []))
        if len(pool) < 2:
            notes.append(f"line {L}: only {len(pool)} select(s); the promo contract asks for >= 2")
        for s0, s1 in spans:
            cue_here = cps.get(s0)
            trans, xf = "cut", 0.0
            if cue_here and cue_here[0]["kind"] == "xfade":
                trans, xf = "xfade", float(cue_here[0].get("dur", DEFAULT_XFADE))
            anchor = cue_here[1] if cue_here else None
            t = s0
            first_piece = True
            while t < s1 - 1e-6:
                need = s1 - t
                chosen = None
                while pool:
                    take = pool.pop(0)
                    cand = cands.get(take["cid"])
                    if cand is None:
                        errors.append(f"line {L}: select {take['cid']} is not in manifest.json")
                        continue
                    kind = "image" if cand.get("kind") in ("image", "still") else "video"
                    tin = float(take.get("in", 0.0))
                    tout = float(take.get("out", cand.get("dur", 0.0))) if kind == "video" else tin + 1e9
                    if kind == "video" and tout > float(cand.get("dur", tout)) + 1e-3:
                        notes.append(f"line {L}: {take['cid']} out {tout:.2f} > clip dur {cand['dur']:.2f}; clamped")
                        tout = float(cand["dur"])
                    have = tout - tin
                    if have >= need - 1e-6:
                        chosen = (take, cand, kind, tin, need)
                        break
                    # short select: split the span on a word onset it can reach
                    onsets = [q(w["start"]) for w in line_words
                              if t + a.min_shot <= q(w["start"]) <= t + have and s1 - q(w["start"]) >= a.min_shot]
                    if onsets and have >= a.min_shot:
                        cut_at = max(onsets)
                        wcut = next(w for w in line_words if q(w["start"]) == cut_at)
                        notes.append(f"line {L}: select {take['cid']} has {have:.2f}s for a {need:.2f}s span; "
                                     f"it plays {cut_at - t:.2f}s, then the next select takes over on '{wcut['word']}' "
                                     f"at {cut_at:.2f}s")
                        chosen = (take, cand, kind, tin, cut_at - t)
                        break
                    notes.append(f"line {L}: select {take['cid']} skipped: {have:.2f}s is too short for "
                                 f"{need:.2f}s and no word onset lets it split")
                if chosen is None:
                    errors.append(f"line {L}: ran out of selects at {t:.2f}s ({s1 - t:.2f}s still to fill); "
                                  f"needs more coverage (never loop or stretch a take)")
                    break
                take, cand, kind, tin, ln_used = chosen
                end = q(t + ln_used)
                if first_piece and anchor is not None:
                    aw = anchor
                elif not first_piece:
                    aw = next((w for w in line_words if q(w["start"]) == q(t)), None)
                else:
                    aw = line_words[0] if line_words and s0 == lo else None
                shots.append({
                    "cid": take["cid"], "file": cand["file"], "kind": kind,
                    "src_in": round(tin, 4), "src_out": round(tin + (end - t), 4),
                    "rec_in": q(t), "rec_out": end, "line": L,
                    "transition": trans if first_piece else "cut", "xfade": xf if first_piece else 0.0,
                    "anchor_word": aw["i"] if aw else first_i,
                    "anchor_text": aw["word"] if aw else None, "speed": 1.0,
                    "head": 0.0, "tail": 0.0, "src_dur": cand.get("dur"),
                    **({"move": take["move"]} if take.get("move") else {}),
                })
                t = end
                first_piece = False

    # ---- dissolve handles (centered on the word) — shrink if the source can't give them
    for n, sh in enumerate(shots):
        if sh["transition"] != "xfade" or n == 0:
            if n == 0 and sh["transition"] == "xfade":
                sh["transition"], sh["xfade"] = "cut", 0.0
                notes.append("first shot can't dissolve from nothing; made it a cut")
            continue
        half = sh["xfade"] / 2
        prev = shots[n - 1]
        head = half if sh["kind"] == "image" else min(half, sh["src_in"])
        tail = half if prev["kind"] == "image" else min(half, float(prev.get("src_dur") or 0) - prev["src_out"])
        h = max(0.0, min(head, tail))
        if h < half - 1e-6:
            notes.append(f"xfade into {sh['cid']} at {sh['rec_in']:.2f}: only {h:.2f}s of handle each side "
                         f"(wanted {half:.2f}); dissolve shortened to {2 * h:.2f}s")
        sh["head"] = round(h, 4)
        prev["tail"] = round(h, 4)
        sh["xfade"] = round(2 * h, 4)
        if h == 0:
            sh["transition"] = "cut"

    # ---- overlays (alpha clips: Manim ProRes 4444 / WebM) land on their words
    overlays = []
    for c, w in resolved:
        if c["kind"] != "overlay":
            continue
        of = film / c.get("file", "")
        if not c.get("file") or not of.exists():
            errors.append(f"overlay cue on '{c['word']}' names file '{c.get('file')}', not found under {film}")
            continue
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                            str(of)], capture_output=True, text=True)
        try:
            fdur = float(r.stdout.strip())
        except ValueError:
            errors.append(f"overlay {c['file']} is not a readable video")
            continue
        t_in = q(w["start"])
        want = float(c.get("dur", fdur))
        if want > fdur + 1e-3:
            notes.append(f"overlay {c['file']}: asked {want:.2f}s, clip is {fdur:.2f}s; it ends with the clip (never looped)")
            want = fdur
        overlays.append({"file": c["file"], "rec_in": t_in, "rec_out": q(min(total, t_in + want)),
                         "x": float(c.get("x", 0.5)), "y": float(c.get("y", 0.5)), "w": float(c.get("w", 1.0)),
                         "opacity": float(c.get("opacity", 1.0)), "cue_word": w["word"], "line": c["line"],
                         "src_in": float(c.get("src_in", 0.0))})

    # ---- titles and callouts land on their words
    for c, w in resolved:
        if c["kind"] == "title":
            titles.append({"text": c.get("text") or w["word"], "rec_in": q(w["start"]),
                           "rec_out": q(min(total, w["start"] + float(c.get("dur", a.title_dur)))),
                           "line": c["line"], "word": w["word"], "i": w["i"]})
    if callouts:
        byid = {co["id"]: co for co in callouts.get("callouts", [])}
        changed = False
        for c, w in resolved:
            if c["kind"] != "callout":
                continue
            co = byid.get(c.get("callout"))
            if co is None:
                errors.append(f"callout cue on '{c['word']}' names '{c.get('callout')}', not in callouts.json")
                continue
            dur = float(co.get("rec_out", 0) - co.get("rec_in", 0)) if "rec_out" in co else 2.5
            if dur <= 0:
                dur = 2.5
            new_in = q(w["start"])
            if abs(co.get("rec_in", -99) - new_in) > 1e-3:
                shift = new_in - co.get("rec_in", new_in)
                co["rec_in"], co["rec_out"] = new_in, q(min(total, new_in + dur))
                if isinstance(co.get("tip"), list) and co["tip"] and isinstance(co["tip"][0], list):
                    co["tip"] = [[round(k[0] + shift, 3), k[1], k[2]] for k in co["tip"]]
                changed = True
                notes.append(f"callout {co['id']} moved onto '{w['word']}' at {new_in:.2f}s")
        if changed:
            (film / "callouts.json").write_text(json.dumps(callouts, indent=1))
    elif any(c["kind"] == "callout" for c, _ in resolved):
        notes.append("callout cues present but no callouts.json yet (07_callouts); cue_check will flag them")

    audio = [{"file": ln["wav"], "rec_in": ln["start"], "kind": "vo", "line": ln["line"]} for ln in lines]
    edl = {"fps": fps, "w": int(man.get("w", 1920)), "h": int(man.get("h", 1080)), "dur": total,
           "shots": shots, "audio": audio, "titles": titles, "overlays": overlays, "events": events,
           "callouts": "callouts.json", "words": "vo/words.json", "tail": a.tail, "endcard": endcard,
           "jcut": a.jcut, "notes": notes}

    # ---- summary
    out_lines = [f"EDL  {film.name}  {total:.2f}s  {len(shots)} shots  fps {fps}  jcut {a.jcut}", ""]
    for sh in shots:
        tr = "CUT " if sh["transition"] == "cut" else f"XF{sh['xfade']:.1f}"
        out_lines.append(f"{sh['rec_in']:7.2f}-{sh['rec_out']:7.2f} ({sh['rec_out'] - sh['rec_in']:4.2f}s) {tr}  "
                         f"L{sh['line']:<2} on '{sh['anchor_text'] or '-'}'  {sh['cid']}  "
                         f"src {sh['src_in']:.2f}-{sh['src_out']:.2f}")
    for ov in overlays:
        out_lines.append(f"{ov['rec_in']:7.2f}-{ov['rec_out']:7.2f} OVERLAY {ov['file']} on '{ov['cue_word']}'")
    if endcard:
        out_lines.append(f"{endcard['rec_in']:7.2f}-{endcard['rec_out']:7.2f} END CARD '{endcard['title']}' "
                         f"(slam {endcard['rec_in'] - endcard['last_word_end']:.2f}s after the last word)")
    for tt in titles:
        out_lines.append(f"{tt['rec_in']:7.2f}-{tt['rec_out']:7.2f} TITLE '{tt['text']}' on '{tt['word']}'")
    if notes:
        out_lines += ["", "NOTES:"] + [f"  - {n}" for n in notes]
    if errors:
        out_lines += ["", "ERRORS:"] + [f"  - {e}" for e in errors]
    (film / "edl.txt").write_text("\n".join(out_lines) + "\n")
    print("\n".join(out_lines))
    if errors:
        print(f"[edit_to_words] {len(errors)} error(s); edl.json NOT written", file=sys.stderr)
        sys.exit(1)
    (film / "edl.json").write_text(json.dumps(edl, indent=1))
    print(f"[edit_to_words] wrote {film / 'edl.json'}")


if __name__ == "__main__":
    main()
