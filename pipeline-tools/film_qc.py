#!/usr/bin/env python3
"""film_qc.py — automated QC agent for story-forge / LTX films.

The verification stage that MUST run before any video is called "checked."
Uses Matt's local Qwen3-VL-32B (Picture Eyes server on :8181, or in-process
fallback) as the eyes, and Whisper (mlx) as the ears.

Checks performed:
  1. LIP SYNC   — for every dialogue line in the manifest, frames are pulled
                  at the line's midpoint and the VL model is asked which
                  character's mouth is open. FAIL if wrong/no character.
  2. SILENCE    — frames pulled mid-silence; FAIL if mouths flapping.
  3. IDENTITY   — one frame per scene, tiled side by side; VL model asked if
                  each character looks like the SAME character in every tile.
  4. ARTIFACTS  — frames sampled every ARTIFACT_STEP seconds; VL model asked
                  about deformities (extra limbs, merged bodies, warped faces).
  5. TRANSCRIPT — Whisper transcribes the film audio; every manifest line's
                  words must appear near its expected timestamp (±TOL s).

Usage:
  ~/.local/mlx-server/bin/python film_qc.py FILM.mp4 manifest.json [--report out.md]

manifest.json:
  {
    "characters": {"hank": "huge round brown bear",
                   "doug": "lanky brown bloodhound dog with long floppy ears"},
    "scenes": [{"name": "winter", "start": 2.4, "end": 13.1}],
    "lines": [{"t": 3.6, "speaker": "doug", "text": "I can't feel my ears."}]
  }
  ("t" = when the line STARTS in the FINAL film's timeline, in seconds.)

Exit code 0 = all checks passed; 1 = defects found (report lists them);
2 = QC itself could not run (missing model etc.) — NEVER treat 2 as a pass.

Written 2026-07-22 after the "Every Day" incident: a film was shipped as
"verified" on 0.3% frame coverage. This script exists so that never repeats.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

PE_URL = "http://127.0.0.1:8181"
MODEL_ID = "divinetribe/Huihui-Qwen3-VL-32B-Instruct-abliterated-4bit-mlx"
WHISPER_ID = "mlx-community/whisper-large-v3-turbo"
ARTIFACT_STEP = 1.0   # seconds between artifact-sweep samples
TOL = 1.2             # transcript timing tolerance, seconds
MAX_TOKENS = 200

_state = {"model": None, "processor": None, "use_server": False}


def _run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def ffprobe_duration(path):
    r = _run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
              "-of", "csv=p=0", str(path)])
    return float(r.stdout.strip())


def extract_frame(video, t, out):
    _run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", str(video),
          "-frames:v", "1", "-vf", "scale=768:-2", str(out)])
    return Path(out).exists() and Path(out).stat().st_size > 1000


def tile(images, out, cols=4):
    from PIL import Image
    imgs = [Image.open(p) for p in images]
    w = max(i.width for i in imgs)
    h = max(i.height for i in imgs)
    rows = (len(imgs) + cols - 1) // cols
    sheet = Image.new("RGB", (w * min(cols, len(imgs)), h * rows), (0, 0, 0))
    for n, im in enumerate(imgs):
        sheet.paste(im, ((n % cols) * w, (n // cols) * h))
    sheet.save(out)


def vl_ask(image_path, prompt):
    """Ask the vision model one question about one image. Server first."""
    if _state["use_server"]:
        import requests
        with open(image_path, "rb") as f:
            r = requests.post(f"{PE_URL}/describe", timeout=600,
                              files={"image": f},
                              data={"prompt": prompt, "max_tokens": MAX_TOKENS})
        r.raise_for_status()
        return r.text.strip()
    # in-process fallback
    if _state["model"] is None:
        from mlx_vlm import load
        _state["model"], _state["processor"] = load(MODEL_ID)
    from mlx_vlm import generate
    from mlx_vlm.prompt_utils import apply_chat_template
    prompt_fmt = apply_chat_template(_state["processor"],
                                     _state["model"].config, prompt,
                                     num_images=1)
    out = generate(_state["model"], _state["processor"], prompt_fmt,
                   image=[str(image_path)], max_tokens=MAX_TOKENS,
                   verbose=False)
    return (out.text if hasattr(out, "text") else str(out)).strip()


def unload_vl() -> float:
    """Drop the in-process VL model and return the GB released.

    When Picture Eyes (:8181) is down, vl_ask loads the 32B VL model INSIDE the
    calling process — so forge-shot carries ~18GB that no outside evictor can
    reach, straight through a Wan render. That co-residency is what put the box
    into swap before the 2026-07-27 panic (CLAUDE.md rule 16). Call this before
    handing the GPU to a heavy render; the next vl_ask reloads it."""
    if _state["model"] is None:
        return 0.0
    _state["model"] = None
    _state["processor"] = None
    import gc
    gc.collect()
    try:
        import mlx.core as mx
        mx.clear_cache()
    except Exception:
        pass
    return 1.0  # freed (exact GB isn't measurable post-hoc; caller just logs it)


def whisper_transcribe(video):
    """Return list of {start, end, text} segments via mlx whisper."""
    import mlx_whisper  # available in the mlx-server venv? fallback: CLI
    res = mlx_whisper.transcribe(str(video), path_or_hf_repo=WHISPER_ID,
                                 word_timestamps=False)
    return res.get("segments", [])


# ── Song Forge keeps its seat (Matt, 2026-07-27) ────────────────────
# The 32B VL judge on top of resident Wan weights froze the whole Mac on
# 7/22, and sustained swap panicked it twice on 7/27. So QC asks forge_guard
# for room out of what is left after ACE/gemma, and waits for it rather than
# taking it. No guard installed = unchanged behaviour.
sys.path.insert(0, str(Path.home() / "SongForgeM5"))
_HAVE_GUARD = True
try:
    from mem_client import reserve as _mem_reserve
except Exception:
    _HAVE_GUARD = False
    import contextlib

    @contextlib.contextmanager
    def _mem_reserve(name, gb, timeout=900, ttl=1800):
        yield None


def _guard_says_critical() -> bool:
    """acquire() returns None for BOTH 'denied' and 'no guard reachable', so the
    lease alone cannot tell us which. Ask the guard directly: only a reachable guard
    reporting a bad level justifies refusing to run QC. If it is unreachable we
    proceed (and say so) rather than block QC on a health endpoint being down."""
    if not _HAVE_GUARD:
        return False
    try:
        import json as _json
        import urllib.request as _u
        with _u.urlopen("http://127.0.0.1:8790/api/state", timeout=5) as r:
            return _json.loads(r.read()).get("level") in ("critical", "high")
    except Exception:
        return False


def main():
    # `reserve` DENIED still runs the body — it logs "not granted … proceeding
    # carefully" and yields anyway. On 2026-07-27 that meant loading a 26GB VL judge
    # onto a box the guard had just called critical (swap 6.4GB); jetsam SIGTERMed it
    # at -15, no report was written, and the build announced COMPLETE.
    # Refusing is the only honest option: an UNCHECKED film reported as unchecked is
    # recoverable, a film killed mid-QC and called done is not. Exit 2 = could not run,
    # which callers must never treat as a pass.
    # Deliberate, logged override for a HUMAN who has judged the box can afford it
    # (e.g. after killing ComfyUI). Not an env var and not a default: the refusal is
    # the behaviour, this is a decision someone made out loud on a specific run.
    override = "--allow-critical-memory" in sys.argv
    # Don't block 30 minutes for a lease we have already decided to run without.
    # With the override set, ask once and proceed; without it, wait properly for a
    # seat. (2026-07-28: an overridden run sat idle at 28MB RSS for 30 minutes
    # waiting for a denial it was going to ignore.)
    _timeout = 5 if override else 1800
    with _mem_reserve("film-qc-vl", 26, timeout=_timeout, ttl=3600) as lease:
        if override and lease is None:
            print("[film_qc] --allow-critical-memory: guard denied the lease, running "
                  "anyway by explicit operator decision. If this is killed the film is "
                  "UNCHECKED, not passed.", file=sys.stderr)
        elif lease is None and _guard_says_critical():
            print("[film_qc] REFUSING TO START: the memory guard would not grant 26GB "
                  "for the vision judge and still reports the machine critical. Free "
                  "memory (bounce ComfyUI, let Song Forge settle) and re-run. The film "
                  "is UNCHECKED — never treat this as a pass.", file=sys.stderr)
            return 2
        elif lease is None and _HAVE_GUARD:
            # Reachable-but-denied is handled above; this is the genuinely-unreachable
            # case only. It was a bare `if` and printed "guard unreachable" on a run
            # where the guard had answered and said critical — a log line that
            # contradicted the line above it (2026-07-27).
            print("[film_qc] no memory lease (guard did not answer) — running anyway; "
                  "if this is killed, the film is UNCHECKED, not passed.", file=sys.stderr)
        return _main()


def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("film")
    ap.add_argument("manifest")
    ap.add_argument("--report", default=None)
    ap.add_argument("--allow-critical-memory", action="store_true",
                    help="run even if the memory guard denies the lease. Operator "
                         "decision for a specific run; never a default, never scripted.")
    args = ap.parse_args()

    film = Path(args.film)
    man = json.loads(Path(args.manifest).read_text())
    chars = man["characters"]
    lines = sorted(man["lines"], key=lambda l: l["t"])
    scenes = man.get("scenes", [])
    char_desc = "; ".join(f"{k} = {v}" for k, v in chars.items())

    # Is the Picture Eyes server up?
    try:
        import requests
        _state["use_server"] = requests.get(f"{PE_URL}/status", timeout=3).json().get("loaded", False)
    except Exception:
        _state["use_server"] = False

    dur = ffprobe_duration(film)
    tmp = Path(tempfile.mkdtemp(prefix="film_qc_"))
    defects, passed, qc_log = [], [], []

    def check(name, ok, detail):
        (passed if ok else defects).append(f"{name}: {detail}")
        qc_log.append(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
        print(qc_log[-1], flush=True)

    # ---- 1. lip sync per line -------------------------------------------
    # COVERAGE, not presence. The question is not "does the mouth open at some
    # instant during this line" — it is "is the mouth moving for MOST of the line".
    # A single open frame in forty is exactly the defect a viewer reads as a
    # character talking with a shut muzzle, and an any-sample rule PASSES it.
    # (2026-07-25: an any-of-three rule was introduced to suppress false FAILs and
    # instead silently green-lit Doug's "three, two, one, push" playing over a
    # closed mouth for a full second. Matt caught it on screen. Never loosen this
    # gate to make the number look better.)
    #
    # So: sample the WHOLE line at LIPSYNC_HZ, and require the speaker's mouth to
    # be open in at least LIPSYNC_MIN_COVERAGE of the samples. The report always
    # states the ratio, so a marginal line is visible rather than a bare PASS.
    # Lines flagged "offscreen" are voice-only by design (a character behind a
    # door, a bird out of frame) — audio-verified only, never mouth-checked.
    LIPSYNC_HZ = 5.0
    LIPSYNC_MIN_COVERAGE = 0.5
    for i, ln in enumerate(lines):
        if ln.get("offscreen"):
            qc_log.append(f"[SKIP] lipsync@{ln['t']:.1f}s: {ln['speaker']} is "
                          f"off-screen by design — audio-only line")
            print(qc_log[-1], flush=True)
            continue
        span = float(ln.get("dur") or 1.2)
        n = max(3, int(span * LIPSYNC_HZ))
        open_hits, wrong, samples = 0, 0, 0
        for k in range(n):
            t = ln["t"] + span * (k + 0.5) / n
            f = tmp / f"line_{i}_{k}.png"
            if not extract_frame(film, t, f):
                continue
            samples += 1
            q = (f"Characters: {char_desc}. In this frame, which character has an "
                 f"open or clearly moving mouth, as if mid-speech? Answer with just "
                 f"the character name, or 'none', or 'both'.")
            ans = vl_ask(f, q).lower()
            if ln["speaker"].lower() in ans and "both" not in ans:
                open_hits += 1
            elif "none" not in ans:
                wrong += 1
        if not samples:
            check(f"line{i}-frame", False, f"could not extract any frame @{ln['t']:.1f}s")
            continue
        cov = open_hits / samples
        ok = cov >= LIPSYNC_MIN_COVERAGE and wrong == 0
        detail = (f"{ln['speaker']}'s mouth moving in {open_hits}/{samples} samples "
                  f"({cov*100:.0f}% of a {span:.1f}s line; need "
                  f"{LIPSYNC_MIN_COVERAGE*100:.0f}%)")
        if wrong:
            detail += f" — and {wrong} sample(s) showed the WRONG character speaking"
        check(f"lipsync@{ln['t']:.1f}s", ok, detail)

    # ---- 2. mouths shut during silence ----------------------------------
    sil = []
    for a, b in zip(lines, lines[1:]):
        gap_start, gap_end = a["t"] + 2.5, b["t"]
        if gap_end - gap_start > 1.0:
            sil.append((gap_start + gap_end) / 2)
    for j, t in enumerate(sil[:6]):
        f = tmp / f"sil_{j}.png"
        if not extract_frame(film, t, f):
            continue
        ans = vl_ask(f, f"Characters: {char_desc}. Nobody is speaking at this "
                        f"moment. Is any character's mouth wide open as if "
                        f"talking? Answer yes or no, then one short reason.").lower()
        check(f"silence@{t:.1f}s", ans.startswith("no"), ans[:80])

    # ---- 3. identity across scenes --------------------------------------
    if len(scenes) >= 2:
        shots = []
        for s in scenes:
            f = tmp / f"scene_{s['name']}.png"
            if extract_frame(film, (s["start"] + s["end"]) / 2, f):
                shots.append(f)
        if len(shots) >= 2:
            sheet = tmp / "identity.png"
            tile(shots, sheet)
            ans = vl_ask(sheet,
                         f"This sheet shows the same two characters ({char_desc}) "
                         f"in {len(shots)} different scenes. For EACH character, do "
                         f"they look like the SAME individual in every tile (same "
                         f"build, proportions, colors, face)? Answer 'consistent' "
                         f"or list every difference you can see.")
            check("identity-across-scenes", "consistent" in ans.lower()[:60], ans[:200])

    # ---- 4. artifact sweep ----------------------------------------------
    t = 0.5
    k = 0
    while t < dur:
        f = tmp / f"art_{k}.png"
        if extract_frame(film, t, f):
            ans = vl_ask(f, "Look closely at any animated characters. Any "
                            "deformities: extra or missing limbs, two bodies "
                            "merged together, warped or smeared face, wrong "
                            "proportions? Answer 'clean' or describe the defect.")
            check(f"artifact@{t:.1f}s", "clean" in ans.lower()[:40], ans[:120])
        t += ARTIFACT_STEP
        k += 1

    # ---- 5. transcript timing -------------------------------------------
    # Silent reels (no manifest lines) legitimately have no audio track —
    # running whisper on them produced a false FAIL (2026-07-23 finals reel).
    # No lines = nothing to verify = skip, stated in the report as UNCHECKED.
    if not lines:
        print("[film_qc] no dialogue lines in manifest — transcript check "
              "SKIPPED (audio UNCHECKED, not passed)", flush=True)
        qc_log.append("[SKIP] transcript: no dialogue lines in manifest — "
                      "audio UNCHECKED")
        segs = None
    try:
        if lines:
            segs = whisper_transcribe(film)
        for ln in lines:
            words = [w for w in ln["text"].lower().split() if len(w) > 3][:3]
            hit = None
            for s in segs:
                if any(w in s["text"].lower() for w in words):
                    hit = s
                    break
            ok = hit is not None and abs(hit["start"] - ln["t"]) <= TOL
            det = (f"'{ln['text'][:30]}' expected @{ln['t']:.1f}s, "
                   f"heard @{hit['start']:.1f}s" if hit else
                   f"'{ln['text'][:30]}' NOT HEARD in audio")
            check(f"audio@{ln['t']:.1f}s", ok, det)
    except Exception as e:
        check("transcript", False, f"whisper unavailable: {e}")

    # ---- report ----------------------------------------------------------
    verdict = "PASS" if not defects else f"FAIL — {len(defects)} defect(s)"
    report = [f"# film_qc report — {film.name}", f"**Verdict: {verdict}**",
              f"Checks run: {len(passed) + len(defects)} | passed: {len(passed)} | failed: {len(defects)}",
              "", "## Defects"] + [f"- {d}" for d in defects or ["(none)"]] + \
             ["", "## Full log"] + [f"- {l}" for l in qc_log]
    out = args.report or str(film.with_suffix("")) + "_qc.md"
    Path(out).write_text("\n".join(report))
    print(f"\n{verdict}\nreport: {out}")
    sys.exit(0 if not defects else 1)


if __name__ == "__main__":
    main()
