import bpy, math, os
glb="/Users/dtribe/AI/ComfyUI/output/doug_spike_00001_.glb"
frames_dir=os.path.expanduser("~/Desktop/PROJECTS/story-forge/3d-spike/turn_frames")
os.makedirs(frames_dir,exist_ok=True)
for f in os.listdir(frames_dir):
    if f.endswith(".png"): os.remove(os.path.join(frames_dir,f))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
objs=[o for o in bpy.context.scene.objects if o.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active=objs[0]
if len(objs)>1: bpy.ops.object.join()
obj=bpy.context.view_layer.objects.active
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY',center='BOUNDS')
obj.location=(0,0,0)
dims=obj.dimensions; H=dims.z; R=max(dims)*1.55

# clay material
mat=bpy.data.materials.new("clay"); mat.use_nodes=True
b=mat.node_tree.nodes.get("Principled BSDF")
b.inputs["Base Color"].default_value=(0.83,0.56,0.36,1); b.inputs["Roughness"].default_value=0.55
obj.data.materials.clear(); obj.data.materials.append(mat)

# lighting: key sun + soft world
sun=bpy.data.lights.new("k",'SUN'); sun.energy=4.0
so=bpy.data.objects.new("k",sun); bpy.context.scene.collection.objects.link(so)
so.rotation_euler=(math.radians(55),0,math.radians(35))
w=bpy.data.worlds.new("w"); bpy.context.scene.world=w; w.use_nodes=True
bg=w.node_tree.nodes["Background"]; bg.inputs[0].default_value=(0.07,0.07,0.09,1); bg.inputs[1].default_value=1.1

# camera fixed, object rotates
cam=bpy.data.cameras.new("c"); co=bpy.data.objects.new("c",cam); bpy.context.scene.collection.objects.link(co)
bpy.context.scene.camera=co
tgt=bpy.data.objects.new("t",None); bpy.context.scene.collection.objects.link(tgt); tgt.location=(0,0,H*0.12)
con=co.constraints.new('TRACK_TO'); con.target=tgt; con.track_axis='TRACK_NEGATIVE_Z'; con.up_axis='UP_Y'
co.location=(0,-R,H*0.28)

sc=bpy.context.scene
for eng in ('BLENDER_EEVEE_NEXT','BLENDER_EEVEE','CYCLES'):
    try: sc.render.engine=eng; break
    except Exception: continue
sc.render.resolution_x=640; sc.render.resolution_y=640
NF=120
obj.rotation_mode='XYZ'
sc.render.image_settings.file_format='PNG'
for fr in range(1,NF+1):
    obj.rotation_euler=(0,0,math.radians(360.0*(fr-1)/NF))   # constant spin, no keyframes
    sc.render.filepath=os.path.join(frames_dir,f"f_{fr:04d}.png")
    bpy.ops.render.render(write_still=True)
    if fr%20==0: print("frame",fr,flush=True)
print("FRAMES_DONE",NF,flush=True)
