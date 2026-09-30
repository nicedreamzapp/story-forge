#!/usr/bin/env python3
"""make_sfx.py — MMAudio foley for every silent clip (video-conditioned, fp32), via ComfyUI.
Writes sfx/<id>.wav. Skips talk shots (their audio is the voice) and clips already done."""
import json, time, subprocess, sys, shutil, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path.home() / "SongForgeM5"))
import mem_client
P = Path(__file__).resolve().parent
URL = "http://127.0.0.1:8188"
OUT = Path.home() / "AI/ComfyUI/output"
NEG = "music, speech, talking, voices, singing, narration"
def sfx_prompt(sid):
    if sid.startswith(("s5_storm","s5_crown","s5_split")): return "thunderstorm, heavy rain, rolling thunder, crackling sparks"
    if sid.startswith(("s5_firewall","s5_embers","s5_trunkfire","s5_shelter")): return "roaring forest fire, crackling burning wood, wind"
    if sid.startswith(("s5_sway","s5_lean")): return "violent wind storm, creaking trees, rain, branches thrashing"
    if sid == "s4_creek": return "babbling creek, water trickling, birds"
    if sid.startswith(("s5_","s6_","s7_")): return "quiet night forest, fog dripping, faint wind, footsteps on leaves, breathing"
    if sid in ("s2_wide_walk","s2_track_behind","s2_boots","s4_walkback","s8_wide"): return "footsteps on forest trail, soft wind in tall trees, distant birdsong"
    return "gentle wind high in tall redwood trees, distant birdsong, calm forest ambience"
def post(path, data):
    r = urllib.request.Request(URL + path, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=30))
def get(path): return json.load(urllib.request.urlopen(URL + path, timeout=30))
def dur(f): return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(f)]))
spec = json.load(open(P / "film_shots.json"))
todo = [s for s in spec["shots"] if not s.get("talk") and (P/"clips"/f"{s['id']}_final.mp4").exists() and not (P/"sfx"/f"{s['id']}.wav").exists()]
import os
todo = todo[:int(os.environ.get("SFX_LIMIT", "999"))]
print(len(todo), "clips need foley", flush=True)
with mem_client.reserve("storyforge-animate mmaudio", 20):
    for s in todo:
        sid = s["id"]; clip = P/"clips"/f"{sid}_final.mp4"
        wf = {
         "1": {"class_type": "MMAudioModelLoader", "inputs": {"mmaudio_model": "mmaudio_large_44k_v2_fp32.safetensors", "base_precision": "fp32"}},
         "2": {"class_type": "MMAudioFeatureUtilsLoader", "inputs": {"vae_model": "mmaudio_vae_44k_fp32.safetensors", "synchformer_model": "mmaudio_synchformer_fp32.safetensors", "clip_model": "apple_DFN5B-CLIP-ViT-H-14-384_fp32.safetensors", "mode": "44k", "precision": "fp32"}},
         "3": {"class_type": "VHS_LoadVideoPath", "inputs": {"video": str(clip), "force_rate": 0, "custom_width": 0, "custom_height": 0, "frame_load_cap": 0, "skip_first_frames": 0, "select_every_nth": 1}},
         "4": {"class_type": "MMAudioSampler", "inputs": {"mmaudio_model": ["1", 0], "feature_utils": ["2", 0], "duration": round(dur(clip), 2), "steps": 25, "cfg": 4.5, "seed": 7, "prompt": sfx_prompt(sid), "negative_prompt": NEG, "mask_away_clip": False, "force_offload": True, "images": ["3", 0]}},
         "5": {"class_type": "SaveAudio", "inputs": {"audio": ["4", 0], "filename_prefix": f"oldest_tree_sfx/{sid}"}},
        }
        pid = None
        for _ in range(60):          # ComfyUI gets bounced by render passes; a dead backend is not a failed clip
            try:
                pid = post("/prompt", {"prompt": wf})["prompt_id"]; break
            except Exception as e:
                err = e; time.sleep(10)
        if not pid:
            print("SUBMIT FAIL", sid, err, flush=True); continue
        for _ in range(360):
            time.sleep(3)
            h = get(f"/history/{pid}")
            if pid in h:
                st = h[pid].get("status", {})
                files = [a for o in h[pid].get("outputs", {}).values() for a in o.get("audio", [])]
                if files:
                    f = files[0]; src = OUT / f.get("subfolder", "") / f["filename"]
                    subprocess.run(["/opt/homebrew/bin/ffmpeg","-v","error","-y","-i",str(src),"-ar","48000","-ac","2",str(P/"sfx"/f"{sid}.wav")])
                    print("ok", sid, flush=True)
                else:
                    print("FAIL", sid, json.dumps(st)[:300], flush=True)
                break
        else:
            print("TIMEOUT", sid, flush=True)
# hand the memory back: an idle ComfyUI holding MMAudio blocked the render queue for 50 min (2026-09-29)
try:
    post("/free", {"unload_models": True, "free_memory": True})
except Exception:
    pass
