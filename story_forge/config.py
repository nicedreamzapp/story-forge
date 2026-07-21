"""story_forge.config — where every external dependency lives.

Story Forge shells out to a handful of things that are not Python imports:
a Flux text-to-image script, the render-route i2v dispatcher, piper for
narration, ffmpeg for assembly, and optionally the avatar pipeline for
lipsync. Those used to be hardcoded to one machine's home directory, which
meant a fresh clone could not run.

Every path below resolves in the same order:

  1. an ``SF_*`` environment variable, if set
  2. a sane default, relative to this repo where the file ships with it
  3. a conventional ``~/`` location for the big external tools

Nothing here touches the filesystem at import time, so importing the package
on a machine that has none of the render dependencies still works. Use
``doctor()`` to find out what is actually installed.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

HOME = Path.home()
REPO_ROOT = Path(__file__).resolve().parent.parent


def _env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name)
    return Path(raw).expanduser() if raw else default


def _env_str(name: str, default: str) -> str:
    return os.environ.get(name) or default


# --- image stage -------------------------------------------------------------
# Ships with the repo. Talks to a running ComfyUI instance over its HTTP API.
FLUX_SCRIPT = _env_path("SF_FLUX_SCRIPT", REPO_ROOT / "tools" / "flux_t2i.py")
COMFY_URL = _env_str("SF_COMFY_URL", "http://127.0.0.1:8188")

# --- motion stage ------------------------------------------------------------
RENDER_ROUTE = _env_path("SF_RENDER_ROUTE", REPO_ROOT / "bin" / "render-route")

# --- narration stage ---------------------------------------------------------
PIPER = _env_path("SF_PIPER", Path(shutil.which("piper") or (HOME / ".local" / "bin" / "piper")))
PIPER_MODEL = _env_path("SF_PIPER_MODEL", HOME / "piper_voices" / "en_US-libritts_r-medium.onnx")

# Optional cloned character voices (ChatterBox). Only needed when a DSL voice
# preset uses `chatterbox/<character>`.
CHATTERBOX_PY = _env_path("SF_CHATTERBOX_PY", HOME / "chatterbox-env" / "bin" / "python")
CHARACTER_VOICE = _env_path("SF_CHARACTER_VOICE", REPO_ROOT / "bin" / "character_voice.py")

# --- optional lipsync / avatar pipeline --------------------------------------
AVATAR_DIR = _env_path("SF_AVATAR_DIR", HOME / "avatar-pipeline")
LP_DIR = AVATAR_DIR / "LivePortrait"
LP_VENV_PYTHON = LP_DIR / ".venv" / "bin" / "python"
LP_INFERENCE = LP_DIR / "inference.py"
W2L_DIR = AVATAR_DIR / "Wav2Lip"
W2L_CKPT = W2L_DIR / "checkpoints" / "wav2lip_gan.pth"
DRIVER_STILL = _env_path("SF_DRIVER_STILL", REPO_ROOT / "assets" / "walk_frame.png")

# --- legacy full-pipeline engine ---------------------------------------------
# `--engine full` delegates to story_pipeline.py, which is not part of this
# repo. Point SF_VIDEOPIPE at a checkout that has it, or stay on the default
# lean engine, which needs nothing outside this repo.
VIDEOPIPE = _env_path("SF_VIDEOPIPE", REPO_ROOT)
PIPELINE = VIDEOPIPE / "story_pipeline.py"

# --- output ------------------------------------------------------------------
OUT_DIR = _env_path("SF_OUT_DIR", HOME / "story-forge" / "outputs")
WORK_DIR = _env_path("SF_WORK_DIR", HOME / "story-forge" / "work")


# A check is (label, path-or-None, why-you-need-it, required-for-lean-engine).
_CHECKS: list[tuple[str, Path | None, str, bool]] = [
    ("flux script", FLUX_SCRIPT, "SF_FLUX_SCRIPT — draws the still for every scene", True),
    ("render-route", RENDER_ROUTE, "SF_RENDER_ROUTE — dispatches i2v to wan or ltx", True),
    ("piper", PIPER, "SF_PIPER — narration voice", False),
    ("piper model", PIPER_MODEL, "SF_PIPER_MODEL — .onnx voice for piper", False),
    ("chatterbox python", CHATTERBOX_PY, "SF_CHATTERBOX_PY — only for cloned character voices", False),
    ("avatar pipeline", AVATAR_DIR, "SF_AVATAR_DIR — only for `with lipsync`", False),
]


def doctor() -> list[tuple[str, bool, str, str, bool]]:
    """Report on every external dependency.

    Returns rows of (label, ok, location, why, required). Does not raise:
    the point is to show a stranger what is missing before a render dies
    forty minutes in.
    """
    rows = []
    for label, path, why, required in _CHECKS:
        ok = bool(path and path.exists())
        rows.append((label, ok, str(path) if path else "unset", why, required))

    for tool in ("ffmpeg", "ffprobe"):
        found = shutil.which(tool)
        rows.append((tool, bool(found), found or "not on PATH",
                     "assembles scenes into the final cut", True))

    rows.append(("comfyui", _comfy_up(), COMFY_URL,
                 "SF_COMFY_URL — the flux script renders through it", True))
    return rows


def _comfy_up(timeout: float = 1.5) -> bool:
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=timeout):
            return True
    except (urllib.error.URLError, OSError):
        return False


def format_doctor() -> str:
    lines = ["story forge doctor", ""]
    missing_required = 0
    for label, ok, where, why, required in doctor():
        mark = "ok  " if ok else ("MISS" if required else "opt ")
        if not ok and required:
            missing_required += 1
        lines.append(f"  [{mark}] {label:<18} {where}")
        if not ok:
            lines.append(f"         {why}")
    lines.append("")
    if missing_required:
        lines.append(f"{missing_required} required piece(s) missing. "
                     "A lean render will fail until those resolve.")
    else:
        lines.append("all required pieces present.")
    return "\n".join(lines)
