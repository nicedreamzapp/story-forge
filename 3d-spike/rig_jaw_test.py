import bpy, bmesh, math, os, sys
from mathutils import Vector
glb="/Users/dtribe/AI/ComfyUI/output/doug_spike_00001_.glb"
outdir=os.path.expanduser("~/Desktop/PROJECTS/story-forge/3d-spike/rig"); os.makedirs(outdir,exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
objs=[o for o in bpy.context.scene.objects if o.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active=objs[0]
if len(objs)>1: bpy.ops.object.join()
obj=bpy.context.view_layer.objects.active
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)

# bbox in world coords (Blender Z-up after gltf import). Face points toward -Y (confirmed by prior front render).
me=obj.data
xs=[v.co.x for v in me.vertices]; ys=[v.co.y for v in me.vertices]; zs=[v.co.z for v in me.vertices]
minx,maxx=min(xs),max(xs); miny,maxy=min(ys),max(ys); minz,maxz=min(zs),max(zs)
H=maxz-minz; D=maxy-miny
print(f"bbox x[{minx:.2f},{maxx:.2f}] y[{miny:.2f},{maxy:.2f}] z[{minz:.2f},{maxz:.2f}] H={H:.2f} D={D:.2f}",flush=True)

# head = top 42% in Z; muzzle = frontmost (low Y) within head
head_z = minz + H*0.58
head_verts=[v for v in me.vertices if v.co.z>head_z]
hy=[v.co.y for v in head_verts]; muzzle_front=min(hy)
muzzle_depth = (max(hy)-muzzle_front)
print(f"head_z={head_z:.2f} muzzle_front_y={muzzle_front:.2f} head_depth={muzzle_depth:.2f}",flush=True)

# jaw/lower-mouth region: head, frontmost ~40% depth, lower part of head height
mouth_z_hi = head_z + H*0.20      # below this z = jaw candidate
sk_basis = obj.shape_key_add(name="Basis", from_mix=False)
sk_open  = obj.shape_key_add(name="jaw_open", from_mix=False)
hinge_y = muzzle_front + muzzle_depth*0.55   # jaw pivots at back of muzzle
sel=0
for i,v in enumerate(me.vertices):
    in_head = v.co.z>head_z
    in_front = v.co.y < muzzle_front + muzzle_depth*0.5
    in_lower = v.co.z < mouth_z_hi
    if in_head and in_front and in_lower:
        # falloff: more open toward the front tip
        t=max(0.0,(hinge_y - v.co.y)/(hinge_y-muzzle_front+1e-6))
        drop = H*0.16*t
        fwd  = D*0.05*t
        sk_open.data[i].co = v.co + Vector((0,-fwd,-drop))
        sel+=1
print(f"jaw verts selected: {sel}",flush=True)

# render helper
def render(name, openval):
    obj.data.shape_keys.key_blocks["jaw_open"].value=openval
    sc=bpy.context.scene
    for eng in ('BLENDER_EEVEE_NEXT','BLENDER_EEVEE','CYCLES'):
        try: sc.render.engine=eng; break
        except Exception: continue
    sc.render.resolution_x=512; sc.render.resolution_y=512
    sc.render.filepath=os.path.join(outdir,name)
    bpy.ops.render.render(write_still=True); print("rendered",name,flush=True)

# material + light + cam (front, slight low angle to see mouth)
mat=bpy.data.materials.new("clay"); mat.use_nodes=True
b=mat.node_tree.nodes.get("Principled BSDF"); b.inputs["Base Color"].default_value=(0.82,0.55,0.34,1); b.inputs["Roughness"].default_value=0.6
obj.data.materials.clear(); obj.data.materials.append(mat)
sun=bpy.data.lights.new("s",'SUN'); sun.energy=4.5; so=bpy.data.objects.new("s",sun); bpy.context.scene.collection.objects.link(so); so.rotation_euler=(math.radians(50),0,math.radians(25))
w=bpy.data.worlds.new("w"); bpy.context.scene.world=w; w.use_nodes=True; w.node_tree.nodes["Background"].inputs[0].default_value=(0.05,0.05,0.06,1)
cx=(minx+maxx)/2; cz=minz+H*0.72; R=max(maxx-minx,D,H)*1.5
cam=bpy.data.cameras.new("c"); co=bpy.data.objects.new("c",cam); bpy.context.scene.collection.objects.link(co); bpy.context.scene.camera=co
tgt=bpy.data.objects.new("t",None); bpy.context.scene.collection.objects.link(tgt); tgt.location=(cx,(miny+maxy)/2,cz)
con=co.constraints.new('TRACK_TO'); con.target=tgt; con.track_axis='TRACK_NEGATIVE_Z'; con.up_axis='UP_Y'
co.location=(cx, miny-R, cz+H*0.08)   # in front (-Y), slightly raised

render("jaw_closed.png",0.0)
render("jaw_open.png",1.0)
print("DONE",flush=True)
