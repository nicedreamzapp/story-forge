# WR3 SFX batch: MOSS-SoundEffect v2.0 (Apache-2.0), CPU float32, ONE load, whole batch.
import os, sys, json, time, contextlib
os.environ["TORCHDYNAMO_DISABLE"] = "1"
import torch, numpy as np, soundfile as sf
torch.autocast = lambda *a, **k: contextlib.nullcontext()   # CPU: no bf16 autocast (no native bf16 on this i7)
torch.set_num_threads(int(os.environ.get("NT", "8")))
from moss_soundeffect_v2 import MossSoundEffectPipeline
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfx_jobs_wr3 import JOBS
W = r"C:\Users\matt\wr3"; O = os.path.join(W, "sfx"); os.makedirs(O, exist_ok=True)
STEPS = int(os.environ.get("STEPS", "30")); ONLY = os.environ.get("ONLY")
NEG = "music, speech, voice, talking, singing, melody"
t0 = time.time()
pipe = MossSoundEffectPipeline.from_pretrained(os.path.join(W, "moss_v2"), torch_dtype=torch.float32, device="cpu")
print(f"loaded {time.time()-t0:.0f}s", flush=True)
log = {}
for name, secs, prompt, seed in JOBS:
    if ONLY and name not in ONLY.split(","): continue
    out = os.path.join(O, f"{name}.wav")
    if os.path.exists(out): continue
    t = time.time()
    mis = max(4, int(np.ceil(secs)) + 1)
    a = pipe(prompt=prompt, seconds=secs, num_inference_steps=STEPS, cfg_scale=4.0, seed=seed,
             negative_prompt=NEG, max_inference_seconds=mis, progress_bar_cmd=lambda x, **k: x)
    y = a[0, 0].float().cpu().numpy(); pk = float(np.abs(y).max())
    if pk > 0.98: y = y * 0.98 / pk
    sf.write(out, y, 48000, subtype="PCM_24")
    log[name] = {"seconds": secs, "steps": STEPS, "seed": seed, "gen_s": round(time.time() - t), "window_s": mis}
    json.dump(log, open(os.path.join(O, f"gen_log_{os.getpid()}.json"), "w"), indent=1)
    print(name, f"{time.time()-t:.0f}s", flush=True)
print("SFX_DONE", round(time.time() - t0), flush=True)
