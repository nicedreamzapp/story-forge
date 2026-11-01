#!/usr/bin/env python3
"""Launch the SeedVR2 node CLI with transformers' flash-attention probe resolved FIRST. The node stubs a fake
`flash_attn` module when the real one is missing (always, on a Mac); newer transformers then sees it as installed
and dies with KeyError 'flash_attn' in PACKAGE_DISTRIBUTION_MAPPING. Importing the probe before the stub exists caches
the honest answer (not available), and the CLI runs unchanged. Usage: same args as inference_cli.py."""
import runpy, sys
from pathlib import Path
import transformers.integrations.flash_attention  # noqa: F401  (evaluated with no stub present)
import diffusers.loaders.single_file_model         # noqa: F401
CLI = Path.home() / "AI/ComfyUI/custom_nodes/ComfyUI-SeedVR2_VideoUpscaler/inference_cli.py"
sys.path.insert(0, str(CLI.parent))
sys.argv = [str(CLI)] + sys.argv[1:]
runpy.run_path(str(CLI), run_name="__main__")
