"""wan_metal_patch.py — monkey-patch Wan 2.2 self-attention to use the fused
Metal flash-attention kernel at videopipe/metal/flash_attn_mps.py.

Activation:
    Set env var WAN_METAL_FUSED=1 (or touch /tmp/wan_metal_fused.flag)
    BEFORE invoking a Wan render. The patch reads the flag on every call,
    so you can flip it without restarting ComfyUI.

Install side:
    from wan_metal_patch import install_wan_metal_attention
    install_wan_metal_attention()

The patch replaces comfy.ldm.wan.model.WanSelfAttention.forward with a
shim that:
  1. Runs the same Q/K/V linear + RMSNorm + RoPE as the original.
  2. Reshapes to (B, H, S, D).
  3. If our kernel's shape contract is satisfied (head_dim=128, fp16,
     S >= 1024 so the fused win materializes), calls flash_attn_fwd.
  4. Otherwise falls back to F.scaled_dot_product_attention (the same path
     ComfyUI's optimized_attention would take on MPS).
  5. Reshapes back to (B, S, H*D) and applies the output projection.

Dispatch logging is one-shot per (B, H, S, D) tuple so we don't spam.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import torch
import torch.nn.functional as F

# Make our metal module importable regardless of how this is loaded.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from flash_attn_mps import flash_attn_fwd  # noqa: E402


_FLAG_FILE = Path("/tmp/wan_metal_fused.flag")
_seen_shapes: set[tuple] = set()
_installed = False
_original_forward = None
_stats = {
    "fused_calls": 0,
    "fallback_calls": 0,
    "fused_time": 0.0,
    "fallback_time": 0.0,
}


def _fused_enabled() -> bool:
    """Re-check the flag on every call so you can toggle live."""
    if os.environ.get("WAN_METAL_FUSED", "0") == "1":
        return True
    if _FLAG_FILE.exists():
        try:
            return _FLAG_FILE.read_text().strip() == "1"
        except OSError:
            return False
    return False


def _log_once(B: int, H: int, S: int, D: int, mode: str):
    key = (B, H, S, D, mode)
    if key not in _seen_shapes:
        _seen_shapes.add(key)
        print(f"[wan-metal] dispatch {mode} B={B} H={H} seq={S} D={D}",
              flush=True)


def _wan_self_attn_forward_patched(self, x, freqs, transformer_options=None):
    """Drop-in replacement for WanSelfAttention.forward.

    Mirrors the original signature exactly. Original implementation:
        b, s, n, d = *x.shape[:2], self.num_heads, self.head_dim
        q = apply_rope1(norm_q(self.q(x)).view(b,s,n,d), freqs)
        k = apply_rope1(norm_k(self.k(x)).view(b,s,n,d), freqs)
        x = optimized_attention(q.view(b,s,n*d), k.view(b,s,n*d),
                                self.v(x).view(b,s,n*d), heads=n, ...)
        x = self.o(x)
    """
    from comfy.ldm.flux.math import apply_rope1
    transformer_options = transformer_options or {}
    patches = transformer_options.get("patches", {})

    b, s, n, d = *x.shape[:2], self.num_heads, self.head_dim

    # Q/K/V projections + RMSNorm + RoPE (same as original).
    q = self.norm_q(self.q(x)).view(b, s, n, d)
    q = apply_rope1(q, freqs)
    k = self.norm_k(self.k(x)).view(b, s, n, d)
    k = apply_rope1(k, freqs)
    v = self.v(x).view(b, s, n, d)

    # Decide dispatch.
    use_fused = (
        _fused_enabled()
        and q.device.type == "mps"
        and q.dtype == torch.float16
        and d == 128
        and s >= 1024
    )

    if use_fused:
        # Reshape to (B, H, S, D) for the kernel.
        q_bhsd = q.permute(0, 2, 1, 3).contiguous()
        k_bhsd = k.permute(0, 2, 1, 3).contiguous()
        v_bhsd = v.permute(0, 2, 1, 3).contiguous()
        _log_once(b, n, s, d, "fused")
        torch.mps.synchronize()
        t0 = time.perf_counter()
        out_bhsd = flash_attn_fwd(q_bhsd, k_bhsd, v_bhsd)
        torch.mps.synchronize()
        _stats["fused_time"] += time.perf_counter() - t0
        _stats["fused_calls"] += 1
        # Back to (B, S, H*D)
        x_out = out_bhsd.permute(0, 2, 1, 3).reshape(b, s, n * d)
    else:
        # Fallback: PyTorch SDPA on (B, H, S, D).
        q_bhsd = q.permute(0, 2, 1, 3)
        k_bhsd = k.permute(0, 2, 1, 3)
        v_bhsd = v.permute(0, 2, 1, 3)
        _log_once(b, n, s, d, "fallback")
        torch.mps.synchronize()
        t0 = time.perf_counter()
        out_bhsd = F.scaled_dot_product_attention(
            q_bhsd, k_bhsd, v_bhsd, is_causal=False, scale=d ** -0.5,
        )
        torch.mps.synchronize()
        _stats["fallback_time"] += time.perf_counter() - t0
        _stats["fallback_calls"] += 1
        x_out = out_bhsd.permute(0, 2, 1, 3).reshape(b, s, n * d)

    # attn1_patch hook for ControlNet etc.
    if "attn1_patch" in patches:
        for p in patches["attn1_patch"]:
            x_out = p({
                "x": x_out,
                "q": q.view(b, s, n * d),
                "k": k.view(b, s, n * d),
                "transformer_options": transformer_options,
            })

    return self.o(x_out)


def install_wan_metal_attention() -> bool:
    """Monkey-patch WanSelfAttention.forward. Idempotent.

    Returns True on success, False if Wan model module isn't importable.
    """
    global _installed, _original_forward
    if _installed:
        return True
    try:
        from comfy.ldm.wan import model as wan_model
    except ImportError as e:
        print(f"[wan-metal] install failed (no comfy.ldm.wan): {e}", flush=True)
        return False

    _original_forward = wan_model.WanSelfAttention.forward
    wan_model.WanSelfAttention.forward = _wan_self_attn_forward_patched
    _installed = True
    print("[wan-metal] WanSelfAttention.forward patched "
          "(WAN_METAL_FUSED env or /tmp/wan_metal_fused.flag controls dispatch)",
          flush=True)
    return True


def uninstall_wan_metal_attention():
    """Restore original forward."""
    global _installed, _original_forward
    if not _installed:
        return
    from comfy.ldm.wan import model as wan_model
    wan_model.WanSelfAttention.forward = _original_forward
    _installed = False
    _original_forward = None


def get_stats() -> dict:
    """Snapshot of fused vs fallback call counts + time."""
    return dict(_stats)


def reset_stats():
    for k in _stats:
        _stats[k] = 0 if isinstance(_stats[k], int) else 0.0
    _seen_shapes.clear()
