#!/usr/bin/env python3
"""promo_gates.py — promo stage 09: the gates the FINISHED promo must pass before anyone watches it.

The Sitka QC log (sitka-video/PRODUCTION.md §9, 2026-10-22), made a tool. On final/<film>.mp4:
  1. WORDS: mlx-whisper (large-v3-turbo, word timestamps, NO script prompt) on the FINAL mix vs
     the narration as spoken (vo/voice.json "spoken", else script.md), word for word, in one pass
     over the whole film. A miss is re-heard line by line (each line's window of the same final
     mix): missed there too = FAIL (music or an SFX masking a word); heard there = WARN, named in
     the report for the full watch (whisper's long-context pass flips borderline words). Also the median
     offset of the heard words vs the planned vo/words.json times (WARN > 120 ms).
  2. LOUDNESS: ebur128 integrated within promo.json gates.lufs +/- lufs_tol (default -16 +/- 1),
     true peak <= gates.true_peak_max (-1 dBFS). Voice stem vs ducked-music stem (final/_vo.wav vs
     final/_music.wav from promo_mix): >= 10 dB apart, WARN under 10, FAIL under 6.
  3. ENDING LANDS: the end-card slam starts AFTER the last heard word ends (never masks it), the
     last line's final words are heard in the last 12 s, the sting rings (RMS after the slam
     > -30 dBFS) and the card itself is on screen (dark frame with bright type).
  4. DESIGN: every shot the EDL uses has design_check verdict "pass" in manifest.json; "fail" =
     FAIL, null/"unchecked" = UNCHECKED (never a pass, frozen rule 22).
  5. FRAME STRIPS: final/strips/line<N>.jpg (8 frames across each narration line) and
     final/strips/ev_<kind>_<t>.jpg (frames -2..+3 around every title, callout, overlay and the
     slam). Made for the agent's eyes; they are NOT verification. The full start-to-finish watch
     and stages/09_gates/known_defects.md are (frozen rule 30).
Writes final/promo_gates_report.md + .json.

Usage:  ~/chatterbox-env/bin/python pipeline-tools/promo_gates.py projects/<film> [--film final/x.mp4]
Exit 0 = no FAIL (UNCHECKED/WARN listed); 1 = a FAIL; 2 = could not run.
"""
from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from promo_common import WHISPER_ID, compare_words, ebur128, load_promo, norm_words, parse_script, run  # noqa: E402


def heard_words(audio: Path) -> tuple[str, list[dict]]:
    import mlx_whisper
    res = mlx_whisper.transcribe(str(audio), path_or_hf_repo=WHISPER_ID, language="en", word_timestamps=True,
                                 condition_on_previous_text=False)
    ws = [{"w": w["word"].strip(), "s": float(w["start"]), "e": float(w["end"])}
          for seg in res.get("segments", []) for w in seg.get("words", []) if w["word"].strip()]
    return res.get("text", "").strip(), ws


def frame(mp4: Path, t: float, out: Path, w=480) -> None:
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, t):.3f}", "-i", mp4, "-frames:v", "1",
         "-vf", f"scale={w}:-2", out])


def strip(mp4: Path, times: list[float], out: Path, w=480) -> None:
    tmp = Path(tempfile.mkdtemp(prefix="strip_"))
    files = []
    for k, t in enumerate(times):
        f = tmp / f"{k:02d}.png"
        frame(mp4, t, f, w)
        files.append(f)
    args = []
    for f in files:
        args += ["-i", str(f)]
    run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex",
         "".join(f"[{i}]" for i in range(len(files))) + f"hstack=inputs={len(files)}", out])
    for f in files:
        f.unlink()
    tmp.rmdir()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("film_dir")
    ap.add_argument("--film", default=None)
    a = ap.parse_args()
    film = Path(a.film_dir).resolve()
    cfg = load_promo(film)
    g = cfg["gates"]
    mp4 = Path(a.film) if a.film else film / "final" / f"{film.name}.mp4"
    if not mp4.is_absolute():
        mp4 = film / mp4
    try:
        edl = json.loads((film / "edl.json").read_text())
        words_plan = json.loads((film / "vo" / "words.json").read_text())
    except Exception as e:  # noqa: BLE001
        print(f"[gates] missing edl.json / vo/words.json ({e})", file=sys.stderr)
        return 2
    if not mp4.exists():
        print(f"[gates] no film at {mp4}", file=sys.stderr)
        return 2
    rows = []   # (gate, verdict, detail)

    def add(gate, verdict, detail):
        rows.append((gate, verdict, detail))
        print(f"  {verdict:9} {gate}: {detail}")

    # ---- 1. words, on the FINAL mix
    vstate = film / "vo" / "voice.json"
    spoken = {ln["line"]: ln.get("spoken") or ln["text"] for ln in json.loads(vstate.read_text())["lines"]} \
        if vstate.exists() else {ln["line"]: ln["text"] for ln in parse_script(film / "script.md")}
    expected = " ".join(spoken[k] for k in sorted(spoken))
    wav = film / "final" / "_gates_audio.wav"
    run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-vn", "-ac", "1", "-ar", "16000", wav])
    text, hw = heard_words(wav)
    got, tot, notes = compare_words(expected, text)
    if got == tot and not notes:
        add("words (final mix vs script)", "PASS", f"{got}/{tot} words matched in one pass over the whole film")
    else:
        # Whisper's whole-film pass flips borderline words on tiny perturbations (sitka_demo: "light pole"
        # read as "light pull" in the full mix, "pole" in the clean stem, in vo+music, in vo+fx and in the
        # line's own window). So a miss is re-heard line by line, still on the FINAL mix: a word heard in
        # neither pass is a FAIL; heard only in its line window is a WARN for the human watch.
        import soundfile as sf
        x, sr = sf.read(str(wav))
        line_bad = []
        for ln in words_plan["lines"]:
            a0, a1 = max(0.0, float(ln["start"]) - 0.3), float(ln["end"]) + 0.3
            seg = film / "final" / "_gates_line.wav"
            sf.write(str(seg), x[int(a0 * sr):int(a1 * sr)], sr)
            ltxt, _ = heard_words(seg)
            seg.unlink()
            g2, t2, n2 = compare_words(spoken[ln["line"]], ltxt)
            if g2 != t2 or n2:
                line_bad.append(f"line {ln['line']}: {'; '.join(n2)}")
        if line_bad:
            add("words (final mix vs script)", "FAIL", f"whole-film pass {got}/{tot} ({'; '.join(notes[:4])}); "
                f"line-by-line pass also missed: {' | '.join(line_bad)}")
        else:
            add("words (final mix vs script)", "WARN", f"whole-film pass {got}/{tot} ({'; '.join(notes[:4])}); every "
                "line heard word for word in its own window of the final mix. Listen for it in the full watch.")
    # timing vs plan: align normalized heard words to planned words in order
    import difflib
    plan = [(w2, float(w["start"])) for w in words_plan["words"] for w2 in norm_words(w["word"])]
    hn = [(w2, h["s"]) for h in hw for w2 in norm_words(h["w"])]
    sm = difflib.SequenceMatcher(a=[p[0] for p in plan], b=[x[0] for x in hn], autojunk=False)
    offs = [abs(hn[b.b + k][1] - plan[b.a + k][1]) for b in sm.get_matching_blocks() for k in range(b.size)]
    if offs:
        med = statistics.median(offs)
        add("word timing vs plan", "PASS" if med <= 0.12 else "WARN", f"median offset {med * 1000:.0f} ms over {len(offs)} words")

    # ---- 2. loudness
    lo = ebur128(mp4)
    I, TP = lo.get("I"), lo.get("TP")
    if I is None:
        add("loudness", "UNCHECKED", "ebur128 unreadable")
    else:
        okI = abs(I - g["lufs"]) <= g["lufs_tol"]
        okT = TP is None or TP <= g["true_peak_max"]
        add("loudness", "PASS" if okI and okT else "FAIL",
            f"integrated {I:.1f} LUFS (target {g['lufs']}+/-{g['lufs_tol']}), true peak {TP} dBFS "
            f"(max {g['true_peak_max']}), LRA {lo.get('LRA')}")
    vs, ms = film / "final" / "_vo.wav", film / "final" / "_music.wav"
    if vs.exists() and ms.exists():
        slam = float(edl["endcard"]["rec_in"]) if edl.get("endcard") else float(edl["dur"])
        Iv, Im = ebur128(vs, 0, slam).get("I"), ebur128(ms, 0, slam).get("I")
        if Iv is not None and Im is not None:
            gap = Iv - Im
            add("voice over music", "PASS" if gap >= 10 else ("WARN" if gap >= 6 else "FAIL"),
                f"voice stem {Iv:.1f} LUFS, ducked music {Im:.1f} LUFS: {gap:.1f} dB apart (want >= 10)")
    else:
        add("voice over music", "UNCHECKED", "no final/_vo.wav + final/_music.wav stems (promo_mix.py writes them)")

    # ---- 3. ending lands
    ec = edl.get("endcard")
    if not ec:
        add("ending", "FAIL", "no end card in edl.json (promo.json endcard.dur > 0)")
    else:
        slam = float(ec["rec_in"])
        last_heard = max((h["e"] for h in hw), default=0.0)
        add("slam after last word", "PASS" if slam >= last_heard - 0.03 else "FAIL",
            f"last heard word ends {last_heard:.2f}s, slam {slam:.2f}s ({(slam - last_heard) * 1000:+.0f} ms)")
        tail_txt = " ".join(h["w"] for h in hw if h["s"] >= float(edl["dur"]) - 14)
        last_line = spoken[max(spoken)]
        want = norm_words(last_line)[-3:]
        have = norm_words(tail_txt)
        ok_tail = any(have[i:i + len(want)] == want for i in range(len(have)))
        add("last words heard", "PASS" if ok_tail else "FAIL",
            f"want '{' '.join(want)}' in the last seconds; heard '{tail_txt[-80:]}'")
        import soundfile as sf
        mix = film / "final" / "mix.wav"
        src = mix if mix.exists() else wav
        x, sr = sf.read(str(src), always_2d=True)
        seg = x[int(slam * sr):int((slam + 2.0) * sr)]
        rms = 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9) if len(seg) else -120
        add("sting rings", "PASS" if rms > -30 else "FAIL", f"RMS {rms:.1f} dBFS in the 2 s after the slam")
        card = film / "final" / "_endcard_probe.png"
        frame(mp4, min(slam + 1.5, float(edl["dur"]) - 0.1), card, 480)
        from PIL import Image
        im = np.asarray(Image.open(card).convert("L"), dtype=float)
        dark, bright = (im < 60).mean(), (im > 200).mean()
        add("end card on screen", "PASS" if dark > 0.6 and bright > 0.004 else "FAIL",
            f"{dark * 100:.0f}% dark, {bright * 100:.1f}% bright type at {slam + 1.5:.2f}s")
        card.unlink()

    # ---- 4. design verdicts of the shots actually used
    man = json.loads((film / "manifest.json").read_text()) if (film / "manifest.json").exists() else {}
    verdict = {c["cid"]: (c.get("checks") or {}).get("design") for c in man.get("candidates", [])}
    used = sorted({s["cid"] for s in edl["shots"]})
    fails = [c for c in used if verdict.get(c) == "fail"]
    unch = [c for c in used if verdict.get(c) not in ("pass", "fail", "n/a")]
    if fails:
        add("design (shots in the cut)", "FAIL", f"{len(fails)} used shot(s) failed design_check: {', '.join(fails)}")
    elif unch:
        add("design (shots in the cut)", "UNCHECKED", f"{len(unch)} of {len(used)} used shots never judged: {', '.join(unch)}")
    else:
        add("design (shots in the cut)", "PASS", f"all {len(used)} used shots passed design_check")

    # ---- 5. frame strips for the agent's eyes
    sd = film / "final" / "strips"
    sd.mkdir(parents=True, exist_ok=True)
    for old in sd.glob("*.jpg"):
        old.unlink()
    fps = float(edl["fps"])
    for ln in words_plan["lines"]:
        t0, t1 = float(ln["start"]), float(ln["end"])
        strip(mp4, [t0 + (t1 - t0) * k / 7 for k in range(8)], sd / f"line{ln['line']:02d}.jpg", 320)
    evs = [("title", t["rec_in"]) for t in edl.get("titles", [])] + \
          [("overlay", o["rec_in"]) for o in edl.get("overlays", [])] + \
          ([("slam", ec["rec_in"])] if ec else [])
    cpath = film / "callouts.json"
    evs += [("callout", c["rec_in"]) for c in (json.loads(cpath.read_text()).get("callouts", []) if cpath.exists() else [])]
    for kind, t in evs:
        strip(mp4, [float(t) + k / fps for k in (-2, 0, 1, 3)], sd / f"ev_{kind}_{float(t):06.2f}.jpg", 400)
    add("frame strips", "REVIEW", f"{len(list(sd.glob('*.jpg')))} strips in final/strips/ (look at every one; "
        "then watch the whole cut and write stages/09_gates/known_defects.md)")
    wav.unlink(missing_ok=True)

    counts = {k: sum(1 for r in rows if r[1] == k) for k in ("PASS", "FAIL", "WARN", "UNCHECKED", "REVIEW")}
    head = (f"# Promo gates: {film.name}\n\nFilm: `final/{mp4.name}`, {float(edl['dur']):.2f} s. "
            f"PASS {counts['PASS']}, FAIL {counts['FAIL']}, WARN {counts['WARN']}, UNCHECKED {counts['UNCHECKED']}.\n\n"
            "| gate | verdict | detail |\n|---|---|---|\n")
    (film / "final" / "promo_gates_report.md").write_text(
        head + "".join(f"| {r[0]} | {r[1]} | {r[2].replace('|', '/')} |\n" for r in rows)
        + f"\nWhisper heard (final mix):\n\n> {text}\n")
    (film / "final" / "promo_gates_report.json").write_text(json.dumps(
        {"film": mp4.name, "counts": counts, "rows": [{"gate": r[0], "verdict": r[1], "detail": r[2]} for r in rows],
         "heard": text}, indent=1))
    print(f"[gates] PASS {counts['PASS']}  FAIL {counts['FAIL']}  WARN {counts['WARN']}  "
          f"UNCHECKED {counts['UNCHECKED']}  -> final/promo_gates_report.md")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
