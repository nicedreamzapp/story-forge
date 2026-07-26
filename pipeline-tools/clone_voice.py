#!/usr/bin/env python3
"""Character voice cloning for Story Forge — chatterbox-turbo on MPS.

Clones a voice from a short reference wav (~8-15s of the character speaking)
and speaks any line in that voice. Replaces/augments Piper for character
dialogue (Piper stays fine for narrator).

Usage:
  ~/chatterbox-env/bin/python3 clone_voice.py REF.wav "line to speak" OUT.wav
  ~/chatterbox-env/bin/python3 clone_voice.py REF.wav --lines lines.txt OUTDIR/

Notes (hard-won, don't re-derive):
- Env: ~/chatterbox-env (chatterbox-tts 0.1.7 + resemble-perth + setuptools<81;
  setuptools>=81 removes pkg_resources and silently nulls the watermarker ->
  "'NoneType' object is not callable" at load).
- MPS can't do float64: chatterbox feeds float64 arrays into S3Tokenizer and
  VoiceEncoder on some inputs. The cast32 patches below fix it; without them
  you get "Cannot convert a MPS Tensor to float64 dtype".
- Reference wav: convert to 16-bit PCM first (ffmpeg -ar 24000 -ac 1 -c:a
  pcm_s16le). ~9s of reference is enough; 2-3s is too short.
- Speed on M5 Max: ~10-15s per line after the one-time model load (~8s).
"""
import sys, os
import numpy as np
import torch, torchaudio


def cast32(w):
    if isinstance(w, torch.Tensor):
        return w.float()
    if isinstance(w, np.ndarray):
        return np.asarray(w, dtype=np.float32)
    return w


def patch_mps_float64():
    from chatterbox.models.s3tokenizer.s3tokenizer import S3Tokenizer
    from chatterbox.models.voice_encoder.voice_encoder import VoiceEncoder
    _sf = S3Tokenizer.forward
    S3Tokenizer.forward = lambda self, wavs, *a, **k: _sf(
        self, [cast32(w) for w in wavs] if isinstance(wavs, list) else cast32(wavs), *a, **k)
    _vf = VoiceEncoder.embeds_from_wavs
    VoiceEncoder.embeds_from_wavs = lambda self, wavs, *a, **k: _vf(
        self, [cast32(w) for w in wavs], *a, **k)


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    ref = sys.argv[1]

    patch_mps_float64()
    from chatterbox.tts_turbo import ChatterboxTurboTTS
    model = ChatterboxTurboTTS.from_pretrained(device="mps")

    if sys.argv[2] == "--lines":
        outdir = sys.argv[4] if len(sys.argv) > 4 else "."
        os.makedirs(outdir, exist_ok=True)
        with open(sys.argv[3]) as f:
            lines = [l.strip() for l in f if l.strip()]
        for i, line in enumerate(lines, 1):
            wav = model.generate(line, audio_prompt_path=ref)
            out = os.path.join(outdir, f"line_{i:02d}.wav")
            torchaudio.save(out, wav, model.sr)
            print(f"OK {out} ({wav.shape[-1]/model.sr:.1f}s): {line[:60]}")
    else:
        line, out = sys.argv[2], sys.argv[3]
        wav = model.generate(line, audio_prompt_path=ref)
        torchaudio.save(out, wav, model.sr)
        print(f"OK {out} ({wav.shape[-1]/model.sr:.1f}s)")


if __name__ == "__main__":
    main()
