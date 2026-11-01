#!/usr/bin/env python3
"""test_surround_mix.py — measured test for tools/surround_mix.py.

Synthesizes a 10 s pink-noise "ship" and a 40 Hz sine rumble, both flying front -> overhead -> rear
with LFE sends, renders them through bin/surround-mix (plus a mux onto a throwaway test video), and
VERIFIES by measurement:
  1. per-channel RMS over time: energy starts in L/R/C and ends in Ls/Rs
  2. LFE carries only < 120 Hz content
  3. no clipping: every channel's peak < -0.1 dBFS (5.1 and stereo)
  4. the mp4 mux has a 5.1 track and a stereo track
Only the final test mix (mix_51.wav + mix_stereo.wav) is kept in sfx-test/panner/.
Nothing is played and nothing is opened.

Run: ~/AI/ComfyUI/venv/bin/python tools/test_surround_mix.py
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "sfx-test" / "panner"
SR = 48000
DUR = 10.0
CH = ["L", "R", "C", "LFE", "Ls", "Rs"]


def pink_noise(n, rng):
    """Voss-McCartney-free pink noise: shape white noise by 1/sqrt(f) in the frequency domain."""
    w = rng.standard_normal(n)
    X = np.fft.rfft(w)
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1]
    X /= np.sqrt(f)
    x = np.fft.irfft(X, n)
    return x / np.abs(x).max() * 0.5


def db(x):
    return 20 * np.log10(np.maximum(x, 1e-6))   # -120 dB display floor


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(7)
    n = int(SR * DUR)
    t = np.arange(n) / SR
    ship = OUT / "src_ship.wav"
    rumble = OUT / "src_rumble.wav"
    sf.write(ship, pink_noise(n, rng), SR, subtype="PCM_24")
    sf.write(rumble, 0.5 * np.sin(2 * np.pi * 40 * t), SR, subtype="PCM_24")

    path = [{"t": 0, "azimuth": 0, "distance": 12},
            {"t": 4, "azimuth": 10, "distance": 3},
            {"t": 5, "azimuth": 90, "distance": 0.6},      # overhead
            {"t": 6, "azimuth": 170, "distance": 3},
            {"t": 10, "azimuth": 180, "distance": 12}]
    plan = {"duration": DUR, "master": {"lufs_51": -24, "lufs_stereo": -14, "ceiling_db": -1.0},
            "sources": [
                {"name": "ship", "file": ship.name, "start": 0, "gain_db": 0, "lfe": 0.3,
                 "doppler": True, "path": path},
                {"name": "rumble", "file": rumble.name, "start": 0, "gain_db": -3, "lfe": 1.0,
                 "path": path}]}
    plan_p = OUT / "plan.json"
    plan_p.write_text(json.dumps(plan, indent=2))
    mix51, mixst = OUT / "mix_51.wav", OUT / "mix_stereo.wav"
    video, muxed = OUT / "test_video.mp4", OUT / "test_mux.mp4"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                    f"color=c=black:s=320x180:r=24:d={DUR}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    str(video)], check=True)
    r = subprocess.run([str(ROOT / "bin" / "surround-mix"), str(plan_p), "--out", str(mix51),
                        "--stereo", str(mixst), "--video", str(video), "--mux", str(muxed)])
    if r.returncode != 0:
        print("RENDER FAILED"); return 1

    x, sr = sf.read(mix51, always_2d=True)
    st, _ = sf.read(mixst, always_2d=True)
    info = sf.info(str(mix51))
    ok = True
    print(f"\n5.1 file: {info.channels} ch, {info.samplerate} Hz, {info.subtype}, {info.duration:.2f}s")
    ok &= info.channels == 6 and info.samplerate == 48000 and info.subtype == "PCM_24"

    # 1. RMS over time
    print("\nPer-channel RMS (dBFS) per 1 s window   [front = L+R+C power, rear = Ls+Rs power]")
    print("  t(s)  " + "".join(f"{c:>7}" for c in CH) + "   front    rear   rear-front")
    win = sr
    fr_rows = []
    for k in range(int(len(x) / win)):
        seg = x[k * win:(k + 1) * win]
        rms = np.sqrt((seg ** 2).mean(axis=0))
        front = np.sqrt((rms[[0, 1, 2]] ** 2).sum())
        rear = np.sqrt((rms[[4, 5]] ** 2).sum())
        fr_rows.append(db(rear) - db(front))
        print(f"  {k:>2}-{k+1:<2} " + "".join(f"{v:7.1f}" for v in db(rms)) +
              f"  {db(front):6.1f}  {db(rear):6.1f}   {db(rear) - db(front):+7.1f}")
    early, late = np.mean(fr_rows[:3]), np.mean(fr_rows[-3:])
    mono_up = fr_rows[-1] > fr_rows[0]
    c1 = early < -10 and late > 10 and mono_up
    print(f"  CHECK energy moves front->rear: first 3 s rear-front {early:+.1f} dB, last 3 s {late:+.1f} dB"
          f"  -> {'PASS' if c1 else 'FAIL'}")
    ok &= c1

    # 1b. zipper check: the actual per-sample pan gains along this path must glide, never step
    sys.path.insert(0, str(ROOT / "tools"))
    import surround_mix as sm
    az, dist, _ = sm.trajectory({"path": path}, n, SR)
    g = sm.pan_gains(az, dist, None, 1.5)
    step = np.abs(np.diff(g, axis=0)).max()
    c1b = step < 1e-3
    print(f"  CHECK no zipper: largest per-sample pan-gain change {step:.2e} (< 1e-3) -> {'PASS' if c1b else 'FAIL'}")
    ok &= c1b

    # 2. LFE band
    lfe = x[:, 3]
    P = np.abs(np.fft.rfft(lfe * np.hanning(len(lfe)))) ** 2
    f = np.fft.rfftfreq(len(lfe), 1 / sr)
    tot = P.sum()
    below = P[f < 120].sum() / tot
    a150 = P[f >= 150].sum() / tot
    a200 = P[f >= 200].sum() / tot
    peak_f = f[np.argmax(P)]
    main_lo = x[:, [0, 1, 2, 4, 5]]
    Pm = (np.abs(np.fft.rfft(main_lo * np.hanning(len(lfe))[:, None], axis=0)) ** 2).sum(axis=1)
    main_hi = Pm[f >= 200].sum() / Pm.sum()
    c2 = below > 0.99 and db(np.sqrt(a200)) < -40
    print(f"\nLFE spectrum: {below * 100:.3f}% of energy < 120 Hz, >=150 Hz {10*np.log10(a150+1e-20):.1f} dB,"
          f" >=200 Hz {10*np.log10(a200+1e-20):.1f} dB rel. total, spectral peak {peak_f:.1f} Hz")
    print(f"  (for contrast, main channels have {main_hi * 100:.1f}% of their energy >= 200 Hz)")
    print(f"  CHECK LFE only < 120 Hz -> {'PASS' if c2 else 'FAIL'}")
    ok &= c2

    # 3. clipping
    print("\nPeaks (dBFS): " + "  ".join(f"{c} {db(np.abs(x[:, i]).max()):.2f}" for i, c in enumerate(CH)) +
          f"  | stereo L {db(np.abs(st[:, 0]).max()):.2f}  R {db(np.abs(st[:, 1]).max()):.2f}")
    pk = max(db(np.abs(x).max()), db(np.abs(st).max()))
    c3 = pk < -0.1
    print(f"  CHECK no clipping (max peak {pk:.2f} dBFS < -0.1) -> {'PASS' if c3 else 'FAIL'}")
    ok &= c3

    # 4. mux
    pr = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                         "stream=index,codec_type,codec_name,channels,channel_layout", "-of", "json", str(muxed)],
                        capture_output=True, text=True)
    streams = json.loads(pr.stdout)["streams"]
    aud = [s for s in streams if s["codec_type"] == "audio"]
    desc = ", ".join(f"{s['codec_name']} {s.get('channel_layout', s.get('channels'))}" for s in aud)
    c4 = len(aud) == 2 and aud[0]["channels"] == 6 and aud[1]["channels"] == 2
    print(f"\nMux: video + {desc}  -> {'PASS' if c4 else 'FAIL'}")
    ok &= c4

    for p in (ship, rumble, plan_p, video, muxed):
        p.unlink(missing_ok=True)
    print(f"\nKept: {mix51}\n      {mixst}")
    print("ALL CHECKS PASS" if ok else "SOME CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
