import json, re, subprocess
from pathlib import Path
F = Path(__file__).resolve().parent.parent
W = json.loads((F/"vo/words.json").read_text()); P = json.loads((F/"promo.json").read_text())
V = {l["line"]: l["spoken"] for l in json.loads((F/"vo/voice.json").read_text())["lines"]}
norm = lambda w: re.sub(r"[^a-z0-9']", "", w.lower()).strip("'")
bound = lambda L: 0.0 if L == 1 else next(l for l in W["lines"] if l["line"] == L)["start"]
def T(L, w, nth=1):
    h = [x for x in W["words"] if x["line"] == L and norm(x["word"]) == norm(w)]; return h[nth-1]["start"] - bound(L)
SLAM = W["words"][-1]["end"] + P["endcard"].get("slam_after", 0.15)
def span(L):
    n = [l for l in W["lines"] if l["line"] == L + 1]
    return (n[0]["start"] if n else SLAM) - bound(L)
CUT = {1: ("A", 1), 2: ("Two", 1), 3: ("And", 1), 5: ("The", 2), 6: ("So", 1), 7: ("Outputs", 1), 8: ("And", 1),
       9: ("We", 1), 10: ("We", 2), 11: ("And", 1), 12: ("License", 1), 14: ("Read", 1)}
SENT = {1: "a ping of curiosity: something new just landed", 2: "rising excitement, 'oh, that's clever'",
        3: "excitement peaks: fast AND small", 4: "'this could be the one'", 5: "a calm brake: the builder's habit kicks in",
        6: "curiosity, following the trail", 7: "the reveal: 'there it is'", 8: "a clear, settled decision, no drama",
        9: "confirmation: it did not fit anyway", 10: "relief and pride in what we have", 11: "warmth, Matt's real reaction",
        12: "'oh, that's a smart system'", 13: "an open door, goodwill toward MiniMax", 14: "a confident landing, the takeaway"}
MOVES = ["push-in", "pan-right", "pull-out", "pan-left"]
kb, cov, sel, cues = [], [], [], []
for L in range(1, 15):
    kb.append({"id": f"l{L:02d}_kb_still", "line": L, "setup": "slow camera move over the finished diagram (still)",
               "still": f"refs/l{L:02d}_still.png", "move": MOVES[L % 4], "seconds": 8})
    cov.append({"line": L, "text": V[L], "sentiment": SENT[L], "setups": [
        {"setup": "code-rendered motion A, first sentence beats on their words", "source": "manim", "file": f"acquired/l{L:02d}_manim_a_1.mp4"},
        {"setup": "code-rendered motion B, alternate layout, later sentence beats", "source": "manim", "file": f"acquired/l{L:02d}_manim_b_1.mp4"},
        {"setup": "camera move over the finished diagram", "source": "still-kb", "still": f"refs/l{L:02d}_still.png"}]})
    bin_ = round(T(L, *CUT[L]), 3) if L in CUT else 0.0
    sp = round(span(L) + 0.4, 3)
    aout = round(bin_ + 0.4, 3) if L in CUT else sp
    sel.append({"line": L, "takes": [
        {"cid": f"l{L:02d}_manim_a_1", "rank": 1, "in": 0.0, "out": aout, "why": "every beat lands on its word for the opening sentence; strongest read"},
        {"cid": f"l{L:02d}_manim_b_1", "rank": 2, "in": bin_, "out": sp, "why": "the alternate layout carries the later sentence; in = its cut word's time so beats stay on words"},
        {"cid": f"l{L:02d}_kb_still_1", "rank": 3, "in": 0.0, "out": 8.0, "why": "a still move over the finished diagram, a safe fallback"}]})
    if L in CUT:
        w, n = CUT[L]; cues.append({"line": L, "word": w, "nth": n, "kind": "cut"})
P["kb"] = kb
(F/"promo.json").write_text(json.dumps(P, indent=1))
(F/"coverage.json").write_text(json.dumps({"target_runtime": round(SLAM + P["endcard"]["dur"]), "lines": cov}, indent=1))
(F/"selects.json").write_text(json.dumps({"lines": sel}, indent=1))
(F/"cues.json").write_text(json.dumps({"cues": cues}, indent=1))
print("ok", [(c["line"], c["word"]) for c in cues])
