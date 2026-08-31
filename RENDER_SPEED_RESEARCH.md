# Render speed & quality research — candidates, ranked by measured payoff

**Written 2026-07-26 from the first instrumented run of `bin/forge-shot`.** Every number
in the "measured now" column came off this machine tonight (M5 Max 128GB, Song Forge
resident, `METRICS.jsonl`), not from a vendor claim.

Nothing here ships on a hunch. Every candidate has to clear
[`bin/measure-render`](bin/measure-render): **per-frame LPIPS < 0.05 AND speedup > 1.10×**.
That gate is why a hand-written Metal flash-attention kernel lives in [`metal/`](metal/) as
a documented null result instead of quietly degrading renders.

## Where the time actually goes (measured, 2026-07-26)

| Step | Measured now | Share of a shot |
|---|---|---|
| Still roll (mflux Flux2-klein 9B 8-bit, 24 steps, 832×480, + LoRAs) | 50–90 s | ~5% |
| Beat gate on a still (3 ballots, Qwen3-VL-32B 4-bit in-process) | 35–50 s | ~4% |
| **i2v animation (Wan 2.2 Q6_K GGUF, 81 frames @ 832×480, 2 steps)** | **~1010 s** | **~85%** |
| Clip judging (5 ballots + up to 5 window probes) | 60–120 s | ~6% |
| ComfyUI bounces forced by the memory gate | ~90 s each, **6+ per hour tonight** | ~15% of wall clock |

Two things fall straight out of this. Animation is the only step worth optimising for raw
speed. And ~15% of tonight's wall clock went to *thrashing*, not computing — which is free
to fix.

---

## Tier 1 — free wins, no quality risk (do first)

### 1. Batch by model, not by shot (est. 10–15% wall clock, zero quality cost)
The queue currently alternates mflux (stills, ~10GB) and Wan GGUF (animation, ~14GB × 2
MoE stages) per shot. Each switch pushes the machine into swap and the memory gate bounces
an idle ComfyUI to reclaim it — measured six times in one hour tonight, ~90 s each.
**Fix:** two passes per queue — lock every still first, then animate every locked still.
The heavy weights load once per pass instead of once per shot. Pure scheduling, no model
change, nothing to LPIPS-gate.

### 2. Keep the vision judge warm on :8181 (est. 1–3 min per run)
`beat_gate` / `forge-shot` fall back to loading Qwen3-VL-32B in-process when Picture Eyes
isn't up — a fresh load per invocation. Running the server once and letting every gate hit
`127.0.0.1:8181` removes reload cost from every separate run. The plumbing already prefers
the server; it just wasn't running.

### 3. Don't animate shots that don't need it
Frozen rule 12 bans faking motion by shaking a still, but a genuinely static beat (a locked
insert, a held reaction) can be a static ffmpeg crop of a wide, or a real
[`bin/ken_burns.py`](bin/ken_burns.py) glide. Each shot moved off the i2v path saves the
full ~17 minutes. The multi-shot coverage rule already sources most close-ups as crops —
this is just applying it deliberately per beat instead of per scene.

---

## Tier 2 — real speedups that must pass the LPIPS gate

### 4. Ship the 1-step distill LoRA into the film path (est. ~2× on animation)
Already built and measured in [`distill/`](distill/): a rank-32 LoRA collapsing 4 denoising
steps into 1 at **LPIPS 0.082** against a measured 0.206 same-resolution wall, and it
transfers to 256×256. It is not yet the default for episode renders. This is the single
biggest lever we already own — the work is validation on *film* shots (characters, motion,
81 frames), not new research.

### 5. Fewer sampled frames + real frame interpolation (est. 1.6–1.9× on animation)
Sample 41 frames instead of 81 and interpolate up (RIFE / film-net class). Sampling cost is
roughly linear in frame count, so this is the largest untried lever after distillation.
**Risk:** interpolation invents motion — exactly where this pipeline has been burned before
(smearing, and rule 12's vibration ban). Gate it on LPIPS *and* re-run the beat gate on the
interpolated clip, since a shot that still depicts its beat is the actual bar.

### 6. Resolution ladder: render small, upscale real (est. 2–3× on animation)
Render at 480×272 and upscale with Real-ESRGAN (already installed here and on the mini).
Motion-transfer work tonight showed draft-res smear on fast motion, so this is likely fine
for ambient/held shots and wrong for anything fast. Gate per shot class, not globally.

### 7. TeaCache-style step skipping for the still pass (est. 1.3–1.5× on stills)
There is now a pure-MLX TeaCache implementation for Flux diffusion on Apple Silicon
([IonDen/mlx-teacache](https://github.com/IonDen/mlx-teacache)), with reported gains that
vary by chip generation. Stills are only ~5% of a shot's cost, so this is a small win — but
it is a *large* win for the refusal path, where a shot burns four to twelve still rolls and
never animates at all. Wan-side TeaCache tuning is documented upstream around
`E012K2R20`-style settings (error threshold, K, retention ratio) from the multi-GPU work;
those parameters would need re-tuning for our 2-step GGUF path.

---

## Tier 3 — investigated, not applicable, or already answered

- **`allow_fp16_accumulation`** — CUDA-only flag requiring a torch nightly; there is no MPS
  equivalent. Not applicable on Apple Silicon.
- **FP8 weights on MPS** — fails or falls back; the community workarounds are fragile.
  **GGUF Q6_K is the right quant here** and is already the i2v default (the fp16 pair at
  ~27GB per MoE stage OOM-killed ComfyUI twice on 2026-07-25).
- **BF16 vs FP16 on MPS** — M2 and later have native bf16; a ComfyUI update that switched a
  path to bf16 caused an 80s → 10min regression for another user on M1 Max. Worth pinning
  dtype explicitly and re-measuring after any ComfyUI update, since our speed can silently
  regress on someone else's default change.
- **Custom Metal flash-attention kernel** — written, measured, **null result**. PyTorch's
  MPS SDPA is already better tuned at our shapes. Kept in [`metal/`](metal/) as documented
  learning.
- **Sequence parallelism across GPUs** — the published Wan 2.2 I2V speedups (2.5× on
  8×H100) are multi-GPU scaling. Irrelevant to a single unified-memory machine, and against
  the point of this project.

---

## Quality levers (not speed, but same discipline)

- **Beats for clips must be judgeable from a single frame.** Two animations were rejected
  tonight on every probe because their beats described *change over time* ("the crack of
  light widens", "she steps down out of the doorway"). A frame can't show a change. Motion
  belongs in a separate motion check; the frame-level beat should describe a state.
- **Identity drifts hardest when a character is small in frame.** Two otherwise-good arrival
  candidates failed the identity gate for a smaller head and lighter orange fur — both wide
  shots. Frame characters big enough to read, or source the wide from a locked plate and
  place characters via crops/inserts.
- **Never prompt an impact.** Wan cannot render collisions; "splinters bursting" became a
  five-second particle spray that reads as drilling. Felt-not-shown, always.

---

## Closing the gap to frontier video (2026-07-26)

Honest position: our output looks worse than frontier models, and the reasons are specific
and mostly self-inflicted rather than a hardware ceiling.

| Why ours looks weaker | Fix, with what we already own |
|---|---|
| **832×480 everywhere.** Frontier demos are 1080p+. Half our "AI look" is just resolution. | LTX-2.3 handles high res natively; Real-ESRGAN is already installed for a ladder. Raise the finish res on locked shots. |
| **2-step lightx2v drafts shipped as finals.** A 4-step-collapsed-to-2 sample is a preview, not a finish. | Reserve the distilled path for drafts/gates; finish approved shots at full steps (`--hq`). The draft gate exists precisely so finals are rare. |
| **Wan 2.2 i2v for talking characters.** Wan can't do lip sync, so dialogue is voice laid over prompted jaw motion — density-matched by hand. That reads as amateur no matter how good the still is. | **LTX-2.3 generates audio and video jointly**, natively — not a post step. We already have LTX-2-distilled downloaded (101GB) and the a2v path proven end-to-end here at ~40 s/clip, with all 12 dialogue close-ups passing lip-sync QC. It is our strongest asset and the episode barely uses it. |
| **Static camera, 5-second held shots.** Frontier reels move. | The multi-shot coverage rule already calls for crops + camera moves per beat; enforce it as a gate (a scene with one framing fails), and use `bin/ken_burns.py` for real glides. |
| **No shot-level aesthetic bar.** We gate story and identity, not craft. | Add a craft ballot to `beat_gate`: composition, lighting, and "does this read as a finished film frame or a diffusion sample" — the plumbing is already there. |

**Model landscape, as of July 2026.** Wan 2.2 leads open-source photorealism (faces, skin,
hair) and is Apache-2.0; HunyuanVideo 1.5 leads natural motion; **LTX-2.3 (22B DiT) is the
only one doing 4K with natively synced audio, and it's the fastest locally.** Apple Silicon
support is the catch: Wan 2.2 and Hunyuan have no stable MPS path, Metal has no
`Float8_e4m3fn` so FP8 checkpoints are out, and LTX on an M2/M3 Max runs at roughly 1/8 the
speed of a 4090. There are now **pure-MLX ports of LTX-2.3** worth evaluating against our
ComfyUI path ([dgrauet/ltx-2-mlx](https://github.com/dgrauet/ltx-2-mlx),
[Acelogic/LTX-2-MLX](https://github.com/Acelogic/LTX-2-MLX)) — MLX would drop the ComfyUI
model-thrash entirely, which is 15% of our wall clock.

**Concrete plan, cheapest first:** (1) make LTX-2 a2v the default for any shot with a
character speaking, since it's proven here and fixes lip sync structurally; (2) finish
locked shots at full steps and higher res instead of shipping drafts; (3) add the craft
ballot so a frame that looks like a diffusion sample fails; (4) evaluate the MLX LTX-2 ports
against our ComfyUI path with `bin/measure-render`.

The audience assumption behind all of it: our AI video posts have been downvoted to nothing
and removed. Assume viewers are hostile to slop. Coherent story, clean synced audio, no
morphing, and real resolution are the price of entry — not extras.

## Next concrete step

Tier 1 items 1 and 2 are pure scheduling and cost nothing to try — do them before any model
work. Then validate the existing 1-step distill LoRA on real film shots, since it is already
measured and already ours.

---

Sources consulted: [mlx-teacache (TeaCache for Flux in pure MLX)](https://github.com/IonDen/mlx-teacache) ·
[Boosting Wan 2.2 I2V inference (TeaCache params, sequence parallelism)](https://morphic.com/blog/boosting-wan2-2-i2v-56-faster) ·
[ComfyUI FP8 on Apple Silicon workaround](https://github.com/Comfy-Org/ComfyUI/discussions/13273) ·
[MPS BF16 regression: 80s → 10min on M1 Max](https://lilting.ch/en/articles/comfyui-qwen-mps-bf16-slowdown) ·
[fp16 accumulation is CUDA-only](https://github.com/Comfy-Org/ComfyUI/issues/11621) ·
[ComfyUI Apple Silicon MPS speed notes](https://www.workflowlab.dev/deploy/comfyui-mac-apple-silicon-mps-speed) ·
[LTX-2 vs Wan 2.2 on M1 Max (GGUF viability on Mac)](https://lilting.ch/en/articles/ltx2-wan22-mac-local-video-gen)

## 2026-08-29 — LTX-2.5 (dgrauet/ltx-2-mlx 0.15.1, bf16 pack) measured against what we ship

Same M5, Song Forge resident (~54GB). All numbers are wall clock of the render process
alone; forge_guard lease waits are excluded (three runs lost 900s each to a stale lease —
see LESSONS "stale-lease").

| shot | engine | wall | memory | judge |
|---|---|---|---|---|
| L01_hank a2v, 97f 768x512, canon face + voice wav | LTX-2 distilled via mlx-video (July path) | **41.7s** | fine | film_qc PASS 4/4 |
| same | LTX-2.5 a2v (dev + CFG two-stage, bf16) | **258s** | 42GB resident, ended at 39GB swap (panic signature) | film_qc PASS 6/6 |
| s1_coldopen i2v, 5s 832x448, locked still | Wan 2.2 14B GGUF (July/Aug director runs) | 13–16 min | wired ~32GB | — |
| same | LTX-2.5 --distilled --image, **--low-ram** | **~69s** | Metal peak small, no swap growth | frames hold composition + identity (bear, dog, rod, water, wagon) |
| same | LTX-2.5 --distilled --image, full | **79s** | 49GB resident, 32GB swap spike at teardown | identical frames (seed-deterministic) |

**Verdicts (applied):**
1. Dialogue close-ups STAY on the July a2v path (mlx-video LTX-2 distilled): 6x faster,
   same QC result, no memory risk. ltx-2-mlx only exposes the dev+CFG a2v pipeline.
2. Scene animation MOVES to LTX-2.5 distilled i2v with --low-ram: ~10x faster than Wan
   per shot, and it holds a two-character composition Wan struggled with. Wired as
   `bin/make-ltx25` (make-video CLI contract) + `engine: ltx25` / `SF_ANIMATE_ENGINE=ltx25`
   in forge-shot. Not yet judged by beat_gate at scale — the overnight director run on
   circus_train is the first real test; read STATUS.md for the pass rate.
3. Gotchas: ltx-2-mlx a2v does not pad audio (short wav vs 97 frames → RoPE broadcast
   error) — make-ltx25 pads with silence. 480 rows render as 448 (LTX rounds to 64).
   Ask forge_guard for ≤20GB on --low-ram; a 45GB ask stalls 15 min behind any other lease.
