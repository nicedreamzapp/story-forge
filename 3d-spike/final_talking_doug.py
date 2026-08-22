import bpy, math, os, wave, struct
import numpy as np
from mathutils import Vector
glb="/Users/dtribe/AI/ComfyUI/output/doug_spike_00001_.glb"
portrait=os.path.expanduser("~/Desktop/PROJECTS/story-forge/3d-spike/in/doug_512.jpg")
pcm=os.path.expanduser("~/Desktop/PROJECTS/story-forge/3d-spike/audio/doug_pcm.wav")
frames_dir=os.path.expanduser("~/Desktop/PROJECTS/story-forge/3d-spike/talk_frames")
os.makedirs(frames_dir,exist_ok=True)
for f in os.listdir(frames_dir):
    if f.endswith(".png"): os.remove(os.path.join(frames_dir,f))

FPS=24
# --- audio envelope -> per-frame jaw value ---
w=wave.open(pcm,'rb'); rate=w.getframerate(); n=w.getnframes()
raw=w.readframes(n); samples=np.frombuffer(raw,dtype=np.int16).astype(np.float32)/32768.0
dur=n/rate; NF=int(dur*FPS)
env=np.zeros(NF)
for i in range(NF):
    a=int(i/FPS*rate); b=int((i+1)/FPS*rate)
    seg=samples[a:b]
    env[i]=np.sqrt(np.mean(seg**2)) if len(seg) else 0.0
env=env/ (env.max()+1e-6)
# smooth a touch
k=np.array([0.25,0.5,0.25]); env=np.convolve(env,k,mode='same')
env=np.clip(env,0,1)
print(f"audio {dur:.2f}s -> {NF} frames; env max {env.max():.2f}",flush=True)

# --- load mesh ---
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
objs=[o for o in bpy.context.scene.objects if o.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active=objs[0]
if len(objs)>1: bpy.ops.object.join()
obj=bpy.context.view_layer.objects.active
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY',center='BOUNDS'); obj.location=(0,0,0)
me=obj.data
xs=[v.co.x for v in me.vertices]; zs=[v.co.z for v in me.vertices]; ys=[v.co.y for v in me.vertices]
minx,maxx=min(xs),max(xs); minz,maxz=min(zs),max(zs); miny,maxy=min(ys),max(ys)
H=maxz-minz; D=maxy-miny

# --- front planar UV + portrait texture ---
uv=me.uv_layers.new(name="front_proj")
for loop in me.loops:
    co=me.vertices[loop.vertex_index].co
    uv.data[loop.index].uv=(1.0-(co.x-minx)/(maxx-minx),(co.z-minz)/(maxz-minz))
img=bpy.data.images.load(portrait)
mat=bpy.data.materials.new("doug"); mat.use_nodes=True
bsdf=mat.node_tree.nodes.get("Principled BSDF")
tex=mat.node_tree.nodes.new("ShaderNodeTexImage"); tex.image=img
mat.node_tree.links.new(tex.outputs["Color"],bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value=0.55
obj.data.materials.clear(); obj.data.materials.append(mat)

# --- jaw shape key (subtle) ---
obj.shape_key_add(name="Basis",from_mix=False)
sk=obj.shape_key_add(name="jaw",from_mix=False)
head_z=minz+H*0.58; muzzle_front=min(v.co.y for v in me.vertices if v.co.z>head_z)
mdepth=(max(v.co.y for v in me.vertices if v.co.z>head_z)-muzzle_front)
hinge_y=muzzle_front+mdepth*0.55; lower_z=head_z+H*0.20
for i,v in enumerate(me.vertices):
    if v.co.z>head_z and v.co.y<muzzle_front+mdepth*0.5 and v.co.z<lower_z:
        t=max(0.0,(hinge_y-v.co.y)/(hinge_y-muzzle_front+1e-6))
        sk.data[i].co=v.co+Vector((0,-D*0.035*t,-H*0.11*t))

# --- skeleton + auto weights ---
arm=bpy.data.armatures.new("rig"); rig=bpy.data.objects.new("rig",arm); bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
sp=arm.edit_bones.new("spine"); sp.head=(0,0.1,minz+H*0.05); sp.tail=(0,0.05,minz+H*0.55)
hd=arm.edit_bones.new("head"); hd.head=(0,0.05,minz+H*0.55); hd.tail=(0,-0.15,maxz-H*0.05); hd.parent=sp
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); rig.select_set(True); bpy.context.view_layer.objects.active=rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')

# --- light/world/cam (talking close-up, front 3/4) ---
sun=bpy.data.lights.new("k",'SUN'); sun.energy=4.2; so=bpy.data.objects.new("k",sun); bpy.context.scene.collection.objects.link(so); so.rotation_euler=(math.radians(52),0,math.radians(22))
fill=bpy.data.lights.new("f",'SUN'); fill.energy=1.4; fo=bpy.data.objects.new("f",fill); bpy.context.scene.collection.objects.link(fo); fo.rotation_euler=(math.radians(60),0,math.radians(-40))
wd=bpy.data.worlds.new("w"); bpy.context.scene.world=wd; wd.use_nodes=True
bn=wd.node_tree.nodes["Background"]; bn.inputs[0].default_value=(0.09,0.10,0.12,1); bn.inputs[1].default_value=1.0
cam=bpy.data.cameras.new("c"); co=bpy.data.objects.new("c",cam); bpy.context.scene.collection.objects.link(co); bpy.context.scene.camera=co
tgt=bpy.data.objects.new("t",None); bpy.context.scene.collection.objects.link(tgt); tgt.location=(0,0,minz+H*0.66)
con=co.constraints.new('TRACK_TO'); con.target=tgt; con.track_axis='TRACK_NEGATIVE_Z'; con.up_axis='UP_Y'
R=max(maxx-minx,D,H)*1.25; co.location=(R*0.4,miny-R*0.95,minz+H*0.78)

sc=bpy.context.scene
for eng in ('BLENDER_EEVEE_NEXT','BLENDER_EEVEE','CYCLES'):
    try: sc.render.engine=eng; break
    except Exception: continue
sc.render.resolution_x=640; sc.render.resolution_y=640; sc.render.image_settings.file_format='PNG'

# --- animate: head idle + jaw=envelope ---
bpy.ops.object.mode_set(mode='POSE')
ph=rig.pose.bones["head"]; ps=rig.pose.bones["spine"]; ph.rotation_mode='XYZ'; ps.rotation_mode='XYZ'
kb=obj.data.shape_keys.key_blocks["jaw"]
for fr in range(1,NF+1):
    t=(fr-1)/NF
    ph.rotation_euler=(math.radians(4)*math.sin(t*2*math.pi), 0, math.radians(9)*math.sin(t*1.3*math.pi))
    ps.rotation_euler=(math.radians(2.5)*math.sin(t*3*math.pi),0,0)
    obj.location.z=0.012*H*math.sin(t*6*math.pi)
    kb.value=float(0.18+0.55*env[fr-1])*env[fr-1]   # jaw opens with speech amplitude
    sc.render.filepath=os.path.join(frames_dir,f"t_{fr:04d}.png")
    bpy.ops.render.render(write_still=True)
    if fr%12==0: print("frame",fr,flush=True)
print("TALK_FRAMES_DONE",NF,flush=True)
