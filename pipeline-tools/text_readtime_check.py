#!/usr/bin/env python3
"""text_readtime_check.py — is every piece of on-screen text up long enough to be READ?

The viewer sees the film once, at full speed, for the first time. A title or callout that is gone
before they finish reading it teaches nothing and reads as a glitch. Rule (from lemo-opuscar's
readcheck.mjs / DIRECTOR.md §7, MIT): from the moment a text block is FULLY visible (entrance
animation done, alpha >= 0.9) until it starts to leave, it must stay up for at least

    hanzi/kana/hangul / 4.5  +  every other non-space character / 15  +  1.5   seconds

(a 5-letter "SITKA" needs 1.83 s fully visible; "Knee tendon" 2.17 s). That is the rule for titles,
callouts, end cards, overlays and film text. SUBTITLES / dialogue captions track speech, so they use the
standard reading-speed rule instead: <= 17 characters per second (CJK 7/s), on screen >= 0.83 s, no
padding; 17-20 cps is a WARN, above 20 cps (or under 0.83 s) a FAIL. No model, string-and-number
work, so it runs before every render (make-promo's edit stage) and again in the gates.

Text blocks, wherever this pipeline defines them (promo SCHEMAS.md and the film side):
  title     edl.json "titles"            text, rec_in..rec_out   (in 0.15 s, out 0.30 s)
  callout   callouts.json "callouts"     label, rec_in..rec_out  (in 0.17 s, out 0.27 s)
  endcard   edl.json "endcard"           title (in 0.25 s), tagline (in 0.78 s), url (in 1.18 s), out 0
  overlay   edl.json "overlays" entries that carry a "text" field (kinetic type baked into a .mov is
            invisible to this tool: give the overlay its "text" to have it checked)
  subtitle  vo/words.json lines when promo.json "lower_third" is true or --lower-third is given
            (Remotion LowerThird: a line is up from start-0.1 to end+0.1), and every cue of any
            .srt in the film folder or final/
  text      generic film text: texts.json or final/timeline.json "texts":
            [{"id", "text", "rec_in", "rec_out", "read_in"?, "read_out"?}]
The entrance/exit seconds are measured from render_edl.py's easing (alpha >= 0.9) and Remotion's fade
frames, the larger of the two. Any block may override them with "read_in" / "read_out" (seconds of
its window that are NOT fully readable). A block cut by the end of the film counts only to the end.

Usage:  python3 pipeline-tools/text_readtime_check.py projects/<film> [--lower-third] [--json]
Exit 0 = every block readable, WARNs listed (or the film declares no on-screen text: said so);
1 = a block is up too short (each one named with need vs got); 2 = could not run (broken files).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

LATIN_CPS, CJK_CPS, PAD = 15.0, 4.5, 1.5
# subtitles / dialogue captions follow the standard reading-speed rule instead (they track speech, so the
# title rule's +1.5 s would fail every normal line): <= 17 cps OK, 17-20 WARN, > 20 FAIL; CJK counts at
# 7 cps (one CJK char = 17/7 Latin chars); on screen >= 0.83 s
SUB_CPS_OK, SUB_CPS_FAIL, SUB_CJK_CPS, SUB_MIN = 17.0, 20.0, 7.0, 0.83
# seconds of a block's window that are not fully readable: (entrance, exit)
ENTER_EXIT = {"title": (0.15, 0.30), "callout": (0.17, 0.27), "overlay": (0.0, 0.0),
              "subtitle": (0.0, 0.0), "text": (0.0, 0.0)}
ENDCARD_IN = {"title": 0.25, "tagline": 0.78, "url": 1.18}
_CJK = re.compile(r"[ᄀ-ᇿ぀-ヿ㄰-㆏㐀-䶿一-鿿"
                  r"가-힯豈-﫿\U00020000-\U0002ffff]")


def need_seconds(text: str) -> float:
    cjk = other = 0
    for ch in text:
        if ch.isspace():
            continue
        if _CJK.match(ch):
            cjk += 1
        else:
            other += 1
    return cjk / CJK_CPS + other / LATIN_CPS + PAD


def readable_window(kind: str, text: str) -> float:
    """The window (rec_out - rec_in) a block of this kind needs so it passes: entrance + read + exit."""
    ei, eo = ENTER_EXIT.get(kind, (0.0, 0.0))
    return round(ei + need_seconds(text) + eo + 0.05, 2)   # +0.05: rec_in/rec_out snap to frames


def _load(p: Path):
    return json.loads(p.read_text()) if p.exists() else None


def _srt_cues(p: Path) -> list[dict]:
    out = []
    ts = re.compile(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)")
    for block in re.split(r"\n\s*\n", p.read_text(errors="ignore").replace("\r", "")):
        lines = [ln for ln in block.strip().splitlines() if ln.strip()]
        for i, ln in enumerate(lines):
            m = ts.search(ln)
            if m:
                g = [int(x) for x in m.groups()]
                a = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
                b = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
                text = re.sub(r"<[^>]+>", "", " ".join(lines[i + 1:])).strip()
                if text:
                    out.append({"text": text, "rec_in": a, "rec_out": b})
                break
    return out


def collect(film: Path, lower_third: bool | None = None) -> tuple[list[dict], float | None]:
    """Every on-screen text block -> [{kind, id, text, rec_in, rec_out, read_in, read_out}], film end."""
    film = Path(film)
    edl = _load(film / "edl.json") or {}
    end = float(edl["dur"]) if edl.get("dur") else None
    items: list[dict] = []

    def add(kind, ident, text, a, b, _src, read_in=None, read_out=None):
        if not text or not str(text).strip():
            return
        ei, eo = ENTER_EXIT.get(kind, (0.0, 0.0))
        items.append({"kind": kind, "id": str(ident), "text": str(text), "rec_in": float(a), "rec_out": float(b),
                      "read_in": float(ei if read_in is None else read_in),
                      "read_out": float(eo if read_out is None else read_out)})

    for k, t in enumerate(edl.get("titles", [])):
        add("title", t.get("id", f"title{k + 1}"), t.get("text"), t["rec_in"], t["rec_out"], t,
            t.get("read_in"), t.get("read_out"))
    for k, o in enumerate(edl.get("overlays", [])):
        if o.get("text"):
            add("overlay", o.get("id", Path(o.get("file", f"overlay{k + 1}")).stem), o["text"], o["rec_in"],
                o["rec_out"], o, o.get("read_in"), o.get("read_out"))
    ec = edl.get("endcard")
    if ec:
        for field, t_in in ENDCARD_IN.items():
            add("endcard", f"endcard.{field}", ec.get(field), ec["rec_in"], ec["rec_out"], ec, t_in, 0.0)
    cpath = film / (edl.get("callouts") or "callouts.json")
    co = _load(cpath) if cpath.suffix == ".json" else None
    for c in (co or {}).get("callouts", []):
        add("callout", c.get("id", "?"), c.get("label") or c.get("id"), c["rec_in"], c["rec_out"], c,
            c.get("read_in"), c.get("read_out"))
    if lower_third is None:
        lower_third = bool((_load(film / "promo.json") or {}).get("lower_third"))
    if lower_third:
        words = _load(film / (edl.get("words") or "vo/words.json")) or {}
        by_line: dict = {}
        for w in words.get("words", []):
            by_line.setdefault(w.get("line"), []).append(w.get("word", ""))
        for ln in words.get("lines", []):
            text = ln.get("text") or " ".join(by_line.get(ln["line"], []))
            add("subtitle", f"line{ln['line']}", text, float(ln["start"]) - 0.1, float(ln["end"]) + 0.1, ln)
    for srt in sorted(list(film.glob("*.srt")) + list((film / "final").glob("*.srt"))):
        for k, c in enumerate(_srt_cues(srt)):
            add("subtitle", f"{srt.name}#{k + 1}", c["text"], c["rec_in"], c["rec_out"], c)
    for src in (film / "texts.json", film / "final" / "timeline.json"):
        d = _load(src)
        for k, t in enumerate((d or {}).get("texts", []) if isinstance(d, dict) else []):
            add("text", t.get("id", f"{src.stem}{k + 1}"), t.get("text"), t["rec_in"], t["rec_out"], t,
                t.get("read_in"), t.get("read_out"))
    items.sort(key=lambda x: x["rec_in"])
    return items, end


def _counts(text: str) -> tuple[int, int]:
    cjk = sum(1 for ch in text if not ch.isspace() and _CJK.match(ch))
    return cjk, sum(1 for ch in text if not ch.isspace()) - cjk


def _judge_subtitle(it: dict, got: float, end: float | None) -> dict:
    cjk, other = _counts(it["text"])
    eq = other + cjk * SUB_CPS_OK / SUB_CJK_CPS          # Latin-equivalent characters
    cps = eq / got if got > 0 else float("inf")
    need = max(SUB_MIN, eq / SUB_CPS_OK)
    level, why = "ok", ""
    if got < SUB_MIN - 1e-6:
        level, why = "fail", f"on screen {got:.2f}s, minimum {SUB_MIN}s"
    elif cps > SUB_CPS_FAIL + 1e-6:
        level, why = "fail", (f"{cps:.1f} cps (fail above {SUB_CPS_FAIL:.0f}): make it {need:.2f}s "
                              f"(rec_out >= {it['rec_in'] + need:.2f}) or shorten the line")
    elif cps > SUB_CPS_OK + 1e-6:
        level, why = "warn", f"{cps:.1f} cps (17-20 is hard to read; {need:.2f}s would be comfortable)"
    if level == "fail" and end and it["rec_out"] > end:
        why += f"; the film ends at {end:.2f}s and cuts it off"
    return {**it, "rule": "subtitle cps", "cps": round(cps, 1), "need": round(need, 2), "got": round(got, 2),
            "ok": level != "fail", "warn": level == "warn", "why": why}


def judge(items: list[dict], end: float | None = None) -> list[dict]:
    rows = []
    for it in items:
        b = min(it["rec_out"], end) if end else it["rec_out"]
        got = max(0.0, (b - it["read_out"]) - (it["rec_in"] + it["read_in"]))
        if it["kind"] == "subtitle":
            rows.append(_judge_subtitle(it, got, end))
            continue
        need = need_seconds(it["text"])
        ok = got >= need - 1e-6
        why = ""
        if not ok:
            # the fix, in the units the author edits: the window it needs
            why = (f"up {got:.2f}s readable, needs {need:.2f}s: make it {it['read_in'] + need + it['read_out']:.2f}s "
                   f"long (rec_out >= {it['rec_in'] + it['read_in'] + need + it['read_out']:.2f})")
            if end and it["rec_out"] > end:
                why += f"; the film ends at {end:.2f}s and cuts it off"
        rows.append({**it, "rule": "chars/15 + 1.5 s", "need": round(need, 2), "got": round(got, 2), "ok": ok,
                     "warn": False, "why": why})
    return rows


def check(film: Path, lower_third: bool | None = None) -> tuple[list[dict], float | None]:
    items, end = collect(film, lower_third)
    return judge(items, end), end


def summary(rows: list[dict]) -> tuple[str, str]:
    """(verdict, detail) in the PASS/FAIL row shape promo_gates and callout_check report."""
    if not rows:
        return "PASS", "no on-screen text declared (titles, callouts, end card, overlays with text, subtitles)"
    bad = [r for r in rows if not r["ok"]]
    warn = [r for r in rows if r.get("warn")]
    if not bad and warn:
        return "WARN", f"{len(warn)} subtitle(s) at 17-20 cps (readable, but tight): " + "; ".join(
            f"'{r['text'][:30]}' at {r['rec_in']:.2f}s {r['why']}" for r in warn[:6])
    if not bad:
        tight = min(rows, key=lambda r: r["got"] - r["need"])
        return "PASS", (f"all {len(rows)} text blocks readable (titles/callouts chars/15 + 1.5 s, subtitles "
                        f"<= 17 cps; tightest: {tight['kind']} '{tight['text'][:30]}' {tight['got']:.2f}s vs "
                        f"{tight['need']:.2f}s)")
    return "FAIL", f"{len(bad)} of {len(rows)} text blocks too short to read: " + "; ".join(
        f"{r['kind']} '{r['text'][:30]}' at {r['rec_in']:.2f}s {r['why']}" for r in bad[:6])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("film")
    ap.add_argument("--lower-third", action="store_true", default=None,
                    help="also check the word-synced lower third (else promo.json lower_third decides)")
    ap.add_argument("--json", action="store_true", help="print the rows as JSON")
    a = ap.parse_args()
    film = Path(a.film).resolve()
    if not film.is_dir():
        print(f"[readtime] no folder {film}", file=sys.stderr)
        return 2
    try:
        rows, end = check(film, a.lower_third)
    except (KeyError, ValueError, TypeError) as e:
        print(f"[readtime] could not read the text blocks ({type(e).__name__}: {e})", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(rows, indent=1, ensure_ascii=False))
    else:
        for r in rows:
            print(f"  {'BAD' if not r['ok'] else 'WRN' if r.get('warn') else 'OK '} {r['kind']:8} {r['id'][:22]:22} at {r['rec_in']:7.2f}s "
                  f"{len(''.join(r['text'].split())):3d} chars  need {r['need']:5.2f}s  got {r['got']:5.2f}s  "
                  f"{json.dumps(r['text'][:34], ensure_ascii=False)}" + (f"\n        {r['why']}" if r["why"] else ""))
    verdict, detail = summary(rows)
    print(f"[readtime] {film.name}: {verdict}: {detail}")
    return 1 if verdict == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
