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

CHARACTER_WORDS = re.compile(
    r"\b(bear|dog|bloodhound|hound|elephant|lion|giraffe|monkey|monkeys|"
    r"parrot|parrots|hank|doug|ellie)\b", re.I)

# ── ADVISORIES: write it so a camera can prove it (2026-08-01) ───────────────
# The rules above are BLOCKS: mistakes that have already cost a night. These are
# ADVICE, printed with ⚠ and deliberately never affecting the exit code, because
# forge-director blocks a shot on any "✗ <id>:" line and a new hard rule would
# stop a film mid-run over a wording preference.
#
# Both come from the Seedance 2.5 prompting guide (ByteDance, read 2026-08-01).
# The model is cloud and we are 100% local, so none of it is usable directly —
# but two of its rules are the same lessons this file already learned the
# expensive way, stated more usefully:
#
#   "Give each stage ONE primary state change, and state what should be directly
#    visible at the end of that stage."
#   "Emotion words leave room for interpretation. For stable control, add
#    directly visible cues — eye movement, brow tension, gaze, hand movement."
#
# That is rule 14 ("the picture must show the beat") and the prescribe() loop,
# except written BEFORE the render instead of after the fourth rejection.
# Measured cost of not doing it: r2_lion_out, 2026-08-01 — four attempts, every
# window probe FAIL, and the prescription the judge finally wrote was pure
# observable cue ("front paws clearly mid-stride, one front leg lifted, the
# other just touching the ground"). Nothing stopped that from being the beat in
# the first place.
ABSTRACT = re.compile(r"\b(free|freedom|happy|happily|joyful|joy|sad|angry|tense|"
                      r"menacing|peaceful|calm|proud|curious|excited|nervous|"
                      r"triumphant|majestic|dramatic|epic|beautiful|wonder|"
                      r"relief|relieved|content|serene)\b", re.I)
# Anything a lens can actually resolve: a body part, or a word that pins its state.
OBSERVABLE = re.compile(r"\b(paws?|legs?|heads?|ears?|eyes?|mouths?|jaws?|tails?|"
                        r"necks?|shoulders?|knees?|hooves?|hoof|wings?|nostrils?|"
                        r"brows?|trunks?|muzzles?|backs?|chests?|"
                        r"lifted|raised|lowered|bent|stretched|planted|flat|"
                        r"open|shut|closed|mid-stride|mid-air|leaning|turned|"
                        r"tilted|pressed|braced|curled|spread|extended)\b", re.I)


# A clip_beat must not require a CAUSAL physical effect (2026-08-02). Frozen
# rule 6: the renderer does ambient motion — drift, sway, breathing, haze — not
# collisions and not cause-and-effect. t2_lion's clip_beat asked for "dust
# lifting off the wood WITH EACH BREATH", so the judge prescribed breath-synced
# dust puffs three times running, the renderer produced ambient drift three times
# running, and four clips died on a requirement nothing in this pipeline can
# satisfy. Ask for the state, let the causation be implied.
CAUSAL = re.compile(r"\b(with each|in sync with|synchron\w+|as (he|she|it|they) "
                    r"(breath\w*|steps?|moves?|pushes|pulls)|every time|each time|"
                    r"in time with|caused by|sending \w+ (flying|up|out))\b", re.I)


def advise_shot(shot: dict) -> list:
    """Non-blocking advice. Same shape as lint_shot, printed with ⚠."""
    notes = []
    sid = shot.get("id", "?")

    for field in ("beat", "animate", "clip_beat"):
        text = shot.get(field) or ""
        if not isinstance(text, str) or not text:
            continue
        m = ABSTRACT.search(text)
        if m and not OBSERVABLE.search(text):
            notes.append(
                f"{sid}: [{field}] '{m.group(0)}' is a feeling, not a picture, and nothing "
                "in this field names a body part or its state — the gate has to vote on "
                "something a lens can resolve. Say which paw, ear, eye, neck or tail is "
                "where (r2_lion_out burned 4 attempts on this and the judge's own "
                "prescription was 'front paws mid-stride, one front leg lifted')")

    for field in ("clip_beat", "animate"):
        text = shot.get(field) or ""
        m = CAUSAL.search(text) if isinstance(text, str) else None
        if m:
            notes.append(
                f"{sid}: [{field}] '{m.group(0)}' asks for cause-and-effect, and the "
                "renderer only does ambient motion (frozen rule 6). The judge will keep "
                "prescribing the synced effect and the renderer will keep producing drift "
                "(t2_lion: 4 clips died on 'dust lifting with each breath'). Describe the "
                "state — dust hanging in the air — and let the cause be implied")

    # A shot that animates needs the END STATE spelled out, because that is what
    # the clip gets judged against — a frame cannot depict a change (rule 14).
    beat = (shot.get("beat") or "").strip()
    clip_beat = (shot.get("clip_beat") or shot.get("end_state") or "").strip()
    if shot.get("animate") and not clip_beat:
        notes.append(
            f"{sid}: animates but declares no `clip_beat` / `end_state` — the clip judge "
            "falls back to the still's beat, which describes the BEFORE. Write the state "
            "that is visible when the motion finishes and judge against that")
    elif shot.get("animate") and clip_beat == beat:
        # A COPIED clip_beat is not an end state (2026-08-01). Found while checking
        # whether the advisory above would have caught r2_lion_out — it would not,
        # its beat already said "mid-stride". The actual defect is subtler and
        # every open beat in circus_train has it: clip_beat is a verbatim copy of
        # the still's beat, so the clip judge is asked to find the STILL's frozen
        # instant somewhere in five seconds of motion. r2_lion_out's beat is "mid-
        # stride" while its animate is "walks slowly and steadily" — the lion is
        # mid-stride for a fraction of each step, so four window probes at fixed
        # times all missed it and the shot was blocked for a story failure it did
        # not have. The clip's beat has to describe what is true for the DURATION,
        # not the pose the still was locked on.
        notes.append(
            f"{sid}: `clip_beat` is a verbatim copy of `beat`, so the clip is judged "
            "against a frozen instant instead of what the motion leaves true. If the "
            "still is a pose the motion only passes THROUGH, the probes will miss it "
            "(r2_lion_out: beat 'mid-stride', animate 'walks slowly and steadily' — "
            "4 attempts, every probe FAIL, blocked as a story failure it did not have). "
            "Write the clip_beat as the state that holds across the whole clip")
    return notes


def lint_shot(shot: dict, project: Path) -> list:
    problems = []
    for field, pattern, why in RULES:
        text = shot.get(field) or ""
        if isinstance(text, str) and (m := pattern.search(text)):
            problems.append(f"{shot.get('id','?')}: [{field}] '{m.group(0)}' — {why}")

    # a shot with named characters must declare who to check against canon
    beat = (shot.get("beat") or "") + " " + (shot.get("prompt") or "")
    named = set(w.lower() for w in CHARACTER_WORDS.findall(beat))
    # `_identity_waived` (2026-08-02): a shot may be framed so tightly that the
    # features the identity gate measures — head shape, ear structure, markings —
    # are not in the frame at all. t2_lion is a muzzle jammed into a plank crack:
    # it passed the beat gate 3/3 and was failed on "different head shape and ear
    # structure" four times, for a head the shot deliberately does not show. A
    # gate that cannot see its subject returns DRIFT, not UNCHECKED, and blocks a
    # correct shot forever. Waiving it requires a written reason so the waiver is
    # an argument, never a shrug.
    if named and shot.get("_identity_waived"):
        named = set()
    if named and not shot.get("identity") and not shot.get("_no_characters"):
        problems.append(
            f"{shot.get('id','?')}: mentions {sorted(named)} but declares no identity check — "
            "every named character is checked against its locked master, or a dog that is "
            "not Doug walks straight through (2026-07-26)")

    # a shot in a locked location must be held to that location
    sets = list((project / "canon").glob("*_canon.png"))
    set_names = [p.stem.replace("_canon", "") for p in sets]
    place = re.search(r"\b(boxcar|train|wagon|carriage|door)\b", beat, re.I)
    if place and set_names and not shot.get("set") and not shot.get("_no_set"):
        problems.append(
            f"{shot.get('id','?')}: is set at the {place.group(0)} but declares no `set` — "
            "the door Hank pushed and the door that opened were different cars entirely "
            "because nothing locked the set (2026-07-26)")

    # TWO STACKED LoRAs DILUTE BOTH (2026-08-01). The rule below only fires when the
    # prompt says the literal word "hank"/"doug"/"ellie" — but every prompt in this film
    # DESCRIBES them ("a big round brown bear", "a tall tan-and-orange bloodhound"), so
    # it never fired on a single two-hander and the 2026-07-26 lesson went unenforced.
    # s4_arrival stacked Hank+Doug at 0.85 each with no composite and produced exactly
    # the documented failure: a small doll-like teddy bear standing barely taller than
    # the dog, next to a canon master that is a huge heavy bear. s6_heave, the shot that
    # holds up, uses ONE LoRA at 0.9. So count the CHARACTERS, not the spelling.
    ident = shot.get("identity")
    n_chars = len(ident) if isinstance(ident, list) else (1 if ident else 0)
    n_loras = len(shot.get("loras") or [])
    if max(n_chars, n_loras) > 1 and not (shot.get("init") or shot.get("parts")):
        problems.append(
            f"{shot.get('id','?')}: puts {max(n_chars, n_loras)} characters in one frame with "
            "no `init` composite — render each ALONE at full LoRA strength and composite, "
            # NEVER name another shot's id in a problem message: forge-director decides
            # what to block with a substring test over this whole stdout, so an id quoted
            # as an EXAMPLE blocks that innocent shot (2026-08-01 — this message cited
            # s4_arrival and got s4_arrival blocked while it was perfectly clean).
            "because stacked LoRAs dilute every character in the frame (2026-07-26: a teddy "
            "bear and a yellow labrador replaced Hank and Doug; 2026-08-01: a doll-sized "
            "bear standing shorter than the dog)")

    # generating a character who already has a locked master, instead of deriving
    #
    # MATCH THE DESCRIPTION, NOT THE NAME (2026-08-02). This rule intersected the
    # prompt against canon FILE STEMS — hank, doug, ellie, lion, giraffe — but no
    # prompt in this film says those words. They say "a big round brown bear", "a
    # tall tan-and-orange bloodhound". So the rule never fired, and the whole of
    # the 2026-08-01 night went to it: 69 stills passed the beat gate and 64 were
    # killed by the identity gate for "different head shape and ear structure",
    # every one of them a character regenerated from scratch when a locked master
    # existed. Checked by eye afterwards — the gate was RIGHT: pale grey-taupe fur
    # against canon's reddish-brown, small low ears against large high ones. Rule
    # 10 says a LoRA locks identity but NOT colour and texture, and colour is
    # exactly what drifted. This is rule 24's spelling failure in a second place,
    # and it cost eight hours of GPU for zero clips.
    #
    # So map the WORDS A PROMPT ACTUALLY USES onto the masters they refer to.
    SPECIES = {"hank": ("bear",), "doug": ("bloodhound", "hound", "dog"),
               "ellie": ("elephant",), "lion": ("lion",), "giraffe": ("giraffe",),
               "monkey": ("monkey", "monkeys"), "parrot": ("parrot", "parrots")}
    # CHARACTERS only. The canon folder also holds SET masters (boxcar, wagon,
    # train); a set does not have to be welded from its master and flagging one
    # would block half the film, including shots with approved footage already in
    # the cut. A stem counts here only if SPECIES knows it as a character.
    canon = {p.stem.replace('_canon', '').lower()
             for p in (project / "canon").glob("*_canon.png")} & set(SPECIES)
    described = {stem for stem in canon
                 for word in SPECIES[stem]
                 if re.search(rf"\b{word}s?\b", beat, re.I)}
    named = named | described
    # Two exemptions, both rule 23's corollary in code:
    #  * a shot with footage already in the cut is never re-rendered, so flagging
    #    it only blocks it if it is ever requeued (and blocks nine shots here);
    #  * a shot whose framing excludes the character's identifying features has
    #    nothing to weld — deriving from the master cannot help a frame that
    #    contains only paws and planks.
    # "Has footage" must mean the SAME thing it means to forge-director: the
    # declared clip, or a non-trivial clip that is not a _raw or _failed corpse.
    # A bare glob called s6_heave unbuilt (its clip is s6_final_v2.mp4) and called
    # r2_lion_out built (it only has r2_lion_out_raw.mp4, a reject).
    sid = shot.get("id", "")
    declared = project / shot["clip"] if shot.get("clip") else None
    has_clip = bool(declared and declared.is_file() and declared.stat().st_size > 50_000) or \
        any(g.stat().st_size > 50_000 and not any(x in g.name for x in ("_failed", "_raw"))
            for g in (project / "clips").glob(f"{sid}*.mp4"))
    if (canon & named) and not (shot.get("init") or shot.get("parts")) \
            and not has_clip and not shot.get("_identity_waived"):
        problems.append(
            f"{shot.get('id','?')}: generates {sorted(canon & named)} from scratch although a "
            "locked master exists — render each character ALONE at full LoRA strength and "
            "composite, or two stacked LoRAs dilute both (2026-07-26: a teddy bear and a "
            "yellow labrador replaced Hank and Doug)")
    return problems


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    strict = "--strict" in sys.argv
    spec_path = Path(args[0])
    spec = json.loads(spec_path.read_text())
    project = spec_path.parent
    problems, notes = [], []
    for shot in spec.get("shots", []):
        problems += lint_shot(shot, project)
        notes += advise_shot(shot)

    # --strict promotes advice to a block. NOT the default: forge-director blocks
    # a shot on any "✗ <id>:" line, so defaulting to strict would stop a running
    # film over wording. Use it when writing a NEW spec, before any GPU time.
    if strict:
        problems += notes
        notes = []

    if problems:
        print(f"[spec_lint] {spec_path.name}: {len(problems)} known mistake(s) about to be repeated:")
        for p in problems:
            print(f"  ✗ {p}")
    else:
        print(f"[spec_lint] {spec_path.name}: clean — no known mistake repeated")

    if notes:
        print(f"[spec_lint] {len(notes)} advisory note(s) — not blocking, but this is how "
              "a shot passes on the first attempt instead of the fourth:")
        for n in notes:
            print(f"  ⚠ {n}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
