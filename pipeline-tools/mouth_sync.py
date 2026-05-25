#!/usr/bin/env python3
"""mouth_sync.py — match voices to a scene's EXISTING mouth motion.

The animation already opens/closes mouths (ambient). This tool, per character:
  1. measures mouth-open activity in that character's mouth box, frame by frame
  2. finds the "talking beats" (open intervals) — and which characters are
     actually opening their mouths vs. staying closed
  3. plays ONLY that character's voice during their open beats, silent when closed

It NEVER touches a video pixel — it only gates/places audio. Reusable per scene.

Usage:
  mouth_sync.py --clip scene.mp4 --out synced.mp4 [--music bed.mp3] \
     --char "hank:There you are, old friend.:760,330,1000,480" \
     --char "doug:Hank! I found you!:100,250,440,470"
"""
import argparse, subprocess, sys, tempfile
from pathlib import Path
import cv2, numpy as np

CHATTERBOX_PY = Path.home() / "chatterbox-env" / "bin" / "python"
CHARACTER_VOICE = Path(__file__).resolve().parent / "character_voice.py"


def _load_gray(clip):
    cap = cv2.VideoCapture(clip); fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frames = []
    while True:
        ok, fr = cap.read()
        if not ok: break
        frames.append(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY).astype(np.int16))
    cap.release()
    return frames, fps


def open_signal_residual(frames, fps, box):
    """LOCAL mouth motion with global (camera/pan) motion subtracted, so only a
    real mouth open/close registers — not the whole head or camera moving."""
    x1, y1, x2, y2 = box
    sig = []
    for i in range(1, len(frames)):
        glob = float(np.mean(np.abs(frames[i] - frames[i - 1])))          # whole-frame (camera) motion
        loc = float(np.mean(np.abs(frames[i][y1:y2, x1:x2]
                                   - frames[i - 1][y1:y2, x1:x2])))         # mouth-box motion
        sig.append(max(0.0, loc - 1.3 * glob))                            # residual = mouth beyond global
    return np.array([0.0] + sig), fps


def find_intervals(sig, fps, thresh_frac=0.35, min_len=0.12, merge_gap=0.18):
    if sig.size == 0:
        return []
    m = sig.max() or 1.0
    active = sig > thresh_frac * m
    runs = []; s = None
    for i, a in enumerate(active):
        if a and s is None: s = i
        if (not a) and s is not None: runs.append((s, i)); s = None
    if s is not None: runs.append((s, len(active)))
    out = []
    for s, e in runs:
        ts, te = s / fps, e / fps
        if out and ts - out[-1][1] <= merge_gap:
            out[-1] = (out[-1][0], te)
        else:
            out.append((ts, te))
    return [(round(s, 2), round(e, 2)) for s, e in out if e - s >= min_len]


def gen_voice(character, line, out_wav):
    subprocess.run([str(CHATTERBOX_PY), str(CHARACTER_VOICE),
                    "--character", character, "--line", line,
                    "--out", str(out_wav)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clip", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--music", default=None)
    ap.add_argument("--char", action="append", default=[],
                    help='"name:line:x1,y1,x2,y2"')
    ap.add_argument("--thresh", type=float, default=0.35)
    args = ap.parse_args()

    tmp = Path(tempfile.mkdtemp())
    chars = []
    for spec in args.char:
        name, line, box_s = spec.split(":", 2)
        chars.append((name, line, [int(v) for v in box_s.split(",")]))

    frames, fps = _load_gray(args.clip)
    sigs = [open_signal_residual(frames, fps, box)[0] for (_, _, box) in chars]
    n = len(frames)
    peak = max((float(s.max()) for s in sigs), default=0.0)
    floor = peak * args.thresh
    # winner-take-all per frame: only the character whose mouth moves most (above
    # the floor) is "talking" that frame — never two voices at once.
    masks = [np.zeros(n) for _ in chars]
    for i in range(n):
        vals = [s[i] for s in sigs]
        j = int(np.argmax(vals)) if vals else -1
        if j >= 0 and vals[j] >= floor and vals[j] > 0:
            masks[j][i] = 1.0

    inputs = ["-i", args.clip]
    filt = []
    voiced = []
    idx = 1  # input index (0 = video)
    for (name, line, box), mask in zip(chars, masks):
        ivs = find_intervals(mask, fps, thresh_frac=0.5, min_len=0.18, merge_gap=0.22)
        total = sum(e - s for s, e in ivs)
        print(f"[mouth_sync] {name}: {'TALKING' if ivs else 'closed (silent)'} "
              f"— {len(ivs)} beat(s), {total:.2f}s: {ivs}")
        if not ivs:
            continue
        wav = tmp / f"{name}.wav"
        gen_voice(name, line, wav)
        start_ms = int(ivs[0][0] * 1000)
        cond = "+".join(f"between(t,{s},{e})" for s, e in ivs)
        inputs += ["-i", str(wav)]
        filt.append(f"[{idx}:a]adelay={start_ms}|{start_ms},"
                    f"volume='if(gt({cond},0),1,0)':eval=frame[v{idx}]")
        voiced.append(f"[v{idx}]")
        idx += 1

    if not voiced:
        print("[mouth_sync] no character mouths opened — nothing to place")
        return

    # mix voices (+ optional ducked music) and mux over the UNTOUCHED video
    mix_inputs = "".join(voiced)
    if args.music:
        inputs += ["-i", args.music]
        filt.append(f"[{idx}:a]volume=0.20[mus]")
        filt.append(f"{mix_inputs}amix={len(voiced)}:duration=longest:normalize=0[spkraw]")
        filt.append("[spkraw]asplit=2[spk1][spk2]")
        filt.append("[mus][spk1]sidechaincompress=threshold=0.03:ratio=8:attack=5:release=300[duck]")
        filt.append("[duck][spk2]amix=2:duration=first:normalize=0,apad[a]")
    else:
        filt.append(f"{mix_inputs}amix={len(voiced)}:duration=longest:normalize=0,apad[a]")

    cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs,
           "-filter_complex", ";".join(filt),
           "-map", "0:v", "-map", "[a]",
           "-c:v", "copy", "-c:a", "aac", "-shortest", args.out]
    subprocess.run(cmd, check=True)
    print(f"[mouth_sync] wrote {args.out}")


if __name__ == "__main__":
    main()
