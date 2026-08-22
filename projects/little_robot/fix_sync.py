#!/usr/bin/env python3
"""Per-line VO scheduling: pin each narration sentence to its intended shot.
Rebuilds audio/sceneN_vo.wav as full-scene-length tracks with each sentence
pasted at the start of its target shot (soft constraint: never overlaps the
previous line). Pure-wave implementation, then assemble.py re-muxes."""
import json, wave, sys
from pathlib import Path

PROJ = Path.home() / "Desktop/PROJECTS/story-forge/projects/little_robot"
PIECES = PROJ / "audio/vo_pieces"
data = json.loads((PROJ / "shots.json").read_text())

# shot timeline per scene (clip durations as assembled; s48 extended +8 credits)
def clip_dur(sid):
    import subprocess
    special = {"s06": "s06_titled.mp4", "s48": "s48_credits.mp4"}
    src = PROJ/"final"/special[sid] if sid in special else PROJ/"clips"/f"{sid}.mp4"
    if not src.exists():
        src = PROJ/"clips"/f"{sid}.mp4"
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                        "-of","csv=p=0",str(src)], capture_output=True, text=True)
    return float(r.stdout.strip())

SCENES = {1:[],2:[],3:[],4:[],5:[]}
for sh in data["shots"]:
    SCENES[data["stills"][sh["still"]]["scene"]].append(sh["id"])

starts = {}  # (scene, shot_id) -> start time in scene
for sc, ids in SCENES.items():
    t = 0.0
    for i in ids:
        starts[(sc,i)] = t
        t += clip_dur(i)
    starts[(sc,"_end")] = t

# line -> target shot mapping (authored against narration.txt order)
MAP = {
 1: ["s01","s02","s03","s03","s04","s05"],
 2: ["s07","s08","s09","s10","s11","s11","s12","s13","s14"],
 3: ["s15","s16","s17","s18","s19","s19","s20","s21","s22","s23","s24","s25"],
 4: ["s26","s28","s29","s30","s30","s30","s31","s31","s32","s33","s34","s35","s36"],
 5: ["s37","s38","s39","s39","s40","s41","s42","s43","s44","s45","s46","s47","s47"],
}

GAP = 0.35   # min gap between lines
LEAD = 0.4   # lead-in after shot start
report = []
for sc, targets in MAP.items():
    pieces = sorted(PIECES.glob(f"sc{sc}_*.wav"))
    assert len(pieces) == len(targets), f"scene{sc}: {len(pieces)} pieces vs {len(targets)} targets"
    with wave.open(str(pieces[0])) as w0:
        params = w0.getparams()
    fr, sw, ch = params.framerate, params.sampwidth, params.nchannels
    scene_len = starts[(sc,"_end")]
    buf = bytearray(int(scene_len * fr) * sw * ch)
    prev_end = 0.0
    for (piece, tgt) in zip(pieces, targets):
        with wave.open(str(piece)) as w:
            frames = w.readframes(w.getnframes())
            pdur = w.getnframes() / fr
        t0 = max(prev_end + GAP, starts[(sc,tgt)] + LEAD)
        t0 = min(t0, max(0.0, scene_len - pdur - 0.3))
        off = int(t0 * fr) * sw * ch
        end = off + len(frames)
        if end > len(buf):
            frames = frames[:len(buf)-off]
            end = len(buf)
        buf[off:end] = frames
        sh_at = [i for i in SCENES[sc] if starts[(sc,i)] <= t0][-1]
        flag = "✓" if sh_at == tgt else f"≈({sh_at})"
        report.append(f"sc{sc} {piece.stem}: {t0:6.1f}s -> {tgt} {flag}")
        prev_end = t0 + pdur
    out = PROJ / f"audio/scene{sc}_vo.wav"
    with wave.open(str(out), "wb") as wout:
        wout.setparams(params)
        wout.writeframes(bytes(buf))

print("\n".join(report))
print("SYNC_FIXED")
