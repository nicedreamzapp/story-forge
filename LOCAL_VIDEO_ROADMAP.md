# Premier Local Video on Apple Silicon (M5 Max) — Roadmap
Researched + verified 2026-05-29 (deep-research, 21 sources, 22 claims confirmed). Field moves weekly.

## The core truth
Talking-character quality splits HARD by character type:
- **Cartoon/stylized:** SOLVED locally, today, cleanly → **Rhubarb Lip Sync + viseme rig** (CPU, native macOS, no CUDA). This is what we just used.
- **Photoreal neural lip-sync** (LatentSync, MuseTalk, Sonic, Hallo, EchoMimic, video-retalking, Wav2Lip): all CUDA-first, experimental-at-best on Mac. Wav2Lip mouth is low-res/mushy regardless. An M5 Max **cannot** do near-Sora photoreal talking locally yet.

## Recommended install order (verified)
1. **Rhubarb Lip Sync** (DanielSWolf/rhubarb-lip-sync) — phonetic visemes A–F+G,H,X from audio. INSTALLED ✅ at `story-forge/rhubarb-pipeline/`.
2. **blender_rhubarb_lipsync_ng** (Premik fork, Blender 4.2+) — maps Rhubarb visemes onto a Blender rig's mouth poses/shape-keys → keyframed 3D talking. (Original scaredyfish fork is dead.) ← next step for 3D Doug.
3. **MLX LTX-2** for B-roll / scenery (james-see/ltx-video-mac, Blaizzy/mlx-video) — the only FAST native Apple-Silicon video path. 64GB+ rec; M5 Max 128GB exceeds it.
4. **WanGP/Wan2GP** experimental MPS (May 2026) — LTX-2 Id Lora + LongCat-1.5 talking-head avatars; slow, accept caveats.
5. Photoreal lip-sync only if needed: **LatentSync PR #359** (open, unmerged MPS branch) or Easy-Wav2Lip MPS (untested). Both experimental.

## Hard Mac caveats
- **No FP8 on MPS** → use FP16/bf16 or GGUF. FP8 checkpoints throw `Float8_e4m3fn ... not supported`.
- Heavy diffusion (Wan 2.2 14B GGUF) ≈ impractically slow (~82 min / 2s clip on M1 Max; M5 faster but still not realtime).
- `PYTORCH_ENABLE_MPS_FALLBACK=1` runs unsupported ops (e.g. FFT) on CPU.

## Our proven pipeline (built 2026-05-29)
Image→3D (Hunyuan3D on MPS) ✅ · skeletal rig + animation in Blender ✅ · **Rhubarb visemes → clean 2D mouth-shape talking** ✅ (`rhubarb-pipeline/doug_talking_rhubarb.mp4`).
Next: build a viseme pose-library on a real character rig (Blender NG addon) so the 3D Doug talks with these same crisp visemes instead of flat 2D mouths.

## Session log 2026-05-29 (what we actually built + learned)
- Rhubarb visemes → flat coded character: real phonetic timing, but art was weak.
- Flux base character + per-viseme INPAINT (denoise 1.0, "closed snout fur" prompt for the closed pose): premium on-model art, distinct viseme mouths. Hard-cut (no crossfade) = crisp.
- LTX-13B i2v on the Flux Doug: GORGEOUS fluid motion (~2min/5s @768x512), identity holds — but LTX invents its own mouth, zero relation to speech ("the disconnect").
- MARRIAGE attempt: gentle FORWARD-FACING LTX idle (closed mouth) + nose-tracked (cv2 matchTemplate, 0.95) compositing of the Rhubarb viseme mouths. Works + roughly synced.
  - **CEILING (Matt, 2026-05-29): only works head-on. A frontal mouth overlay can't ride a turning head → not practical for real shots. Also slightly blurry (768x512 upscale + overlay feather).**

## The practical any-angle answer (next real build)
Compositing a frontal mouth is a dead-end for production. Two paths that lip-sync at ANY angle/pose:
1. **Audio-driven neural avatar** — LongCat-Video-Avatar-1.5 (8-step distilled, voice+image→talking with motion) or LTX-2 Id Lora, via WanGP/Wan2GP experimental MPS. Generates the correct mouth per phoneme at any pose. THE practical fix; cost = big WanGP install + experimental MPS (slow, may fight).
2. **3D rig with viseme blendshapes** — give the 3D Doug a real articulable mouth (sculpt/retopo) + viseme shape keys, drive with Rhubarb via blender_rhubarb_lipsync_ng. Talks at any camera angle natively. Cost = one-time mouth sculpt.

### ELIMINATION (verified 2026-05-29, late session)
Neural lip-sync (#1) is DEAD for cartoon characters. Installed LatentSync 1.6 MPS branch (PR #359) fully on the M5 (torch 2.12, all deps, 4.7G ckpt) — ran on the Flux/LTX cartoon Doug clip → **"RuntimeError: Face not detected."** insightface/mediapipe face detectors are human-face-only; they can't see a stylized dog. Same root reason Wav2Lip/video-retalking mangle cartoons. So ALL neural audio-driven lip-sync (LatentSync, MuseTalk, Sonic, Hallo, LongCat, video-retalking, Wav2Lip) is OFF THE TABLE for non-human cartoon characters — they need a detectable human-ish face.

### THE remaining practical path for a CARTOON show = a RIG + Rhubarb (no face detection needed)
This is the research's original #1, and now the ONLY non-dead path for any-angle cartoon talking:
- **2D puppet rig** (layered head/jaw/eyes/body/limbs, posed by transforms) + Rhubarb-driven viseme mouth-swap. How Character Animator / Cartoon Animator / Moho / blender_rhubarb_lipsync_ng 2D shows work. Moves freely in 2D + synced mouth, reusable. ← most achievable.
- **3D rig** (mouth sculpt + viseme blendshapes) — any 3D angle, but the Hunyuan3D mesh has no mouth cavity, so needs a real mouth-capable rig (sculpt or a pre-rigged base).

Recommendation: build a proper **2D puppet rig of Doug** (layered, Rhubarb-driven) — it's the genuinely practical answer and a focused fresh build, not a tail-end grind.

Sources: github.com/DanielSWolf/rhubarb-lip-sync, Premik/blender_rhubarb_lipsync_ng, james-see/ltx-video-mac, bytedance/LatentSync#359, deepbeepmeep/Wan2GP, huggingface.co/meituan-longcat/LongCat-Video-Avatar-1.5.

## ★ BREAKTHROUGH (deep research #2, 2026-05-29) — the holy grail EXISTS
Pixar-style cartoon animation WITH synced dialogue for a NON-human character is a SOLVED capability. The right tool is an audio-driven CHARACTER-ANIMATION model (image + audio → talking video), NOT a separate lip-sync pass:
- **Wan2.2-S2V-14B** — image + audio → lip-synced talking video; explicitly supports cartoons/animals/non-human (its own demo drives a stylized cat). STRONGEST fit. On Replicate (pay-per-clip).
- **HunyuanVideo-Avatar** — explicitly cartoon/3D/anthropomorphic (LEGO/anime demos).
- **LTX-2** — co-generates synced audio+video in ONE pass.
- **OmniSync** (NeurIPS'25) — mask-free, purpose-built for cartoon/non-human lip-sync (no face detection), 87% on stylized. NO public weights yet — WATCH for release = would make this fully local.

### Why we hit the wall: it was the LOCAL-ONLY constraint, not impossibility
EVERY strong audio-driven model (Wan2.2-S2V, HunyuanVideo-Avatar, InfiniteTalk/LongCat, LTX-2) is CUDA/Linux — NO native Apple Silicon. The "LTX-2 supports MPS" claim was REFUTED 0-3. That single fact is the whole three-day wall.

### The concrete way through
- **OPTION A (best quality, tiny cloud cost):** local Pixar still + local TTS voice → run **Wan2.2-S2V on a rented GPU / Replicate** (you only pay for the talking-render seconds, per shot) → composite/upscale local. The 80GB-VRAM claim was REFUTED, so an unofficial GGUF/CPU-fallback attempt on the M5 is also worth one shot (a Mac Studio M2 reportedly ran it).
- **OPTION B (fully local, no cloud):** Blender rig (3D or 2D puppet) + Rhubarb (Premik fork) viseme keyframes → render on M5. Sidesteps face detection (animates geometry). More upfront rigging.
- **Fix warpy i2v:** IC-LoRA pose/depth control + keep motion words OUT of the prompt (let reference/pose video drive motion).

Sources: huggingface.co/Wan-AI/Wan2.2-S2V-14B, Tencent-Hunyuan/HunyuanVideo-Avatar, Lightricks/LTX-2, ziqiaopeng.github.io/OmniSync, Premik/blender_rhubarb_lipsync_ng.

## ✅✅ SOLVED — the working talking-cartoon pipeline (2026-05-29, Matt: "that's pretty good")
After eliminating every local-only path, THIS is the recipe that delivered a real talking cartoon Doug:
1. **Character art** — Flux (local, free): `rhubarb-pipeline/art/base.png` (Pixar bloodhound).
2. **Voice** — ChatterBox / TTS (local, free): `3d-spike/audio/doug_line.wav` (Matt's cloned voice).
3. **Talking render** — **Wan2.2-S2V on the FREE Hugging Face Space** `Wan-AI/Wan2.2-S2V` via gradio_client (online, $0, NO card):
   ```python
   from gradio_client import Client, handle_file
   c = Client("Wan-AI/Wan2.2-S2V")
   res = c.predict(ref_img=handle_file(IMG), audio=handle_file(WAV), resolution="480P", api_name="/predict")
   # res["video"] = talking-cartoon mp4 (audio baked in)
   ```
   Driver script: `/tmp/wan_s2v_hf.py`. ~3 min incl. queue. Output: real neural lip-sync IN the character's own 3D style, identity held, mouth shapes genuinely vary (QC'd frame-by-frame). NOT mangled (unlike Wav2Lip/LatentSync which can't even detect a cartoon face).

WHY THIS WORKS where everything local failed: Wan2.2-S2V is character-agnostic (its own demo is a cat), so no human-face-detector dependency. It's CUDA so it can't run on the M5 — but the FREE HF Space runs it in the cloud at no cost.

### Next levers (not yet done)
- **720P** (the Space supports it) for higher quality.
- **Multi-shot scenes** — generate per shot, stitch.
- Combine with LTX-13B (local) for non-talking B-roll/scenery between dialogue shots.
- Watch OmniSync for a weights release → would bring this fully local.
