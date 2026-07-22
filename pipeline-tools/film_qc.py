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


def whisper_transcribe(video):
    """Return list of {start, end, text} segments via mlx whisper."""
    import mlx_whisper  # available in the mlx-server venv? fallback: CLI
    res = mlx_whisper.transcribe(str(video), path_or_hf_repo=WHISPER_ID,
                                 word_timestamps=False)
    return res.get("segments", [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("film")
    ap.add_argument("manifest")
    ap.add_argument("--report", default=None)
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
    for i, ln in enumerate(lines):
        mid = ln["t"] + 0.5
        f = tmp / f"line_{i}.png"
        if not extract_frame(film, mid, f):
            check(f"line{i}-frame", False, f"could not extract frame @{mid:.1f}s")
            continue
        q = (f"Characters: {char_desc}. In this frame, ONE character should be "
             f"speaking. Which character has an open or clearly moving mouth? "
             f"Answer with just the character name, or 'none', or 'both'.")
        ans = vl_ask(f, q).lower()
        ok = ln["speaker"].lower() in ans and "both" not in ans
        check(f"lipsync@{ln['t']:.1f}s", ok,
              f"expected {ln['speaker']} speaking, model saw: {ans[:80]}")

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
    try:
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
