# Story Forge — Session Handoff

> Read this first when resuming the build. Captures exact state as of the last commit.

---

## What Story Forge is

A local-only generative cinema pipeline. Five open-source models composed by ffmpeg:
- **Flux 1 Dev FP8** — still per scene
- **Wan 2.2 i2v + lightx2v 4-step LoRA** — motion per scene (5-sec native)
- **Piper LibriTTS speaker 0** — warm storyteller narration
- **ACE-Step (Song Forge)** — original instrumental music
- **ffmpeg** — xfade stitch, sidechain ducking, fade in/out, mux, Pillow PNG title/credits

GitHub: https://github.com/nicedreamzapp/story-forge
First film live on YouTube: https://youtu.be/_bFQTl7_vF4
Live website: https://nicedreamzwholesale.com/software/story-forge/
First Facebook Reel: posted (in processing as of last session)

---

## What's working RIGHT NOW (verified end-to-end)

**Pipeline (M5 Max):**
- Story Forge UI at `http://127.0.0.1:17600/story` — form-driven scene authoring
- `story_pipeline.py` at `~/Desktop/PROJECTS/AI/videopipe/story_pipeline.py` — runs the full Flux → Wan → Piper → ffmpeg pipeline given a JSON config
- Scene-synced narration via `adelay+amix` (each Piper line at its scene's onscreen start)
- Warm EQ chain for narration: highpass(80) → +2dB low-shelf @ 250Hz → -2dB high-shelf @ 7kHz → compressor → aecho 60ms → loudnorm I=-16 LUFS
- Sidechain music ducking under narration (automatic)
- Saga stitch recipe (multi-film): strip credits from each act, `xfade=fadeblack` 1.8s between, new combined credit roll. Validated on bear-sister + bear-return saga (4:08 total).

**M5 Forge running services:**
- Flask/Story Forge server: `127.0.0.1:17600`
- ComfyUI: `127.0.0.1:8188`
- Song Forge / ACE-Step server: `localhost:8767`

**Apps / launchers:**
- `~/Desktop/Story Forge.app` (renamed from MakeVideo.app) — clicking opens Brave at `localhost:17600/story`

---

## Critical workflow rules (lessons learned the hard way)

These are FROZEN — do not re-derive, just apply:

1. **Piper flag is `--noise-w-scale`, NOT `--noise-scale-w`** (word order matters; the wrong order silently gets read aloud as part of the speech).
2. **Pipe each Piper sentence to its own file** — `-f` only saves the LAST stdin line, so multi-sentence Piper requires per-sentence rendering + concat with silence.
3. **Scene-synced narration via `adelay+amix`, never naive concat at t=0** — concat puts all narration in the first scene's audio band.
4. **Native 5-sec Wan, not stretched** — never `setpts=PTS*1.5`. Looks like dreamy slow-motion. Use more scenes if you need a longer movie.
5. **QC every audio output before claiming it works** — use silencedetect + spectrogram, not duration alone. The Piper flag bug only got caught after Matt heard "noise-scale-w 0.7" said aloud.
6. **QC every visual output before showing Matt** — extract 3-4 frames with `ffmpeg -ss`, Read them, judge yourself. The baseball commercial fiasco came from shipping without checking.
7. **Wan doesn't understand physics** — never ask for object collisions (bat-meets-ball), trajectories (curveball arcs), or coordinated multi-character action. Wan handles: ambient motion, camera moves, walking, breathing, atmosphere, particles. Stay inside that lane.
8. **First-person POV doesn't work** — Wan pulls back to third-person. If you need POV, use a reference photo with the right composition baked in (we used a real MLB home-plate photo + Wan animated it correctly).

---

## The two-week speedup build — status

Stack goal: drop a 4-min film render from 5 hours to ~10-30 min. Stacked savings target: 30× baseline.

### ✅ Plumbed (model files, configs, scripts written)

| Item | Where | Status |
|---|---|---|
| LTX-Video 13B distilled model | `~/AI/ComfyUI/models/diffusion_models/ltx/ltxv-13b-0.9.8-distilled.safetensors` (27 GB) | On disk |
| LTX-Video ComfyUI custom node | `~/AI/ComfyUI/custom_nodes/ComfyUI-LTXVideo` | Installed |
| `make-ltx-video` CLI | `~/Desktop/PROJECTS/AI/videopipe/bin/make-ltx-video` | Written, NOT WORKING — see "Open problems" |
| `render-route` CLI (Wan/LTX auto-selector) | `~/Desktop/PROJECTS/AI/videopipe/bin/render-route` | Written, depends on make-ltx-video |
| Mini ComfyUI install | `~/AI/ComfyUI/` on mini | Installed, listening on `:8188` |
| Mini Wan i2v models | `~/AI/ComfyUI/models/diffusion_models/wan2.2_i2v_*.safetensors` on mini (54 GB) | Downloaded |
| Mini Wan i2v LoRAs | `~/AI/ComfyUI/models/loras/wan2.2_i2v_lightx2v_*.safetensors` on mini (2.2 GB) | Downloaded |
| Mini Wan VAE | `~/AI/ComfyUI/models/vae/wan_2.1_vae.safetensors` on mini | Downloaded (verify with `mini "ls -lh ~/AI/ComfyUI/models/vae/"`) |
| Mini text encoder | `~/AI/ComfyUI/models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors` on mini (6.3 GB) | Downloaded |
| Mini Piper + LibriTTS voice | `~/Library/Python/3.9/bin/piper` + `~/piper_voices/en_US-libritts_r-medium.onnx` on mini | Installed |
| Mini Real-ESRGAN weights | `~/AI/upscale/RealESRGAN_x4plus.pth` on mini | Downloaded |
| Mini training stack | `peft 0.19.1`, `accelerate 1.13.0` in mini's ComfyUI venv | Installed |
| Mini-side Wan render CLI | `~/mini_wan_render.py` on mini | Pushed |
| Wan distill v1 scaffold | `~/AI/distill/wan_distill_v1.py` on mini | Scaffolded (stubs for ComfyUI WanVideoWrapper integration) |

### 🛑 2026-05-24 midday: the Metal patch CRASHES renders even when "disabled"

Root cause of repeated ComfyUI `Abort trap: 6` crashes during cabin_open renders: the `wan_metal_fused` ComfyUI custom node monkeypatches `WanSelfAttention.forward` at startup. Even with `WAN_METAL_FUSED=0` the patch's *fallback* branch calls plain `F.scaled_dot_product_attention`, **bypassing ComfyUI's native sub-quadratic/split attention**. At Wan i2v's real sequence length (S≈28350 for 832×480×81f) MPS SDPA materializes the full score matrix → tries to allocate a **128 GB** MTLBuffer → `failed assertion ... size 128595600000` → process aborts. The `WAN_METAL_FUSED=0` "safe default" claim was WRONG; the monkeypatch itself is unsafe.

**FIX (applied):** disabled the node — `~/AI/ComfyUI/custom_nodes/wan_metal_fused` → `…/wan_metal_fused.disabled`, removed `/tmp/wan_metal_fused.flag`, cold-restarted ComfyUI. It now logs `Using sub quadratic optimization for attention` and Wan renders fit ~64 GB peak. **DO NOT re-enable that node.** The repo's `metal/` code stays as documented learning, but the live ComfyUI shim must remain disabled. See updated `metal/README.md`.

### ⚠️ 2026-05-24 morning correction

Last night's session ran ~13 hours and shipped a lot, but two celebrated "wins" were FALSE:

1. **Metal flash-attention "12.32× speedup" was a measurement bug.** `torch.mps.compile_shader` dispatch parameters were misinterpreted — the kernel only computed 1/128th of the output rows. Unused rows received whatever was in freed memory from the previous SDPA call, which happened to contain the correct reference output (passing PSNR=137dB by pure coincidence). On real Wan renders the leftover memory was saturated fp16 garbage = brown noise frames. Bug fixed in `metal/flash_attn_mps.py`; kernel now produces correct output (PSNR 82+ dB at Wan shapes) but is **2-4× SLOWER than MPS SDPA** — vendor too tuned to beat. Code preserved as documented learning in `metal/README.md`. Metal kernel is OFF in production (`WAN_METAL_FUSED=0` default).

2. **Wan 2-step distill training OOM'd on mini.** Estimated 40-44GB peak vs 64GB available was wrong — actual peak ~70GB, macOS hung overnight, mini force-rebooted at 10:49AM, Matt's 9AM morning briefing didn't run. Distill training is INCOMPLETE. Re-fire on M5 (128GB, fits cleanly) OR mini with Q4 GGUF weights (~25GB peak).

### Machine utilization rules (do not repeat last night's mistakes)

| Machine | RAM | Safe peak | Best uses |
|---|---|---|---|
| M5 Max | 128GB | ~90GB | Wan fp16 inference, distill training, LTX renders, Metal kernel dev (when revisited), heavy compute |
| Mac mini M4 Pro | 64GB | ~45GB | Wan Q4 GGUF inference, Piper TTS, ACE-Step music, avatar-pipeline lipsync, status server, light services, morning briefing |
| HQ VPS | small | small | dashboard, job queue, WP hosting |

For any new long-running job, compute peak memory FIRST (model_GB × stages + activations + optimizer + 25% margin), pick machine, verify fits. See memory `feedback-machine-select-by-memory-budget.md`.

### ✅ Validated working as of 2026-05-24 night session

1. **LTX 13B distilled 0.9.8 i2v on M5 MPS** — 118.6s per 5-sec clip (5.6× faster than Wan baseline). Uses Lightricks' OWN upstream code at `~/Desktop/PROJECTS/AI/videopipe/LTX-Video/`. Wrapper: `bin/make-ltx-lightricks`. Multi-scale recipe (7-step low-res first pass → spatial upscaler → 3-step high-res second pass). **Do NOT use diffusers** — `LTXImageToVideoPipeline.from_single_file()` is single-pass and physically cannot reproduce the multi-scale architecture, produces psychedelic noise every time. Confirmed across 5 retest attempts. Must set `prompt_enhancement_words_threshold: 0` in the derived YAML to disable Florence-2 prompt enhancer (transformers 5.9 broke it with `AttributeError: 'Florence2LanguageConfig' has no 'forced_bos_token_id'`). See `[[reference-ltx-lightricks-mps-recipe]]` memory.

2. **Measurement harness** at `bin/measure-render` — `baseline <name> -- <cmd>` and `compare <name> -- <cmd>` subcommands. Per-frame LPIPS via the `lpips` pypi pkg, ffprobe metadata, gates default to mean<0.05 / p95<0.10 / speedup>1.10. Use for every multiplier before integrating.

3. **mini ComfyUI :8189** — runs the `~/AI/ComfyUI/` install (newer ComfyUI v0.22 with `Wan22ImageToVideoLatent` + correct mask handling for the 36-channel patch_embedding). Spawn from Mac mini Terminal (FIA) via `nohup ~/AI/ComfyUI/venv/bin/python ~/AI/ComfyUI/main.py --listen 127.0.0.1 --port 8189 < /dev/null > /tmp/comfy8189.log 2>&1 & disown`. LaunchAgent plist staged at `/tmp/com.matt.comfyui-8189.plist` for `launchctl bootstrap` install.

4. **Custom nodes cloned on mini** (no ComfyUI restart yet): `~/AI/ComfyUI/custom_nodes/ComfyUI-WanVideoWrapper` (kijai — MagCache/TeaCache/EasyCache nodes) and `~/AI/ComfyUI/custom_nodes/ComfyUI-GGUF` (city96 — `UnetLoaderGGUF` for Q4_K_M Wan weights). Will activate on next ComfyUI :8189 restart.

5. **Q4_K_M Wan weights cached on mini** at `~/AI/ComfyUI/models/unet/Wan2.2-I2V-A14B-{HighNoise,LowNoise}-Q4_K_M.gguf` (9.65GB each, from QuantStack). Replaces the 28GB fp16 files we currently use. ~4× memory drop, faster load.

### Open problems

1. **Wan fp16 dual-stage on mini takes >50 min per clip.** 14B × 2 stages = 56GB fp16 weights on a 64GB M2 Pro hits memory pressure hard. Q4_K_M (just downloaded, not yet validated) should fix this — both stages fit in ~20GB. Test pending ComfyUI restart.

2. **MPS does NOT support FP8_E4M3FN dtype.** Wan 2.2 fp8_scaled checkpoint files load but immediately RuntimeError on first sampler step. Stick with fp16 or GGUF Q4. Apple may add FP8 support later.

3. **Wan attention bench OOMs.** `bin/bench-wan-attention` loads all models simultaneously and overruns M5's 180GB MPS watermark. Needs sequential-load fix (unload TE before sampler runs, etc.) before we can get the Metal-kernel ROI numbers. Phase 0 effort: ~1 hour.

4. **Story Forge UI extensions — mostly shipped 2026-05-25.** Multi-voice routing, SFX, and per-scene fast-mode were always supported by the DSL; they're now SURFACED in the web editor via one-click example scripts (`multi_voice.sf`, `sfx_demo.sf`, `styled_reel.sf`) plus a live Styles & Formats picker (`/api/packs`). New `story-new` scaffold CLI and `story_forge/packs.py` style/format packs added. Still TODO: Wav2Lip lip-sync toggle in the UI (deliberately deprioritized — mouth-repaint is banned for stylized characters anyway).

### Roadmap (in priority order, updated 2026-05-24)

1. **Wan Q4_K_M validation** (next, ~15 min) — Restart mini ComfyUI, write Q4 workflow JSON variant (swap `UNETLoader` → `UnetLoaderGGUF`), test 5-sec render. Expected speedup ~2× from faster load alone.
2. **MagCache/TeaCache layer** (~30 min) — Add `WanVideoTeaCache` node to Q4 workflow on both high-noise and low-noise branches, sweep threshold via measurement harness. Expected ~1.1-1.3× more.
3. **Wan baseline + harness comparison run** (~15 min) — Record fp16 (or Q4 if fp16 won't finish) as baseline; compare Q4+MagCache. First real LPIPS numbers.
4. **`render-route` integration of `make-ltx-lightricks`** — Replace broken `make-ltx-video` with `make-ltx-lightricks` so B-roll scenes auto-route to working LTX.
5. **Phase 0 attention bench rewrite** — Sequential model load so it doesn't OOM. Then we have hard numbers to gate the Metal kernel work.
6. **Phase 1 Metal kernel** (Xcode + Metal compiler are installed) — Start with fused RMSNorm+Linear (safer than fused QKV+RoPE first try). PyTorch `torch.mps.compile_shader` + custom op + env-var gate.
7. **Story Forge DSL MVP** — Indentation-based blocks, `.sf` → `.storyplan.json` IR → ComfyUI workflow + ffmpeg plan.
8. **Wan distill training** — 1-2 day project, the genuine perpetual 2× via 2-step student.
9. **Story Forge UI extensions** (multi-voice + SFX + fast-mode toggle).
10. **Wav2Lip integration** for dialogue scenes.

---

## File locations cheatsheet

| Thing | Path |
|---|---|
| Pipeline core (Python) | `~/Desktop/PROJECTS/AI/videopipe/story_pipeline.py` |
| Story Forge server | `~/Desktop/PROJECTS/AI/videopipe/server.py` (port 17600) |
| Story Forge UI HTML | `~/Desktop/PROJECTS/AI/videopipe/ui/story.html` |
| Story Forge app launcher | `~/Desktop/Story Forge.app` |
| Wan inference CLI (M5) | `~/Desktop/PROJECTS/AI/videopipe/bin/make-video` |
| LTX inference CLI (M5) | `~/Desktop/PROJECTS/AI/videopipe/bin/make-ltx-video` (BROKEN — see open problems) |
| Render router (M5) | `~/Desktop/PROJECTS/AI/videopipe/bin/render-route` |
| Mini Wan render CLI | `~/mini_wan_render.py` on mini |
| Mini distill scaffold | `~/AI/distill/wan_distill_v1.py` on mini |
| Flux T2I script | `~/Scripts/flux_t2i.py` |
| Piper binary | `~/Library/Python/3.9/bin/piper` |
| Piper voice model | `~/Desktop/PROJECTS/Song Forge/piper_voices/en_US-libritts_r-medium.onnx` |
| Song Forge server | `localhost:8767` |
| ComfyUI (M5) | `localhost:8188`, dir `~/AI/ComfyUI/` |
| Mini access CLI | `~/.local/bin/mini "<cmd>"` |
| Saga output | `~/Desktop/AI Videos/bear-sister-saga.mp4` (161 MB) |
| Saga compressed for repo | `~/Desktop/PROJECTS/story-forge/saga.mp4` (92 MB) |
| Saga 9:16 vertical (Reels) | `~/Desktop/AI Videos/bear-sister-saga-vertical.mp4` |

---

## How to drive Matt's real Brave for web tasks

ComfyUI restart pattern needed: `--remote-debugging-port=9222`. Memory rule: never use Playwright/Chromium — always Matt's authenticated Brave. To enable CDP control:

```bash
osascript -e 'tell application "Brave Browser" to quit'
sleep 3
open -na "Brave Browser" --args --remote-debugging-port=9222 --restore-last-session
sleep 4
curl -s http://127.0.0.1:9222/json/version  # verify
```

Then `mcp__chrome-devtools__*` tools work. YouTube + Facebook Reels upload was validated this way.

---

## Memory entries that matter (in `~/.claude/projects/-Users-dtribe/memory/`)

- `reference_story_forge_pipeline.md` — full pipeline architecture
- `reference_warm_narration_recipe.md` — the exact Piper + EQ chain for warm storyteller voice
- `reference_saga_stitch_recipe.md` — how to combine films into a saga
- `feedback_narration_must_sync_scenes.md` — adelay+amix rule
- `feedback_qc_ai_videos_before_sending.md` — always frame-check before showing Matt

---

## Last actions in the session

1. Saga published to YouTube: https://youtu.be/_bFQTl7_vF4 (public, made for kids, AI + sensory-friendly tag stack)
2. Saga posted to Facebook Reels as 9:16 vertical with blurred-background extension (full original preserved + tasteful padding)
3. Story Forge GitHub repo updated with YouTube embed thumbnail
4. nicedreamzwholesale.com/software/story-forge/ page deployed
5. /software/ index card added under "🧠 The local-AI stack"
6. Started mini Wan validation (job in flight at session end — check status with mini --done command)
7. Tried LTX-Video standalone test → failed on T5 encoder loading (documented above)

---

## Next session — drop right in with

```bash
# 1. Check if the mini Wan validation job finished
~/.local/bin/mini --done $(cat /tmp/mini_wan_job.txt 2>/dev/null)

# 2. Or restart validation cleanly
~/.local/bin/mini --queue "~/AI/ComfyUI/venv/bin/python ~/mini_wan_render.py --still /tmp/mini_test_still.png --prompt 'gentle wind moves' --label mini_validate --duration 5 --width 832 --height 480"

# 3. Fix LTX (open problem #1) — needs T5 encoder loader fix in make-ltx-video
```

Resume from "Validate mini Wan inference" in the roadmap above.
