#!/usr/bin/env python3
"""things_we_remember voices: Qwen3-TTS VoiceDesign (Apache-2.0, bf16, local), 4 untouched takes per line + one
reference passage per character (for ChatterBox casting in later cuts). No stretch, no pitch."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path.home() / "SongForgeM5"))
import mem_client, numpy as np, soundfile as sf, mlx.core as mx
from mlx_audio.tts.utils import load_model
P = Path(__file__).resolve().parent
CAST = {
 "claire": "A woman in her late thirties, American, soft warm mid-range voice, tired and uneasy, a nervous half laugh, quiet and intimate, close to the microphone.",
 "ruth": "An old woman in her mid seventies, American, thin fragile slightly raspy voice, slow, quiet and grave, heavy with sorrow, close to the microphone.",
 "lily": "A seven-year-old little girl, American, a small high child's voice, calm and matter-of-fact, flat and eerie, quiet, close to the microphone.",
 "daniel": "A five-year-old little boy, a tiny high child's voice, breathy hushed whisper, sad and lonely, very close to the microphone.",
 "rememberer": "A man in his fifties, American, soft warm gentle baritone, slow and tender, loving like remembering an old friend, almost a whisper, very calm, close to the microphone.",
}
REF = "The kitchen always smelled like rain and bread in the morning, and the radio played old songs nobody else remembered."
LINES = json.load(open(P / "lines.json"))
with mem_client.reserve("qwen3-tts twr voices", 10, honest=False):
    m = load_model("mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16")
    def say(text, desc, seed, out):
        if out.exists(): return
        mx.random.seed(seed)
        a = np.concatenate([np.array(r.audio) for r in m.generate(text=text, instruct=desc, temperature=0.8, lang_code="english")])
        sf.write(str(out), a, 24000); print("done", out.name, round(len(a)/24000, 2), flush=True)
    for i, (ch, t) in LINES.items():
        for seed in (11, 23, 37, 51):
            say(t, CAST[ch], seed, P / "pieces" / f"{i}_s{seed}.wav")
    for ch, d in CAST.items():
        say(REF, d, 7, P / "refs" / f"twr_{ch}_ref.wav")
print("GEN_DONE")
