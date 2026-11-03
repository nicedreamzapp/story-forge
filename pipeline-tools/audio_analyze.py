#!/usr/bin/env python3
"""audio_analyze.py — the music's grid as JSON: tempo, beats, downbeats, sections, onsets.

WHY THIS EXISTS (2026-11-02): cuts already land on WORDS (edit_to_words.py); everything that is
free to move (a J-cut line boundary, the end-card slam, the bed's hit) was placed with no idea
where the music's beats are. promo_mix found the bed's "big downbeat" as the loudest onset peak,
which can be an off-beat crash. Method ported from mexicat/pdoom-video (MIT, analysis/analyze.py),
re-implemented here, with the hand-made parts (their bar phase and section map) made automatic:

  * beat grid: Song Forge / ACE-Step beds are constant tempo, so the grid is ONE period + phase,
    fitted by brute-force search on spectral-flux onset envelopes (drums stem + mix when
    --stems, else the percussive part of the mix), coarse then fine, phase refined on kick
    attacks (median residual). librosa's dynamic beat tracker only seeds the tempo range;
    its beats are kept as "beats_dynamic" and "grid_fit" says how well the grid explains them
  * downbeats: the bar phase (0-3) whose beats carry the most low-band (kick) onset energy
    plus harmonic change (chroma novelty), 4/4 assumed
  * sections: beat-synchronous chroma + MFCC, checkerboard novelty on the self-similarity
    matrix, boundaries snapped to downbeats, min 4 bars; labels A/B/C by feature similarity,
    each with an energy level 0-1
  * onsets: all (mix, backtracked), kick (< 150 Hz), hat (> 5 kHz), each [t, strength 0-1]

Usage:
  ~/chatterbox-env/bin/python pipeline-tools/audio_analyze.py music/bed.wav [--out X.json]
        [--stems] [--bpm-range 60 200]
Default out: <audio>.analysis.json next to the audio (music/bed.analysis.json). --stems
separates drums with Demucs (~/.local/demucs-env) for a cleaner grid on busy mixes.
Exit 0 = written; 2 = could not run. Library helpers: load_analysis(), nearest(), pick_hit().
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

SR = 22050
HOP = 256              # onset envelope hop for the grid fit (11.6 ms)
BAND_LAG = 0.014       # band_onsets timing correction (see band_onsets)


def load(path, sr=SR):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr),
                        "-f", "f32le", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype=np.float32).copy()


def demucs_drums(path) -> Path | None:
    """Drums stem via the same Demucs venv ctc_align uses; None if unavailable."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import ctc_align as C
        stem = C.vocal_stem(path)            # caches the run; drums sit next to it
        drums = stem.with_name(stem.name.replace("_vocals.wav", "_drums.wav"))
        return drums if drums.exists() else None
    except Exception as e:
        print(f"[audio_analyze] demucs unavailable ({e}); using the mix", file=sys.stderr)
        return None


def flux(y, sr=SR, hop=HOP):
    import librosa
    o = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop, lag=1, max_size=1)
    return o / (np.percentile(o, 99) + 1e-9)


def band_onsets(y, sr, lo, hi, min_gap=0.08, rel=0.15):
    """Onset times + strengths from one frequency band's flux (peaks over a running threshold)."""
    import librosa
    from scipy.signal import find_peaks
    S = np.abs(librosa.stft(y, n_fft=1024, hop_length=128))
    f = librosa.fft_frequencies(sr=sr, n_fft=1024)
    m = np.ones_like(f, bool)
    if lo:
        m &= f >= lo
    if hi:
        m &= f <= hi
    e = np.log1p(100 * S[m].sum(0))
    d = np.maximum(0, np.diff(e, prepend=e[0]))
    d = d / (np.percentile(d, 99.5) + 1e-9)
    fps = sr / 128
    pk, pr = find_peaks(d, height=rel, distance=max(1, int(min_gap * fps)))
    # centered 1024-sample frames see an attack before it happens: measured -14 ms on synthetic
    # kicks at 84/97/124 BPM (known beat times), so the detector's times are shifted back
    return pk / fps + BAND_LAG, np.clip(pr["peak_heights"], 0, 1)


def fit_grid(o, ofps, duration, bpm_lo, bpm_hi, seed_bpm=None):
    """Constant tempo grid: brute-force (period, phase) maximizing mean onset strength at the
    grid points (pdoom fit_grid), coarse 0.05 BPM / 4 ms, then fine 0.002 BPM / 1 ms."""
    def score(P, off):
        idx = np.round((off + P * np.arange(int((duration - off) / P) + 1)) * ofps).astype(int)
        idx = idx[(idx > 1) & (idx < len(o) - 2)]
        if len(idx) == 0:
            return 0.0
        return float(np.maximum.reduce([o[idx - 1], o[idx], o[idx + 1]]).mean())

    if seed_bpm:
        # Octave: the mean-onset score always prefers HALF tempo (only the strong beats), so the
        # search stays in one octave: the tracker's tempo folded into 70-160 BPM (the perceptual
        # range) unless --bpm-range says otherwise. Synthetic test: 123.7 BPM came out 61.85 before.
        b = seed_bpm
        while b >= 160 and b / 2 >= bpm_lo:
            b /= 2
        while b < 70 and b * 2 <= bpm_hi:
            b *= 2
        bpms = np.arange(max(bpm_lo, b - 3), min(bpm_hi, b + 3), 0.05)
    else:
        bpms = np.arange(bpm_lo, bpm_hi, 0.1)
    best = (0.0, None, None)
    for bpm in bpms:
        P = 60.0 / bpm
        for off in np.arange(0, P, 0.004):
            s = score(P, off)
            if s > best[0]:
                best = (s, bpm, off)
    _, bpm, off = best
    for b2 in np.arange(bpm - 0.05, bpm + 0.05, 0.002):
        P = 60.0 / b2
        for o2 in np.arange(off - 0.006, off + 0.006, 0.001):
            s = score(P, o2)
            if s > best[0]:
                best = (s, b2, o2)
    return best


def sections_from(y, sr, beats, downbeats, duration, min_bars=4):
    import librosa
    from scipy.signal import find_peaks
    hop = 512
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=hop)
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    bf = np.clip(librosa.time_to_frames(beats, sr=sr, hop_length=hop), 0, chroma.shape[1] - 1)
    bf = np.unique(np.concatenate([[0], bf, [chroma.shape[1]]]))
    C = librosa.util.sync(chroma, bf, aggregate=np.median)
    M = librosa.util.sync(mfcc, bf, aggregate=np.mean)
    R = librosa.util.sync(rms[None], bf, aggregate=np.mean)[0]
    M = M[1:]                                     # drop MFCC0 (loudness); z-score the timbre
    M = (M - M.mean(1, keepdims=True)) / (M.std(1, keepdims=True) + 1e-9)
    C = C - C.mean(1, keepdims=True)
    F = np.vstack([C / (np.linalg.norm(C, axis=0) + 1e-9), M / (np.linalg.norm(M, axis=0) + 1e-9)]) / np.sqrt(2)
    S = F.T @ F
    n = S.shape[0]
    k = 8                                       # checkerboard half-width in beats (2 bars)
    g = np.outer(np.r_[-np.ones(k), np.ones(k)], np.r_[-np.ones(k), np.ones(k)])  # + within, - across
    pad = np.pad(S, k, mode="edge")
    nov = np.array([(pad[i:i + 2 * k, i:i + 2 * k] * g).sum() for i in range(n)])
    nov = np.maximum(0, nov)
    nov = nov / (nov.max() + 1e-9)
    tb = librosa.frames_to_time(bf[:n], sr=sr, hop_length=hop)
    pk, _ = find_peaks(nov, height=0.25, distance=4 * min_bars)
    bounds = [0.0]
    db = np.asarray(downbeats)
    bar = 4 * (beats[1] - beats[0]) if len(beats) > 1 else 2.0
    for p in pk:
        t = tb[p]
        if len(db):
            t = float(db[np.argmin(np.abs(db - t))])
        if t - bounds[-1] >= min_bars * bar - 1e-3 and duration - t >= bar:
            bounds.append(t)
    bounds.append(duration)
    segs = []
    for a, b in zip(bounds, bounds[1:]):
        m = (tb >= a) & (tb < b)
        segs.append((a, b, F[:, m].mean(1) if m.any() else F.mean(1), float(R[m].mean()) if m.any() else 0.0))
    labels, protos = [], []
    for _, _, f, _ in segs:                       # greedy labelling by cosine similarity
        sims = [float(f @ p / (np.linalg.norm(f) * np.linalg.norm(p) + 1e-9)) for p in protos]
        if sims and max(sims) > 0.6:
            labels.append(chr(65 + int(np.argmax(sims))))
        else:
            protos.append(f)
            labels.append(chr(65 + len(protos) - 1))
    emax = max([s[3] for s in segs] + [1e-9])
    out = []
    for (a, b, _, e), l in zip(segs, labels):    # a repeat of the same material is one section
        if out and out[-1]["label"] == l:
            o = out[-1]
            w0, w1 = o["end"] - o["start"], b - a
            o["energy"] = round((o["energy"] * w0 + e / emax * w1) / (w0 + w1), 2)
            o["end"] = round(b, 3)
            continue
        out.append({"label": l, "start": round(a, 3), "end": round(b, 3), "energy": round(e / emax, 2)})
    return out


def analyze(path, stems=False, bpm_lo=60.0, bpm_hi=200.0):
    import librosa
    y = load(path)
    duration = len(y) / SR
    yp = librosa.effects.percussive(y, margin=2.0)
    o = flux(yp) + flux(y)
    drums = demucs_drums(path) if stems else None
    if drums is not None:
        yd = load(drums)[: len(y)]
        od = flux(yd)
        L = min(len(o), len(od))
        o = o[:L] + 1.5 * od[:L]
    ofps = SR / HOP
    seed, dyn = librosa.beat.beat_track(y=y, sr=SR, hop_length=HOP, units="time")
    seed = float(np.atleast_1d(seed)[0])
    fit, bpm, off = fit_grid(o, ofps, duration, bpm_lo, bpm_hi, seed_bpm=seed)
    P = 60.0 / bpm
    kick_t, kick_s = band_onsets(yd if drums is not None else yp, SR, None, 150, min_gap=0.18, rel=0.2)
    for _ in range(2):  # refine phase AND period on kick attacks: res = a + b*n (robust line fit)
        if len(kick_t) < 8:
            break
        n = np.round((kick_t - off) / P)
        res = kick_t - (off + n * P)
        ok = np.abs(res) < 0.06
        if ok.sum() < 8:
            break
        b_, a_ = np.polyfit(n[ok], res[ok], 1)
        if abs(b_) < 0.002:                      # never more than 0.3% tempo change
            P += b_
            off += a_
    bpm = 60.0 / P
    off -= P * math.floor(off / P)
    beats = off + P * np.arange(int((duration - off) / P) + 1)
    # bar phase: kick energy + harmonic change on each candidate downbeat
    # harmonic change per beat: cosine distance between the beat-synchronous chroma of the
    # HARMONIC part on this beat vs the previous one (frame-level chroma spikes on snares)
    yh = y - yp
    chroma = librosa.feature.chroma_cqt(y=yh, sr=SR, hop_length=512)
    bfr = np.clip(librosa.time_to_frames(beats, sr=SR, hop_length=512), 0, chroma.shape[1] - 1)
    Cb = librosa.util.sync(chroma, np.r_[bfr, chroma.shape[1]], aggregate=np.median)[:, 1:len(beats) + 1]
    Cb = Cb / (np.linalg.norm(Cb, axis=0) + 1e-9)
    chg_at = np.r_[0.0, 1 - (Cb[:, 1:] * Cb[:, :-1]).sum(0)]
    chg_at = np.r_[chg_at, np.zeros(max(0, len(beats) - len(chg_at)))][:len(beats)]
    kick_at = np.array([kick_s[np.abs(kick_t - b) < 0.05].sum() if len(kick_t) else 0 for b in beats])
    ph_score = []
    for ph in range(4):
        sel = np.arange(len(beats)) % 4 == ph
        # harmonic change is the stronger bar cue (kick often sits on 1 AND 3); weight it 2x
        ph_score.append(kick_at[sel].mean() / (kick_at.mean() + 1e-9) + 2 * chg_at[sel].mean() / (chg_at.mean() + 1e-9))
    phase = int(np.argmax(ph_score))
    downbeats = beats[phase::4]
    dyn = np.asarray(dyn, float)
    ref = beats
    if len(dyn) > 1 and np.median(np.diff(dyn)) < 0.75 * P:   # tracker at double tempo: half-grid
        ref = np.sort(np.r_[beats, beats + P / 2])
    near = [np.min(np.abs(ref - t)) for t in dyn] if len(dyn) else []
    grid_fit = float(np.mean(np.array(near) < 0.07)) if len(near) else None
    on_t = librosa.onset.onset_detect(y=y, sr=SR, hop_length=HOP, backtrack=True, units="time")
    env = flux(y)
    on_s = np.clip(env[np.clip(np.round(np.asarray(on_t) * ofps).astype(int), 0, len(env) - 1)], 0, 1)
    hat_t, hat_s = band_onsets(yp, SR, 5000, None, min_gap=0.06, rel=0.25)
    secs = sections_from(y, SR, beats, downbeats, duration)
    r3 = lambda a: [round(float(t), 3) for t in a]
    pairs = lambda t, s: [[round(float(a), 3), round(float(b), 2)] for a, b in zip(t, s)]
    return {
        "audio": str(path), "duration": round(duration, 3), "bpm": round(bpm, 3),
        "beat_period": round(P, 5), "time_signature": 4, "first_beat": round(off, 4),
        "downbeat_phase": phase, "grid_score": round(fit, 3), "grid_fit": grid_fit,
        "tracker_bpm": round(seed, 2), "stems": drums is not None,
        "beats": r3(beats), "downbeats": r3(downbeats), "beats_dynamic": r3(dyn),
        "sections": secs,
        "onsets": pairs(on_t, on_s), "kick": pairs(kick_t, kick_s), "hat": pairs(hat_t, hat_s),
        "method": "constant grid (pdoom fit_grid port) + kick phase refine; downbeat = kick+chroma "
                  "change phase; sections = checkerboard novelty on beat-sync chroma+MFCC",
    }


# ---------------------------------------------------------------- helpers for other tools
def load_analysis(audio_or_json):
    """The analysis for a bed: X.analysis.json beside it (computed and cached if missing)."""
    p = Path(audio_or_json)
    j = p if p.suffix == ".json" else p.with_suffix(".analysis.json")
    if j.exists() and (p.suffix == ".json" or j.stat().st_mtime >= p.stat().st_mtime):
        return json.loads(j.read_text())
    try:
        import librosa  # noqa: F401
    except ImportError:  # a tool running under plain python3: analyze in the env that has librosa
        subprocess.run([str(Path.home() / "chatterbox-env" / "bin" / "python"), str(Path(__file__).resolve()),
                        str(p), "--out", str(j)], check=True, capture_output=True)
        return json.loads(j.read_text())
    a = analyze(p)
    j.write_text(json.dumps(a, indent=1))
    return a


def nearest(ts, t, max_d=None, lo=None, hi=None):
    """Nearest time in ts to t (optionally within max_d and inside [lo, hi]); None if none."""
    c = [x for x in ts if (lo is None or x >= lo) and (hi is None or x <= hi)
         and (max_d is None or abs(x - t) <= max_d)]
    return min(c, key=lambda x: abs(x - t)) if c else None


def pick_hit(an, want_after, tail_keep=4.0):
    """The bed's big downbeat for the end-card slam: the downbeat in the last 45% (at least
    want_after s in, at least tail_keep s before the end) with the most onset energy in the
    beat after it. Returns seconds into the bed, or None if no downbeat qualifies."""
    dur = an["duration"]
    lo = max(want_after, dur * 0.55)
    cand = [d for d in an["downbeats"] if lo <= d <= dur - tail_keep]
    if not cand:
        cand = [d for d in an["downbeats"] if d >= dur * 0.5]
    if not cand:
        return None
    on = np.array(an["onsets"] or [[0, 0]])
    P = an["beat_period"]
    score = lambda d: float(on[(on[:, 0] >= d - 0.04) & (on[:, 0] < d + P * 0.5), 1].sum())
    return max(cand, key=score)


def timeline_grid(bed, slam, hit=None):
    """The bed's beat grid on the FILM timeline. promo_mix offsets the bed so its hit (promo.json
    music.hit, else pick_hit) lands on the end-card slam: film_t = bed_t - (hit - slam).
    Returns {"beats","downbeats","offset","hit","bpm"} (film seconds, >= 0 only) or None."""
    an = load_analysis(bed)
    h = float(hit) if hit is not None else pick_hit(an, slam)
    if h is None:
        return None
    off = h - slam
    keep = lambda ts: [round(t - off, 4) for t in ts if t - off >= 0]
    return {"beats": keep(an["beats"]), "downbeats": keep(an["downbeats"]), "offset": round(off, 4),
            "hit": round(h, 4), "bpm": an["bpm"], "bed": str(bed)}


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("audio")
    ap.add_argument("--out", default=None)
    ap.add_argument("--stems", action="store_true", help="Demucs drums stem for the grid")
    ap.add_argument("--bpm-range", nargs=2, type=float, default=[60.0, 200.0])
    a = ap.parse_args()
    try:
        res = analyze(a.audio, stems=a.stems, bpm_lo=a.bpm_range[0], bpm_hi=a.bpm_range[1])
    except Exception as e:
        print(f"[audio_analyze] could not run: {e}", file=sys.stderr)
        sys.exit(2)
    out = Path(a.out) if a.out else Path(a.audio).with_suffix(".analysis.json")
    out.write_text(json.dumps(res, indent=1))
    print(f"[audio_analyze] {Path(a.audio).name}: {res['bpm']:.2f} BPM, first beat {res['first_beat']:.3f}s, "
          f"{len(res['beats'])} beats, {len(res['downbeats'])} bars (phase {res['downbeat_phase']}), "
          f"grid fit {res['grid_fit']}, tracker {res['tracker_bpm']} BPM")
    print("  sections: " + "  ".join(f"{s['label']}@{s['start']:.1f}(e{s['energy']})" for s in res["sections"]))
    print(f"  onsets {len(res['onsets'])}, kick {len(res['kick'])}, hat {len(res['hat'])} -> {out}")


if __name__ == "__main__":
    main()
