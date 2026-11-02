#!/usr/bin/env python3
"""THE LAST SIGNAL v2c (2026-11-02, Matt approved "Fix all three"): fix the cuts qc_cuts still flagged in v2b.
  c06b_crew_walk : new R07 K6 clip (locked-off camera, the two walk at the lens and grow in frame), Refine + face lock.
  c11_yanked / c11b_yanked : same R13 clip, face-locked to canon/crewmate.png (c11 reuses its v2 Refine output; c11b,
                   under 0.9 s, gets Refine for the first time).
  c07_handwriting: false flag (a hand on stone, no face; the detector reads fingers as a face) - left as is.
Every other segment, the timing and both audio streams are copied from v2b. Outputs final/LAST_SIGNAL_v2c(.mp4|_51|_1080p).
Run: ~/AI/ComfyUI/venv/bin/python tools/recut_v2c.py renders_v2_krea_k6/clips/walk_v2c/seedNNNN.mp4   (or --c11-only first)"""
import json, shutil, subprocess, sys
from pathlib import Path

sys.argv, ARGS = sys.argv[:1], sys.argv[1:]
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path.home() / "SongForgeM5"))
import redo_v2 as R
from mem_client import reserve_ex

V2, FPS, F = R.V2, R.FPS, R.V2 / "final"
ONLY_C11 = ARGS[0] == "--c11-only"   # pre-pass: Refine + lock the yank cuts while the walk clip is still queued
NEWCLIP = {} if ONLY_C11 else {"c06b_crew_walk": Path(ARGS[0]).resolve()}
# c11b's first frame is a near-profile head turn face_lock leaves alone (|yaw| > 60) and it read 0.34 against the locked
# frames; start 2 frames later, inside the Refined handles, so the cut is 14 locked frames. Same length, same timing.
SHIFT = {"c11b_yanked": 2}
FIX = ("c11_yanked", "c11b_yanked") if ONLY_C11 else ("c06b_crew_walk", "c11_yanked", "c11b_yanked")
B = F / "segs_v2c"
for d in ("h", "scope", "up", "locked", "4k"): (B / d).mkdir(parents=True, exist_ok=True)
e = json.load(open(F / "edl_v2b_graded.json"))
H = {m["seg"]: m for m in json.load(open(F / "segs/handles.json"))}
new = {}

def refine_locked(src, out, n):
    while True:   # same honest 64 GB lease as redo_v2; queue, never push past the guard
        with reserve_ex("ltx25-refine", 64) as (lid, status):
            if status == "refused": print("refine lease refused, retry in 60s", flush=True); R.time.sleep(60); continue
            return R.refine(src, out, n)

for k, c in enumerate(e["cuts"]):
    if c["id"] not in FIX: continue
    nm, n = f"{k:02d}_{c['id']}.mp4", c["frames"]
    up = B / "up" / nm
    old_up = F / "segs/up" / nm
    if c["id"] not in NEWCLIP and old_up.exists() and (F / "segs/up" / (nm[:-4] + ".refine.json")).exists():
        shutil.copy2(old_up, up); m = H[nm]   # unchanged clip, already Refined in v2: reuse it
    else:
        clip = NEWCLIP.get(c["id"], Path(c["src"])); T = R.nfr(clip)
        f0 = min(round(c["in"] * FPS), T - n)
        c["src"], c["in"], c["clip_frames"] = str(clip), round(f0 / FPS, 4), T
        h0, h1 = max(0, f0 - 4), min(T - 1, f0 + n - 1 + 4)
        R.ff("-i", clip, "-vf", f"select='between(n\\,{h0}\\,{h1})',setpts=N/{FPS}/TB", "-an", "-c:v", "libx264", "-crf", "4", "-pix_fmt", "yuv420p", B / "h" / nm)
        R.ff("-i", B / "h" / nm, "-vf", "crop=832:348:0:66", "-c:v", "libx264", "-crf", "4", "-pix_fmt", "yuv420p", B / "scope" / nm)
        m = {"seg": nm, "pre": f0 - h0, "n": n, "post": h1 - (f0 + n - 1)}
        if not up.exists():
            tot = R.nfr(B / "scope" / nm); rc, res = refine_locked(B / "scope" / nm, up, tot)
            R.log(f"[v2c refine] {nm}: {tot} frames, rc {rc}, out {R.nfr(up) if up.exists() else 0}")
    sh = SHIFT.get(c["id"], 0)
    if sh:
        m = dict(m, pre=m["pre"] + sh); c["in"] = round(c["in"] + sh / FPS, 4)
        assert m["pre"] + n <= R.nfr(up), f"{nm}: shift {sh} runs past the handles"
    lk = B / "locked" / nm
    r = subprocess.run([str(R.COMFY_PY), str(R.SF / "pipeline-tools/face_lock.py"), str(R.P), c["id"], str(up), str(lk)],
                       capture_output=True, text=True, cwd=str(R.SF))
    R.log(f"[v2c face_lock] {c['id']} rc {r.returncode} :: {(r.stdout or r.stderr).strip()[-200:]}")
    if r.returncode or not lk.exists(): sys.exit(f"face_lock failed on {nm}")
    c["upscale"], c["face_lock"] = "ltx-2.5 refine 1920x800 + lanczos", True
    f = (f"[0:v]trim=start_frame={m['pre']}:end_frame={m['pre']+n},setpts=N/{FPS}/TB,"
         f"scale={R.FW}:{R.VH}:flags=lanczos,format=gbrp")
    if c["id"] in R.BLOOM or c["section"] == "strobe": f += "," + R.bloom_chain(R.BLOOM.get(c["id"], 0.5))
    f += f",format=yuv420p,pad={R.FW}:{R.FH}:0:{R.BAR}:black[v]"
    pre, o = B / "4k" / ("pre_" + nm), B / "4k" / nm
    R.ff("-i", lk, "-filter_complex", f, "-map", "[v]", "-frames:v", n, "-r", FPS, "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", pre)
    subprocess.run([str(R.SF / "bin/grade"), str(pre), str(o), "--lut", c["lut"], "--grain", str(R.GRAIN), "--scope"], check=True); pre.unlink()
    assert R.nfr(o) == n, f"{nm}: {R.nfr(o)} frames != {n}"
    new[nm] = o; R.log(f"[v2c finish] {nm} n {n}")
if ONLY_C11: sys.exit(0)
lst = []
for l in (F / "segs_v2b/list.txt").read_text().splitlines():
    nm = Path(l.split("'")[1]).name if l.startswith("file") else None
    lst.append(f"file '{new[nm]}'" if nm in new else l)
(B / "list.txt").write_text("\n".join(lst) + "\n")
pic = F / "picture_4k_v2c.mp4"
R.ff("-f", "concat", "-safe", "0", "-i", B / "list.txt", "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", FPS, pic)
assert R.nfr(pic) == R.nfr(F / "picture_4k_v2b.mp4"), "picture frame count changed"
for src, dst in (("LAST_SIGNAL_v2b.mp4", "LAST_SIGNAL_v2c.mp4"), ("LAST_SIGNAL_v2b_51.mp4", "LAST_SIGNAL_v2c_51.mp4")):   # same audio, untouched
    R.ff("-i", pic, "-i", F / src, "-map", "0:v", "-map", "1:a", "-c", "copy", "-movflags", "+faststart", "-metadata", "title=THE LAST SIGNAL", F / dst)
R.ff("-i", F / "LAST_SIGNAL_v2c.mp4", "-vf", "scale=1920:1080:flags=lanczos", "-c:v", "libx264", "-crf", "17", "-preset", "slow",
     "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", F / "LAST_SIGNAL_v2c_1080p.mp4")
json.dump(e, open(F / "edl_v2c_graded.json", "w"), indent=1)
for x in ("LAST_SIGNAL_v2c.mp4", "LAST_SIGNAL_v2c_51.mp4", "LAST_SIGNAL_v2c_1080p.mp4"):
    o = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name,width,height,channels", "-of", "compact", str(F / x)]).decode()
    R.log(f"[v2c deliver] {x} {o.strip().replace(chr(10), ' | ')}")
