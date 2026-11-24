#!/usr/bin/env python3
"""matt_voice.py — Matt's narration voice, LOCKED (Matt 2026-11-24). The only way Story Forge voices Matt.

    engine       ChatterBox (~/chatterbox-env)
    reference    ~/Desktop/PROJECTS/avatar-assets/matt-inputs/matt_real_ref.wav
    settings     exaggeration 0.45, cfg_weight 0.5, temperature 0.75, torch seed 7 (set before every line)
    finish       silence trim at both ends ONLY. No pitch, no EQ, no effects, no limiter, no loudnorm on his voice.

voices/voice2_matt.wav is retired for Matt and must never be used for him again; pitch 0.92 and the warm EQ
are retired too. Any other setting is not his voice. Run on ~/chatterbox-env/bin/python.

    # one line
    ~/chatterbox-env/bin/python pipeline-tools/matt_voice.py --line "Text." --out vo/n01.wav
    # many lines, ONE model load (same stdin shape as ~/.local/bin/chatterbox-batch, writes part000.wav ...)
    echo '{"lines": ["one.", "two."], "out_dir": "/tmp/x"}' | ~/chatterbox-env/bin/python pipeline-tools/matt_voice.py --batch
    # inside your own script:  from matt_voice import load, say;  m = load();  say(m, "Text.", "out.wav")
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
PY = HOME / "chatterbox-env" / "bin" / "python"
REF = HOME / "Desktop" / "PROJECTS" / "avatar-assets" / "matt-inputs" / "matt_real_ref.wav"
EXAGGERATION = 0.45
CFG_WEIGHT = 0.5
TEMPERATURE = 0.75
SEED = 7
RETIRED = ("voice2_matt",)          # refs that must never voice Matt again
TRIM = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,"
        "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse")
SETTINGS = {"engine": "chatterbox", "ref": str(REF), "exaggeration": EXAGGERATION, "cfg_weight": CFG_WEIGHT,
            "temperature": TEMPERATURE, "seed": SEED, "finish": "silence trim only"}


def check_locked() -> None:
    if not REF.is_file():
        raise SystemExit(f"[matt_voice] Matt's reference {REF} is missing; nothing is voiced with a stand-in")


def load():
    check_locked()
    os.environ.setdefault("PYTORCH_MPS_HIGH_WATERMARK_RATIO", "0.3")
    os.environ.setdefault("PYTORCH_MPS_LOW_WATERMARK_RATIO", "0.25")
    import torch
    from chatterbox.tts import ChatterboxTTS
    return ChatterboxTTS.from_pretrained(device="mps" if torch.backends.mps.is_available() else "cpu")


def trim(src: Path, dst: Path) -> None:
    """Silence trim at both ends, same sample rate, nothing else."""
    ff = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
    r = subprocess.run([ff, "-v", "error", "-y", "-i", str(src), "-af", TRIM, str(dst)], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"silence trim failed on {src.name}: {r.stderr.strip()[-200:]}")


def say(model, text: str, out: str | Path) -> Path:
    """One line in Matt's locked voice -> out (silence-trimmed only)."""
    import torch
    import torchaudio
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(SEED)
    wav = model.generate(text, exaggeration=EXAGGERATION, cfg_weight=CFG_WEIGHT, temperature=TEMPERATURE,
                         audio_prompt_path=str(REF))
    raw = out.with_name(out.stem + ".raw" + out.suffix)
    torchaudio.save(str(raw), wav.cpu() if hasattr(wav, "cpu") else wav, model.sr)
    trim(raw, out)
    raw.unlink(missing_ok=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Matt's locked narration voice")
    ap.add_argument("--line")
    ap.add_argument("--out")
    ap.add_argument("--batch", action="store_true", help='stdin JSON {"lines": [...], "out_dir": "..."}')
    ap.add_argument("--settings", action="store_true", help="print the locked settings and exit")
    a = ap.parse_args()
    if a.settings:
        print(json.dumps(SETTINGS, indent=1))
        return 0
    if a.batch:
        req = json.load(sys.stdin)
        lines, out_dir = req["lines"], Path(req["out_dir"])
    elif a.line and a.out:
        lines, out_dir = [a.line], None
    else:
        ap.error("--line + --out, or --batch")
    m = load()
    for i, text in enumerate(lines):
        dst = (out_dir / f"part{i:03d}.wav") if out_dir else Path(a.out)
        say(m, text, dst)
        print(f"[matt_voice] {dst}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
