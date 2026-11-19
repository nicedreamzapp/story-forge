import json, sys
from pathlib import Path
import mlx_whisper
P = Path(__file__).resolve().parent.parent
for name in ("theme_1", "theme_2"):
    r = mlx_whisper.transcribe(str(P / f"music/{name}.wav"), path_or_hf_repo="mlx-community/whisper-large-v3-turbo", word_timestamps=True)
    segs = [{"start": round(s["start"], 2), "end": round(s["end"], 2), "text": s["text"].strip()} for s in r["segments"]]
    (P / f"music/{name}_words.json").write_text(json.dumps({"segments": segs, "words": [w for s in r["segments"] for w in s.get("words", [])]}, indent=1, default=float))
    print(name); [print(f"  {s['start']:5.1f}-{s['end']:5.1f} {s['text']}") for s in segs]
