import bpy, math, os, sys
# args: [glb_path] [outdir] [name_prefix]
argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
glb = argv[0] if len(argv)>0 else "/Users/dtribe/AI/ComfyUI/output/doug_spike_00001_.glb"
outdir = os.path.expanduser(argv[1]) if len(argv)>1 else os.path.expanduser("~/Desktop/PROJECTS/story-forge/3d-spike/views")
prefix = argv[2] if len(argv)>2 else "doug"
os.makedirs(outdir,exist_ok=True)
# clean scene
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
objs=[o for o in bpy.context.scene.objects if o.type=='MESH']
# join + center
bpy.ops.object.select_all(action='DESELECT')
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active=objs[0]
if len(objs)>1: bpy.ops.object.join()
obj=bpy.context.view_layer.objects.active
# matte clay material
mat=bpy.data.materials.new("clay"); mat.use_nodes=True
bsdf=mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value=(0.8,0.55,0.35,1); bsdf.inputs["Roughness"].default_value=0.6
obj.data.materials.clear(); obj.data.materials.append(mat)
# center to origin, get radius
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY',center='BOUNDS')
obj.location=(0,0,0)
dims=obj.dimensions; R=max(dims)*1.6; cz=dims.z*0.15
# light
sun=bpy.data.lights.new("sun",'SUN'); sun.energy=4
so=bpy.data.objects.new("sun",sun); bpy.context.scene.collection.objects.link(so); so.rotation_euler=(math.radians(55),0,math.radians(30))
world=bpy.data.worlds.new("w"); bpy.context.scene.world=world; world.use_nodes=True
world.node_tree.nodes["Background"].inputs[0].default_value=(0.05,0.05,0.06,1)
world.node_tree.nodes["Background"].inputs[1].default_value=1.0
# camera
cam=bpy.data.cameras.new("cam"); co=bpy.data.objects.new("cam",cam); bpy.context.scene.collection.objects.link(co)
bpy.context.scene.camera=co
tgt=bpy.data.objects.new("tgt",None); bpy.context.scene.collection.objects.link(tgt); tgt.location=(0,0,cz)
con=co.constraints.new('TRACK_TO'); con.target=tgt; con.track_axis='TRACK_NEGATIVE_Z'; con.up_axis='UP_Y'
sc=bpy.context.scene
for eng in ('BLENDER_EEVEE_NEXT','BLENDER_EEVEE','CYCLES'):
    try: sc.render.engine=eng; break
    except Exception: continue
sc.render.resolution_x=512; sc.render.resolution_y=512; sc.render.film_transparent=False
views={"front":0,"right":90,"back":180,"left":270}
for name,ang in views.items():
    a=math.radians(ang)
    co.location=(R*math.sin(a), -R*math.cos(a), cz+dims.z*0.25)
    sc.render.filepath=os.path.join(outdir,f"{prefix}_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered",name,flush=True)
print("ENGINE", sc.render.engine, flush=True)
