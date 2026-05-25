# One-step distillation of Wan 2.2 i2v on Apple Silicon

> Goal: make a Wan 2.2 image-to-video student render a clip in **one** denoising step
> that matches what the model normally needs **four** steps to produce — fully local,
> on a single M5 Max (128 GB), no cloud.

The off-the-shelf 4-step accelerator (lightx2v) **degrades noticeably at 1 step** — at 192×192
its single-step output scores **LPIPS 0.206** against the 4-step reference (we originally carried
a 1.09 figure from a harsher/higher-resolution setup; measuring it at our own resolution is part
of the point). We wanted to know if a small trained adapter could close that gap, and forge our
own objective to do it rather than reaching for someone else's recipe.

## The objective we forged

We train a rank-32 LoRA on top of Wan 2.2 i2v 14B + the lightx2v LoRA, with a two-term loss:

1. **Teacher-anchor** — the student's *single* denoising step should land on the latent the
   4-step teacher produces from the same noise. `MSE(student_1step, teacher_4step)`.
2. **Self-consistency** — the student's 1-step prediction, when re-noised to a lighter noise
   level and stepped again, should agree with itself. This is the consistency-model idea,
   implemented directly on MPS. `MSE(one_step_from(student.detach()), student.detach())`.

Backprop updates only the LoRA adapters. Everything runs in-process through ComfyUI's own
modules (no HTTP queue) — the genuinely hard part was making Wan's sampler differentiable on
MPS (ComfyUI's k-diffusion samplers are `@torch.no_grad`; we drive a differentiable euler
through `CFGGuider` under `enable_grad`).

## Setup

- **Hardware:** M5 Max, 128 GB unified memory, MPS.
- **Model:** Wan 2.2 i2v high-noise 14B (fp16) + lightx2v 4-step LoRA, Wan 2.1 VAE, umt5-xxl fp16.
- **Training:** rank-32 LoRA, 150 steps, 192×192×17 frames, consistency every step, ~20 s/step (~51 min total).
- **Eval:** per-frame LPIPS of the student's 1-step render vs the 4-step teacher, same still/prompt/seed.
  We measure the **real wall at the same resolution** (raw lightx2v 1-step vs 4-step teacher),
  rather than comparing to a literature number measured at a different resolution.

## Results

11 prompts per checkpoint, scored as per-frame LPIPS (1-step student vs 4-step teacher, same
still/prompt/seed). The wall is measured at the same 192×192 resolution.

| checkpoint | LPIPS (↓ better) | beats wall? |
|---|---|---|
| raw lightx2v 1-step (**the wall**) | **0.2056** | — |
| student step 25 | 0.1291 | ✅ |
| student step 50 | 0.1178 | ✅ |
| student step 75 | 0.1098 | ✅ |
| student step 100 | 0.1151 | ✅ |
| student step 125 | 0.1145 | ✅ |
| **student step 150 (best)** | **0.0823** | ✅ |

Every checkpoint beats the raw 1-step baseline; at 150 steps the best cuts the perceptual gap to
**~40% of it** (0.082 vs 0.206) — a ~2.5× improvement. The single denoising step now lands much
closer to the four-step teacher. Note the latent-MSE training loss fell monotonically, but LPIPS
bottomed in a noisy ~0.11 band through step 125 before step 150 broke lower.

### Does more training help? (300-step extension)

A second run to 300 steps (same config) tested whether step 150 was the ceiling. It wasn't —
LPIPS kept dropping into new territory (8-sample eval, same-res wall = 0.218):

| step | 150 | 200 | 250 | 300 |
|---|---|---|---|---|
| LPIPS | 0.070 | 0.061 | 0.054 | **0.052** |

(Step-150 reads 0.070 here vs 0.082 at 11 samples — sample-count variance; the trend within one
eval is what matters.) **New best: step 300 @ 0.052** — ~37% below the 150-step result and
**~4.2× under the 0.218 wall**. The descent flattens at the end (250→300 is only −0.0014), so
~300 steps is near the practical floor for this config — a 400-step run likely wouldn't pay off.

## Honest learnings (the stuff that bit us)

1. **Resolution is the memory lever, not rank.** At 256×256 the consistency term holds two
   autograd graphs through the 14B at once; the peak sat right at the 128 GB edge, so macOS
   compressed ~40 GB / swapped ~28 GB and random steps ballooned from 5 min to 30–40 min
   (~28 h projected for the run). Dropping to 192×192 (~0.56× activations) gave 95 % free RAM,
   ~0 swap, and ~20 s/step — a ~16× speedup just from removing the memory tax.

2. **A "clever" memory optimization silently broke the objective.** We tried backwarding the
   two loss terms separately (to halve peak memory). But the two forwards share upstream saved
   tensors, so the second backward threw *"backward through the graph a second time"* — and the
   `try/except` swallowed it, silently disabling consistency (`cons=0.0`). A verify monitor
   caught it on step 1. Reverted to a single combined `loss.backward()`. **Lesson: after any
   backward change, confirm the term you care about is still nonzero.**

3. **The training proxy is not the metric.** Latent MSE kept dropping monotonically, but
   perceptual LPIPS did *not* track it past the early checkpoints — it bottomed and then bounced
   in a noisy band. So the last checkpoint is not automatically the best. **We evaluate every
   checkpoint's real LPIPS, not just the final weights.**

## Reproduce

```bash
# train
python wan_distill_v3.py --dataset dataset.example.json \
    --out-dir checkpoints_v3 --steps 150 --save-every 25
# evaluate every checkpoint (renders 1-step vs 4-step, scores LPIPS, measures the real wall)
python eval_checkpoint.py --ckpt-dir checkpoints_v3 --n-samples 11 --md-out RESULTS.md
```

## Caveats

- Trained and evaluated at 192×192×17; generalization to production resolution is untested.
- LPIPS is measured against this model's own 4-step teacher (a faithfulness metric), not against
  ground-truth video.
- Eval is on a small still/prompt set; numbers carry sampling noise (which is why we report all
  checkpoints and the same-resolution wall).
