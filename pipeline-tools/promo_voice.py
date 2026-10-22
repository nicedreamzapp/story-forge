#!/usr/bin/env python3
"""promo_voice.py — promo stage 02: the narration, voiced, finished, and HEARD back before use.

WHY THIS EXISTS (promo format, 2026-10-22, the Sitka recipe): narration is Matt's ChatterBox
clone (matt2) with a fixed finish chain, and every line is transcribed AFTER the finish because
the pitch shift can change a word (Sitka line 5 came back "cam chair" instead of "camp chair";
a retake fixed it). A line is only used when whisper hears every word of it.

Per script.md line (promo_common.parse_script; `say:` = what the TTS reads, `alt:` = a
re-wording allowed when the line keeps failing):
  1. ChatterBox batch render (one model load for every line; Song Forge must be idle);
  2. finish: silenceremove both ends (-45 dB) -> asetrate=SR*pitch,aresample,atempo=1/pitch
     -> EQ (promo.json voice.eq, default +3 dB @180 Hz, -3 dB @5 kHz) -> 0.25 s pad
     -> loudnorm I=-16 TP=-1.5 LRA=11 -> 48 kHz mono  => vo/final/part<NNN>.wav (line order);
  3. mlx-whisper (large-v3-turbo, NO script prompt, so it cannot be primed into agreeing)
     vs the expected words (promo_common.compare_words: numbers spelled out, 'and' ignored);
  4. mismatch -> `retakes` more takes of that line (default 3), first full match wins;
  5. still wrong -> AUTO-REWORD: each `alt:` line, then automatic variants (numbers written
     out as words; the misheard word set off with commas), 2 takes each. A reworded line is
     recorded in vo/voice.json "spoken", and every later gate checks against what was SPOKEN;
  6. nothing matches -> exit 1 with the line, what was expected and what was heard.

State: vo/voice.json {"lines": [{"line", "text", "spoken", "wav", "heard", "match", "take",
"reworded", "hash"}]}. A line whose text/say/voice settings are unchanged and whose wav exists
is not re-rendered (pass --force to redo all).

Usage:  ~/chatterbox-env/bin/python pipeline-tools/promo_voice.py projects/<film> [--force] [--only 2]
Exit 0 = every line voiced and heard right; 1 = a line failed (read the table); 2 = couldn't run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from promo_common import (CHATTERBOX_BATCH, CHATTERBOX_PY, WHISPER_ID, _say_int, compare_words,  # noqa: E402
                          load_promo, norm_words, parse_script, run, song_forge_busy)


def finish(src: Path, dst: Path, v: dict) -> None:
    sr = int(run(["ffprobe", "-v", "error", "-show_entries", "stream=sample_rate", "-of", "csv=p=0", src]).stdout.split()[0])
    p = float(v.get("pitch", 0.92))
    trim = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,"
            "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse")
    pitch = f"asetrate={int(round(sr * p))},aresample={sr},atempo={1 / p:.6f}" if abs(p - 1) > 1e-3 else "anull"
    eq = ",".join(f"equalizer=f={f}:t=q:w=1:g={g}" for f, g in v.get("eq", []))
    chain = ",".join(x for x in (trim, pitch, eq, "apad=pad_dur=0.25",
                                 f"loudnorm=I={v.get('lufs', -16)}:TP=-1.5:LRA=11", "aresample=48000") if x)
    dst.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-v", "error", "-i", src, "-af", chain, "-ar", "48000", "-ac", "1", dst])


def tts(texts: list[str], out_dir: Path, v: dict) -> list[Path]:
    """One ChatterBox load for every text; returns part000.wav.. in order (missing = failed)."""
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    env = dict(os.environ, CHATTERBOX_EXAG=str(v["exaggeration"]), CHATTERBOX_CFG=str(v["cfg"]))
    req = json.dumps({"character": v["character"], "lines": texts, "out_dir": str(out_dir)})
    r = subprocess.run([str(CHATTERBOX_PY), str(CHATTERBOX_BATCH)], input=req, text=True,
                       capture_output=True, env=env, timeout=3600)
    if r.returncode != 0 and not any(out_dir.glob("part*.wav")):
        raise RuntimeError("chatterbox-batch failed:\n" + "\n".join(r.stderr.strip().splitlines()[-8:]))
    return [out_dir / f"part{i:03d}.wav" for i in range(len(texts))]


def hear(wav: Path) -> str:
    import mlx_whisper
    res = mlx_whisper.transcribe(str(wav), path_or_hf_repo=WHISPER_ID, language="en",
                                 condition_on_previous_text=False)
    return res.get("text", "").strip()


def auto_alts(text: str, notes: list[str]) -> list[str]:
    """Re-wordings to try when retakes fail: numbers as words, then the misheard words set off."""
    alts = []
    spelled = re.sub(r"\d+", lambda m: _say_int(int(m.group(0))), text.replace(",", ", ").replace("  ", " "))
    if spelled != text:
        alts.append(spelled)
    for n in notes:
        m = re.match(r"expected '([^']+)' heard", n)
        if m and m.group(1) != "-":
            frag = m.group(1).split()[0]
            pat = re.compile(r"\b(" + re.escape(frag) + r")\b", re.I)
            if pat.search(text):
                alt = pat.sub(r", \1,", text, count=1)
                alt = re.sub(r"\s+,", ",", alt)
                alt = re.sub(r",\s*([,.!?])", r"\1", alt)
                alts.append(re.sub(r"^,\s*", "", alt))
    return [a for i, a in enumerate(alts) if a not in alts[:i]]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("film")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", type=int, action="append", help="script line number(s) to redo")
    a = ap.parse_args()
    film = Path(a.film).resolve()
    cfg = load_promo(film)
    v = cfg["voice"]
    lines = parse_script(film / "script.md") if (film / "script.md").exists() else []
    if not lines:
        print("[voice] script.md has no numbered lines", file=sys.stderr)
        return 2
    state_p = film / "vo" / "voice.json"
    state = {ln["line"]: ln for ln in (json.loads(state_p.read_text()).get("lines", []) if state_p.exists() else [])}
    vkey = json.dumps({k: v[k] for k in ("character", "exaggeration", "cfg", "pitch", "eq", "lufs")}, sort_keys=True)

    todo = []
    for idx, ln in enumerate(lines):
        h = hashlib.sha1((ln["text"] + "|" + (ln["say"] or "") + "|" + "|".join(ln["alts"]) + "|" + vkey).encode()).hexdigest()[:12]
        wav = film / "vo" / "final" / f"part{idx:03d}.wav"
        old = state.get(ln["line"])
        ln.update(idx=idx, hash=h, wav=wav)
        fresh = old and old.get("hash") == h and old.get("match") and wav.exists()
        if a.force or (a.only and ln["line"] in a.only) or not fresh:
            todo.append(ln)
    if not todo:
        print(f"[voice] all {len(lines)} lines already voiced and heard right (vo/voice.json)")
        return 0
    busy, why = song_forge_busy()
    if busy:
        print(f"[voice] Song Forge is busy ({why}); customer jobs outrank renders. Try again when it is idle.",
              file=sys.stderr)
        return 2
    print(f"[voice] {len(todo)} line(s) to voice with {v['character']} (exag {v['exaggeration']}, cfg {v['cfg']}, "
          f"pitch {v['pitch']}); Song Forge {why}")

    raw = film / "vo" / "raw"
    results = {}

    def attempt(batch: list[tuple[dict, str]], tag: str) -> None:
        """render every (line, text) in one load, finish, hear, keep the first full match per line."""
        wavs = tts([t for _, t in batch], raw / tag, v)
        for (ln, text), w in zip(batch, wavs):
            if ln["line"] in results and results[ln["line"]]["match"]:
                continue
            if not w.exists():
                print(f"  line {ln['line']} {tag}: TTS produced nothing")
                continue
            fin = raw / tag / f"fin_{w.name}"
            finish(w, fin, v)
            heard = hear(fin)
            expected = text if text != ln.get("say") else ln["text"]
            got, tot, notes = compare_words(expected, heard)
            ok = got == tot and not notes
            prev = results.get(ln["line"])
            if ok or prev is None or got > prev["got"]:
                results[ln["line"]] = {"match": ok, "got": got, "tot": tot, "notes": notes, "heard": heard,
                                       "fin": fin, "spoken": expected, "take": tag,
                                       "reworded": norm_words(expected) != norm_words(ln["text"])}
            print(f"  line {ln['line']} {tag}: {'OK ' if ok else 'MISS'} {got}/{tot}  heard: {heard}")

    attempt([(ln, ln["say"] or ln["text"]) for ln in todo], "take1")
    for k in range(int(v.get("retakes", 3))):
        bad = [ln for ln in todo if not results.get(ln["line"], {}).get("match")]
        if not bad:
            break
        attempt([(ln, ln["say"] or ln["text"]) for ln in bad], f"retake{k + 1}")
    bad = [ln for ln in todo if not results.get(ln["line"], {}).get("match")]
    for ln in bad:
        alts = ln["alts"] + auto_alts(ln["text"], results.get(ln["line"], {}).get("notes", []))
        for j, alt in enumerate(alts):
            print(f"  line {ln['line']}: AUTO-REWORD try {j + 1}: {alt}")
            attempt([(ln, alt), (ln, alt)], f"reword{ln['line']}_{j + 1}")
            if results.get(ln["line"], {}).get("match"):
                break

    failed = []
    for ln in todo:
        r = results.get(ln["line"])
        if not r:
            failed.append((ln, None))
            continue
        if r["match"]:
            ln["wav"].parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(r["fin"], ln["wav"])
        else:
            failed.append((ln, r))
        state[ln["line"]] = {"line": ln["line"], "text": ln["text"], "spoken": r["spoken"],
                             "wav": str(ln["wav"].relative_to(film)), "heard": r["heard"], "match": r["match"],
                             "take": r["take"], "reworded": r["reworded"], "hash": ln["hash"],
                             "notes": r["notes"]}
    state_p.parent.mkdir(parents=True, exist_ok=True)
    state_p.write_text(json.dumps({"voice": v, "lines": [state[k] for k in sorted(state)]}, indent=1))
    # a script that got shorter leaves stale wavs behind; words_align would read them as lines
    for extra in sorted((film / "vo" / "final").glob("part*.wav"))[len(lines):]:
        extra.unlink()
        print(f"  removed stale {extra.name} (script has {len(lines)} lines)")
    print()
    for ln in lines:
        s = state.get(ln["line"], {})
        flag = "OK  " if s.get("match") else "FAIL"
        rw = "  (REWORDED: " + s["spoken"] + ")" if s.get("reworded") else ""
        print(f"  {flag} line {ln['line']} {s.get('take', '-')}{rw}")
    if failed:
        print("\n[voice] FAILED: whisper never heard these lines as written. Add an `alt:` re-wording (or a `say:` "
              "respelling) under the line in script.md and run again:")
        for ln, r in failed:
            print(f"  line {ln['line']}: {ln['text']}\n    heard: {r['heard'] if r else '(no audio)'}\n"
                  f"    {'; '.join(r['notes']) if r else ''}")
        return 1
    print(f"[voice] {len(lines)} lines voiced and heard word for word -> vo/final/, vo/voice.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
