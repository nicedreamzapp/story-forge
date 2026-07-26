#!/usr/bin/env python3
"""Queue a Wan2.2-S2V render on local ComfyUI (native nodes, lightx2v 4-step).

Usage: s2v_render.py --image doug_talk_601.png --audio doug_s2v_test.wav \
                     --prompt "..." [--width 832 --height 480] [--length 77] [--out NAME]
Image/audio paths are relative to the ComfyUI input dir.
"""
import argparse, json, time, urllib.request, sys

API = "http://127.0.0.1:8188"

NEG = ("色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，"
       "JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，"
       "形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走")


def build_graph(a):
    return {
        "1": {"class_type": "UNETLoader", "inputs": {
            "unet_name": "wan2.2_s2v_14B_bf16.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "LoraLoaderModelOnly", "inputs": {
            "model": ["1", 0],
            "lora_name": "wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors",
            "strength_model": 1.0}},
        "3": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["2", 0], "shift": 8.0}},
        "4": {"class_type": "CLIPLoader", "inputs": {
            "clip_name": "umt5_xxl_fp16.safetensors", "type": "wan", "device": "default"}},
        "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 0], "text": a.prompt}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 0], "text": NEG}},
        "7": {"class_type": "VAELoader", "inputs": {"vae_name": "wan_2.1_vae.safetensors"}},
        "8": {"class_type": "AudioEncoderLoader", "inputs": {
            "audio_encoder_name": "wav2vec2_large_english_fp16.safetensors"}},
        "9": {"class_type": "LoadAudio", "inputs": {"audio": a.audio}},
        "10": {"class_type": "AudioEncoderEncode", "inputs": {
            "audio_encoder": ["8", 0], "audio": ["9", 0]}},
        "11": {"class_type": "LoadImage", "inputs": {"image": a.image}},
        "12": {"class_type": "WanSoundImageToVideo", "inputs": {
            "positive": ["5", 0], "negative": ["6", 0], "vae": ["7", 0],
            "audio_encoder_output": ["10", 0], "ref_image": ["11", 0],
            "width": a.width, "height": a.height, "length": a.length, "batch_size": 1}},
        "13": {"class_type": "KSampler", "inputs": {
            "model": ["3", 0], "positive": ["12", 0], "negative": ["12", 1],
            "latent_image": ["12", 2], "seed": a.seed, "steps": 4, "cfg": 1.0,
            "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
        "14": {"class_type": "VAEDecode", "inputs": {"samples": ["13", 0], "vae": ["7", 0]}},
        "15": {"class_type": "CreateVideo", "inputs": {
            "images": ["14", 0], "audio": ["9", 0], "fps": 16}},
        "16": {"class_type": "SaveVideo", "inputs": {
            "video": ["15", 0], "filename_prefix": a.out,
            "format": "mp4", "codec": "h264"}},
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--image", required=True)
    p.add_argument("--audio", required=True)
    p.add_argument("--prompt", required=True)
    p.add_argument("--width", type=int, default=832)
    p.add_argument("--height", type=int, default=480)
    p.add_argument("--length", type=int, default=77)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", default="s2v/doug_s2v")
    a = p.parse_args()

    req = urllib.request.Request(f"{API}/prompt",
        data=json.dumps({"prompt": build_graph(a)}).encode(),
        headers={"Content-Type": "application/json"})
    try:
        resp = json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as e:
        print("QUEUE FAILED:", e.read().decode()[:2000]); sys.exit(1)
    pid = resp["prompt_id"]
    print("queued:", pid, flush=True)

    while True:
        time.sleep(15)
        hist = json.load(urllib.request.urlopen(f"{API}/history/{pid}"))
        if pid in hist:
            st = hist[pid]["status"]
            if st.get("status_str") == "error":
                msgs = [m for m in st.get("messages", []) if m[0] == "execution_error"]
                print("RENDER ERROR:", json.dumps(msgs)[:3000]); sys.exit(1)
            outs = hist[pid].get("outputs", {})
            for node in outs.values():
                for v in node.get("images", []) + node.get("video", []):
                    print("DONE:", v.get("subfolder", ""), v["filename"]); return
            print("finished, no video output?"); sys.exit(1)
        print("rendering...", flush=True)


if __name__ == "__main__":
    main()
