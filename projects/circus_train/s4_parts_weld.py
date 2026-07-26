#!/usr/bin/env python3
"""s4_arrival via the PROVEN recipe (s2_weld_hunt): single-LoRA character parts →
cut out → composited onto a character-free plate → gentle weld with both LoRAs.

Why not just prompt the scene: two character LoRAs stacked in one text2img dilute
each other and both characters come out generic — that is exactly how a teddy bear
and a yellow labrador ended up in the arrival shot on 2026-07-26. Each character is
rendered ALONE at full LoRA strength (which is how the canon masters were made),
so each one is on-model before it is ever placed.

Run with the mflux venv (it has rembg):
    ~/mflux-venv/bin/python projects/circus_train/s4_parts_weld.py
"""
import subprocess, sys, time
from pathlib import Path
from PIL import Image
from rembg import remove

HERE = Path(__file__).resolve().parent
STILLS = HERE / "stills"
WIP = STILLS / "wip"
MFLUX = Path.home() / "mflux-venv/bin/mflux-generate-flux2"
MODEL = "AITRADER/FLUX2-klein-9B-mlx-8bit"
HL = str(Path.home() / ".hankdoug_seeds/HANK_LORA.safetensors")
DL = str(Path.home() / ".hankdoug_seeds/DOUG_LORA_V2.safetensors")


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def gen(prompt, loras, scales, seed, out, w=832, h=480, init=None, strength=None):
    cmd = ["nice", "-n", "10", str(MFLUX), "-m", MODEL,
           "--lora-paths", *loras, "--lora-scales", *[str(s) for s in scales],
           "--guidance", "1.0", "--steps", "26", "--seed", str(seed),
           "--width", str(w), "--height", str(h), "--output", str(out), "--prompt", prompt]
    if init:
        cmd += ["--image-path", str(init), "--image-strength", str(strength)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
    if not out.exists():
        log(f"  gen failed: {(r.stderr or '')[-200:]}")
        return False
    return True


# ── 1. character-free plate, cut from the generated scene rather than fought for ──
# The sampler will not render an empty scene (12 seeds, 3 cycles, it drew a dog every
# time; FLUX.2 refuses negative prompts). Framing solves what prompting could not.
base = Image.open(WIP / "s4_scene_base.png").convert("RGB")
plate = base.crop((360, 0, base.width, base.height)).resize((832, 480), Image.LANCZOS)
plate.save(WIP / "s4_plate.png")
log(f"plate cut from the right of the base scene → {plate.size}, no animals in frame")

# ── 2. each character ALONE at full LoRA strength ──
parts = {
    "hank": dict(
        prompt=("hankbear a huge round brown bear with a light tan muzzle and a tan belly "
                "patch, standing in three-quarter view facing the camera, head turned and "
                "tilted up looking off to the right, full face and belly visible, mouth closed, Pixar 3D "
                "animated movie style, plain flat light grey background, full body"),
        loras=[HL], scales=[1.0], seed=6101),
    "doug": dict(
        prompt=("dougdog a tall lanky orange-tan bloodhound with very long heavy flat "
                "dark-brown floppy ears and droopy jowls, no collar, sitting in three-quarter "
                "view facing the camera, head turned and tilted up looking off to the right, "
                "full face and long ears visible, mouth closed, Pixar 3D animated movie style, plain flat light grey "
                "background, full body"),
        loras=[DL], scales=[1.0], seed=6203),
}
for name, spec in parts.items():
    out = WIP / f"s4_part_{name}.png"
    log(f"rendering {name} alone at LoRA 1.0")
    if not gen(spec["prompt"], spec["loras"], spec["scales"], spec["seed"], out):
        sys.exit(f"{name} part failed")

# ── 3. cut out and place on the plate ──
def cutout(p, target_h):
    im = remove(Image.open(p).convert("RGBA"))
    im = im.crop(im.getbbox())
    s = target_h / im.height
    return im.resize((int(im.width * s), target_h), Image.LANCZOS)

canvas = plate.convert("RGBA")
hank = cutout(WIP / "s4_part_hank.png", 300)
doug = cutout(WIP / "s4_part_doug.png", 215)
canvas.alpha_composite(hank, (60, 480 - 300 - 10))
canvas.alpha_composite(doug, (330, 480 - 215 - 5))
canvas.convert("RGB").save(WIP / "s4_rough.png")
log("rough composite written (hank left, doug centre, wide gap between them)")

# ── 4. gentle weld, both LoRAs, trigger words, low strength so the parts survive ──
WELD_PROMPT = ("hankbear a huge round brown bear with a light tan muzzle and tan belly "
               "patch stands beside dougdog a tall lanky orange-tan bloodhound with very "
               "long heavy dark-brown floppy ears and no collar, both in three-quarter view "
               "facing the camera and looking up off to the right at a weathered dark red "
               "circus freight train stopped on the "
               "tracks in blazing afternoon sun, sliding boxcar doors shut, heat shimmer, "
               "dust in the air, mouths closed, Pixar 3D animated movie style")
made = []
for strength in (0.30, 0.25, 0.35):
    for seed in (8801, 8807):
        out = WIP / f"s4_weld_{seed}_{int(strength * 100)}.png"
        log(f"weld strength={strength} seed={seed}")
        if gen(WELD_PROMPT, [HL, DL], [0.85, 1.0], seed, out, init=WIP / "s4_rough.png",
               strength=strength):
            made.append(str(out))
log(f"DONE — {len(made)} welds to judge:")
for m in made:
    log("  " + m)
