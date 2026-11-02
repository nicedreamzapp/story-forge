"""LTX-2.5 IC-LoRA Refine-Details, tiled per-step fusion (driver; no repo edits).
usage: ~/Desktop/PROJECTS/ltx-2-mlx-main/.venv/bin/python tools/ltx25_refine_tiled.py OUT_DIR W H TW TH OV_W OV_H clip1.mp4 [clip2.mp4 ...]
Each input must already be lanczos-resized to WxH and padded to 8n+1 frames."""
import sys, time, glob, resource, subprocess, json, os
from pathlib import Path
import mlx.core as mx
import ltx_pipelines_mlx.ic_lora as icl
from ltx_core_mlx.components.modality_tiling import TiledLTXModel, VideoModalityTiler
from ltx_core_mlx.model.video_vae.tiling import DimensionTilingConfig, TileCountConfig

out_dir = Path(sys.argv[1]); W, H, TW, TH, OVW, OVH = map(int, sys.argv[2:8]); clips = sys.argv[8:]
PACK = sorted(glob.glob(str(Path.home() / ".cache/huggingface/hub/models--dgrauet--ltx-2.5-mlx/snapshots/*")))[-1]
LORA = glob.glob(str(Path.home() / ".cache/huggingface/hub/models--Lightricks--LTX-2.5-22b-IC-LoRA-Refine-Details/snapshots/*/*.safetensors"))[0]
PROMPT = ("sharp photographic detail, crisp natural texture, fine surface detail, clean edges, "
          "natural film grain, high resolution footage")
LOW_RAM = os.environ.get("LOW_RAM", "1") == "1"
tc = TileCountConfig(frames=DimensionTilingConfig(num_tiles=1, overlap=0),
                     height=DimensionTilingConfig(num_tiles=TH, overlap=OVH if TH > 1 else 0),
                     width=DimensionTilingConfig(num_tiles=TW, overlap=OVW if TW > 1 else 0))
_orig = icl.X0Model
state = {}
def tiled_x0(dit):
    F = (state["frames"] - 1) // 8 + 1
    tiler = VideoModalityTiler(tc, latent_shape=(F, H // 32, W // 32))
    if not state.get("printed"):
        for t in tiler.tiles:
            print("tile", getattr(t, "in_coords", t), flush=True)
        state["printed"] = 1
    return _orig(TiledLTXModel(dit, tiler))
if TW * TH > 1:
    icl.X0Model = tiled_x0
res = []
for c in clips:
    n = int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v", "-show_entries",
                            "stream=nb_read_frames", "-of", "csv=p=0", c], capture_output=True, text=True).stdout.strip())
    state["frames"] = n
    pipe = icl.ICLoraPipeline(model_dir=PACK, lora_paths=[(LORA, 1.0)], low_memory=True, low_ram_streaming=LOW_RAM)
    pipe.verbose = True
    out = out_dir / (Path(c).stem + f"_refine_{W}x{H}.mp4")
    mx.reset_peak_memory(); t = time.time()
    pipe.generate_and_save(prompt=PROMPT, output_path=str(out), video_conditioning=[(c, 1.0)], height=H, width=W,
                           num_frames=n, frame_rate=24.0, seed=42, single_stage=True)
    dt = time.time() - t
    r = dict(clip=Path(c).name, frames=n, W=W, H=H, tiles=TW * TH, sec=round(dt, 1),
             metal_peak_gb=round(mx.get_peak_memory() / 1e9, 1),
             maxrss_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e9, 1), out=str(out))
    print("RESULT", json.dumps(r), flush=True); res.append(r)
    del pipe
(out_dir / f"results_{W}x{H}.json").write_text(json.dumps(res, indent=1))
