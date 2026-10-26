#!/usr/bin/env python3
"""promo_mix.py — promo stage 08: the soundtrack. Narration + ducked instrumental bed + SFX + the sting.

The Sitka recipe (sitka-video/tools/mix_audio.py, 2026-10-22), made generic:
  * narration: every edl.json "audio" vo wav at its rec_in (the words the edit was cut to);
  * bed: promo.json music.bed (a Song Forge instrumental, `promo_music.py` makes one). Its big
    downbeat (music.hit, seconds into the bed; auto-detected when null) is offset to land
    EXACTLY on the end-card slam, which edit_to_words put AFTER the last word, so the hit never
    masks a word. Gain music.gain, sidechain-ducked by the voice (threshold 0.015, ratio 8,
    attack 20 ms, release 420 ms), faded out music.tail s after the slam over music.fade s;
  * SFX synthesised in numpy (no samples to license): a hit + flash-whoosh on every title slam,
    a blip on every callout, a whoosh into every overlay, and at the slam a resolved major-chord
    sting (bell partials + string pad + sub boom + 3 s reverb) that rings out under the end card;
  * the bed gets a -4 dB presence carve at 2.5 kHz (music.carve_db) so consonants survive the music;
  * the whole mix: two-pass loudnorm with linear=true (a STATIC gain to -16 LUFS / TP -1.5,
    never dynamic compression of the narration; gates-and-qc "static gain").
Writes final/mix.wav (48 kHz stereo) and stems final/_vo.wav, final/_fx.wav, final/_music.wav
(the ducked bed, before the master gain) so promo_gates can check voice-over-music level.

Usage:  ~/chatterbox-env/bin/python pipeline-tools/promo_mix.py projects/<film>
Exit 0 = mix written; 2 = could not run (no edl/bed).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from promo_common import duration, load_promo, run  # noqa: E402

SR = 48000
rng = np.random.default_rng(7)


def rd(path: Path) -> np.ndarray:
    x, sr = sf.read(str(path), always_2d=True)
    if sr != SR:
        tmp = path.parent / (path.stem + ".48k.wav")
        run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ar", str(SR), tmp])
        x, sr = sf.read(str(tmp), always_2d=True)
        tmp.unlink()
    return np.repeat(x, 2, axis=1) if x.shape[1] == 1 else x[:, :2]


def place(buf, x, t, gain=1.0):
    i = int(round(t * SR))
    if i < 0:
        x, i = x[-i:], 0
    n = min(len(x), len(buf) - i)
    if n > 0:
        buf[i:i + n] += x[:n] * gain


def reverb(x, secs=2.6, mix=0.35, damp=3.0):
    from scipy.signal import fftconvolve
    n = int(SR * secs)
    t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-t * damp)[:, None]
    ir[:, 0] *= np.exp(-t * 0.6)
    ir /= np.sqrt((ir ** 2).sum(0))
    wet = np.stack([fftconvolve(x[:, c], ir[:, c]) for c in range(2)], 1)
    dry = np.vstack([x, np.zeros((len(wet) - len(x), 2))])
    return dry * (1 - mix) + wet * mix


def sting(root=65.41):
    """resolved major chord on `root` (default C2): bell-like partials, a string pad, a sub boom."""
    L = 6.5
    n = int(SR * L)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    ratios = (1, 2, 3, 4, 5, 6, 8)   # C2 C3 G3 C4 E4 G4 C5 on a C root
    for k, r in enumerate(ratios):
        f = root * r
        pan = 0.5 + 0.35 * np.sin(k * 1.7)
        tone = np.zeros(n)
        for h, amp in ((1, 1.0), (2, 0.45), (3, 0.22), (4, 0.12), (5, 0.06)):
            tone += amp * np.sin(2 * np.pi * f * h * (1 + 0.0015 * (h - 1)) * t) * np.exp(-t * (0.55 + 0.35 * h))
        tone *= np.minimum(1, t / 0.005)
        g = 0.22 if f > 100 else 0.45
        out[:, 0] += tone * g * (1 - pan)
        out[:, 1] += tone * g * pan
    pad = np.zeros(n)
    for r in (2, 2.5198, 3, 4):   # C E G C, equal-tempered E
        for d in (-0.6, 0.0, 0.6):
            pad += np.sin(2 * np.pi * (root * r + d) * t + rng.uniform(0, 6))
    out += (pad * np.minimum(1, t / 0.35) * np.exp(-t / 2.2) * 0.045)[:, None]
    out += (np.sin(2 * np.pi * (42 + 30 * np.exp(-t * 9)) * t) * np.exp(-t * 2.2) * 0.8)[:, None]
    out = reverb(out, 3.2, 0.32, 1.6)
    return out / np.abs(out).max() * 0.9


def hit():
    n = int(SR * 1.4)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * (48 + 110 * np.exp(-t * 16)) * t) * np.exp(-t * 4.0)
    x += rng.standard_normal(n) * np.exp(-t * 28) * 0.45
    return reverb(np.stack([x, x], 1), 1.6, 0.25, 3.0) * 0.9


def whoosh(L=0.7, rev=False):
    from scipy.signal import butter, sosfilt
    n = int(SR * L)
    t = np.arange(n) / SR
    env = (t / L) ** 3 if rev else np.sin(np.pi * np.clip(t / L, 0, 1)) ** 2
    nz = rng.standard_normal(n)
    lo = sosfilt(butter(2, 900, "low", fs=SR, output="sos"), nz)
    hi = sosfilt(butter(2, 3500, "high", fs=SR, output="sos"), nz)
    m = (lo * (1 - t / L) + hi * (t / L) * 0.6) * env
    return np.stack([m * (1 - 0.3 * t / L), m * (0.7 + 0.3 * t / L)], 1) * 0.55


def blip(f=1760):
    n = int(SR * 0.16)
    t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 1.5 * t)) * np.exp(-t * 32) * 0.28
    return np.stack([x, x], 1)


def find_hit(bed: Path, want_after: float) -> float:
    """The bed's biggest downbeat: the strongest onset-strength peak in its last 45%, at least
    `want_after` s from the start (so the bed can be offset onto the slam without starting late)."""
    import librosa
    y, sr = librosa.load(str(bed), sr=22050, mono=True)
    env = librosa.onset.onset_strength(y=y, sr=sr)
    times = librosa.times_like(env, sr=sr)
    rms = librosa.feature.rms(y=y)[0]
    rms = np.interp(times, librosa.times_like(rms, sr=sr), rms)
    lo = max(want_after, times[-1] * 0.55)
    ok = (times >= lo) & (times <= times[-1] - 4.0)
    if not ok.any():
        ok = times >= times[-1] * 0.5
    score = env * (rms / (rms.max() + 1e-9))
    return float(times[ok][np.argmax(score[ok])])


def main() -> int:
    film = Path(sys.argv[1]).resolve()
    cfg = load_promo(film)
    try:
        edl = json.loads((film / "edl.json").read_text())
    except Exception as e:  # noqa: BLE001
        print(f"[mix] no edl.json ({e})", file=sys.stderr)
        return 2
    mu = cfg["music"]
    bed = film / mu["bed"] if mu.get("bed") else film / "music" / "bed.wav"
    if not bed.exists():
        print(f"[mix] no music bed at {bed.relative_to(film)} (run promo_music.py or set promo.json music.bed)",
              file=sys.stderr)
        return 2
    total = float(edl["dur"])
    ec = edl.get("endcard")
    slam = float(ec["rec_in"]) if ec else total - 1.5
    N = int(SR * (total + 0.2))

    vo = np.zeros((N, 2))
    for au in edl.get("audio", []):
        if au.get("kind", "vo") == "vo":
            place(vo, rd(film / au["file"]), float(au["rec_in"]))
    fx = np.zeros((N, 2))
    events = []
    for tt in edl.get("titles", []):
        place(fx, whoosh(0.5, True), float(tt["rec_in"]) - 0.5, 0.5)
        place(fx, hit(), float(tt["rec_in"]), 0.55)
        events.append(("title hit", tt["rec_in"]))
    cpath = film / "callouts.json"
    for co in (json.loads(cpath.read_text()).get("callouts", []) if cpath.exists() else []):
        place(fx, blip(), float(co["rec_in"]), 0.5)
        events.append(("callout blip", co["rec_in"]))
    for ov in edl.get("overlays", []):
        if ov.get("whoosh") is False:      # cue {"whoosh": false}: an overlay that starts ON a spoken word
            continue                       # (kinetic type at a line's first word) must not get a whoosh over it
        place(fx, whoosh(0.6), float(ov["rec_in"]) - 0.3, 0.35)
        events.append(("overlay whoosh", ov["rec_in"]))
    place(fx, hit(), slam, 0.8)
    # music.sting_root (Hz, added 2026-10-22 sitka_v3): the resolved chord in the BED's key. The default C
    # root clashed with a bed in A major (Body Movin' "Star Jumps Coach"); A1 = 55.0, F#1 = 46.25, G1 = 49.0 ...
    place(fx, sting(float(mu.get("sting_root", 65.41))), slam, float(mu.get("sting_gain", 0.9)))
    events.append(("end slam + sting", slam))
    final = film / "final"
    final.mkdir(exist_ok=True)
    sf.write(str(final / "_vo.wav"), vo, SR)
    sf.write(str(final / "_fx.wav"), fx, SR)

    bed_len = duration(bed)
    bed_hit = float(mu["hit"]) if mu.get("hit") is not None else find_hit(bed, slam)
    off = bed_hit - slam          # seconds of bed skipped so its downbeat lands on the slam
    if off + total > bed_len + 0.5 and bed_len > total + 0.5:
        # 10/26 moonstone: the downbeat finder picked a hit near the bed's end, leaving ~4 s of music
        # under a 29 s film and a silent mix (loudnorm measured -inf). Keep the whole film covered.
        print(f"[mix] downbeat at {bed_hit:.1f}s leaves the film short of bed; using offset "
              f"{bed_len - total - 0.5:.1f}s so the bed covers the whole film")
        off = bed_len - total - 0.5
    if off + total > bed_len + 0.5:
        print(f"[mix] WARNING: the bed ({bed_len:.1f}s) runs out {off + total - bed_len:.1f}s before the film ends")
    gain = float(mu.get("gain", 0.55))
    fade_st = slam + float(mu.get("tail", 1.1))
    head = (f"[1:a]aresample={SR},atrim=start={off:.3f},asetpts=PTS-STARTPTS," if off >= 0
            else f"[1:a]aresample={SR},adelay={int(-off * 1000)}|{int(-off * 1000)},")
    # carve the voice's presence band out of the bed (-4 dB @2.5 kHz): in sitka_demo the full mix
    # turned "light pole" into "light pull" for whisper while the clean stem read right
    duck = (head + f"volume={gain},equalizer=f=2500:t=q:w=1.2:g={mu.get('carve_db', -4)},"
            f"afade=t=in:st=0:d=0.8,afade=t=out:st={fade_st:.2f}:d={mu.get('fade', 1.6)}[bed];"
            "[0:a]asplit=2[vk][vm];"
            "[bed][vk]sidechaincompress=threshold=0.015:ratio=8:attack=20:release=420:makeup=1[duck];")
    # stem: the ducked bed alone (for the voice-over-music check)
    run(["ffmpeg", "-v", "error", "-y", "-i", final / "_vo.wav", "-i", bed, "-filter_complex",
         duck + f"[vm]anullsink;[duck]atrim=0:{total:.3f}[m]", "-map", "[m]", "-ar", str(SR), final / "_music.wav"])
    pre = (duck + f"[duck][vm][2:a]amix=inputs=3:normalize=0:duration=first,"
           f"atrim=0:{total:.3f},afade=t=out:st={total - 1.2:.2f}:d=1.2")
    ins = ["-i", final / "_vo.wav", "-i", bed, "-i", final / "_fx.wav"]
    # two-pass loudnorm: measure, then apply ONE static gain (linear=true with the measurements)
    r = subprocess.run(["ffmpeg", "-v", "info", "-hide_banner", "-nostats", "-y", *[str(x) for x in ins],
                        "-filter_complex", pre + ",loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json[a]",
                        "-map", "[a]", "-f", "null", "-"], capture_output=True, text=True)
    js = r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1]
    try:
        m = json.loads(js)
        ln = (f"loudnorm=I=-16:TP=-1.5:LRA=11:linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
              f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}")
    except Exception:  # noqa: BLE001
        print("[mix] loudnorm measure pass unreadable; falling back to single-pass", file=sys.stderr)
        ln = "loudnorm=I=-16:TP=-1.5:LRA=11:linear=true"
    run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", pre + f",{ln},aresample={SR}[a]",
         "-map", "[a]", "-ar", str(SR), "-c:a", "pcm_s24le", final / "mix.wav"])
    meta = {"bed": str(bed.relative_to(film)), "bed_len": round(bed_len, 3), "bed_hit": round(bed_hit, 3),
            "bed_hit_source": "promo.json" if mu.get("hit") is not None else "auto (onset x rms)",
            "bed_offset": round(off, 3), "slam": slam, "total": total, "gain": gain,
            "events": [{"what": w, "t": round(float(t), 3)} for w, t in events]}
    (final / "mix.json").write_text(json.dumps(meta, indent=1))
    print(f"[mix] final/mix.wav {total:.2f}s; bed {bed.name} downbeat {bed_hit:.2f}s -> slam {slam:.2f}s "
          f"(offset {off:+.2f}s); {len(events)} sfx events")
    return 0


if __name__ == "__main__":
    sys.exit(main())
