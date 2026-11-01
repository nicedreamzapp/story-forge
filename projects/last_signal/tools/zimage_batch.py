#!/usr/bin/env python3
"""Z-Image-Turbo bf16 batch (diffusers, MPS), staged so the peak stays under the guard's allowance:
  stage 1: text encoder only -> encode every prompt -> free it
  stage 2: transformer + VAE -> render every job (t2i, or img2img when a job has "init" + "strength") -> free.
  zimage_batch.py jobs.json   (resumable; skips existing outputs)
jobs: [{"out","prompt","w","h","seed", optional "init","strength"}]"""
import gc, json, os, subprocess, sys, time, urllib.request
from pathlib import Path
SF = Path.home() / "Desktop/PROJECTS/story-forge"
jobs = json.load(open(sys.argv[1]))
todo = [j for j in jobs if not Path(j["out"]).exists()]
print(f"[zimg] {len(todo)}/{len(jobs)} jobs", flush=True)
if not todo: sys.exit(0)
GB = float(os.environ.get("ZIMG_GB", "20"))

def wait_songforge():
    while True:
        try:
            s = json.load(urllib.request.urlopen("http://127.0.0.1:8767/api/status", timeout=5))
            if s.get("jobs_running", 0) == 0: return
            print(f"[zimg] Song Forge busy, waiting", flush=True)
        except Exception: return
        time.sleep(20)

wait_songforge()
if subprocess.run([str(SF / "bin/mem-gate"), "lastsignal z-image"]).returncode != 0:
    sys.exit("[zimg] mem-gate refused")
sys.path.insert(0, str(Path.home() / "SongForgeM5"))
from mem_client import reserve_ex  # noqa
import glob, torch
from PIL import Image
from diffusers import ZImagePipeline, ZImageImg2ImgPipeline
MODEL = glob.glob(str(Path.home() / ".cache/huggingface/hub/models--Tongyi-MAI--Z-Image-Turbo/snapshots/*"))[0]

with reserve_ex("lastsignal-z-image", GB) as got:
    if got[1] == "refused":
        sys.exit(f"[zimg] forge_guard refused {GB}GB")
    t = time.time()
    pipe = ZImagePipeline.from_pretrained(MODEL, torch_dtype=torch.bfloat16, transformer=None, vae=None)
    pipe.text_encoder.to("mps")
    embeds = {}
    with torch.no_grad():
        for j in todo:
            if j["prompt"] not in embeds:
                pe, _ = pipe.encode_prompt(prompt=j["prompt"], device="mps", do_classifier_free_guidance=False)
                embeds[j["prompt"]] = [e.to("cpu") for e in pe] if isinstance(pe, list) else pe.to("cpu")
    del pipe; gc.collect(); torch.mps.empty_cache()
    print(f"[zimg] encoded {len(embeds)} prompts in {time.time()-t:.0f}s", flush=True)
    t = time.time()
    pipe = ZImagePipeline.from_pretrained(MODEL, torch_dtype=torch.bfloat16, text_encoder=None, tokenizer=None).to("mps")
    i2i = ZImageImg2ImgPipeline(**pipe.components)
    print(f"[zimg] transformer loaded in {time.time()-t:.0f}s", flush=True)
    for k, j in enumerate(todo, 1):
        wait_songforge()
        out = Path(j["out"]); out.parent.mkdir(parents=True, exist_ok=True)
        pe = embeds[j["prompt"]]
        pe = [e.to("mps") for e in pe] if isinstance(pe, list) else pe.to("mps")
        g = torch.Generator("cpu").manual_seed(j.get("seed", 1))
        t = time.time()
        kw = dict(prompt_embeds=pe, width=j.get("w", 1248), height=j.get("h", 720),
                  num_inference_steps=j.get("steps", 9), guidance_scale=0.0, generator=g)
        if j.get("init"):
            init = Image.open(j["init"]).convert("RGB").resize((kw["width"], kw["height"]), Image.LANCZOS)
            img = i2i(image=init, strength=j.get("strength", 0.5), **kw).images[0]
        else:
            img = pipe(**kw).images[0]
        tmp = out.with_suffix(".tmp.png"); img.save(tmp); os.replace(tmp, out)
        print(f"[zimg] {k}/{len(todo)} {out.name} {time.time()-t:.0f}s peak {torch.mps.driver_allocated_memory()/1e9:.1f}GB", flush=True)
    del pipe, i2i; gc.collect(); torch.mps.empty_cache()
print("[zimg] batch done, model unloaded", flush=True)
