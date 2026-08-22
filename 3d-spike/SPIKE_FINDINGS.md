# 3D Character Spike — Findings (2026-05-29)

Goal: test whether a **deterministic local 3D-character pipeline** on Apple Silicon could
solve i2v's weaknesses (character consistency, pose/expression control, render-time lip-sync).
Proving asset: Doug (bloodhound) from Hank & Doug, single locked still `f04`/`02_portrait_doug`.

## What WORKS (proven this session, 100% local, M5 Max MPS)

1. **Image → 3D mesh on MPS** — Hunyuan3D v2.0 shape-gen runs on Apple Silicon.
   - Driver: ComfyUI HTTP API graph, shape-only (skip CUDA texture stage).
   - LoadImage(rembg'd RGBA) → Hy3DModelLoader → Hy3DGenerateMesh → Hy3DVAEDecode → Hy3DPostprocessMesh → Hy3DExportMesh.
   - ~4 min, watertight single-manifold mesh, 40k faces, **front production-quality recognizable**.
   - Model: `~/AI/ComfyUI/models/diffusion_models/hunyuan3d-dit-v2-0-fp16.safetensors`
   - Script: `run_shapegen.py`. Output: `~/AI/ComfyUI/output/doug_spike_00001_.glb`

2. **Consistent multiview generation** — Zero123++ via diffusers, 1 image → 6 view-consistent images.
   - **Must run on CPU** — MPS produces rainbow noise (known numerical quirk). CPU ~4 min, correct.
   - Code vetted + run from LOCAL copy (`vet/pipeline.py`, `trust_remote_code=True`).
   - Script: `gen_views_zero123.py [cpu|mps]`.

3. **Skeletal rig + animation, identity preserved** — Blender, headless.
   - Armature (spine+head) → `parent_set(ARMATURE_AUTO)` auto-weights → pose-bone keyframes.
   - Head look-around + nod + breathe rendered clean; **same mesh, every frame, no drift**. THE win over i2v.
   - Render: EEVEE → PNG frames → ffmpeg `h264_videotoolbox`. Scripts: `rig_move.py`, `turntable.py`, `render_views.py`.
   - Samples: `doug_turntable.mp4`, `doug_moving.mp4`.

## What FAILED / is BLOCKED

- **Naive multiview mesh (Zero123++ → Hunyuan3D-2mv): shattered garbage.**
  View-convention mismatch — mv model expects canonical front/back/L/R at fixed elevation, 90° apart.
  Zero123++ gives alternating elevations (+20/-10) and 30°-offset azimuths → conflicting geometry → broken.
  Fix would need TRUE orthographic turnaround views (a Doug LoRA), not Zero123++. mv weights at
  `diffusion_models/hunyuan3d-dit-v2-mv-fp16.safetensors`. All 4 view inputs MUST be same pixel size.

- **Clean lip-sync / visemes: blocked on mesh topology.**
  Generated mesh is a closed-mouth solid skin — no mouth cavity, fused lips. "Opening" only stretches
  surface skin (ugly). Needs a properly modeled/retopo'd head with articulable mouth + viseme blendshapes
  (hand-sculpt for a quadruped; the thing CC4/MetaHuman automate for humans).

- **Texture (Hunyuan native painter): CUDA-only.** custom_rasterizer won't build on MPS.
  Local path = UV-unwrap (xatlas) + project reference image in Blender + fur shader. NOT YET DONE.

## Strategic conclusion
3D is **cheap at consistency / pose / camera** (huge win, proven) and **expensive at lip-sync**
(needs a modeled mouth). Pragmatic split: use 3D for consistent stills/turnarounds/camera + body motion;
keep talking on the proven i2v-mouth-motion + voice-over method until a properly rigged Doug head is worth sculpting.

## Hardware / env notes
- All heavy work on M5 Max (128GB, 40-core GPU). Xcode/RC Pro live on the mini; not needed (usdrecord ships in /usr/bin).
- `mini` job-queue stdout caps ~8KB → binary transfer via downscaled JPEG + 90-line base64 chunks, sha-verified.
- Blender 4.x: `action.fcurves` API changed — set rotation per-frame in render loop instead of keyframing+fcurves.

## NEXT (menu, not committed)
1. Texture pass — UV + project portrait + fur shader → colored Doug.
2. Fuller rig — legs/tail, a walk cycle or tail wag.
3. Proper multiview — build a Doug LoRA → true ortho turnaround → re-run mv for a non-flat mesh.
4. Real lip-sync — sculpt/retopo a Doug head with mouth + visemes.
