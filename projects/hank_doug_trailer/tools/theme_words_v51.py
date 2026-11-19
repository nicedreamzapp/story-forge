#!/usr/bin/env python3
"""theme_words_v51.py NAME... — whisper word timings for regenerated themes (music/NAME.wav -> music/NAME_words.json),
same as theme_check.py, plus the cut points mix_v51 needs: pickup "Here we go!" (sting), "[Verse 1]" first word,
and the title phrase "It's Hank and Doug's Wild Rescue!" (start of "It's", end of "Rescue")."""
import json, sys
from pathlib import Path
import mlx_whisper
P = Path(__file__).resolve().parent.parent
for name in sys.argv[1:]:
    r = mlx_whisper.transcribe(str(P / f"music/{name}.wav"), path_or_hf_repo="mlx-community/whisper-large-v3-turbo", word_timestamps=True)
    segs = [{"start": round(s["start"], 2), "end": round(s["end"], 2), "text": s["text"].strip()} for s in r["segments"]]
    words = [w for s in r["segments"] for w in s.get("words", [])]
    (P / f"music/{name}_words.json").write_text(json.dumps({"segments": segs, "words": words}, indent=1, default=float))
    print(name); [print(f"  {s['start']:5.1f}-{s['end']:5.1f} {s['text']}") for s in segs]
    norm = lambda w: w.strip().lower().strip("'!?,.\"")
    cuts = {}
    for i, w in enumerate(words):
        n = norm(w["word"]); nxt = [norm(x["word"]) for x in words[i + 1:i + 4]]
        if n == "here" and nxt[:2] == ["we", "go"] and "sting" not in cuts: cuts["sting"] = [round(w["start"], 2), round(words[i + 2]["end"], 2)]
        if n == "when" and nxt[:2] == ["a", "goat's"] and "verse" not in cuts: cuts["verse"] = round(w["start"], 2)
        if n == "it's" and nxt[:1] == ["hank"]: cuts["t_its"] = round(w["start"], 2)
        if n == "rescue" and "t_its" in cuts and "rescue_end" not in cuts and w["start"] > cuts["t_its"]: cuts["rescue_end"] = round(w["end"], 2)
    print("  cuts:", json.dumps(cuts))
    (P / f"music/{name}_cuts.json").write_text(json.dumps(cuts, indent=1))
