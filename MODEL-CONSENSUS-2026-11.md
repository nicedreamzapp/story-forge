# Local model consensus for Story Forge, November 2026

Researched 2026-11-01. Sources, weighted in this order: r/StableDiffusion, r/comfyui and r/LocalLLaMA threads from the last 30 to 90 days (read via the mini's Reddit API client); Artificial Analysis (AA) arenas, read live today; Hugging Face downloads and trending; license files read straight from the model repos. r/aivideo searches turned up nothing useful. Anything I could not verify is marked **UNVERIFIED**. No benchmark here is invented.

## Read this first: licenses

Several of the models the community loves most are **not licensed for a US company**, or only below a revenue line. Whether we can use them depends on Divine Tribe's annual revenue (all affiliates combined), which I don't have. The revenue lines:

| Revenue line | Models |
|---|---|
| **US banned outright** | MiniMax H3 and everything built on it (Pika H3 Flex, FastH3, Singularity, Open-H3-Regenerate-2K) |
| Non-commercial only | Qwen-Image-2.1, Fibo 2.0, Ideogram 4, YuE2, MMAudio weights (**we use MMAudio now**), OmniVoice weights, Breeze-TTS-2, Higgs Audio v3 |
| Under $500K | Fish Drama-3 TTS (attribution required too) |
| Under $1M | Krea 2, Stable Audio 3 |
| Under $5M | FLUX 3 Image Klein |
| Under $10M | LTX-2.x (what we use now) |
| Under $20M | MiniMax Music3 (no territory exclusion in its license) |
| Free for any use (MIT / Apache) | MOSS-Image, Kandinsky 6, Wan 2.2 / Wan Animate 2, SCAIL 2, SeedVR2, Kandinsky 6 VSR, RIFE, Qwen-Image-Edit-2511, Chatterbox, Qwen3-TTS, VoxCPM2, ACE-Step 1.5, MOSS-SoundEffect v2, InfiniteTalk, MuseTalk |

### The MiniMax H3 license, verbatim

From `huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/LICENSE`:
- *"'Applicable Territory' means worldwide, excluding the Excluded Territories."*
- *"'Excluded Territories' means the European Union, the United Kingdom, the Republic of Korea and the United States of America."*
- *"You may not use, reproduce, modify, distribute, or display the MiniMax H3 Works or any of their Outputs or results outside the Applicable Territory."*

So the roundup was right. Running H3 on our own Mac in the US isn't licensed at all, for commercial or personal use, and the ban covers the outputs too. Comfy's official guide ([thread, 8/27](https://www.reddit.com/r/StableDiffusion/comments/1w09wb5/)) lists the ways to use it legally from the US:
- **Comfy Cloud**: commercial use is included, but it runs on their servers, not locally.
- **Professional License**: own hardware in the US, "starting at $5K/mo", sold through Comfy.
- **Enterprise**: custom annual deal.

At the MiniMax AMA ([summary](https://www.reddit.com/r/StableDiffusion/comments/1vkplzt/)) the team said switching to Apache-2.0 is "maybe, no promises". Every finetune inherits the same territory clause: Pika-H3-Flex, FastH3-Omni, Open-H3-Regenerate-2K and the MLX ports all carry `minimax-h3-community-license-agreement` on HF. A few community LoRAs and merges are tagged apache-2.0 on HF, but that tag doesn't change the license on the base weights they need.

Matt publicly promised the r/StableDiffusion thread a newer video. If it's made with H3 on our hardware, we'd be displaying H3 output from the US, which the license forbids.

---

## 1. Text-to-video and image-to-video (top priority)

**Hard ranking, AA image-to-video arena (read live today):** MiniMax H3 768p is #4 overall at **1128 Elo** and the top open-weights model. Next open model is LTX-2.5 Fast at **918** (#25), then LTX-2.5 Pro at 910 and LTX-2.3 at 837. Wan 3.0 places #9 (1111) but is **not open weights**. Kandinsky and Hunyuan video aren't listed. ([AA I2V leaderboard](https://artificialanalysis.ai/video/leaderboard/image-to-video))

| # | Model | Why (practitioner evidence) | License for us | Mac viability | Measured Mac speed | Size |
|---|---|---|---|---|---|---|
| 1 | **MiniMax H3** (33B DiT + Qwen3-VL-32B text encoder, native stereo audio, 15s, FLF2VA + Ref2VA with up to 9 images and 3 videos) | It's the default model on the sub right now. Its own thread: "MiniMax H3 - Really is the best open-source video model" (554 pts, [link](https://www.reddit.com/r/StableDiffusion/comments/1xahodr/)). On Matt's thread, u/ofrm1: "LTX just hallucinates too much and it isn't very prompt accurate. The only benefit it has is its speed." Most-upvoted reply on [the nostalgia thread](https://www.reddit.com/r/StableDiffusion/comments/1xka3rd/) (137): "ltx 2.5 still looks like this if you ask it to do anything other than a static shot of someone talking". In a side-by-side short story, LTX "duplicated the wolf and Red hood" and "H3 wins" ([r/comfyui](https://www.reddit.com/r/comfyui/comments/1x608az/)). Character consistency comes from Ref2VA plus character LoRAs ([LoRA learnings](https://www.reddit.com/r/StableDiffusion/comments/1xbobrr/)), and anime and cartoon work is common. Known weaknesses, admitted by MiniMax: "faces and objects go to mush when they're far from the camera", softer Ref2V, and seams when clips are stitched. | **Banned in the US** (see above). The only legal routes cost $5K/mo or run on Comfy Cloud. | Good. bf16 fits 128GB: PipeNetwork measured DiT 40.3GB after dropping AdaLN, text encoder 50.3GB, VAE 10.4GB, about 102GB total ([PipeNetwork/minimax-h3-mlx](https://github.com/PipeNetwork/minimax-h3-mlx)). Ports: `pipenetwork/MiniMax-H3-MLX-bf16` (66GB repo) and `-8bit` (35GB), `appautomaton/mlx-h3` (pure MLX, 8-bit, has an M5-only W8A8 path), Draw Things, Valtz (native Metal), h3c-studio. | M5 Ultra: 15s at 768p plus Regen-2K to 1920x1088 took **12m19s** (Pika H3 Flex 6-step, [thread](https://www.reddit.com/r/StableDiffusion/comments/1xk4xpd/)). M5 16GB in Draw Things: **15-20 min** per 8-10s clip with a 3-step LoRA ([thread](https://www.reddit.com/r/StableDiffusion/comments/1wmqqnj/)). TensorFold claims 5s at 864x480 in about 50s on an M5 Ultra (author's claim, int8 + turbo). PipeNetwork, full undistilled at 1344x768: 8.86 min per step (machine not stated in the excerpt). **The "~45 min/clip on M5 Max" figure: UNVERIFIED, I found no source for it.** | 498GB full repo; about 102GB needed at bf16 for inference |
| 2 | **Kandinsky 6 Pro** (29B, plus a 3B Lite; text/image to video with audio) | Repo reader's summary: "Better than LTX 2.5 (not much of an achievement), but worse than H3 … no FLF2V or reference … Free software" ([thread](https://www.reddit.com/r/StableDiffusion/comments/1wyvnga/)). A 5090 tester: "OK but not as good as Minimax. The 5 seconds are a hard limit … Upscale is very good" ([thread](https://www.reddit.com/r/StableDiffusion/comments/1x0c5d8/)). Ignored by the community, partly for being "Russian" and "heavy". | **MIT, clean** | Diffusers is the reference implementation. The only MLX port is `VVladTech/Kandinsky-6.0-Lite-distill-5s-MLX` with 0 downloads. MPS untested: **UNVERIFIED**. | none reported | about 29B params; bf16 should fit (not measured) |
| 3 | **LTX-2.5** (22B, audio+video; **what we use now**) | Fast (one tester got about 70s per clip against H3's 220s on a GPU) and good at static talking shots and audio-driven lip-sync, but "hallucinates too much" (see #1). AA Elo 918, against H3's 1128. | LTX-2.x Community: free under **$10M** revenue | Excellent. MLX port is already on disk. | our own runs | 223GB on disk |
| Specialty | **Wan Animate 2** (Apache) and **SCAIL 2** (MIT) | For motion and performance transfer. "Wan Animate still did a better job with both the dance motion and the facial expressions" than H3 Ref2V. Expression transfer is "not at the same level as old good scail2" in H3 ([thread](https://www.reddit.com/r/StableDiffusion/comments/1x1ei7r/)). | clean | ComfyUI on MPS; no MLX port found | none reported | Wan 14B class |

**Bottom line for video:** the community consensus is right that H3 is the best open model by a wide margin (210 Elo over LTX). But we can't legally use it locally from the US. For a license-clean bake-off: **Kandinsky 6 Pro vs LTX-2.5 vs Wan Animate 2 (for performance)**, plus H3 only if Matt decides to pay or to run it through Comfy Cloud.

## 2. Text-to-image and image editing

**Hard ranking, AA text-to-image, open-weights entries (read live):** FLUX 3 Image Klein 1043, Qwen-Image-2.1 1042, Fibo 2.0 1039, Krea 2 Large 1034 (AA shows no HF marker on the Large tier), Ideogram 4.0 1026, HunyuanImage 3.0 932, **Z-Image Turbo 936** (what we use). That puts ZIT about 100 Elo below the leaders. MOSS isn't listed. ([AA T2I](https://artificialanalysis.ai/image/leaderboard/text-to-image))

### Text-to-image

| # | Model | Why | License | Mac | Size |
|---|---|---|---|---|---|
| 1 | **Krea 2** (12B; Turbo and Raw) | The community favorite for both looks and styles. "Krea 2 king of styles!" (1133 pts, 1,255 styles, [link](https://www.reddit.com/r/StableDiffusion/comments/1xfeonr/)). "I've trained 100+ Krea 2 character LoRAs" (881 pts, [link](https://www.reddit.com/r/StableDiffusion/comments/1x0imbp/)), so character LoRAs for consistency are well understood. Commenter on Matt's thread: "Krea 2 is a better model than ZIT, but ZIT is good enough." Weakness: Turbo gives "basically the same image every time" ([thread](https://www.reddit.com/r/StableDiffusion/comments/1xj7sk5/)). | Krea 2 Community: commercial only under **$1M** revenue ([krea.ai/krea-2-licensing](https://krea.ai/krea-2-licensing)). A 50-seat limit is mentioned by secondary sources only: UNVERIFIED. | **Already on disk**: `krea2_turbo_bf16` (26.3GB) plus the Qwen3-VL-4B bf16 encoder. Draw Things supports it; MLX q8 port exists. | 26GB bf16 |
| 2 | **FLUX 3 Image Klein** | Highest open model on AA for both T2I (1043) and editing (1072). Trending #1 in image-to-image on HF. Reddit is lukewarm: "Fibo 2 Edit is what Klein 3 should've been" (827 pts, [link](https://www.reddit.com/r/StableDiffusion/comments/1xb59yw/)). | FLUX Kommunity: commercial only under **$5M** revenue | `vanch007/FLUX.3-Image-Klein-mlx-bf16` | not measured |
| 3 | **MOSS-Image** (5B, FLUX.2 VAE) | "Moss is the best base model we've gotten yet" (440). Also: "sub 15 seconds per render … really good img2img … Krea2 … can get more technically better results, but MOSS is … 5x faster." The complaints: "body horrors" and a "love of cartoons and blur" ([1](https://www.reddit.com/r/StableDiffusion/comments/1x8ixsy/), [2](https://www.reddit.com/r/StableDiffusion/comments/1xj7sk5/)). A common workflow uses Krea to compose and MOSS to finish. | **Apache-2.0, clean** | MLX 8-bit ports exist (`VisualInference/MOSS-Image-SFT-MLX-8bit`) | about 10GB bf16 (5B params) |

Excluded despite good scores: Qwen-Image-2.1 (the Qwen RESEARCH license grants rights "FOR NON-COMMERCIAL PURPOSES ONLY"), Fibo 2.0 (CC-BY-NC), Ideogram 4 (non-commercial). ZIT is Apache and fast, but AA has it about 100 Elo below Krea 2 and FLUX 3 Klein.

For the Pixar / animated-feature look: Krea 2 with its style library is the strongest pick, and MOSS leans cartoon by default. No head-to-head Pixar benchmark exists: **UNVERIFIED**.

### Image editing / img2img (AA editing, open weights)

| # | Model | Elo | License |
|---|---|---|---|
| — | Fibo 2.0 | 1088 (best) | **CC-BY-NC, excluded** |
| — | Qwen-Image-2.1 | 1081 | **non-commercial, excluded** |
| 1 | FLUX 3 Image Klein | 1072 | under $5M |
| 2 | HunyuanImage 3.0 Instruct (80B) | 1063 | Tencent Hunyuan community license (license text not re-read today: UNVERIFIED); too heavy to be practical |
| 3 | Qwen-Image-Edit-2511 | 991 | **Apache-2.0, clean**. Practitioners call MOSS "incredible at inpainting" ([r/comfyui](https://www.reddit.com/r/comfyui/comments/1xa9cf7/)). |

## 3. Video upscaling, restoration, frame interpolation

Practitioner evidence here is thinner. Most upscaling talk this month is about H3's own Regenerate-2K, which carries the H3 license, or NVIDIA RTX VSR, which needs CUDA.

| # | Model | Why | License | Mac |
|---|---|---|---|---|
| 1 | **SeedVR2** (3B / 7B) | Still the generic restoration upscaler. Big earlier threads ("when an upscaler is so good it feels illegal"). | Apache | **3B fp16 already on disk**. MLX ports: `benc0/SeedVR2-7B-mlx`, `mlx-community/SeedVR2-3B-mlx-int8`. |
| 2 | **Kandinsky 6 VSR** (2-step distilled) | "Upscale is very good" (5090 tester above). Has a ComfyUI node. | MIT | diffusers/MPS: UNVERIFIED |
| 3 | **LTX-2.5 IC-LoRA spatial upscaler** | Used even to "ReDetail" H3 renders ([thread](https://www.reddit.com/r/StableDiffusion/comments/1vo5vnz/)) | LTX (under $10M) | MLX LTX stack already on disk |
| Interp. | **RIFE 4.25** | Default frame interpolator; MIT, and an MLX port exists (`mlx-community/RIFE-4.25`). GIMM-VFI is sharper but carries the S-Lab license (likely non-commercial, not re-read). Modern models render at 24fps natively, so interpolation matters less. | MIT | yes |

## 4. TTS / voice cloning and lip-sync

No clear open "king" with a clean license. The most-hyped options are restricted. Fish Drama-3: "New TTS king" (455 pts), but the license allows commercial use only under $500K and "the voice cloning fidelity is pretty weak … more like a cousin of the reference voice" ([thread](https://www.reddit.com/r/LocalLLaMA/comments/1x6f9p2/)). Breeze-TTS-2 is non-commercial. One practitioner says "the best right now is minimax h3 … You just ignore the video part" ([thread](https://www.reddit.com/r/StableDiffusion/comments/1x27ic7/)), and that is US-banned.

| # | Model | Why | License | Mac | Size |
|---|---|---|---|---|---|
| 1 | **Chatterbox** (what we use) | "Chatterbox runs fine on 10GB and the cloning is scary close for how light it is". Also: "Breeze TTS 2 is the best, chatterbox for voice conversion. But mind the license of breeze" ([thread](https://www.reddit.com/r/StableDiffusion/comments/1x27ic7/)). | MIT | on disk (12GB); MLX ports exist | small |
| 2 | **Qwen3-TTS 1.7B** (Base / VoiceDesign / CustomVoice) | 3.4M downloads. VoiceDesign creates a voice from a text description, which suits invented characters. Has an emotion-tag finetune. | Apache | `mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16` | 1.7B |
| 3 | **VoxCPM2** | About 1M downloads; a steady pick in roundups | Apache | `mlx-community/VoxCPM2-bf16` | small |

Excluded: OmniVoice ("the pre-trained model is licensed under the CC-BY-NC"), Higgs Audio v3 (non-commercial), IndexTTS-2.5 (bilibili license, not read: UNVERIFIED).

**Lip-sync / talking heads:** the practitioner trend is audio-driven video models, not separate lip-sync passes. H3 does native dialogue (banned for us). **LTX-2.5 audio-to-video I2V** has big threads where people sync to an MP3. So: (1) LTX-2.5 audio-conditioned I2V (what we have); (2) InfiniteTalk (Apache, built on Wan 2.1); (3) LatentSync 1.6 (openrail++, what we use) or MuseTalk 1.5 (MIT, MLX port). No fresh head-to-head exists: **UNVERIFIED**.

## 5. Music (score) and sound effects

| # | Music model | Why | License | Mac | Size |
|---|---|---|---|---|---|
| 1 | **MiniMax Music3** (8B global LLM + 0.6B local LLM; up to 5 min) | "Today I have unsubscribed from Suno thanks to Minimax Music" (560 pts, [link](https://www.reddit.com/r/StableDiffusion/comments/1vnpkfk/)). Cinematic ambient score from "A slow, dark, and brooding cinematic ambient score". Downside: instrumental-only is hard ("keeps adding singing"); use the `[Instrumental]` tags. | Community license: free under **$20M**. No territory exclusion (unlike H3). Output-safeguard duties apply only if we host it for others. | full precision under 24GB; audio.cpp GGUF; MLX not found | about 9B |
| 2 | **ACE-Step 1.5 / 1.5-XL-Turbo** (what we use) | Still the MIT workhorse. YuE2 is "a big improvement over ACESTEP 1.5", but YuE2 is CC-BY-NC. | MIT | `roman220220/ACE-Step1.5-sft-MLX-bf16` | small |
| 3 | **Stable Audio 3 small-music** | Short cues and stingers | under $1M | MLX port exists | small |

| # | SFX / foley model | Why | License | Mac |
|---|---|---|---|---|
| 1 | **MOSS-SoundEffect v2.0** (1.3B DiT) | The clean replacement for MMAudio | Apache | PyTorch MPS (not tested) |
| 2 | **Stable Audio 3 small-sfx** | Text-to-SFX, popular on HF | under $1M | `mlx-community/stable-audio-3-small-sfx` |
| 3 | **LTX-2.3 Foley V2A LoRA**, or native audio from Kandinsky 6 / LTX-2.5 | Video-to-audio that stays in sync | LTX / MIT | on our stack |
| (now) | MMAudio | **Weights are CC BY-NC 4.0, "non-commercial purposes only"**. We have to replace it. | ✗ | on disk 11GB |

---

## What we use now vs what we should use

| Job | Now | Should use (license-clean for a US company) |
|---|---|---|
| Video | LTX-2.5 | Bake-off: Kandinsky 6 Pro vs LTX-2.5; Wan Animate 2 for acting/motion transfer. H3 only via paid license or Comfy Cloud. |
| Stills | Z-Image-Turbo | Krea 2 Turbo (already on disk, if revenue is under $1M), otherwise FLUX 3 Klein (under $5M), otherwise MOSS-Image (Apache) |
| Edit | (none specific) | FLUX 3 Klein, falling back to Qwen-Image-Edit-2511 (Apache) |
| Upscale | SeedVR2 3B | SeedVR2 7B MLX; test Kandinsky 6 VSR |
| Interpolation | — | RIFE 4.25 MLX |
| TTS | Chatterbox | Keep Chatterbox; add Qwen3-TTS VoiceDesign for new character voices |
| Lip-sync | LatentSync | LTX-2.5 audio-driven I2V first, LatentSync as touch-up |
| Music | ACE-Step 1.5 | MiniMax Music3 for score, ACE-Step as fallback |
| SFX | MMAudio (non-commercial) | MOSS-SoundEffect v2 + Stable Audio 3 SFX |

## Recommended Story Forge stack

1. **Stills:** Krea 2 Turbo bf16 (already on disk) with a character LoRA per lead. MOSS-Image for variety and finishing passes. FLUX 3 Klein for edits.
2. **Video:** run a 5-shot bake-off of Kandinsky 6 Pro, LTX-2.5 and Wan Animate 2 on the same Krea stills (one talking shot, one walk, one wide shot, one cartoon, one action), scored by `film_qc.py`. If Matt OKs a paid route, add H3 through Comfy Cloud as the quality reference.
3. **Upscale:** SeedVR2 7B, then RIFE only when a model renders below 24fps.
4. **Voice:** Chatterbox clones plus Qwen3-TTS VoiceDesign; lip-sync driven by the video model's audio conditioning.
5. **Score and SFX:** MiniMax Music3 (instrumental tags) or ACE-Step for score; MOSS-SoundEffect v2 for foley. MMAudio retired.

Unknown that decides several of these: Divine Tribe's annual revenue against the $1M (Krea 2, Stable Audio), $5M (FLUX 3 Klein) and $10M (LTX) lines.
