"""verify_integration.py — full end-to-end correctness test of the patched
WanSelfAttention.forward against the original.

This loads a real WanSelfAttention module (with random weights), runs both the
original forward and the patched forward on the same input, and compares the
output. PSNR >= 35 dB means the integration is correct.
"""
import math
import sys
import time
from pathlib import Path

import torch
import torch.nn.functional as F

# Set up paths
COMFY = Path("/Users/dtribe/Desktop/PROJECTS/AI/ComfyUI")
sys.path.insert(0, str(COMFY))
sys.path.insert(0, "/Users/dtribe/Desktop/PROJECTS/AI/videopipe/metal")

import comfy.ops  # noqa: E402
from comfy.ldm.wan.model import WanSelfAttention  # noqa: E402
import wan_metal_patch  # noqa: E402

# Force flag ON for this test
import os
os.environ["WAN_METAL_FUSED"] = "1"


def psnr(ref, test):
    diff = (test.float() - ref.float())
    mse = (diff * diff).mean().item()
    if mse == 0.0:
        return float("inf")
    peak = max(ref.abs().max().item(), 1e-6)
    return 20.0 * math.log10(peak) - 10.0 * math.log10(mse)


def main():
    # Wan 2.2 14B: dim=5120, num_heads=40, head_dim=128
    B, S = 1, 7488
    dim, n_heads, head_dim = 5120, 40, 128

    ops = comfy.ops.manual_cast
    op_settings = {"operations": ops, "device": "mps", "dtype": torch.float16}

    torch.manual_seed(0xBEEF)
    attn = WanSelfAttention(
        dim=dim, num_heads=n_heads, qk_norm=True, eps=1e-6,
        operation_settings=op_settings,
    )
    # Realize manual_cast weights
    for p in attn.parameters():
        p.data = torch.randn_like(p.data).half().to("mps") * 0.02
    attn = attn.to("mps").half()

    # Random input shaped as Wan expects: [B, S, dim]
    x = torch.randn(B, S, dim, dtype=torch.float16, device="mps") * 0.5

    # Build freqs (RoPE) — shape (1, S, head_dim/2, 2, 2) per apply_rope1
    # Easier: use the model's own rope encoder.
    from comfy.ldm.flux.layers import EmbedND
    d = head_dim
    embed = EmbedND(dim=d, theta=10000.0,
                    axes_dim=[d - 4 * (d // 6), 2 * (d // 6), 2 * (d // 6)])
    # Fake img_ids: just 1D sweep
    img_ids = torch.zeros(1, S, 3, device="mps", dtype=torch.float32)
    img_ids[..., 0] = torch.arange(S, device="mps", dtype=torch.float32).unsqueeze(0)
    freqs = embed(img_ids).movedim(1, 2)

    # First: vanilla path (uninstall patch).
    wan_metal_patch.uninstall_wan_metal_attention()
    torch.mps.synchronize()
    t0 = time.perf_counter()
    out_ref = attn(x, freqs)
    torch.mps.synchronize()
    t_ref = time.perf_counter() - t0

    # Reinstall and run fused.
    wan_metal_patch.install_wan_metal_attention()
    # Ensure flag is on for this call
    os.environ["WAN_METAL_FUSED"] = "1"
    Path("/tmp/wan_metal_fused.flag").write_text("1")
    torch.mps.synchronize()
    t0 = time.perf_counter()
    out_fused = attn(x, freqs)
    torch.mps.synchronize()
    t_fused = time.perf_counter() - t0

    # Compare
    db = psnr(out_ref, out_fused)
    max_abs = (out_fused.float() - out_ref.float()).abs().max().item()
    print(f"Shape: x={tuple(x.shape)} dtype={x.dtype}")
    print(f"out_ref   stats: min={out_ref.float().min().item():.4f} max={out_ref.float().max().item():.4f}")
    print(f"out_fused stats: min={out_fused.float().min().item():.4f} max={out_fused.float().max().item():.4f}")
    print(f"max_abs_diff = {max_abs:.4e}")
    print(f"PSNR         = {db:.2f} dB   (gate >= 35)")
    print(f"ref   wall   = {t_ref*1000:.1f} ms")
    print(f"fused wall   = {t_fused*1000:.1f} ms")
    return 0 if db >= 35 else 1


if __name__ == "__main__":
    raise SystemExit(main())
