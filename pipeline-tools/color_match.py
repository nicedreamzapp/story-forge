#!/usr/bin/env python3
"""color_match — pull every shot of a film toward one reference look before the final grade.

AI shots drift: each take comes back a little warmer, greener or flatter than the one next
to it, and a LUT applied on top keeps the drift. This matches every shot to a reference
frame first (color-matcher, github.com/hahnec/color-matcher, MKL or HM-MVGD-HM), then the
grade lays the film look over shots that already agree.

How it stays calm on screen:
  * One transform per shot, fitted on frames pooled from across the whole shot and baked
    into a 33-point 3D LUT. Nothing is fitted per frame, so nothing can flicker inside a
    shot. Shots longer than --window seconds get one keyframe LUT per window, smoothed and
    cross-faded frame by frame so a lighting change inside the shot is followed gently.
  * --strength (default 0.6) blends the LUT with identity: it nudges, it does not flatten.
  * Cards (black, title, credit) and near-black shots are passed through untouched.

Reference, first match wins:
  --ref IMAGE | VIDEO@SECONDS     one hero frame for the whole film
  --ref-cut CUT_ID                the middle frame of that cut
  --refs refs.json                {"reference": ..., "sections": {"hook": ..., ...}}
  project files                   canon/color_refs.json, or a "color_match" block in
                                  final/timeline.json, same shape as --refs (paths are
                                  relative to the project). Sections are the EDL "section".
  auto                            the medoid shot (closest in mean Lab to all others);
                                  --per-section picks one medoid per section instead.

Modes:
  --film FILM.mp4 --edl edl.json --out OUT.mp4   cut the film at EDL start/len, match per cut
  --segs DIR --out DIR                           every mp4 in DIR (EDL segments) to DIR
  --clips a.mp4 b.mp4 --out DIR                  loose clips
  --measure                                      only report the before numbers

Every run prints and (with --report) writes per-shot mean Lab delta E (CIE76, mean colour of
the shot vs mean colour of its reference) before and after.

    ~/.local/finish-env/bin/python pipeline-tools/color_match.py --film final/cut.mp4 \
        --edl final/edl_final.json --project projects/last_signal --out final/cut_matched.mp4
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

try:
    from color_matcher import ColorMatcher
except ImportError:  # the tool lives in its own venv
    sys.exit("color-matcher missing: run with ~/.local/finish-env/bin/python")

N_LUT = 33
SAMPLE_W = 256
CARD_RE = re.compile(r"(title|black|card|credit|slate)", re.I)


# ---------------------------------------------------------------- frames + colour maths
def probe_fps(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=r_frame_rate", "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    n, _, d = r.stdout.strip().partition("/")
    return float(n) / float(d or 1)


def trim_frames(a: float, b: float, fps: float) -> str:
    """Frame-exact trim: seconds-based trims double or drop a frame on 1/24-s boundaries."""
    return f"trim=start_frame={round(a * fps)}:end_frame={round(b * fps)}"


def probe_duration(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def grab(path: Path, t: float | None = None, w: int = SAMPLE_W) -> np.ndarray:
    """One frame (video at t seconds, or an image) as float RGB 0..1, w pixels wide."""
    cmd = ["ffmpeg", "-v", "error"]
    if t is not None:
        cmd += ["-ss", f"{max(0.0, t):.3f}"]
    cmd += ["-i", str(path), "-frames:v", "1", "-vf", f"scale={w}:-2:flags=area",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    if not raw:
        raise RuntimeError(f"no frame from {path} at {t}")
    h = len(raw) // (w * 3)
    return np.frombuffer(raw[: h * w * 3], np.uint8).reshape(h, w, 3).astype(np.float64) / 255.0


def sample_frames(path: Path, t0: float, t1: float, n: int) -> list[np.ndarray]:
    span = max(t1 - t0, 1e-3)
    ts = [t0 + span * (i + 0.5) / n for i in range(n)]
    return [grab(path, t) for t in ts]


def srgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    c = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    m = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    xyz = c.reshape(-1, 3) @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    lab = np.stack([116 * f[:, 1] - 16, 500 * (f[:, 0] - f[:, 1]), 200 * (f[:, 1] - f[:, 2])], 1)
    return lab


def mean_lab(frames: list[np.ndarray]) -> np.ndarray:
    return np.concatenate([srgb_to_lab(f) for f in frames]).mean(0)


def de76(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


# ---------------------------------------------------------------- fit a shot -> LUT
def identity_grid(n: int = N_LUT) -> np.ndarray:
    g = np.linspace(0, 1, n)
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")          # .cube order: red fastest
    return np.stack([r, gg, b], -1).reshape(-1, 3)


def fit_lut(src_frames: list[np.ndarray], ref: np.ndarray, method: str, strength: float) -> np.ndarray:
    """Run color-matcher on a mosaic of the shot, record each stage as a pointwise map
    (histogram stages are monotone per-channel curves, MKL/MVGD stages are affine), and
    replay those maps on the identity grid. Returns the blended LUT (N^3 x 3)."""
    mosaic = np.concatenate(src_frames, 0)
    if method in ("mvgd", "hm-mvgd-hm"):   # the analytical MVGD solver wants equal shapes
        yi = np.linspace(0, ref.shape[0] - 1, mosaic.shape[0]).round().astype(int)
        xi = np.linspace(0, ref.shape[1] - 1, mosaic.shape[1]).round().astype(int)
        ref = ref[yi][:, xi]
    cm = ColorMatcher(src=mosaic, ref=ref, method=method)
    funs = {"mkl": ["mvgd"], "mvgd": ["mvgd"], "hm-mvgd-hm": ["hm", "mvgd", "hm"],
            "hm-mkl-hm": ["hm", "mvgd", "hm"]}[method]
    cur = mosaic
    stages = []
    for kind in funs:
        if kind == "hm":
            out = cm.hist_match(cur, ref)
            curves = []
            for ch in range(3):
                x = cur[..., ch].ravel(); y = out[..., ch].ravel()
                o = np.argsort(x, kind="stable")
                xs, idx = np.unique(x[o], return_index=True)
                curves.append((xs, y[o][idx]))
            stages.append(("hm", curves))
        else:
            out = cm.multivar_transfer(cur, ref)
            stages.append(("lin", (cm.transfer_mat.copy(), cm.mu_r.copy(), cm.mu_z.copy())))
        cur = out
    grid = identity_grid()
    x = grid.copy()
    for kind, p in stages:
        if kind == "hm":
            x = np.stack([np.interp(x[:, ch], *p[ch]) for ch in range(3)], 1)
        else:
            mat, mu_r, mu_z = p
            x = (mat @ (x.T - mu_r) + mu_z).T
    x = np.real(x)
    return np.clip(grid + strength * (x - grid), 0.0, 1.0)


def write_cube(path: Path, lut: np.ndarray) -> None:
    with open(path, "w") as f:
        f.write(f'TITLE "color_match"\nLUT_3D_SIZE {N_LUT}\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n')
        f.write("\n".join(f"{v[0]:.6f} {v[1]:.6f} {v[2]:.6f}" for v in lut) + "\n")


def apply_lut_np(frame: np.ndarray, lut: np.ndarray) -> np.ndarray:
    """Trilinear LUT lookup in numpy (used only to predict the after-numbers cheaply)."""
    cube = lut.reshape(N_LUT, N_LUT, N_LUT, 3)               # [b, g, r]
    p = np.clip(frame.reshape(-1, 3), 0, 1) * (N_LUT - 1)
    i0 = np.floor(p).astype(int).clip(0, N_LUT - 2); d = p - i0
    out = np.zeros_like(p)
    for dr in (0, 1):
        for dg in (0, 1):
            for db in (0, 1):
                w = (d[:, 0] if dr else 1 - d[:, 0]) * (d[:, 1] if dg else 1 - d[:, 1]) * \
                    (d[:, 2] if db else 1 - d[:, 2])
                out += w[:, None] * cube[i0[:, 2] + db, i0[:, 1] + dg, i0[:, 0] + dr]
    return out.reshape(frame.shape)


# ---------------------------------------------------------------- shots + references
class Shot:
    def __init__(self, sid, path, t0, t1, section=None, skip=False):
        self.id, self.path, self.t0, self.t1, self.section, self.skip = sid, Path(path), t0, t1, section, skip
        self.frames: list[np.ndarray] = []
        self.lab = None
        self.luts: list[tuple[float, np.ndarray]] = []       # (time within shot, lut)

    @property
    def dur(self):
        return self.t1 - self.t0


def load_ref(spec: str, base: Path | None, shots: list[Shot]) -> np.ndarray:
    m = re.match(r"^(.*)@([\d.]+)$", spec)
    path, t = (m.group(1), float(m.group(2))) if m else (spec, None)
    p = Path(path).expanduser()
    if not p.is_absolute() and base is not None and (base / p).exists():
        p = base / p
    if not p.exists():
        cut = next((s for s in shots if s.id == spec), None)
        if cut:
            return grab(cut.path, (cut.t0 + cut.t1) / 2)
        sys.exit(f"reference not found: {spec}")
    if t is None and p.suffix.lower() in (".mp4", ".mov", ".mkv", ".webm"):
        t = probe_duration(p) / 2
    return grab(p, t)


def medoid(shots: list[Shot]) -> Shot:
    shots = [s for s in shots if s.dur >= 1.0] or shots   # a strobe flash is no hero frame
    labs = np.stack([s.lab for s in shots])
    d = np.linalg.norm(labs[:, None] - labs[None], axis=-1).sum(1)
    return shots[int(np.argmin(d))]


def project_refs(project: Path | None) -> dict:
    if project is None:
        return {}
    f = project / "canon" / "color_refs.json"
    if f.is_file():
        return json.loads(f.read_text())
    tl = project / "final" / "timeline.json"
    if tl.is_file():
        return json.loads(tl.read_text()).get("color_match", {}) or {}
    return {}


# ---------------------------------------------------------------- rendering
def lut_chain(shot: Shot, tmp: Path, label: str) -> list[tuple[float, float, Path | None, Path | None]]:
    """(t0, t1, cubeA, cubeB) pieces in shot-local time. cubeB set = cross-fade A->B across the
    piece, frame by frame (blending two LUT outputs linearly is exactly a linearly blended LUT).
    Stepping LUTs in chunks was tried first and measured as a sawtooth in luma: never step."""
    if shot.skip or not shot.luts:
        return [(0.0, shot.dur, None, None)]
    cubes = []
    for i, (_, lut) in enumerate(shot.luts):
        p = tmp / f"{label}_{i:02d}.cube"; write_cube(p, lut); cubes.append(p)
    if len(cubes) == 1:
        return [(0.0, shot.dur, cubes[0], None)]
    keys = [t for t, _ in shot.luts]
    pieces = [(0.0, keys[0], cubes[0], None)]
    pieces += [(keys[i], keys[i + 1], cubes[i], cubes[i + 1]) for i in range(len(keys) - 1)]
    pieces.append((keys[-1], shot.dur, cubes[-1], None))
    return [p for p in pieces if p[1] - p[0] > 1e-6]


def piece_filter(src: str, a: float, b: float, ca, cb, fps: float, tag: str) -> str:
    head = f"{src}{trim_frames(a, b, fps)},setpts=PTS-STARTPTS"
    if ca is None:
        return f"{head},null[{tag}]"
    if cb is None:
        return f"{head},lut3d=file='{ca}':interp=tetrahedral[{tag}]"
    span = max(b - a, 1e-3)
    return (f"{head},split[{tag}a][{tag}b];[{tag}a]lut3d=file='{ca}':interp=tetrahedral[{tag}A];"
            f"[{tag}b]lut3d=file='{cb}':interp=tetrahedral[{tag}B];"
            f"[{tag}A][{tag}B]blend=all_expr='A+(B-A)*clip(T/{span:.4f},0,1)'[{tag}]")


def run_graph(inp: Path, graph: str, out: Path, tmp: Path, crf: int, what: str) -> None:
    script = tmp / "graph.txt"; script.write_text(graph)
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(inp), "-filter_complex_script", str(script),
           "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-crf", str(crf), "-preset", "medium",
           "-pix_fmt", "yuv420p", "-c:a", "copy", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"ffmpeg failed on {what}: {r.stderr[-800:]}")


def build_graph(items: list[tuple[float, Shot, str]], fps: float, tmp: Path) -> str:
    """items: (offset of the shot in the input, shot, label). Trims every piece, concats."""
    parts, labels, n = [], [], 0
    for off, s, label in items:
        for a, b, ca, cb in lut_chain(s, tmp, label):
            parts.append(piece_filter("[0:v]", off + a, off + b, ca, cb, fps, f"p{n}"))
            labels.append(f"[p{n}]"); n += 1
    if n == 1:
        return parts[0].rsplit("[", 1)[0] + "[v]"
    return ";".join(parts) + f";{''.join(labels)}concat=n={n}:v=1:a=0[v]"


def render_clip(shot: Shot, out: Path, tmp: Path, crf: int) -> None:
    run_graph(shot.path, build_graph([(0.0, shot, shot.id)], probe_fps(shot.path), tmp), out, tmp, crf, shot.id)


def render_film(film: Path, shots: list[Shot], out: Path, tmp: Path, crf: int) -> None:
    """One ffmpeg pass: trim the film at every cut, LUT each piece, concat."""
    items = [(s.t0, s, f"s{i:03d}") for i, s in enumerate(shots)]
    run_graph(film, build_graph(items, probe_fps(film), tmp), out, tmp, crf, "the film")


# ---------------------------------------------------------------- main
def build_shots(a) -> tuple[list[Shot], Path | None]:
    shots: list[Shot] = []
    if a.film:
        film = Path(a.film).resolve()
        edl = json.loads(Path(a.edl).read_text())
        total = probe_duration(film)
        for c in edl["cuts"]:
            t0 = float(c["start"]); t1 = min(total, t0 + float(c["len"]))
            if t1 - t0 <= 0:
                continue
            skip = (not c.get("src")) or bool(CARD_RE.search(c["id"])) or c.get("color_match") is False
            shots.append(Shot(c["id"], film, t0, t1, c.get("section"), skip))
        return shots, film
    paths = sorted(Path(a.segs).glob("*.mp4")) if a.segs else [Path(p) for p in a.clips]
    for p in paths:
        sid = re.sub(r"^\d+_", "", p.stem)
        shots.append(Shot(sid, p, 0.0, probe_duration(p), None, bool(CARD_RE.search(sid))))
    if a.edl:  # borrow sections from the EDL by cut id
        sec = {c["id"]: c.get("section") for c in json.loads(Path(a.edl).read_text())["cuts"]}
        for s in shots:
            s.section = sec.get(s.id)
    return shots, None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--film"); src.add_argument("--segs"); src.add_argument("--clips", nargs="+")
    ap.add_argument("--edl")
    ap.add_argument("--out")
    ap.add_argument("--project", help="projects/<film>: reads canon/color_refs.json or timeline color_match")
    ap.add_argument("--ref"); ap.add_argument("--ref-cut"); ap.add_argument("--refs")
    ap.add_argument("--per-section", action="store_true", help="auto mode: one medoid reference per section")
    ap.add_argument("--method", default="mkl", choices=["mkl", "hm-mvgd-hm", "hm-mkl-hm", "mvgd"])
    ap.add_argument("--strength", type=float, default=0.6)
    ap.add_argument("--window", type=float, default=6.0, help="keyframe a shot longer than this (s)")
    ap.add_argument("--samples", type=int, default=6, help="frames pooled per shot / window")
    ap.add_argument("--crf", type=int, default=12)
    ap.add_argument("--measure", action="store_true", help="report the before numbers only")
    ap.add_argument("--verify", action="store_true", help="re-measure the written output (slower, exact)")
    ap.add_argument("--report")
    a = ap.parse_args()
    if a.film and not a.edl:
        sys.exit("--film needs --edl (cut times)")
    if not a.measure and not a.out:
        sys.exit("--out is required unless --measure")

    shots, film = build_shots(a)
    project = Path(a.project).resolve() if a.project else None
    for s in shots:
        n = max(2, min(a.samples, int(s.dur * 4)))
        s.frames = sample_frames(s.path, s.t0, s.t1, n)
        s.lab = mean_lab(s.frames)
        if s.lab[0] < 6:
            s.skip = True                                   # near-black: nothing to match
    live = [s for s in shots if not s.skip]
    if not live:
        sys.exit("no matchable shots")

    # pick references
    cfg = json.loads(Path(a.refs).read_text()) if a.refs else project_refs(project)
    base = Path(a.refs).resolve().parent if a.refs else project
    ref_for: dict[str, tuple[str, np.ndarray]] = {}
    if a.ref or a.ref_cut:
        spec = a.ref or a.ref_cut
        img = load_ref(spec, base, shots)
        for s in live: ref_for[s.id] = (spec, img)
    else:
        global_spec = cfg.get("reference")
        global_img = load_ref(global_spec, base, shots) if global_spec else None
        sec_imgs = {k: (v, load_ref(v, base, shots)) for k, v in (cfg.get("sections") or {}).items()}
        if global_img is None and not sec_imgs:
            groups = {}
            for s in live: groups.setdefault(s.section if a.per_section else "_all", []).append(s)
            for g, members in groups.items():
                m = medoid(members)
                img = grab(m.path, (m.t0 + m.t1) / 2)
                sec_imgs[g] = (f"auto medoid {m.id}", img)
            for s in live:
                ref_for[s.id] = sec_imgs[s.section if a.per_section else "_all"]
        else:
            for s in live:
                if s.section in sec_imgs: ref_for[s.id] = sec_imgs[s.section]
                elif global_img is not None: ref_for[s.id] = (global_spec, global_img)
            live = [s for s in live if s.id in ref_for]

    ref_lab = {k: mean_lab([v[1]]) for k, v in {r[0]: r for r in ref_for.values()}.items()}

    # fit
    rows = []
    for s in shots:
        row = {"id": s.id, "section": s.section, "skip": s.skip or s.id not in ref_for}
        if not row["skip"]:
            spec, img = ref_for[s.id]
            before = de76(s.lab, ref_lab[spec])
            row.update(ref=spec, before=round(before, 2))
            if not a.measure:
                if s.dur > a.window:
                    k = int(np.ceil(s.dur / a.window))
                    for i in range(k):
                        w0 = s.t0 + s.dur * i / k; w1 = s.t0 + s.dur * (i + 1) / k
                        fr = sample_frames(s.path, w0, w1, max(2, a.samples // 2))
                        s.luts.append(((w0 + w1) / 2 - s.t0, fit_lut(fr, img, a.method, a.strength)))
                    if len(s.luts) >= 3:                     # 1-2-1 smoothing of the keyframes
                        L = np.stack([l for _, l in s.luts]); sm = L.copy()
                        sm[1:-1] = 0.25 * L[:-2] + 0.5 * L[1:-1] + 0.25 * L[2:]
                        s.luts = [(t, sm[i]) for i, (t, _) in enumerate(s.luts)]
                else:
                    s.luts = [(s.dur / 2, fit_lut(s.frames, img, a.method, a.strength))]
                pred = [apply_lut_np(f, s.luts[min(len(s.luts) - 1, int(i * len(s.luts) / len(s.frames)))][1])
                        for i, f in enumerate(s.frames)]
                row["after"] = round(de76(mean_lab(pred), ref_lab[spec]), 2)
        rows.append(row)

    # render
    if not a.measure:
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            if film:
                out = Path(a.out).resolve()
                if out == film:
                    sys.exit("refusing to overwrite the input")
                render_film(film, shots, out, tmp, a.crf)
            else:
                outdir = Path(a.out).resolve(); outdir.mkdir(parents=True, exist_ok=True)
                for s in shots:
                    o = outdir / s.path.name
                    if o.resolve() == s.path.resolve():
                        sys.exit("refusing to overwrite an input clip")
                    render_clip(s, o, tmp, a.crf)
        if a.verify:
            for s, row in zip(shots, rows):
                if row.get("after") is None:
                    continue
                p = Path(a.out).resolve() if film else Path(a.out).resolve() / s.path.name
                fr = sample_frames(p, s.t0, s.t1, len(s.frames))
                row["after_measured"] = round(de76(mean_lab(fr), ref_lab[row["ref"]]), 2)

    # report
    live_rows = [r for r in rows if not r["skip"]]
    def stat(key):
        v = [r[key] for r in live_rows if key in r]
        return (round(float(np.mean(v)), 2), round(float(np.median(v)), 2), round(float(np.max(v)), 2)) if v else None
    print(f"[color_match] method {a.method} · strength {a.strength} · {len(live_rows)} shots matched, "
          f"{len(rows) - len(live_rows)} passed through")
    for r in rows:
        if r["skip"]:
            print(f"  {r['id']:<22} pass-through")
        else:
            aft = r.get("after_measured", r.get("after", "-"))
            print(f"  {r['id']:<22} dE {r['before']:>6} -> {aft}")
    for k in ("before", "after", "after_measured"):
        st = stat(k)
        if st:
            print(f"  {k:<15} mean {st[0]}  median {st[1]}  max {st[2]}")
    refs_used = sorted({r["ref"] for r in live_rows})
    print("  reference(s): " + "; ".join(refs_used))
    if a.report:
        Path(a.report).write_text(json.dumps({"method": a.method, "strength": a.strength, "refs": refs_used,
                                              "summary": {k: stat(k) for k in ("before", "after", "after_measured")},
                                              "shots": rows}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
