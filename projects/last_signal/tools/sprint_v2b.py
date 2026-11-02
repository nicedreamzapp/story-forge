#!/usr/bin/env python3
"""THE LAST SIGNAL v2b (2026-11-02, Matt-approved): redo ONLY the captain's running shot.
v2's R17 sprint clip had the camera tracking back at her speed, so she ran in place, and its two cuts
(c14b_sprint 0.71 s, c15c_sprint 0.50 s) are under 0.9 s, so they never got an upscale and never got the face lock.
This takes the new R17 K6 clip (locked-off camera, she sprints at the lens and grows in frame), re-cuts those two
cuts at the same length and position, upscales them with LTX-2.5 Refine (face cuts rule), face-locks them to
canon/captain.png like c06b/c09, finishes them with the v2 recipe, and splices them into v2's 4K picture.
Every other segment, the timing and the audio streams are copied untouched from v2. Outputs:
  final/LAST_SIGNAL_v2b.mp4, final/LAST_SIGNAL_v2b_51.mp4, final/LAST_SIGNAL_v2b_1080p.mp4 (v2 files are left as is).
Run: ~/AI/ComfyUI/venv/bin/python tools/sprint_v2b.py renders_v2_krea_k6/clips/sprint_v2b/seedNNNN.mp4 [in_c14b in_c15c]"""
import json, shutil, subprocess, sys
from pathlib import Path

sys.argv, ARGS = sys.argv[:1], sys.argv[1:]
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path.home() / "SongForgeM5"))
import redo_v2 as R
from mem_client import reserve_ex

V2, FPS = R.V2, R.FPS
CLIP = Path(ARGS[0]).resolve()
INS = dict(zip(("c14b_sprint", "c15c_sprint"), map(float, ARGS[1:3])))
B = V2 / "final/segs_v2b"
for d in ("h", "scope", "up", "locked", "4k"): (B / d).mkdir(parents=True, exist_ok=True)
F = V2 / "final"
e = json.load(open(F / "edl_v2_graded.json"))
T = R.nfr(CLIP)
H = {m["seg"]: m for m in json.load(open(V2 / "final/segs/handles.json"))}
new = {}
for k, c in enumerate(e["cuts"]):
    if c["id"] not in ("c14b_sprint", "c15c_sprint"): continue
    nm, n = f"{k:02d}_{c['id']}.mp4", c["frames"]
    f0 = min(round(INS.get(c["id"], c["in"]) * FPS), T - n)
    c["src"], c["in"], c["clip_frames"] = str(CLIP), round(f0 / FPS, 4), T
    h0, h1 = max(0, f0 - 4), min(T - 1, f0 + n - 1 + 4)
    R.ff("-i", CLIP, "-vf", f"select='between(n\\,{h0}\\,{h1})',setpts=N/{FPS}/TB", "-an", "-c:v", "libx264", "-crf", "4", "-pix_fmt", "yuv420p", B / "h" / nm)
    R.ff("-i", B / "h" / nm, "-vf", "crop=832:348:0:66", "-c:v", "libx264", "-crf", "4", "-pix_fmt", "yuv420p", B / "scope" / nm)
    m = {"seg": nm, "pre": f0 - h0, "n": n, "post": h1 - (f0 + n - 1)}; H[nm] = m
    tot = R.nfr(B / "scope" / nm)
    up = B / "up" / nm
    if not up.exists():   # LTX-2.5 Refine (Matt: faces get Refine, not SeedVR2), same honest 64 GB lease as redo_v2
        while True:
            with reserve_ex("ltx25-refine", 64) as (lid, status):
                if status == "refused": print("refine lease refused, retry in 60s", flush=True); R.time.sleep(60); continue
                rc, res = R.refine(B / "scope" / nm, up, tot); break
        R.log(f"[v2b refine] {nm}: {tot} frames, rc {rc}, out {R.nfr(up) if up.exists() else 0}")
    lk = B / "locked" / nm
    r = subprocess.run([str(R.COMFY_PY), str(R.SF / "pipeline-tools/face_lock.py"), str(R.P), c["id"], str(up), str(lk)],
                       capture_output=True, text=True, cwd=str(R.SF))
    R.log(f"[v2b face_lock] {c['id']} rc {r.returncode} :: {(r.stdout or r.stderr).strip()[-200:]}")
    if r.returncode or not lk.exists(): sys.exit(f"face_lock failed on {nm}")
    c["upscale"], c["face_lock"], c["bloom"] = "ltx-2.5 refine 1920x800 + lanczos", True, R.BLOOM.get(c["id"], 0)
    f = (f"[0:v]trim=start_frame={m['pre']}:end_frame={m['pre']+n},setpts=N/{FPS}/TB,"
         f"scale={R.FW}:{R.VH}:flags=lanczos,format=gbrp,format=yuv420p,pad={R.FW}:{R.FH}:0:{R.BAR}:black[v]")
    pre, o = B / "4k" / ("pre_" + nm), B / "4k" / nm
    R.ff("-i", lk, "-filter_complex", f, "-map", "[v]", "-frames:v", n, "-r", FPS, "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", pre)
    subprocess.run([str(R.SF / "bin/grade"), str(pre), str(o), "--lut", c["lut"], "--grain", str(R.GRAIN), "--scope"], check=True); pre.unlink()
    assert R.nfr(o) == n, f"{nm}: {R.nfr(o)} frames != {n}"
    new[nm] = o; R.log(f"[v2b finish] {nm} f0 {f0} n {n}")
lst = []
for l in (V2 / "final/segs/4k/list.txt").read_text().splitlines():
    nm = Path(l.split("'")[1]).name if l.startswith("file") else None
    lst.append(f"file '{new[nm]}'" if nm in new else l)
(B / "list.txt").write_text("\n".join(lst) + "\n")
pic = F / "picture_4k_v2b.mp4"
R.ff("-f", "concat", "-safe", "0", "-i", B / "list.txt", "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", FPS, pic)
assert R.nfr(pic) == R.nfr(F / "picture_4k.mp4"), "picture frame count changed"
for src, dst in (("LAST_SIGNAL_v2.mp4", "LAST_SIGNAL_v2b.mp4"), ("LAST_SIGNAL_v2_51.mp4", "LAST_SIGNAL_v2b_51.mp4")):   # same audio, untouched
    R.ff("-i", pic, "-i", F / src, "-map", "0:v", "-map", "1:a", "-c", "copy", "-movflags", "+faststart", "-metadata", "title=THE LAST SIGNAL", F / dst)
R.ff("-i", F / "LAST_SIGNAL_v2b.mp4", "-vf", "scale=1920:1080:flags=lanczos", "-c:v", "libx264", "-crf", "17", "-preset", "slow",
     "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", F / "LAST_SIGNAL_v2b_1080p.mp4")
json.dump(e, open(F / "edl_v2b_graded.json", "w"), indent=1)
for x in ("LAST_SIGNAL_v2b.mp4", "LAST_SIGNAL_v2b_51.mp4", "LAST_SIGNAL_v2b_1080p.mp4"):
    o = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name,width,height,channels", "-of", "compact", str(F / x)]).decode()
    R.log(f"[v2b deliver] {x} {o.strip().replace(chr(10), ' | ')}")
