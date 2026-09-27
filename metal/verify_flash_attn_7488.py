"""verify_flash_attn_7488.py — same as verify_flash_attn.py but at the REAL
Wan i2v shape (1, 40, 7488, 128) used by the production workflow."""
import math
import time

import torch
import torch.nn.functional as F

from flash_attn_mps import flash_attn_fwd

assert torch.backends.mps.is_available()

B, H, S, D = 1, 40, 7488, 128
SCALE = D ** -0.5


def psnr(ref, test):
    diff = (test.float() - ref.float())
    mse = (diff * diff).mean().item()
    if mse == 0.0:
        return float("inf")
    peak = max(ref.abs().max().item(), 1e-6)
    return 20.0 * math.log10(peak) - 10.0 * math.log10(mse)


def main():
    g = torch.Generator(device="mps").manual_seed(0xBEEF)
    q = torch.randn((B, H, S, D), dtype=torch.float16, device="mps", generator=g)
    k = torch.randn((B, H, S, D), dtype=torch.float16, device="mps", generator=g)
    v = torch.randn((B, H, S, D), dtype=torch.float16, device="mps", generator=g)
    print(f"Shape: Q,K,V = {tuple(q.shape)} {q.dtype}  scale={SCALE:.5f}")

    torch.mps.synchronize()
    t0 = time.perf_counter()
    ref = F.scaled_dot_product_attention(q, k, v, is_causal=False, scale=SCALE)
    torch.mps.synchronize()
    ref_t = time.perf_counter() - t0

    torch.mps.synchronize()
    t0 = time.perf_counter()
    fused = flash_attn_fwd(q, k, v)
    torch.mps.synchronize()
    fused_t = time.perf_counter() - t0

    max_abs = (fused.float() - ref.float()).abs().max().item()
    db = psnr(ref, fused)
    print(f"max_abs_diff = {max_abs:.4e}")
    print(f"PSNR         = {db:.2f} dB   (gate >= 35)")
    print(f"fused wall   = {fused_t*1000:.1f} ms")
    print(f"ref   wall   = {ref_t*1000:.1f} ms")
    has_nan = torch.isnan(fused).any().item()
    has_inf = torch.isinf(fused).any().item()
    print(f"fused has NaN/Inf: nan={has_nan} inf={has_inf}")
    print(f"fused stats: min={fused.float().min().item():.3f} max={fused.float().max().item():.3f} mean={fused.float().mean().item():.4f}")
    print(f"ref   stats: min={ref.float().min().item():.3f} max={ref.float().max().item():.3f} mean={ref.float().mean().item():.4f}")
    return 0 if db >= 35 else 1


if __name__ == "__main__":
    raise SystemExit(main())
