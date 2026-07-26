import bpy, math, os
from mathutils import Vector
glb="/Users/dtribe/AI/ComfyUI/output/doug_spike_00001_.glb"
frames_dir=os.path.expanduser("~/Desktop/PROJECTS/story-forge/3d-spike/move_frames")
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
zs=[v.co.z for v in obj.data.vertices]; minz,maxz=min(zs),max(zs); H=maxz-minz
dims=obj.dimensions

# --- build a simple skeleton ---
arm=bpy.data.armatures.new("rig"); rig=bpy.data.objects.new("rig",arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig; rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
eb=arm.edit_bones
neck_z=minz+H*0.55
spine=eb.new("spine"); spine.head=(0,0.1,minz+H*0.05); spine.tail=(0,0.05,neck_z)
head=eb.new("head");  head.head=(0,0.05,neck_z); head.tail=(0,-0.15,maxz-H*0.05)
head.parent=spine
bpy.ops.object.mode_set(mode='OBJECT')

# --- bind mesh to skeleton with automatic weights ---
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True); rig.select_set(True); bpy.context.view_layer.objects.active=rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')

# --- material / light / world ---
mat=bpy.data.materials.new("clay"); mat.use_nodes=True
b=mat.node_tree.nodes.get("Principled BSDF"); b.inputs["Base Color"].default_value=(0.83,0.56,0.36,1); b.inputs["Roughness"].default_value=0.55
obj.data.materials.clear(); obj.data.materials.append(mat)
sun=bpy.data.lights.new("k",'SUN'); sun.energy=4.0; so=bpy.data.objects.new("k",sun); bpy.context.scene.collection.objects.link(so); so.rotation_euler=(math.radians(55),0,math.radians(35))
w=bpy.data.worlds.new("w"); bpy.context.scene.world=w; w.use_nodes=True
bgnode=w.node_tree.nodes["Background"]; bgnode.inputs[0].default_value=(0.07,0.07,0.09,1); bgnode.inputs[1].default_value=1.1

# --- camera: 3/4 front ---
cam=bpy.data.cameras.new("c"); co=bpy.data.objects.new("c",cam); bpy.context.scene.collection.objects.link(co); bpy.context.scene.camera=co
tgt=bpy.data.objects.new("t",None); bpy.context.scene.collection.objects.link(tgt); tgt.location=(0,0,minz+H*0.6)
con=co.constraints.new('TRACK_TO'); con.target=tgt; con.track_axis='TRACK_NEGATIVE_Z'; con.up_axis='UP_Y'
R=max(dims)*1.5; co.location=(R*0.55,-R*0.85,minz+H*0.72)

sc=bpy.context.scene
for eng in ('BLENDER_EEVEE_NEXT','BLENDER_EEVEE','CYCLES'):
    try: sc.render.engine=eng; break
    except Exception: continue
sc.render.resolution_x=640; sc.render.resolution_y=640
sc.render.image_settings.file_format='PNG'

# --- animate: head look-around + nod + gentle body breathe ---
bpy.ops.object.mode_set(mode='POSE')
pb_head=rig.pose.bones["head"]; pb_spine=rig.pose.bones["spine"]
pb_head.rotation_mode='XYZ'; pb_spine.rotation_mode='XYZ'
NF=144
for fr in range(1,NF+1):
    t=(fr-1)/NF
    turn=math.radians(28)*math.sin(t*2*math.pi)          # look left/right
    nod =math.radians(10)*math.sin(t*4*math.pi)          # slight nod
    breathe=math.radians(4)*math.sin(t*4*math.pi)        # spine bob
    pb_head.rotation_euler=(nod,0,turn)
    pb_spine.rotation_euler=(breathe,0,0)
    obj.location.z = 0.02*H*math.sin(t*4*math.pi)        # subtle vertical breathe
    sc.render.filepath=os.path.join(frames_dir,f"m_{fr:04d}.png")
    bpy.ops.render.render(write_still=True)
    if fr%24==0: print("frame",fr,flush=True)
print("MOVE_FRAMES_DONE",NF,flush=True)
