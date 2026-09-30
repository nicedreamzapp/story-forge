#!/usr/bin/env python3
"""audio_check.py — the ears film_qc does not have. MANDATORY before a film is shown.

Built 2026-09-30 after The Oldest Tree shipped to Matt four times with audio he caught
and the pipeline did not: a score with a sung vocal ("instrumental" in the style is not
enough — Song Forge writes lyrics whenever `lyrics` is blank), a 5 Hz beating drone at
54/57 and 108/113 Hz ("what is that buzzing"), a looping score with a hard jump in the
middle, and loudnorm pumping the music up between lines ("music is too loud at times").
Every one of those passed loudness + whisper checks. This script measures each directly.

    ~/chatterbox-env/bin/python pipeline-tools/audio_check.py FILM.mp4   (needs librosa + mlx_whisper) \
        --score score.wav --timeline final/timeline.json --narration narration.json

timeline.json: {"narration": [["nia_n01.wav", 3.8], ...]}   (file name, start in film)
narration.json: [{"id": "n01", "text": "..."}]  — files are voices/nia_<id>.wav

Checks (FAIL blocks showing the film; WARN must be read by a human/Claude and mentioned):
  1. SCORE VOCALS   demucs vocal stem must sit >= 15 dB under the music stem
  2. DRONE          no single low tone (30-250 Hz) > 20% of the energy for 3 s+ (film AND score)
  3. SCORE LOOPS    near-identical 4 s passages and hard jumps -> WARN with timestamps
  4. BALANCE        demucs on the film: music never louder than the narration average;
                    while someone speaks, music >= 6 dB under the voice (else WARN)
  5. EVERY LINE     each narration line re-listened in its own window (full-film whisper
                    hallucinates repeats/drops — rule from 2026-07 and 2026-09-29)
  6. LOUDNESS       integrated LUFS + true peak reported; LRA > 15 -> WARN (pumping)

Exit 0 = no FAIL; 1 = FAIL(s); 2 = could not run. I cannot hear: a PASS here means the
measurable failure modes are absent, not that it sounds good. Say that when reporting.
"""
import argparse, json, re, subprocess, sys, tempfile
from pathlib import Path

FF = "/opt/homebrew/bin/ffmpeg"
DEMUCS = Path.home() / "Library/Python/3.9/bin/demucs"
WHISPER = "mlx-community/whisper-large-v3-turbo"


def vol(f, a=None, b=None):
    cmd = [FF]
    if a is not None:
        cmd += ["-ss", str(a), "-to", str(b)]
    cmd += ["-i", str(f), "-af", "volumedetect", "-f", "null", "-"]
    m = re.search(r"mean_volume: ([-\d.]+)", subprocess.run(cmd, capture_output=True, text=True).stderr)
    return float(m.group(1)) if m else -99.0


def dur(f):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", str(f)]).decode().strip())


def stems(src, tmp):
    wav = Path(tmp) / (Path(src).stem + ".wav")
    subprocess.run([FF, "-v", "error", "-y", "-i", str(src), "-vn", "-ac", "2", "-ar", "44100", str(wav)], check=True)
    subprocess.run([str(DEMUCS), "--two-stems", "vocals", "-o", str(Path(tmp) / "sep"), str(wav)],
                   capture_output=True, check=True)
    d = next((Path(tmp) / "sep").glob(f"*/{wav.stem}"))
    return d / "vocals.wav", d / "no_vocals.wav"


def drone_runs(f, min_s=3.0, share_min=0.20):
    import librosa, numpy as np
    y, sr = librosa.load(str(f), sr=22050)
    S = np.abs(librosa.stft(y, n_fft=8192, hop_length=11025))
    fr = librosa.fft_frequencies(sr=sr, n_fft=8192)
    band = (fr > 30) & (fr < 250)
    runs, cur = [], None
    for i in range(S.shape[1]):
        col = S[:, i]
        if col.sum() < 1e-3:
            cur = None; continue
        j = int(np.argmax(col * band))
        share = col[max(0, j - 3):j + 4].sum() / col.sum()
        t = i * 0.5
        if share > share_min:
            if cur and t - cur[1] <= 1.0 and abs(fr[j] - cur[2]) < 10:
                cur[1] = t
            else:
                cur = [t, t, round(float(fr[j]))]; runs.append(cur)
        else:
            cur = None
    return [(a, b, hz) for a, b, hz in runs if b - a + 0.5 >= min_s]


def loops_and_jumps(f):
    import librosa, numpy as np
    y, sr = librosa.load(str(f), sr=22050)
    hop = 2205
    C = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)
    M = librosa.feature.mfcc(y=y, sr=sr, hop_length=hop, n_mfcc=20)
    F = np.vstack([C, M / 50]); F = F / (np.linalg.norm(F, axis=0) + 1e-9)
    n, w = F.shape[1], 40
    reps = []
    for a in range(0, n - w, 20):
        A = F[:, a:a + w].flatten(); best, bj = 0, None
        for b in range(0, n - w, 10):
            if abs(a - b) < 80:
                continue
            B = F[:, b:b + w].flatten()
            s = float(A @ B / (np.linalg.norm(A) * np.linalg.norm(B)))
            if s > best:
                best, bj = s, b
        if best > 0.985:
            reps.append((a / 10, bj / 10))
    flux = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    z = (flux - np.median(flux)) / (np.std(flux) + 1e-9)
    jumps = [round(i / 10, 1) for i in np.where(z > 6)[0]]
    return reps, jumps, max(1, (n - w) // 20)


def relisten(film, start, length, tmp):
    import mlx_whisper
    w = Path(tmp) / "win.wav"
    subprocess.run([FF, "-v", "error", "-y", "-ss", str(max(0, start - 0.3)), "-to", str(start + length + 0.6),
                    "-i", str(film), "-vn", str(w)], check=True)
    return mlx_whisper.transcribe(str(w), path_or_hf_repo=WHISPER)["text"]


def words(s):
    s = s.lower().replace("2,000", "two thousand").replace("500", "five hundred").replace("10", "ten")
    return [x for x in re.sub(r"[^a-z' ]", " ", s).split() if x]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("film")
    ap.add_argument("--score")
    ap.add_argument("--timeline")
    ap.add_argument("--narration")
    ap.add_argument("--voices", default=None, help="dir holding nia_<id>.wav (default: <timeline>/../voices)")
    ap.add_argument("--report")
    a = ap.parse_args()
    fails, warns, log = [], [], []

    def rec(level, msg):
        log.append(f"- [{level}] {msg}")
        (fails if level == "FAIL" else warns if level == "WARN" else []).append(msg)

    with tempfile.TemporaryDirectory() as tmp:
        if a.score:
            sv, sm = stems(a.score, tmp)
            gap = vol(sm) - vol(sv)
            rec("PASS" if gap >= 15 else "FAIL", f"score vocals: vocal stem {gap:.1f} dB under the music (need >= 15)")
            for label, f in (("score", a.score),):
                d = drone_runs(f)
                rec("FAIL" if d else "PASS", f"{label} drone: {len(d)} sustained low tones {d[:6]}")
            reps, jumps, tot = loops_and_jumps(a.score)
            if reps or jumps:
                rec("WARN", f"score repeats: {len(reps)}/{tot} 4s passages near-identical elsewhere {reps[:6]}; "
                            f"hard jumps at {jumps[:10]}s — listen at these times or have Matt pick")
        d = drone_runs(a.film)
        rec("FAIL" if d else "PASS", f"film drone: {len(d)} sustained low tones {d[:6]}")

        fv, fm = stems(a.film, tmp)
        total = dur(a.film)
        W = [x / 2 for x in range(0, int(total * 2) - 4, 4)]
        music = [vol(fm, t, t + 2) for t in W]
        voice = [vol(fv, t, t + 2) for t in W]
        spoken = [v for v in voice if v > -35]
        if spoken:
            na = sum(spoken) / len(spoken)
            over = [(t, round(m, 1)) for t, m in zip(W, music) if m > na]
            rec("FAIL" if over else "PASS", f"balance: narration avg {na:.1f} dB, music max {max(music):.1f} dB, "
                                           f"music louder than narration at {over[:8]}")
            close = [(t, round(m, 1), round(v, 1)) for t, m, v in zip(W, music, voice) if v > -35 and m > v - 6]
            if close:
                rec("WARN", f"music within 6 dB of the voice while speaking at {close[:8]}")

        if a.timeline and a.narration:
            tl = json.load(open(a.timeline))
            texts = {f"nia_{x['id']}.wav": x["text"] for x in json.load(open(a.narration))}
            vdir = Path(a.voices) if a.voices else Path(a.timeline).resolve().parent.parent / "voices"
            for fname, st in tl.get("narration", []):
                want = words(texts.get(fname, ""))
                got = words(relisten(a.film, st, dur(vdir / fname), tmp))
                hit = sum(1 for x in want if x in got) / max(1, len(want))
                rec("PASS" if hit >= 0.8 else "FAIL", f"line {fname} @ {st:.1f}s heard {hit*100:.0f}%")

        m = subprocess.run([FF, "-i", str(a.film), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
        I = re.findall(r"I:\s+(-?[\d.]+) LUFS", m); lra = re.findall(r"LRA:\s+([\d.]+) LU", m)
        pk = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", m)
        msg = f"loudness: {I[-1] if I else '?'} LUFS, LRA {lra[-1] if lra else '?'} LU, true peak {pk[-1] if pk else '?'} dBFS"
        rec("WARN" if lra and float(lra[-1]) > 15 else "PASS", msg)

    verdict = "FAIL" if fails else "PASS"
    out = [f"# audio_check — {Path(a.film).name}", f"**Verdict: {verdict}** — {len(fails)} fail, {len(warns)} warn",
           "I cannot hear. PASS = the measured failure modes are absent, not that it sounds good.", ""] + log
    text = "\n".join(out)
    print(text)
    if a.report:
        Path(a.report).write_text(text + "\n")
    return 1 if fails else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # noqa: BLE001
        print(f"audio_check could not run: {e}")
        sys.exit(2)
