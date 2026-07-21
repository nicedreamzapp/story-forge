#!/usr/bin/env python3
"""flux_t2i.py — one still from one prompt, through a running ComfyUI.

This is the image stage of Story Forge. Every scene starts as a single Flux
still; the motion models take it from there. It is a thin ComfyUI API client
on purpose, so you can swap models without touching the pipeline.

Usage:
  flux_t2i.py "prompt text" [--out FILE.png] [--w 1280] [--h 720] [--seed N]

Prints the saved path on stdout. Everything else goes to stderr, so the
pipeline can capture the path cleanly.

Environment:
  SF_COMFY_URL    ComfyUI base URL           (default http://127.0.0.1:8188)
  SF_FLUX_UNET    unet filename as ComfyUI sees it
  SF_FLUX_CLIP1   first CLIP filename
  SF_FLUX_CLIP2   second CLIP (t5) filename
  SF_FLUX_VAE     vae filename
  SF_FLUX_STEPS   sampler steps              (default 20)

The model names must match what ComfyUI lists, including any subfolder. If a
render fails with "value not in list", run `flux_t2i.py --list-models` to see
what your install actually has.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

COMFY = os.environ.get("SF_COMFY_URL", "http://127.0.0.1:8188").rstrip("/")

UNET = os.environ.get("SF_FLUX_UNET", "flux/flux1-dev-fp8.safetensors")
CLIP1 = os.environ.get("SF_FLUX_CLIP1", "clip_l.safetensors")
CLIP2 = os.environ.get("SF_FLUX_CLIP2", "t5xxl_fp16.safetensors")
VAE = os.environ.get("SF_FLUX_VAE", "flux/ae.safetensors")
STEPS = int(os.environ.get("SF_FLUX_STEPS", "20"))


def build_workflow(prompt: str, width: int, height: int, seed: int) -> dict:
    return {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {"unet_name": UNET, "weight_dtype": "default"},
        },
        "2": {
            "class_type": "DualCLIPLoader",
            "inputs": {"clip_name1": CLIP1, "clip_name2": CLIP2, "type": "flux"},
        },
        "3": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": VAE},
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["2", 0], "text": prompt},
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1},
        },
        "6": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": STEPS,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["4", 0],
                "negative": ["4", 0],
                "latent_image": ["5", 0],
            },
        },
        "7": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["6", 0], "vae": ["3", 0]},
        },
        "8": {
            "class_type": "SaveImage",
            "inputs": {"images": ["7", 0], "filename_prefix": "storyforge"},
        },
    }


def http_json(path: str, body=None, method=None):
    url = COMFY + path
    if body is not None:
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"},
            method=method or "POST")
    else:
        req = urllib.request.Request(url, method=method or "GET")
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read().decode())


def fetch_image(filename: str, subfolder: str, kind: str) -> bytes:
    """Pull the rendered image over HTTP.

    Deliberately not reading ComfyUI's output directory off disk: that
    hardcodes one machine's layout and breaks the moment ComfyUI runs
    somewhere else. /view is the supported way out.
    """
    q = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": kind})
    with urllib.request.urlopen(f"{COMFY}/view?{q}", timeout=600) as r:
        return r.read()


def queue_prompt(workflow: dict) -> str:
    return http_json("/prompt", {"prompt": workflow})["prompt_id"]


def wait_for(prompt_id: str, poll_s: float = 2.0, deadline_s: float = 600.0) -> dict:
    start = time.time()
    while True:
        hist = http_json(f"/history/{prompt_id}")
        if prompt_id in hist:
            return hist[prompt_id]
        if time.time() - start > deadline_s:
            raise RuntimeError(f"timed out waiting for {prompt_id}")
        time.sleep(poll_s)


def list_models() -> int:
    """Print what this ComfyUI actually has, so name mismatches are obvious."""
    try:
        info = http_json("/object_info")
    except (urllib.error.URLError, OSError) as e:
        print(f"cannot reach ComfyUI at {COMFY}: {e}", file=sys.stderr)
        return 2
    for node, key in (("UNETLoader", "unet_name"),
                      ("DualCLIPLoader", "clip_name1"),
                      ("VAELoader", "vae_name")):
        try:
            opts = info[node]["input"]["required"][key][0]
        except (KeyError, IndexError, TypeError):
            continue
        print(f"{node}.{key}:")
        for o in opts:
            print(f"  {o}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?")
    ap.add_argument("--out", default=None, help="write the image here")
    ap.add_argument("--w", type=int, default=1280)
    ap.add_argument("--h", type=int, default=720)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--list-models", action="store_true",
                    help="show the model names this ComfyUI exposes, then exit")
    args = ap.parse_args()

    if args.list_models:
        return list_models()
    if not args.prompt:
        ap.error("prompt is required (or pass --list-models)")

    seed = args.seed if args.seed is not None else random.randint(1, 2**31 - 1)
    wf = build_workflow(args.prompt, args.w, args.h, seed)

    try:
        prompt_id = queue_prompt(wf)
    except urllib.error.URLError as e:
        print(f"cannot reach ComfyUI at {COMFY}: {e}\n"
              f"start ComfyUI first, or set SF_COMFY_URL.", file=sys.stderr)
        return 2

    print(f"queued prompt_id={prompt_id} seed={seed}", file=sys.stderr)
    result = wait_for(prompt_id)

    outputs = result.get("outputs", {})
    save_node = outputs.get("8") or next(
        (v for v in outputs.values() if "images" in v), None)
    if not save_node or not save_node.get("images"):
        status = result.get("status", {})
        raise RuntimeError(
            f"no image came back. comfy status={json.dumps(status)[:400]}")

    img = save_node["images"][0]
    blob = fetch_image(img["filename"], img.get("subfolder", ""),
                       img.get("type", "output"))

    out = Path(args.out).expanduser() if args.out else Path(img["filename"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)
    print(str(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
