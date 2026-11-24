#!/usr/bin/env python3
"""cliche_gate.py — stop the same film from being made again. Plain code, no model.

Matt 2026-11-24: every film looks the same (robot hands, red alarm beacons, empty corridors, vault doors,
padlocks, a desk lamp in a dark room, rain on windows, mist, dust in light beams, night city from above,
server rooms, silhouettes, moonlight, embers, "slow push" shots where nothing happens, one shared house
style, metaphors instead of the real subject, "nobody in the room"). This gate runs on a project's shot
list BEFORE any still or render and fails the run when it finds them.

    python3 pipeline-tools/cliche_gate.py projects/<p>                  # check (exit 0 pass, 1 fail, 2 could not run)
    python3 pipeline-tools/cliche_gate.py projects/<p> --prompts x.json # also check any prompts JSON
    python3 pipeline-tools/cliche_gate.py --record projects/<p>         # finished film: add its scenes to the ledger
    python3 pipeline-tools/cliche_gate.py --seed                        # rebuild the ledger from every project

What it checks
  1. projects/<p>/LOOK.md exists, is written (no TEMPLATE line), and does not carry the old house style.
     Each film writes its own look from references Matt gives; there is no shared look any more.
  2. Every still/motion prompt (work/shots.py SHOTS, shots.py, *shots*.json, --prompts files) for the
     banned motifs below (with synonyms), "nobody in the room" style emptiness, metaphors standing in
     for the real subject, and the old house style phrases.
  3. Every motion prompt names something HAPPENING, not only a camera move plus drifting ambience.
  4. No shot repeats a main scene a past film already used (_shared/used_scenes.jsonl).

Allowing something Matt asked for: projects/<p>/ALLOW.md, one line per motif, with his reason:
    - robot: Matt 11/30 "this one is about my robot arm"
or per shot, an allow=[...] field in shots.py / "allow": [...] in shots.json. Keys are the motif names
printed in the report (robot, alarm, corridor, ...; repeat:<project>/<shot> to reuse a past scene).
The house style can not be allowed: write the film's own LOOK.md.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "_shared" / "used_scenes.jsonl"
TEMPLATE_MARK = "<!-- TEMPLATE:"

# ---- banned motifs: key -> (plain name, regexes) -------------------------------------------------------------
MOTIFS: dict[str, tuple[str, list[str]]] = {
    "robot": ("robots / robot hands", [r"\brobot(ic|s)?\b", r"\bandroids?\b", r"\bcyborgs?\b", r"\bdroids?\b",
              r"\bautomatons?\b", r"\bmechanical (hand|arm|fingers?)\b", r"\bhumanoid\b"]),
    "alarm": ("red sirens / alarm beacons", [r"\bsirens?\b", r"\balarm\b", r"\b(warning|emergency|rotating|flashing) (light|beacon|lamp)s?\b",
              r"\bbeacons?\b", r"\bred (strobe|flashing|rotating) "]),
    "corridor": ("empty hallways / corridors", [r"\bhallways?\b", r"\bcorridors?\b", r"\bpassageways?\b", r"\bhall of doors\b"]),
    "vault": ("vault / safe doors", [r"\bvaults?\b", r"\bsafe door\b", r"\bbank safe\b", r"\bstrongroom\b", r"\bsafe deposit\b"]),
    "lock": ("padlocks / keys / fingerprints", [r"\bpadlock", r"\bdeadbolt", r"\bkeyholes?\b", r"\bkey ?rings?\b", r"\bkey ?cards?\b",
             r"\bfingerprints?\b", r"\bthumbprints?\b", r"\b(door|combination|iron|old|steel|brass) locks?\b",
             r"\b(brass|iron|metal|silver|gold(en)?|old|small|skeleton|house|door|car|glowing) keys?\b",
             r"\bkeys? (rests?|resting|hangs?|hanging|turns?|turning|in the (lock|door))\b"]),
    "lamp": ("a single desk lamp in a dark room", [r"\bdesk ?lamps?\b", r"\bbanker'?s lamp\b", r"\breading lamp\b",
             r"\b(single|lone|one|old) (\w+ )?lamp\b", r"\b(only|single|one|lone) (light|light source)\b",
             r"\blamp is the only\b", r"\bsingle bulb\b", r"\bbare bulb\b"]),
    "rain_window": ("rain on windows", [r"\brain\w*\b.{0,40}\b(window|glass|windshield|pane)s?\b",
                    r"\b(window|glass|pane)s?\b.{0,30}\brain", r"\braindrops?\b", r"\brain-?streaked\b"]),
    "haze": ("mist / fog / haze", [r"\bmist(y|s)?\b", r"\bfog(gy|s)?\b", r"\bhaz(e|y)\b", r"\bvolumetric\b", r"\batmospheric smoke\b"]),
    "dust_beam": ("dust in light beams / god rays", [r"\bdust\b.{0,40}\b(light|beam|air|drift|float|glow|motes?)", r"\bdust motes?\b",
                  r"\b(light|sun) ?beams?\b", r"\bshafts? of (light|sun)", r"\bgod ?rays\b", r"\blight rays?\b"]),
    "night_city": ("night city from above", [r"\bnight city\b", r"\bcity at night\b", r"\bcity lights\b", r"\bskyline\b",
                   r"\b(aerial|from (high )?above|overhead|bird'?s?[- ]eye)\b.{0,80}\b(city|town|streets|rooftops)\b",
                   r"\b(city|town|streets|rooftops)\b.{0,60}\bfrom (high )?above\b"]),
    "screens": ("server rooms / glowing monitors", [r"\bserver (room|rack|farm)s?\b", r"\bdata ?cent(er|re)s?\b",
                r"\bglowing (computer |crt )?(monitor|screen|display)s?\b", r"\b(monitor|screen) (glow|light)\b",
                r"\bwall of (screens|monitors)\b", r"\b(monitor|screen)s? glow(s|ing)?\b", r"\bblinking (leds|lights) on racks\b"]),
    "silhouette": ("silhouettes", [r"\bsilhouett"]),
    "moonlight": ("moonlight", [r"\bmoon(light|lit|beams?)?\b"]),
    "embers": ("floating embers / sparks", [r"\bembers?\b", r"\b(floating|drifting) sparks\b", r"\bsparks (float|drift|rise)"]),
    "nobody": ("nobody in the room / frame", [r"\bnobody\b", r"\bno ?one (is )?(in|visible|around|there)\b", r"\bno (people|person|humans?|figures?)\b",
               r"\b(empty|deserted|abandoned|unoccupied) (room|hallway|corridor|office|street|space|house|building|lab|warehouse)\b",
               r"\bdark empty\b", r"\bempty dark\b", r"\bdevoid of (people|life)\b"]),
    "metaphor": ("a metaphor instead of the real subject", [r"\bmetaphor", r"\bsymboli[sz]", r"\brepresent(s|ing)\b",
                 r"\b(standing|stands|rises|looms)\b.{0,40}\blike an? (gate|door|doorway|portal|monument|monolith|wall)\b",
                 r"\bgiant (glowing |floating )?(checkbox|cursor|arrow|icon|button|padlock|key|lock)\b",
                 r"\b(cursor|checkbox|icon|button|arrow)s?\b.{0,30}\bfloating in (the )?(air|space|darkness)\b",
                 r"\briver of\b", r"\bportal\b"]),
}
HOUSE_STYLE = ("the old shared house style", [r"\b35 ?mm\b", r"\banamorphic\b", r"\bteal[- ](and[- ])?(amber|orange)\b",
               r"\bquiet (modern )?thriller\b", r"\bone light source\b", r"\bsingle motivated key light\b",
               r"\bonly light source\b"])
MOTIF_RE = {k: [re.compile(p, re.I) for p in ps] for k, (_, ps) in MOTIFS.items()}
HOUSE_RE = [re.compile(p, re.I) for p in HOUSE_STYLE[1]]

# ---- motion must have an action ------------------------------------------------------------------------------
CAMERA_RE = re.compile(r"\b(camera|push(es|ing)?( in| forward)?|pull(s|ing)? (back|out)|dolly|dollies|pan(s|ning)?|tilt(s|ing)?|"
                       r"orbit(s|ing)?|crane|zoom(s|ing)?|track(s|ing)? (in|out|left|right|alongside|past)|locked[- ]off|static|"
                       r"handheld|truck(s|ing)?|arc(s|ing)? around|slow (push|move|drift)|drift(s|ing)? (in|forward))\b", re.I)
AMBIENT_RE = re.compile(r"\b(drift(s|ing)?|pulse(s|d)?|pulsing|flicker(s|ing)?|glow(s|ing)?|twinkl(e|es|ing)|sway(s|ing)?|"
                        r"breathe(s)?|shimmer(s|ing)?|roll(s|ing)? (across|in|low)|sweep(s|ing)?|keeps? (its|their) (exact )?shape|"
                        r"stays? (perfectly )?(still|the same|empty)|nothing (else )?(moves|appears|happens)|"
                        r"no (camera )?movement|no hands|no people|swell(s|ing)?|fades?|brightens?|dims?|"
                        r"light (moves|spreads|shifts)|stays? completely|remains? (still|motionless))\b", re.I)
WORD_RE = re.compile(r"[a-z]+")
STOP = set("""a an the and or of in on at to from with into onto over under through toward towards by for as is are its it
their his her this that these those very slowly slow softly soft gently gentle little bit small large tiny huge giant
each every one two three no not nothing only just still exact shape frame shot seen side medium distance close wide
extreme left right above below behind far near background foreground light lit lighting key fill rim warm cool cold
dark darkness bright glowing glow soft hard deep fine film grain photorealistic cinematic highly detailed real scale
color colour grade lens camera static push dolly pan move moves moving movement locked off stays keeps""".split())

SHOT_TEXT_FIELDS = ("still", "prompt", "still_prompt", "image_prompt", "first_frame", "motion", "i2v", "motion_prompt",
                    "video_prompt", "i2v_prompt")
MOTION_FIELDS = ("motion", "i2v", "motion_prompt", "video_prompt", "i2v_prompt")


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip()


# ---- reading a project's shots --------------------------------------------------------------------------------
def _shots_from_py(p: Path) -> list[dict]:
    ns = runpy.run_path(str(p), run_name="cliche_gate_read")
    shots = ns.get("SHOTS") or {}
    out = []
    items = shots.items() if isinstance(shots, dict) else enumerate(shots)
    for k, v in items:
        if isinstance(v, dict):
            out.append(dict(v, id=str(v.get("id", k)), _src=str(p)))
    return out


def _shots_from_json(p: Path) -> list[dict]:
    d = json.loads(p.read_text())
    lst = d.get("shots", d.get("SHOTS", d)) if isinstance(d, dict) else d
    if isinstance(lst, dict):
        lst = [dict(v, id=str(v.get("id", k))) for k, v in lst.items() if isinstance(v, dict)]
    out = []
    for i, v in enumerate(lst if isinstance(lst, list) else []):
        if isinstance(v, dict):
            out.append(dict(v, id=str(v.get("id", v.get("name", i))), _src=str(p)))
    return out


def shot_files(proj: Path) -> list[Path]:
    fs = [proj / "work" / "shots.py", proj / "shots.py"]
    fs += sorted(proj.glob("*shots*.json")) + sorted(proj.glob("work/*shots*.json"))
    return [f for f in fs if f.is_file()]


def load_shots(proj: Path, extra: list[Path] = ()) -> tuple[list[dict], list[str]]:
    shots, errs = [], []
    for f in list(shot_files(proj)) + [Path(x) for x in extra]:
        try:
            shots += _shots_from_py(f) if f.suffix == ".py" else _shots_from_json(f)
        except Exception as e:  # a shot list we can not read is a failure, never a pass
            errs.append(f"could not read {f.name}: {type(e).__name__}: {str(e)[:120]}")
    return [s for s in shots if any(isinstance(s.get(k), str) and s.get(k).strip() for k in SHOT_TEXT_FIELDS)], errs


def project_allows(proj: Path) -> set[str]:
    f = proj / "ALLOW.md"
    out = set()
    if f.is_file():
        for line in f.read_text().splitlines():
            m = re.match(r"\s*[-*]\s+([a-z_]+(?::[\w./-]+)?)\s*:\s*\S", line)
            if m and (m.group(1) in MOTIFS or m.group(1) in ("camera_only", "repeat") or m.group(1).startswith("repeat:")):
                out.add(m.group(1))
    return out


# ---- checks ---------------------------------------------------------------------------------------------------
def find_motifs(text: str) -> dict[str, str]:
    hits = {}
    for k, regs in MOTIF_RE.items():
        for r in regs:
            m = r.search(text)
            if m:
                hits[k] = m.group(0)
                break
    return hits


def house_hits(text: str) -> list[str]:
    return [m.group(0) for r in HOUSE_RE for m in [r.search(text)] if m]


ACTION_VERBS = """tear tip set fold seal rip shove toss swap fit attach detach unbox walk step run reach pick lift put place open close turn twist press type click tap swipe scroll write draw pour fill load screw unscrew grip give take grab carry drop throw catch cut slice mix stir inhale exhale vape glance nod smile laugh speak talk say sit stand kneel lean climb jump dance ride drive plug unplug install assemble build fix clean wipe weld solder stack sort wash cook eat drink dig harvest swing chase pet hug shake nudge slide spin flip insert remove connect charge scan select solve enter leave exit arrive follow bounce kick wrap unwrap peel squeeze tighten loosen hold try grind""".split()
# a verb counts only in a doing form (picks, walking, opened), so nouns like "hand" or "light" never pass
ACTION_RE = re.compile(r"\b(?:" + "|".join(ACTION_VERBS) + r")(?:s|es|ed|d|ing|ping|ning|ting|ped|ned)\b|\b(?:carries|carrying|tries|trying|holds|holding)\b", re.I)


# "he tears", "Matt lifts", "the woman ...s": a person as the subject of a verb is something happening
PERSON_DOES_RE = re.compile(r"\b(he|she|they|we|i|matt|man|woman|men|women|person|people|kid|child|worker|customer|"
                            r"dog|cat|horse|bird)\s+(\w+ly\s+)?(?!is\b|are\b|was\b|stays?\b|remains?\b|keeps?\b)\w+(s|ed)\b", re.I)


def motion_has_action(motion: str) -> bool:
    """True when some clause of the motion names a subject doing something, not just a camera move or
    ambience (glow pulses, dust drifts, mist rolls, it keeps its shape)."""
    for clause in re.split(r"[,.;]|\bwhile\b|\bas\b", motion):
        rest = AMBIENT_RE.sub(" ", CAMERA_RE.sub(" ", clause))
        if ACTION_RE.search(rest) or PERSON_DOES_RE.search(rest):
            return True
    return False


def signature(text: str) -> set[str]:
    t = text.lower()
    for r in HOUSE_RE:
        t = r.sub(" ", t)
    return {w for w in WORD_RE.findall(t) if w not in STOP and len(w) > 3}


def same_scene(a: set, b: set) -> float:
    """Share of the smaller prompt's content words found in the other (0 below 4 shared words), so a short
    rewording of a past scene still counts as that scene."""
    i = len(a & b)
    return i / min(len(a), len(b)) if i >= 4 else 0.0


def read_ledger() -> list[dict]:
    if not LEDGER.is_file():
        return []
    out = []
    for line in LEDGER.read_text().splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


REPEAT_AT = 0.6    # share of content words in common that counts as "the same scene again"


def check(proj: Path, extra: list[Path] = ()) -> tuple[bool, list[str]]:
    proj = proj.resolve()
    lines, fail = [], False
    # 1. the film's own look
    look = proj / "LOOK.md"
    if not look.is_file():
        fail = True
        lines.append("LOOK: no LOOK.md. Write this film's own look from the references Matt gave "
                     "(see _templates/film/LOOK.md); there is no shared house style any more.")
    else:
        lt = look.read_text()
        if TEMPLATE_MARK in lt:
            fail = True
            lines.append("LOOK: LOOK.md is still the template, write the real one.")
        hh = house_hits(lt)
        if hh:
            fail = True
            lines.append(f"LOOK: LOOK.md carries the old house style ({', '.join(hh)}). Each film gets its own look.")
    shots, errs = load_shots(proj, extra)
    for e in errs:
        fail = True
        lines.append("READ: " + e)
    if not shots:
        return False, lines + ["SHOTS: no shot prompts found (work/shots.py SHOTS, shots.py, *shots*.json or --prompts). "
                               "Nothing checked is never a pass."]
    allow_p = project_allows(proj)
    ledger = [e for e in read_ledger() if e.get("project") != proj.name]
    bad_shots = 0
    for s in shots:
        sid = s["id"]
        allow = allow_p | set(s.get("allow") or [])
        probs = []
        pos = " ".join(norm(s[k]) for k in SHOT_TEXT_FIELDS if isinstance(s.get(k), str))
        for k, word in find_motifs(pos).items():
            if k not in allow:
                probs.append(f"{k}: {MOTIFS[k][0]} (found \"{word}\")")
        hh = house_hits(pos)
        if hh:
            probs.append(f"house_style: the old shared look in the prompt ({', '.join(hh)}); use this film's LOOK.md")
        motion = " ".join(norm(s[k]) for k in MOTION_FIELDS if isinstance(s.get(k), str))
        if motion and not motion_has_action(motion) and "camera_only" not in allow:
            probs.append(f"camera_only: the motion is only a camera move or drifting ambience, nothing happens "
                         f"(\"{motion[:90]}\"). Say what the person or subject DOES")
        still = norm(s.get("still") or s.get("prompt") or s.get("still_prompt") or s.get("image_prompt") or "")
        sig = signature(still)
        best = max(((same_scene(sig, set(e.get("signature", []))), e) for e in ledger), default=(0, None), key=lambda x: x[0])
        if best[1] is not None and best[0] >= REPEAT_AT:
            key = f"repeat:{best[1]['project']}/{best[1]['shot']}"
            if key not in allow and "repeat" not in allow:
                probs.append(f"repeat: the same scene as {best[1]['project']} shot {best[1]['shot']} "
                             f"(\"{best[1].get('name') or best[1].get('text', '')[:70]}\", {best[0]:.0%} the same words)")
        if probs:
            bad_shots += 1
            fail = True
            name = s.get("name") or s.get("beat") or ""
            lines.append(f"SHOT {sid}" + (f" ({str(name)[:60]})" if name else "") + ":")
            lines += [f"    - {p}" for p in probs]
    lines.append(f"{len(shots)} shots checked, {bad_shots} with problems.")
    return not fail, lines


# ---- ledger ---------------------------------------------------------------------------------------------------
def entries_for(proj: Path) -> list[dict]:
    shots, _ = load_shots(proj)
    out, seen = [], set()
    for s in shots:
        still = norm(s.get("still") or s.get("prompt") or s.get("still_prompt") or s.get("image_prompt") or "")
        if not still:
            continue
        sig = sorted(signature(still))
        key = " ".join(sig)
        if key in seen:
            continue
        seen.add(key)
        out.append({"project": proj.name, "shot": s["id"], "name": str(s.get("name") or s.get("beat") or "")[:100],
                    "motifs": sorted(find_motifs(still + " " + norm(s.get("motion") or ""))),
                    "text": still[:240], "signature": sig,
                    "recorded": _dt.date.today().isoformat()})
    return out


def record(projs: list[Path]) -> int:
    names = {p.resolve().name for p in projs}
    keep = [e for e in read_ledger() if e.get("project") not in names]
    new = []
    for p in projs:
        new += entries_for(p.resolve())
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "w") as f:
        for e in keep + new:
            f.write(json.dumps(e) + "\n")
    print(f"[cliche_gate] ledger {LEDGER.relative_to(ROOT)}: {len(new)} scenes from {', '.join(sorted(names))}; "
          f"{len(keep) + len(new)} scenes total")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Reject the same old shots before any still or render.")
    ap.add_argument("project", nargs="?", help="projects/<p>")
    ap.add_argument("--prompts", action="append", default=[], help="extra prompts JSON to check (repeatable)")
    ap.add_argument("--record", action="store_true", help="add this finished film's scenes to the used-scenes ledger")
    ap.add_argument("--seed", action="store_true", help="rebuild the ledger from every project under projects/")
    a = ap.parse_args()
    if a.seed:
        return record([p for p in sorted((ROOT / "projects").iterdir()) if p.is_dir() and shot_files(p)])
    if not a.project:
        ap.error("give a project, or --seed")
    proj = Path(a.project)
    if not proj.is_dir():
        proj = ROOT / "projects" / a.project
    if not proj.is_dir():
        print(f"[cliche_gate] no project {a.project}", file=sys.stderr)
        return 2
    if a.record:
        return record([proj])
    ok, lines = check(proj, [Path(x) for x in a.prompts])
    print(f"[cliche_gate] {proj.name}: {'PASS' if ok else 'FAIL'}")
    for l in lines:
        print("  " + l)
    if not ok:
        print("  Fix the shots (show the real subject doing something, in this film's own look), or add the motif to "
              "ALLOW.md with Matt's words if he asked for it. Nothing is drawn or rendered until this passes.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
