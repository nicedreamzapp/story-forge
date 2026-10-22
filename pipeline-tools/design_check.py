#!/usr/bin/env python3
"""design_check.py — is the PRODUCT in this footage built the way the product is built?

The hole this fills (2026-10-22, the Sitka promo): every gate we had compared FACES against
references. Nothing compared a physical product's geometry against its design. A promo for a
real device (Sitka: a carbon rear leg swings down behind each thigh and plants on the ground;
one knee motor + steel ratchet per knee; belt batteries) cannot ship a Grok clip where the
rear leg grows out of the shin, or a ChatGPT still with wheels. Acquired footage (browser AI
tools, CAD renders) passes the same gate as local renders.

Per candidate in manifest.json (frozen rule 14 / RULES 1, 3, 7, 18; frozen rule 26):
  1. BLIND  — the middle frame is described with NO product facts in the prompt. Saved.
  2. VISIBLE — side-by-side (CANDIDATE left, REFERENCE right): is the same device in the
     candidate at all? If not, every fact is UNCHECKED for that frame (never a pass).
  3. FACTS  — each design.json fact is asked about the CANDIDATE only, against the matching
     reference angle, on 5 frames (1 for a still). Majority vote; every ballot prints.
  4. MUST_NOT — each must_not item (plus beat_gate's house list as ONE question, rule 26)
     is asked per frame; a majority yes = FAIL.
Verdict: any fact or must_not FAIL -> fail; else anything unreadable -> unchecked; else pass.

design.json (SCHEMAS.md) — optional extra field per fact (added 2026-10-22):
  "when": "the person is seated"   a visible precondition; frames where it is false make the
                                   fact n/a for that frame (a walking shot has no planted leg).

Usage:
  ~/.local/mlx-server/bin/python pipeline-tools/design_check.py projects/<film> [--votes 5]
        [--only CID] [--force]
  ~/.local/mlx-server/bin/python pipeline-tools/design_check.py --calibrate CAL.json
  ~/.local/mlx-server/bin/python pipeline-tools/design_check.py projects/<film> --calibrate
        (uses projects/<film>/design_calibration.json)
Writes design_report.json + design_report.md and updates manifest.json checks.design.
Exit 0 = every judged candidate passed; 1 = a fail/unchecked candidate (or calibration < 80%);
2 = could not run (Song Forge busy, memory guard critical, model missing) — NEVER a pass.

Ballots are cached by (image bytes, prompt, model) in ~/.cache/story-forge/design_ballots.json
so a re-run only pays for what changed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import film_qc  # noqa: E402  (same VL plumbing: vl_ask, _state, memory lease)
from film_qc import vl_ask, _state, PE_URL, MODEL_ID  # noqa: E402

try:
    from beat_gate import HOUSE_MUST_NOT  # noqa: E402
except Exception:                                            # noqa: BLE001
    HOUSE_MUST_NOT = []

SONGFORGE = "http://127.0.0.1:8767/api/status"
CACHE = Path.home() / ".cache" / "story-forge" / "design_ballots.json"
STILL_SECS = 4.0
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}

BLIND = (
    "Describe exactly what you see in this image in 3 short sentences: (1) who or what is in "
    "it, (2) what any machine or device looks like and where each of its parts sits relative "
    "to the person or objects around it (above, below, behind, in front), (3) what touches the "
    "ground. Do not guess what it is for."
)
PANELS = (
    "This picture has two panels. The RIGHT panel, labelled REFERENCE (correct design), shows "
    "the correct product. The LEFT panel, labelled CANDIDATE, is the image being checked. "
    "Look ONLY at the CANDIDATE (left) panel when you answer; use the reference only to know "
    "which device and which parts are meant.\n\n"
)
VISIBLE_Q = (PANELS + "Is the same kind of product or device shown in the REFERENCE also "
             "clearly visible in the CANDIDATE? Answer yes or no first, then one short reason.")
FACT_Q = (PANELS + "Question about the CANDIDATE: {q}\nAnswer with {fmt} first, then one short "
          "reason. If that part of the device cannot be seen in the CANDIDATE, answer "
          "'not visible'.")
MUSTNOT_Q = (PANELS + "Does the CANDIDATE show {x}? Answer yes or no first, then one short reason.")
WHEN_Q = "Look at this image. Is this true: {w}? Answer yes or no first, then one short reason."

WORDNUM = {"zero": 0, "none": 0, "no": 0, "one": 1, "single": 1, "two": 2, "both": 2,
           "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8}


# ---------------------------------------------------------------- shared VL plumbing
def songforge_busy() -> int:
    """jobs_running on Song Forge (0 when it is idle or unreachable)."""
    try:
        with urllib.request.urlopen(SONGFORGE, timeout=5) as r:
            return int(json.loads(r.read()).get("jobs_running", 0) or 0)
    except Exception:                                        # noqa: BLE001
        return 0


def wait_for_songforge(max_wait: int, tag: str) -> bool:
    """Song Forge customer jobs outrank QC. Wait for it to go idle, else give up (exit 2)."""
    deadline = time.time() + max_wait
    while True:
        n = songforge_busy()
        if n == 0:
            return True
        if time.time() >= deadline:
            print(f"[{tag}] Song Forge still has {n} job(s) running after {max_wait}s — "
                  "NOT loading the 32B judge. UNCHECKED, never a pass.", file=sys.stderr)
            return False
        print(f"[{tag}] Song Forge busy ({n} job running) — waiting", file=sys.stderr, flush=True)
        time.sleep(20)


def detect_server() -> bool:
    try:
        import requests
        _state["use_server"] = requests.get(f"{PE_URL}/status", timeout=3).json().get("loaded", False)
    except Exception:                                        # noqa: BLE001
        _state["use_server"] = False
    return _state["use_server"]


def run_with_vl(tag: str, body, max_wait: int = 900) -> int:
    """Song Forge check -> memory lease (film_qc's pattern) -> body(). Returns an exit code."""
    if not wait_for_songforge(max_wait, tag):
        return 2
    server = detect_server()
    print(f"[{tag}] VL via {'server :8181' if server else 'in-process ' + MODEL_ID}", flush=True)
    if server:
        return body()
    # frozen rule 11: non-ComfyUI heavy steps pass bin/mem-gate before loading anything big
    mg = HERE.parent / "bin" / "mem-gate"
    if mg.exists() and subprocess.run([str(mg), f"{tag} 32B VL judge"]).returncode != 0:
        print(f"[{tag}] mem-gate refused — UNCHECKED, never a pass.", file=sys.stderr)
        return 2
    with film_qc._mem_reserve(f"{tag}-vl", 26, timeout=1800, ttl=3600) as lease:
        if lease is None and film_qc._guard_says_critical():
            print(f"[{tag}] REFUSING TO START: the memory guard would not grant 26GB for the "
                  "vision judge and reports the machine critical. UNCHECKED, never a pass.",
                  file=sys.stderr)
            return 2
        if lease is None and film_qc._HAVE_GUARD:
            print(f"[{tag}] no memory lease (guard did not answer) — running anyway; if this "
                  "is killed the result is UNCHECKED, not passed.", file=sys.stderr)
        try:
            return body()
        finally:
            film_qc.unload_vl()


class Ballots:
    """vl_ask with a content-addressed cache; every answer is kept for the report."""

    def __init__(self):
        try:
            self.cache = json.loads(CACHE.read_text())
        except Exception:                                    # noqa: BLE001
            self.cache = {}
        self.calls = 0
        self.hits = 0

    def ask(self, image: Path, prompt: str) -> str:
        h = hashlib.sha256(Path(image).read_bytes()).hexdigest()
        key = hashlib.sha256(f"{MODEL_ID}|{h}|{prompt}".encode()).hexdigest()
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        ans = vl_ask(str(image), prompt)
        self.calls += 1
        self.cache[key] = ans
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CACHE.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.cache))
        tmp.replace(CACHE)
        return ans


# ---------------------------------------------------------------- parsing
def parse_yesno(text: str):
    t = (text or "").strip().lower()
    if re.match(r"^\W*(not visible|cannot|can't|unclear|unable|unknown|n/a)", t):
        return None
    m = re.match(r"^\W*(yes|no)\b", t)
    if m:
        return m.group(1)
    ys, ns = re.search(r"\byes\b", t), re.search(r"\bno\b", t)
    if ys and not ns:
        return "yes"
    if ns and not ys:
        return "no"
    return None


def parse_number(text: str):
    t = (text or "").strip().lower()
    if re.match(r"^\W*(not visible|cannot|can't|unclear|unable|unknown|n/a)", t):
        return None
    m = re.match(r"^\W*(\d+)", t)
    if m:
        return int(m.group(1))
    m = re.match(r"^\W*([a-z]+)", t)
    if m and m.group(1) in WORDNUM:
        return WORDNUM[m.group(1)]
    m = re.search(r"\b(\d+)\b", t)
    return int(m.group(1)) if m else None


def majority(values: list):
    """Strict majority over ALL ballots (unreadable ones count against a decision)."""
    from collections import Counter
    real = [v for v in values if v is not None]
    if not real:
        return None
    v, n = Counter(real).most_common(1)[0]
    return v if n * 2 > len(values) else None


# ---------------------------------------------------------------- frames and panels
def probe_dur(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def frames_for(path: Path, votes: int, tmp: Path) -> list:
    """[(t, png)] — the still itself, or `votes` frames spread over 10..90% of the clip."""
    from PIL import Image
    if path.suffix.lower() in IMG_EXT:
        out = tmp / f"{path.stem}_still.png"
        im = Image.open(path).convert("RGB")
        im.thumbnail((768, 768))
        im.save(out)
        return [(None, out)]
    dur = probe_dur(path)
    if dur <= 0:
        return []
    n = max(1, votes)
    ts = [dur / 2] if n == 1 else [dur * (0.1 + 0.8 * i / (n - 1)) for i in range(n)]
    got = []
    for t in ts:
        out = tmp / f"{path.stem}_{t:07.2f}.png"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", str(path),
                        "-frames:v", "1", "-vf", "scale=768:-2", str(out)], capture_output=True)
        if out.exists() and out.stat().st_size > 1000:
            got.append((round(t, 2), out))
    return got


def middle_frame(path: Path, tmp: Path) -> Path | None:
    f = frames_for(path, 1, tmp)
    return f[0][1] if f else None


def _font(size):
    from PIL import ImageFont
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def side_by_side(cand: Path, ref: Path, out: Path) -> Path:
    """CANDIDATE on the left, REFERENCE on the right, labelled, same height."""
    from PIL import Image, ImageDraw
    c = Image.open(cand).convert("RGB")
    r = Image.open(ref).convert("RGB")
    H = 520
    fit = lambda im: im.resize((max(1, int(im.width * H / im.height)), H), Image.LANCZOS)
    c, r = fit(c), fit(r)
    sheet = Image.new("RGB", (c.width + r.width + 30, H + 46), (18, 18, 18))
    sheet.paste(c, (0, 46))
    sheet.paste(r, (c.width + 30, 46))
    d = ImageDraw.Draw(sheet)
    d.text((10, 8), "CANDIDATE", fill=(0, 255, 255), font=_font(30))
    d.text((c.width + 40, 8), "REFERENCE (correct design)", fill=(255, 255, 0), font=_font(30))
    sheet.save(out)
    return out


# ---------------------------------------------------------------- the judge
def judge(path: Path, design: dict, design_root: Path, votes: int, B: Ballots, tmp: Path,
          house: bool = True) -> dict:
    """Judge one image/clip against design.json. Returns a full record with every ballot."""
    rec = {"file": str(path), "verdict": "unchecked", "why": "", "blind": None,
           "visible": [], "facts": [], "must_not": []}
    if not path.exists():
        rec["why"] = "file missing"
        return rec
    refs = {k: (design_root / v) for k, v in design.get("references", {}).items()}
    if not refs or not all(p.exists() for p in refs.values()):
        rec["why"] = "design.json reference image missing: " + ", ".join(
            str(p) for p in refs.values() if not p.exists())
        return rec
    frames = frames_for(path, votes, tmp)
    if not frames:
        rec["why"] = "could not read any frame"
        return rec

    # 1. BLIND, before any product fact is in a prompt.
    mid = frames[len(frames) // 2][1]
    rec["blind"] = B.ask(mid, BLIND)

    default_angle = "side" if "side" in refs else sorted(refs)[0]
    panels = {}

    def panel(fr: Path, angle: str) -> Path:
        key = (str(fr), angle)
        if key not in panels:
            panels[key] = side_by_side(fr, refs.get(angle, refs[default_angle]),
                                       tmp / f"{fr.stem}__{angle}.png")
        return panels[key]

    # 2. VISIBLE per frame; frames without the device are skipped (their ballots are None).
    seen = {}
    for t, fr in frames:
        raw = B.ask(panel(fr, default_angle), VISIBLE_Q)
        v = parse_yesno(raw)
        seen[str(fr)] = v == "yes"
        rec["visible"].append({"t": t, "raw": raw, "parsed": v})
    if not any(seen.values()):
        rec["why"] = "device not visible in any sampled frame"
        return rec

    # 3. FACTS
    fails, unread = [], []
    for f in design.get("facts", []):
        exp = f["expect"]
        numeric = isinstance(exp, (int, float)) and not isinstance(exp, bool)
        fmt = "a number (digits)" if numeric else "yes or no"
        q = FACT_Q.format(q=f["q"], fmt=fmt)
        ballots = []
        for t, fr in frames:
            if not seen[str(fr)]:
                ballots.append({"t": t, "raw": "(device not visible in this frame)", "parsed": None})
                continue
            if f.get("when"):
                wraw = B.ask(fr, WHEN_Q.format(w=f["when"]))
                if parse_yesno(wraw) == "no":
                    ballots.append({"t": t, "raw": f"(n/a: '{f['when']}' is false) {wraw}",
                                    "parsed": "n/a"})
                    continue
            raw = B.ask(panel(fr, f.get("angle", default_angle)), q)
            p = parse_number(raw) if numeric else parse_yesno(raw)
            ballots.append({"t": t, "raw": raw, "parsed": p})
        vals = [b["parsed"] for b in ballots if b["parsed"] != "n/a"]
        if not vals:
            result, maj = "n/a", None
        else:
            maj = majority(vals)
            want = int(exp) if numeric else str(exp).lower()
            result = "unchecked" if maj is None else ("pass" if maj == want else "fail")
        rec["facts"].append({"q": f["q"], "expect": exp, "angle": f.get("angle", default_angle),
                             "when": f.get("when"), "ballots": ballots, "majority": maj,
                             "result": result})
        if result == "fail":
            fails.append(f"fact '{f['q']}' answered {maj}, design says {exp}")
        elif result == "unchecked":
            unread.append(f"fact '{f['q']}' had no majority")

    # 4. MUST_NOT (+ the house list as one question, frozen rule 26)
    items = list(design.get("must_not", []))
    if house and HOUSE_MUST_NOT:
        items.append("any of these: " + "; ".join(HOUSE_MUST_NOT))
    for x in items:
        ballots = []
        for t, fr in frames:
            if not seen[str(fr)]:
                ballots.append({"t": t, "raw": "(device not visible in this frame)", "parsed": None})
                continue
            raw = B.ask(panel(fr, default_angle), MUSTNOT_Q.format(x=x))
            ballots.append({"t": t, "raw": raw, "parsed": parse_yesno(raw)})
        vals = [b["parsed"] for b in ballots]
        yes = sum(v == "yes" for v in vals)
        if yes * 2 > len(vals):
            result = "fail"
        elif majority(vals) == "no":
            result = "pass"
        else:
            result = "unchecked"
        rec["must_not"].append({"x": x, "ballots": ballots, "yes": yes, "of": len(vals),
                                "result": result})
        if result == "fail":
            fails.append(f"shows forbidden '{x[:80]}' ({yes}/{len(vals)} frames)")
        elif result == "unchecked":
            unread.append(f"must_not '{x[:60]}' had no majority")

    judged = [f for f in rec["facts"] if f["result"] in ("pass", "fail")]
    if fails:
        rec["verdict"], rec["why"] = "fail", "; ".join(fails)
    elif unread:
        rec["verdict"], rec["why"] = "unchecked", "; ".join(unread)
    elif not judged:
        rec["verdict"], rec["why"] = "unchecked", "every fact was n/a for these frames"
    else:
        rec["verdict"], rec["why"] = "pass", f"{len(judged)} facts and {len(items)} must_not held"
    return rec


# ---------------------------------------------------------------- reports
def write_md(path: Path, title: str, recs: list, extra: list | None = None) -> None:
    L = [f"# {title}", "", f"_ran {time.strftime('%Y-%m-%d %H:%M')} · judge {MODEL_ID}_", ""]
    L += extra or []
    L += ["| cid | verdict | why |", "|---|---|---|"]
    for r in recs:
        L.append(f"| {r.get('cid', r.get('id'))} | **{r['verdict'].upper()}** "
                 f"{('(expect ' + r['expect'] + ')') if r.get('expect') else ''} | "
                 f"{r.get('why', '').replace('|', '/')[:200]} |")
    for r in recs:
        L += ["", f"## {r.get('cid', r.get('id'))} — {r['verdict'].upper()}", f"`{r['file']}`", "",
              f"**Blind:** {r.get('blind')}", "", "**Device visible:**"]
        L += [f"- t={b['t']}: {b['parsed']} — {b['raw'][:160]}" for b in r.get("visible", [])]
        for f in r.get("facts", []):
            L += ["", f"**Fact ({f['result'].upper()})** {f['q']} — expect `{f['expect']}`, "
                      f"majority `{f['majority']}` [{f['angle']}]"]
            L += [f"- t={b['t']}: `{b['parsed']}` — {b['raw'][:160]}" for b in f["ballots"]]
        for m in r.get("must_not", []):
            L += ["", f"**Must not ({m['result'].upper()}, {m['yes']}/{m['of']} yes)** {m['x'][:120]}"]
            L += [f"- t={b['t']}: `{b['parsed']}` — {b['raw'][:160]}" for b in m["ballots"]]
    path.write_text("\n".join(L) + "\n")


def update_manifest(man_path: Path, verdicts: dict) -> None:
    man = json.loads(man_path.read_text())          # re-read: others may have written it
    for c in man.get("candidates", []):
        if c["cid"] in verdicts:
            c.setdefault("checks", {})["design"] = verdicts[c["cid"]]
    tmp = man_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(man, indent=1))
    tmp.replace(man_path)


# ---------------------------------------------------------------- modes
def check_film(film: Path, votes: int, only: str | None, force: bool) -> int:
    man_path, des_path = film / "manifest.json", film / "design.json"
    if not man_path.exists():
        print(f"[design_check] no {man_path} — run ingest_acquired.py first", file=sys.stderr)
        return 2
    man = json.loads(man_path.read_text())
    cands = man.get("candidates", [])
    if not des_path.exists():
        update_manifest(man_path, {c["cid"]: "n/a" for c in cands})
        print("[design_check] no design.json — every candidate marked n/a (no product to check)")
        return 0
    design = json.loads(des_path.read_text())
    todo = [c for c in cands if (only is None or c["cid"] == only)
            and (force or (c.get("checks") or {}).get("design") not in ("pass", "fail"))]
    print(f"[design_check] {design.get('product')}: {len(todo)} of {len(cands)} candidates to judge, "
          f"{votes} frames per clip", flush=True)

    def body() -> int:
        B, tmp = Ballots(), Path(tempfile.mkdtemp(prefix="design_check_"))
        blind_dir = film / "design" / "blind"
        blind_dir.mkdir(parents=True, exist_ok=True)
        rep_path = film / "design_report.json"
        try:
            prior = {r["cid"]: r for r in json.loads(rep_path.read_text()).get("candidates", [])}
        except Exception:                                    # noqa: BLE001
            prior = {}
        verdicts = {}
        for c in todo:
            try:
                r = judge(film / c["file"], design, film, votes, B, tmp)
            except Exception as e:                           # noqa: BLE001
                r = {"file": c["file"], "verdict": "unchecked", "why": f"{type(e).__name__}: {e}"}
            r["cid"] = c["cid"]
            r["line"] = c.get("line")
            if r.get("blind"):
                (blind_dir / f"{c['cid']}.txt").write_text(r["blind"] + "\n")
            prior[c["cid"]] = r
            verdicts[c["cid"]] = r["verdict"]
            update_manifest(man_path, {c["cid"]: r["verdict"]})
            print(f"[{r['verdict'].upper():9}] {c['cid']}: {r.get('why', '')[:150]}", flush=True)
        recs = [prior[k] for k in sorted(prior)]
        rep_path.write_text(json.dumps({"product": design.get("product"), "judge": MODEL_ID,
                                        "ran": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                        "votes": votes, "candidates": recs}, indent=1))
        write_md(film / "design_report.md", f"Design check — {design.get('product')}", recs)
        print(f"[design_check] VL calls {B.calls}, cache hits {B.hits} → design_report.md", flush=True)
        bad = [r for r in recs if r["verdict"] != "pass"]
        return 1 if bad else 0

    if not todo:
        print("[design_check] nothing to judge (use --force to re-judge)")
        return 0
    return run_with_vl("design_check", body)


def calibrate(cal_path: Path, votes: int) -> int:
    cal = json.loads(cal_path.read_text())
    root = cal_path.parent
    design = json.loads((root / cal["design"]).read_text())
    design_root = (root / cal["design"]).parent

    def body() -> int:
        B, tmp = Ballots(), Path(tempfile.mkdtemp(prefix="design_cal_"))
        recs = []
        for s in cal["shots"]:
            p = root / (s.get("image") or s["clip"])
            try:
                r = judge(p, design, design_root, votes, B, tmp)
            except Exception as e:                           # noqa: BLE001
                r = {"file": str(p), "verdict": "unchecked", "why": f"{type(e).__name__}: {e}"}
            r["id"], r["expect"] = s["id"], s["expect"].upper()
            recs.append(r)
            print(f"[{r['verdict'].upper():9}] {s['id']} (human {r['expect']}): "
                  f"{r.get('why', '')[:140]}", flush=True)
        # Unjudgeable is excluded from the score, never counted as agreement (beat_gate rule).
        graded = [r for r in recs if r["verdict"] in ("pass", "fail")]
        agree = [r for r in graded if r["verdict"].upper() == r["expect"]]
        for r in recs:
            if r not in graded:
                print(f"[UNCHECKED] {r['id']}: excluded from calibration — {r.get('why', '')[:140]}")
        pct = round(100 * len(agree) / len(graded)) if graded else 0
        line = (f"[design_check] CALIBRATION: agrees with {len(agree)}/{len(graded)} known verdicts "
                f"({pct}%), {len(recs) - len(graded)} UNCHECKED")
        print(line, flush=True)
        for r in graded:
            if r["verdict"].upper() != r["expect"]:
                print(f"[MISCAL] {r['id']}: gate said {r['verdict'].upper()}, truth {r['expect']} "
                      f"— {r.get('why', '')[:160]}", flush=True)
        warn = pct < 80 or not graded
        if warn:
            print("[design_check] WARNING: the design judge disagrees with known verdicts too often "
                  "to be trusted — fix the facts' wording or the judge before believing a verdict",
                  flush=True)
        write_md(root / "design_calibration_report.md", "Design check calibration",
                 recs, extra=[line.split("] ", 1)[1], ""])
        print(f"[design_check] VL calls {B.calls}, cache hits {B.hits} → "
              f"{root / 'design_calibration_report.md'}", flush=True)
        return 1 if warn else 0

    return run_with_vl("design_check", body)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("film", nargs="?", help="projects/<film>")
    ap.add_argument("--votes", type=int, default=5, help="frames per clip (stills always 1)")
    ap.add_argument("--only", default=None, help="judge one cid")
    ap.add_argument("--force", action="store_true", help="re-judge candidates already pass/fail")
    ap.add_argument("--calibrate", nargs="?", const="", default=None,
                    help="grade the judge on a calibration file (default <film>/design_calibration.json)")
    a = ap.parse_args()
    if a.calibrate is not None:
        cal = Path(a.calibrate) if a.calibrate else (Path(a.film or ".") / "design_calibration.json")
        if not cal.exists():
            print(f"[design_check] no calibration file {cal} — verdicts are UNVERIFIED", file=sys.stderr)
            return 2
        return calibrate(cal.resolve(), a.votes)
    if not a.film:
        ap.error("film dir required")
    return check_film(Path(a.film).resolve(), a.votes, a.only, a.force)


if __name__ == "__main__":
    sys.exit(main())
