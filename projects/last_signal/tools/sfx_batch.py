#!/usr/bin/env python3
"""sfx_batch (THE LAST SIGNAL, from bin/make-sfx): loads MMAudio ONCE, runs every job in jobs.json.
make-sfx "prompt" --seconds N --out file.wav [--seed S] [--steps 25] [--negative TXT] [--cfg 4.5] [--video clip.mp4]
MMAudio large 44k v2 (fp32, MPS) using the code from ComfyUI-MMAudio. Text-to-audio by default;
--video switches to picture-synced video-to-audio. Output: 44.1kHz stereo wav. Exits after one
generation so memory is freed. Waits while Song Forge has customer jobs running."""
import argparse, json, subprocess, sys, time, urllib.request
from contextlib import nullcontext
from pathlib import Path

jobs = json.load(open(sys.argv[1]))
class A: pass

def jobs_running():
    try:
        with urllib.request.urlopen("http://127.0.0.1:8767/api/status", timeout=5) as r:
            return int(json.load(r).get("jobs_running", 0))
    except Exception:
        return 0
while jobs_running() > 0:
    print("make-sfx: Song Forge job running, waiting 30s", file=sys.stderr, flush=True)
    time.sleep(30)

sys.path.insert(0, str(Path.home() / "SongForgeM5"))
try:
    from mem_client import reserve
except Exception:
    print("make-sfx: mem_client unavailable, no lease", file=sys.stderr)
    reserve = lambda name, gb: nullcontext()

NODE = Path.home() / "AI/ComfyUI/custom_nodes/ComfyUI-MMAudio"
MODELS = Path.home() / "AI/ComfyUI/models/mmaudio"
sys.path.insert(0, str(NODE)); sys.path.insert(1, str(Path.home() / "AI/ComfyUI"))

import numpy as np, torch, soundfile as sf
from accelerate import init_empty_weights
from accelerate.utils import set_module_tensor_to_device
from safetensors.torch import load_file
from open_clip import CLIP
from mmaudio.eval_utils import generate
from mmaudio.model.flow_matching import FlowMatching
from mmaudio.model.networks import MMAudio
from mmaudio.model.utils.features_utils import FeaturesUtils
from mmaudio.model.sequence_config import CONFIG_44K
from mmaudio.ext.bigvgan_v2.bigvgan import BigVGAN as BigVGANv2
from mmaudio.ext.synchformer import Synchformer
from mmaudio.ext.autoencoder import AutoEncoderModule

def frames(path, fps, vf, secs):
    w, h = vf[1]
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-t", str(secs), "-vf", f"fps={fps},{vf[0]}",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    arr = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    return torch.from_numpy(arr.copy()).permute(0, 3, 1, 2).float() / 255.0

dev, dtype = torch.device("mps"), torch.float32
with reserve("make-sfx-batch", 14):
    t0 = time.time()
    sd = load_file(str(MODELS / "mmaudio_large_44k_v2_fp32.safetensors"))
    with init_empty_weights():
        net = MMAudio(latent_dim=40, clip_dim=1024, sync_dim=768, text_dim=1024, hidden_dim=64 * 14,
                      depth=21, fused_depth=14, num_heads=14, latent_seq_len=345, clip_seq_len=64,
                      sync_seq_len=192, v2=sd["t_embed.mlp.0.weight"].shape[1] == 896).eval()
    for n, _ in net.named_parameters():
        set_module_tensor_to_device(net, n, device=dev, dtype=dtype, value=sd[n])
    del sd
    for _, b in net.named_buffers():   # non-persistent buffers (timestep freqs) were built on cpu
        if b.device.type == "cpu":
            b.data = b.data.to(dev)
    net.seq_cfg = CONFIG_44K

    syn_sd = load_file(str(MODELS / "mmaudio_synchformer_fp32.safetensors"))
    with init_empty_weights():
        syn = Synchformer().eval()
    for n, _ in syn.named_parameters():
        set_module_tensor_to_device(syn, n, device=dev, dtype=dtype, value=syn_sd[n])
    del syn_sd

    voc = BigVGANv2.from_pretrained(str(MODELS / "nvidia/bigvgan_v2_44khz_128band_512x")).eval().to(dev, dtype)
    vae = AutoEncoderModule(vae_state_dict=load_file(str(MODELS / "mmaudio_vae_44k_fp32.safetensors")),
                            bigvgan_vocoder=voc, mode="44k").eval().to(dev, dtype)

    cfg = json.load(open(NODE / "configs/DFN5B-CLIP-ViT-H-14-384.json"))
    with init_empty_weights():
        try: clip = CLIP(**cfg["model_cfg"]).eval()
        except Exception:
            cfg["model_cfg"]["nonscalar_logit_scale"] = True
            clip = CLIP(**cfg["model_cfg"]).eval()
    csd = load_file(str(MODELS / "apple_DFN5B-CLIP-ViT-H-14-384_fp32.safetensors"))
    for n, _ in clip.named_parameters():
        set_module_tensor_to_device(clip, n, device=dev, dtype=dtype, value=csd[n])
    del csd
    clip.to(dev, dtype)
    fu = FeaturesUtils(vae=vae, synchformer=syn, enable_conditions=True, clip_model=clip)
    print(f"make-sfx: models loaded in {time.time()-t0:.1f}s", flush=True)

    for j in jobs:
        a = A(); a.prompt = j["prompt"]; a.seconds = j.get("seconds", 4); a.out = j["out"]; a.seed = j.get("seed", 7)
        a.steps = j.get("steps", 25); a.cfg = j.get("cfg", 4.5); a.negative = j.get("negative", "music, speech, voice, singing"); a.video = j.get("video")
        if Path(a.out).exists(): print("have", a.out); continue
        while jobs_running() > 0:
            print("Song Forge job running, waiting 30s", flush=True); time.sleep(30)
        dur = a.seconds
        clip_f = sync_f = None
        if a.video:
            clip_f = frames(a.video, 8, ("scale=384:384:flags=bicubic", (384, 384)), dur)
            sync_f = frames(a.video, 25, ("scale=-2:224:flags=bicubic,crop=224:224", (224, 224)), dur)
            sync_f = (sync_f - 0.5) / 0.5
            dur = min(dur, clip_f.shape[0] / 8, sync_f.shape[0] / 25)
            clip_f = clip_f[: int(8 * dur)].unsqueeze(0)
            sync_f = sync_f[: int(25 * dur)].unsqueeze(0)
            print(f"make-sfx: video mode, duration {dur:.2f}s", flush=True)

        net.seq_cfg.duration = dur
        net.update_seq_lengths(net.seq_cfg.latent_seq_len, net.seq_cfg.clip_seq_len, net.seq_cfg.sync_seq_len)
        rng = torch.Generator(device=dev)
        rng.manual_seed(a.seed if a.seed is not None else int(time.time()) % 2**31)
        fm = FlowMatching(min_sigma=0, inference_mode="euler", num_steps=a.steps)
        t1 = time.time()
        with torch.no_grad():
            audio = generate(clip_f, sync_f, [a.prompt], negative_text=[a.negative],
                             feature_utils=fu, net=net, fm=fm, rng=rng, cfg_strength=a.cfg)
        wav = audio.float().cpu()[0]            # (channels, samples)
        if wav.shape[0] == 1: wav = wav.repeat(2, 1)
        out = wav.T.numpy()[: int(dur * 44100)]
        peak = float(np.abs(out).max())
        if peak > 0.98: out = out * (0.98 / peak)   # avoid clipping
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        sf.write(a.out, out, 44100, subtype="PCM_16")
        try: mem = f", peak MPS mem {torch.mps.driver_allocated_memory()/1e9:.1f} GB"
        except Exception: mem = ""
        print(f"done: generate {time.time()-t1:.1f}s, total {time.time()-t0:.1f}s{mem} -> {a.out}")
