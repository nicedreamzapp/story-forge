import torch, os, sys
from PIL import Image
from diffusers import DiffusionPipeline, EulerAncestralDiscreteScheduler
# device: pass "cpu" or "mps" as arg1; default cpu (MPS gives noise with this pipeline)
dev = sys.argv[1] if len(sys.argv) > 1 else "cpu"
print("device:", dev, flush=True)
# LOCAL vetted custom pipeline (reviewed) — weights still pulled from HF
VET = os.path.expanduser("~/Desktop/PROJECTS/story-forge/3d-spike/vet")
pipe = DiffusionPipeline.from_pretrained(
    "sudo-ai/zero123plus-v1.2",
    custom_pipeline=VET,
    trust_remote_code=True,
    torch_dtype=torch.float32)
pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(
    pipe.scheduler.config, timestep_spacing='trailing')
pipe.to(dev)
print("pipeline loaded", flush=True)
cond = Image.open(os.path.expanduser("~/AI/ComfyUI/input/doug_rgba.png")).convert("RGBA")
bg = Image.new("RGBA", cond.size, (255, 255, 255, 255)); bg.alpha_composite(cond)
cond = bg.convert("RGB")
g = torch.Generator(dev).manual_seed(42)
result = pipe(cond, num_inference_steps=36, generator=g).images[0]
out = os.path.expanduser("~/Desktop/PROJECTS/story-forge/3d-spike/views_z123")
os.makedirs(out, exist_ok=True)
result.save(os.path.join(out, "grid.png"))
# zero123++ returns a 2-col x 3-row grid; az order 30,90,150,210,270,330
W, H = result.size; tw, th = W // 2, H // 3
az = [30, 90, 150, 210, 270, 330]; k = 0
for r in range(3):
    for c in range(2):
        result.crop((c*tw, r*th, (c+1)*tw, (r+1)*th)).save(os.path.join(out, f"view_{az[k]:03d}.png")); k += 1
print("saved grid + 6 views to", out, "grid size", result.size, flush=True)
