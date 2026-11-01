#!/usr/bin/env python3
"""Stills batch (diffusers, MPS, bf16), staged so the peak stays under the guard's allowance:
  stage 1: text encoder only -> encode every prompt -> free it
  stage 2: transformer + VAE -> render every job -> free.
  Text-to-image jobs render on Krea 2 Turbo (8 steps, cfg 0; switched from Z-Image-Turbo 2026-11-01,
  it won 5 of 6 trailer shots). img2img jobs (a job with "init" + "strength") stay on Z-Image-Turbo,
  diffusers has no Krea 2 img2img. Re-runs itself under ~/AI/krea2/venv (diffusers 0.42.1).
  zimage_batch.py jobs.json   (resumable; skips existing outputs)
jobs: [{"out","prompt","w","h","seed", optional "init","strength"}]"""
import gc, json, os, subprocess, sys, threading, time, urllib.request
from pathlib import Path
KREA_PY = Path.home() / "AI/krea2/venv/bin/python"
if KREA_PY.exists() and Path(sys.prefix) != KREA_PY.parent.parent:
    os.execv(str(KREA_PY), [str(KREA_PY), *sys.argv])
SF = Path.home() / "Desktop/PROJECTS/story-forge"
jobs = json.load(open(sys.argv[1]))
todo = [j for j in jobs if not Path(j["out"]).exists()]
print(f"[zimg] {len(todo)}/{len(jobs)} jobs", flush=True)
if not todo: sys.exit(0)
t2i_jobs = [j for j in todo if not j.get("init")]
i2i_jobs = [j for j in todo if j.get("init")]
GB = float(os.environ.get("ZIMG_GB", "40" if t2i_jobs else "20"))

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
from safetensors.torch import load_file
HUB = Path.home() / ".cache/huggingface/hub"
snap = lambda repo: Path(glob.glob(str(HUB / f"models--{repo.replace('/', '--')}/snapshots/*"))[0])

PEAK = [0]
def _sample():  # max MPS driver memory since the last reset
    while True:
        try: PEAK[0] = max(PEAK[0], torch.mps.driver_allocated_memory())
        except Exception: pass
        time.sleep(0.1)
threading.Thread(target=_sample, daemon=True).start()
def peak_gb(): return max(PEAK[0], torch.mps.driver_allocated_memory()) / 1e9
def free(): gc.collect(); torch.mps.synchronize(); torch.mps.empty_cache()

def save(img, out):
    tmp = out.with_suffix(".tmp.png"); img.save(tmp); os.replace(tmp, out)

# ---------------- Krea 2 Turbo (text-to-image) ----------------
# Weights: Comfy-Org/Krea-2 (ungated mirror of krea/Krea-2-Turbo): krea2_turbo_bf16 transformer,
# qwen3vl_4b_bf16 text encoder. Configs/tokenizer from Qwen/Qwen3-VL-4B-Instruct, VAE = Qwen-Image VAE.
def krea2_text_encoder():
    from transformers import AutoConfig, Qwen3VLModel
    from accelerate import init_empty_weights
    with init_empty_weights():
        te = Qwen3VLModel(AutoConfig.from_pretrained(snap("Qwen/Qwen3-VL-4B-Instruct")))
    sd = load_file(str(snap("Comfy-Org/Krea-2") / "text_encoders/qwen3vl_4b_bf16.safetensors"))
    want = set(te.state_dict().keys()); fixed = {}
    for k, v in sd.items():
        for pre in ("model.", ""):
            if k.startswith(pre) and k[len(pre):] in want:
                fixed[k[len(pre):]] = v; break
    te.load_state_dict(fixed, assign=True, strict=True)
    return te.to(torch.bfloat16).eval()

def krea2_transformer():
    from diffusers import Krea2Transformer2DModel
    from diffusers.loaders.single_file_utils import convert_krea2_transformer_checkpoint_to_diffusers
    from accelerate import init_empty_weights
    with init_empty_weights():
        tr = Krea2Transformer2DModel()
    tr.load_state_dict(convert_krea2_transformer_checkpoint_to_diffusers(
        load_file(str(snap("Comfy-Org/Krea-2") / "diffusion_models/krea2_turbo_bf16.safetensors"))), assign=True, strict=True)
    return tr.to(torch.bfloat16).eval()

def krea2_pipe(**parts):
    from diffusers import Krea2Pipeline, FlowMatchEulerDiscreteScheduler
    sched = FlowMatchEulerDiscreteScheduler(use_dynamic_shifting=True, base_shift=0.5, max_shift=1.15,
                                            base_image_seq_len=256, max_image_seq_len=6400)
    return Krea2Pipeline(scheduler=sched, is_distilled=True, **parts)

def run_krea2(todo):
    from transformers import AutoTokenizer
    from diffusers import AutoencoderKLQwenImage
    t = time.time()
    te = krea2_text_encoder().to("mps")
    pipe = krea2_pipe(vae=None, text_encoder=te, tokenizer=AutoTokenizer.from_pretrained(snap("Qwen/Qwen3-VL-4B-Instruct")), transformer=None)
    embeds = {}
    with torch.no_grad():
        for j in todo:
            if j["prompt"] not in embeds:
                pe, pm = pipe.get_text_hidden_states(j["prompt"], device=torch.device("mps"))
                embeds[j["prompt"]] = (pe.to("cpu"), pm.to("cpu"))
    del pipe, te; free()
    print(f"[zimg] krea2: encoded {len(embeds)} prompts in {time.time()-t:.0f}s", flush=True)
    t = time.time()
    tr = krea2_transformer().to("mps")
    vae = AutoencoderKLQwenImage.from_pretrained(snap("Qwen/Qwen-Image") / "vae", torch_dtype=torch.bfloat16).to("mps")
    pipe = krea2_pipe(vae=vae, text_encoder=None, tokenizer=None, transformer=tr)
    print(f"[zimg] krea2: transformer loaded in {time.time()-t:.0f}s", flush=True)
    for k, j in enumerate(todo, 1):
        wait_songforge()
        out = Path(j["out"]); out.parent.mkdir(parents=True, exist_ok=True)
        pe, pm = (x.to("mps") for x in embeds[j["prompt"]])
        g = torch.Generator("cpu").manual_seed(j.get("seed", 1))
        PEAK[0] = 0; t = time.time()
        img = pipe(prompt_embeds=pe, prompt_embeds_mask=pm, width=j.get("w", 1248), height=j.get("h", 720),
                   num_inference_steps=8, guidance_scale=0.0, generator=g).images[0]
        torch.mps.synchronize(); save(img, out)
        print(f"[zimg] krea2 {k}/{len(todo)} {out.name} {time.time()-t:.0f}s peak {peak_gb():.1f}GB", flush=True)
    del pipe, tr, vae; free()

# ---------------- Z-Image-Turbo (img2img only) ----------------
def run_zimage_i2i(todo):
    from diffusers import ZImagePipeline, ZImageImg2ImgPipeline
    MODEL = snap("Tongyi-MAI/Z-Image-Turbo")
    t = time.time()
    pipe = ZImagePipeline.from_pretrained(MODEL, torch_dtype=torch.bfloat16, transformer=None, vae=None)
    pipe.text_encoder.to("mps")
    embeds = {}
    with torch.no_grad():
        for j in todo:
            if j["prompt"] not in embeds:
                pe, _ = pipe.encode_prompt(prompt=j["prompt"], device="mps", do_classifier_free_guidance=False)
                embeds[j["prompt"]] = [e.to("cpu") for e in pe] if isinstance(pe, list) else pe.to("cpu")
    del pipe; free()
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
        PEAK[0] = 0; t = time.time()
        w, h = j.get("w", 1248), j.get("h", 720)
        init = Image.open(j["init"]).convert("RGB").resize((w, h), Image.LANCZOS)
        img = i2i(image=init, strength=j.get("strength", 0.5), prompt_embeds=pe, width=w, height=h,
                  num_inference_steps=j.get("steps", 9), guidance_scale=0.0, generator=g).images[0]
        save(img, out)
        print(f"[zimg] {k}/{len(todo)} {out.name} {time.time()-t:.0f}s peak {peak_gb():.1f}GB", flush=True)
    del pipe, i2i; free()

with reserve_ex("lastsignal-z-image", GB) as got:
    if got[1] == "refused":
        sys.exit(f"[zimg] forge_guard refused {GB}GB")
    if t2i_jobs: run_krea2(t2i_jobs)
    if i2i_jobs: run_zimage_i2i(i2i_jobs)
print("[zimg] batch done, model unloaded", flush=True)
