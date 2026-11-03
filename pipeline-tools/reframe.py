#!/usr/bin/env python3
"""reframe.py — subject-aware 9:16 crop paths for one shot at a time (used by vertical_compose.py).

WHY THIS EXISTS (2026-11-02): a vertical is its own composition, not the wide film center-cropped or
padded. Each shot gets a window 9/16 of the source height wide that follows the SUBJECT: faces first
(Apple Vision, the same on-device detector bin/face_area uses), then whole people, then attention
saliency for products and creatures the face detector misses. Rules:
  * a face is NEVER cut: every kept face (plus a 15 % margin) sits inside the window on every sample;
    the window is full source height, so heads are never cut top or bottom either
  * the camera prefers to stay locked off; it moves only when the subject leaves a dead zone or a face
    would leave the window, and every move uses the CAMERA motion token (quintic ease, >= 0.6 s)
  * when no window can hold the subject (a wide two-shot, a group, a product wider than the vertical
    frame) the shot is FLAGGED with the reason, never quietly padded or chopped; vertical_compose turns
    the flag into a 9:16 re-render request
Probe: tools/subject_probe.swift, compiled on first use into bin/subject_probe (gitignored).
"""
from __future__ import annotations

import json
import statistics
import subprocess
import tempfile
from pathlib import Path

import motion_tokens as mt

SF = Path(__file__).resolve().parent.parent
PROBE_SRC = SF / "tools" / "subject_probe.swift"
PROBE_BIN = SF / "bin" / "subject_probe"

FACE_MARGIN = 0.15      # of the face width, each side
EDGE = 0.01             # of the source width: keep boxes this far from the window edge
DEADZONE = 0.12         # of the source width: target drift tolerated before the camera follows
MIN_MOVE = mt.TOKENS["camera"]["min_dur"]
MAX_MOVE = 1.4
SAMPLE_DT = 0.25
SCENERY_W = 0.75       # a salient box this wide is the scene, not an object: crop freely
MIN_COVER = 0.5         # a discrete object must show at least half of itself in the window
PIN_PAD = 0.04          # of the source width around a callout tip


def ensure_probe() -> Path:
    if not PROBE_BIN.exists() or PROBE_BIN.stat().st_mtime < PROBE_SRC.stat().st_mtime:
        r = subprocess.run(["swiftc", "-O", str(PROBE_SRC), "-o", str(PROBE_BIN)], capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"could not compile {PROBE_SRC.name}: {r.stderr[-400:]}")
    return PROBE_BIN


def probe(pngs: list) -> list:
    if not pngs:
        return []
    r = subprocess.run([str(ensure_probe())] + [str(p) for p in pngs], capture_output=True, text=True)
    out = {}
    for line in r.stdout.splitlines():
        try:
            d = json.loads(line)
            out[d["path"]] = d
        except Exception:
            pass
    return [out.get(str(p), {"path": str(p), "error": "no output"}) for p in pngs]


def video_size(f: Path) -> tuple:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", str(f)], capture_output=True, text=True)
    w, h = r.stdout.strip().split(",")[:2]
    return int(w), int(h)


def sample_times(src_in: float, src_out: float) -> list:
    d = max(0.0, src_out - src_in)
    n = max(3, min(24, int(d / SAMPLE_DT) + 1))
    a, b = src_in + min(0.04, d / 4), src_out - min(0.06, d / 4)
    return [a + (b - a) * k / (n - 1) for k in range(n)]


def grab_frames(f: Path, times: list, kind: str, td: Path, tag: str) -> list:
    out = []
    for k, t in enumerate(times):
        p = td / f"{tag}_{k:02d}.png"
        if kind == "image":
            cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(f), "-frames:v", "1", "-vf", "scale=640:-2", str(p)]
        else:
            cmd = ["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", str(f), "-frames:v", "1",
                   "-vf", "scale=640:-2", str(p)]
        subprocess.run(cmd, capture_output=True)
        out.append(p if p.exists() else None)
    return out


def _subject(det: dict) -> dict:
    """One sample -> what to keep. kind: face | human | saliency | none.
    hard = [x0, x1] that must sit inside the window (faces, people); soft = a box we try to cover."""
    faces = [f for f in det.get("faces", []) if f[4] >= 0.5]
    if faces:
        big = max(f[2] * f[3] for f in faces)
        faces = [f for f in faces if f[2] * f[3] >= 0.25 * big]   # background faces do not steer
        x0 = min(f[0] for f in faces)
        x1 = max(f[0] + f[2] for f in faces)
        margin = FACE_MARGIN * max(f[2] for f in faces)   # trimmed per window in _interval when space is short
        wts = [f[2] * f[3] for f in faces]
        cx = sum((f[0] + f[2] / 2) * w for f, w in zip(faces, wts)) / sum(wts)
        return {"kind": "face", "n": len(faces), "target": cx, "hard": [x0, x1], "margin": margin, "soft": None,
                "boxes": faces}
    hum = [h for h in det.get("humans", []) if h[4] >= 0.5]
    if hum:
        big = max(h[3] for h in hum)
        hum = [h for h in hum if h[3] >= 0.5 * big]
        # the torso band (middle 50 %), not outstretched arms
        x0 = min(h[0] + 0.25 * h[2] for h in hum)
        x1 = max(h[0] + 0.75 * h[2] for h in hum)
        cx = sum(h[0] + h[2] / 2 for h in hum) / len(hum)
        return {"kind": "human", "n": len(hum), "target": cx, "hard": [x0, x1], "soft": None, "boxes": hum}
    sal = [s for s in det.get("saliency", []) if s[4] >= 0.2] or [s for s in det.get("objects", []) if s[4] >= 0.3]
    if sal:
        x0 = min(s[0] for s in sal)
        x1 = max(s[0] + s[2] for s in sal)
        best = max(sal, key=lambda s: s[4] * s[2] * s[3])
        # soft = the MAIN salient object only; a union of everything salient is just "the scene"
        return {"kind": "saliency", "n": len(sal), "target": best[0] + best[2] / 2, "hard": None,
                "soft": [best[0], best[0] + best[2]], "boxes": sal}
    return {"kind": "none", "n": 0, "target": None, "hard": None, "soft": None, "boxes": []}


def _interval(sub: dict, cw: float) -> tuple:
    """Window-center values that keep sub's hard span inside the window (and the window inside the frame)."""
    lo, hi = cw / 2, 1 - cw / 2
    if sub["hard"]:
        x0, x1 = sub["hard"]
        # a face margin is wanted, not required: it shrinks when a close-up face nearly fills the window
        m = min(sub.get("margin", 0.0), max(0.0, (cw - 2 * EDGE - (x1 - x0)) / 2))
        x0, x1 = x0 - m, x1 + m
        lo = max(lo, x1 + EDGE - cw / 2)
        hi = min(hi, x0 - EDGE + cw / 2)
    return lo, hi


def _ok(keys: list, times: list, ivs: list) -> bool:
    return all(lo - 1e-4 <= mt.camera_path(keys, t) <= hi + 1e-4 for t, (lo, hi) in zip(times, ivs) if lo <= hi)


def _pin(sub: dict, x: float) -> dict:
    """A callout tip on this sample: the part being pointed at becomes the subject (it must stay in frame,
    with room for the arrow), whatever else the detector saw."""
    span = [x - PIN_PAD, x + PIN_PAD]
    if sub["hard"]:
        span = [min(span[0], sub["hard"][0]), max(span[1], sub["hard"][1])]
        if span[1] - span[0] > 0.9:      # a face far from the part: the part wins while it is pointed at
            span = [x - PIN_PAD, x + PIN_PAD]
    return {**sub, "kind": "part", "n": 1, "target": x, "hard": span, "margin": 0.0, "soft": None}


def plan_shot(times: list, dets: list, cw: float, pins: list | None = None) -> dict:
    """times (source seconds) + subject_probe results -> {verdict, keys [[t, cx]], cw, reason, ...}.
    verdict: static | pan | center (no subject found: locked center crop, listed as UNCHECKED) | flagged."""
    subs = [_subject(d) for d in dets]
    for t0, t1, x in pins or []:   # (src_t0, src_t1, tip_x): callouts that point into this shot
        subs = [_pin(sb, x) if t0 - 0.05 <= t <= t1 + 0.05 else sb for sb, t in zip(subs, times)]
    kinds = [s["kind"] for s in subs]
    main_kind = max(set(kinds), key=kinds.count)
    if cw >= 0.999:
        return {"verdict": "static", "keys": [[times[0], 0.5], [times[-1], 0.5]], "cw": 1.0, "kind": main_kind,
                "reason": "source is already as narrow as the vertical frame", "subjects": kinds}
    # fill gaps (a missed detection holds the neighbour's target)
    tg = [s["target"] for s in subs]
    if all(t is None for t in tg):
        return {"verdict": "center", "keys": [[times[0], 0.5], [times[-1], 0.5]], "cw": cw, "kind": "none",
                "reason": "no face, person or salient subject found: locked center crop (UNCHECKED, look at it)",
                "subjects": kinds}
    last = next(t for t in tg if t is not None)
    for k in range(len(tg)):
        tg[k] = last = tg[k] if tg[k] is not None else last
    ivs = [_interval(s, cw) for s in subs]
    infeasible = [k for k, (lo, hi) in enumerate(ivs) if lo > hi]
    span = max(((s["hard"][1] - s["hard"][0]) for s in subs if s["hard"]), default=0.0)
    if len(infeasible) >= max(1, round(0.25 * len(subs))):
        many = max(s["n"] for s in subs)
        what = ("a close-up face wider than the window" if main_kind == "face" and many == 1 else
                f"{many} faces" if main_kind == "face" and many > 1 else
                f"{many} people" if main_kind == "human" and many > 1 else f"the {main_kind}")
        return {"verdict": "flagged", "cw": cw, "kind": main_kind, "subjects": kinds,
                "keys": [[times[0], min(max(statistics.median(tg), cw / 2), 1 - cw / 2)]] * 2,
                "reason": f"{what} span {span:.2f} of the width on {len(infeasible)}/{len(subs)} samples; the 9:16 "
                          f"window is {cw:.2f} wide{' (wide two-shot / group)' if many > 1 else ''}: needs a vertical re-render"}
    feas = [(t, iv, g) for t, iv, g in zip(times, ivs, tg) if iv[0] <= iv[1]]
    # 1. locked off if one window position satisfies every sample
    lo_all = max(iv[0] for _, iv, _ in feas)
    hi_all = min(iv[1] for _, iv, _ in feas)
    med = statistics.median(g for _, _, g in feas)
    drift = max(g for _, _, g in feas) - min(g for _, _, g in feas)
    if lo_all <= hi_all and drift <= 2 * DEADZONE:
        p = min(max(med, lo_all), hi_all)
        keys = [[times[0], p], [times[-1], p]]
        verdict = "static"
    else:
        # 2. holds + eased moves: a new hold starts when the intersection empties or the target drifts out of
        #    the dead zone for two samples in a row
        segs, cur = [], [0]
        A, B = ivs[0] if ivs[0][0] <= ivs[0][1] else (cw / 2, 1 - cw / 2)
        for k in range(1, len(times)):
            lo, hi = ivs[k] if ivs[k][0] <= ivs[k][1] else (cw / 2, 1 - cw / 2)
            nA, nB = max(A, lo), min(B, hi)
            hold = min(max(statistics.median(tg[j] for j in cur), A), B)
            drifted = abs(tg[k] - hold) > DEADZONE and k + 1 < len(times) and abs(tg[k + 1] - hold) > DEADZONE
            if nA > nB or drifted:
                segs.append((cur, A, B))
                cur, A, B = [k], lo, hi
            else:
                cur.append(k)
                A, B = nA, nB
        segs.append((cur, A, B))
        holds = [(idx, min(max(statistics.median(tg[j] for j in idx), A), B)) for idx, A, B in segs]
        keys = []
        for j, (idx, v) in enumerate(holds):
            keys.append([times[idx[0]], v])
            keys.append([times[idx[-1]], v])
        # stretch every move to MIN_MOVE..MAX_MOVE where the samples it crosses allow it
        for j in range(len(holds) - 1):
            ia, ib = 2 * j + 1, 2 * j + 2
            best = None
            for back in [x * SAMPLE_DT for x in range(0, 7)]:
                for fwd in [x * SAMPLE_DT for x in range(0, 7)]:
                    s0 = max(keys[ia - 1][0], keys[ia][0] - back)
                    s1 = min(keys[ib + 1][0], keys[ib][0] + fwd)
                    if s1 - s0 > MAX_MOVE or s1 <= s0:
                        continue
                    trial = [k[:] for k in keys]
                    trial[ia][0], trial[ib][0] = s0, s1
                    if _ok(trial, times, ivs) and (best is None or (s1 - s0) > best[1] - best[0]):
                        best = (s0, s1)
            if best:
                keys[ia][0], keys[ib][0] = best
        verdict = "pan"
    keys = _dedupe(keys)
    if not _ok(keys, times, ivs):
        return {"verdict": "flagged", "cw": cw, "kind": main_kind, "subjects": kinds, "keys": keys,
                "reason": "the subject moves faster than a smooth camera can follow without cutting a face: "
                          "needs a vertical re-render"}
    # a graphic or text card: real lines of text that the window would slice (a parts table, a 16:9 title card)
    cut_text = 0
    for t, d in zip(times, dets):
        lines = [x for x in d.get("text", []) if len(x) >= 6 and x[5] >= 3]
        if len(lines) >= 2 and sum(x[5] for x in lines) >= 20:
            c = mt.camera_path(keys, t)
            if any(x[0] < c - cw / 2 - 0.005 or x[0] + x[2] > c + cw / 2 + 0.005 for x in lines):
                cut_text += 1
    if cut_text >= max(1, round(0.25 * len(times))):
        return {"verdict": "flagged", "cw": cw, "kind": "text", "subjects": kinds, "keys": keys,
                "reason": f"on-screen text would be cut by the 9:16 window on {cut_text}/{len(times)} samples "
                          f"(a graphic or text card): lay it out again for 9:16"}
    # soft coverage (saliency shots): how much of the salient subject the window shows
    cov, widths = [], []
    for t, s in zip(times, subs):
        if s["soft"]:
            widths.append(s["soft"][1] - s["soft"][0])
            x0, x1 = s["soft"]
            c = mt.camera_path(keys, t)
            inside = max(0.0, min(x1, c + cw / 2) - max(x0, c - cw / 2))
            cov.append(inside / max(1e-6, x1 - x0))
    coverage = round(sum(cov) / len(cov), 3) if cov else None
    moves = [(b[0] - a[0], abs(b[1] - a[1])) for a, b in zip(keys, keys[1:]) if abs(b[1] - a[1]) > 1e-6]
    out = {"verdict": verdict, "keys": [[round(t, 4), round(v, 5)] for t, v in keys], "cw": round(cw, 5),
           "kind": main_kind, "subjects": kinds, "coverage": coverage,
           "max_pan_speed": round(max((dv / dt for dt, dv in moves), default=0.0), 3),
           "min_move_secs": round(min((dt for dt, _ in moves), default=0.0), 3)}
    scenery = bool(widths) and statistics.median(widths) >= SCENERY_W
    if main_kind == "saliency" and coverage is not None and coverage < MIN_COVER and not scenery:
        out.update(verdict="flagged", reason=f"the main object is wider than the 9:16 window (only {coverage:.0%} of "
                   f"it fits): needs a vertical re-render")
    elif main_kind == "saliency" and scenery:
        out["reason"] = "scenery (the salient area fills the frame): cropped to its center of interest"
    elif "reason" in out:
        pass
    elif verdict == "pan":
        out["reason"] = f"follows the {main_kind} with {len(moves)} eased move(s)"
    else:
        out["reason"] = f"locked off on the {main_kind}"
    return out


def _dedupe(keys: list) -> list:
    keys = sorted(keys, key=lambda k: k[0])
    out = [keys[0]]
    for k in keys[1:]:
        if k[0] - out[-1][0] < 1e-4:
            out[-1] = k
        else:
            out.append(k)
    if len(out) > 2:   # drop interior keys inside a hold
        slim = [out[0]]
        for a, b, c in zip(out, out[1:], out[2:]):
            if not (abs(a[1] - b[1]) < 1e-9 and abs(b[1] - c[1]) < 1e-9):
                slim.append(b)
        slim.append(out[-1])
        out = slim
    return out


def window_at(rf: dict, t_src: float) -> float:
    """Window center (0..1 of the source width) at source time t."""
    return mt.camera_path(rf["keys"], t_src)


def reframe_vf(rf: dict, W: int, H: int, seg_start: float, fps: int = 30) -> str:
    """ffmpeg -vf for one segment that starts at source second seg_start (input-seeked, so the filter's t
    is seconds since seg_start): the moving crop, then scale to the composition."""
    sw, sh = int(rf["src_w"]), int(rf["src_h"])
    cwp = min(sw, int(round(float(rf["cw"]) * sw / 2)) * 2)
    keys_px = [[t - seg_start, min(max((c - float(rf["cw"]) / 2) * sw, 0.0), sw - cwp)] for t, c in rf["keys"]]
    x = mt.camera_path_ffmpeg(keys_px, "t")
    return (f"crop={cwp}:{sh}:x='{x}':y=0:exact=1,scale={W}:{H}:flags=lanczos,fps={fps},setsar=1,format=yuv420p,"
            f"tpad=stop_mode=clone:stop_duration=0.1")


def plan_file(f: Path, src_in: float, src_out: float, kind: str, cw_for, tag: str, td: Path,
              pins: list | None = None) -> tuple:
    """Sample + probe + plan one shot. cw_for(src_w, src_h) -> normalized window width. Returns (plan, dets, pngs, times)."""
    if kind == "image":
        from PIL import Image
        sw, sh = Image.open(f).size
    else:
        sw, sh = video_size(f)
    times = sample_times(src_in, src_out) if kind != "image" else [src_in, (src_in + src_out) / 2, src_out]
    pngs = grab_frames(f, times, kind, td, tag)
    ok = [(t, p) for t, p in zip(times, pngs) if p]
    if not ok:
        return ({"verdict": "flagged", "reason": "could not read frames", "keys": [[src_in, 0.5]] * 2,
                 "cw": cw_for(sw, sh), "src_w": sw, "src_h": sh}, [], [], [])
    dets = probe([p for _, p in ok])
    plan = plan_shot([t for t, _ in ok], dets, cw_for(sw, sh), pins)
    plan.update(src_w=sw, src_h=sh)
    return plan, dets, [p for _, p in ok], [t for t, _ in ok]


if __name__ == "__main__":
    import sys
    f = Path(sys.argv[1])
    a, b = float(sys.argv[2]), float(sys.argv[3])
    with tempfile.TemporaryDirectory() as td:
        plan, dets, _, _ = plan_file(f, a, b, "video", lambda w, h: (h * 9 / 16) / w, "x", Path(td))
    print(json.dumps(plan, indent=1))
