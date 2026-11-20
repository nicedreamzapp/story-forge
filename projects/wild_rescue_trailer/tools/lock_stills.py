#!/usr/bin/env python3
"""Lock one start still per render: the first candidate in tools/preselect.txt order that the vision gate PASSED;
if none passed, the agent's first by-eye pick is locked and flagged GATE-FAIL-KEPT (a declared exception, listed in
stages/04_shots/kept_clips_review.md). Writes stills/LOCKED_<rid>.png at 832x480 (chmod 444) + logs/locks.json."""
import json, os, re
from pathlib import Path
from PIL import Image
P = Path(__file__).resolve().parent.parent
log = "".join((P / f).read_text() for f in ("logs/gate_stills.log", "logs/gate_stills2.log") if (P / f).exists())
verdict = {m.group(2): m.group(1) for m in re.finditer(r"^\[(PASS|FAIL)\] (\S+):", log, re.M)}
locks = {}
for line in open(P / "tools/preselect.txt"):
    rid, *tags = line.split()
    cands = [f"{rid}_{t}" for t in tags if (P / f"stills/cand/{rid}_{t}.png").exists()]
    win = next((c for c in cands if verdict.get(c) == "PASS"), None)
    flag = "PASS" if win else "GATE-FAIL-KEPT"
    win = win or cands[0]
    out = P / f"stills/LOCKED_{rid}.png"
    if out.exists(): os.chmod(out, 0o644)
    Image.open(P / f"stills/cand/{win}.png").convert("RGB").resize((832, 480), Image.LANCZOS).save(out)
    os.chmod(out, 0o444)
    locks[rid] = {"from": f"stills/cand/{win}.png", "gate": flag, "votes": {c: verdict.get(c, "UNCHECKED") for c in cands}}
json.dump(locks, open(P / "logs/locks.json", "w"), indent=1)
print(sum(v["gate"] == "PASS" for v in locks.values()), "PASS-locked;", [k for k, v in locks.items() if v["gate"] != "PASS"], "kept by eye")
