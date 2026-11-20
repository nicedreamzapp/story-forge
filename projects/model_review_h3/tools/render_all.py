#!/usr/bin/env python3
"""Render every LnnA/LnnB Manim scene into acquired/ with provenance (source "manim"), plus a still
(the last frame of A) into refs/ for the promo.json "kb" jobs. Usage: render_all.py [SCENE ...] [-j N]"""
import hashlib, json, subprocess, sys, time, re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
FILM = Path(__file__).resolve().parent.parent
MANIM = str(Path.home() / "manim-env/bin/manim")
SRC = FILM / "tools/scenes.py"
MEDIA = Path("/tmp/mr_manim")
sys.path.insert(0, str(FILM.parent.parent / "pipeline-tools"))
from promo_footage import record, sha256  # noqa: E402

SETUPS = {}
for m in re.finditer(r"^class (L\d\d[AB])\(Beat\):", SRC.read_text(), re.M):
    SETUPS[m.group(1)] = None

def one(scene):
    L = int(scene[1:3]); ab = scene[3]
    t = time.time()
    r = subprocess.run([MANIM, "-r", "1920,1080", "--fps", "30", "--disable_caching", "-v", "WARNING",
                        "--media_dir", str(MEDIA), "-o", scene, str(SRC), scene], capture_output=True, text=True, cwd=FILM)
    out = next(MEDIA.glob(f"videos/scenes/*/{scene}.mp4"), None)
    if r.returncode or out is None:
        return scene, False, (r.stderr or r.stdout)[-1500:]
    dst = FILM / "acquired" / f"l{L:02d}_manim_{ab.lower()}_1.mp4"
    dst.parent.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(out), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "16", "-r", "30", str(dst)], check=True)
    rel = str(dst.relative_to(FILM))
    record(FILM, {"file": rel, "id": f"l{L:02d}_manim_{ab.lower()}", "n": 1, "line": L,
                  "setup": f"code-rendered motion, setup {ab} (tools/scenes.py {scene}, timed to vo/words.json)",
                  "backend": "manim", "source": "manim", "tool": "Manim Community v0.22.0 (Cairo), 1920x1080@30",
                  "prompt": None, "refs": [], "sha256": sha256(dst), "bytes": dst.stat().st_size,
                  "created": time.strftime("%Y-%m-%dT%H:%M:%S"), "gen_secs": round(time.time() - t, 1),
                  "src": f"tools/scenes.py::{scene}", "src_sha256": sha256(SRC)})
    if ab == "A":
        (FILM / "refs").mkdir(exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-sseof", "-0.1", "-i", str(dst), "-frames:v", "1",
                        "-update", "1", str(FILM / "refs" / f"l{L:02d}_still.png")], check=True)
    return scene, True, f"{time.time() - t:.0f}s"

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-j")]
    j = int(next((a[2:] for a in sys.argv[1:] if a.startswith("-j")), "6"))
    todo = args or list(SETUPS)
    bad = 0
    with ThreadPoolExecutor(j) as ex:
        for scene, ok, msg in ex.map(one, todo):
            print(("OK  " if ok else "FAIL"), scene, msg if ok else "\n" + msg, flush=True)
            bad += not ok
    sys.exit(1 if bad else 0)
