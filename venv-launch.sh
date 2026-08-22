#!/bin/bash
# Launch the Flask UI using ComfyUI's venv (which has flask + our deps installed)
source ~/AI/ComfyUI/venv/bin/activate
export PYTHONPATH="$HOME/AI/videopipe:$PYTHONPATH"
cd ~/AI/videopipe
exec python server.py
