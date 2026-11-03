#!/usr/bin/env python3
"""words_align.py — word timestamps for the narration, laid out on the FINAL timeline.

WHY THIS EXISTS (promo format, 2026-10-22): the first Sitka promo laid the narration over
shots and never cut to the words. Every cut was a 0.5 s xfade at an arbitrary time, so the
picture and the voice never agreed. The promo rule now is "cuts land on word onsets", and
that needs to know, to the frame, when every word starts. This tool is the ears for that:
it writes `vo/words.json` (schema: pipeline/formats/promo/SCHEMAS.md), which
edit_to_words.py, cue_check.py and every renderer read.

What it does:
  * reads `vo/final/part000.wav, part001.wav, ...` (sorted) — one wav per narration line
  * lays them end to end on the final timeline with `--gap` seconds of silence between
    (line N+1 starts at line N's end + gap; line 1 starts at --lead, default 0)
  * transcribes each wav with mlx-whisper (word_timestamps=True, whisper-large-v3-turbo,
    same model as film_qc) or, if mlx_whisper is not importable, whisper-cli -ojf with
    ~/whisper-models/ggml-small.en.bin
  * the AUDIO is the truth: words.json lists the words actually spoken. If `script.md`
    exists, its numbered lines only fix spelling where they clearly agree with what whisper
    heard (difflib on normalized tokens), so a cue naming "Sitka" still matches when whisper
    wrote "Sitca". Where the recording and the script disagree (Sitka line 8 was re-worded
    in the booth: "with a backup catch built right in", not "with two pawls"), it WARNS and
    keeps the spoken words; a first version interpolated times for unspoken script words
    and produced zero-length fictions. Added fields (nothing renamed): words carry "heard",
    "onset", "w_start"; lines carry "dur", "script_text".
  * snaps each onset to the waveform: whisper's word starts drift 50-100 ms around pauses
    (measured on Sitka: "anywhere" 70 ms late, "it's" 90 ms early, sitting inside a breath).
    A start that sits in a quiet run moves to the run's end; a start within --snap s of a
    quiet->loud edge moves onto that edge. The last word ends at the last loud frame.
    "onset" says which one won ("energy" or "whisper"); "w_start" keeps whisper's value.
  * TIMING (2026-11-02, default --align ctc): whisper decides WHAT was said; WHEN comes from
    ctc_align.py, a fused MMS_FA + wav2vec2 CTC forced alignment of those exact words in one
    global Viterbi pass over every line (each line's words held inside its own wav), with
    manual anchors from vo/anchors.json and per-word "conf" (0-1, < 0.6 = check it). Measured
    on Kokoro speech with known word times: start error sd 21 ms vs whisper's 86-98 ms, 95%
    within 50 ms vs 46-55% (pipeline/formats/promo/06_edit/CONTEXT.md). The energy snap is
    off for ctc (it made CTC worse); whisper times + snap remain as `--align whisper` and as
    the automatic fallback if torchaudio/the models can't load (warned loudly). `--vocals`
    aligns on a Demucs vocal stem (VO with music baked in). Added fields: "conf",
    "ctc_start", "anchored"; top level "align", "align_model", "snap".
  * sanity checks: words monotonic, every word inside its wav's duration, no zero-length
    line. Prints a per-line summary.

Usage:
  ~/chatterbox-env/bin/python pipeline-tools/words_align.py projects/<film> [--gap 0.35]
        [--lead 0.0] [--engine auto|mlx|cli] [--script script.md] [--out vo/words.json]
        [--align ctc|whisper] [--anchors vo/anchors.json] [--vocals] [--snap S]

Exit code 0 = words.json written and sane; 1 = written but sanity checks failed (read
the printed problems); 2 = could not run (no wavs, no whisper) — NEVER treat 2 as a pass.
"""
import argparse
import difflib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

WHISPER_ID = "mlx-community/whisper-large-v3-turbo"
CLI_MODEL = Path.home() / "whisper-models" / "ggml-small.en.bin"
CTC_SNAP = 0.0  # CTC starts are already acoustic; energy snap measured on sitka_v3 (see docstring)


def wav_duration(path):
    try:
        with wave.open(str(path), "rb") as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", str(path)], capture_output=True, text=True)
        return float(r.stdout.strip())


def norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower()).strip("'")


def parse_script(path):
    """Numbered lines `N. [picture note] spoken text` -> {N: text}."""
    out = {}
    for raw in Path(path).read_text().splitlines():
        m = re.match(r"^\s*(\d+)[.)]\s+(.*)$", raw)
        if not m:
            continue
        text = re.sub(r"\[[^\]]*\]", "", m.group(2)).strip()
        text = re.sub(r"\s+", " ", text)
        if text:
            out[int(m.group(1))] = text
    return out


def words_mlx(wav, prompt=None):
    import mlx_whisper
    res = mlx_whisper.transcribe(str(wav), path_or_hf_repo=WHISPER_ID, word_timestamps=True,
                                 language="en", initial_prompt=prompt,
                                 condition_on_previous_text=False)
    out = []
    for seg in res.get("segments", []):
        for w in seg.get("words", []):
            t = w["word"].strip()
            if not t:
                continue
            if t.startswith("-") and out:  # "Ninety" "-three" -> "Ninety-three"
                out[-1]["word"] += t
                out[-1]["end"] = float(w["end"])
                continue
            out.append({"word": t, "start": float(w["start"]), "end": float(w["end"]),
                        "p": float(w.get("probability", 0.0))})
    return out


def words_cli(wav, prompt=None):
    exe = shutil.which("whisper-cli")
    if not exe or not CLI_MODEL.exists():
        raise RuntimeError("whisper-cli or ggml-small.en.bin missing")
    tmp = Path(tempfile.mkdtemp(prefix="wa_"))
    w16 = tmp / "in.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-ar", "16000", "-ac", "1",
                    str(w16)], check=True)
    cmd = [exe, "-m", str(CLI_MODEL), "-f", str(w16), "-ojf", "-of", str(tmp / "out"),
           "-l", "en", "-np"]
    if prompt:
        cmd += ["--prompt", prompt]
    subprocess.run(cmd, check=True, capture_output=True)
    data = json.loads((tmp / "out.json").read_text())
    out = []
    for seg in data.get("transcription", []):
        for tok in seg.get("tokens", []):
            txt = tok.get("text", "")
            if txt.startswith("[_") or not txt.strip():
                continue
            a = tok["offsets"]["from"] / 1000.0
            b = tok["offsets"]["to"] / 1000.0
            if txt.startswith(" ") or not out:
                out.append({"word": txt.strip(), "start": a, "end": b})
            else:  # sub-word token continues the previous word
                out[-1]["word"] += txt
                out[-1]["end"] = b
    shutil.rmtree(tmp, ignore_errors=True)
    return [w for w in out if norm(w["word"])]


def align_to_script(script_text, heard, dur):
    """The AUDIO is the truth: words.json holds the words actually spoken, with whisper's
    times. The script only fixes spelling where it clearly agrees (Sitca -> Sitka).
    Returns (words, matched, mismatches). Script words that are not in the audio are
    reported, never invented a time for (a cut on a word nobody says is a lie)."""
    toks = script_text.split()
    sn = [norm(t) for t in toks]
    hn = [norm(h["word"]) for h in heard]
    out = [{"word": re.sub(r"^[^\w']+|[^\w']+$", "", h["word"]) or h["word"],
            "start": h["start"], "end": h["end"], "heard": h["word"]} for h in heard]
    matched, mism = 0, []
    sm = difflib.SequenceMatcher(a=sn, b=hn, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                out[j1 + k]["word"] = re.sub(r"^[^\w']+|[^\w']+$", "", toks[i1 + k]) or toks[i1 + k]
                matched += 1
            continue
        if tag == "replace" and (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1):
                if difflib.SequenceMatcher(a=sn[i1 + k], b=hn[j1 + k]).ratio() >= 0.6:
                    out[j1 + k]["word"] = re.sub(r"^[^\w']+|[^\w']+$", "", toks[i1 + k])
                    matched += 1
                else:
                    mism.append(f"script '{toks[i1 + k]}' / spoken '{heard[j1 + k]['word']}'")
            continue
        said = " ".join(h["word"] for h in heard[j1:j2])
        wrote = " ".join(toks[i1:i2])
        if wrote or said:
            mism.append(f"script '{wrote}' / spoken '{said}'")
    return out, matched, mism


def envelope(wav, hop=0.01):
    """Per-10ms loudness in dB relative to the wav's peak (mono mixdown)."""
    import numpy as np
    with wave.open(str(wav), "rb") as w:
        sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(w.getnframes())
    dt = {2: np.int16, 4: np.int32}.get(sw)
    if dt is None:
        return None
    x = np.frombuffer(raw, dtype=dt).astype(np.float64)
    if ch > 1:
        x = x.reshape(-1, ch).mean(1)
    f = max(1, int(sr * hop))
    n = len(x) // f
    r = np.sqrt((x[:n * f].reshape(n, f) ** 2).mean(1) + 1e-9)
    return 20 * np.log10(r / r.max())


def snap_onsets(lw, db, dur, quiet_db=-35.0, snap=0.12, hop=0.01, source="whisper"):
    """Move word starts onto the real attack in the waveform (see docstring). `source` names
    where the unsnapped start came from ("whisper" or "ctc"); w_start keeps whisper's value."""
    if db is None or not lw:
        return lw
    loud = db > quiet_db
    n = len(loud)
    edges = [k for k in range(1, n) if loud[k] and not loud[k - 1]]  # quiet->loud frames
    used = set()
    prev = -1.0
    for w in lw:
        w.setdefault("w_start", round(w["start"], 3))
        w["onset"] = source
        if snap <= 0:
            prev = w["start"]
            continue
        floor = prev + 0.05  # never snap onto or before the previous word
        k = int(round(w["start"] / hop))
        cand = None
        if 0 <= k < n and not loud[k]:
            j = k
            while j < n and not loud[j]:
                j += 1
            if j < n and (j - k) * hop <= 0.25:
                cand = j
        if cand is None:
            near = [e for e in edges if abs(e * hop - w["start"]) <= snap and e not in used]
            if near:
                cand = min(near, key=lambda e: abs(e * hop - w["start"]))
        if cand is not None and cand not in used and cand * hop >= floor:
            w["start"] = cand * hop
            w["onset"] = "energy"
            used.add(cand)
        prev = w["start"]
    for a, b in zip(lw, lw[1:]):  # keep order and make ends meet the next start
        if b["start"] < a["start"]:
            b["start"] = a["start"]
        a["end"] = min(max(a["end"], a["start"]), b["start"])
        if a["end"] - a["start"] < 0.03:  # whisper sometimes gives 0-length words
            a["end"] = b["start"]
    last_loud = max((k for k in range(n) if loud[k]), default=None)
    if last_loud is not None:
        lw[-1]["end"] = min(dur, max(lw[-1]["start"], (last_loud + 1) * hop))
    return lw


def ctc_refine(items, film, anchors_path, vocals, log=print):
    """Replace whisper's word times with the fused CTC forced alignment (ctc_align.py), one
    global pass over every line laid on the final timeline. Mutates items' "lw" in place
    (line-local seconds). Raises if the models can't load; the caller falls back."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import ctc_align as C
    segs, whisper, flat = [], [], []
    for it in items:
        src = C.vocal_stem(it["wav"]) if vocals else it["wav"]
        segs.append({"audio": C.load16k(src), "t0": it["start"], "words": [w["word"] for w in it["lw"]]})
        whisper += [it["start"] + w["start"] for w in it["lw"]]
        flat += [(it["line"], w["word"]) for w in it["lw"]]
    anchors, po = C.load_anchors(anchors_path, flat)
    if anchors:
        log(f"[words_align] {len(anchors)} manual anchor(s) from {anchors_path}")
    res = C.align_segments(segs, anchors=anchors, whisper=whisper, pron_override=po, log=log)
    C.unload()
    k = 0
    for it in items:
        for w in it["lw"]:
            r = res[k]
            k += 1
            w["w_start"] = round(w["start"], 3)
            if r is None:  # nothing pronounceable ("—"): keep whisper's time, say so
                w["conf"] = 0.3
                continue
            w["start"] = max(0.0, r["start"] - it["start"])
            w["end"] = max(w["start"], r["end"] - it["start"])
            w["ctc_start"] = r["start"]
            w["conf"] = r["conf"]
            if r["anchored"]:
                w["anchored"] = True


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("film", help="projects/<film> folder")
    ap.add_argument("--gap", type=float, default=0.35)
    ap.add_argument("--lead", type=float, default=0.0, help="silence before line 1")
    ap.add_argument("--engine", choices=["auto", "mlx", "cli"], default="auto")
    ap.add_argument("--script", default=None, help="default: <film>/script.md if present")
    ap.add_argument("--out", default="vo/words.json")
    ap.add_argument("--align", choices=["ctc", "whisper"], default="ctc",
                    help="ctc = fused MMS_FA+wav2vec2 forced alignment (default); whisper = the old path")
    ap.add_argument("--snap", type=float, default=None,
                    help="onset snap window, s (0 = off; default 0.12 whisper, %.2f ctc)" % CTC_SNAP)
    ap.add_argument("--anchors", default=None, help="manual anchors (default: <film>/vo/anchors.json)")
    ap.add_argument("--vocals", action="store_true", help="align on the Demucs vocal stem (VO over music)")
    a = ap.parse_args()

    film = Path(a.film).resolve()
    wavs = sorted((film / "vo" / "final").glob("part*.wav"))
    if not wavs:
        print(f"[words_align] no vo/final/part*.wav in {film}", file=sys.stderr)
        sys.exit(2)
    spath = Path(a.script) if a.script else film / "script.md"
    if a.script and not spath.is_absolute():
        spath = film / a.script
    script = parse_script(spath) if spath.exists() else {}
    # promo_voice.py may have re-worded a line whisper kept mishearing: what was SPOKEN wins
    vj = film / "vo" / "voice.json"
    if vj.exists() and not a.script:
        for ln in json.loads(vj.read_text()).get("lines", []):
            if ln.get("spoken") and ln.get("line") in script:
                script[ln["line"]] = re.sub(r"\s+", " ", ln["spoken"]).strip()

    engine = a.engine
    if engine == "auto":
        try:
            import mlx_whisper  # noqa: F401
            engine = "mlx"
        except Exception:
            engine = "cli"
    fn = words_mlx if engine == "mlx" else words_cli
    print(f"[words_align] {len(wavs)} wavs, engine={engine}, align={a.align}, "
          f"script={'yes' if script else 'no'}, gap={a.gap}")

    # ---- pass 1: WHAT was said (whisper + script spelling), and where each line sits
    lines, words, problems, warnings, items = [], [], [], [], []
    t = a.lead
    for n, wav in enumerate(wavs):
        line_no = n + 1
        dur = wav_duration(wav)
        text = script.get(line_no)
        try:
            heard = fn(wav, prompt=text)
        except Exception as e:
            print(f"[words_align] transcription failed on {wav.name}: {e}", file=sys.stderr)
            sys.exit(2)
        if text:
            lw, matched, mism = align_to_script(text, heard, dur)
            for m in mism:
                warnings.append(f"line {line_no}: VO differs from script.md: {m}")
        else:
            lw = [dict(h, heard=h["word"]) for h in heard]
            matched = len(lw)
        for w, h in zip(lw, heard):
            w["p"] = h.get("p")
        items.append({"line": line_no, "wav": wav, "dur": dur, "start": round(t, 3), "lw": lw,
                      "matched": matched, "script_text": text,
                      "text": " ".join(h["word"] for h in heard)})
        t = t + dur + a.gap

    # ---- pass 2: WHEN it was said. Fused CTC forced alignment of those words, one global pass
    align_used = "whisper"
    if a.align == "ctc" and any(it["lw"] for it in items):
        anchors = Path(a.anchors) if a.anchors else film / "vo" / "anchors.json"
        if a.anchors and not anchors.is_absolute():
            anchors = film / a.anchors
        try:
            ctc_refine(items, film, anchors, a.vocals)
            align_used = "ctc"
        except Exception as e:
            warnings.append(f"CTC alignment could not run ({type(e).__name__}: {e}); FELL BACK to whisper "
                            f"word times (--align whisper path). Timing is the old, less exact kind.")
            for it in items:
                for w in it["lw"]:
                    w.pop("w_start", None)
    snap = a.snap if a.snap is not None else (CTC_SNAP if align_used == "ctc" else 0.12)

    for it in items:
        line_no, wav, dur, lw = it["line"], it["wav"], it["dur"], it["lw"]
        if align_used == "whisper":
            for w in lw:  # whisper's own word probability is the only confidence we have
                w["conf"] = round(float(w.get("p") or 0.0), 2)
        lw = snap_onsets(lw, envelope(wav), dur, snap=snap, source=align_used)
        n_snapped = sum(1 for w in lw if w.get("onset") == "energy")
        start = it["start"]
        end = round(start + dur, 3)
        lines.append({"line": line_no, "wav": str(wav.relative_to(film)), "start": start,
                      "end": end, "dur": round(dur, 3), "text": it["text"],
                      "script_text": it["script_text"]})
        prev = -1.0
        for w in lw:
            ws, we = max(0.0, w["start"]), min(dur, w["end"])
            if ws < prev - 1e-6:
                problems.append(f"line {line_no}: '{w['word']}' at {ws:.2f}s goes backwards")
            if ws > dur + 1e-3 or we < 0:
                problems.append(f"line {line_no}: '{w['word']}' outside the wav ({dur:.2f}s)")
            prev = ws
            d = {"i": len(words), "line": line_no, "word": w["word"],
                 "start": round(start + ws, 3), "end": round(start + max(we, ws), 3),
                 "heard": w.get("heard"), "onset": w.get("onset", align_used),
                 "w_start": round(start + w.get("w_start", w["start"]), 3),
                 "conf": w.get("conf")}
            if "ctc_start" in w:
                d["ctc_start"] = round(w["ctc_start"], 3)
            if w.get("anchored"):
                d["anchored"] = True
            words.append(d)
        for w in lw:
            if w["end"] - w["start"] < 0.03:
                warnings.append(f"line {line_no}: '{w['word']}' has ~0 length (whisper collapsed it); "
                                f"its onset is unreliable, don't put a cut cue on it")
            if align_used == "ctc" and (w.get("conf") or 0) < 0.6:
                warnings.append(f"line {line_no}: '{w['word']}' low alignment confidence {w.get('conf')}; "
                                f"check it before cueing a cut on it (or pin it in vo/anchors.json)")
        if not lw:
            problems.append(f"line {line_no}: no words heard")
        first = lw[0]["start"] if lw else 0
        last = lw[-1]["end"] if lw else 0
        print(f"  line {line_no:2d}  {start:7.2f}-{end:7.2f}  dur {dur:5.2f}  words {len(lw):2d} "
              f"(matched {it['matched']}, snapped {n_snapped})  speech {first:4.2f}-{last:4.2f}  | {it['text'][:60]}")

    out = film / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"gap": a.gap, "lead": a.lead, "engine": engine,
                               "model": WHISPER_ID if engine == "mlx" else str(CLI_MODEL),
                               "align": align_used,
                               "align_model": ("fused CTC: torchaudio MMS_FA + WAV2VEC2_ASR_LARGE_LV60K_960H, "
                                               "global Viterbi" + (", demucs vocals" if a.vocals else ""))
                               if align_used == "ctc" else "whisper word timestamps",
                               "snap": snap, "lines": lines, "words": words}, indent=1))
    print(f"[words_align] wrote {out} ({len(words)} words, timeline {lines[-1]['end']:.2f}s, align={align_used})")
    if warnings:
        print("[words_align] WARN (words.json follows the AUDIO; fix script.md or re-record):")
        for w in warnings:
            print("   ", w)
    if problems:
        print("[words_align] PROBLEMS:")
        for p in problems:
            print("   ", p)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
