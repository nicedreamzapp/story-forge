#!/usr/bin/env python3
"""New lines for the trailer/short/parts: same Qwen3-TTS VoiceDesign cast as gen_narration.py (teaser), plus TOM and
LILY3 (Lily at three, home video). 4 untouched takes per line, no stretch, no pitch.  gen_more.py lines_X.json"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path.home() / "SongForgeM5"))
import mem_client, numpy as np, soundfile as sf, mlx.core as mx
from mlx_audio.tts.utils import load_model
P = Path(__file__).resolve().parent
sys.path.insert(0, str(P))
from gen_narration_cast import CAST
LINES = json.load(open(sys.argv[1]))
with mem_client.reserve("qwen3-tts twr more voices", 10, honest=False):
    m = load_model("mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16")
    for i, (ch, t) in LINES.items():
        for seed in (11, 23, 37, 51):
            out = P / "pieces" / f"{i}_s{seed}.wav"
            if out.exists(): continue
            mx.random.seed(seed)
            a = np.concatenate([np.array(r.audio) for r in m.generate(text=t, instruct=CAST[ch], temperature=0.8, lang_code="english")])
            sf.write(str(out), a, 24000); print("done", out.name, round(len(a) / 24000, 2), flush=True)
print("GEN_DONE")
