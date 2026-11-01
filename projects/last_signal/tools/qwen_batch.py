#!/usr/bin/env python3
"""Qwen-Image 2.1 bf16 batch (diffusers on MPS): load ONCE, render every job, unload.
   qwen_batch.py jobs.json      (resumable: skips outputs that already exist)
jobs.json = [{"out": path, "prompt": str, "refs": [paths], "w": int, "h": int, "seed": int, "steps": int}]
Honours: Song Forge first (waits while jobs_running > 0), mem-gate + forge_guard lease (frozen rules 11/16)."""
import json, os, subprocess, sys, time, urllib.request
from pathlib import Path
SF = Path.home() / "Desktop/PROJECTS/story-forge"
jobs = json.load(open(sys.argv[1]))
base = Path(sys.argv[1]).resolve().parent.parent  # project dir (jobs live in tools/ or logs/)
todo = [j for j in jobs if not Path(j["out"]).exists()]
print(f"[qwen] {len(todo)}/{len(jobs)} jobs to render", flush=True)
if not todo:
    sys.exit(0)

def wait_songforge():
    while True:
        try:
            s = json.load(urllib.request.urlopen("http://127.0.0.1:8767/api/status", timeout=5))
            if s.get("jobs_running", 0) == 0:
                return
            print(f"[qwen] Song Forge busy ({s.get('jobs_running')} running), waiting", flush=True)
        except Exception as e:
            print(f"[qwen] status check failed ({e}), proceeding", flush=True); return
        time.sleep(20)

wait_songforge()
if subprocess.run([str(SF / "bin/mem-gate"), "lastsignal qwen-image"]).returncode != 0:
    sys.exit("[qwen] mem-gate refused")
sys.path.insert(0, str(Path.home() / "SongForgeM5"))
from mem_client import reserve_ex  # noqa
import torch
from PIL import Image
from diffusers import QwenImage21Pipeline

with reserve_ex("lastsignal-qwen-image", 48) as got:
    if got[1] == "refused":
        sys.exit("[qwen] forge_guard refused 48GB")
    t = time.time()
    pipe = QwenImage21Pipeline.from_pretrained(str(Path.home() / "AI_Models/Qwen-Image-2.1"),
                                               torch_dtype=torch.bfloat16).to("mps")
    print(f"[qwen] loaded in {time.time()-t:.0f}s", flush=True)
    for i, j in enumerate(todo, 1):
        wait_songforge()
        out = Path(j["out"]); out.parent.mkdir(parents=True, exist_ok=True)
        refs = [Image.open(p).convert("RGB") for p in j.get("refs", [])]
        t = time.time()
        img = pipe(prompt=j["prompt"], image=refs or None, width=j.get("w", 1248), height=j.get("h", 720),
                   num_inference_steps=j.get("steps", 40),
                   generator=torch.Generator("cpu").manual_seed(j.get("seed", 1))).images[0]
        tmp = out.with_suffix(".tmp.png"); img.save(tmp); os.replace(tmp, out)
        print(f"[qwen] {i}/{len(todo)} {out.name} {time.time()-t:.0f}s peak {torch.mps.driver_allocated_memory()/1e9:.1f}GB", flush=True)
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()
    del pipe
print("[qwen] batch done, model unloaded", flush=True)
