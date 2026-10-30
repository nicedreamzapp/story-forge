"""promo_common.py — the bits every promo tool shares (promo format, 2026-10-22).

promo.json loading with defaults, script.md parsing (numbered lines plus optional `say:` / `alt:`
sub-lines), the text normalizer the whisper gates compare with, Song Forge's busy check, and
small ffmpeg helpers. Pure stdlib; num2words is used when the venv has it.

The defaults below ARE the proven Sitka recipe (sitka-video/PRODUCTION.md, 2026-10-22):
Matt's ChatterBox clone matt2, exaggeration 0.40, cfg 0.5, pitch 0.92 via asetrate (never
rubberband), EQ +3 dB @180 Hz / -3 dB @5 kHz, -16 LUFS, 0.5-0.85 s line gaps, bed sidechain-
ducked under the voice, the end-card slam AFTER the last word so the hit never masks it.
"""
from __future__ import annotations

import json
import re
import subprocess
import urllib.request
from pathlib import Path

SF = Path(__file__).resolve().parent.parent
HOME = Path.home()
CHATTERBOX_PY = HOME / "chatterbox-env" / "bin" / "python"
CHATTERBOX_BATCH = HOME / ".local" / "bin" / "chatterbox-batch"
MLX_PY = HOME / ".local" / "mlx-server" / "bin" / "python"
SONG_FORGE = "http://127.0.0.1:8767"
WHISPER_ID = "mlx-community/whisper-large-v3-turbo"

DEFAULTS = {
    "title": "",
    "brand": "",
    "voice": {"character": "matt2", "exaggeration": 0.40, "cfg": 0.5, "pitch": 0.92,
              "eq": [[180, 3.0], [5000, -3.0]], "lufs": -16.0, "retakes": 3},
    "gap": 0.6,
    "lead": 0.4,
    "music": {"bed": None, "style": "cinematic orchestral and piano build, hopeful, instrumental",
              "gain": 0.55, "hit": None, "fade": 1.6, "tail": 1.1},
    "endcard": {"title": "", "tagline": "", "url": "", "dur": 5.0, "slam_after": 0.15},
    "bug": "",
    "renderer": "ffmpeg",
    "blender": [],
    "i2v": [],
    "youtube": {"title": "", "tags": [], "category": "Science & Technology", "description": ""},
    "gates": {"lufs": -16.0, "lufs_tol": 1.0, "true_peak_max": -1.0, "design_votes": 3},
}


def deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = deep_merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


def load_promo(film: Path) -> dict:
    p = Path(film) / "promo.json"
    raw = json.loads(p.read_text()) if p.exists() else {}
    return deep_merge(DEFAULTS, raw)


def parse_script(path: Path) -> list[dict]:
    """script.md -> [{"line": N, "text": str, "say": str|None, "alts": [str]}].

    `N. [picture note] spoken text` is a line; indented `say: ...` (what the TTS reads when it
    differs, e.g. "fifteen kilo" for "15 kg") and `alt: ...` (a re-wording the voice stage may
    fall back to when whisper keeps mishearing the line) belong to the line above them."""
    out: list[dict] = []
    for raw in Path(path).read_text().splitlines():
        if raw.startswith("<!--"):
            continue
        m = re.match(r"^\s*(\d+)[.)]\s+(.*)$", raw)
        if m:
            text = re.sub(r"\s+", " ", re.sub(r"\[[^\]]*\]", "", m.group(2))).strip()
            if text:
                out.append({"line": int(m.group(1)), "text": text, "say": None, "alts": []})
            continue
        m = re.match(r"^\s+(say|alt):\s*(.+)$", raw, re.I)
        if m and out:
            if m.group(1).lower() == "say":
                out[-1]["say"] = m.group(2).strip()
            else:
                out[-1]["alts"].append(m.group(2).strip())
    return out


_ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
         "fifteen sixteen seventeen eighteen nineteen").split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def _say_int(n: int) -> str:
    try:
        from num2words import num2words
        return num2words(n)
    except Exception:  # noqa: BLE001 — small fallback, enough for promo numbers
        if n < 20:
            return _ONES[n]
        if n < 100:
            return _TENS[n // 10] + ("" if n % 10 == 0 else " " + _ONES[n % 10])
        if n < 1000:
            return _ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " " + _say_int(n % 100))
        return _say_int(n // 1000) + " thousand" + ("" if n % 1000 == 0 else " " + _say_int(n % 1000))


def norm_words(text: str) -> list[str]:
    """Words as a listener hears them: lowercase, numbers spelled out, $ and % read aloud,
    hyphens/punctuation dropped. Both sides of every whisper compare go through this."""
    t = text.lower().replace("’", "'")
    t = re.sub(r"\$\s?([\d,]+)", lambda m: m.group(1) + " dollars", t)
    t = re.sub(r"(\d)%", r"\1 percent", t)
    t = re.sub(r"(\d),(\d{3})", r"\1\2", t)
    t = re.sub(r"\d+", lambda m: " " + _say_int(int(m.group(0))) + " ", t)
    t = re.sub(r"[-\u2010-\u2015]", " ", t)  # hyphens AND en/em dashes: "hardware—zero" is two words (10/26)
    t = re.sub(r"\band\b", " and ", t)
    return [w for w in (re.sub(r"[^a-z0-9']", "", w).strip("'") for w in t.split()) if w and w != "and"]


def compare_words(expected: str, heard: str) -> tuple[int, int, list[str]]:
    """(matched, total expected, mismatch notes). 'and' is ignored on both sides (whisper drops
    and adds it freely around numbers); everything else must match in order."""
    import difflib
    e, h = norm_words(expected), norm_words(heard)
    sm = difflib.SequenceMatcher(a=e, b=h, autojunk=False)
    matched = sum(b.size for b in sm.get_matching_blocks())
    notes = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op != "equal":
            notes.append(f"expected '{' '.join(e[i1:i2]) or '-'}' heard '{' '.join(h[j1:j2]) or '-'}'")
    return matched, len(e), notes


def song_forge_busy() -> tuple[bool, str]:
    """(busy, why). Song Forge customer jobs outrank every render (frozen rules 11, 16).
    Unreachable counts as NOT busy only because it means nothing is running there; say so."""
    try:
        with urllib.request.urlopen(SONG_FORGE + "/api/status", timeout=5) as r:
            st = json.load(r)
    except Exception as e:  # noqa: BLE001
        return False, f"Song Forge not reachable ({type(e).__name__}); treating as idle"
    n = int(st.get("jobs_running") or 0)
    return n > 0, f"jobs_running={n}"


def run(cmd, **kw) -> subprocess.CompletedProcess:
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kw)
    if r.returncode != 0:
        tail = "\n".join((r.stderr or r.stdout).strip().splitlines()[-12:])
        raise RuntimeError(f"command failed ({Path(str(cmd[0])).name} ...):\n{tail}")
    return r


def duration(path) -> float:
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path])
    return float(r.stdout.strip())


def ebur128(path, start=None, dur=None) -> dict:
    """Integrated loudness, true peak, LRA of a file (or a window of it) via ffmpeg ebur128."""
    cmd = ["ffmpeg", "-hide_banner", "-nostats"]
    if start is not None:
        cmd += ["-ss", f"{start:.3f}"]
    if dur is not None:
        cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    txt = r.stderr
    summ = txt[txt.rfind("Summary:"):] if "Summary:" in txt else txt

    def grab(pat):
        m = re.search(pat, summ)
        return float(m.group(1)) if m else None
    return {"I": grab(r"I:\s+(-?[\d.]+) LUFS"), "LRA": grab(r"LRA:\s+(-?[\d.]+) LU"),
            "TP": grab(r"Peak:\s+(-?[\d.]+) dBFS")}
