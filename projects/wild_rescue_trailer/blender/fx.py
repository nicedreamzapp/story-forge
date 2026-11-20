"""Soft puffs for steam and dust (WILD RESCUE, 2026-11-01 evening).
Each puff is an icosphere with a shared Principled Volume material; its density fade rides on the object colour (R),
so one material serves every puff. Motion is physical: a puff leaves its emitter with velocity u0 (world) and air drag
k brings it to rest in the world (p = p0 + u0 (1 - e^-k tau) / k), plus a little buoyancy; it grows and thins out."""
import bpy, bmesh, math
from mathutils import Vector


def puff_mat(name, color, dens):
    """soft surface puff (2026-11-01: true volumes cost ~45 s a frame at 832x480 on the mini; a camera-facing soft
    falloff on a transparent surface reads the same in a stylised film at a tenth of the cost). `dens` = opacity."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links
    for n_ in list(N):
        N.remove(n_)
    out = N.new('ShaderNodeOutputMaterial')
    bs = N.new('ShaderNodeBsdfPrincipled')
    bs.inputs['Base Color'].default_value = (*color, 1); bs.inputs['Roughness'].default_value = 0.95
    bs.inputs['Emission Color'].default_value = (*color, 1); bs.inputs['Emission Strength'].default_value = 0.22
    tr = N.new('ShaderNodeBsdfTransparent')
    lw = N.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35
    c = N.new('ShaderNodeMath'); c.operation = 'SUBTRACT'; c.inputs[0].default_value = 1.0; L.new(lw.outputs['Facing'], c.inputs[1])
    cp = N.new('ShaderNodeMath'); cp.operation = 'POWER'; L.new(c.outputs[0], cp.inputs[0]); cp.inputs[1].default_value = 1.8
    tc = N.new('ShaderNodeTexCoord')
    nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.2; nz.inputs['Detail'].default_value = 3
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    mr = N.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.3; mr.inputs['From Max'].default_value = 0.68
    L.new(nz.outputs['Fac'], mr.inputs['Value'])
    oi = N.new('ShaderNodeObjectInfo')
    sep = N.new('ShaderNodeSeparateColor'); L.new(oi.outputs['Color'], sep.inputs[0])
    m1 = N.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; L.new(cp.outputs[0], m1.inputs[0]); L.new(mr.outputs['Result'], m1.inputs[1])
    m2 = N.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; L.new(m1.outputs[0], m2.inputs[0]); L.new(sep.outputs[0], m2.inputs[1])
    m3 = N.new('ShaderNodeMath'); m3.operation = 'MULTIPLY'; m3.use_clamp = True; L.new(m2.outputs[0], m3.inputs[0]); m3.inputs[1].default_value = dens
    mix = N.new('ShaderNodeMixShader'); L.new(m3.outputs[0], mix.inputs[0]); L.new(tr.outputs[0], mix.inputs[1]); L.new(bs.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs['Surface'])
    try:
        m.surface_render_method = 'BLENDED'
    except Exception:
        pass
    sc = bpy.context.scene
    sc.cycles.transparent_max_bounces = max(sc.cycles.transparent_max_bounces, 48)
    return m


def volume_puffs(name, births, frames, fps, color=(1, 1, 1), coll=None, buoy=0.6, dens=None):
    """births: list of dict(f, p0, u0, k, r0, grow, life, dens). Keys location/scale/colour on every frame in `frames`."""
    coll = coll or bpy.context.scene.collection
    me = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    for f_ in bm.faces:
        f_.smooth = True
    bm.to_mesh(me); bm.free()
    mat = puff_mat(name + "_vol", color, dens if dens is not None else births[0].get("dens", 6.0))
    me.materials.append(mat)
    frames = list(frames)
    obs = []
    for i, b in enumerate(births):
        # skip puffs that are dead before the first frame or born after the last
        if b["f"] + b["life"] * fps < frames[0] - 1 or b["f"] > frames[-1] + 1:
            continue
        o = bpy.data.objects.new(f"{name}_{i:03d}", me); coll.objects.link(o)
        o.rotation_euler = (i * 1.3, i * 0.7, i * 2.1)
        for f in frames:
            tau = (f - b["f"]) / fps
            if tau < 0 or tau > b["life"]:
                o.location = b["p0"]; o.scale = (1e-4,) * 3; o.color = (0, 0, 0, 1)
            else:
                k = b["k"]
                p = b["p0"] + b["u0"] * ((1 - math.exp(-k * tau)) / k) + Vector((0, 0, buoy * tau * tau))
                r = b["r0"] + b["grow"] * tau
                fade = min(1.0, tau / 0.06) * max(0.0, 1.0 - tau / b["life"]) ** 1.3
                o.location = p; o.scale = (r, r, r * 0.9); o.color = (fade * b.get("dmul", 1.0), 0, 0, 1)
            o.keyframe_insert("location", frame=f); o.keyframe_insert("scale", frame=f); o.keyframe_insert("color", frame=f)
        obs.append(o)
    print(f"[fx] {name}: {len(obs)} puffs", flush=True)
    return obs
