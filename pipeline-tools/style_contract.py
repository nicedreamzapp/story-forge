#!/usr/bin/env python3
"""style_contract — extract ONE locked paragraph of visual language from frames
that already earned their place, then paste it into every prompt in the project.

    python3 pipeline-tools/style_contract.py projects/circus_train
    python3 pipeline-tools/style_contract.py projects/circus_train --images a.png b.png

Why this exists (2026-08-01). "Cinematic" is the most wasted word in the prompt:
the models have seen ten million images tagged with it. What lands is measured
ingredients — "motivated warm light from frame left, 35mm grain, lifted blacks,
shallow depth of field". The usual advice is to extract those from real cinema
stills. We extract them from OUR OWN approved frames instead, because the repo's
first rule is to build off what is already known to work: a still that survived
the beat gate, the identity gate and Matt's eye is a stronger source of truth
about what this film looks like than somebody else's movie.

By default it reads the LOCKED stills whose clip is already in the cut — proven
frames only, never a candidate or a rejected take (rule 13).

Everything is local: Qwen3-VL through film_qc.vl_ask for the per-frame reading,
gemma :9420 for the synthesis. And it asks forge_guard for room first, because
the VL judge is ~18GB and this is exactly the kind of job that used to load on
top of a render (see CLAUDE.md rule 25).
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

SF = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SF / "pipeline-tools"))
sys.path.insert(0, str(SF))

GEMMA = "http://127.0.0.1:9420/v1/chat/completions"

# One question, answered the same way for every frame, so the answers can be
# compared and merged instead of wandering off into description.
READ_FRAME = (
    "You are a cinematographer reading one frame of a finished film. Do NOT "
    "describe the story, the characters, or what is happening. Report only the "
    "photographic parameters, as short labelled lines:\n"
    "LENS: apparent focal length and depth of field.\n"
    "LIGHT: direction, hardness, and apparent source of the key light.\n"
    "PALETTE: the three or four colours that actually dominate the frame.\n"
    "CONTRAST: are the blacks crushed or lifted, are the highlights clipped.\n"
    "TEXTURE: grain, softness, haze, atmosphere in the air.\n"
    "TIME: time of day and weather the light implies."
)

SYNTHESISE = (
    "Below are cinematography readings of several frames from ONE film. Write a "
    "SINGLE paragraph, 60 to 90 words, naming only the photographic qualities "
    "they share — lens feel, light direction and quality, palette, contrast, "
    "grain and atmosphere. It will be pasted verbatim into every image prompt "
    "for this film, so write it as a description of the look, not as advice, "
    "and never mention frames, films, characters, or the word cinematic. Where "
    "the readings disagree, keep what most of them share and drop the rest.\n\n"
)


def approved_stills(proj: Path, limit: int) -> list:
    """Locked stills whose clip made the cut. A still that never became a kept
    clip is not proof of anything (rule 13: approved work is the only work)."""
    out = []
    for lock in sorted((proj / "stills").glob("LOCKED_*.png")):
        sid = lock.stem.replace("LOCKED_", "")
        if list((proj / "clips").glob(f"{sid}*_final.mp4")) or (proj / "clips" / f"{sid}.mp4").is_file():
            out.append(lock)
    return out[:limit]


def gemma(prompt: str, max_tokens: int = 2500) -> str:
    body = json.dumps({
        # :9420 404s when handed two system messages — one only (see the agent
        # memory note mlx-server-9420-single-system-message).
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens, "temperature": 0.3,
    }).encode()
    req = urllib.request.Request(GEMMA, data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        msg = json.loads(r.read())["choices"][0]["message"]
    # gemma-4 on :9420 is a reasoning model: it emits `reasoning` first and only
    # then `content`. Ask for too few tokens and the answer never arrives — the
    # response is a thought with no reply and `content` is simply absent.
    text = (msg.get("content") or "").strip()
    if not text:
        raise RuntimeError(
            "gemma returned reasoning but no answer — raise max_tokens. Got: "
            + (msg.get("reasoning") or "")[:200])
    return text


def merge_readings(readings: list) -> str:
    """Assemble the contract from the readings with no model in the loop.

    Not as fluent as a written paragraph, but it always answers, it is identical
    every run, and it can only contain things the frames actually said — which
    for a document that gets pasted verbatim into every prompt is the property
    that matters most. It reports how many frames back each field, so an outlier
    (an interior frame among golden-hour exteriors) is visible rather than
    averaged away.
    """
    fields = ("LENS", "LIGHT", "PALETTE", "CONTRAST", "TEXTURE", "TIME")
    got = {f: [] for f in fields}
    for r in readings:
        for line in r.splitlines():
            for f in fields:
                if line.strip().upper().startswith(f):
                    got[f].append(line.split(":", 1)[-1].strip().rstrip("."))
    n = len(readings)
    out = []
    for f in fields:
        vals = got[f]
        if not vals:
            continue
        # the most common phrasing, plus how many frames agreed on that field
        best = max(set(vals), key=vals.count)
        out.append(f"{f.title()}: {best} [{vals.count(best)}/{n} frames]")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--images", nargs="*", default=None,
                    help="explicit frames to read instead of the approved stills")
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--reread", action="store_true",
                    help="look at the frames again instead of reusing banked readings")
    ap.add_argument("--mem-timeout", type=float, default=3600,
                    help="how long to wait for room before giving up")
    args = ap.parse_args()

    proj = Path(args.project).resolve()
    frames = [Path(p).resolve() for p in args.images] if args.images \
        else approved_stills(proj, args.limit)
    frames = [f for f in frames if f.is_file()]
    if not frames:
        print("no approved locked stills found — nothing proven to read a style from")
        return 2
    print(f"[style] reading {len(frames)} approved frame(s): "
          f"{', '.join(f.stem.replace('LOCKED_', '') for f in frames)}", flush=True)

    # Reuse banked readings rather than paying for the GPU twice.
    cache = proj / "canon" / ".style_readings.json"
    readings = []
    if cache.is_file() and not args.reread:
        try:
            d = json.loads(cache.read_text())
            if d.get("frames") == [f.name for f in frames]:
                readings = d["readings"]
                print(f"[style] reusing {len(readings)} banked reading(s) — "
                      "pass --reread to look at the frames again", flush=True)
        except Exception:                                          # noqa: BLE001
            readings = []

    # ASK FOR THE ROOM. The VL judge is ~18GB and a render may be mid-flight;
    # loading on top of one is the whole reason this box froze (rule 25). No
    # lease is taken at all when the readings are already banked.
    from contextlib import nullcontext
    lease = nullcontext()
    if not readings:
        try:
            sys.path.insert(0, str(Path.home() / "SongForgeM5"))
            from mem_client import reserve
            lease = reserve("storyforge-vl_qc style-contract", 22,
                            timeout=args.mem_timeout, ttl=3600)
        except Exception as e:                                    # noqa: BLE001
            print(f"[style] mem lease unavailable ({type(e).__name__}) — running unleased")

    if not readings:
        with lease:
            from film_qc import vl_ask, _state, PE_URL, unload_vl
            try:
                import requests
                _state["use_server"] = requests.get(f"{PE_URL}/status", timeout=3).json().get("loaded", False)
            except Exception:
                _state["use_server"] = False
            print(f"[style] eyes: {'server :8181' if _state['use_server'] else 'in-process VL'}",
                  flush=True)

            for f in frames:
                try:
                    r = vl_ask(str(f), READ_FRAME)
                except Exception as e:                            # noqa: BLE001
                    print(f"[style] {f.name}: UNREADABLE ({type(e).__name__}) — skipped")
                    continue
                print(f"[style] {f.stem.replace('LOCKED_', '')}: read", flush=True)
                readings.append(f"--- {f.stem.replace('LOCKED_', '')}\n{r.strip()}")
            # Hand the GPU back before asking gemma — same symmetry rule
            # forge-shot uses around a render.
            unload_vl()

    if not readings:
        print("every frame was unreadable — no contract written (UNCHECKED, not a pass)")
        return 2

    # BANK THE EXPENSIVE HALF BEFORE THE CHEAP HALF CAN FAIL (2026-08-01). The
    # first run waited 440s for memory, loaded the VL judge and read all eight
    # frames — then died in the one-line synthesis because gemma spent its token
    # budget reasoning, and every bit of that work was gone. Readings go to disk
    # the moment they exist; a re-run reuses them and never touches the GPU.
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"frames": [f.name for f in frames],
                                 "readings": readings}, indent=1))
    print(f"[style] readings banked → {cache.name}", flush=True)

    # gemma writes the paragraph when it can. It is a reasoning model and this is
    # a long prompt, so it sometimes spends the whole budget thinking and returns
    # no answer at all (three times on 2026-08-01). The readings are already the
    # expensive, non-reproducible part; the merge must never be what loses them.
    try:
        paragraph = gemma(SYNTHESISE + "\n\n".join(readings))
    except Exception as e:                                        # noqa: BLE001
        print(f"[style] gemma could not write the merge ({type(e).__name__}) — "
              "falling back to the deterministic one", flush=True)
        paragraph = merge_readings(readings)

    out = proj / "canon" / "STYLE_CONTRACT.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "# Style contract\n\n"
        "Paste this paragraph verbatim into every image and animate prompt for "
        "this project. It was measured from the frames listed below — frames that "
        "already passed the gates and made the cut — not written from imagination.\n\n"
        f"## The contract\n\n{paragraph}\n\n"
        f"## Read from\n\n" + "\n".join(f"- {f.name}" for f in frames) + "\n\n"
        "## Raw readings\n\n```\n" + "\n\n".join(readings) + "\n```\n"
    )
    print(f"\n[style] contract written → {out}\n")
    print(paragraph)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
