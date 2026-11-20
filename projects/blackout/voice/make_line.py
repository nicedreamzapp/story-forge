import sys, torch, torchaudio
from chatterbox.tts import ChatterboxTTS
REF = "/Users/dtribe/Desktop/PROJECTS/avatar-assets/matt-inputs/matt_real_ref.wav"
LINE = "It never needed the internet."
out = sys.argv[1]
m = ChatterboxTTS.from_pretrained(device="mps")
for i, seed in enumerate([0, 7, 21], 1):
    torch.manual_seed(seed)
    wav = m.generate(LINE, audio_prompt_path=REF, exaggeration=0.4, cfg_weight=0.5)
    torchaudio.save(f"{out}/matt_line_take{i}.wav", wav.cpu(), m.sr)
    print("take", i)
