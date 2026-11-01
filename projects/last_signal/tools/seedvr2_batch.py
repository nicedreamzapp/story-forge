#!/usr/bin/env python3
"""SeedVR2-3B (fp16, MPS) restore-upscale of the scope-cropped picture segments, one process per segment (the model is
the only one loaded; ~10 s reload each). Measured on the M5 10/31: ~13 s per output frame at 720p short side, VAE
decode is 70% of it, tiling does not help, 4K direct is ~6x slower (7 min just to ENCODE 21 frames). So:
  * shots held >= 0.9 s (every shot the eye can inspect): SeedVR2 to 1720x720 (2.07x real restoration), then
    tools/finish_4k.py lanczos-scales to 3840x1608 inside the 2160p scope frame;
  * sub-0.9 s ramp cuts and the strobe (4-21 frames on screen, motion-blurred): lanczos straight from source.
batch = fewest batches of <= 49 frames, each 4n+1 (a 46-frame shot at batch 45 had padded to 90 frames: fixed 14:20). Waits on Song Forge jobs,
holds a forge_guard lease for the run."""
import json, math, subprocess, sys, time, urllib.request
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path.home() / "SongForgeM5"))
from mem_client import reserve
e = json.load(open(P / "final/edl_final.json")); H = {m["seg"]: m for m in json.load(open(P / "final/segs/handles.json"))}
COMFY = Path.home() / "AI/ComfyUI"
def busy():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8767/api/status", timeout=5) as r: return int(json.load(r).get("jobs_running", 0)) > 0
    except Exception: return False
def frames(f, w=208, h=87):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3).astype(np.float32)
def bad_frames(src, up):
    """A SeedVR2 temporal batch can come back grey with white smears (c04 arrival batch 2, 10/31): every output frame
    is compared with its source frame at thumbnail size; a mean abs diff > 12 marks that frame bad."""
    a, b = frames(src), frames(up); k = min(len(a), len(b))
    if len(a) != len(b): return list(range(k, max(len(a), len(b)))) or [0]
    return [int(i) for i in np.where(np.abs(a[:k] - b[:k]).mean(axis=(1, 2, 3)) > 12)[0]]
todo = []
for k, c in enumerate(e["cuts"]):
    if not c["src"] or c["section"] in ("title",) or c["len"] < 0.9: continue
    name = f"{k:02d}_{c['id']}.mp4"; m = H[name]; n = m["pre"] + m["n"] + m["post"]
    todo.append((name, n))
print(len(todo), "segments,", sum(n for _, n in todo), "frames", flush=True)
with reserve("seedvr2-3b", 34):
    for name, n in todo:
        out = P / "final/segs/up" / name
        if out.exists(): continue
        while busy(): print("Song Forge job running, waiting 30s", flush=True); time.sleep(30)
        k = math.ceil(n / 49)                       # fewest temporal batches of <= 49 frames
        per = math.ceil(n / k); b = 4 * math.ceil((per - 1) / 4) + 1   # 4n+1, padding only the last batch a little
        for seed in (42, 7, 1234):
          t0 = time.time()
          r = subprocess.run([str(COMFY / "venv/bin/python"), str(P / "tools/seedvr2_run.py"), str(P / "final/segs/scope" / name),
                            "--output", str(out), "--resolution", "720", "--batch_size", str(b), "--uniform_batch_size",
                            "--model_dir", str(COMFY / "models/SEEDVR2"), "--dit_model", "seedvr2_ema_3b_fp16.safetensors",
                            "--video_backend", "ffmpeg", "--color_correction", "lab", "--seed", str(seed)], cwd=str(COMFY), capture_output=True, text=True)
          rc = r.returncode
          bad = bad_frames(P / "final/segs/scope" / name, out) if rc == 0 and out.exists() else ["no output"]
          print(f"{name}: {n} frames, batch {b}, seed {seed}, rc {rc}, {time.time()-t0:.0f}s, bad frames {len(bad)}", flush=True)
          if rc != 0: print(r.stdout[-1500:], r.stderr[-1500:], flush=True)
          if not bad: break
          out.rename(out.with_suffix(f".bad{seed}.mp4")) if out.exists() else None
