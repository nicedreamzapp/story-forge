#!/usr/bin/env python3
"""surround_mix.py — Story Forge's own 5.1 film panner.

Takes mono/stereo WAV sound sources plus a JSON "mix plan" and renders:
  * a 5.1 film mix: L, R, C, LFE, Ls, Rs — 48 kHz, 24-bit WAV (WAVE_FORMAT_EXTENSIBLE, ffmpeg "5.1" layout)
  * a stereo downmix (ITU-R BS.775 coefficients, then loudness-normalized)
  * optionally an mp4: the video stream copied, 5.1 audio (E-AC3 if this ffmpeg has it, else AAC 5.1)
    as track 1 and the stereo mix (AAC) as track 2.

Pure numpy + scipy + soundfile + ffmpeg. No models.

CLI
---
    surround-mix plan.json --out mix_51.wav --stereo mix_stereo.wav
    surround-mix plan.json --out mix_51.wav --stereo mix_stereo.wav --video in.mp4 --mux out.mp4
Options: --lufs-51 -24  --lufs-stereo -14  --no-loudnorm  --ceiling -1.0  --codec auto|eac3|aac

Coordinates
-----------
Azimuth in degrees, 0 = straight ahead, POSITIVE = to the RIGHT (clockwise seen from above),
180 = directly behind, -90 = hard left. Speakers at ITU-R BS.775 angles:
C 0, R +30, L -30, Rs +110, Ls -110.
Path azimuths are interpolated exactly as written (no wrap-around), so you choose the direction
of travel: 0 -> 90 -> 180 passes down the right side, 0 -> -90 -> -180 passes down the left.
Distance in metres. At or inside "ref_distance" (default 1 m) the source plays at its gain_db.

Panning is pairwise constant-power 2-D VBAP between adjacent speakers (C-R, R-Rs, Rs-Ls, Ls-L, L-C).
"spread" (0..1) blends the VBAP gains toward an equal-power wash over all 5 speakers — that is how
"overhead" is rendered in a flat 5.1 bed. If a keyframe has no "spread", it is derived from distance:
spread = smoothstep(1 - distance / overhead_radius) (overhead_radius default 1.5 m), so a source that
passes very close to the listener blooms into the whole room instead of snapping across.
Keyframe paths are interpolated per sample with monotone cubic (PCHIP, C1-smooth) curves, so gains
and doppler pitch glide with no zipper noise or pitch steps ("interp": "linear" to opt out).

Distance model
--------------
gain    : (ref / max(d, ref)) ** rolloff          (rolloff 1.0 = -6 dB per doubling)
air     : gentle low-pass — the dry signal is crossfaded toward a 2nd-order 5 kHz low-passed copy,
          wet = air_amount * clip((d - ref) / (air_far - ref), 0, 1)   (air_far default 60 m, air_amount 0.85)
doppler : optional ("doppler": true). Variable propagation delay d(t)/343 m/s applied by fractional
          resampling; the minimum delay is subtracted so the source stays in sync with picture.
          "doppler_scale" exaggerates (>1) or softens (<1) the effect.

LFE
---
Each source has "lfe": 0.0-1.0, a linear send of the (distance-attenuated) mono source into the LFE bus.
The bus is low-passed at 120 Hz (8th-order Butterworth, run forward+backward = zero phase, ~ -96 dB/oct).
No +10 dB playback gain compensation is applied: the value you write is what lands in the LFE channel.

Dialog
------
"dialog": true locks the source to Center (no pan, no doppler, no air). Distance gain still applies if a
position is given. "lfe" defaults to 0 for dialog.

Master
------
1. Sum all sources.  2. Measure integrated loudness with ffmpeg loudnorm (ITU-R BS.1770) and apply a
static gain to reach the target (-24 LUFS film by default).  3. Look-ahead peak limiter (5 ms look-ahead,
instant attack, 120 ms release) to "ceiling_db" (default -1.0 dBFS sample peak; 4x-oversampled check).
Stereo: Lo = L + 0.7071*C + 0.7071*Ls,  Ro = R + 0.7071*C + 0.7071*Rs (LFE dropped, per ITU),
then the same loudness (-14 LUFS web default) + limiter.

Plan schema
-----------
{
  "sample_rate": 48000,              # optional, output is always this rate (default 48000)
  "duration": 10.0,                  # optional; default = end of the last source + "tail" (0.5 s)
  "tail": 0.5,
  "master": {                        # all optional; CLI flags override
    "lufs_51": -24.0,                # film target; null = skip loudness normalize
    "lufs_stereo": -14.0,            # web target;  null = skip
    "ceiling_db": -1.0
  },
  "sources": [
    {
      "name": "ship",                # label for logs
      "file": "ship.wav",            # relative to the plan file's folder, or absolute
      "start": 0.0,                  # seconds on the film timeline
      "gain_db": -6.0,
      "trim": [0.0, 8.0],            # optional in/out seconds within the file
      "fade_in": 0.05, "fade_out": 0.05,   # optional, seconds (default 0.005 each, click guard)
      "lfe": 0.3,                    # 0..1 LFE send
      "dialog": false,               # true = locked to Center
      # EITHER a fixed position:
      "position": {"azimuth": 30, "distance": 2.0, "spread": 0.0},
      # OR a moving path (keyframe t is seconds from THIS source's start):
      "path": [
        {"t": 0.0, "azimuth": 0,   "distance": 25},
        {"t": 5.0, "azimuth": 90,  "distance": 0.6},      # overhead: spread auto-blooms
        {"t": 10.0, "azimuth": 180, "distance": 25}
      ],
      "interp": "pchip",             # or "linear"
      "doppler": true, "doppler_scale": 1.0,
      "rolloff": 1.0, "ref_distance": 1.0,
      "air": true, "air_far": 60.0, "air_amount": 0.85,
      "overhead_radius": 1.5
    }
  ]
}
Stereo source files are folded to mono before panning (each source is a point). A source with neither
"position" nor "path" plays at azimuth 0, distance ref (front centre).

Example
-------
{
  "duration": 12,
  "master": {"lufs_51": -24, "lufs_stereo": -14},
  "sources": [
    {"name": "ship", "file": "ship.wav", "start": 1.0, "gain_db": 0, "lfe": 0.4, "doppler": true,
     "path": [{"t": 0, "azimuth": 0, "distance": 30},
              {"t": 4, "azimuth": 20, "distance": 4},
              {"t": 5, "azimuth": 90, "distance": 0.7},
              {"t": 6, "azimuth": 160, "distance": 4},
              {"t": 10, "azimuth": 180, "distance": 30}]},
    {"name": "captain", "file": "captain_line.wav", "start": 2.5, "gain_db": -3, "dialog": true},
    {"name": "radio", "file": "radio.wav", "start": 0, "gain_db": -12,
     "position": {"azimuth": -110, "distance": 2}}
  ]
}
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from math import gcd
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import minimum_filter1d

SR = 48000
SPEED_OF_SOUND = 343.0
CH_NAMES = ["L", "R", "C", "LFE", "Ls", "Rs"]          # output channel order (ffmpeg / WAV 5.1)
# Main speakers in clockwise ring order with ITU angles (positive = right).
RING = [("C", 0.0), ("R", 30.0), ("Rs", 110.0), ("Ls", 250.0), ("L", 330.0)]
CH_INDEX = {n: i for i, n in enumerate(CH_NAMES)}


def db2lin(db: float) -> float:
    return float(10.0 ** (db / 20.0))


# ---------------------------------------------------------------- loading
def load_mono(path: Path, sr: int, trim=None) -> np.ndarray:
    data, fsr = sf.read(str(path), dtype="float64", always_2d=True)
    if trim:
        a = int(round(trim[0] * fsr))
        b = int(round(trim[1] * fsr)) if len(trim) > 1 and trim[1] is not None else data.shape[0]
        data = data[a:b]
    mono = data.mean(axis=1)
    if fsr != sr:
        g = gcd(int(fsr), int(sr))
        mono = signal.resample_poly(mono, sr // g, int(fsr) // g)
    return mono


def apply_fades(x: np.ndarray, sr: int, fi: float, fo: float) -> np.ndarray:
    n = len(x)
    ni, no = min(n, int(fi * sr)), min(n, int(fo * sr))
    if ni > 1:
        x[:ni] *= np.sin(np.linspace(0, np.pi / 2, ni)) ** 2
    if no > 1:
        x[n - no:] *= np.cos(np.linspace(0, np.pi / 2, no)) ** 2
    return x


# ---------------------------------------------------------------- trajectories
def trajectory(src: dict, n: int, sr: int):
    """Per-sample azimuth (deg), distance (m), spread (0..1) or None for auto."""
    t = np.arange(n) / sr
    if "path" in src and src["path"]:
        kf = sorted(src["path"], key=lambda k: k["t"])
        kt = np.array([float(k["t"]) for k in kf])
        az = np.array([float(k.get("azimuth", 0.0)) for k in kf])
        di = np.array([float(k.get("distance", src.get("ref_distance", 1.0))) for k in kf])
        has_spread = all("spread" in k for k in kf)
        sp = np.array([float(k.get("spread", 0.0)) for k in kf])
        if len(kt) == 1:
            return (np.full(n, az[0]), np.full(n, di[0]), np.full(n, sp[0]) if has_spread else None)
        if np.any(np.diff(kt) <= 0):
            raise ValueError(f"source {src.get('name')}: path keyframe times must be strictly increasing")
        tc = np.clip(t, kt[0], kt[-1])            # hold first/last keyframe outside the path
        if src.get("interp", "pchip") == "linear":
            f = lambda y: np.interp(tc, kt, y)
        else:
            f = lambda y: PchipInterpolator(kt, y)(tc)
        a, d = f(az), np.maximum(f(di), 0.05)
        s = np.clip(f(sp), 0, 1) if has_spread else None
        return a, d, s
    pos = src.get("position", {})
    a = np.full(n, float(pos.get("azimuth", 0.0)))
    d = np.full(n, max(float(pos.get("distance", src.get("ref_distance", 1.0))), 0.05))
    s = np.full(n, float(pos["spread"])) if "spread" in pos else None
    return a, d, s


def vbap_gains(az_deg: np.ndarray) -> np.ndarray:
    """Pairwise constant-power 2-D VBAP. Returns (n, 5) gains in RING order, sum of squares = 1."""
    a = np.mod(az_deg, 360.0)
    n = len(a)
    g = np.zeros((n, len(RING)))
    for i in range(len(RING)):
        a1 = RING[i][1]
        a2 = RING[(i + 1) % len(RING)][1]
        span = (a2 - a1) % 360.0
        rel = (a - a1) % 360.0
        m = rel <= span + 1e-9
        m &= ~(g.sum(axis=1) > 0)                 # first pair wins at exact boundaries
        if not m.any():
            continue
        # Solve p = g1*l1 + g2*l2 with unit vectors (angle measured from speaker 1).
        th = np.deg2rad(rel[m])
        sp = np.deg2rad(span)
        g1 = np.sin(sp - th) / np.sin(sp)
        g2 = np.sin(th) / np.sin(sp)
        g1, g2 = np.maximum(g1, 0), np.maximum(g2, 0)
        norm = np.sqrt(g1 ** 2 + g2 ** 2) + 1e-12
        g[m, i] = g1 / norm
        g[m, (i + 1) % len(RING)] = g2 / norm
    return g


def pan_gains(az, dist, spread=None, overhead_radius=1.5) -> np.ndarray:
    """VBAP gains bloomed toward an equal wash by spread. (n, 5) in RING order, constant power.
    Auto spread (no explicit value) = smoothstep(1 - d/overhead_radius), so the bloom eases in
    without a kink. The blend is in the amplitude domain then power-normalised: smooth in s."""
    g = vbap_gains(az)
    if spread is None:
        u = np.clip(1.0 - dist / max(overhead_radius, 1e-6), 0, 1)
        spread = u * u * (3 - 2 * u)
    s = np.asarray(spread, dtype=float)[:, None]
    g = (1 - s) * g + s * (1.0 / np.sqrt(len(RING)))
    return g / np.sqrt((g ** 2).sum(axis=1, keepdims=True))


# ---------------------------------------------------------------- per-source render
def render_source(src: dict, sr: int, total_n: int, base: Path):
    """Returns (main 6-ch contribution, lfe send mono) already placed on the timeline."""
    path = Path(src["file"])
    if not path.is_absolute():
        path = base / path
    x = load_mono(path, sr, src.get("trim"))
    x = apply_fades(x, sr, float(src.get("fade_in", 0.005)), float(src.get("fade_out", 0.005)))
    x *= db2lin(float(src.get("gain_db", 0.0)))
    n = len(x)
    dialog = bool(src.get("dialog", False))
    ref = float(src.get("ref_distance", 1.0))
    az, dist, spread = trajectory(src, n, sr)

    # Doppler: output sample k reads the input at k - (d(k)-d_min)/c * sr.
    if src.get("doppler") and not dialog and "path" in src:
        scale = float(src.get("doppler_scale", 1.0))
        delay = (dist - dist.min()) / SPEED_OF_SOUND * sr * scale
        read_pos = np.arange(n) - delay
        x = np.interp(read_pos, np.arange(n), x, left=0.0, right=0.0)

    # Distance gain.
    rolloff = float(src.get("rolloff", 1.0))
    dgain = (ref / np.maximum(dist, ref)) ** rolloff

    # Air absorption: crossfade toward a gentle low-passed copy.
    if src.get("air", True) and not dialog:
        far = float(src.get("air_far", 60.0))
        amt = float(src.get("air_amount", 0.85))
        wet = amt * np.clip((dist - ref) / max(far - ref, 1e-6), 0, 1)
        if wet.max() > 0:
            sos = signal.butter(2, 5000, "low", fs=sr, output="sos")
            lp = signal.sosfilt(sos, x)
            x = (1 - wet) * x + wet * lp
    x = x * dgain

    out = np.zeros((n, 6))
    if dialog:
        out[:, CH_INDEX["C"]] = x
    else:
        g = pan_gains(az, dist, spread, float(src.get("overhead_radius", 1.5)))
        for i, (name, _) in enumerate(RING):
            out[:, CH_INDEX[name]] = x * g[:, i]
    lfe_amt = float(src.get("lfe", 0.0))
    lfe = x * lfe_amt if lfe_amt > 0 else None

    start = int(round(float(src.get("start", 0.0)) * sr))
    full = np.zeros((total_n, 6))
    full_lfe = np.zeros(total_n)
    if start < total_n:
        m = min(n, total_n - start)
        full[start:start + m] = out[:m]
        if lfe is not None:
            full_lfe[start:start + m] = lfe[:m]
    return full, full_lfe


# ---------------------------------------------------------------- master
def lfe_filter(x: np.ndarray, sr: int) -> np.ndarray:
    sos = signal.butter(8, 120, "low", fs=sr, output="sos")
    return signal.sosfiltfilt(sos, x)


def limiter(x: np.ndarray, sr: int, ceiling_db: float, lookahead_ms=5.0, release_ms=120.0) -> np.ndarray:
    """Linked look-ahead peak limiter over all channels. Instant attack, exponential release."""
    ceil = db2lin(ceiling_db)
    if x.ndim == 1:
        x = x[:, None]
    # 4x oversampled peak estimate per sample (catches inter-sample overs).
    up = signal.resample_poly(x, 4, 1, axis=0)
    peak = np.abs(up).max(axis=1).reshape(-1, 4).max(axis=1)[: x.shape[0]]
    if len(peak) < x.shape[0]:
        peak = np.pad(peak, (0, x.shape[0] - len(peak)))
    need = np.minimum(1.0, ceil / np.maximum(peak, 1e-12))
    if need.min() >= 1.0:
        return x
    la = max(1, int(lookahead_ms * sr / 1000))
    need = minimum_filter1d(need, size=2 * la + 1, mode="nearest")
    # Block-rate release (1 ms blocks), then smooth to sample rate.
    blk = max(1, sr // 1000)
    nb = int(np.ceil(len(need) / blk))
    pad = np.pad(need, (0, nb * blk - len(need)), constant_values=1.0)
    bmin = pad.reshape(nb, blk).min(axis=1)
    rel = np.exp(-1.0 / max(release_ms, 1.0))
    env = np.empty(nb)
    g = 1.0
    for i in range(nb):
        g = bmin[i] if bmin[i] < g else bmin[i] + (g - bmin[i]) * rel
        env[i] = g
    # Min over a block and both neighbours so interpolation never overshoots the need.
    env = np.minimum.reduce([env, np.concatenate([env[1:], env[-1:]]), np.concatenate([env[:1], env[:-1]])])
    gain = np.interp(np.arange(len(need)), np.arange(nb) * blk + blk / 2, env)
    gain = np.minimum(gain, need)                  # hard guarantee
    return x * gain[:, None]


def measure_lufs(x: np.ndarray, sr: int) -> float | None:
    """Integrated loudness via ffmpeg loudnorm (BS.1770). x: (n, ch)."""
    ch = x.shape[1]
    layout = {1: "mono", 2: "stereo", 6: "5.1"}[ch]
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "m.f32"
        x.astype("<f4").tofile(p)
        r = subprocess.run(
            ["ffmpeg", "-hide_banner", "-nostats", "-f", "f32le", "-ar", str(sr), "-ch_layout", layout,
             "-i", str(p), "-af", "loudnorm=print_format=json", "-f", "null", "-"],
            capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not m:
        raise RuntimeError("ffmpeg loudnorm measurement failed:\n" + r.stderr[-800:])
    val = json.loads(m.group(0))["input_i"]
    try:
        v = float(val)
    except ValueError:
        return None
    return None if not np.isfinite(v) or v < -69 else v


def master(x: np.ndarray, sr: int, target_lufs, ceiling_db: float, label: str) -> np.ndarray:
    """Static gain to the loudness target, then limit; repeats (max 8 passes) because limiting
    peaky content (sub rumble) pulls integrated loudness back under the target."""
    if target_lufs is None:
        return limiter(x, sr, ceiling_db)
    cur = measure_lufs(x, sr)
    if cur is None:
        print(f"[{label}] loudness: silent, skipped normalize")
        return limiter(x, sr, ceiling_db)
    print(f"[{label}] loudness {cur:.1f} LUFS, target {target_lufs:.1f} LUFS")
    src, gain_db, y = x, target_lufs - cur, x
    for i in range(8):
        y = limiter(src * db2lin(gain_db), sr, ceiling_db)
        after = measure_lufs(y, sr)
        pk = 20 * np.log10(np.abs(y).max() + 1e-12)
        print(f"[{label}]   pass {i + 1}: gain {gain_db:+.1f} dB -> {after:.1f} LUFS, peak {pk:.2f} dBFS")
        if after is None or abs(after - target_lufs) <= 0.5 or gain_db > 30:
            break
        gain_db += target_lufs - after
    return y


def downmix_stereo(x6: np.ndarray) -> np.ndarray:
    k = 1 / np.sqrt(2)
    L, R, C, _lfe, Ls, Rs = (x6[:, i] for i in range(6))
    return np.stack([L + k * C + k * Ls, R + k * C + k * Rs], axis=1)


def write_wav24(path: Path, x: np.ndarray, sr: int):
    """24-bit WAV with a proper channel mask (via ffmpeg) so players know which channel is which."""
    path.parent.mkdir(parents=True, exist_ok=True)
    layout = {2: "stereo", 6: "5.1"}[x.shape[1]]
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "o.f32"
        np.clip(x, -1, 1).astype("<f4").tofile(p)
        r = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "f32le", "-ar", str(sr),
             "-ch_layout", layout, "-i", str(p), "-c:a", "pcm_s24le", "-rf64", "auto", str(path)],
            capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg wav write failed: {r.stderr[-500:]}")


def has_encoder(name: str) -> bool:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True)
    return re.search(rf"^\s*A\S*\s+{re.escape(name)}\s", r.stdout, re.M) is not None


def mux(video: Path, wav51: Path, wav2: Path, out: Path, codec: str = "auto"):
    if codec == "auto":
        codec = "eac3" if has_encoder("eac3") else "aac"
    br = "640k" if codec == "eac3" else "384k"
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-i", str(video), "-i", str(wav51), "-i", str(wav2),
           "-map", "0:v:0", "-map", "1:a:0", "-map", "2:a:0",
           "-c:v", "copy",
           "-c:a:0", codec, "-b:a:0", br, "-ch_layout:a:0", "5.1",
           "-c:a:1", "aac", "-b:a:1", "256k",
           "-metadata:s:a:0", "title=5.1 Surround", "-metadata:s:a:0", "language=eng",
           "-metadata:s:a:1", "title=Stereo", "-metadata:s:a:1", "language=eng",
           "-disposition:a:0", "default", "-disposition:a:1", "0",
           "-movflags", "+faststart", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg mux failed: {r.stderr[-800:]}")
    print(f"[mux] {out}  (video copy + {codec} 5.1 @ {br} + aac stereo)")
    return codec


# ---------------------------------------------------------------- top level
def render_plan(plan: dict, base: Path, lufs_51="plan", lufs_stereo="plan", ceiling=None):
    sr = int(plan.get("sample_rate", SR))
    m = plan.get("master", {})
    t51 = m.get("lufs_51", -24.0) if lufs_51 == "plan" else lufs_51
    t2 = m.get("lufs_stereo", -14.0) if lufs_stereo == "plan" else lufs_stereo
    ceil = float(ceiling if ceiling is not None else m.get("ceiling_db", -1.0))
    sources = plan["sources"]
    if not sources:
        raise ValueError("plan has no sources")

    if plan.get("duration"):
        total = float(plan["duration"])
    else:
        ends = []
        for s in sources:
            p = Path(s["file"]) if Path(s["file"]).is_absolute() else base / s["file"]
            info = sf.info(str(p))
            ln = info.duration
            if s.get("trim"):
                a = s["trim"][0]
                b = s["trim"][1] if len(s["trim"]) > 1 and s["trim"][1] is not None else ln
                ln = b - a
            ends.append(float(s.get("start", 0.0)) + ln)
        total = max(ends) + float(plan.get("tail", 0.5))
    total_n = int(round(total * sr))

    mix = np.zeros((total_n, 6))
    lfe_bus = np.zeros(total_n)
    for s in sources:
        part, lfe = render_source(s, sr, total_n, base)
        mix += part
        lfe_bus += lfe
        print(f"[src] {s.get('name', s['file'])}: placed at {float(s.get('start', 0)):.2f}s"
              f"{'  (dialog -> C)' if s.get('dialog') else ''}{'  path' if s.get('path') else ''}"
              f"  lfe={float(s.get('lfe', 0)):.2f}")
    mix[:, CH_INDEX["LFE"]] = lfe_filter(lfe_bus, sr)

    st = downmix_stereo(mix)                       # from the pre-master bed, then normalized itself
    mix = master(mix, sr, t51, ceil, "5.1")
    st = master(st, sr, t2, ceil, "stereo")
    return mix, st, sr


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render a 5.1 film mix + stereo downmix from a JSON mix plan.")
    ap.add_argument("plan")
    ap.add_argument("--out", required=True, help="5.1 WAV output (48k/24-bit)")
    ap.add_argument("--stereo", help="stereo downmix WAV output")
    ap.add_argument("--lufs-51", type=float, default=None, help="film loudness target (default plan or -24)")
    ap.add_argument("--lufs-stereo", type=float, default=None, help="stereo loudness target (default plan or -14)")
    ap.add_argument("--no-loudnorm", action="store_true", help="skip loudness normalization (limiter only)")
    ap.add_argument("--ceiling", type=float, default=None, help="limiter ceiling dBFS (default -1.0)")
    ap.add_argument("--video", help="input mp4 to mux the mixes onto")
    ap.add_argument("--mux", help="output mp4 (requires --video)")
    ap.add_argument("--codec", default="auto", choices=["auto", "eac3", "aac"], help="5.1 codec in the mp4")
    a = ap.parse_args(argv)
    if bool(a.video) != bool(a.mux):
        ap.error("--video and --mux go together")

    plan_path = Path(a.plan).resolve()
    plan = json.loads(plan_path.read_text())
    l51 = None if a.no_loudnorm else (a.lufs_51 if a.lufs_51 is not None else "plan")
    l2 = None if a.no_loudnorm else (a.lufs_stereo if a.lufs_stereo is not None else "plan")
    mix, st, sr = render_plan(plan, plan_path.parent, l51, l2, a.ceiling)

    out = Path(a.out).resolve()
    write_wav24(out, mix, sr)
    print(f"[out] 5.1   {out}  ({mix.shape[0] / sr:.2f}s, {sr} Hz, 24-bit, L R C LFE Ls Rs)")
    st_path = Path(a.stereo).resolve() if a.stereo else None
    if st_path:
        write_wav24(st_path, st, sr)
        print(f"[out] stereo {st_path}")
    if a.mux:
        tmp_st = None
        if not st_path:
            tmp_st = Path(tempfile.mkstemp(suffix=".wav")[1])
            write_wav24(tmp_st, st, sr)
        try:
            mux(Path(a.video).resolve(), out, st_path or tmp_st, Path(a.mux).resolve(), a.codec)
        finally:
            if tmp_st:
                tmp_st.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
