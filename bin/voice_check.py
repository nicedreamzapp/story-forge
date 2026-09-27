#!/usr/bin/env python3
"""voice_check.py — measure speaker similarity so the agent can catch a
character sounding like another character (e.g., bear == Matt) WITHOUT Matt
having to listen. Cosine sim 1.0 = same speaker; lower = more distinct.
Run with ~/chatterbox-env/bin/python.
  voice_check.py REF.wav CANDIDATE.wav [CANDIDATE2.wav ...]
"""
import sys, numpy as np, librosa
from chatterbox.models.voice_encoder import VoiceEncoder
ve = VoiceEncoder()
def emb(p):
    w,sr = librosa.load(p, sr=16000)
    return ve.embeds_from_wavs([w], 16000, as_spk=True).reshape(-1)
ref = sys.argv[1]; re = emb(ref); re = re/np.linalg.norm(re)
print(f"REF = {ref.split('/')[-1]}")
for c in sys.argv[2:]:
    ce = emb(c); ce = ce/np.linalg.norm(ce)
    sim = float(np.dot(re, ce))
    verdict = "SAME-ish (TOO CLOSE)" if sim>0.75 else ("distinct" if sim<0.6 else "borderline")
    print(f"  sim={sim:.3f}  {verdict}  <- {c.split('/')[-1]}")
