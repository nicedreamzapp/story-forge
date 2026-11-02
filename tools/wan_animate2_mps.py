"""wan_animate2_mps — run diffusers' Wan-Animate-2 on Apple Silicon (MPS) without flex attention.

Added 2026-11-01 (video bake-off). diffusers 0.42's WanAnimate2 generation self-attention is a flex `BlockMask`
over a packed [generation | reference] buffer and "needs torch.compile"; uncompiled flex materializes the full
attention matrix, and create_block_mask(_compile=True) / inductor flex is not a path we trust on MPS.

The mask itself is simple (transformer_wan_animate_2.create_mask):
  a query in generation frame q (q < F+1, where F = origin latent frames) attends
    * every generation key with index < (F+1)*hw   (the "base" part), plus
    * the reference keys of reference frame q-1    (rel index in [(q-1)*hw, q*hw), valid while < F*hw).
So we compute exactly that with plain SDPA, one query frame at a time (and a few heads at a time to keep the
score matrix ~1 GB). Same math, no flex, no compile.

Usage: import this module BEFORE building the pipeline; it patches the transformer module in place.
"""
from __future__ import annotations

import math

import torch
import torch.nn.functional as F

import diffusers.models.transformers.transformer_wan_animate_2 as wa2
from diffusers.models.attention_dispatch import AttentionBackendName

_orig_dispatch = wa2.dispatch_attention_fn
HEAD_CHUNK = 8


class FrameMask:
    """Stands in for the flex BlockMask: just the geometry create_mask was built from."""

    def __init__(self, origin_latent_f: int, hw: int):
        self.F, self.hw = origin_latent_f, hw
        self.q_limit = (origin_latent_f + 1) * hw
        self.k_limit = origin_latent_f * hw
        self.q_total = math.ceil(self.q_limit / 128) * 128


def _create_mask(self, origin_latent_f, hw, device):
    return FrameMask(origin_latent_f, hw)


def _frame_attention(q, k, v, m: FrameMask):
    """q: [B, Lq_packed, H, D]; k, v: [B, q_total + ref_packed, H, D] (diffusers layout). Returns q-shaped output."""
    B, Lq, H, D = q.shape
    out = q.new_zeros(B, Lq, H, D)
    hw = m.hw
    base_k = k[:, : m.q_limit]
    base_v = v[:, : m.q_limit]
    n_frames = min(m.F + 1, math.ceil(min(Lq, m.q_limit) / hw))
    for f in range(n_frames):
        q0, q1 = f * hw, min((f + 1) * hw, m.q_limit, Lq)
        if q0 >= q1:
            break
        kk, vv = base_k, base_v
        if f >= 1:
            r0 = (f - 1) * hw
            r1 = min(f * hw, m.k_limit)
            if r0 < r1:
                kk = torch.cat([base_k, k[:, m.q_total + r0: m.q_total + r1]], dim=1)
                vv = torch.cat([base_v, v[:, m.q_total + r0: m.q_total + r1]], dim=1)
        qf = q[:, q0:q1]
        for h0 in range(0, H, HEAD_CHUNK):
            h1 = min(h0 + HEAD_CHUNK, H)
            o = F.scaled_dot_product_attention(
                qf[:, :, h0:h1].transpose(1, 2), kk[:, :, h0:h1].transpose(1, 2), vv[:, :, h0:h1].transpose(1, 2))
            out[:, q0:q1, h0:h1] = o.transpose(1, 2)
    return out


def _dispatch(query, key, value, attn_mask=None, *args, backend=None, **kw):
    if backend == AttentionBackendName.FLEX and isinstance(attn_mask, FrameMask):
        return _frame_attention(query, key, value, attn_mask)
    return _orig_dispatch(query, key, value, attn_mask, *args, backend=backend, **kw)


def _rope_params(max_seq_len, dim, theta=10000, offset=0):
    """MPS has no float64/complex128: angles are still computed in float64 on the CPU, then stored as a real
    float32 (cos, sin) pair of shape [L, dim/2, 2] instead of a complex128 table."""
    assert dim % 2 == 0
    ang = torch.outer(torch.arange(max_seq_len, dtype=torch.float64) + offset,
                      1.0 / torch.pow(theta, torch.arange(0, dim, 2).to(torch.float64).div(dim)))
    return torch.stack([ang.cos(), ang.sin()], dim=-1).float()


def _rope_apply(x, grid_sizes, freqs, time_stride=1):
    """Same rotation as diffusers' rope_apply, in float32 real arithmetic over the (cos, sin) table above."""
    n, c = x.size(2), x.size(3) // 2
    c0, c1 = c - 2 * (c // 3), c // 3
    p0, p1, p2 = freqs.split([c0, c1, c1], dim=1)
    output = []
    for i, (f, h, w) in enumerate(grid_sizes.tolist()):
        seq_len = f * h * w
        fr = torch.cat([
            p0[: f * time_stride: time_stride].view(f, 1, 1, c0, 2).expand(f, h, w, c0, 2),
            p1[:h].view(1, h, 1, c1, 2).expand(f, h, w, c1, 2),
            p2[:w].view(1, 1, w, c1, 2).expand(f, h, w, c1, 2),
        ], dim=3).reshape(seq_len, 1, c, 2)
        xr = x[i, :seq_len].float().reshape(seq_len, n, c, 2)
        a, b = xr[..., 0], xr[..., 1]
        cos, sin = fr[..., 0], fr[..., 1]
        rot = torch.stack([a * cos - b * sin, a * sin + b * cos], dim=-1).flatten(2)
        output.append(torch.cat([rot, x[i, seq_len:].float()]))
    return torch.stack(output).float()


def install():
    wa2.dispatch_attention_fn = _dispatch
    wa2.WanAnimate2Transformer3DModel.create_mask = _create_mask
    wa2.rope_params = _rope_params
    wa2.rope_apply = _rope_apply
    return True


install()
