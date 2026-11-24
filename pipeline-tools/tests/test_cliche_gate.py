#!/usr/bin/env python3
"""Run: python3 pipeline-tools/tests/test_cliche_gate.py   (plain code, no model, a few seconds)
The captcha film must FAIL on its known cliches; the clean sample must PASS."""
import subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
GATE = [sys.executable, str(ROOT / "pipeline-tools" / "cliche_gate.py")]
bad = 0
cap = ROOT / "projects" / "captcha_checkbox"
if cap.is_dir():
    r = subprocess.run(GATE + [str(cap)], capture_output=True, text=True)
    need = ["robot", "alarm", "corridor", "vault", "lock", "lamp", "LOOK"]
    missing = [w for w in need if w not in r.stdout]
    ok = r.returncode == 1 and not missing
    print(("ok  " if ok else "BAD ") + f"captcha_checkbox fails (rc={r.returncode})" + (f", missing {missing}" if missing else ""))
    bad += not ok
else:
    print("skip captcha_checkbox (not on this machine)")
r = subprocess.run(GATE + [str(HERE / "cliche_sample")], capture_output=True, text=True)
ok = r.returncode == 0
print(("ok  " if ok else "BAD ") + f"clean sample passes (rc={r.returncode})")
if not ok:
    print(r.stdout)
bad += not ok
sys.exit(1 if bad else 0)
