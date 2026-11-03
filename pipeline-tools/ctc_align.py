#!/usr/bin/env python3
"""ctc_align.py — fused CTC forced alignment of a KNOWN transcript: word times to the frame.

WHY THIS EXISTS (2026-11-02): words_align.py took word starts from whisper and nudged them
onto waveform edges. Whisper's word times are a by-product of its attention, not an
alignment, and they drift 50-150 ms (worse on singing). When we already know the words
(script.md, the lyric sheet, or whisper's own transcript), a forced aligner places them
against acoustic evidence frame by frame. Method ported from mexicat/pdoom-video (MIT,
analysis/ctcalign.py + align.py), re-implemented here:

  * optional Demucs vocal stem first (`vocals=True`; for songs or VO over music; runs in
    its own venv ~/.local/demucs-env so the chatterbox env is never touched)
  * frame-wise CTC log-probs (20 ms) from two independent acoustic models, torchaudio
    MMS_FA (trained for alignment) and WAV2VEC2_ASR_LARGE_LV60K_960H, both fp32, chunked
    20 s with 3 s context, mapped to one alphabet (blank, a-z, ')
  * FUSED = probability mixture of the two (logaddexp - log 2), a more robust single path
  * ONE global constrained Viterbi over the whole transcript: a garbage "star" token sits
    between lines and at both ends (score = best frame log-prob - margin) so ad-libs,
    breaths and backing vocals not in the text get absorbed instead of stretching words
  * constraints: per-line windows (words_align knows where each line's wav sits on the
    timeline) and manual anchors (word -> earliest start / latest end, seconds)
  * per-word confidence = 0.35 + 0.30*(MMS-only and wav2vec2-only paths agree within
    60 ms) + 0.20*CTC posterior + 0.15*(whisper agrees within 150 ms; 0.5 if no whisper);
    an anchored word gets at least 0.8 (pdoom's formula)

Library use (words_align.py does this):
    from ctc_align import align_segments
    res = align_segments([{"audio": y16k, "t0": 0.0, "words": ["Most", "exoskeletons", ...]}, ...],
                         anchors={word_index: (lo_s, hi_s)}, whisper=[start_s or None, ...])
CLI (any wav + a text file, one line per lyric/dialogue line):
    ~/chatterbox-env/bin/python pipeline-tools/ctc_align.py song.wav --text lyrics.txt
        [--vocals] [--anchors anchors.json] [--whisper] [--out words.json]
Exit 0 = written; 2 = could not run (models would not load) — never treat 2 as a pass.
Models stay fp32 (frozen: never 4-bit). Song Forge jobs outrank us: --wait-songforge.
"""
from __future__ import annotations

import gc
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

FRAME = 0.02            # s per emission frame (both models hop 320 samples @ 16 kHz)
SR = 16000
ALPHA = ["-"] + list("abcdefghijklmnopqrstuvwxyz'")
AIDX = {c: i for i, c in enumerate(ALPHA)}
STAR = len(ALPHA)       # garbage token column, appended at align time
NEG = -1e18
# CTC emits a word's first letter a little AFTER the sound starts. Measured 2026-11-02: fused
# starts sat +20 ms after the waveform attack on Matt's real VO (sitka_v3, line-initial words),
# +22 ms on Kokoro speech, +32 ms vs Kokoro's duration-predictor timestamps. Subtracted from
# every start (never before the previous word's end).
LEAD_COMP = 0.025
DEMUCS_PY = Path.home() / ".local" / "demucs-env" / "bin" / "python"
CACHE = Path.home() / ".cache" / "story-forge" / "ctc_align"

# ---------------------------------------------------------------- pronunciation spelling
_ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen " \
        "fifteen sixteen seventeen eighteen nineteen".split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
SPOKEN_ACRONYMS = {"NASA", "LED", "LEDS", "SAAS", "GIF", "JPEG", "RAM", "ROM", "LIDAR", "PIN", "UNESCO"}
LETTER = {"a": "ay", "b": "bee", "c": "see", "d": "dee", "e": "ee", "f": "eff", "g": "gee", "h": "aitch",
          "i": "eye", "j": "jay", "k": "kay", "l": "el", "m": "em", "n": "en", "o": "oh", "p": "pee",
          "q": "cue", "r": "are", "s": "ess", "t": "tee", "u": "you", "v": "vee", "w": "double you",
          "x": "ex", "y": "why", "z": "zee"}


def num_words(n: int) -> str:
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + ("" if n % 10 == 0 else " " + _ONES[n % 10])
    if n < 1000:
        return _ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " " + num_words(n % 100))
    for div, name in ((10 ** 9, "billion"), (10 ** 6, "million"), (1000, "thousand")):
        if n >= div:
            return num_words(n // div) + " " + name + ("" if n % div == 0 else " " + num_words(n % div))
    return str(n)


def pron(token: str, override: dict | None = None) -> list[str]:
    """Display token -> pronunciation sub-words made of a-z and internal apostrophes.
    'GPU' -> ['gee','pee','you'], '15' -> ['fifteen'], '$2,000' -> ['two','thousand','dollars'],
    '3D' -> ['three','dee']. An override {"Sitka": "sit ka"} wins (case-insensitive)."""
    if override:
        for k, v in override.items():
            if k.lower() == token.lower().strip(".,!?;:\"'"):
                return v.lower().split()
    t = token.replace("’", "'").replace("—", " ").replace("–", " ")
    core = t.strip(".,!?;:\"()[]")
    out = []
    dollars = core.startswith("$")
    core = core.lstrip("$~").replace("%", " percent").replace("&", " and ").replace("+", " plus ")
    for piece in re.split(r"[\s\-/]+", core):
        if not piece:
            continue
        m = re.fullmatch(r"(\d[\d,]*)(?:\.(\d+))?([a-zA-Z]*)", piece)
        if m:
            out += num_words(int(m.group(1).replace(",", ""))).split()
            if m.group(2):
                out += ["point"] + [_ONES[int(d)] for d in m.group(2)]
            suf = m.group(3)
            if suf and suf.lower() not in ("st", "nd", "rd", "th", "s"):
                out += [x for ch in suf.lower() if ch in LETTER for x in LETTER[ch].split()]
            continue
        letters = re.sub(r"[^A-Za-z']", "", piece)
        if not letters:
            continue
        if letters.isupper() and 2 <= len(letters) <= 5 and letters not in SPOKEN_ACRONYMS:
            for ch in letters.lower():
                if ch in LETTER:
                    out += LETTER[ch].split()
            continue
        w = letters.lower().strip("'")
        if w:
            out.append(w)
    if dollars:
        out.append("dollars")
    return out


# ---------------------------------------------------------------- audio helpers
def load16k(path) -> np.ndarray:
    """Any audio file -> mono float32 @16 kHz (ffmpeg decode, the same clock as everything else)."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR),
                        "-f", "f32le", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype=np.float32).copy()


def vocal_stem(path, model="htdemucs") -> Path:
    """Demucs vocal stem (cached by file hash; drums/bass/other are written beside it).
    Runs in ~/.local/demucs-env as a subprocess."""
    path = Path(path)
    h = hashlib.sha1(path.read_bytes()).hexdigest()[:16]
    out = CACHE / "stems" / f"{h}_{model}_vocals.wav"
    if out.exists():
        return out
    if not DEMUCS_PY.exists():
        raise RuntimeError(f"demucs venv missing ({DEMUCS_PY}); create it with "
                           "`uv venv ~/.local/demucs-env --python 3.12 && uv pip install --python "
                           "~/.local/demucs-env/bin/python demucs soundfile`")
    out.parent.mkdir(parents=True, exist_ok=True)
    code = r"""
import sys, numpy as np, soundfile as sf, torch, subprocess
from demucs.pretrained import get_model
from demucs.apply import apply_model
src, dst, name = sys.argv[1:4]
m = get_model(name).eval()
sr = m.samplerate
raw = subprocess.run(["ffmpeg","-v","error","-i",src,"-ac","2","-ar",str(sr),"-f","f32le","-"],
                     capture_output=True, check=True).stdout
x = torch.from_numpy(np.frombuffer(raw, dtype=np.float32).copy()).view(-1, 2).T.contiguous()
ref = x.mean(0)
x = (x - ref.mean()) / (ref.std() + 1e-8)
dev = "mps" if torch.backends.mps.is_available() else "cpu"
with torch.inference_mode():
    s = apply_model(m, x[None], device=dev, shifts=1, split=True, overlap=0.25, segment=7.8)[0]
s = s * (ref.std() + 1e-8) + ref.mean()
for i, name_ in enumerate(m.sources):   # every stem is kept: audio_analyze reads the drums
    sf.write(dst.replace("_vocals.wav", f"_{name_}.wav"), s[i].cpu().numpy().T, sr, subtype="FLOAT")
"""
    subprocess.run([str(DEMUCS_PY), "-I", "-c", code, str(path), str(out), model], check=True)
    return out


# ---------------------------------------------------------------- CTC emissions
_MODELS: dict = {}


def _device():
    import torch
    return "mps" if torch.backends.mps.is_available() else "cpu"


def _load(name):
    import torchaudio
    if name not in _MODELS:
        if name == "mms":
            b = torchaudio.pipelines.MMS_FA
            m, labels = b.get_model(with_star=False), list(b.get_labels(star=None))
        else:
            b = torchaudio.pipelines.WAV2VEC2_ASR_LARGE_LV60K_960H
            m, labels = b.get_model(), list(b.get_labels())
        _MODELS[name] = (m.float().to(_device()).eval(), labels)
    return _MODELS[name]


def unload():
    _MODELS.clear()
    gc.collect()
    try:
        import torch
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()
    except Exception:
        pass


def emission(y: np.ndarray, name: str, chunk_s=20.0, ctx_s=3.0) -> np.ndarray:
    """[frames, len(ALPHA)] normalized log-probs on the common alphabet for one model."""
    import torch
    model, labels = _load(name)
    dev = next(model.parameters()).device
    y = y / (np.abs(y).max() + 1e-9)
    n_frames = max(1, len(y) // 320)
    chunk, ctx = int(chunk_s * SR), int(ctx_s * SR)
    raw = None
    for s in range(0, len(y), chunk):
        a, b = max(0, s - ctx), min(len(y), s + chunk + ctx)
        x = torch.from_numpy(np.ascontiguousarray(y[a:b])).float()[None].to(dev)
        with torch.inference_mode():
            em, _ = model(x)
            em = torch.log_softmax(em, dim=-1)[0].float().cpu().numpy()
        if raw is None:
            raw = np.full((n_frames, em.shape[1]), np.nan, np.float64)
        f0 = a // 320
        lo, hi = s // 320, min(n_frames, (s + chunk) // 320)
        seg = em[max(0, lo - f0): max(0, hi - f0)]
        raw[lo: lo + len(seg)] = seg
    ok = np.where(~np.isnan(raw[:, 0]))[0]
    raw[ok.max() + 1:] = raw[ok.max()]
    out = np.full((n_frames, len(ALPHA)), -1e4)
    blank_cols = [labels.index("-")] + ([labels.index("|")] if "|" in labels else [])
    out[:, 0] = np.logaddexp.reduce(raw[:, blank_cols], axis=1)
    for i, c in enumerate(labels):
        k = c.lower()
        if k in AIDX and k != "-":
            out[:, AIDX[k]] = raw[:, i]
    out -= np.logaddexp.reduce(out, axis=1, keepdims=True)
    return out


# ---------------------------------------------------------------- Viterbi
def viterbi(E: np.ndarray, tgt: np.ndarray, lo: np.ndarray, hi: np.ndarray):
    """CTC Viterbi (blank-interleaved states) with per-token frame windows, numpy-vectorized
    over states. E: [T, V] log-probs incl. the star column; tgt: token ids; lo/hi: allowed
    frame range for each token. Returns the state path [T]."""
    T, L = E.shape[0], len(tgt)
    S = 2 * L + 1
    ext = np.zeros(S, np.int64)
    ext[1::2] = tgt
    odd = np.zeros(S, bool)
    odd[1::2] = True
    skip = np.zeros(S, bool)
    skip[3::2] = tgt[1:] != tgt[:-1]
    slo = np.full(S, -1, np.int64)
    shi = np.full(S, T, np.int64)
    slo[1::2], shi[1::2] = lo, hi
    bp = np.zeros((T, S), np.int8)
    prev = np.full(S, NEG)
    prev[0] = E[0, 0]
    if lo[0] <= 0 <= hi[0]:
        prev[1] = E[0, tgt[0]]
    c1 = np.full(S, NEG)
    c2 = np.full(S, NEG)
    for t in range(1, T):
        c1[1:] = prev[:-1]
        c2[2:] = np.where(skip[2:], prev[:-2], NEG)
        stack = np.stack([prev, c1, c2])
        arg = stack.argmax(0)
        best = stack[arg, np.arange(S)]
        cur = best + E[t, ext]
        cur[odd & ((t < slo) | (t > shi))] = NEG
        bp[t] = arg
        prev = cur
    s = S - 1 if prev[S - 1] >= prev[S - 2] else S - 2
    if prev[s] <= NEG / 2:
        raise RuntimeError("no alignment path satisfies the windows/anchors (an anchor or line window "
                           "is too tight, or the audio is shorter than the text)")
    path = np.zeros(T, np.int64)
    for t in range(T - 1, -1, -1):
        path[t] = s
        s -= int(bp[t, s])
    return path


def _targets(segments, prons):
    """tgt ids with star between segments; index[(word_k)] = (a, b) token range."""
    tgt, index = [STAR], []
    k = 0
    for seg in segments:
        for _ in seg["words"]:
            a = len(tgt)
            for sub in prons[k]:
                tgt.extend(AIDX[c] for c in sub if c in AIDX)
            index.append((a, len(tgt)))
            k += 1
        tgt.append(STAR)
    return np.array(tgt, np.int64), index


def _path_words(E, segments, prons, windows, anchors, margin):
    T = E.shape[0]
    Ex = np.concatenate([E, E.max(axis=1, keepdims=True) - margin], axis=1)
    tgt, index = _targets(segments, prons)
    lo = np.zeros(len(tgt), np.int64)
    hi = np.full(len(tgt), T - 1, np.int64)
    for k, (a, b) in enumerate(index):
        if windows and windows[k] is not None:
            wl, wh = windows[k]
            lo[a:b] = np.maximum(lo[a:b], int(wl / FRAME))
            hi[a:b] = np.minimum(hi[a:b], int(wh / FRAME))
        if anchors and k in anchors:
            wl, wh = anchors[k]
            if wl is not None:
                lo[a:b] = np.maximum(lo[a:b], int(round(wl / FRAME)))
            if wh is not None:
                hi[a:b] = np.minimum(hi[a:b], int(round(wh / FRAME)))
    path = viterbi(Ex, tgt, lo, hi)
    tokpos = np.where(path % 2 == 1, (path - 1) // 2, -1)
    P = np.exp(Ex[np.arange(T), np.where(tokpos >= 0, tgt[np.maximum(tokpos, 0)], 0)])
    out = []
    for (a, b) in index:
        if b <= a:                               # nothing pronounceable ("—"): no evidence
            out.append(None)
            continue
        fr = np.where((tokpos >= a) & (tokpos < b))[0]
        out.append((float(fr.min() * FRAME), float((fr.max() + 1) * FRAME), float(P[fr].mean())))
    return out


def align_segments(segments, anchors=None, whisper=None, pron_override=None, margin=1.5,
                   use_windows=True, alts=True, lead_comp=LEAD_COMP, log=print):
    """segments: [{"audio": float32 16 kHz mono, "t0": start on the common timeline (s),
    "words": [display tokens]}] (audio may be None: a text-only line break that shares the
    previous audio, used for one song file with many lyric lines). Segments are laid on one timeline (gaps = silence) and the
    whole transcript is aligned in ONE pass; with use_windows each segment's words must lie
    inside its own audio. anchors: {global word index: (lo_s, hi_s)} in timeline seconds.
    whisper: [timeline start or None per word] for the cross-check.
    Returns a list per word: {"start","end","post","agree","conf","anchored"} (timeline s),
    or None for a word with nothing pronounceable."""
    words = [w for s in segments for w in s["words"]]
    prons = [pron(w, pron_override) for w in words]
    has = [s for s in segments if s.get("audio") is not None and len(s["audio"])]
    T = int(np.ceil(max(s["t0"] + len(s["audio"]) / SR for s in has) / FRAME)) + 1
    em = {}
    for name in ("mms", "w2v"):
        E = np.full((T, len(ALPHA)), -1e4)
        E[:, 0] = 0.0                            # gaps between segments = certain blank
        for s in has:
            e = emission(s["audio"], name)
            f0 = int(round(s["t0"] / FRAME))
            n = min(len(e), T - f0)
            E[f0:f0 + n] = e[:n]
        em[name] = E
        log(f"[ctc_align] {name} emissions {E.shape}")
    fused = np.logaddexp(em["mms"], em["w2v"]) - np.log(2)
    windows = None
    if use_windows:
        windows = []
        for s in segments:
            w = (s["t0"], s["t0"] + len(s["audio"]) / SR)
            windows += [w] * len(s["words"])
    main = _path_words(fused, segments, prons, windows, anchors, margin)
    alt = [_path_words(em[n], segments, prons, windows, anchors, margin) for n in ("mms", "w2v")] if alts else []
    res = []
    prev_end = 0.0
    for k, m in enumerate(main):
        if m is None:
            res.append(None)
            continue
        st, en, post = m
        raw_st = st
        if not (anchors and k in anchors and anchors[k][0] is not None):
            st = max(prev_end, st - lead_comp, 0.0)
        prev_end = en
        ds = [abs(a[k][0] - raw_st) for a in alt if a[k] is not None]
        agree = float(np.mean([d <= 0.06 for d in ds])) if ds else 0.5
        wh = whisper[k] if whisper and k < len(whisper) else None
        wag = 0.5 if wh is None else float(abs(wh - st) <= 0.15)
        c = 0.35 + 0.3 * agree + 0.2 * min(1.0, post / 0.5) + 0.15 * wag
        anchored = bool(anchors and k in anchors)
        if anchored:
            c = max(c, 0.8)
        res.append({"start": round(st, 3), "end": round(en, 3), "raw_start": round(raw_st, 3),
                    "post": round(post, 3),
                    "agree": round(agree, 2), "conf": round(float(np.clip(c, 0, 1)), 2),
                    "anchored": anchored,
                    "alt_starts": [round(a[k][0], 3) if a[k] else None for a in alt]})
    return res


def load_anchors(path, words_flat):
    """anchors.json: {"anchors": [{"word": "stairs", "nth": 1, "line": 8 (optional),
    "start": 61.20 (earliest), "end": 61.80 (latest)}], "pron": {"Sitka": "sit ka"}}.
    Times are on the same timeline as the output (words.json). Returns ({k: (lo, hi)}, pron)."""
    if not path or not Path(path).exists():
        return {}, {}
    d = json.loads(Path(path).read_text())
    norm = lambda w: re.sub(r"[^a-z0-9']", "", str(w).lower()).strip("'")
    out = {}
    for a in d.get("anchors", []):
        hits = [k for k, (ln, w) in enumerate(words_flat)
                if norm(w) == norm(a["word"]) and (a.get("line") is None or a["line"] == ln)]
        n = int(a.get("nth", 1))
        if len(hits) >= n:
            out[hits[n - 1]] = (a.get("start"), a.get("end"))
        else:
            print(f"[ctc_align] anchor {a} matches no word; ignored", file=sys.stderr)
    return out, d.get("pron", {})


def songforge_busy():
    try:
        import urllib.request
        with urllib.request.urlopen("http://127.0.0.1:8767/api/status", timeout=3) as r:
            return int(json.loads(r.read()).get("jobs_running", 0)) > 0
    except Exception:
        return False


# ---------------------------------------------------------------- CLI
def main():
    import argparse
    import time
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("audio")
    ap.add_argument("--text", required=True, help="transcript, one line per lyric/dialogue line")
    ap.add_argument("--vocals", action="store_true", help="align the Demucs vocal stem (songs, VO over music)")
    ap.add_argument("--anchors", default=None)
    ap.add_argument("--whisper", action="store_true", help="mlx-whisper cross-check for confidence")
    ap.add_argument("--margin", type=float, default=1.5, help="star (garbage) token margin")
    ap.add_argument("--out", default=None)
    ap.add_argument("--wait-songforge", action="store_true")
    a = ap.parse_args()
    while songforge_busy():
        if not a.wait_songforge:
            print("[ctc_align] Song Forge has a customer job running; rerun later or --wait-songforge",
                  file=sys.stderr)
            sys.exit(2)
        time.sleep(30)
    lines = [re.sub(r"\s+", " ", l).strip() for l in Path(a.text).read_text().splitlines()]
    lines = [l for l in lines if l and not l.startswith("#")]
    src = Path(a.audio)
    try:
        if a.vocals:
            src = vocal_stem(src)
            print(f"[ctc_align] vocal stem {src}")
        y = load16k(src)
        toks = [l.split(" ") for l in lines]
        flat = [(i + 1, w) for i, ts in enumerate(toks) for w in ts]
        anchors, po = load_anchors(a.anchors, flat)
        whisper = None
        if a.whisper:
            whisper = whisper_starts(src, " ".join(lines), [w for _, w in flat])
        # one audio, one segment per text line (a star token separates lines; audio=None means
        # "no audio of its own", the first segment carries the whole file)
        segs = [{"audio": y if i == 0 else None, "t0": 0.0, "words": ts} for i, ts in enumerate(toks)]
        res = align_segments(segs, anchors=anchors, whisper=whisper, pron_override=po,
                             margin=a.margin, use_windows=False)
    except Exception as e:
        print(f"[ctc_align] could not run: {e}", file=sys.stderr)
        sys.exit(2)
    words = []
    for k, ((ln, w), r) in enumerate(zip(flat, res)):
        d = {"i": k, "line": ln, "word": w}
        d.update(r or {"start": None, "end": None, "conf": 0.0})
        if whisper:
            d["w_start"] = whisper[k]
        words.append(d)
    out = Path(a.out) if a.out else src.with_suffix(".words.json")
    out.write_text(json.dumps({"audio": str(a.audio), "aligned_on": str(src), "method":
                               "fused CTC (MMS_FA + wav2vec2 LV60K), global Viterbi", "words": words}, indent=1))
    lowc = [w for w in words if (w.get("conf") or 0) < 0.6]
    print(f"[ctc_align] wrote {out} ({len(words)} words, {len(lowc)} under conf 0.6)")
    for w in lowc[:20]:
        print(f"    low conf {w['conf']:.2f}  line {w['line']} '{w['word']}' @ {w['start']}")


def whisper_starts(path, prompt, tokens):
    """mlx-whisper word starts mapped onto `tokens` by sequence alignment (None where unmatched)."""
    import difflib
    import mlx_whisper
    r = mlx_whisper.transcribe(str(path), path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
                               word_timestamps=True, language="en", initial_prompt=prompt[:800],
                               condition_on_previous_text=False)
    ww = [(w["word"].strip(), float(w["start"])) for s in r.get("segments", []) for w in s.get("words", [])]
    norm = lambda t: re.sub(r"[^a-z0-9]", "", t.lower())
    sm = difflib.SequenceMatcher(a=[norm(t) for t in tokens], b=[norm(w) for w, _ in ww], autojunk=False)
    out = [None] * len(tokens)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
            for d in range(i2 - i1):
                out[i1 + d] = ww[j1 + d][1]
    return out


if __name__ == "__main__":
    main()
