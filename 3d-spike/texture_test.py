import bpy, math, os
glb="/Users/dtribe/AI/ComfyUI/output/doug_spike_00001_.glb"
portrait=os.path.expanduser("~/Desktop/PROJECTS/story-forge/3d-spike/in/doug_512.jpg")
outdir=os.path.expanduser("~/Desktop/PROJECTS/story-forge/3d-spike/tex"); os.makedirs(outdir,exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
objs=[o for o in bpy.context.scene.objects if o.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active=objs[0]
if len(objs)>1: bpy.ops.object.join()
obj=bpy.context.view_layer.objects.active
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
me=obj.data
xs=[v.co.x for v in me.vertices]; zs=[v.co.z for v in me.vertices]; ys=[v.co.y for v in me.vertices]
minx,maxx=min(xs),max(xs); minz,maxz=min(zs),max(zs); miny,maxy=min(ys),max(ys)

# --- front planar UV projection (front faces -Y; project onto X-Z plane) ---
uv=me.uv_layers.new(name="front_proj")
for loop in me.loops:
    co=me.vertices[loop.vertex_index].co
    u=(co.x-minx)/(maxx-minx)
    u=1.0-u                      # mirror so portrait isn't flipped (verify by eye)
    v=(co.z-minz)/(maxz-minz)
    uv.data[loop.index].uv=(u,v)

# --- material: portrait image, but only show it on front-facing faces; fur color on back ---
img=bpy.data.images.load(portrait)
mat=bpy.data.materials.new("doug_tex"); mat.use_nodes=True
nt=mat.node_tree; nodes=nt.nodes; links=nt.links
bsdf=nodes.get("Principled BSDF")
tex=nodes.new("ShaderNodeTexImage"); tex.image=img
links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value=0.55
obj.data.materials.clear(); obj.data.materials.append(mat)

# light/world/cam (front)
sun=bpy.data.lights.new("k",'SUN'); sun.energy=4.0; so=bpy.data.objects.new("k",sun); bpy.context.scene.collection.objects.link(so); so.rotation_euler=(math.radians(55),0,math.radians(20))
w=bpy.data.worlds.new("w"); bpy.context.scene.world=w; w.use_nodes=True
bn=w.node_tree.nodes["Background"]; bn.inputs[0].default_value=(0.08,0.08,0.10,1); bn.inputs[1].default_value=1.0
H=maxz-minz; D=maxy-miny; cx=(minx+maxx)/2
cam=bpy.data.cameras.new("c"); co=bpy.data.objects.new("c",cam); bpy.context.scene.collection.objects.link(co); bpy.context.scene.camera=co
tgt=bpy.data.objects.new("t",None); bpy.context.scene.collection.objects.link(tgt); tgt.location=(cx,(miny+maxy)/2,minz+H*0.62)
con=co.constraints.new('TRACK_TO'); con.target=tgt; con.track_axis='TRACK_NEGATIVE_Z'; con.up_axis='UP_Y'
R=max(maxx-minx,D,H)*1.5; co.location=(cx,miny-R,minz+H*0.7)

sc=bpy.context.scene
for eng in ('BLENDER_EEVEE_NEXT','BLENDER_EEVEE','CYCLES'):
    try: sc.render.engine=eng; break
    except Exception: continue
sc.render.resolution_x=512; sc.render.resolution_y=512
sc.render.filepath=os.path.join(outdir,"doug_textured_front.png")
bpy.ops.render.render(write_still=True)
print("RENDERED textured front",flush=True)
