#!/usr/bin/env python3
"""vl_ask_cli — ask the local vision model one question about one image, from any venv.

The judge lives in the mlx venv; rembg and mflux live in another. Scripts kept dying
on ModuleNotFoundError trying to have both. This is the bridge: shell out, get an
answer, no shared environment required.

    ~/.local/mlx-server/bin/python pipeline-tools/vl_ask_cli.py IMG "question"
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from film_qc import vl_ask, _state
_state["use_server"] = False
print(vl_ask(sys.argv[1], sys.argv[2]).strip().replace("\n", " "))
