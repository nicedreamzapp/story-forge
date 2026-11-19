import json, sys, subprocess
from pathlib import Path
import mlx_whisper
P = Path(__file__).resolve().parent.parent
res = {}
for f in sorted((P / "voices/raw").glob("*.wav")):
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)], capture_output=True, text=True).stdout.strip() or 0)
    r = mlx_whisper.transcribe(str(f), path_or_hf_repo="mlx-community/whisper-large-v3-turbo")
    res[f.name] = {"dur": round(dur, 2), "heard": r["text"].strip()}
    print(f"{f.name:34s} {dur:5.2f}s  {r['text'].strip()}", flush=True)
(P / "voices/raw_check.json").write_text(json.dumps(res, indent=1))
