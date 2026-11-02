# Story Forge video model, 2026-11-01

**Decision (Matt, 4:02 PM, after watching the K6 smoke clip: "That's the best I've ever seen"):**
**Kandinsky 6.0 Pro is the default scene video model.** `bin/make-k6` is forge-shot's default engine (`"engine": "k6"`),
and `pipeline/04_shots/CONTEXT.md` names it for the quality pass. LTX-2.5 stays only as the fast previs drafter
and for a2v lip-sync close-ups. Wan-Animate-2 is the acting/close-up candidate and is not proven yet.

How we got here: `MODEL-CONSENSUS-2026-11.md` ranked MiniMax H3 #1 for local video, but its license bans all use
(and its outputs) in the US, and Matt cancelled the paid H3 routes. The next model on the list, Kandinsky 6 Pro, is
MIT. Wan 2.2 i2v and HunyuanVideo 1.5 were half-downloaded as fallbacks, then deleted once K6 ran.

## Results on the M5 Max (128 GB)

| Model | License (US commercial) | Precision | Test | Wall time | Peak memory | What the clip looks like |
|---|---|---|---|---|---|---|
| **Kandinsky 6.0 Pro distill** (29B), `kandinskylab/Kandinsky-6.0-Pro-distill-5s-Diffusers` | **MIT**, no revenue line | bf16 | i2v, wagon burst shot, 832x480, 73 frames (3 s), 10 steps, seed 11 | **718 s a clip** (encode 6 s, load 40 s, denoise 635 s, decode ~36 s) | **68.7 GB** Metal (82.9 GB before the decode fix) | Clean and coherent: the whole team (2 horses, 2 camels, 2 cows) gallops with readable legs, the wooden wheels roll, dust trails, the camera tracks back. Hank and Doug stay on model the whole way. No morphing or smear. Matt: "the best I've ever seen." |
| **Wan-Animate-2 distill** (14B), `Wan-AI/Wan2.2-Animate-2-14B-Distilled-Diffusers` | **Apache-2.0** | bf16 | performance transfer: Doug close-up still + a 3 s talking-human driver (LTX-2.5 a2v made from the Doug voice wav) | **no clip yet** | 91 GB (base + CFG), 78 GB (distill, double load) | Not rendered. See the next section. |
| LTX-2.5 (22B, current) | LTX community license, free under **$10M** revenue | bf16 | from earlier runs: `--hq` ~9-10 min a 3.5 s take; distilled previs ~70-106 s a clip | — | 81 GB full, ~20 GB `--low-ram` | Kept as the previs drafter and a2v engine only (r/StableDiffusion: "hallucinates too much"). The revenue line is worth a look before anything ships commercially. |

## Wan-Animate-2: three runs, three blockers (each one fixed, no clip yet)

1. **Base checkpoint (40 steps, CFG 3.0):** diffusers' WA2 doesn't run on MPS as shipped. The flex-attention
   BlockMask needs torch.compile, and RoPE uses float64. Both are replaced in `tools/wan_animate2_mps.py` with the
   same math (verified to 2e-7). It then ran, but held 91 GB with UMT5 resident plus the ~27 GB reference KV cache.
   forge_guard paused it for swapping after 25 minutes, and the session restart killed it.
2. **Distilled (10 steps, no CFG), UMT5 dropped after encoding:** loading all components to the CPU and then
   moving them to MPS held two copies of the transformer (78 GB), so forge_guard SIGTERMed it at 2 minutes.
3. **Distilled, staged load with `device_map="mps"`:** stalled 10 minutes in `torch.mps.empty_cache()` waiting on a
   Metal command buffer (0% CPU). I killed it so the GPU could go to Last Signal.

Next attempt (one run, about 10-15 min expected): load each component on the plain CPU path one at a time, move it
to MPS, free the CPU copy, and skip `empty_cache` between loads. The driver clip, the Doug still and the distilled
weights are all on disk. Until it produces a clip, dialogue close-ups stay on LTX-2.5 a2v.

## What changed in the code

- `bin/make-k6` (new): the K6 CLI, same shape as make-ltx25 (`--i2v --res --duration --seed --label --static --keep-audio`). It waits for Song Forge, passes mem-gate, takes a forge_guard lease `k6-<label>` (72 GB), loads in stages (text encoder → free → transformer → free → VAE decode), and prints `done in Ns → path`.
- `bin/forge-shot`: default engine `k6`. K6 skips the ComfyUI bounce and the 46 GB storyforge-animate lease, since it takes its own lease.
- `bin/make-wa2` + `tools/wan_animate2_mps.py` (new): Wan-Animate-2 on MPS. Test engine, not a default.
- `SongForgeM5/forge_guard.py`, `Scripts/render_sentry.py`: `make-k6` / `make-wa2` registered (process family, lease label, over-budget-OK on measured headroom, sentry pause and lease reaper). Backups are in `/tmp/*.bak-20261101`.
- `projects/last_signal/tools/zimage_batch.py`: fixed an infinite self-re-exec. `~/AI` is a symlink, so the venv path compare never matched; it now compares `.resolve()` on both sides. Its Krea verify job had been spinning for 17 minutes, and I killed it.
- Krea 2 venv (`~/AI/krea2/venv`): added torchvision, imageio and imageio-ffmpeg (K6's Qwen2.5-VL processor and WA2's video loader need them).

## On disk now

- Kandinsky 6 Pro distill: 80.6 GB. Wan-Animate-2 distill: 45.9 GB. LTX-2.5: 119.7 GB.
- Deleted: Wan 2.2 i2v and HunyuanVideo 1.5 (partial, 32 GB), Wan-Animate-2 base (32.8 GB), two empty Wan/Hunyuan cache stubs, and the declined Krea stills.
- Proof clip: `~/AI/videopipe/outputs/k6smoke2_20261101_141520_k6.mp4`. Start frames are in `~/AI/videomodel-2026-11/frames/`.
