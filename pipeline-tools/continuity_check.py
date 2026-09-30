#!/usr/bin/env python3
"""continuity_check.py — does the cut tell the story? MANDATORY before a film is shown.

Built 2026-09-30. film_qc passed The Oldest Tree while the story contradicted itself on
screen, and Matt found every one of these by watching: the tree looked burned to a
stump (twice — a fallen log and a smoking snapped snag), the flashlight "went out" and
then glowed in four later shots, a lost and freezing grandfather grinned, the raincoat
changed owners off-screen, and the "heart is still there" ending showed charred bark
with no heart. film_qc checks faces, mouths and glitches; nothing checked STORY STATE.

Two halves:
  1. STATE RULES (automatic). projects/<film>/continuity.json lists facts that must hold
     over a range of shots; the VL judge votes on 3 frames of each shot.
        {"rules": [
          {"id": "flashlight_dead", "from": "s6_black", "to": "s7_wide",
           "question": "Is there a lit flashlight, lamp or beam of artificial light anywhere in this frame?",
           "expect": "NO"},
          {"id": "tree_stands", "shots": ["*"],
           "question": "Does this frame show a tree that has burned down, fallen over or been reduced to a stump?",
           "expect": "NO"}]}
     "shots": ["*"] = every shot; "from"/"to" = an inclusive range in cut order.
  2. STORY SHEET (for the reader). final/story_sheet.png (one labelled frame per shot)
     and final/story_sheet.md (shot, time, the narration line playing over it). Claude
     READS both against the story before showing Matt, and writes down anything a viewer
     would find confusing. The rules only catch what someone already thought of.

    ~/.local/mlx-server/bin/python pipeline-tools/continuity_check.py projects/<film> [FILM.mp4]

Exit 0 = every rule holds; 1 = violations (listed with shot + time); 2 = could not run.
"""
import json, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from film_qc import vl_ask, extract_frame  # noqa: E402

FF = "/opt/homebrew/bin/ffmpeg"


def main():
    proj = Path(sys.argv[1]).resolve()
    if len(sys.argv) > 2:
        film = Path(sys.argv[2]).resolve()
    else:  # the newest finished cut in final/ (not WIP reels or tests)
        cands = [c for c in (proj / "final").glob("*.mp4")
                 if not c.name.startswith(("WIP", "_")) and "test" not in c.name.lower()]
        film = max(cands, key=lambda c: c.stat().st_mtime)
    tl = json.load(open(proj / "final" / "timeline.json"))
    order, starts, lens = tl["order"], tl["starts"], tl["lens"]
    nar = tl.get("narration", [])
    texts = {}
    nj = proj / "narration.json"
    if nj.exists():
        texts = {f"nia_{x['id']}.wav": x["text"] for x in json.load(open(nj))}

    # --- story sheet -------------------------------------------------------
    from PIL import Image, ImageDraw
    frames, md = [], ["| # | shot | time | narration over this shot |", "|---|---|---|---|"]
    with tempfile.TemporaryDirectory() as tmp:
        for i, (sid, st, ln) in enumerate(zip(order, starts, lens)):
            f = Path(tmp) / f"{i:02d}.png"
            extract_frame(film, st + ln / 2, f)
            im = Image.open(f).convert("RGB")
            im = im.crop((0, int(im.height * 0.144), im.width, int(im.height * 0.856))).resize((384, 154))
            ImageDraw.Draw(im).text((6, 4), f"{i:02d} {sid} {st:.0f}s", fill=(255, 255, 0))
            frames.append(im)
            over = [texts.get(fn, fn) for fn, t in nar if st - 0.5 <= t < st + ln]
            md.append(f"| {i:02d} | {sid} | {st:.1f}s | {' / '.join(over)} |")
        cols = 6; rows = (len(frames) + cols - 1) // cols
        sheet = Image.new("RGB", (384 * cols, 154 * rows))
        for i, im in enumerate(frames):
            sheet.paste(im, ((i % cols) * 384, (i // cols) * 154))
        sheet.save(proj / "final" / "story_sheet.png")
        (proj / "final" / "story_sheet.md").write_text("\n".join(md) + "\n")

        # --- state rules -----------------------------------------------------
        cj = proj / "continuity.json"
        if not cj.exists():
            print("NO continuity.json — write the film's state rules first (see docstring). Story sheet written.")
            return 1
        rules = json.load(open(cj))["rules"]
        bad, log = [], []
        for r in rules:
            if r.get("shots") == ["*"]:
                ids = list(order)
            elif "shots" in r:
                ids = [s for s in r["shots"] if s in order]
            else:
                a = order.index(r["from"]) if r["from"] in order else 0
                b = order.index(r["to"]) if r["to"] in order else len(order) - 1
                ids = order[a:b + 1]
            for sid in ids:
                i = order.index(sid); st, ln = starts[i], lens[i]
                votes = []
                for k, frac in enumerate((0.25, 0.5, 0.75)):
                    f = Path(tmp) / f"r{k}.png"
                    extract_frame(film, st + ln * frac, f)
                    ans = vl_ask(f, r["question"] + " Answer YES or NO first, then one short sentence.")
                    votes.append("YES" if ans.strip().upper().startswith("YES") else "NO")
                got = max(set(votes), key=votes.count)
                ok = got == r["expect"]
                log.append(f"- [{'PASS' if ok else 'FAIL'}] {r['id']} @ {sid} ({st:.1f}s): {votes} (expect {r['expect']})")
                if not ok:
                    bad.append(f"{r['id']} broken in {sid} at {st:.1f}s")
    out = [f"# continuity_check — {film.name}", f"**Verdict: {'FAIL' if bad else 'PASS'}** — {len(bad)} violation(s)",
           "Rules only catch what someone thought of. ALSO read final/story_sheet.png + story_sheet.md against the story.",
           ""] + [f"- {b}" for b in bad] + ["", "## Full log"] + log
    text = "\n".join(out)
    (proj / "final" / "continuity_report.md").write_text(text + "\n")
    print(text)
    return 1 if bad else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001
        print(f"continuity_check could not run: {e}")
        sys.exit(2)
