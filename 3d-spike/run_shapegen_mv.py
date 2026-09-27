import json, urllib.request, time, os, glob
SRV="http://127.0.0.1:8188"
def post(p,d=None):
    r=urllib.request.Request(SRV+p, data=json.dumps(d).encode() if d else None,
                             headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(r,timeout=30).read())
def get(p): return json.loads(urllib.request.urlopen(SRV+p,timeout=30).read())

g={
 "1f":{"class_type":"LoadImage","inputs":{"image":"mv_front.png"}},
 "1r":{"class_type":"LoadImage","inputs":{"image":"mv_right.png"}},
 "1l":{"class_type":"LoadImage","inputs":{"image":"mv_left.png"}},
 "1b":{"class_type":"LoadImage","inputs":{"image":"mv_back.png"}},
 "2":{"class_type":"Hy3DModelLoader","inputs":{"model":"hunyuan3d-dit-v2-mv-fp16.safetensors","attention_mode":"sdpa"}},
 "3":{"class_type":"Hy3DGenerateMeshMultiView","inputs":{
        "pipeline":["2",0],"front":["1f",0],"left":["1l",0],"right":["1r",0],"back":["1b",0],
        "guidance_scale":5.5,"steps":30,"seed":42,"scheduler":"FlowMatchEulerDiscreteScheduler"}},
 "4":{"class_type":"Hy3DVAEDecode","inputs":{
        "vae":["2",1],"latents":["3",0],"box_v":1.01,"octree_resolution":256,
        "num_chunks":8000,"mc_level":0.0,"mc_algo":"mc","enable_flash_vdm":False,"force_offload":True}},
 "5":{"class_type":"Hy3DPostprocessMesh","inputs":{
        "trimesh":["4",0],"remove_floaters":True,"remove_degenerate_faces":True,
        "reduce_faces":True,"max_facenum":40000,"smooth_normals":False}},
 "6":{"class_type":"Hy3DExportMesh","inputs":{
        "trimesh":["5",0],"filename_prefix":"doug_mv","file_format":"glb","save_file":True}},
}
r=post("/prompt",{"prompt":g}); pid=r["prompt_id"]; print("submitted",pid,flush=True)
t0=time.time()
while True:
    h=get(f"/history/{pid}")
    if pid in h:
        st=h[pid].get("status",{})
        print("DONE",json.dumps(st)[:500],flush=True); break
    if time.time()-t0>1800: print("TIMEOUT",flush=True); break
    time.sleep(5)
gs=sorted(glob.glob(os.path.expanduser("~/AI/ComfyUI/output/**/doug_mv*.glb"),recursive=True),key=os.path.getmtime)
print("GLB:", gs[-1] if gs else "NONE", flush=True)
if gs: print("bytes:", os.path.getsize(gs[-1]), flush=True)
