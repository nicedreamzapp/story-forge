#!/usr/bin/env python3
"""beat_gate.py — does the PICTURE show the BEAT?

The hole this fills (found 2026-07-25, the circus_train "stick in the door"
incident): film_qc.py checks mouths, faces, limb counts and audio timing. Every
one of those passes on a shot that depicts completely the wrong action. A bear
idly poking a plank wall with a stick passed 91 checks while the story beat —
"he drives his shoulder into a jammed door" — was nowhere on screen.

So this gate asks the only question that matters before render time: LOOK at
this frame, say what is physically happening, and is that the beat or not.

Two passes per shot, deliberately:
  1. BLIND — the model describes the action with NO knowledge of the intended
     beat. This is what makes the check honest; told the answer first, a VL
     model will agree with it.
  2. VERDICT — the blind description plus the intended beat go back in and the
     model rules PASS/FAIL, with hard fail conditions the shot must not contain.

Optional third pass: SET continuity against a locked set master (the train, the
wagon), the same way characters are held to canon. Sets were never locked, which
is how one episode ended up with four different trains.

Beats file (JSON):
{
  "set_masters": {"train": "canon/train_canon.png"},
  "shots": [
    {"id": "s6_heave",
     "image": "stills/LOCKED_s6.png",
     "beat": "a large brown bear drives his shoulder into a stuck boxcar door,
              straining with his whole body weight",
     "must_not": ["holding a stick, tool or any object",
                  "standing relaxed or smiling",
                  "sawdust or debris spraying from the wall"],
     "set": "train"}
  ]
}
A shot may name "clip" + "t" instead of "image" and the frame is pulled with ffmpeg.

Usage:
  beat_gate.py beats.json [--report OUT.md] [--only s6_heave]
Exit 0 = every shot depicts its beat. 1 = at least one FAIL. 2 = gate could not
run (never treat 2 as a pass).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from film_qc import vl_ask, _state, PE_URL  # noqa: E402  (same VL plumbing)

BLIND = (
    "Describe EXACTLY what is physically happening in this image. Answer in 3 "
    "short sentences covering: (1) what each animal or person is DOING with "
    "their body — posture, weight, effort, is anything being pushed or lifted; "
    "(2) every object in or near their hands or paws, however small; (3) the "
    "location and anything unusual in the air (dust, debris, smoke). Describe "
    "only what is visible. Do not guess at story or intent."
)

VERDICT = (
    "A film shot must depict this beat:\n\n  {beat}\n\n"
    "An independent viewer described the actual image as:\n\n  {desc}\n\n"
    "{forbid}"
    "Looking at the image yourself, does it clearly depict the beat above to a "
    "viewer who has no script? Be strict — an action that is merely POSSIBLE in "
    "the frame is not depicted. If the body shows no effort, or the wrong "
    "action, or a forbidden element is present, it FAILS.\n"
    "Answer with PASS or FAIL as the first word, then one sentence of reason."
)

FORBID = ("The shot FAILS automatically if any of these is present: {items}.\n")

SET_Q = (
    "The LEFT image is the locked design of this production's {name}. The RIGHT "
    "image is a shot from the same film. Is the {name} in the right image the "
    "SAME one — same construction, same colours, same materials, same era — so "
    "a viewer reads them as one object and not two different ones? Answer YES or "
    "NO first, then one sentence."
)


def grab_frame(clip: Path, t: float) -> Path:
    out = Path(tempfile.mkdtemp()) / f"{clip.stem}_{t}.png"
    subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(clip),
                    "-frames:v", "1", str(out), "-y"], check=True)
    return out


def side_by_side(master: Path, shot: Path, out: Path) -> Path:
    from PIL import Image, ImageDraw
    m = Image.open(master).convert("RGB")
    s = Image.open(shot).convert("RGB")
    H = 520
    fit = lambda im: im.resize((int(im.width * H / im.height), H), Image.LANCZOS)
    m, s = fit(m), fit(s)
    sheet = Image.new("RGB", (m.width + s.width + 30, H + 34), (18, 18, 18))
    sheet.paste(m, (0, 34))
    sheet.paste(s, (m.width + 30, 34))
    d = ImageDraw.Draw(sheet)
    d.text((8, 10), "LOCKED SET (canon)", fill=(255, 255, 0))
    d.text((m.width + 38, 10), "THIS SHOT", fill=(0, 255, 255))
    sheet.save(out)
    return out


def clip_duration(clip: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(clip)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def sample_frames(shot: dict, root: Path, votes: int) -> list:
    """The frames this shot gets judged on.

    A single instant is NOT a verdict. Same clip, same content, sampled 1.1s vs
    2.7s, produced opposite rulings on 2026-07-25 — the identical noise that sent
    seven good lip-sync clips to 'failed' in film_qc two days earlier. So a clip
    is judged on several frames spread across its length and the majority rules;
    a still is judged several times independently.
    """
    if shot.get("image"):
        img = (root / shot["image"]).resolve()
        return [img] * max(1, votes) if Path(img).exists() else []
    clip = (root / shot["clip"]).resolve()
    if not clip.exists():
        return []
    if shot.get("t") is not None and votes == 1:
        return [grab_frame(clip, float(shot["t"]))]
    dur = clip_duration(clip)
    lo, hi = shot.get("window", [0.15 * dur, 0.85 * dur])
    n = max(1, votes)
    step = (hi - lo) / max(1, n - 1) if n > 1 else 0
    return [grab_frame(clip, round(lo + i * step, 2)) for i in range(n)]


def check_shot(shot: dict, root: Path, masters: dict, votes: int = 3) -> dict:
    frames = sample_frames(shot, root, votes)
    if not frames:
        src = shot.get("image") or shot.get("clip")
        return {"id": shot["id"], "verdict": "ERROR", "why": f"missing or unreadable {src}"}

    forbid = FORBID.format(items="; ".join(shot["must_not"])) if shot.get("must_not") else ""
    ballots = []
    for f in frames:
        desc = vl_ask(f, BLIND)
        ruling = vl_ask(f, VERDICT.format(beat=shot["beat"].strip(), desc=desc, forbid=forbid))
        ballots.append({"frame": str(f), "description": desc, "ruling": ruling,
                        "pass": bool(re.match(r"^\W*PASS", ruling, re.I))})
    yes = sum(1 for b in ballots if b["pass"])
    passed = yes * 2 > len(ballots)          # strict majority
    img = frames[0]

    res = {"id": shot["id"], "image": str(img), "votes": f"{yes}/{len(ballots)}",
           "description": ballots[0]["description"], "ballots": ballots,
           "verdict": "PASS" if passed else "FAIL",
           "why": f"{yes} of {len(ballots)} sampled frames depict the beat. "
                  + next((b["ruling"] for b in ballots if b["pass"] != passed),
                         ballots[0]["ruling"])}

    name = shot.get("set")
    if name and name in masters:
        cmp_png = Path(tempfile.mkdtemp()) / "set_cmp.png"
        side_by_side((root / masters[name]).resolve(), Path(img), cmp_png)
        ans = vl_ask(cmp_png, SET_Q.format(name=name))
        same = bool(re.match(r"^\W*YES", ans, re.I))
        res["set_check"] = {"set": name, "verdict": "PASS" if same else "FAIL", "why": ans}
        if not same:
            res["verdict"] = "FAIL"
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("beats")
    ap.add_argument("--report", default=None)
    ap.add_argument("--only", default=None, help="check a single shot id")
    ap.add_argument("--votes", type=int, default=3,
                    help="frames sampled per shot; majority rules (default 3). "
                         "1 = single instant, which is NOT a verdict — see sample_frames")
    args = ap.parse_args()

    beats_path = Path(args.beats).resolve()
    spec = json.loads(beats_path.read_text())
    root = beats_path.parent
    masters = spec.get("set_masters", {})
    shots = spec["shots"]
    if args.only:
        shots = [s for s in shots if s["id"] == args.only]
        if not shots:
            print(f"no shot id {args.only}", file=sys.stderr)
            return 2

    try:
        import requests
        _state["use_server"] = requests.get(f"{PE_URL}/status", timeout=3).json().get("loaded", False)
    except Exception:
        _state["use_server"] = False
    print(f"[beat_gate] VL via {'server :8181' if _state['use_server'] else 'in-process'}",
          flush=True)

    results = []
    for s in shots:
        try:
            r = check_shot(s, root, masters, votes=args.votes)
        except Exception as e:                                  # noqa: BLE001
            r = {"id": s["id"], "verdict": "ERROR", "why": f"{type(e).__name__}: {e}"}
        results.append(r)
        mark = {"PASS": "PASS", "FAIL": "FAIL", "ERROR": "ERR "}[r["verdict"]]
        print(f"[{mark}] {r['id']}: {r.get('why','')[:150]}", flush=True)

    fails = [r for r in results if r["verdict"] == "FAIL"]
    errs = [r for r in results if r["verdict"] == "ERROR"]

    # ---- STORY SPINE ---------------------------------------------------------
    # Per-shot checks cannot catch a beat that was never shot at all. Episode 1
    # shipped with no door ever opening and Ellie never on screen: every shot
    # present was fine on its own terms and the middle of the story was simply
    # absent. So the spine lists the beats the film cannot exist without, and
    # each one must be satisfied by at least one PASSING shot.
    spine = spec.get("spine", [])
    holes = []
    if spine and not args.only:
        passed_ids = {r["id"] for r in results if r["verdict"] == "PASS"}
        for need in spine:
            if not (set(need.get("shots", [])) & passed_ids):
                holes.append(need)
        print(f"[beat_gate] story spine: {len(spine) - len(holes)}/{len(spine)} required "
              f"beats are on screen", flush=True)
        for h in holes:
            print(f"[HOLE] {h['beat']} — no passing shot ({', '.join(h.get('shots', [])) or 'none listed'})",
                  flush=True)

    lines = [f"# beat_gate report — {beats_path.name}", ""]
    lines.append(f"**{len(results) - len(fails) - len(errs)} of {len(results)} shots depict "
                 f"their beat.** {len(fails)} FAIL, {len(errs)} could not be judged.")
    if spine:
        lines.append("")
        lines.append(f"**Story spine: {len(spine) - len(holes)}/{len(spine)} required beats "
                     f"are on screen.**")
        for h in holes:
            lines.append(f"- HOLE — {h['beat']} (expected from: "
                         f"{', '.join(h.get('shots', [])) or 'nothing'})")
    for r in results:
        lines += ["", f"## {r['id']} — {r['verdict']}"]
        if r.get("votes"):
            lines.append(f"- frames depicting the beat: {r['votes']}")
        for b in r.get("ballots", []):
            mark = "PASS" if b["pass"] else "FAIL"
            lines.append(f"  - [{mark}] {Path(b['frame']).name}: {b['description']}")
            lines.append(f"    ruling: {b['ruling']}")
        lines.append(f"- ruling: {r.get('why','')}")
        if r.get("set_check"):
            sc = r["set_check"]
            lines.append(f"- set continuity ({sc['set']}): {sc['verdict']} — {sc['why']}")
    out = Path(args.report) if args.report else beats_path.with_name(
        beats_path.stem + "_report.md")
    out.write_text("\n".join(lines) + "\n")
    print(f"[beat_gate] report → {out}")

    if errs and not fails and not holes:
        return 2
    return 1 if (fails or holes) else 0


if __name__ == "__main__":
    raise SystemExit(main())
