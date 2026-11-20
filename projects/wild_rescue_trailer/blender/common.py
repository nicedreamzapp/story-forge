"""Shared helpers for the Wild Rescue Blender prop builds (deterministic, headless)."""
import bpy, bmesh, math, random, os, time, sys
from mathutils import Vector, Matrix, Euler, noise

HERE = os.path.dirname(os.path.abspath(__file__))
RENDERS = os.path.join(HERE, "renders")
HAZE = (1.0, 0.74, 0.52)
_COLL = [None]


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def setup_gpu(scene):
    prefs = bpy.context.preferences.addons['cycles'].preferences
    if os.environ.get("WR_CPU", "0") == "1":   # the PC (Iris Xe, no Metal/CUDA): Cycles on CPU
        scene.cycles.device = 'CPU'
        print("GPU_DEVICES: none (WR_CPU=1, CPU render)")
        return []
    prefs.compute_device_type = 'METAL'
    try:
        prefs.refresh_devices()
    except Exception:
        prefs.get_devices()
    used = []
    for d in prefs.devices:
        d.use = (d.type != 'CPU')
        if d.use:
            used.append(f"{d.name}[{d.type}]")
    scene.cycles.device = 'GPU'
    print("GPU_DEVICES:", used, "compute_device_type:", prefs.compute_device_type, "scene.device:", scene.cycles.device)
    return used


def setup_render(scene, w=1248, h=720, samples=48):
    scene.render.engine = 'CYCLES'
    setup_gpu(scene)
    c = scene.cycles
    c.samples = samples
    c.use_adaptive_sampling = True
    c.adaptive_threshold = 0.02
    c.use_denoising = True
    c.denoiser = 'OPENIMAGEDENOISE'
    try:
        c.denoising_use_gpu = True
    except Exception:
        pass
    c.max_bounces = 6
    c.diffuse_bounces = 3
    c.glossy_bounces = 3
    c.transmission_bounces = 4
    c.volume_bounces = 0
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.sample_clamp_indirect = 8.0
    scene.render.resolution_x = w
    scene.render.resolution_y = h
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.use_persistent_data = True
    if os.environ.get("WR_LOWMEM", "1") == "1":
        # the mini (2026-11-01): forge_guard SIGTERMs any unleased process whose phys_footprint (RSS + Metal buffers)
        # passes 12 GB while the box is critical; a 832x480 wagon test measured 20 GB on Metal with GPU OIDN.
        # Small tiles, CPU denoise, no persistent data keep Blender under the line.
        scene.render.use_persistent_data = False
        c.use_auto_tile = True
        c.tile_size = int(os.environ.get("WR_TILE", "512"))
        try:
            c.denoising_use_gpu = False
        except Exception:
            pass
        if os.environ.get("WR_CPU", "0") == "1":
            scene.cycles.device = 'CPU'
    vs = scene.view_settings
    vs.view_transform = 'AgX'
    for look in ('AgX - Punchy', 'Punchy', 'AgX - High Contrast', 'High Contrast'):
        try:
            vs.look = look
            break
        except Exception:
            continue
    vs.exposure = -0.25
    if os.environ.get("WR_SAMPLES"):
        c.samples = int(os.environ["WR_SAMPLES"])
    # per-shot override (PC CPU time budget, 2026-11-01): lines "<shot> <w> <h> <samples>" in res_override.txt
    ov = os.path.join(HERE, "res_override.txt")
    if os.path.exists(ov) and "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
        for line in open(ov):
            p = line.split()
            if len(p) == 4 and p[0] in args and "--test" not in args:
                scene.render.resolution_x, scene.render.resolution_y, c.samples = int(p[1]), int(p[2]), int(p[3])
                print("RES_OVERRIDE", p, flush=True)
    if os.environ.get("WR_ENGINE", "") == "EEVEE":   # PC fallback (Iris Xe): EEVEE Next on the integrated GPU
        scene.render.engine = 'BLENDER_EEVEE'
        e = scene.eevee
        e.taa_render_samples = int(os.environ.get("WR_EEVEE_SAMPLES", "48"))
        for k, v in (("use_raytracing", True), ("use_shadows", True), ("shadow_ray_count", 2), ("shadow_step_count", 8),
                     ("use_volumetric_shadows", False), ("fast_gi_method", 'GLOBAL_ILLUMINATION')):
            try:
                setattr(e, k, v)
            except Exception as ex:
                print("eevee setting skipped", k, ex)
    print("LOOK:", vs.view_transform, vs.look, "engine", scene.render.engine, "samples", c.samples)


# ---------------------------------------------------------------- collections
def new_coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def set_coll(c):
    _COLL[0] = c


def link(ob):
    (_COLL[0] or bpy.context.scene.collection).objects.link(ob)
    return ob


# ---------------------------------------------------------------- materials
def nodes_mat(name):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    return m, nt, b


def flat_mat(name, color, rough=0.45, metal=0.0, coat=0.0, emit=None, emit_str=0.0, alpha=1.0):
    m, nt, b = nodes_mat(name)
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if coat:
        b.inputs['Coat Weight'].default_value = coat
        b.inputs['Coat Roughness'].default_value = 0.15
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = emit_str
    return m


def _ramp(N, stops, constant=False):
    cr = N.new('ShaderNodeValToRGB')
    els = cr.color_ramp.elements
    els[0].position = stops[0][0]; els[0].color = (*stops[0][1], 1)
    els[1].position = stops[-1][0]; els[1].color = (*stops[-1][1], 1)
    for p, col in stops[1:-1]:
        e = els.new(p); e.color = (*col, 1)
    if constant:
        cr.color_ramp.interpolation = 'CONSTANT'
    return cr


def ramp_mat(name, tex='noise', stops=((0, (1, 1, 1)), (1, (0, 0, 0))), rough=0.5, metal=0.0,
             bump=0.0, bump_dist=0.02, scale=1.0, map_scale=(1, 1, 1), detail=4.0, distortion=0.0,
             constant=False, haze=0.0, coat=0.0, coord='Object'):
    m, nt, b = nodes_mat(name)
    N, L = nt.nodes, nt.links
    tc = N.new('ShaderNodeTexCoord')
    mp = N.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = map_scale
    L.new(tc.outputs[coord], mp.inputs['Vector'])
    if tex == 'noise':
        t = N.new('ShaderNodeTexNoise')
        t.inputs['Scale'].default_value = scale
        t.inputs['Detail'].default_value = detail
        t.inputs['Distortion'].default_value = distortion
        fac = t.outputs['Fac']
    elif tex.startswith('wave'):
        t = N.new('ShaderNodeTexWave')
        t.wave_type = 'BANDS'
        t.bands_direction = tex[-1].upper()
        t.inputs['Scale'].default_value = scale
        t.inputs['Distortion'].default_value = distortion
        t.inputs['Detail'].default_value = detail
        fac = t.outputs['Fac']
    elif tex == 'voronoi_edge':
        t = N.new('ShaderNodeTexVoronoi')
        t.feature = 'DISTANCE_TO_EDGE'
        t.inputs['Scale'].default_value = scale
        fac = t.outputs['Distance']
    elif tex == 'brick':
        t = N.new('ShaderNodeTexBrick')
        t.inputs['Scale'].default_value = scale
        t.inputs['Mortar Size'].default_value = 0.025
        t.inputs['Color1'].default_value = (0.2, 0.2, 0.2, 1)
        t.inputs['Color2'].default_value = (0.8, 0.8, 0.8, 1)
        t.inputs['Mortar'].default_value = (0.0, 0.0, 0.0, 1)
        fac = t.outputs['Color']
    L.new(mp.outputs['Vector'], t.inputs['Vector'])
    cr = _ramp(N, stops, constant)
    L.new(fac, cr.inputs['Fac'])
    L.new(cr.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if coat:
        b.inputs['Coat Weight'].default_value = coat
        b.inputs['Coat Roughness'].default_value = 0.12
    if bump:
        bp = N.new('ShaderNodeBump')
        bp.inputs['Strength'].default_value = bump
        bp.inputs['Distance'].default_value = bump_dist
        L.new(fac, bp.inputs['Height'])
        L.new(bp.outputs['Normal'], b.inputs['Normal'])
    if haze:
        add_haze(m, haze)
    return m


def add_haze(m, H=900.0, color=HAZE):
    nt = m.node_tree; N = nt.nodes; L = nt.links
    out = [n for n in N if n.type == 'OUTPUT_MATERIAL'][0]
    b = N.get('Principled BSDF')
    cam = N.new('ShaderNodeCameraData')
    m1 = N.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; m1.inputs[1].default_value = -1.0 / H
    L.new(cam.outputs['View Distance'], m1.inputs[0])
    ex = N.new('ShaderNodeMath'); ex.operation = 'EXPONENT'
    L.new(m1.outputs[0], ex.inputs[0])
    inv = N.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    L.new(ex.outputs[0], inv.inputs[1])
    em = N.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (*color, 1)
    em.inputs['Strength'].default_value = 1.0
    mix = N.new('ShaderNodeMixShader')
    L.new(inv.outputs[0], mix.inputs[0])
    L.new(b.outputs[0], mix.inputs[1])
    L.new(em.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs['Surface'])


def wood_mat(name, dark, light, along='X', rough=0.45, coat=0.25, bump=0.08):
    ms = {'X': (0.6, 14, 14), 'Y': (14, 0.6, 14), 'Z': (14, 14, 0.6)}[along]
    return ramp_mat(name, 'noise', ((0.3, dark), (0.5, light), (0.72, dark)), rough=rough,
                    bump=bump, bump_dist=0.004, scale=2.5, map_scale=ms, detail=6, distortion=0.6, coat=coat)


def strata_mat(name, haze=0.0):
    stops = ((0.0, (0.45, 0.1, 0.04)), (0.2, (0.7, 0.24, 0.08)), (0.38, (0.85, 0.42, 0.18)),
             (0.52, (0.55, 0.15, 0.05)), (0.7, (0.88, 0.55, 0.3)), (0.85, (0.62, 0.2, 0.07)),
             (1.0, (0.42, 0.1, 0.04)))
    return ramp_mat(name, 'wave_z', stops, rough=0.85, bump=0.35, bump_dist=0.3, scale=0.05,
                    distortion=3.5, detail=4, haze=haze)


def world_sky(strength=1.0):
    w = bpy.data.worlds.new("Sky")
    bpy.context.scene.world = w
    try:
        w.use_nodes = True
    except Exception:
        pass
    N = w.node_tree.nodes; L = w.node_tree.links
    bg = N.get('Background') or N.new('ShaderNodeBackground')
    out = [n for n in N if n.type == 'OUTPUT_WORLD'][0]
    tc = N.new('ShaderNodeTexCoord')
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(tc.outputs['Generated'], sep.inputs[0])
    cr = _ramp(N, ((0.0, HAZE), (0.05, (1.0, 0.8, 0.55)), (0.14, (0.45, 0.85, 0.85)),
                   (0.38, (0.05, 0.55, 0.75)), (1.0, (0.01, 0.22, 0.55))))
    L.new(sep.outputs['Z'], cr.inputs['Fac'])
    L.new(cr.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = strength
    L.new(bg.outputs[0], out.inputs['Surface'])
    return w


def sun(to_sun, energy=4.5, angle_deg=7.0, color=(1.0, 0.8, 0.58)):
    ld = bpy.data.lights.new("Sun", 'SUN')
    ld.energy = energy
    ld.angle = math.radians(angle_deg)
    ld.color = color
    ob = bpy.data.objects.new("Sun", ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.rotation_euler = Vector(to_sun).normalized().to_track_quat('Z', 'Y').to_euler()
    return ob


def camera(name="Cam"):
    cd = bpy.data.cameras.new(name)
    cd.clip_start = 0.01
    cd.clip_end = 6000
    ob = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.scene.camera = ob
    return ob


def look_at(cam, loc, target, lens=35, fstop=None, focus=None, roll=0.0):
    cam.location = Vector(loc)
    d = Vector(target) - Vector(loc)
    q = d.to_track_quat('-Z', 'Y')
    if roll:
        q = q @ Euler((0, 0, math.radians(roll))).to_quaternion()
    cam.rotation_euler = q.to_euler()
    cam.data.lens = lens
    if fstop:
        cam.data.dof.use_dof = True
        cam.data.dof.aperture_fstop = fstop
        cam.data.dof.focus_distance = focus if focus else d.length
    else:
        cam.data.dof.use_dof = False


# ---------------------------------------------------------------- meshes
def _finish(name, bm, mat=None, loc=(0, 0, 0), rot=(0, 0, 0), smooth=None):
    """smooth: None=flat, True=all smooth, 'sides'=smooth faces not facing local Z."""
    if smooth == 'sides':
        bm.normal_update()
        for f in bm.faces:
            f.smooth = abs(f.normal.z) < 0.7
    elif smooth:
        for f in bm.faces:
            f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if mat:
        me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    link(ob)
    ob.location = Vector(loc)
    ob.rotation_euler = Euler(rot)
    return ob


def box(name, size, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    if bevel > 0:
        try:
            bmesh.ops.bevel(bm, geom=bm.verts[:] + bm.edges[:], offset=bevel, segments=2,
                            affect='EDGES', profile=0.5, clamp_overlap=True)
        except Exception as e:
            print("bevel fail", e)
    return _finish(name, bm, mat, loc, rot)


def ellipsoid(name, r, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, seg=24):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(8, seg // 2), radius=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * r[0], v.co.y * r[1], v.co.z * r[2]))
    return _finish(name, bm, mat, loc, rot, smooth=True)


def sphere(name, r, loc=(0, 0, 0), mat=None, seg=20):
    return ellipsoid(name, (r, r, r), loc, (0, 0, 0), mat, seg)


AXIS_ROT = {'Z': Matrix.Identity(4), 'Y': Matrix.Rotation(-math.pi / 2, 4, 'X'),
            'X': Matrix.Rotation(math.pi / 2, 4, 'Y')}


def cyl(name, r1, r2, depth, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, seg=24, axis='Z', squash=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r1, radius2=r2, depth=depth)
    bm.normal_update()
    for f in bm.faces:
        f.smooth = abs(f.normal.z) < 0.7
    bmesh.ops.transform(bm, matrix=AXIS_ROT[axis], verts=bm.verts)
    if squash:
        for v in bm.verts:
            v.co = Vector((v.co.x * squash[0], v.co.y * squash[1], v.co.z * squash[2]))
    return _finish(name, bm, mat, loc, rot)


def cyl_between(name, p1, p2, r1, r2=None, mat=None, seg=12):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    ob = cyl(name, r1, r2 if r2 is not None else r1, d.length, (p1 + p2) / 2, (0, 0, 0), mat, seg)
    ob.rotation_euler = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_euler()
    return ob


def lathe(name, prof, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, seg=32, axis='Z', closed=False, caps=True, scale=None):
    """prof = [(r, z), ...] revolved around Z (then mapped to axis)."""
    bm = bmesh.new()
    rings = []
    for (r, z) in prof:
        ring = [bm.verts.new((r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg), z)) for i in range(seg)]
        rings.append(ring)
    n = len(rings)
    pairs = [(k, k + 1) for k in range(n - 1)] + ([(n - 1, 0)] if closed else [])
    for a, b in pairs:
        for i in range(seg):
            j = (i + 1) % seg
            try:
                bm.faces.new((rings[a][i], rings[a][j], rings[b][j], rings[b][i]))
            except ValueError:
                pass
    if caps and not closed:
        if prof[0][0] > 1e-4:
            bm.faces.new(list(reversed(rings[0])))
        if prof[-1][0] > 1e-4:
            bm.faces.new(rings[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bm.normal_update()
    for f in bm.faces:
        f.smooth = len(f.verts) == 4
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.transform(bm, matrix=AXIS_ROT[axis], verts=bm.verts)
    if scale:
        for v in bm.verts:
            v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2]))
    return _finish(name, bm, mat, loc, rot)


def torus(name, R, r, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, seg=48, rseg=12, axis='Z', scale=None):
    prof = [(R + r * math.cos(2 * math.pi * k / rseg), r * math.sin(2 * math.pi * k / rseg)) for k in range(rseg)]
    return lathe(name, prof, loc, rot, mat, seg, axis, closed=True, scale=scale)


def tube(name, r_in, r_out, width, loc=(0, 0, 0), rot=(0, 0, 0), mat=None, seg=64, axis='Y'):
    w = width / 2
    prof = [(r_out, -w), (r_out, w), (r_in, w), (r_in, -w)]
    return lathe(name, prof, loc, rot, mat, seg, axis, closed=True)


def poly_curve(name, pts, radius, mat=None):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts):
        p.co = (c[0], c[1], c[2], 1)
    cu.bevel_depth = radius
    cu.bevel_resolution = 2
    cu.use_fill_caps = True
    if mat:
        cu.materials.append(mat)
    ob = bpy.data.objects.new(name, cu)
    link(ob)
    return ob


def sag_points(a, b, sag, n=12):
    a, b = Vector(a), Vector(b)
    return [tuple(a.lerp(b, t) - Vector((0, 0, sag * 4 * t * (1 - t)))) for t in [i / n for i in range(n + 1)]]


def join(name, objs, origin=(0, 0, 0)):
    """Merge mesh objects (keeps materials per part) into one object with given origin."""
    origin = Vector(origin)
    bm = bmesh.new()
    mats = []
    for ob in objs:
        if ob.type != 'MESH':
            continue
        tmp = bmesh.new()
        tmp.from_mesh(ob.data)
        M = (Matrix.Translation(Vector(ob.location) - origin) @ ob.rotation_euler.to_matrix().to_4x4()
             @ Matrix.Diagonal((*ob.scale, 1.0)))
        bmesh.ops.transform(tmp, matrix=M, verts=tmp.verts)
        m = ob.data.materials[0] if len(ob.data.materials) else None
        if m not in mats:
            mats.append(m)
        idx = mats.index(m)
        for f in tmp.faces:
            f.material_index = idx
        me2 = bpy.data.meshes.new('tmpjoin')
        tmp.to_mesh(me2)
        tmp.free()
        bm.from_mesh(me2)
        bpy.data.meshes.remove(me2)
        old = ob.data
        bpy.data.objects.remove(ob)
        bpy.data.meshes.remove(old)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    link(ob)
    ob.location = origin
    return ob


def parent_keep(child, parent):
    bpy.context.view_layer.update()
    mw = child.matrix_world.copy()
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()
    return child


def empty(name, loc=(0, 0, 0)):
    ob = bpy.data.objects.new(name, None)
    link(ob)
    ob.location = Vector(loc)
    return ob


def grid_mesh(name, xs, ys, hfun, mat=None, flat_steep=0.8):
    nx = len(xs)
    verts = [(x, y, hfun(x, y)) for y in ys for x in xs]
    faces = [(j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i)
             for j in range(len(ys) - 1) for i in range(nx - 1)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    sm = [p.normal.z > flat_steep for p in me.polygons]
    me.polygons.foreach_set('use_smooth', sm)
    if mat:
        me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    link(ob)
    return ob


def axis_samples(segs):
    """segs = [(start, stop, step), ...] -> sorted unique list"""
    out = set()
    for a, b, s in segs:
        n = int(round((b - a) / s))
        for i in range(n + 1):
            out.add(round(a + i * (b - a) / n, 4))
    return sorted(out)


def dunes(x, y, amp=1.0):
    p = Vector((x / 45.0, y / 45.0, 0.3))
    q = Vector((x / 9.0, y / 9.0, 1.7))
    return amp * (0.9 * noise.noise(p) + 0.18 * noise.noise(q))


def mesa(name, loc, r, h, mat, seed):
    rnd = random.Random(seed)
    seg = 22
    prof = [(1.55, 0.0), (1.2, 0.12), (1.04, 0.3), (1.0, 0.55), (0.95, 0.85), (0.93, 0.97), (0.9, 1.0)]
    bm = bmesh.new()
    ph = rnd.uniform(0, 100)
    rings = []
    for (rf, zf) in prof:
        ring = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            nf = 1 + 0.22 * noise.noise(Vector((math.cos(a) * 1.4 + ph, math.sin(a) * 1.4, zf * 0.6)))
            rr = r * rf * nf
            ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), h * zf - (1.5 if zf == 0 else 0))))
        rings.append(ring)
    for k in range(len(rings) - 1):
        for i in range(seg):
            j = (i + 1) % seg
            bm.faces.new((rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]))
    bm.faces.new(rings[-1])
    return _finish(name, bm, mat, loc, (0, 0, rnd.uniform(0, 6.28)))


def scatter(name, n, region, hfun, avoid, kind, mat, seed):
    """Joined scatter of rocks / bushes / cacti into one mesh."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    placed = 0
    tries = 0
    while placed < n and tries < n * 20:
        tries += 1
        x = rnd.uniform(region[0], region[1]); y = rnd.uniform(region[2], region[3])
        if avoid(x, y):
            continue
        z = hfun(x, y)
        if kind == 'rock':
            s = rnd.uniform(0.15, 0.9) * (1.0 if rnd.random() > 0.08 else 2.5)
            M = Matrix.Translation((x, y, z)) @ Euler((rnd.random(), rnd.random(), rnd.random() * 6)).to_matrix().to_4x4() \
                @ Matrix.Diagonal((s * rnd.uniform(0.8, 1.6), s, s * rnd.uniform(0.5, 0.9), 1))
            bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0, matrix=M)
        elif kind == 'bush':
            s = rnd.uniform(0.35, 0.9)
            for k in range(3):
                M = Matrix.Translation((x + rnd.uniform(-0.4, 0.4) * s, y + rnd.uniform(-0.4, 0.4) * s, z + 0.15 * s)) \
                    @ Matrix.Diagonal((s, s, s * 0.7, 1))
                bmesh.ops.create_icosphere(bm, subdivisions=2, radius=rnd.uniform(0.5, 0.8), matrix=M)
        elif kind == 'cactus':
            hgt = rnd.uniform(4.0, 7.0); rr = rnd.uniform(0.28, 0.4)
            bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=rr, radius2=rr, depth=hgt,
                                  matrix=Matrix.Translation((x, y, z + hgt / 2)))
            bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=8, radius=rr, matrix=Matrix.Translation((x, y, z + hgt)))
            a0 = rnd.uniform(0, 6.28)
            for side in (-1, 1):
                if rnd.random() < 0.75:
                    a = a0 if side < 0 else a0 + math.pi
                    ax = (math.cos(a), math.sin(a))
                    hz = z + hgt * rnd.uniform(0.35, 0.55); ar = rr * 0.7; out = rnd.uniform(0.7, 1.0)
                    mid = Vector((x + ax[0] * out / 2, y + ax[1] * out / 2, hz))
                    bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=ar, radius2=ar, depth=out,
                                          matrix=Matrix.Translation(mid) @ Vector((0, 0, 1)).rotation_difference(Vector((ax[0], ax[1], 0))).to_matrix().to_4x4())
                    up = rnd.uniform(1.2, 2.2)
                    tip = Vector((x + ax[0] * out, y + ax[1] * out, hz))
                    bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=ar, radius2=ar, depth=up,
                                          matrix=Matrix.Translation(tip + Vector((0, 0, up / 2))))
                    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=ar, matrix=Matrix.Translation(tip + Vector((0, 0, up))))
                    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=ar, matrix=Matrix.Translation(tip))
        placed += 1
    for f in bm.faces:
        f.smooth = True
    return _finish(name, bm, mat)


def desert_mats():
    sand = ramp_mat("sand", 'noise', ((0.0, (0.62, 0.26, 0.1)), (0.5, (0.8, 0.4, 0.17)), (1.0, (0.9, 0.55, 0.28))),
                    rough=0.9, bump=0.25, bump_dist=0.05, scale=0.35, detail=8, haze=900)
    rock = ramp_mat("rock", 'noise', ((0.2, (0.42, 0.13, 0.06)), (0.8, (0.7, 0.3, 0.14))), rough=0.85, bump=0.4, scale=3, haze=700)
    bush = ramp_mat("bush", 'noise', ((0.3, (0.25, 0.32, 0.1)), (0.8, (0.5, 0.55, 0.22))), rough=0.8, scale=6, bump=0.5, haze=700)
    cactus = ramp_mat("cactus", 'wave_x', ((0.3, (0.1, 0.3, 0.1)), (0.7, (0.25, 0.5, 0.18))), rough=0.6, scale=4, bump=0.3, haze=700, coord='Object')
    return dict(sand=sand, rock=rock, bush=bush, cactus=cactus, strata=strata_mat("strata_far", haze=2500))


def mesas_ring(mat, specs, coll=None):
    obs = []
    for i, (ang, dist, r, h) in enumerate(specs):
        a = math.radians(ang)
        obs.append(mesa(f"mesa{i}", (dist * math.cos(a), dist * math.sin(a), -2), r, h, mat, 100 + i))
    return obs


def render_still(scene, path):
    scene.render.filepath = path
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t0
    print(f"RENDER_TIME {os.path.basename(path)} {dt:.1f}s")
    return dt
