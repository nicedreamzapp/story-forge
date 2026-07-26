#!/usr/bin/env python3
"""spec_lint — refuse to repeat a known mistake, deterministically.

Prompt-injected lessons are soft: the sampler may or may not listen. This is the
hard half of self-learning. Every mistake that cost us a night is encoded here as a
rule that reads the SPEC before a single second of GPU time is spent, and blocks it.

A lesson that only lives in a text file gets ignored under pressure. A lesson that
fails the run cannot be.

    python3 pipeline-tools/spec_lint.py projects/circus_train/shots.json
    exit 0 = clean · 1 = the spec repeats a known mistake (message says which)

Every rule below is dated to the incident that produced it.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# ── the mistakes, as patterns ────────────────────────────────────────────────
INTENT = re.compile(r"\b(trying to|attempting to|wants? to|hoping|about to|so that|"
                    r"in order to|realiz\w+|understand\w*|decide\w*)\b", re.I)
UNSEEABLE = re.compile(r"\b(inside|behind the door|off[- ]screen|out of frame|"
                       r"frightened animal|thinking|feels?)\b", re.I)
CHANGE_OVER_TIME = re.compile(r"\b(widen\w*|steps? (down|out|forward)|opens? up|"
                              r"begins? to|starts? to|slowly \w+s|gradually|"
                              r"turns? into|becomes?)\b", re.I)
IMPACT = re.compile(r"\b(impact|collision|collide|smash\w*|bursts?|shatter\w*|"
                    r"splinters?|slams?|crash\w*|hits?|strikes?|punch\w*)\b", re.I)
POSITIVE_EXCLUSION = re.compile(r"\bno\s+(animals?|people|persons?|characters?|text|"
                                r"letters?|words?|humans?)\b", re.I)
REAR_VIEW = re.compile(r"\b(from behind|rear view|back to (the )?camera|seen from the back)\b", re.I)

RULES = [
    ("beat", INTENT,
     "beats must be VISIBLE STATES — this one describes intent, which no frame can show "
     "(2026-07-26: 'trying to reach the frightened animal' failed every probe on a still "
     "that had already been approved)"),
    ("beat", UNSEEABLE,
     "beats must not depend on facts the camera cannot see (what is inside, off-screen, "
     "or in a character's head)"),
    ("beat", CHANGE_OVER_TIME,
     "beats must describe a STATE, not a change over time — a single frame cannot show a "
     "crack widening or a step being taken (2026-07-26: two animations failed every probe)"),
    ("animate", IMPACT,
     "never prompt an impact or collision: the renderer converts it into a continuous "
     "particle spray that reads as drilling (2026-07-24, the rejected door shot)"),
    ("prompt", IMPACT,
     "never prompt an impact in a still either — the debris ends up baked into the frame"),
    ("prompt", POSITIVE_EXCLUSION,
     "'NO animals/people/text' in a POSITIVE prompt produces exactly that, and FLUX.2 "
     "rejects negative prompts outright — describe the scene as deserted, abandoned, "
     "silent instead (2026-07-26: 12 seeds, 3 cycles, a dog every time)"),
    ("prompt", REAR_VIEW,
     "character parts rendered from behind carry NO identity — muzzle, ears, markings are "
     "all on the front — so they can never pass the identity gate (2026-07-26)"),
]

CHARACTER_WORDS = re.compile(r"\b(bear|dog|bloodhound|hound|elephant|hank|doug|ellie)\b", re.I)


def lint_shot(shot: dict, project: Path) -> list:
    problems = []
    for field, pattern, why in RULES:
        text = shot.get(field) or ""
        if isinstance(text, str) and (m := pattern.search(text)):
            problems.append(f"{shot.get('id','?')}: [{field}] '{m.group(0)}' — {why}")

    # a shot with named characters must declare who to check against canon
    beat = (shot.get("beat") or "") + " " + (shot.get("prompt") or "")
    named = set(w.lower() for w in CHARACTER_WORDS.findall(beat))
    if named and not shot.get("identity") and not shot.get("_no_characters"):
        problems.append(
            f"{shot.get('id','?')}: mentions {sorted(named)} but declares no identity check — "
            "every named character is checked against its locked master, or a dog that is "
            "not Doug walks straight through (2026-07-26)")

    # generating a character who already has a locked master, instead of deriving
    canon = {p.stem.replace('_canon', '').lower() for p in (project / "canon").glob("*_canon.png")}
    if canon & named and not (shot.get("init") or shot.get("parts")):
        problems.append(
            f"{shot.get('id','?')}: generates {sorted(canon & named)} from scratch although a "
            "locked master exists — render each character ALONE at full LoRA strength and "
            "composite, or two stacked LoRAs dilute both (2026-07-26: a teddy bear and a "
            "yellow labrador replaced Hank and Doug)")
    return problems


def main() -> int:
    spec_path = Path(sys.argv[1])
    spec = json.loads(spec_path.read_text())
    project = spec_path.parent
    problems = []
    for shot in spec.get("shots", []):
        problems += lint_shot(shot, project)

    if not problems:
        print(f"[spec_lint] {spec_path.name}: clean — no known mistake repeated")
        return 0
    print(f"[spec_lint] {spec_path.name}: {len(problems)} known mistake(s) about to be repeated:")
    for p in problems:
        print(f"  ✗ {p}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
