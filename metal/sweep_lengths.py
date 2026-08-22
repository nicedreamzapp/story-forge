"""sweep_lengths.py — find where the kernel goes wrong by sweeping S."""
import math
import torch
import torch.nn.functional as F
from flash_attn_mps import flash_attn_fwd

B, H, D = 1, 40, 128
SCALE = D ** -0.5

def psnr(ref, test):
    diff = (test.float() - ref.float())
    mse = (diff * diff).mean().item()
    if mse == 0.0: return float("inf")
    peak = max(ref.abs().max().item(), 1e-6)
    return 20.0 * math.log10(peak) - 10.0 * math.log10(mse)

# Try a few S values that hit edges of the per-block math
for S in [2048, 4096, 4128, 5120, 6144, 7168, 7488, 8192]:
    g = torch.Generator(device="mps").manual_seed(0xBEEF)
    q = torch.randn((B, H, S, D), dtype=torch.float16, device="mps", generator=g)
    k = torch.randn((B, H, S, D), dtype=torch.float16, device="mps", generator=g)
    v = torch.randn((B, H, S, D), dtype=torch.float16, device="mps", generator=g)
    ref = F.scaled_dot_product_attention(q, k, v, is_causal=False, scale=SCALE)
    fused = flash_attn_fwd(q, k, v)
    torch.mps.synchronize()
    db = psnr(ref, fused)
    n_kv = (S + 32 - 1) // 32
    print(f"S={S:>5d}  n_kv_blocks={n_kv:>4d}  PSNR={db:6.2f} dB"
          f"  fused_max={fused.float().abs().max().item():.3f}"
          f"  ref_max={ref.float().abs().max().item():.3f}")
