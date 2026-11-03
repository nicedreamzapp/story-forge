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
      [--spec] [--jury [--edl edl.json]]      add spec check / harsh jury
  film_qc.py FILM.mp4 manifest.json --spec-only    ffmpeg only, seconds, no model
  film_qc.py FILM.mp4 manifest.json --jury-only [--edl edl.json]

  6. SPEC (--spec, --spec-only, implied by --jury) — no model: resolution, fps,
                  duration vs manifest "spec"; EBU R128 loudness + true peak
                  (default -14 LUFS +-1, <= -1 dBTP); unintended black frames and
                  frozen spans. See SPEC_DEFAULTS for the "spec" block keys.
  7. JURY (--jury, --jury-only) — two-round harsh jury (rubric adapted from
                  mg-styles-15, MIT). Round 1: the same VL judge scores a frame
                  strip of every shot 1-10 on identity, anatomy, motion,
                  composition, lighting, story, calibrated harsh (most first
                  renders deserve 5-7). Round 2 sees round 1 and must argue
                  against every 8+; scores can only hold or drop. PASS = every
                  dimension's film mean >= 6, overall mean >= 7, no shot under 4
                  (all configurable: --jury-dim-min/--jury-mean-min/--jury-shot-floor).
  Spec and jury results get their own report sections and SPEC:/JURY: lines;
  the classic "Checks run | passed | failed" counts are untouched by them. Exit
  code is 1 if ANY requested gate fails.

manifest.json:
  {
    "characters": {"hank": "huge round brown bear",
                   "doug": "lanky brown bloodhound dog with long floppy ears"},
    "scenes": [{"name": "winter", "start": 2.4, "end": 13.1}],
    "lines": [{"t": 3.6, "speaker": "doug", "text": "I can't feel my ears."}],
    "shots": [{"name": "c01", "start": 0.0, "end": 1.5, "note": "..."}],   (optional, jury)
    "spec": {"width": 1920, "height": 1080, "fps": 24, "lufs": -14}        (optional, spec)
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


def vl_ask(image_path, prompt, max_tokens=None):
    """Ask the vision model one question about one image. Server first.
    max_tokens defaults to MAX_TOKENS; the jury needs more room for its JSON."""
    max_tokens = max_tokens or MAX_TOKENS
    if _state["use_server"]:
        import requests
        with open(image_path, "rb") as f:
            r = requests.post(f"{PE_URL}/describe", timeout=600,
                              files={"image": f},
                              data={"prompt": prompt, "max_tokens": max_tokens})
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
                   image=[str(image_path)], max_tokens=max_tokens,
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


def whisper_relisten(video, t, pre=2.0, post=4.0):
    """Transcribe ONLY a small window around t and return the joined text.

    Long-form whisper over a whole film can skip an entire music-heavy block
    (2026-07-31: six lines between 29.8s and 42.0s reported NOT HEARD while a
    direct transcription of that window heard every one at the right moment).
    A full-film transcript hole is therefore not proof of absent audio — the
    line must be re-judged on its own window before a FAIL is allowed.
    """
    import subprocess as sp
    import tempfile

    import mlx_whisper
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav = f.name
    try:
        sp.run(["ffmpeg", "-y", "-v", "error", "-ss", str(max(0.0, t - pre)),
                "-to", str(t + post), "-i", str(video), "-vn", "-ac", "1",
                "-ar", "16000", wav], check=True, capture_output=True)
        res = mlx_whisper.transcribe(wav, path_or_hf_repo=WHISPER_ID,
                                     word_timestamps=False)
        return res.get("text", "")
    finally:
        Path(wav).unlink(missing_ok=True)


# ── SPEC CHECK (no model) ───────────────────────────────────────────
# Cheap, deterministic checks that need nothing but ffmpeg: resolution / fps /
# duration against the manifest, loudness and true peak (EBU R128), unintended
# black frames and frozen spans. Runs in seconds, safe next to any render.
#
# manifest "spec" block (every key optional; a missing target is reported as
# UNCHECKED, never as a pass):
#   "spec": {"width": 1920, "height": 1080, "fps": 24, "duration": 46.625,
#            "duration_tol": 0.05,
#            "lufs": -14, "lufs_tol": 1.0, "true_peak_max": -1.0, "audio": true,
#            "black_min": 0.15, "freeze_min": 1.0,
#            "allow_black": [[44.9, 46.6]], "allow_static": [[0.0, 1.4]]}
# Loudness defaults follow the mg-styles-15 jury rubric: -14 LUFS +-1, TP <= -1 dBTP.
SPEC_DEFAULTS = {"lufs": -14.0, "lufs_tol": 1.0, "true_peak_max": -1.0,
                 "duration_tol": 0.05, "black_min": 0.15, "freeze_min": 1.0,
                 "edge_grace": 0.6}


def _probe_video(path):
    r = _run(["ffprobe", "-v", "error", "-show_entries",
              "stream=codec_type,width,height,r_frame_rate:format=duration",
              "-of", "json", str(path)])
    d = json.loads(r.stdout or "{}")
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
    a = any(s.get("codec_type") == "audio" for s in d.get("streams", []))
    num, _, den = (v.get("r_frame_rate") or "0/1").partition("/")
    fps = float(num) / float(den or 1) if float(den or 1) else 0.0
    return {"width": v.get("width"), "height": v.get("height"), "fps": fps,
            "duration": float(d.get("format", {}).get("duration") or 0), "audio": a}


def _ebur128(path):
    """Integrated loudness (LUFS), loudness range and true peak (dBTP)."""
    import re
    r = _run(["ffmpeg", "-nostats", "-hide_banner", "-i", str(path), "-vn",
              "-af", "ebur128=peak=true", "-f", "null", "-"])
    tail = r.stderr[r.stderr.rfind("Summary:"):] if "Summary:" in r.stderr else ""
    def grab(pat):
        m = re.search(pat, tail, re.S)
        return float(m.group(1)) if m else None
    return {"lufs": grab(r"I:\s+(-?[\d.]+|-inf)\s+LUFS"),
            "lra": grab(r"LRA:\s+(-?[\d.]+)\s+LU"),
            "true_peak": grab(r"True peak:\s+Peak:\s+(-?[\d.]+|-inf)\s+dBFS")}


def _spans(path, vf, start_key, end_key):
    import re
    r = _run(["ffmpeg", "-nostats", "-hide_banner", "-i", str(path), "-an",
              "-vf", vf, "-f", "null", "-"])
    out, cur = [], None
    for ln in r.stderr.splitlines():
        m = re.search(start_key + r":\s*(-?[\d.]+)", ln)
        if m:
            cur = float(m.group(1))
        m = re.search(end_key + r":\s*(-?[\d.]+)", ln)
        if m and cur is not None:
            out.append((cur, float(m.group(1))))
            cur = None
    return out, cur


def _covered(span, allowed, grace=0.05):
    a, b = span
    return any(a >= s - grace and b <= e + grace for s, e in allowed)


def spec_check(film, man):
    """Returns (rows, failed) where rows are (status, name, detail);
    status is PASS / FAIL / UNCHECKED / INFO."""
    spec = dict(SPEC_DEFAULTS)
    spec.update(man.get("spec") or {})
    rows = []
    p = _probe_video(film)
    dur = p["duration"]

    for key, label in (("width", "width"), ("height", "height")):
        if spec.get(key) is None:
            rows.append(("UNCHECKED", f"spec-{label}", f"{p[key]} px (no target in manifest spec)"))
        else:
            rows.append(("PASS" if p[key] == spec[key] else "FAIL", f"spec-{label}",
                         f"{p[key]} px, manifest wants {spec[key]}"))
    if spec.get("fps") is None:
        rows.append(("UNCHECKED", "spec-fps", f"{p['fps']:.3f} fps (no target in manifest spec)"))
    else:
        rows.append(("PASS" if abs(p["fps"] - float(spec["fps"])) < 0.01 else "FAIL",
                     "spec-fps", f"{p['fps']:.3f} fps, manifest wants {spec['fps']}"))
    if spec.get("duration") is not None:
        ok = abs(dur - float(spec["duration"])) <= float(spec["duration_tol"])
        rows.append(("PASS" if ok else "FAIL", "spec-duration",
                     f"{dur:.3f} s, manifest wants {spec['duration']} +-{spec['duration_tol']}"))
    else:
        rows.append(("INFO", "spec-duration", f"{dur:.3f} s"))

    want_audio = spec.get("audio", True)
    if not p["audio"]:
        rows.append(("FAIL" if want_audio else "PASS", "spec-audio",
                     "no audio stream" + ("" if want_audio else " (manifest says silent)")))
    else:
        ld = _ebur128(film)
        if ld["lufs"] is None:
            rows.append(("UNCHECKED", "spec-loudness", "ebur128 gave no integrated loudness"))
        else:
            ok = abs(ld["lufs"] - float(spec["lufs"])) <= float(spec["lufs_tol"])
            rows.append(("PASS" if ok else "FAIL", "spec-loudness",
                         f"{ld['lufs']:.1f} LUFS integrated (LRA {ld['lra']} LU), target "
                         f"{spec['lufs']} +-{spec['lufs_tol']}"))
        if ld["true_peak"] is None:
            rows.append(("UNCHECKED", "spec-true-peak", "ebur128 gave no true peak"))
        else:
            ok = ld["true_peak"] <= float(spec["true_peak_max"])
            rows.append(("PASS" if ok else "FAIL", "spec-true-peak",
                         f"{ld['true_peak']:.1f} dBTP, ceiling {spec['true_peak_max']}"))

    # Black frames: spans touching the head or tail (fade in/out) are allowed,
    # anything else must be listed in allow_black.
    grace = float(spec["edge_grace"])
    allow_b = [tuple(x) for x in spec.get("allow_black", [])]
    blacks, open_b = _spans(film, f"blackdetect=d={spec['black_min']}:pix_th=0.10",
                            "black_start", "black_end")
    if open_b is not None:
        blacks.append((open_b, dur))
    bad_b = [b for b in blacks if not (b[0] <= grace or b[1] >= dur - grace
                                       or _covered(b, allow_b))]
    rows.append(("PASS" if not bad_b else "FAIL", "spec-black-frames",
                 f"{len(blacks)} black span(s) >= {spec['black_min']}s, "
                 f"{len(bad_b)} unintended" +
                 (": " + ", ".join(f"{a:.2f}-{b:.2f}s" for a, b in bad_b) if bad_b else "")))

    # Frozen frames: freezedetect, ignoring spans that are black (already judged)
    # and spans listed in allow_static (title cards, intended holds).
    allow_s = [tuple(x) for x in spec.get("allow_static", [])]
    freezes, open_f = _spans(film, f"freezedetect=n=-60dB:d={spec['freeze_min']}",
                             "lavfi.freezedetect.freeze_start", "lavfi.freezedetect.freeze_end")
    if open_f is not None:
        freezes.append((open_f, dur))
    def mostly_black(f):
        ov = sum(max(0.0, min(f[1], b[1]) - max(f[0], b[0])) for b in blacks)
        return ov >= 0.8 * (f[1] - f[0])
    bad_f = [f for f in freezes if not (mostly_black(f) or _covered(f, allow_s))]
    rows.append(("PASS" if not bad_f else "FAIL", "spec-frozen-frames",
                 f"{len(freezes)} static span(s) >= {spec['freeze_min']}s, "
                 f"{len(bad_f)} unintended" +
                 (": " + ", ".join(f"{a:.2f}-{b:.2f}s" for a, b in bad_f) if bad_f else "")))
    failed = sum(1 for r in rows if r[0] == "FAIL")
    return rows, failed


# ── HARSH JURY (two rounds, local Qwen3-VL) ─────────────────────────
# Adapted from the "second AI as harsh jury" rubric in mg-styles-15 (MIT,
# github.com/Vincentwei1021/mg-styles-15, rubric.md). Round 1 scores every shot
# 1-10 on fixed dimensions with a calibrated-harsh scale. Round 2 sees round 1
# and must argue AGAINST every score of 8 or more; it can only hold or lower a
# score, never raise it (a jury that argues itself upward is not a jury).
# The judge is the same VL model and loader the rest of film_qc uses.
JURY_DIMS = [
    ("identity", "identity consistency: every person/creature keeps the same face, "
                 "build, hair, costume and markings across the frames"),
    ("anatomy", "anatomy and artifacts: hands, fingers, limbs, faces, eyes, teeth are "
                "correct; no melting, smearing, merged bodies, warped geometry, "
                "garbled text or AI mush"),
    ("motion", "motion plausibility: from frame to frame the movement reads as "
               "physically real (weight, direction, contact with ground); no "
               "running in place, sliding, popping or morphing"),
    ("composition", "composition: framing, subject placement, depth, readable "
                    "silhouette, purposeful camera"),
    ("lighting", "lighting and continuity: light direction and colour consistent "
                 "within the shot, props and costume continuous, grade intentional"),
    ("story", "story read: a first-time viewer instantly understands what is "
              "happening in this shot and why it is in the film"),
]
JURY_SCALE = ("Scale: 5 = competent student work, 6 = decent template level, "
              "7 = solid professional, 8 = high-end agency work, 9 = award "
              "shortlist, 10 = best in the world. Most first renders deserve 5-7. "
              "Do not inflate. Kindness is useless here; specificity is everything.")
JURY_NA = ("If a dimension has truly nothing to judge in this shot (identity or anatomy "
           "when no person or creature is visible), give null instead of a number and say "
           "why. Never give a high score just because there is nothing to fault. The cast "
           "list is reference only: not every character appears in every shot, and a "
           "character's absence is not a flaw.")
JURY_TOKENS = 520


def _num(x):
    return "n/a" if x is None else f"{x:g}"


def _mean(vals):
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None


def jury_shots(film, man, edl_path=None, max_shots=None):
    """Shots to judge, in film order: --edl cuts, else manifest "shots", else
    manifest "scenes", else uniform 3 s windows. Each: {name, start, end, note}."""
    shots = []
    if edl_path:
        edl = json.loads(Path(edl_path).read_text())
        cuts = edl["cuts"] if isinstance(edl, dict) else edl
        for c in cuts:
            st = float(c["start"])
            shots.append({"name": c.get("id", f"cut{len(shots)}"), "start": st,
                          "end": st + float(c.get("len", c.get("dur", 1.0))),
                          "note": " ".join(str(c.get(k, "")) for k in
                                           ("section", "prompt", "desc", "note")).strip()})
    elif man.get("shots"):
        for s in man["shots"]:
            shots.append({"name": s.get("name", f"shot{len(shots)}"), "start": float(s["start"]),
                          "end": float(s["end"]), "note": s.get("note", s.get("desc", ""))})
    elif man.get("scenes"):
        for s in man["scenes"]:
            shots.append({"name": s["name"], "start": float(s["start"]),
                          "end": float(s["end"]), "note": s.get("note", "")})
    else:
        dur = ffprobe_duration(film)
        t = 0.0
        while t < dur - 0.2:
            shots.append({"name": f"w{len(shots):02d}", "start": t,
                          "end": min(dur, t + 3.0), "note": ""})
            t += 3.0
    if max_shots and len(shots) > max_shots:
        # spread the sample over the whole film rather than taking the head
        step = len(shots) / max_shots
        shots = [shots[int(i * step)] for i in range(max_shots)]
    return shots


def _jury_json(ans):
    """Pull {dim: [score, reason]} out of the judge's reply. Accepts
    {"identity": [6, "..."]} or {"identity": {"score": 6, "reason": "..."}}.
    Returns None unless every dimension parsed."""
    import re
    m = re.search(r"\{.*\}", ans, re.S)
    if not m:
        return None
    txt = m.group(0)
    try:
        d = json.loads(txt)
    except Exception:
        d = {}
        for key, _ in JURY_DIMS:
            mm = re.search(r'"%s"\s*:\s*[\[{]\s*(?:"score"\s*:\s*)?(\d+(?:\.\d+)?|null)\s*,\s*'
                           r'(?:"reason"\s*:\s*|"argument"\s*:\s*)?"([^"]*)"' % key, txt)
            if mm:
                d[key] = [None if mm.group(1) == "null" else float(mm.group(1)), mm.group(2)]
    out = {}
    for key, _ in JURY_DIMS:
        v = d.get(key)
        if isinstance(v, dict):
            v = [v.get("score"), v.get("reason") or v.get("argument") or ""]
        if not isinstance(v, (list, tuple)) or not v:
            return None
        if v[0] is None or str(v[0]).strip().lower() in ("null", "n/a", "na"):
            sc = None   # nothing to judge (no people in the shot): excluded, never a free 10
        else:
            try:
                sc = max(1.0, min(10.0, float(v[0])))
            except Exception:
                return None
        out[key] = (sc, str(v[1] if len(v) > 1 else "").strip())
    return out


def _log_flush(msg):
    print(msg, flush=True)


def jury_film(film, man, tmp, shots, frames=4, log=_log_flush):
    """Two-round jury over every shot. Returns list of per-shot dicts."""
    chars = man.get("characters") or {}
    char_desc = "; ".join(f"{k} = {v}" for k, v in chars.items()) or "(no cast listed)"
    story = man.get("logline") or man.get("story") or man.get("_film_qc_note") or ""
    dims_txt = "\n".join(f"- {k}: {d}" for k, d in JURY_DIMS)
    keys = ", ".join(f'"{k}"' for k, _ in JURY_DIMS)
    results = []
    for n, sh in enumerate(shots):
        span = max(0.04, sh["end"] - sh["start"])
        k = max(2, min(frames, int(span * 12)))
        pics = []
        for i in range(k):
            t = sh["start"] + span * (i + 0.5) / k
            f = tmp / f"jury_{n}_{i}.png"
            if extract_frame(film, t, f):
                pics.append(f)
        row = {"name": sh["name"], "start": sh["start"], "end": sh["end"],
               "r1": None, "final": None, "raw1": "", "raw2": ""}
        if not pics:
            row["error"] = "no frames extracted"
            results.append(row)
            continue
        sheet = tmp / f"jury_{n}.png"
        tile(pics, sheet, cols=len(pics))
        ctx = (f"Shot '{sh['name']}' at {sh['start']:.2f}-{sh['end']:.2f}s of the film "
               f"(shot {n + 1} of {len(shots)}). Cast: {char_desc}."
               + (f" Shot notes: {sh['note']}." if sh.get("note") else "")
               + (f" About the film: {story}" if story else ""))
        q1 = (f"You are a senior film jury member. You did NOT make this film. Judge it "
              f"harshly and precisely. The image is a strip of {len(pics)} frames from ONE "
              f"shot, in time order left to right, {span / len(pics):.2f}s apart. {ctx}\n"
              f"Score 1-10 on each dimension:\n{dims_txt}\n{JURY_SCALE}\n{JURY_NA}\n"
              f"Reply with ONLY one JSON object, keys {keys}, each value "
              f"[score or null, \"one short concrete reason naming what you see\"]. No other text.")
        r1 = None
        for attempt in range(2):
            ans = vl_ask(sheet, q1 if attempt == 0 else
                         q1 + " Your last reply was not valid JSON. JSON only.",
                         max_tokens=JURY_TOKENS)
            row["raw1"] = ans
            r1 = _jury_json(ans)
            if r1:
                break
        if not r1:
            row["error"] = "round 1 unparsed"
            results.append(row)
            log(f"[JURY] {sh['name']}: UNCHECKED (round 1 gave no parseable scores)")
            continue
        row["r1"] = r1
        final = dict(r1)
        high = [d for d, (sc, _) in r1.items() if sc is not None and sc >= 8]
        if high:
            r1_txt = "; ".join(f"{d}={_num(sc)} ({why})" for d, (sc, why) in r1.items())
            q2 = (f"You are the SECOND, harsher juror. Same strip: {len(pics)} frames of one "
                  f"shot, time order left to right. {ctx}\nRound 1 scored: {r1_txt}\n"
                  f"{JURY_SCALE}\nFor EVERY score of 8 or more ({', '.join(high)}) you must "
                  f"argue against it: name the concrete visible flaw that keeps it below "
                  f"high-end agency level, then give the final score. Scores under 8 may be "
                  f"kept or lowered, never raised; keep null where round 1 gave null. "
                  f"{JURY_NA} Reply with ONLY one JSON object, keys "
                  f"{keys}, each value [final_score or null, \"your argument\"]. No other text.")
            r2 = None
            for attempt in range(2):
                ans = vl_ask(sheet, q2 if attempt == 0 else
                             q2 + " Your last reply was not valid JSON. JSON only.",
                             max_tokens=JURY_TOKENS)
                row["raw2"] = ans
                r2 = _jury_json(ans)
                if r2:
                    break
            if r2:
                # the jury may only argue a score down
                final = {}
                for d in r1:
                    a, b = r1[d][0], r2[d][0]
                    if a is None:
                        final[d] = r1[d]          # round 1 said nothing to judge
                    elif b is None:
                        final[d] = (a, r1[d][1])  # round 2 cannot erase a score
                    else:
                        final[d] = (min(a, b), r2[d][1] if b < a or d in high else r1[d][1])
            else:
                # round 2 never ruled: the inflated scores are not trusted
                final = {d: ((7.0, f"capped: round 2 unparsed, round 1 said {sc:g}")
                             if sc is not None and sc >= 8 else (sc, why))
                         for d, (sc, why) in r1.items()}
                row["error"] = "round 2 unparsed, 8+ scores capped at 7"
        row["final"] = final
        row["round2"] = bool(high)
        results.append(row)
        mean = _mean(v[0] for v in final.values())
        log(f"[JURY] {sh['name']}: " + " ".join(f"{d}={_num(final[d][0])}" for d, _ in JURY_DIMS)
            + f"  mean {_num(round(mean, 2)) if mean is not None else 'n/a'}"
            + ("  (round 2 ran on " + ",".join(high) + ")" if high else ""))
    return results


def jury_verdict(results, dim_min=6.0, mean_min=7.0, shot_floor=4.0):
    """Film-level verdict. Each dimension's film score = mean over judged shots.
    PASS needs every dimension >= dim_min, overall mean >= mean_min, no shot
    scoring under shot_floor anywhere, and no unjudged shot (UNCHECKED is not a pass)."""
    judged = [r for r in results if r.get("final")]
    unjudged = [r for r in results if not r.get("final")]
    reasons = []
    film = {}
    # n/a scores (nothing to judge) are left out of every mean, never counted as 10.
    for d, _ in JURY_DIMS:
        vals = [r["final"][d][0] for r in judged if r["final"][d][0] is not None]
        film[d] = (sum(vals) / len(vals), min(vals)) if vals else (None, None)
        if vals and film[d][0] < dim_min:
            reasons.append(f"{d} {film[d][0]:.2f} < {dim_min:g}")
    overall = _mean(v[0] for v in film.values()) or 0.0
    if judged and overall < mean_min:
        reasons.append(f"mean {overall:.2f} < {mean_min:g}")
    floor_hits = [(r["name"], d, r["final"][d][0], r["final"][d][1]) for r in judged
                  for d, _ in JURY_DIMS
                  if r["final"][d][0] is not None and r["final"][d][0] < shot_floor]
    if floor_hits:
        reasons.append(f"{len(floor_hits)} shot score(s) under the floor {shot_floor:g}")
    if unjudged:
        reasons.append(f"{len(unjudged)} shot(s) UNCHECKED (judge gave no usable answer)")
    if not judged:
        reasons.append("no shot judged")
    return {"pass": not reasons, "film": film, "overall": overall, "reasons": reasons,
            "floor_hits": floor_hits, "judged": len(judged), "unjudged": unjudged}


def jury_report_lines(results, v, thresholds):
    dim_min, mean_min, shot_floor = thresholds
    L = ["", "## Harsh jury (two rounds, local Qwen3-VL)",
         f"**Jury verdict: {'PASS' if v['pass'] else 'FAIL'}** "
         f"(needs each dimension >= {dim_min:g}, mean >= {mean_min:g}, no shot under "
         f"{shot_floor:g}) | shots judged: {v['judged']} | unchecked: {len(v['unjudged'])} "
         f"| round 2 ran on {sum(1 for r in results if r.get('round2'))}",
         f"Film mean: **{v['overall']:.2f}**", "",
         "| dimension | film mean | worst shot |", "|---|---|---|"]
    for d, _ in JURY_DIMS:
        m, w = v["film"][d]
        L.append(f"| {d} | {'n/a' if m is None else f'{m:.2f}'} | {_num(w)} |")
    if v["reasons"]:
        L += ["", "Why it failed:"] + [f"- {r}" for r in v["reasons"]]
    if v["floor_hits"]:
        L += ["", "Shots under the floor:"] + [
            f"- {n} {d}={sc:g}: {why}" for n, d, sc, why in v["floor_hits"]]
    L += ["", "### Per shot (final scores; r1 = round 1 where round 2 argued it down)",
          "| shot | t | " + " | ".join(d for d, _ in JURY_DIMS) + " | mean |",
          "|---|---|" + "---|" * (len(JURY_DIMS) + 1)]
    for r in results:
        if not r.get("final"):
            L.append(f"| {r['name']} | {r['start']:.2f} | UNCHECKED: {r.get('error', '')} |")
            continue
        cells = []
        for d, _ in JURY_DIMS:
            f = r["final"][d][0]
            o = r["r1"][d][0] if r.get("r1") else f
            cells.append(_num(f) + (f" (r1 {_num(o)})" if f != o else ""))
        mean = _mean(x[0] for x in r["final"].values())
        L.append(f"| {r['name']} | {r['start']:.2f} | " + " | ".join(cells) +
                 f" | {'n/a' if mean is None else f'{mean:.2f}'} |")
    L += ["", "### Jury reasons (final)"]
    for r in results:
        if r.get("final"):
            L.append(f"- **{r['name']}**: " + " / ".join(
                f"{d} {_num(r['final'][d][0])}: {r['final'][d][1]}" for d, _ in JURY_DIMS))
    return L


def songforge_wait(max_wait=1800):
    """Song Forge customer jobs outrank QC (frozen rule 11): wait while
    jobs_running > 0 on :8767 before loading the VL judge. Unreachable = go."""
    import time
    import urllib.request
    waited = 0
    while True:
        try:
            with urllib.request.urlopen("http://127.0.0.1:8767/api/status", timeout=5) as r:
                running = json.loads(r.read()).get("jobs_running", 0)
        except Exception:
            return True
        if not running:
            return True
        if waited >= max_wait:
            return False
        if waited == 0:
            print(f"[film_qc] Song Forge has {running} job(s) running, waiting before "
                  f"loading the judge", file=sys.stderr, flush=True)
        time.sleep(20)
        waited += 20


def run_extras(args, film, man):
    """Spec check and/or jury. Returns (report_lines, failed: bool)."""
    lines, failed = [], False
    if args.spec or args.jury or args.jury_only or args.spec_only:
        rows, nfail = spec_check(film, man)
        for st, name, det in rows:
            print(f"[{st}] {name}: {det}", flush=True)
        lines += ["", "## Spec check (no model)",
                  f"**Spec verdict: {'PASS' if not nfail else f'FAIL — {nfail} problem(s)'}**"] + \
                 [f"- [{st}] {name}: {det}" for st, name, det in rows]
        failed |= nfail > 0
        args._spec_summary = "SPEC: " + ("PASS" if not nfail else f"FAIL — {nfail} problem(s)")
    if args.jury or args.jury_only:
        tmp = Path(tempfile.mkdtemp(prefix="film_jury_"))
        shots = jury_shots(film, man, args.edl, args.jury_max_shots)
        print(f"[film_qc] jury: {len(shots)} shot(s), {args.jury_frames} frames each",
              flush=True)
        res = jury_film(film, man, tmp, shots, frames=args.jury_frames)
        th = (args.jury_dim_min, args.jury_mean_min, args.jury_shot_floor)
        v = jury_verdict(res, *th)
        lines += jury_report_lines(res, v, th)
        failed |= not v["pass"]
        args._jury_summary = (f"JURY: {'PASS' if v['pass'] else 'FAIL'} (mean "
                              f"{v['overall']:.2f}; " + ", ".join(
                                  f"{d} " + ("n/a" if v["film"][d][0] is None else
                                             f"{v['film'][d][0]:.1f}")
                                  for d, _ in JURY_DIMS) + ")")
        if args.jury_json:
            Path(args.jury_json).write_text(json.dumps(
                {"film": str(film), "verdict": "PASS" if v["pass"] else "FAIL",
                 "overall": v["overall"], "reasons": v["reasons"],
                 "dims": {d: {"mean": v["film"][d][0], "worst": v["film"][d][1]}
                          for d, _ in JURY_DIMS},
                 "shots": [{"name": r["name"], "start": r["start"], "end": r["end"],
                            "round1": r["r1"], "final": r["final"],
                            "error": r.get("error")} for r in res]}, indent=1))
    return lines, failed


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
    # The spec checker is ffmpeg only: no judge, no lease, no waiting.
    if "--spec-only" in sys.argv:
        return _main()
    # Song Forge customer jobs outrank the jury's VL passes (frozen rule 11).
    if ("--jury" in sys.argv or "--jury-only" in sys.argv) and not songforge_wait():
        print("[film_qc] REFUSING TO START the jury: Song Forge jobs kept running for "
              "30 minutes. The film is UNCHECKED, not passed.", file=sys.stderr)
        return 2
    # Don't block 30 minutes for a lease we have already decided to run without.
    # With the override set, ask once and proceed; without it, wait properly for a
    # seat. (2026-07-28: an overridden run sat idle at 28MB RSS for 30 minutes
    # waiting for a denial it was going to ignore.)
    # NOTE (2026-07-28): the override is nearly always the WRONG tool. A lease is
    # PROTECTION, not permission — forge_guard SIGTERMs big unleased processes when
    # it is unhappy, so running "anyway" is precisely what got film_qc killed three
    # times. If the guard won't seat you, fix why it is unhappy; don't sneak past it.
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
    # Jury + spec modes. None of these change the classic checks or their counts;
    # their results go in their own report sections with their own verdict lines.
    ap.add_argument("--spec", action="store_true",
                    help="also run the no-model spec check (loudness, true peak, black/"
                         "frozen frames, resolution/fps vs manifest 'spec')")
    ap.add_argument("--spec-only", action="store_true",
                    help="run ONLY the spec check (ffmpeg, seconds, no model)")
    ap.add_argument("--jury", action="store_true",
                    help="also run the two-round harsh jury (implies --spec)")
    ap.add_argument("--jury-only", action="store_true",
                    help="run ONLY the jury + spec check, skip the classic checks")
    ap.add_argument("--edl", default=None,
                    help="EDL json with 'cuts' (id/start/len): jury judges every cut. "
                         "Default: manifest 'shots', else 'scenes', else 3 s windows")
    ap.add_argument("--jury-frames", type=int, default=4, help="frames per shot strip")
    ap.add_argument("--jury-max-shots", type=int, default=None,
                    help="judge at most N shots, spread evenly over the film")
    ap.add_argument("--jury-dim-min", type=float, default=6.0,
                    help="every dimension's film mean must reach this (default 6)")
    ap.add_argument("--jury-mean-min", type=float, default=7.0,
                    help="overall mean must reach this (default 7)")
    ap.add_argument("--jury-shot-floor", type=float, default=4.0,
                    help="any single shot score under this fails the film (default 4)")
    ap.add_argument("--jury-json", default=None, help="also write jury scores as JSON")
    args = ap.parse_args()

    film = Path(args.film)
    man = json.loads(Path(args.manifest).read_text())

    if args.jury_only or args.spec_only:
        if args.jury_only:
            try:
                import requests
                _state["use_server"] = requests.get(f"{PE_URL}/status", timeout=3).json().get("loaded", False)
            except Exception:
                _state["use_server"] = False
        try:
            extra, failed = run_extras(args, film, man)
        except Exception as e:
            print(f"[film_qc] jury/spec could not run: {e}. The film is UNCHECKED, "
                  f"not passed.", file=sys.stderr)
            sys.exit(2)
        mode = "jury + spec" if args.jury_only else "spec"
        summary = [x for x in (getattr(args, "_spec_summary", None),
                               getattr(args, "_jury_summary", None)) if x]
        report = [f"# film_qc report ({mode} only) — {film.name}",
                  f"**Verdict: {'PASS' if not failed else 'FAIL'}**",
                  "Classic checks (lip sync, silence, identity, artifacts, transcript) "
                  "were NOT run in this mode: they are UNCHECKED, not passed."] + extra
        suffix = "_jury.md" if args.jury_only else "_spec.md"
        out = args.report or str(film.with_suffix("")) + suffix
        Path(out).write_text("\n".join(report))
        print("\n" + "\n".join(summary) + f"\nreport: {out}")
        sys.exit(1 if failed else 0)

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
            # VERDICT FIRST. The old prompt ended "answer 'consistent' or list every
            # difference you can see" — an invitation to enumerate, which the model
            # accepted: it opened "Let's analyze each character across the 9 scenes..."
            # and hit the 200-token cap mid-sentence without ever reaching a verdict.
            # The scorer wanted "consistent" in the first 60 characters, so a truncated
            # ramble scored FAIL and the report showed a defect that was really an
            # unanswered question (2026-07-28). Every other gate in this pipeline
            # learned the same lesson: demand the ruling first, reasons after.
            # SAME TOLERANCE AS THE PER-SHOT GATE. forge-shot's IDENT_Q explicitly
            # forgives "scale, haze, warmth of light or camera angle" and asks about
            # DESIGN, because that is what canon governs. This check had no such
            # allowance, so on 2026-07-28 it ruled DRIFT on "cream in some tiles and
            # white in others" across a golden-hour tile, a bright-daylight tile and a
            # forest-shade tile — the same five shots the per-shot gate had just passed
            # against canon. Two gates asking one question with different tolerances;
            # one of them is wrong by construction. A film is LIT, and a character
            # whose fur reads warmer at sunset has not drifted.
            ans = vl_ask(sheet,
                         f"This sheet shows the same two characters ({char_desc}) "
                         f"in {len(shots)} different scenes, each lit differently and "
                         f"shot at a different distance. Ignore differences that come "
                         f"only from lighting, colour temperature, scale, haze or "
                         f"camera angle. Judge DESIGN: same species and body "
                         f"proportions, same head and ear shape, same markings. "
                         f"Reply with ONE word first — CONSISTENT or DRIFT — then ONE "
                         f"short sentence. Do not analyse the tiles one by one.")
            verdict = ans.strip().lower()
            ok = verdict.startswith("consistent")
            unparsed = not (verdict.startswith("consistent") or verdict.startswith("drift"))
            if unparsed:
                # An unanswered question is UNCHECKED, not a defect. Saying "identity
                # drifted" when the judge never ruled is the same lie as calling a
                # killed QC a pass.
                check("identity-across-scenes", False,
                      f"UNCHECKED — the judge never returned a verdict (got: "
                      f"'{ans.strip()[:90]}...'). Identity is UNVERIFIED, not failed.")
            else:
                check("identity-across-scenes", ok, ans[:200])

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
        # Match INSIDE a window around the expected time, and score by how many
        # words agree. This used to scan the whole transcript from t=0 and break on
        # the FIRST segment containing ANY single word over three characters — so a
        # repeated phrase always resolved to its earliest occurrence. On 2026-07-28
        # that reported six false failures on a cut whose audio was provably correct:
        # "Circus train? Hank, we're rolling" @17.6s matched the bird's "the circus
        # train broke down" @13.0s, and "the Wild Rescue rolls" @61.3s matched
        # "The Wild Rescue's here!" @31.0s. Verified by transcribing 3s windows at
        # each timestamp — every line was exactly where the manifest said.
        # A dialogue line is a CLAIM ABOUT A MOMENT; it has to be judged at that
        # moment, not wherever similar words first appear in the film.
        import re as _re
        for ln in lines:
            words = [w for w in _re.sub(r"[^\w\s]", " ", ln["text"].lower()).split()
                     if len(w) > 3][:4]
            need = max(1, (len(words) + 1) // 2)      # majority of the sampled words
            best, best_score = None, 0
            for s in segs:
                st = s["start"]
                en = s.get("end", st + 3.0)
                # the segment must overlap the expected moment, allowing for
                # whisper's coarse (~1s) segment boundaries
                if en < ln["t"] - TOL or st > ln["t"] + TOL + 3.0:
                    continue
                score = sum(1 for w in words if w in s["text"].lower())
                if score > best_score:
                    best, best_score = s, score
            ok = best is not None and best_score >= need
            if not ok:
                # Targeted re-listen before ruling FAIL: the full-film pass can
                # skip a whole block (see whisper_relisten docstring). A miss in
                # the global transcript is a lead, not a verdict.
                try:
                    heard = whisper_relisten(film, ln["t"]).lower()
                    rescore = sum(1 for w in words if w in heard)
                    if rescore >= need:
                        ok = True
                        check(f"audio@{ln['t']:.1f}s", True,
                              f"'{ln['text'][:30]}' expected @{ln['t']:.1f}s, heard on "
                              f"targeted re-listen ({rescore}/{len(words)} words; "
                              f"full-film transcript had a hole here)")
                        continue
                except Exception:
                    pass
            if best is None:
                det = (f"'{ln['text'][:30]}' NOT HEARD anywhere near @{ln['t']:.1f}s "
                       f"(no transcript segment covers that moment)")
            elif not ok:
                det = (f"'{ln['text'][:30]}' expected @{ln['t']:.1f}s — a segment is "
                       f"there (@{best['start']:.1f}s) but only {best_score}/{len(words)} "
                       f"words match (need {need}): heard '{best['text'].strip()[:40]}'")
            else:
                det = (f"'{ln['text'][:30]}' expected @{ln['t']:.1f}s, heard "
                       f"@{best['start']:.1f}s ({best_score}/{len(words)} words)")
            check(f"audio@{ln['t']:.1f}s", ok, det)
    except Exception as e:
        check("transcript", False, f"whisper unavailable: {e}")

    # ---- optional spec check + jury (own sections, own verdicts) ----------
    extra, extra_failed = [], False
    if args.spec or args.jury:
        try:
            extra, extra_failed = run_extras(args, film, man)
        except Exception as e:
            extra, extra_failed = ["", f"## Jury / spec: UNCHECKED — could not run: {e}"], True

    # ---- report ----------------------------------------------------------
    verdict = "PASS" if not defects else f"FAIL — {len(defects)} defect(s)"
    report = [f"# film_qc report — {film.name}", f"**Verdict: {verdict}**",
              f"Checks run: {len(passed) + len(defects)} | passed: {len(passed)} | failed: {len(defects)}",
              "", "## Defects"] + [f"- {d}" for d in defects or ["(none)"]] + \
             ["", "## Full log"] + [f"- {l}" for l in qc_log] + extra
    out = args.report or str(film.with_suffix("")) + "_qc.md"
    Path(out).write_text("\n".join(report))
    print(f"\n{verdict}\nreport: {out}")
    for x in (getattr(args, "_spec_summary", None), getattr(args, "_jury_summary", None)):
        if x:
            print(x)
    sys.exit(0 if not defects and not extra_failed else 1)


if __name__ == "__main__":
    # main() returns 2 when it refuses to start; that must reach the shell as 2,
    # not 0 (a bare main() call turned every refusal into a silent "pass").
    sys.exit(main())
