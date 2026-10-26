#!/usr/bin/env python3
"""promo_footage.py — promo stage 04: make the footage we render OURSELVES, with its papers.

Sources, in order of trust (frozen rule 28, Matt 2026-10-22):
  1. blender-render (PRIMARY for any physical product): promo.json "blender" shots, each a GLB of
     the exact CAD + PBR material presets + a studio or HDRI world + a motivated camera move,
     rendered by pipeline-tools/blender_render.py (Cycles on Metal) to
     acquired/blender/<id>/beauty_####.png + ids_####.png (flat object-ID pass for callout checks),
     encoded to acquired/blender/<id>/beauty.mp4.
  2. local i2v (optional): promo.json "i2v" jobs {"id", "line", "setup", "still", "prompt",
     "seconds": 5, "res": "832x480", "static": false} through bin/make-ltx25 (LTX-2.5 on the M5;
     the prompt names an action or a motivated camera move, frozen rule 31). Out:
     acquired/<id>_1.mp4.
  2b. kb still moves (software/screenshots): promo.json "kb" jobs, ffmpeg pan/zoom over a real still,
     pixel-exact (see kb_job). Out: acquired/<id>_1.mp4, backend still-kb.
  3. Browser takes are NOT made here. bin/browser-acquire is a separate, optional, manual step
     (Matt's Brave on the mini; refs[] required; ChatGPT never for photoreal product shots).
Every take gets a record in acquired/provenance.json and a <file>.json sidecar (SCHEMAS.md), so
ingest_acquired.py lists it like any acquired take. A shot whose spec (and GLB bytes) did not
change since its last render is skipped. Song Forge customer jobs outrank renders: nothing heavy
starts while jobs_running > 0, and every heavy step passes bin/mem-gate (frozen rules 11, 16).

Usage:  python3 pipeline-tools/promo_footage.py projects/<film> [--only ID] [--preview] [--force]
Exit 0 = every listed shot is on disk; 1 = a render failed; 2 = could not start (Song Forge busy, ...).
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from promo_common import SF, load_promo, run, song_forge_busy  # noqa: E402

BLENDER = shutil.which("blender") or "/Applications/Blender.app/Contents/MacOS/Blender"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def record(film: Path, entry: dict) -> None:
    acq = film / "acquired"
    acq.mkdir(parents=True, exist_ok=True)
    prov = acq / "provenance.json"
    with (acq / ".provenance.lock").open("w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        data = json.loads(prov.read_text()) if prov.exists() else {"takes": []}
        data["takes"] = [t for t in data["takes"] if t.get("file") != entry["file"]] + [entry]
        tmp = prov.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=1))
        tmp.replace(prov)
    (film / (entry["file"] + ".json")).write_text(json.dumps(entry, indent=1))


def blender_shot(film: Path, shot: dict, cfg: dict, preview: bool, force: bool) -> bool:
    sid = shot["id"]
    out = film / "acquired" / "blender" / sid
    spec = {**shot, "materials": {**cfg.get("materials", {}), **shot.get("materials", {})}}
    spec["glb"] = [str((film / g).resolve()) for g in shot["glb"]]
    if shot.get("hdri"):
        spec["hdri"] = str((film / shot["hdri"]).resolve())
    spec["out"] = str(out.resolve())
    glb_sha = {Path(g).name: sha256(Path(g)) for g in spec["glb"]}
    tool = sha256(SF / "pipeline-tools" / "blender_render.py")   # a renderer change re-renders too
    key = hashlib.sha1(json.dumps({"spec": spec, "glb": glb_sha, "preview": preview, "tool": tool},
                                  sort_keys=True).encode()).hexdigest()[:16]
    mp4 = out / "beauty.mp4"
    stamp = out / "spec_key.txt"
    if not force and mp4.exists() and stamp.exists() and stamp.read_text().strip() == key:
        print(f"  {sid}: up to date (acquired/blender/{sid}/beauty.mp4)")
        return True
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    sp = out / "spec.json"
    sp.write_text(json.dumps(spec, indent=1))
    t0 = time.time()
    print(f"  {sid}: rendering {spec.get('frames', 120)} frames, {spec.get('engine', 'CYCLES')} "
          f"{spec.get('samples', 48)} spp, {'x'.join(map(str, spec.get('res', [1920, 1080])))}"
          f"{' PREVIEW' if preview else ''} (started {time.strftime('%H:%M')})", flush=True)
    cmd = [BLENDER, "-b", "--factory-startup", "-noaudio", "--python", str(SF / "pipeline-tools" / "blender_render.py"),
           "--", str(sp)] + (["--preview"] if preview else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    (out / "blender.log").write_text(r.stdout[-20000:] + "\n" + r.stderr[-20000:])
    frames = sorted(out.glob("beauty_*.png"))
    if r.returncode != 0 or not frames:
        print(f"  {sid}: FAILED (see acquired/blender/{sid}/blender.log)")
        return False
    fps = int(spec.get("fps", 30))
    run(["ffmpeg", "-v", "error", "-y", "-framerate", fps, "-pattern_type", "glob", "-i", str(out / "beauty_*.png"),
         "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", mp4])
    meta = json.loads((out / "render_meta.json").read_text())
    rel = str(mp4.relative_to(film))
    record(film, {"file": rel, "id": sid, "n": 1, "line": shot.get("line"), "setup": shot.get("setup"),
                  "backend": "blender-render", "tool": f"Blender {meta['blender']} {meta['engine']} Metal",
                  "glb": [str(Path(g).relative_to(film.resolve())) if Path(g).is_relative_to(film.resolve()) else Path(g).name
                          for g in spec["glb"]],
                  "glb_sha256": glb_sha, "camera": meta["camera"], "materials": meta["materials"],
                  "samples": meta["samples"], "world": meta["world"], "hdri": meta["hdri"],
                  "ids": "acquired/blender/%s/ids_####.png" % sid if (out / "ids.json").exists() else None,
                  "sha256": sha256(mp4), "bytes": mp4.stat().st_size,
                  "created": time.strftime("%Y-%m-%dT%H:%M:%S"), "gen_secs": round(time.time() - t0)})
    stamp.write_text(key)
    for f in frames:   # the mp4 is the take; the ID pass PNGs stay for callout checks
        f.unlink()
    print(f"  {sid}: OK {rel} ({len(frames)} frames in {time.time() - t0:.0f}s)")
    return True


def i2v_job(film: Path, job: dict, force: bool) -> bool:
    jid = job["id"]
    dst = film / "acquired" / f"{jid}_1.mp4"
    if dst.exists() and not force:
        print(f"  {jid}: up to date ({dst.relative_to(film)})")
        return True
    still = film / job["still"]
    cmd = [str(SF / "bin" / "make-ltx25"), "--i2v", str(still), "--res", job.get("res", "832x480"),
           "--duration", str(job.get("seconds", 5)), "--label", jid]
    if job.get("static"):
        cmd.append("--static")
    cmd.append(job["prompt"])
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True)
    import re
    m = re.search(r"done in [\d.]+s → (\S+)", r.stdout)
    if r.returncode != 0 or not m:
        print(f"  {jid}: i2v FAILED: {(r.stderr or r.stdout).strip()[-300:]}")
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(m.group(1), dst)
    record(film, {"file": str(dst.relative_to(film)), "id": jid, "n": 1, "line": job.get("line"),
                  "setup": job.get("setup"), "backend": "ltx25", "tool": "LTX-2.5 i2v (bin/make-ltx25, M5)",
                  "prompt": job["prompt"], "refs": [{"path": job["still"], "sha256": sha256(still)}],
                  "sha256": sha256(dst), "bytes": dst.stat().st_size,
                  "created": time.strftime("%Y-%m-%dT%H:%M:%S"), "gen_secs": round(time.time() - t0)})
    print(f"  {jid}: OK {dst.relative_to(film)}")
    return True


KB_MOVES = {   # zoompan expressions over the shot's frames (n = frame index, N = frame count)
    "push-in":   ("1+0.18*on/{N}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    "pull-out":  ("1.18-0.18*on/{N}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    "pan-right": ("1.15", "(iw-iw/zoom)*on/{N}", "ih/2-(ih/zoom/2)"),
    "pan-left":  ("1.15", "(iw-iw/zoom)*(1-on/{N})", "ih/2-(ih/zoom/2)"),
    "pan-down":  ("1.15", "iw/2-(iw/zoom/2)", "(ih-ih/zoom)*on/{N}"),
}


def kb_job(film: Path, job: dict, force: bool) -> bool:
    """A pan/zoom over a real still (screenshots of software, photos): the "still-kb" source. 10/26: a
    software promo has no CAD to render and i2v warps UI text, so the stills move with ffmpeg instead,
    pixel-exact. promo.json "kb" jobs {"id", "line", "setup", "still", "move": push-in|pull-out|
    pan-left|pan-right|pan-down, "seconds": 5}. Out: acquired/<id>_1.mp4 at 1920x1080@30."""
    jid = job["id"]
    dst = film / "acquired" / f"{jid}_1.mp4"
    if dst.exists() and not force:
        print(f"  {jid}: up to date ({dst.relative_to(film)})")
        return True
    still = film / job["still"]
    if not still.exists():
        print(f"  {jid}: kb FAILED: missing still {job['still']} (copy it into the project first)")
        return False
    move = job.get("move", "push-in")
    if move not in KB_MOVES:
        print(f"  {jid}: kb FAILED: move '{move}' is not one of {', '.join(KB_MOVES)}")
        return False
    n = int(round(float(job.get("seconds", 5)) * 30))
    z, x, y = (e.replace("{N}", str(n)) for e in KB_MOVES[move])
    # fit the still into 16:9 on a dark ground first, upscaled 2x so the zoom stays sharp
    vf = ("scale=3840:2160:force_original_aspect_ratio=decrease,pad=3840:2160:(ow-iw)/2:(oh-ih)/2:color=0x0b0d12,"
          f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s=1920x1080:fps=30,format=yuv420p")
    dst.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(still), "-vf", vf,
                        "-frames:v", str(n), "-c:v", "libx264", "-crf", "14", str(dst)], capture_output=True, text=True)
    if r.returncode != 0 or not dst.exists():
        print(f"  {jid}: kb FAILED: {r.stderr.strip()[-300:]}")
        return False
    record(film, {"file": str(dst.relative_to(film)), "id": jid, "n": 1, "line": job.get("line"),
                  "setup": job.get("setup"), "backend": "still-kb", "tool": f"ffmpeg zoompan ({move})",
                  "refs": [{"path": job["still"], "sha256": sha256(still)}],
                  "sha256": sha256(dst), "bytes": dst.stat().st_size,
                  "created": time.strftime("%Y-%m-%dT%H:%M:%S"), "gen_secs": round(time.time() - t0)})
    print(f"  {jid}: OK {dst.relative_to(film)} ({move})")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("film")
    ap.add_argument("--only", action="append")
    ap.add_argument("--preview", action="store_true", help="half res, 12 spp: framing checks only, never the cut")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    film = Path(a.film).resolve()
    cfg = load_promo(film)
    shots = [s for s in cfg.get("blender", []) if not a.only or s["id"] in a.only]
    jobs = [j for j in cfg.get("i2v", []) if not a.only or j["id"] in a.only]
    kbs = [j for j in cfg.get("kb", []) if not a.only or j["id"] in a.only]
    if not shots and not jobs and not kbs:
        print("[footage] promo.json lists no blender shots, i2v or kb jobs; nothing to render")
        return 0
    busy, why = song_forge_busy()
    if busy:
        print(f"[footage] Song Forge busy ({why}); customer jobs outrank renders. Not starting.", file=sys.stderr)
        return 2
    if subprocess.run([str(SF / "bin" / "mem-gate"), f"promo_footage {film.name}"]).returncode != 0:
        print("[footage] memory gate refused; not rendering", file=sys.stderr)
        return 2
    print(f"[footage] {len(shots)} blender shot(s), {len(jobs)} i2v job(s), {len(kbs)} kb still move(s); Song Forge {why}")
    ok = all([blender_shot(film, s, cfg, a.preview, a.force) for s in shots] +
             [i2v_job(film, j, a.force) for j in jobs] + [kb_job(film, j, a.force) for j in kbs])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
