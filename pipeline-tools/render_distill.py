#!/usr/bin/env python3
"""render_distill.py — render a clip with the 1-step distilled student.

Reuses wan_distill_v3 + eval_checkpoint's PROVEN single-stage loaders/sampler
(the same path that scored LPIPS 0.052), so output matches the eval — unlike
make-video's dual-stage MoE path, which collapses to gray at 1 step.

  pipeline = Wan high-noise + lightx2v + student LoRA, KSampler 1 step (denoise=1)
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path.home() / "AI/distill"))
import wan_distill_v3 as W                # noqa: E402
import comfy.model_management as mm       # noqa: E402
mm.in_training = False
import eval_checkpoint as E               # noqa: E402  (decode_to_frames, load_ckpt_into_student)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--still", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--ckpt", default=str(Path.home() / "AI/distill/checkpoints_v3_300/student_step_0300.safetensors"))
    ap.add_argument("--out", default="/tmp/distill_clip.mp4")
    ap.add_argument("--width", type=int, default=256)
    ap.add_argument("--height", type=int, default=256)
    ap.add_argument("--length", type=int, default=17)
    ap.add_argument("--fps", type=int, default=16)
    ap.add_argument("--cfg", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--rank", type=int, default=32)
    ap.add_argument("--sampler", default="euler")
    ap.add_argument("--scheduler", default="simple")
    ap.add_argument("--student-steps", dest="student_steps", type=int, default=1)
    ap.add_argument("--negative", default="")
    # build_pipeline expects these (mirror eval_checkpoint's parser exactly):
    ap.add_argument("--wan-unet", dest="wan_unet", default=W.DEFAULT_WAN_UNET)
    ap.add_argument("--lightx2v-lora", dest="lightx2v_lora", default=W.DEFAULT_LIGHTX2V_LORA)
    ap.add_argument("--vae", default=W.DEFAULT_VAE)
    ap.add_argument("--text-encoder", dest="text_encoder", default=W.DEFAULT_TEXT_ENCODER)
    ap.add_argument("--teacher-steps", dest="teacher_steps", type=int, default=4)
    args = ap.parse_args()

    t0 = time.time()
    print(f"[render_distill] building pipeline @ {args.width}x{args.height} len={args.length} ...")
    model_t, model_s, clip, vae = W.build_pipeline(args)
    peft_wan = W.inject_peft_lora(model_s, args.rank)
    E.load_ckpt_into_student(peft_wan, args.ckpt)

    still = W.load_still_as_tensor(args.still, args.width, args.height)
    pos = W.encode_prompt(clip, args.prompt)
    neg = W.encode_prompt(clip, args.negative)
    pos_t, neg_t, latent = W.prepare_wan_inputs(pos, neg, vae, still, args.width, args.height, args.length)

    peft_wan.enable_adapter_layers()  # student LoRA ON
    with torch.no_grad():
        lat = W.sample_latent(model_s, pos_t, neg_t, latent,
                              args.student_steps, args.cfg,
                              args.sampler, args.scheduler, args.seed)
    frames = E.decode_to_frames(vae, lat)  # [N,3,H,W] in [0,1]

    from PIL import Image
    outdir = Path("/tmp/distill_frames")
    outdir.mkdir(exist_ok=True)
    for f in outdir.glob("*.png"):
        f.unlink()
    arr = (frames.detach().permute(0, 2, 3, 1).float().cpu().numpy() * 255).clip(0, 255).astype("uint8")
    for i, im in enumerate(arr):
        Image.fromarray(im).save(outdir / f"f_{i:03d}.png")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(args.fps),
                    "-i", str(outdir / "f_%03d.png"), "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "18", args.out], check=True)
    print(f"[render_distill] {len(arr)} frames @ {args.width}x{args.height} -> {args.out} in {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
