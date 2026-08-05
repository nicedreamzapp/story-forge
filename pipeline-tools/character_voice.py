#!/usr/bin/env python3
"""character_voice.py — generate a character's spoken line via ChatterBox TTS.

Run with the chatterbox env:
  ~/chatterbox-env/bin/python character_voice.py --character hank --line "..." --out out.wav

Casting (locked 2026-05-25):
  hank (bear) = ChatterBox built-in voice (NO reference clip — reproducible, not Matt)
  doug (dog)  = Matt's cloned voice (reference: StoryForge-voices/voice2_matt.wav)

Add a character: drop a clean 3-10s reference wav and add an entry below.
"""
import argparse
from pathlib import Path

import torch
import torchaudio
from chatterbox.tts import ChatterboxTTS

VOICES_DIR = Path.home() / "Desktop" / "StoryForge-voices"

VOICES = {
    # bear: Tone 4 = the BUILT-IN voice with NO clone + seed 44 (Matt's pick).
    # Do NOT clone hank.wav — cloning that synthetic clip drifts toward Matt's
    # voice (collides with Doug). No reference + fixed seed = distinct & stable.
    "hank": {"ref": None,
             "exaggeration": 0.7, "cfg": 0.4, "seed": 44},
    # dog: Matt's own voice
    "doug": {"ref": str(VOICES_DIR / "voice2_matt.wav"),
             "exaggeration": 0.7, "cfg": 0.4, "seed": 0},
    # spare casting pool — distinct voices Matt liked, for new characters
    "voiceA": {"ref": str(VOICES_DIR / "spare_voiceA.wav"),
               "exaggeration": 0.7, "cfg": 0.4, "seed": 0},
    "voiceB": {"ref": str(VOICES_DIR / "spare_voiceB.wav"),
               "exaggeration": 0.7, "cfg": 0.4, "seed": 0},
    "voiceC": {"ref": str(VOICES_DIR / "spare_voiceC.wav"),
               "exaggeration": 0.7, "cfg": 0.4, "seed": 0},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--character", required=True, choices=sorted(VOICES.keys()))
    ap.add_argument("--line", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--exaggeration", type=float, default=None)
    ap.add_argument("--cfg", type=float, default=None)
    args = ap.parse_args()

    v = VOICES[args.character]
    ex = args.exaggeration if args.exaggeration is not None else v["exaggeration"]
    cfg = args.cfg if args.cfg is not None else v["cfg"]
    if v.get("seed"):
        torch.manual_seed(v["seed"])

    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    m = ChatterboxTTS.from_pretrained(device=dev)
    kw = {"exaggeration": ex, "cfg_weight": cfg}
    if v["ref"]:
        kw["audio_prompt_path"] = v["ref"]
    wav = m.generate(args.line, **kw)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    torchaudio.save(args.out, wav.cpu() if hasattr(wav, "cpu") else wav, m.sr)
    print(f"[character_voice] {args.character} -> {args.out}")


if __name__ == "__main__":
    main()
