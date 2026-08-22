# 🙏 Credits

None of this starts from scratch. Here's whose work this is built on, and under what terms.

| Project | What it does here | By | License |
|---|---|---|---|
| 🖼️ [FLUX](https://github.com/black-forest-labs/flux) | Stills and keyframes | Black Forest Labs | code Apache-2.0 — **see the weights note below** |
| 🎞️ [LTX-Video](https://github.com/Lightricks/LTX-Video) | Image-to-video motion | Lightricks | Apache-2.0 |
| 🌊 [Wan](https://github.com/Wan-Video/Wan2.2) | The other motion path, and the 1-step distill target | Alibaba's Wan team | Apache-2.0 |
| 🗣️ [Piper](https://github.com/rhasspy/piper) | Narration and character voices | [Michael Hansen](https://github.com/synesthesiam) and the Rhasspy project | MIT |
| 🎼 [ACE-Step](https://github.com/ace-step/ACE-Step) | Original score | The ACE-Step team | Apache-2.0 |
| 👄 [Rhubarb Lip Sync](https://github.com/DanielSWolf/rhubarb-lip-sync) | Mouth shapes from audio | [Daniel Wolf](https://github.com/DanielSWolf) | MIT |
| 🎬 [FFmpeg](https://ffmpeg.org/) | Every cut, mux and grade | The FFmpeg project | LGPL/GPL depending on build |

## A note on the FLUX weights

The FLUX **code** is Apache-2.0, but the weights are licensed separately. This pipeline
currently references `flux1-dev`, whose weights carry the **FLUX.1 [dev] Non-Commercial
License Agreement**. That is fine for personal and research work, and it means anything
rendered with those weights should not be sold.

If you want commercial output, **[FLUX.1-schnell](https://huggingface.co/black-forest-labs/FLUX.1-schnell)**
is Apache-2.0 and its model card states commercial use is permitted. Swapping to schnell is
the supported path for that.

Rhubarb is worth calling out too: its license says the lip-sync data it produces belongs to
you outright, so films made with this pipeline carry no obligation from that side.

---

If your work is listed here and you'd like the wording changed, or if something's
missing or wrong, open an issue and I'll fix it.
