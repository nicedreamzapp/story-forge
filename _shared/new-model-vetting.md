# New model vetting — the production every new model goes through

Added 2026-11-03 after the Minimax-H3-Hybrid-DMAD-PDMD check (Matt: "bake that into all things for the
future when we look over new models and make this production"). Every new model the watcher or Matt
brings in runs these steps in order, and stops at the first one it fails. The verdict and the reasons get
written down, and the review itself becomes a short video (step 7).

## 0. The brief, before anything else
- One or two plain lines for Matt: what the model does, who made it and what for, its size, how it runs.
  Matt 11/3: "I always want like a brief on what the model can do... or what it was made for."
  Every watcher text carries a short version of it. License-blocked models are never texted (Matt 11/3), only logged.

## 1. License first, before anything is downloaded
- Read the LICENSE file itself, not the HF tag. A merge or finetune carries its base model's license:
  follow `base_model` in the card all the way back and read each one's license.
- Hard stops: any territory exclusion that covers the US (MiniMax H3: "Excluded Territories ... the United
  States of America", outputs included), non-commercial (CC-BY-NC, YuE2), or anything that limits what we
  can do with outputs. Revenue caps (LTX under $10M, Music3 under $20M) are fine, but write the cap down.
- A failed license means no download, no MLX port, no HF upload (uploading from the US is distribution).

## 2. Does it fit how we build
- Building/LLM models must read images (confirmed from config.json). Media models: does it do something our
  current default can't, or the same thing better or faster?
- Precision: bf16 if it fits in 128 GB. If the only release is quantized (int8, fp8, GGUF), look for bf16 sources.
- Runtime: does an MLX/MPS path exist? If not, can we port it (we did MPS fixes for WA2 in `tools/wan_animate2_mps.py`)?

## 3. Compare with what we use now
- Video default: Kandinsky 6 Pro (`bin/make-k6`, MIT). Previs + lip-sync: LTX-2.5. Stills: Krea 2 Turbo.
  Upscale: `bin/upscale-route`. Read `VIDEO-MODEL-2026-11-01.md` and `MODEL-CONSENSUS-2026-11.md` first.
- Check community reports (r/StableDiffusion, r/LocalLLaMA, HF discussions) before spending render time.

## 4. Test, same shot against the current default
- Same prompt, still, seed and length as the default's reference test. Log wall time, peak memory and what
  the clip looks like. Health-check Song Forge first and pass the memory gate (frozen rules 11, 16).

## 5. If it wins: convert, document, publish
- Convert to MLX at bf16, verify the output matches the reference within tolerance, and write the exact
  conversion steps into a `MODEL-<name>-<date>.md` report here plus a `bin/make-<name>` wrapper.
- Upload the MLX port to HF only if the license allows redistribution; credit the original authors and
  link the license.

## 6. Write down the verdict, whatever it is
- Add the verdict + license reason to the report and to memory, so no session re-checks a closed model.
- Delete the loser the same day (no fallback copies).

## 7. Make the review into a video
- A short explainer of the review (what came in, what we checked, the verdict, why), in Matt's matt2 voice,
  made with our CURRENT default tools, never with a model that failed step 1. It's built with the promo format
  (`pipeline/formats/promo/`), gated, and shown to Matt as READY before anything is uploaded.

## Log
| Date | Model | Verdict | Reason |
|---|---|---|---|
| 2026-11-01 | MiniMax H3 (base) | Out | License bans all US use, outputs included |
| 2026-11-01 | Kandinsky 6.0 Pro distill | Default | MIT, best clip we've made |
| 2026-11-03 | OliviaRossi/Minimax-H3-Hybrid-DMAD-PDMD | Out | H3 merge, inherits the US ban; int8-only, ComfyUI-only |
| 2026-11-03 | milliwattlabs/leokani-tts-7M | Out (commercial) | CC-BY-NC-4.0; 7M-param CPU TTS, one female voice trained on Kokoro output. Kokoro (Apache) already covers it |
- 2026-11-03 7:44 PM: the review video for this model went public, https://youtu.be/RwvO8TgfN0o (Nice Dreamz). The channel comment watcher covers it.
