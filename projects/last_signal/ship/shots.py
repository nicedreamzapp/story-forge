# THE LAST SIGNAL - shot renderer.
# blender -b ship.blend -P shots.py -- <shot> [--samples N] [--pct P] [--test] [--norgba] [--anim]
import bpy, bmesh, sys, os, math, time, random, subprocess
from mathutils import Vector, Euler, Matrix, noise

HERE = os.path.dirname(os.path.abspath(__file__))
REN = os.path.join(HERE, "renders")
LOG = os.path.join(os.path.dirname(HERE), "logs", "ship_renders.log")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SHOT = argv[0]
def opt(name, default):
    if name in argv:
        return type(default)(argv[argv.index(name) + 1])
    return default
SAMPLES = opt("--samples", 128)
PCT = opt("--pct", 100)
TEST = "--test" in argv
NORGBA = "--norgba" in argv
FRAMES = opt("--frames", "")
R = random.Random(42)
scn = bpy.context.scene
ENV = []  # environment objects (hidden for RGBA pass)

def log(msg):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f: f.write(time.strftime("%H:%M:%S ") + msg + "\n")
    print(msg, flush=True)

# ------------------------------------------------------------------ render setup
def setup_render(w=1664, h=960):
    scn.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = 'METAL'
    prefs.get_devices()
    for d in prefs.devices: d.use = True
    c = scn.cycles
    c.device = 'GPU'; c.samples = SAMPLES; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.02
    c.use_denoising = True
    try: c.denoiser = 'OPENIMAGEDENOISE'
    except Exception: pass
    try: c.denoising_use_gpu = True
    except Exception: pass
    c.max_bounces = 6; c.diffuse_bounces = 3; c.glossy_bounces = 3; c.transmission_bounces = 4
    c.transparent_max_bounces = 16; c.volume_bounces = 0
    try: c.volume_step_rate = 6.0; c.volume_max_steps = 256
    except Exception: pass
    c.sample_clamp_indirect = 8.0
    scn.render.resolution_x = w; scn.render.resolution_y = h; scn.render.resolution_percentage = PCT
    scn.render.film_transparent = False
    scn.view_settings.view_transform = 'AgX'
    for look in ("AgX - Medium High Contrast", "Medium High Contrast", "AgX - Base Contrast"):
        try: scn.view_settings.look = look; break
        except Exception: continue
    scn.view_settings.exposure = 0.0
    scn.render.image_settings.file_format = 'PNG'
    scn.render.image_settings.color_mode = 'RGB'
    scn.render.image_settings.color_depth = '8'

# ------------------------------------------------------------------ helpers
def ob(name): return bpy.data.objects[name]
ROOT = ob("ShipRoot")
SHIP_OBS = [o for o in bpy.data.collections["Ship"].objects]

def place_ship(loc, rot_deg=(0, 0, 0)):
    ROOT.location = Vector(loc)
    ROOT.rotation_euler = Euler([math.radians(a) for a in rot_deg], 'XYZ')
    bpy.context.view_layer.update()

def ship_world(p):
    return ROOT.matrix_world @ Vector(p)

def set_legs(deploy):  # 1 = fully down, 0 = stowed (hidden in belly bays)
    for o in SHIP_OBS:
        if o.name.startswith("Leg_"):
            s = o.get("side", 1)
            o.rotation_euler = Euler((0, math.radians(80 * (1 - deploy)) * s, 0))
            o.hide_render = deploy <= 0.001

def engines(power=1.0, plume=1.0, light=2.5e6):
    for m in bpy.data.materials:
        if m.name == "M_EngineInner": m.node_tree.nodes["EngineStrength"].inputs[1].default_value = 3.5 * power
        if m.name == "M_EngineCore":
            mr = [n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeMapRange"][0]
            mr.inputs[3].default_value = mr.inputs[4].default_value = 6 * power
        if m.name == "M_Plume": m.node_tree.nodes["PlumeStrength"].inputs[1].default_value = 0.9 * plume
    ob("Ship_Plumes").hide_render = plume <= 0
    for o in SHIP_OBS:
        if o.name.startswith("EngineLight_"):
            o.data.energy = light; o.visible_camera = False; o.visible_glossy = False

def lights_gain(win=1.0, teal=1.0):
    for name, g in (("M_Window", win), ("M_Teal", teal)):
        m = bpy.data.materials[name]; base = m["base_strength"]
        mr = [n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeMapRange"][0]
        mr.inputs[3].default_value = base * 0.35 * g; mr.inputs[4].default_value = base * 1.3 * g

def camera(loc, target, lens=35, roll=0.0, name="Cam"):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_start = 0.5; cd.clip_end = 2e5
    cd.sensor_width = 36
    co = bpy.data.objects.new(name, cd); scn.collection.objects.link(co)
    co.location = Vector(loc)
    look_at(co, target, roll)
    scn.camera = co
    return co

def look_at(co, target, roll=0.0):
    d = Vector(target) - co.location
    q = d.to_track_quat('-Z', 'Y')
    co.rotation_euler = q.to_euler()
    if roll: co.rotation_euler.rotate_axis('Z', math.radians(roll))

def sun(name, rot_deg, color, strength, angle=1.0):
    ld = bpy.data.lights.new(name, 'SUN'); ld.color = color; ld.energy = strength; ld.angle = math.radians(angle)
    o = bpy.data.objects.new(name, ld); scn.collection.objects.link(o)
    o.rotation_euler = Euler([math.radians(a) for a in rot_deg]); return o

def point(name, loc, color, energy, radius=10):
    ld = bpy.data.lights.new(name, 'POINT'); ld.color = color; ld.energy = energy; ld.shadow_soft_size = radius
    o = bpy.data.objects.new(name, ld); scn.collection.objects.link(o); o.location = Vector(loc)
    o.visible_camera = False; o.visible_glossy = False; return o

def new_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    return m, nt.nodes, nt.links, nt.nodes.new("ShaderNodeOutputMaterial")

def mesh_obj(name, verts, faces, mat, env=True):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.materials.append(mat)
    o = bpy.data.objects.new(name, me); scn.collection.objects.link(o)
    if env: ENV.append(o)
    return o

# ------------------------------------------------------------------ SPACE
def world_space(neb=1.0):
    w = bpy.data.worlds.new("Space"); scn.world = w; w.use_nodes = True
    N, L = w.node_tree.nodes, w.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputWorld"); tc = N.new("ShaderNodeTexCoord")
    # stars
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 520
    L.new(tc.outputs["Generated"], vo.inputs["Vector"])
    st = N.new("ShaderNodeMapRange"); st.inputs[1].default_value = 0.03; st.inputs[2].default_value = 0.0
    st.inputs[3].default_value = 0; st.inputs[4].default_value = 1
    L.new(vo.outputs["Distance"], st.inputs[0])
    pw = N.new("ShaderNodeMath"); pw.operation = 'POWER'; pw.inputs[1].default_value = 6; L.new(st.outputs[0], pw.inputs[0])
    sm = N.new("ShaderNodeMath"); sm.operation = 'MULTIPLY'; sm.inputs[1].default_value = 3.0; L.new(pw.outputs[0], sm.inputs[0])
    # nebula
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.6; nz.inputs["Detail"].default_value = 10
    nz.inputs["Roughness"].default_value = 0.62
    L.new(tc.outputs["Generated"], nz.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements
    e[0].position = 0.45; e[0].color = (0, 0, 0, 1); e[1].position = 0.8; e[1].color = (0.35, 0.12, 0.05, 1)
    el = e.new(0.62); el.color = (0.02, 0.05, 0.07, 1)
    L.new(nz.outputs["Fac"], cr.inputs[0])
    nm = N.new("ShaderNodeMix"); nm.data_type = 'RGBA'; nm.blend_type = 'ADD'; nm.inputs[0].default_value = 1
    L.new(cr.outputs[0], nm.inputs[6])
    sc = N.new("ShaderNodeCombineColor"); [L.new(sm.outputs[0], sc.inputs[i]) for i in range(3)]
    L.new(sc.outputs[0], nm.inputs[7])
    bg = N.new("ShaderNodeBackground"); bg.inputs["Strength"].default_value = 0.06 * neb
    L.new(nm.outputs[2], bg.inputs["Color"]); L.new(bg.outputs[0], out.inputs["Surface"])

def rock_mat():
    m, N, L, out = new_mat("M_Rock")
    b = N.new("ShaderNodeBsdfPrincipled"); tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.6; nz.inputs["Detail"].default_value = 12
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.elements[0].color = (0.006, 0.0055, 0.005, 1); cr.color_ramp.elements[1].color = (0.016, 0.013, 0.011, 1)
    L.new(nz.outputs["Fac"], cr.inputs[0]); L.new(cr.outputs[0], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.92
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 3.0; L.new(tc.outputs["Object"], vo.inputs["Vector"])
    L.new(vo.outputs["Distance"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    L.new(b.outputs[0], out.inputs[0]); return m

def make_rock_meshes(n=8):
    meshes = []
    mat = rock_mat()
    for k in range(n):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0)
        sx, sy, sz = R.uniform(.6, 1.4), R.uniform(.6, 1.3), R.uniform(.5, 1.0)
        off = Vector((R.random() * 50, R.random() * 50, R.random() * 50))
        for v in bm.verts:
            p = v.co.copy()
            d = noise.fractal(p * 0.8 + off, 0.55, 2.0, 5) * 0.32
            d += noise.fractal(p * 3.0 + off, 0.5, 2.0, 3) * 0.09
            d += -abs(noise.noise(p * 1.7 + off)) * 0.10   # ridges
            v.co = Vector((p.x * sx, p.y * sy, p.z * sz)) * (1 + d)
        me = bpy.data.meshes.new(f"Rock{k}"); bm.to_mesh(me); bm.free()
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        me.materials.append(mat); meshes.append(me)
    return meshes

def asteroid_field(cam_loc, cam_dir, count=420, near=25, far=2600, avoid=None, avoid_r=0):
    meshes = make_rock_meshes()
    cam_loc = Vector(cam_loc); f = Vector(cam_dir).normalized()
    up = Vector((0, 0, 1)); rt = f.cross(up).normalized(); up = rt.cross(f)
    placed = 0; tries = 0
    while placed < count and tries < count * 20:
        tries += 1
        dist = near + (far - near) * R.random() ** 1.6
        spread = dist * 0.75
        p = cam_loc + f * dist + rt * R.uniform(-spread, spread) + up * R.uniform(-spread * .6, spread * .6)
        if avoid is not None and min((p - a).length for a in avoid) < avoid_r: continue
        size = R.uniform(1.0, 7) * (dist / 300) ** 0.45 * (5 if R.random() < .05 else 1)
        o = bpy.data.objects.new(f"Ast{placed}", R.choice(meshes)); scn.collection.objects.link(o)
        o.location = p; o.scale = (size, size, size)
        o.rotation_euler = Euler((R.random() * 6.3, R.random() * 6.3, R.random() * 6.3)); ENV.append(o); placed += 1
    return meshes

def hero_rock(loc, size, meshes):
    o = bpy.data.objects.new("HeroRock", R.choice(meshes)); scn.collection.objects.link(o)
    o.location = Vector(loc); o.scale = (size, size * .8, size * .7)
    o.rotation_euler = Euler((R.random() * 6, R.random() * 6, R.random() * 6)); ENV.append(o)

# ------------------------------------------------------------------ PLANET
def world_storm(strength=1.0, haze=0.00008):
    w = bpy.data.worlds.new("Storm"); scn.world = w; w.use_nodes = True
    N, L = w.node_tree.nodes, w.node_tree.links; N.clear()
    out = N.new("ShaderNodeOutputWorld"); tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sep.inputs[0])
    grad = N.new("ShaderNodeValToRGB"); e = grad.color_ramp.elements
    e[0].position = 0.0; e[0].color = (0.10, 0.022, 0.004, 1)
    e[1].position = 0.6; e[1].color = (0.035, 0.007, 0.002, 1)
    e2 = e.new(0.06); e2.color = (0.6, 0.14, 0.015, 1)
    e3 = e.new(0.2); e3.color = (0.32, 0.065, 0.01, 1)
    mz = N.new("ShaderNodeMapRange"); mz.inputs[1].default_value = -0.05; mz.inputs[2].default_value = 1.0
    L.new(sep.outputs["Z"], mz.inputs[0]); L.new(mz.outputs[0], grad.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.5; nz.inputs["Detail"].default_value = 9
    nz.inputs["Distortion"].default_value = 0.6
    L.new(tc.outputs["Generated"], nz.inputs["Vector"])
    nr = N.new("ShaderNodeMapRange"); nr.inputs[3].default_value = 0.35; nr.inputs[4].default_value = 1.6
    L.new(nz.outputs["Fac"], nr.inputs[0])
    mul = N.new("ShaderNodeMix"); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1
    L.new(grad.outputs[0], mul.inputs[6])
    cc = N.new("ShaderNodeCombineColor"); [L.new(nr.outputs[0], cc.inputs[i]) for i in range(3)]
    L.new(cc.outputs[0], mul.inputs[7])
    bg = N.new("ShaderNodeBackground"); bg.inputs["Strength"].default_value = 1.3 * strength
    L.new(mul.outputs[2], bg.inputs["Color"]); L.new(bg.outputs[0], out.inputs["Surface"])
    if haze > 0:
        vs = N.new("ShaderNodeVolumePrincipled"); vs.inputs["Density"].default_value = haze
        vs.inputs["Color"].default_value = (1.0, 0.36, 0.1, 1); vs.inputs["Anisotropy"].default_value = 0.4
        L.new(vs.outputs[0], out.inputs["Volume"])

def glass_ground(size=80000):
    m, N, L, out = new_mat("M_BlackGlass")
    b = N.new("ShaderNodeBsdfPrincipled"); tc = N.new("ShaderNodeTexCoord")
    b.inputs["Base Color"].default_value = (0.006, 0.004, 0.003, 1)
    b.inputs["IOR"].default_value = 1.55
    try: b.inputs["Specular IOR Level"].default_value = 0.35; b.inputs["Specular Tint"].default_value = (1.0, 0.5, 0.25, 1)
    except Exception: pass
    def facet(scale, k):
        vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = scale
        L.new(tc.outputs["Object"], vo.inputs["Vector"])
        sub = N.new("ShaderNodeVectorMath"); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = (0.5, 0.5, 0.5)
        L.new(vo.outputs["Color"], sub.inputs[0])
        scl = N.new("ShaderNodeVectorMath"); scl.operation = 'SCALE'; scl.inputs["Scale"].default_value = k
        L.new(sub.outputs[0], scl.inputs[0]); return scl, vo
    f1, v1 = facet(0.9, 0.5); f2, v2 = facet(5.0, 1.4)
    a1 = N.new("ShaderNodeVectorMath"); a1.operation = 'ADD'; L.new(f1.outputs[0], a1.inputs[0]); L.new(f2.outputs[0], a1.inputs[1])
    a2 = N.new("ShaderNodeVectorMath"); a2.operation = 'ADD'; a2.inputs[1].default_value = (0, 0, 1.0)
    L.new(a1.outputs[0], a2.inputs[0])
    nn = N.new("ShaderNodeVectorMath"); nn.operation = 'NORMALIZE'; L.new(a2.outputs[0], nn.inputs[0])
    sepc = N.new("ShaderNodeSeparateColor"); L.new(v2.outputs["Color"], sepc.inputs[0])
    gt = N.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.86
    L.new(sepc.outputs[0], gt.inputs[0])
    rr = N.new("ShaderNodeMapRange"); rr.inputs[3].default_value = 0.55; rr.inputs[4].default_value = 0.04
    L.new(gt.outputs[0], rr.inputs[0])
    gl = N.new("ShaderNodeBsdfGlossy"); gl.inputs["Color"].default_value = (0.75, 0.36, 0.14, 1)
    L.new(rr.outputs[0], gl.inputs["Roughness"]); L.new(nn.outputs[0], gl.inputs["Normal"])
    df = N.new("ShaderNodeBsdfDiffuse"); df.inputs["Color"].default_value = (0.03, 0.019, 0.013, 1)
    fr = N.new("ShaderNodeFresnel"); fr.inputs["IOR"].default_value = 1.5; L.new(nn.outputs[0], fr.inputs["Normal"])
    fm = N.new("ShaderNodeMath"); fm.operation = 'MULTIPLY'; fm.inputs[1].default_value = 0.5
    L.new(fr.outputs[0], fm.inputs[0])
    mx = N.new("ShaderNodeMixShader"); L.new(fm.outputs[0], mx.inputs[0]); L.new(df.outputs[0], mx.inputs[1]); L.new(gl.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs[0])
    s = size / 2
    o = mesh_obj("Ground", [(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [(0, 1, 2, 3)], m)
    return o, m

def shard_field(center, radius, count, mat, scale=1.0, inner=0.0):
    verts, faces = [], []
    c = Vector(center)
    for i in range(count):
        r = inner + (radius - inner) * math.sqrt(R.random()); a = R.random() * 6.283
        p = c + Vector((math.cos(a) * r, math.sin(a) * r, 0))
        h = R.uniform(.02, .12) * scale; wd = R.uniform(.1, .5) * scale
        tilt = Vector((R.uniform(-.7, .7), R.uniform(-.7, .7), 1)).normalized()
        rot = tilt.to_track_quat('Z', 'Y').to_matrix() @ Matrix.Rotation(R.random() * 6.28, 3, 'Z')
        n = R.choice((3, 4)); base = len(verts)
        for k in range(n):
            aa = 6.283 * k / n + R.uniform(-.3, .3); rr = wd * R.uniform(.5, 1.2)
            verts.append(tuple(p + rot @ Vector((math.cos(aa) * rr, math.sin(aa) * rr * .5, -0.1 * scale))))
        verts.append(tuple(p + rot @ Vector((R.uniform(-.1, .1) * wd, 0, h))))
        for k in range(n): faces.append((base + k, base + (k + 1) % n, base + n))
    return mesh_obj("Shards", verts, faces, mat)

def cloud_slab(z0, thick, box=None, size=60000, density=0.025, scale=0.0035, color=(0.85, 0.38, 0.14), cover=0.45, emit=0.0):
    m, N, L, out = new_mat("M_Cloud")
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1, 1, 2.2)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 8
    nz.inputs["Roughness"].default_value = 0.6; nz.inputs["Distortion"].default_value = 0.4
    L.new(mp.outputs[0], nz.inputs["Vector"])
    # vertical falloff (soft top/bottom)
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    vz = N.new("ShaderNodeMapRange"); vz.inputs[1].default_value = 0; vz.inputs[2].default_value = thick
    L.new(sep.outputs["Z"], vz.inputs[0])
    bell = N.new("ShaderNodeFloatCurve")
    cm = bell.mapping; cv = cm.curves[0]
    cv.points[0].location = (0, 0); cv.points[1].location = (1, 0)
    cv.points.new(0.25, 1.0); cv.points.new(0.7, 0.85); cm.update()
    L.new(vz.outputs[0], bell.inputs["Value"])
    sub = N.new("ShaderNodeMath"); sub.operation = 'MULTIPLY'; L.new(nz.outputs["Fac"], sub.inputs[0]); L.new(bell.outputs[0], sub.inputs[1])
    dr = N.new("ShaderNodeMapRange"); dr.inputs[1].default_value = cover; dr.inputs[2].default_value = cover + 0.1
    dr.inputs[3].default_value = 0; dr.inputs[4].default_value = density
    L.new(sub.outputs[0], dr.inputs[0])
    pv = N.new("ShaderNodeVolumePrincipled"); pv.inputs["Color"].default_value = (*color, 1)
    pv.inputs["Anisotropy"].default_value = 0.35
    L.new(dr.outputs[0], pv.inputs["Density"])
    if emit > 0:
        pv.inputs["Emission Strength"].default_value = emit; pv.inputs["Emission Color"].default_value = (1.0, 0.35, 0.08, 1)
    L.new(pv.outputs[0], out.inputs["Volume"])
    s = size / 2
    x0, x1, y0, y1 = box if box else (-s, s, -s, s)
    v = [(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0), (x0, y0, thick), (x1, y0, thick), (x1, y1, thick), (x0, y1, thick)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    o = mesh_obj("CloudSlab", v, f, m); o.location.z = z0
    o.visible_shadow = False
    return o, m

def storm_lighting(sun_rot=(62, 0, 140), sun_str=2.2, fill=0.0):
    s = sun("StormSun", sun_rot, (1.0, 0.5, 0.18), sun_str, angle=3)
    ENV.append(s)
    return s

def lightning(loc, energy=6e7, color=(0.85, 0.85, 1.0)):
    p = point("Lightning", loc, color, energy, radius=60); ENV.append(p); return p

# ------------------------------------------------------------------ shots
def shot_r01():
    world_space(neb=1.4)
    place_ship((0, 0, 0), (0, 0, 180))     # prow now points to -Y
    set_legs(0); engines(1.0, 0.8)
    prow = ship_world((0, 400, 24))
    cam = camera(prow + Vector((-150, -290, -38)), prow + Vector((22, 30, 2)), lens=30, roll=-6)
    # fine debris cloud around the ship for scale
    dm = make_rock_meshes(3)
    for i in range(500):
        p = ship_world((R.uniform(-260, 260), R.uniform(-300, 700), R.uniform(-150, 200)))
        if abs(p.x) < 110 and -40 < p.z < 110 and p.y < 520: continue
        o = bpy.data.objects.new("Deb", R.choice(dm)); scn.collection.objects.link(o)
        o.location = p; sz = R.uniform(.4, 2.2); o.scale = (sz, sz, sz); o.rotation_euler = Euler((R.random() * 6, R.random() * 6, 0)); ENV.append(o)
    sun("Key", (62, 0, -72), (1.0, 0.78, 0.55), 6.0, angle=0.6)
    sun("Rim", (-65, 0, 150), (0.15, 0.85, 0.8), 2.5, angle=1.0)
    sun("Fill", (150, 0, 20), (0.35, 0.4, 0.5), 0.6, angle=10)
    avoid = [ship_world((0, y, 30)) for y in range(-480, 440, 30)] + [cam.location.lerp(prow, t) for t in (0.3, 0.5, 0.7, 0.9)]
    meshes = asteroid_field(cam.location, (prow - cam.location), count=230, near=90, far=4200, avoid=avoid, avoid_r=130)
    C = cam.location; f = (prow - C).normalized(); rt = f.cross(Vector((0, 0, 1))).normalized(); up = rt.cross(f)
    for (a, b, d, sz) in ((-0.62, -0.40, 70, 15), (0.43, 0.20, 95, 14), (0.33, -0.27, 60, 7), (-0.36, 0.25, 140, 10), (0.12, 0.33, 210, 8), (-0.15, -0.30, 260, 9), (0.30, 0.05, 330, 12)):
        hero_rock(C + f * d + rt * a * d + up * b * d, sz, meshes)
    lights_gain(1.5, 1.2)

def cloud_ceiling(base, center=(0, 0), size=14000, res=300, amp=110, freq=1 / 700.0, up=False, name="CloudCeil",
                  col=(0.20, 0.05, 0.012), glow=0.6, seed=3.0, translucent=0.0, flash=0.0, lobes=True):
    m, N, L, out = new_mat("M_" + name)
    b = N.new("ShaderNodeBsdfPrincipled"); b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = 1.0
    try:
        b.inputs["Subsurface Weight"].default_value = 0.0
    except Exception: pass
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.0018; nz.inputs["Detail"].default_value = 6
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements
    e[0].position = 0.45; e[0].color = (0, 0, 0, 1); e[1].position = 0.75; e[1].color = (1.0, 0.42, 0.12, 1)
    L.new(nz.outputs["Fac"], cr.inputs[0]); L.new(cr.outputs[0], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = glow
    nz2 = N.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 0.02 if lobes else 0.008; nz2.inputs["Detail"].default_value = 12
    L.new(tc.outputs["Object"], nz2.inputs["Vector"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25 if lobes else 0.9; bp.inputs["Distance"].default_value = 10 if lobes else 60
    L.new(nz2.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    tl = N.new("ShaderNodeBsdfTranslucent"); tl.inputs["Color"].default_value = (1.0, 0.45, 0.15, 1)
    mx = N.new("ShaderNodeMixShader"); mx.inputs[0].default_value = translucent
    L.new(b.outputs[0], mx.inputs[1]); L.new(tl.outputs[0], mx.inputs[2])
    if flash > 0:
        fz = N.new("ShaderNodeTexNoise"); fz.inputs["Scale"].default_value = 0.0009; fz.inputs["Detail"].default_value = 3
        L.new(tc.outputs["Object"], fz.inputs["Vector"])
        fr_ = N.new("ShaderNodeMapRange"); fr_.inputs[1].default_value = 0.66; fr_.inputs[2].default_value = 0.78
        fr_.inputs[3].default_value = 0; fr_.inputs[4].default_value = flash
        L.new(fz.outputs["Fac"], fr_.inputs[0])
        em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.8, 0.8, 1.0, 1)
        L.new(fr_.outputs[0], em.inputs["Strength"])
        ad = N.new("ShaderNodeAddShader"); L.new(mx.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1])
        L.new(ad.outputs[0], out.inputs[0])
    else:
        L.new(mx.outputs[0], out.inputs[0])
    verts, faces = [], []
    cx, cy = center; h = size / 2
    for j in range(res + 1):
        for i in range(res + 1):
            x = cx - h + size * i / res; y = cy - h + size * j / res
            p = Vector((x * freq, y * freq, seed))
            n1 = noise.fractal(p, 0.45, 2.0, 3) if lobes else (noise.fractal(p, 0.6, 2.1, 6) + 0.5 * abs(noise.noise(p * 4.0)) + 0.25 * abs(noise.noise(p * 11.0)))
            lob = 0.5 + 0.5 * math.sin(x / 95.0 + 1.7 * math.sin(y / 140.0)) * math.sin(y / 110.0 + 1.3 * math.sin(x / 170.0))
            bump = max(0.0, n1 + 0.25) ** 1.2 * 0.8 + (0.35 * lob ** 2 if lobes else 0.0)
            z = base + (bump * amp if up else -bump * amp)
            verts.append((x, y, z))
    for j in range(res):
        for i in range(res):
            a = j * (res + 1) + i
            faces.append((a, a + 1, a + res + 2, a + res + 1))
    o = mesh_obj(name, verts, faces, m)
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    o.visible_shadow = False
    return o

def planet_base(haze=0.00012, cloud_z=1300, cloud_th=700, sun_rot=(62, 0, 140), sun_str=2.2, center=(0, 0), skirt=False, glow_up=1.0):
    world_storm(1.0, haze)
    g, gm = glass_ground()
    cs = cloud_ceiling(cloud_z, center=center)
    if skirt:
        cloud_slab(cloud_z - 190, 200, size=16000, density=0.012, scale=0.004, cover=0.42)
        ENV[-1].location.x, ENV[-1].location.y = center
    storm_lighting(sun_rot, sun_str)
    up = sun("GroundGlow", (180, 0, 0), (1.0, 0.38, 0.1), glow_up, angle=60); ENV.append(up)
    return gm, cs

def shot_r04a():
    gm, cs = planet_base(cloud_z=430, sun_rot=(-40, 0, 20), sun_str=1.8, center=(0, 2000))
    place_ship((-40, 470, 255), (-11, 0, 232))
    set_legs(0.0); engines(0.6, 0.0, 6e5)
    cam = camera((0, 0, 3.0), (-30, 600, 150), lens=18, roll=-3)
    shard_field(cam.location, 70, 5000, gm, scale=0.6, inner=7)
    lightning((650, 1500, 395), 1.4e8); lightning((-1500, 2400, 400), 5e7); lightning((350, 800, 400), 2e7)
    lights_gain(1.5, 0.22)

def shot_r04b():
    gm, cs = planet_base(cloud_z=470, sun_rot=(-35, 0, 40), sun_str=1.8, center=(0, 0))
    place_ship((20, 90, 230), (-4, 0, 205))
    set_legs(0.0); engines(0.6, 0.0, 6e5)
    cam = camera((0, 0, 2.0), (25, 150, 300), lens=20, roll=0)
    shard_field(cam.location, 60, 4000, gm, scale=0.6, inner=6)
    lightning((500, 700, 440), 1.2e8); lightning((-700, -300, 450), 5e7)
    lights_gain(1.6, 0.4)

LAND_Z = 81.2 * 1.15

def shot_r05():
    gm, cs = planet_base(cloud_z=900, sun_rot=(42, 0, 37), sun_str=2.6, center=(0, 0), glow_up=0.6)
    place_ship((0, 0, LAND_Z), (0, 0, 0))
    set_legs(1.0); engines(0.15, 0.0, 0)
    foot = ship_world((62 + 32, -30, -80.5))
    cam = camera(foot + Vector((46, -62, -10.5)), foot + Vector((-6, 8, 16)), lens=24)
    fg = Vector((foot.x, foot.y, 0))
    shard_field(fg, 90, 16000, gm, scale=0.7, inner=5)
    shard_field(fg, 24, 2500, gm, scale=1.6, inner=11)
    lightning((1200, 1500, 880), 1e8)
    point("ClawFill", cam.location + Vector((60, -40, 70)), (1.0, 0.55, 0.3), 6e5, radius=30); ENV.append(scn.objects["ClawFill"])
    lights_gain(1.5, 0.5)

def shot_r12():
    gm, cs = planet_base(cloud_z=900, sun_rot=(58, 0, 110), sun_str=1.8, center=(0, 0), glow_up=0.5)
    place_ship((0, 0, 34), (0, 0, 0))
    set_legs(0.0); engines(1.0, 0.45, 2.5e5)
    cam = camera((175, -640, 9), (10, -430, 52), lens=24)
    shard_field(Vector((175, -640, 0)), 110, 9000, gm, scale=0.7, inner=6)
    lightning((-600, -2400, 880), 1e8)
    lights_gain(1.3, 0.6)

def shot_r15():
    gm, cs = planet_base(cloud_z=950, sun_rot=(48, 0, -20), sun_str=2.2, center=(0, 0), glow_up=0.8)
    place_ship((-520, 0, 160), (10, 0, 90))   # side-on, prow to -X, nose-up
    set_legs(0.7); engines(1.2, 0.6, 1.5e6)
    cam = camera((-250, -830, 3), (-330, 0, 270), lens=24)
    shard_field(cam.location, 80, 5000, gm, scale=0.8, inner=6)
    lightning((1400, 2400, 930), 1.5e8); lightning((-2600, 1800, 930), 6e7)
    lights_gain(1.5, 0.6)

def shot_r03():
    world_storm(0.7, 0.00006)
    cloud_slab(-3000, 6500, box=(-15000, 15000, 1300, 25000), density=0.010, scale=0.0012, cover=0.47, color=(0.6, 0.2, 0.04))
    cloud_slab(-2600, 1700, box=(-15000, 15000, -15000, 1300), density=0.010, scale=0.0014, cover=0.5, color=(0.6, 0.2, 0.04))
    for o in ENV:
        m = o.data.materials[0]
        dr = [n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeMapRange" and abs(n.inputs[4].default_value - 0.010) < 1e-6][0]
        dr.inputs[2].default_value = dr.inputs[1].default_value + 0.2
    place_ship((0, 0, 380), (-24, 0, 0))   # nose down, prow +Y
    set_legs(0); engines(1.0, 0.45, 0)
    cam = camera(Vector((300, -1150, 820)), Vector((-60, 1500, 650)), lens=28, roll=5)
    sun("StormSun", (35, 0, 210), (1.0, 0.5, 0.2), 2.2, angle=2)
    lightning((400, 1700, 300), 3e8); lightning((-1300, 2200, 1300), 2e8); lightning((1600, 1900, -300), 2e8)
    lights_gain(2.2, 1.2)
    scn.view_settings.exposure = -1.3
    for m in bpy.data.materials:
        if m.name == "M_EngineInner": m.node_tree.nodes["EngineStrength"].inputs[1].default_value = 9

def shot_look():
    world_space(neb=1.0)
    place_ship((0, 0, 0), (0, 0, 0)); set_legs(1.0); engines(1.0, 0.8)
    v = Vector(tuple(float(x) for x in opt("--view", "-700,520,300").split(",")))
    camera(v, (0, 60, 10), lens=opt("--lens", 35))
    sun("Key", (50, 0, 35), (1.0, 0.78, 0.55), 5.0, angle=0.6)
    sun("Rim", (-60, 0, 160), (0.15, 0.85, 0.8), 3.0, angle=1.0)
    sun("Fill", (120, 0, 40), (0.25, 0.3, 0.4), 0.3, angle=10)

SHOTS = {"look": ("look", shot_look), "r01": ("r01_asteroids", shot_r01), "r03": ("r03_dive", shot_r03), "r04a": ("r04_arrival_a", shot_r04a),
         "r04b": ("r04_arrival_b", shot_r04b), "r05": ("r05_claws", shot_r05), "r12": ("r12_engines", shot_r12),
         "r15": ("r15_liftoff", shot_r15)}

def downscale(src, dst, w=832, h=480):
    subprocess.run(["/opt/homebrew/bin/ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vf", f"scale={w}:{h}:flags=lanczos", dst], check=True)

def render_still(outname):
    d = os.path.join(REN, "test") if TEST else REN
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, outname + ".png")
    scn.render.filepath = path
    t = time.time(); bpy.ops.render.render(write_still=True); dt = time.time() - t
    log(f"{SHOT} {outname} {scn.render.resolution_x}x{scn.render.resolution_y}@{PCT}% s={SAMPLES} {dt:.1f}s")
    if not TEST: downscale(path, os.path.join(d, outname + "_832.png"))
    if not NORGBA:
        for o in ENV:
            o.visible_camera = False
            if o.name.startswith("CloudSlab") or o.name.startswith("Ground") or o.name.startswith("Shards"):
                o.hide_render = True
        if scn.world:
            for lk in list(scn.world.node_tree.links):
                if lk.to_socket.name == "Volume": scn.world.node_tree.links.remove(lk)
        scn.render.film_transparent = True
        scn.render.image_settings.color_mode = 'RGBA'
        rp = os.path.join(d, outname + "_rgba.png"); scn.render.filepath = rp
        scn.cycles.samples = max(32, SAMPLES // 2)
        t = time.time(); bpy.ops.render.render(write_still=True)
        log(f"{SHOT} {outname}_rgba {time.time() - t:.1f}s")

# ------------------------------------------------------------------ animations
def key_ship(f, loc, rot_deg):
    place_ship(loc, rot_deg)
    ROOT.keyframe_insert("location", frame=f); ROOT.keyframe_insert("rotation_euler", frame=f)

def key_legs(f, deploy):
    for o in SHIP_OBS:
        if o.name.startswith("Leg_"):
            s_ = o.get("side", 1)
            o.rotation_euler = Euler((0, math.radians(80 * (1 - deploy)) * s_, 0))
            o.hide_render = False
            o.keyframe_insert("rotation_euler", frame=f)

def tracker(name="CamTarget"):
    e = bpy.data.objects.new(name, None); scn.collection.objects.link(e)
    return e

def track_cam(cam, target):
    c = cam.constraints.new('TRACK_TO'); c.target = target; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'

def ease_all():
    for o in bpy.data.objects:
        ad = o.animation_data
        if ad and ad.action:
            try:
                for fc in ad.action.fcurves:
                    for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'
            except Exception:
                pass

def anim_04():
    gm, cs = planet_base(cloud_z=470, sun_rot=(-40, 0, 20), sun_str=2.2, center=(0, 1500))
    set_legs(0.0); engines(0.6, 0.0, 6e5)
    scn.frame_start, scn.frame_end = 1, 96
    key_ship(1, (-30, 900, 405), (-13, 0, 186))
    key_ship(96, (10, 190, 225), (-5, 0, 181))
    cam = camera((70, -150, 5), (0, 450, 380), lens=20)
    tgt = tracker()
    tgt.location = (-10, 480, 300); tgt.keyframe_insert("location", frame=1)
    tgt.location = (10, 300, 300); tgt.keyframe_insert("location", frame=55)
    tgt.location = (22, 330, 210); tgt.keyframe_insert("location", frame=96)
    cam.location = (70, -150, 5); cam.keyframe_insert("location", frame=1)
    cam.location = (45, 130, 4); cam.keyframe_insert("location", frame=55)
    cam.location = (22, 255, 6); cam.keyframe_insert("location", frame=96)
    track_cam(cam, tgt)
    shard_field((40, 50, 0), 330, 22000, gm, scale=0.8, inner=0)
    lightning((650, 1500, 395), 1.4e8); lightning((-1500, 2400, 400), 5e7); lightning((350, 800, 400), 2e7)
    lights_gain(1.5, 0.3)
    ease_all()

def anim_15():
    gm, cs = planet_base(cloud_z=950, sun_rot=(48, 0, -20), sun_str=2.2, center=(0, 0), glow_up=0.8)
    scn.frame_start, scn.frame_end = 1, 72
    engines(1.2, 0.6, 1.5e6)
    key_ship(1, (-520, 0, LAND_Z), (0, 0, 90)); key_legs(1, 1.0)
    key_ship(14, (-520, 0, LAND_Z + 6), (0.5, 0, 90)); key_legs(14, 1.0)
    key_ship(72, (-540, 0, LAND_Z + 210), (11, 0, 90)); key_legs(72, 0.25)
    cam = camera((-250, -830, 3), (-430, 0, 120), lens=24)
    tgt = tracker()
    tgt.location = (-430, 0, 115); tgt.keyframe_insert("location", frame=1)
    tgt.location = (-430, 0, 140); tgt.keyframe_insert("location", frame=24)
    tgt.location = (-400, 0, 300); tgt.keyframe_insert("location", frame=72)
    track_cam(cam, tgt)
    shard_field(cam.location, 80, 5000, gm, scale=0.8, inner=6)
    shard_field(Vector((-500, 0, 0)), 520, 20000, gm, scale=1.0, inner=0)
    lightning((1400, 2400, 930), 1.5e8); lightning((-2600, 1800, 930), 6e7)
    lights_gain(1.5, 0.6)
    ease_all()

ANIMS = {"anim04": ("anim_04_arrival", anim_04), "anim15": ("anim_15_liftoff", anim_15)}

def render_anim(name):
    scn.render.use_motion_blur = True
    try: scn.render.motion_blur_shutter = 0.5
    except Exception: pass
    d = os.path.join(REN, "test" if TEST else name); os.makedirs(d, exist_ok=True)
    frames = [int(x) for x in FRAMES.split(",")] if FRAMES else list(range(scn.frame_start, scn.frame_end + 1))
    t0 = time.time()
    for f in frames:
        scn.frame_set(f)
        scn.render.filepath = os.path.join(d, (name + "_%04d.png") % f if TEST else "%04d.png" % f)
        if not TEST and os.path.exists(scn.render.filepath): continue   # resumable
        t = time.time(); bpy.ops.render.render(write_still=True)
        log(f"{name} frame {f} {time.time() - t:.1f}s")
    log(f"{name} total {time.time() - t0:.1f}s for {len(frames)} frames")
    if not TEST and not FRAMES:
        subprocess.run(["/opt/homebrew/bin/ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", os.path.join(d, "%04d.png"),
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", os.path.join(REN, name + ".mp4")], check=True)
        log(f"{name} mp4 written")

if __name__ == "__main__":
    if SHOT in ANIMS:
        setup_render(832, 480)
        name, fn = ANIMS[SHOT]; fn(); render_anim(name); sys.exit(0)
    setup_render()
    name, fn = SHOTS[SHOT]
    fn()
    if "--exec" in argv: exec(open(opt("--exec", "")).read()); sys.exit(0)
    render_still(name)
