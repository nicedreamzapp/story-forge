#!/usr/bin/env python3
"""final_audio_gate.py — the last thing that touches a film's sound: measure, fix, or fail loudly.

Runs in the final mux/deliver step (promo_deliver.py for promos, bin/build-episode's assemble stage
for films). On FILM.mp4:
  1. TRUNCATION IN: the audio that actually DECODES (not the container's claim) must cover the
     picture. Shorter = a cut-off ending upstream: FAIL, never padded over (padding hides a lost word).
  2. MEASURE (pass 1): ffmpeg loudnorm print_format=json, integrated loudness + true peak.
  3. FIX (pass 2), always a STATIC gain to the target (gates-and-qc: "static gain, never loudnorm dynamic"):
       * the gain fits under the peak ceiling -> loudnorm linear=true with the pass-1 measurements;
       * it does not -> the same static gain + a 4x-oversampled lookahead peak limiter
         (alimiter, latency-compensated, auto-level off) that only shaves the peaks over the ceiling.
     The picture is stream-copied; audio AAC 320k 48 kHz.
  4. VERIFY on the OUTPUT with an independent ebur128 decode (loudnorm's own summary can under-report,
     lemo-opuscar mux.sh): integrated within +/-tol of the target, true peak <= the max. Off target ->
     one corrective pass from the new measurement; still off -> FAIL, output deleted.
  5. TRUNCATION OUT: decoded output audio >= the video duration (one frame of slack). Shorter = FAIL,
     output deleted.
Defaults -14 LUFS integrated, true peak <= -1.0 dBTP (limiter ceiling -1.5, AAC adds a little), tol 0.5 LU.
A silent or undecodable track is a FAIL, never "skipped".

Usage:  python3 pipeline-tools/final_audio_gate.py FILM.mp4 [--out OUT.mp4 | --in-place]
                                                 [--lufs -14] [--tp -1.0] [--tol 0.5] [--report gate.json]
          (no --out/--in-place = measure only: PASS if already on target, else FAIL with the numbers)
Exit 0 = PASS (or FIXED and verified); 1 = FAIL (message says which check); 2 = could not run.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"     # launchd PATH has no homebrew (build-episode)
FFPROBE = shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"
CEILING_MARGIN = 0.5      # limiter / loudnorm TP target sits this far under the gate's max (AAC overshoot)


class GateFail(Exception):
    pass


def _run(cmd: list) -> subprocess.CompletedProcess:
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True)


def video_duration(path: Path) -> tuple[float, float]:
    """(duration of the first video stream, fps). Falls back to the container duration."""
    r = _run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries",
              "stream=duration,r_frame_rate:format=duration", "-of", "json", path])
    js = json.loads(r.stdout or "{}")
    st = (js.get("streams") or [{}])[0]
    d = st.get("duration") or (js.get("format") or {}).get("duration")
    if d in (None, "N/A"):
        raise GateFail(f"no video stream / duration in {path.name}")
    num, _, den = (st.get("r_frame_rate") or "24/1").partition("/")
    fps = float(num) / float(den or 1) if float(den or 1) else 24.0
    return float(d), fps or 24.0


def decoded_audio_seconds(path: Path) -> float:
    """Seconds of the first audio stream that actually decode (the container can claim more)."""
    if not _run([FFPROBE, "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_type",
                 "-of", "csv=p=0", path]).stdout.strip():
        raise GateFail(f"no audio stream in {path.name}")
    r = _run([FFMPEG, "-v", "error", "-nostats", "-i", path, "-map", "0:a:0", "-f", "null", "-",
              "-progress", "pipe:1"])
    us = [int(m) for m in re.findall(r"^out_time_us=(\d+)", r.stdout, re.M)]
    if not us:
        raise GateFail(f"the audio in {path.name} does not decode: {(r.stderr or '').strip()[-200:]}")
    return max(us) / 1e6


def ebur128(path: Path) -> dict:
    r = _run([FFMPEG, "-hide_banner", "-nostats", "-i", path, "-map", "0:a:0",
              "-af", "ebur128=peak=true", "-f", "null", "-"])
    txt = r.stderr
    summ = txt[txt.rfind("Summary:"):] if "Summary:" in txt else ""

    def grab(pat):
        m = re.search(pat, summ)
        return float(m.group(1)) if m else None
    return {"I": grab(r"I:\s+(-?[\d.]+|-inf) LUFS"), "TP": grab(r"Peak:\s+(-?[\d.]+|-inf) dBFS"),
            "LRA": grab(r"LRA:\s+(-?[\d.]+) LU")}


def loudnorm_measure(path: Path, lufs: float, tp: float) -> dict:
    r = _run([FFMPEG, "-hide_banner", "-nostats", "-i", path, "-map", "0:a:0",
              "-af", f"loudnorm=I={lufs}:TP={tp}:LRA=11:print_format=json", "-f", "null", "-"])
    js = r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1]
    try:
        m = json.loads(js)
        out = {k: float(m[k]) for k in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")}
    except Exception:  # noqa: BLE001
        raise GateFail(f"loudnorm could not measure {path.name}: {(r.stderr or '').strip()[-200:]}")
    if not all(math.isfinite(v) for v in out.values()) or out["input_i"] < -70:
        raise GateFail(f"the audio in {path.name} is silent (integrated {out['input_i']} LUFS); a film with no "
                       "sound is broken, not quiet")
    return out


def _apply(src: Path, out: Path, af: str) -> None:
    r = _run([FFMPEG, "-v", "error", "-y", "-i", src, "-map", "0:v:0", "-map", "0:a:0", "-c:v", "copy",
              "-af", af, "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-movflags", "+faststart", out])
    if r.returncode != 0 or not out.exists() or out.stat().st_size == 0:
        out.unlink(missing_ok=True)
        raise GateFail(f"ffmpeg failed writing {out.name}: {(r.stderr or '').strip()[-300:]}")


def _filter(m: dict, lufs: float, ceiling: float) -> tuple[str, str]:
    """(audio filter, method) for a STATIC gain from measurement m to `lufs`, peaks held under `ceiling`."""
    gain = lufs - m["input_i"]
    if m["input_tp"] + gain <= ceiling:
        return (f"loudnorm=I={lufs}:TP={ceiling}:LRA=11:linear=true:measured_I={m['input_i']}:"
                f"measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
                f"offset={m['target_offset']}:print_format=summary,aresample=48000",
                f"static gain {gain:+.2f} dB (loudnorm linear)")
    lim = 10 ** (ceiling / 20)
    return (f"volume={gain:.3f}dB,aresample=192000,alimiter=limit={lim:.5f}:attack=2:release=60:level=false:"
            f"latency=true,aresample=48000",
            f"static gain {gain:+.2f} dB + 4x-oversampled peak limiter at {ceiling} dBTP "
            f"(peaks would reach {m['input_tp'] + gain:+.1f})")


def gate(src: Path, out: Path | None = None, lufs: float = -14.0, tp_max: float = -1.0,
         tol: float = 0.5) -> dict:
    """Run the gate. Returns the report dict ("verdict": PASS | FIXED | FAIL, "why")."""
    src = Path(src)
    rep = {"ran": time.strftime("%Y-%m-%dT%H:%M:%S"), "file": str(src), "target_lufs": lufs, "tp_max": tp_max,
           "tol": tol, "steps": []}
    tmp = None
    try:
        vdur, fps = video_duration(src)
        slack = max(1.0 / fps, 0.034)
        adur = decoded_audio_seconds(src)
        rep.update(video_s=round(vdur, 3), audio_in_s=round(adur, 3))
        if adur < vdur - slack:
            raise GateFail(f"TRUNCATED INPUT: audio decodes {adur:.3f}s, picture runs {vdur:.3f}s "
                           f"({(vdur - adur) * 1000:.0f} ms short). Fix the mix/mux upstream; padding would hide it")
        before = ebur128(src)
        rep["before"] = before
        on_target = (before["I"] is not None and abs(before["I"] - lufs) <= tol
                     and before["TP"] is not None and before["TP"] <= tp_max)
        if out is None or (on_target and Path(out).resolve() == src.resolve()):
            # measure-only, or already on target in place: nothing to write (no extra AAC generation)
            rep["verdict"] = "PASS" if on_target else "FAIL"
            rep["output"], rep["output_bytes"] = str(src), src.stat().st_size
            rep["why"] = (f"integrated {before['I']} LUFS (target {lufs}+/-{tol}), true peak {before['TP']} dBTP "
                          f"(max {tp_max}); audio {adur:.2f}s covers picture {vdur:.2f}s" +
                          ("; already on target, left untouched" if on_target else "; measure-only run, nothing written"))
            return rep
        out = Path(out)
        tmp = out.with_name(out.stem + ".audiogate_tmp" + out.suffix)
        ceiling = tp_max - CEILING_MARGIN
        m = loudnorm_measure(src, lufs, ceiling)
        target = lufs
        for attempt in (1, 2):
            af, method = _filter(m, target, ceiling)
            _apply(src, tmp, af)
            after = ebur128(tmp)
            rep["steps"].append({"attempt": attempt, "method": method, "measured_in": m, "after": after})
            okI = after["I"] is not None and abs(after["I"] - lufs) <= tol
            okT = after["TP"] is not None and after["TP"] <= tp_max
            if okI and okT:
                break
            if attempt == 2:
                raise GateFail(f"LOUDNESS: after two passes the film measures {after['I']} LUFS / true peak "
                               f"{after['TP']} dBTP (want {lufs}+/-{tol}, <= {tp_max}). The mix is probably "
                               "clipping or has very hot transients: tame them in the mix, then re-run")
            # corrective pass: aim off by however far the first pass landed, peaks a little lower
            if after["I"] is not None:
                target = round(target + (lufs - after["I"]), 2)
            ceiling -= 0.5
        aout = decoded_audio_seconds(tmp)
        vout, _ = video_duration(tmp)
        rep.update(audio_out_s=round(aout, 3), video_out_s=round(vout, 3), after=after)
        if aout < vout - slack or aout < adur - slack:
            raise GateFail(f"TRUNCATED OUTPUT: audio decodes {aout:.3f}s, picture {vout:.3f}s, input audio "
                           f"{adur:.3f}s. The output is rejected")
        os.replace(tmp, out)
        tmp = None
        rep["verdict"], rep["output"], rep["output_bytes"] = "FIXED", str(out), out.stat().st_size
        rep["why"] = (f"{before['I']} LUFS / {before['TP']} dBTP -> {after['I']} LUFS / {after['TP']} dBTP "
                      f"({rep['steps'][-1]['method']}); audio {aout:.2f}s covers picture {vout:.2f}s")
        return rep
    except GateFail as e:
        rep["verdict"], rep["why"] = "FAIL", str(e)
        return rep
    finally:
        if tmp is not None:
            Path(tmp).unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("film")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--out", default=None)
    g.add_argument("--in-place", action="store_true")
    ap.add_argument("--lufs", type=float, default=-14.0)
    ap.add_argument("--tp", type=float, default=-1.0)
    ap.add_argument("--tol", type=float, default=0.5)
    ap.add_argument("--report", default=None, help="write the report JSON here")
    a = ap.parse_args()
    src = Path(a.film).resolve()
    if not src.exists():
        print(f"[audio_gate] no file {src}", file=sys.stderr)
        return 2
    out = src if a.in_place else (Path(a.out).resolve() if a.out else None)
    rep = gate(src, out, a.lufs, a.tp, a.tol)
    if a.report:
        Path(a.report).write_text(json.dumps(rep, indent=1))
    print(f"[audio_gate] {rep['verdict']}: {rep['why']}")
    return 1 if rep["verdict"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
