# Metal flash-attention for Wan — what we tried and what we learned

## TL;DR

We hand-wrote a Metal flash-attention kernel for Wan 2.2 14B i2v on Apple Silicon (M5 Max) via `torch.mps.compile_shader`. **It does not beat PyTorch's MPS SDPA at the shapes Wan operates on.**

Initial benchmarks claimed 12.32× speedup with PSNR 137 dB. That was wrong — measurement artifact from a dispatch bug. With the bug fixed, the kernel is 1.8-4× *slower* than vanilla MPS SDPA at our real workflow shapes (S=4096-7488 tokens). It only wins at extreme shapes (S > ~10000) where SDPA OOMs.

This directory is preserved as a public record of the attempt so the next person trying the same approach doesn't repeat the mistakes.

## ⚠️ CRITICAL: the monkeypatch is NOT safe even when "disabled" (2026-05-24)

`wan_metal_patch.install_wan_metal_attention()` replaces `WanSelfAttention.forward` wholesale. When `WAN_METAL_FUSED=0` it takes a "fallback" branch that calls plain `F.scaled_dot_product_attention` — **bypassing ComfyUI's native sub-quadratic / split attention dispatch.** At Wan's real i2v sequence length (S≈28350 for 832×480×81f) MPS SDPA materializes the full S×S×H score matrix and tries to allocate a **128 GB** MTLBuffer → `failed assertion ... Failed to allocate private MTLBuffer for size 128595600000` → `Abort trap: 6`. ComfyUI dies mid-render.

The flag only chooses fused-vs-fallback. **Both branches are broken**: fused = wrong output, fallback = OOM-abort. So merely setting `WAN_METAL_FUSED=0` does NOT make the patch safe — the patch must not be loaded at all.

**Production rule:** the ComfyUI custom-node shim must stay disabled. The live node lives at `~/AI/ComfyUI/custom_nodes/wan_metal_fused/` — it is renamed to `wan_metal_fused.disabled` so ComfyUI never imports it. With the node gone, ComfyUI logs `Using sub quadratic optimization for attention` and Wan renders fit in ~64 GB peak. Do NOT re-enable this node. The native bear-sister renders (pre-patch) prove native attention handles these shapes fine.

## What's in here

- `flash_attn_mps.py` — the kernel (fixed). MSL tiled fp16 flash-attention with online softmax. ~144 lines of MSL.
- `hello_metal.py` — proof that `torch.mps.compile_shader` works in PyTorch 2.12.
- `verify_flash_attn.py` — original standalone bench (the one that gave us the bogus 12.32×).
- `verify_flash_attn_7488.py` — corrected bench at real Wan shape.
- `sweep_lengths.py` — sweep across sequence lengths showing where the kernel wins (S > ~10k) vs loses (S < ~10k).
- `verify_integration.py` — integration test against `WanSelfAttention`.
- `metal_rmsnorm_linear.py` + `verify_rmsnorm_linear.py` — earlier RMSNorm+Linear fusion attempt that was 60× slower (vendor matmul too tuned to beat).
- `wan_metal_patch.py` — monkey-patch into `WanSelfAttention.forward`. Currently default-off via `WAN_METAL_FUSED=0`.

## The real bug

`torch.mps.compile_shader`'s `threads=` parameter is the TOTAL THREAD COUNT per dim, NOT the threadgroup count. We passed `threads=(n_q_blocks, bh, 1), group_size=(128, 1, 1)` thinking n_q_blocks was the number of threadgroups. PyTorch computed `threadgroups_per_grid = ceil(threads/group_size) = ceil(n_q_blocks/128)` so we dispatched only 1/128th of the work.

The bench at S=4096 *passed PSNR 137 dB* by sheer coincidence — the unused output rows received whatever was sitting in freed memory from the previous SDPA call, which was the correct reference output. Different timing = different memory state = different garbage. On real Wan renders the leftover memory contained saturated fp16 values, which decoded as brown noise frames.

Fix: `threads=(n_q_blocks * 128, bh, 1)`. Now all rows are computed correctly. Kernel matches `F.scaled_dot_product_attention` to within fp16 precision (PSNR 82+ dB). And is 2-4× slower than the reference because MPS SDPA is highly tuned.

## Why we kept the code

Three reasons this isn't deleted:
1. It documents the dispatch semantics gotcha for anyone trying `torch.mps.compile_shader` next.
2. The kernel is real and correct now — it could be useful for future architectures with sequence lengths past the MPS SDPA OOM ceiling (~10k).
3. The "always frame-QC before claiming a speedup" lesson — see [feedback memory](../../../../.claude/projects/-Users-dtribe/memory/feedback_qc_ai_videos_before_sending.md).

## What actually delivers Wan speedup on M5

- `lightx2v` 4-step LoRA (already in production, ~4× over base Wan)
- 2-step distillation LoRA (training overnight as of 2026-05-24 — perpetual ~2×)
- LTX 13B distilled 0.9.8 routing for B-roll scenes (~5× per scene)
- Smaller frame sizes / shorter clips where appropriate

Metal flash-attn is NOT on this list. Save the optimization budget for ops that don't already have a tuned vendor kernel.
