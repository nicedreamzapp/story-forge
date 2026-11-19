#!/bin/bash
# narrator (Kokoro Heart, as v3's N1) + Doug's one new line (ChatterBox wr3_doug, 2 seeds); whisper + durations after
cd "$(dirname "$0")/.."
i=0; while IFS='|' read -r id text; do
  [ -f "voices/v4/$id.wav" ] || SPEAK_OUT="voices/v4/$id.wav" SPEAK_SPEED=1.0 speak-heart "$text" >/dev/null 2>&1
done <<'LINES'
N01|This is Doug. Doug used to hunt bears.
N02|Not because he wanted to. His owner made him.
N03|One night, his nose found a bear.
N04|But this bear wasn't hurting anybody. He was saving a fox.
N05|So Doug led his owner away from the bear...
N06|...right into a ditch.
N07|Then he went back.
N08|That bear was Hank. Doug never hunted again.
N09|Now they rescue animals.
N10|A fire wagon, and a crew that's all animals.
LINES
~/chatterbox-env/bin/python - <<'PY'
import sys, torch, torchaudio
from pathlib import Path
sys.path.insert(0, str(Path.home() / "AI/videopipe/bin")); from character_voice import VOICES
from chatterbox.tts import ChatterboxTTS
m = ChatterboxTTS.from_pretrained(device="mps"); v = VOICES["wr3_doug"]
for s in (101, 303):
    out = Path(f"voices/v4/D01_raw_s{s}.wav")
    if out.exists(): continue
    torch.manual_seed(s); wav = m.generate("Huh. That bear is... cool.", exaggeration=0.35, cfg_weight=0.5, audio_prompt_path=v["ref"])
    torchaudio.save(str(out), wav.cpu(), m.sr)
PY
echo "$(date +%T) v4 voices done" >> voices/v4/log.txt
