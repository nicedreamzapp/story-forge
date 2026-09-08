#!/usr/bin/env python3
"""scene_audit — brief the judge like a crew member, then make it answer a checklist.

Matt's pipeline (2026-08-31, after the empty-carriage goodbye): the vision model
gets the STORY first — what this film is, what this scene is for, the setting,
what must be on screen — and then rules element by element: present or missing.
A shot passes only if every required element is found. This is the opposite
failure mode from beat_gate's blind pass: beat_gate catches "the frame doesn't
show the beat"; scene_audit catches "the beat itself forgot something the story
needs" (nobody put the heroes in their own goodbye wagon).

Two passes per frame so the brief can't lead the witness:
  A. BLIND: describe the frame cold (no brief).
  B. CHECKLIST: full brief + required elements, one PRESENT/MISSING per element,
     each judged against what pass A actually saw.

Usage:
  ~/.local/mlx-server/bin/python pipeline-tools/scene_audit.py \
      projects/circus_train [--only s3_rollout] [--frames 3]

Reads:  <proj>/beats.json (shots + clip paths), <proj>/scene_checklists.json
        (per-shot required elements; falls back to the beat text as one element)
Writes: <proj>/SCENE_AUDIT.md and prints a verdict table.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from film_qc import vl_ask  # Picture Eyes :8181 first, in-process fallback

FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"

BRIEF = """You are the continuity supervisor on an animated children's film.

THE FILM: "The Wild Rescue" — Hank (a big round cartoon brown bear with a cream
belly) and Doug (a tall tan-and-orange cartoon bloodhound) run an animal rescue.
A circus train has broken down in the heat with the circus animals trapped
inside the boxcars; Hank and Doug race out on their wooden horse-drawn wagon,
force open the jammed boxcar door, and free the animals — including Ellie, a
young elephant in a red circus cap. The film ends with the animals free in a
meadow at golden hour.

THIS SCENE: {scene_role}
SETTING: {setting}

A colleague who has not read the script described this exact frame as:
\"{blind}\"

Judge the frame yourself. For each required element below, answer PRESENT or
MISSING with one short line of evidence you can SEE. Do not give the scene the
benefit of the doubt: if you cannot clearly see it, it is MISSING.

REQUIRED ELEMENTS:
{elements}

Answer in exactly this format, one line per element, then the last line:
1. PRESENT|MISSING — evidence
2. PRESENT|MISSING — evidence
...
CONTRADICTIONS: <anything on screen that fights the story or physics, or 'none'>"""


def frames_of(clip: Path, n: int, outdir: Path) -> list[Path]:
    dur = float(subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(clip)], capture_output=True, text=True).stdout.strip())
    times = [dur * (i + 1) / (n + 1) for i in range(n)]
    out = []
    for i, t in enumerate(times):
        p = outdir / f"{clip.stem}_{i}.png"
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-ss", f"{t:.2f}",
                        "-i", str(clip), "-frames:v", "1", str(p)], check=True)
        out.append(p)
    return out


def parse_verdicts(text: str, n_elements: int) -> tuple[list[bool], str]:
    present = []
    for i in range(1, n_elements + 1):
        m = re.search(rf"^\s*{i}[.)]\s*(PRESENT|MISSING)", text, re.M | re.I)
        present.append(bool(m and m.group(1).upper() == "PRESENT"))
    c = re.search(r"CONTRADICTIONS:\s*(.+)", text, re.I | re.S)
    contra = (c.group(1).strip().split("\n")[0] if c else "?")
    return present, contra


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--only", action="append")
    ap.add_argument("--frames", type=int, default=2)
    args = ap.parse_args()

    proj = Path(args.project).expanduser().resolve()
    beats = json.loads((proj / "beats.json").read_text())
    checklists = json.loads((proj / "scene_checklists.json").read_text())

    report = ["# Scene audit — brief + checklist judge",
              f"_{time.strftime('%Y-%m-%d %H:%M')} — Qwen3-VL, "
              f"{args.frames} frames per shot, majority per element_", ""]
    table = []
    tmp = Path(tempfile.mkdtemp(prefix="scene_audit_"))

    for shot in beats.get("shots", []):
        sid = shot["id"]
        if args.only and sid not in args.only:
            continue
        spec = checklists.get(sid)
        clip = proj / shot.get("clip", f"clips/{sid}_final.mp4")
        if not clip.is_file():
            if spec:
                table.append((sid, "NO FOOTAGE", "-"))
            continue
        if not spec:
            spec = {"scene_role": shot.get("beat", ""), "setting": shot.get("set", ""),
                    "elements": [shot.get("beat", "")]}
        els = spec["elements"]
        el_lines = "\n".join(f"{i+1}. {e}" for i, e in enumerate(els))
        votes = [0] * len(els)
        contras = []
        for fr in frames_of(clip, args.frames, tmp):
            blind = vl_ask(fr, "Describe everything visible in this frame: every "
                               "character and animal, every object, the setting, "
                               "their positions and what they are doing. Plain and complete.")
            verdict = vl_ask(fr, BRIEF.format(scene_role=spec["scene_role"],
                                              setting=spec.get("setting", ""),
                                              blind=blind[:1200], elements=el_lines))
            present, contra = parse_verdicts(verdict, len(els))
            for i, p in enumerate(present):
                votes[i] += 1 if p else 0
            if contra.lower() not in ("none", "none.", "'none'"):
                contras.append(contra[:200])
        need = args.frames / 2.0
        missing = [els[i] for i, v in enumerate(votes) if v < need]
        ok = not missing
        table.append((sid, "PASS" if ok else "FAIL",
                      "; ".join(m[:70] for m in missing) or
                      (contras[0][:70] if contras else "all elements present")))
        report.append(f"## {sid} — {'PASS' if ok else 'FAIL'}")
        for i, e in enumerate(els):
            report.append(f"- {'✅' if votes[i] >= need else '❌ MISSING'} "
                          f"({votes[i]}/{args.frames}) {e}")
        for c in contras:
            report.append(f"- ⚠ contradiction: {c}")
        report.append("")
        print(f"[{time.strftime('%H:%M:%S')}] {sid}: "
              f"{'PASS' if ok else 'FAIL — missing: ' + '; '.join(missing)[:120]}",
              flush=True)

    (proj / "SCENE_AUDIT.md").write_text("\n".join(report))
    print("\n=== SCENE AUDIT ===")
    for sid, v, why in table:
        print(f"{sid:20s} {v:10s} {why}")
    print(f"\nreport: {proj/'SCENE_AUDIT.md'}")


if __name__ == "__main__":
    main()
