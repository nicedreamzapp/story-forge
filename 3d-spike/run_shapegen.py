import json, urllib.request, time, os, glob
SRV="http://127.0.0.1:8188"
def post(path, data=None):
    req=urllib.request.Request(SRV+path, data=json.dumps(data).encode() if data else None,
                               headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())
def get(path):
    return json.loads(urllib.request.urlopen(SRV+path, timeout=30).read())

graph = {
 "1": {"class_type":"LoadImage","inputs":{"image":"doug_rgba.png"}},
 "2": {"class_type":"Hy3DModelLoader","inputs":{"model":"hunyuan3d-dit-v2-0-fp16.safetensors","attention_mode":"sdpa"}},
 "3": {"class_type":"Hy3DGenerateMesh","inputs":{
        "pipeline":["2",0],"image":["1",0],"mask":["1",1],
        "guidance_scale":5.5,"steps":30,"seed":42,
        "scheduler":"FlowMatchEulerDiscreteScheduler","force_offload":True}},
 "4": {"class_type":"Hy3DVAEDecode","inputs":{
        "vae":["2",1],"latents":["3",0],
        "box_v":1.01,"octree_resolution":256,"num_chunks":8000,
        "mc_level":0.0,"mc_algo":"mc","enable_flash_vdm":False,"force_offload":True}},
 "5": {"class_type":"Hy3DPostprocessMesh","inputs":{
        "trimesh":["4",0],"remove_floaters":True,"remove_degenerate_faces":True,
        "reduce_faces":True,"max_facenum":40000,"smooth_normals":False}},
 "6": {"class_type":"Hy3DExportMesh","inputs":{
        "trimesh":["5",0],"filename_prefix":"doug_spike","file_format":"glb","save_file":True}},
}
r=post("/prompt",{"prompt":graph})
pid=r["prompt_id"]; print("submitted prompt_id:",pid, flush=True)
t0=time.time()
while True:
    h=get(f"/history/{pid}")
    if pid in h:
        st=h[pid].get("status",{})
        print("DONE status:",json.dumps(st)[:400], flush=True)
        break
    if time.time()-t0>1500:
        print("TIMEOUT after 25min", flush=True); break
    time.sleep(5)
# locate newest glb
gs=sorted(glob.glob(os.path.expanduser("~/AI/ComfyUI/output/**/doug_spike*.glb"),recursive=True),
          key=os.path.getmtime)
print("GLB:", gs[-1] if gs else "NONE FOUND", flush=True)
if gs: print("bytes:", os.path.getsize(gs[-1]), flush=True)
