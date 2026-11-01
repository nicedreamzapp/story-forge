# THE LAST SIGNAL - procedural hero ship generator (re-runnable, deterministic)
# blender -b -P build_ship.py      -> writes ship.blend next to this file
# Units: 1 BU = 10 m. Ship ~ 8.6 km long. Forward = +Y, up = +Z, belly at z=0.
import bpy, bmesh, math, random, os, time
from mathutils import Vector, Matrix

T0 = time.time()
HERE = os.path.dirname(os.path.abspath(__file__))
R = random.Random(1977)

L0, L1 = -400.0, 400.0

# ---------------------------------------------------------------- profile
def hw(y):  # half width
    t = (y - L0) / (L1 - L0)
    w = 86 + (56 - 86) * t
    if t > 0.9:
        k = (t - 0.9) / 0.1
        w *= 1 - 0.33 * k ** 1.6
    return w

def zbot(y):
    t = (y - L0) / (L1 - L0)
    return 7.0 * ((t - 0.9) / 0.1) ** 2 if t > 0.9 else 0.0

def htop(y):
    t = (y - L0) / (L1 - L0)
    h = 62 + (44 - 62) * t
    if t > 0.88:
        k = (t - 0.88) / 0.12
        h *= 1 - 0.38 * k ** 1.3
    return h

def hull_sec(y):
    w, zb, H = hw(y), zbot(y), htop(y)
    hh = H - zb
    return [(0.82 * w, zb), (w, zb + 0.22 * hh), (w, zb + 0.62 * hh), (0.78 * w, H),
            (-0.78 * w, H), (-w, zb + 0.62 * hh), (-w, zb + 0.22 * hh), (-0.82 * w, zb)]

# ---------------------------------------------------------------- accum mesh
class Acc:
    def __init__(s):
        s.v, s.f, s.mat, s.pr, s.glow = [], [], [], [], []

    def _face(s, idx, mat, pr):
        s.f.append(idx); s.mat.append(mat); s.pr.append(pr)

    def box(s, c, M, sx, sy, sz, mat=0, pr=None, z0=0.0, topmat=None):
        if pr is None: pr = R.random()
        b = len(s.v)
        for zi in (0, 1):
            for yi in (0, 1):
                for xi in (0, 1):
                    lp = Vector(((xi - .5) * sx, (yi - .5) * sy, z0 + zi * sz))
                    s.v.append(tuple(c + M @ lp)); s.glow.append(0.0)
        F = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
        for i, q in enumerate(F):
            m = topmat if (topmat is not None and i == 1) else mat
            s._face(tuple(b + k for k in q), m, pr)

    def quad(s, c, M, sx, sy, z, mat, pr):
        b = len(s.v)
        for (x, y) in ((-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5)):
            s.v.append(tuple(c + M @ Vector((x * sx, y * sy, z)))); s.glow.append(0.0)
        s._face((b, b + 1, b + 2, b + 3), mat, pr)

    def cyl(s, p0, p1, r0, r1, seg=12, mat=0, pr=None, caps=True, g0=0.0, g1=0.0):
        if pr is None: pr = R.random()
        p0, p1 = Vector(p0), Vector(p1)
        d = (p1 - p0)
        if d.length < 1e-6: return
        d.normalize()
        u = d.cross(Vector((0, 0, 1)))
        if u.length < 0.1: u = d.cross(Vector((1, 0, 0)))
        u.normalize(); v = d.cross(u)
        b = len(s.v)
        for (p, r, g) in ((p0, r0, g0), (p1, r1, g1)):
            for i in range(seg):
                a = 2 * math.pi * i / seg
                s.v.append(tuple(p + (u * math.cos(a) + v * math.sin(a)) * r)); s.glow.append(g)
        for i in range(seg):
            j = (i + 1) % seg
            s._face((b + i, b + j, b + seg + j, b + seg + i), mat, pr)
        if caps:
            s._face(tuple(b + i for i in reversed(range(seg))), mat, pr)
            s._face(tuple(b + seg + i for i in range(seg)), mat, pr)

    def sphere(s, c, r, mat=0, pr=None, seg=10, rings=6):
        if pr is None: pr = R.random()
        c = Vector(c); b = len(s.v)
        s.v.append(tuple(c + Vector((0, 0, -r)))); s.glow.append(0.0)
        for k in range(1, rings):
            ph = -math.pi / 2 + math.pi * k / rings
            for i in range(seg):
                a = 2 * math.pi * i / seg
                s.v.append(tuple(c + Vector((math.cos(a) * math.cos(ph), math.sin(a) * math.cos(ph), math.sin(ph))) * r)); s.glow.append(0.0)
        top = len(s.v); s.v.append(tuple(c + Vector((0, 0, r)))); s.glow.append(0.0)
        for i in range(seg):
            j = (i + 1) % seg
            s._face((b, b + 1 + j, b + 1 + i), mat, pr)
        for k in range(rings - 2):
            o = b + 1 + k * seg
            for i in range(seg):
                j = (i + 1) % seg
                s._face((o + i, o + j, o + seg + j, o + seg + i), mat, pr)
        o = b + 1 + (rings - 2) * seg
        for i in range(seg):
            j = (i + 1) % seg
            s._face((o + i, o + j, top), mat, pr)

    def lathe(s, prof, axis_origin, seg=64, mat=0, pr=0.5, smooth_glow=None):
        # prof: list of (r, y_offset, glow); revolves around +Y axis through origin
        o = Vector(axis_origin); b = len(s.v); n = len(prof)
        for (r, yo, g) in prof:
            for i in range(seg):
                a = 2 * math.pi * i / seg
                s.v.append((o.x + r * math.cos(a), o.y + yo, o.z + r * math.sin(a))); s.glow.append(g)
        for k in range(n - 1):
            for i in range(seg):
                j = (i + 1) % seg
                a0, a1 = b + k * seg, b + (k + 1) * seg
                s._face((a0 + i, a1 + i, a1 + j, a0 + j), mat, pr)

    def to_object(s, name, mats, coll, smooth=False):
        me = bpy.data.meshes.new(name)
        me.from_pydata(s.v, [], s.f)
        me.polygons.foreach_set("material_index", s.mat)
        a = me.attributes.new("prand", 'FLOAT', 'FACE'); a.data.foreach_set("value", s.pr)
        g = me.attributes.new("glow_t", 'FLOAT', 'POINT'); g.data.foreach_set("value", s.glow)
        if smooth:
            me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        for m in mats: me.materials.append(m)
        ob = bpy.data.objects.new(name, me); coll.objects.link(ob)
        return ob

def frame(n, pref=Vector((0, 1, 0))):
    n = Vector(n).normalized()
    t = pref - n * pref.dot(n)
    if t.length < 0.2:
        t = Vector((1, 0, 0)) - n * n.x
    t.normalize(); b = n.cross(t)
    return Matrix((t, b, n)).transposed()  # columns t,b,n

# ---------------------------------------------------------------- materials
def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    return m, nt, out

def mk_hull():
    m, nt, out = node_mat("M_Hull")
    N, L = nt.nodes, nt.links
    bsdf = N.new("ShaderNodeBsdfPrincipled")
    attr = N.new("ShaderNodeAttribute"); attr.attribute_name = "prand"; attr.attribute_type = 'GEOMETRY'
    # value per plate
    vr = N.new("ShaderNodeMapRange"); vr.inputs[1].default_value = 0; vr.inputs[2].default_value = 1
    vr.inputs[3].default_value = 0.035; vr.inputs[4].default_value = 0.13
    L.new(attr.outputs["Fac"], vr.inputs[0])
    # gaps (prand==0) darker
    gap = N.new("ShaderNodeMath"); gap.operation = 'GREATER_THAN'; gap.inputs[1].default_value = 0.001
    L.new(attr.outputs["Fac"], gap.inputs[0])
    # big grime noise
    tc = N.new("ShaderNodeTexCoord")
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.012; nz.inputs["Detail"].default_value = 6
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    gr = N.new("ShaderNodeMapRange"); gr.inputs[1].default_value = 0.35; gr.inputs[2].default_value = 0.65
    gr.inputs[3].default_value = 0.55; gr.inputs[4].default_value = 1.25
    L.new(nz.outputs["Fac"], gr.inputs[0])
    mul = N.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'
    L.new(vr.outputs[0], mul.inputs[0]); L.new(gr.outputs[0], mul.inputs[1])
    mul2 = N.new("ShaderNodeMath"); mul2.operation = 'MULTIPLY'
    L.new(mul.outputs[0], mul2.inputs[0]); L.new(gap.outputs[0], mul2.inputs[1])
    gfloor = N.new("ShaderNodeMath"); gfloor.operation = 'MAXIMUM'; gfloor.inputs[1].default_value = 0.006
    L.new(mul2.outputs[0], gfloor.inputs[0])
    # tint: gunmetal, a few plates warmer/browner
    tint = N.new("ShaderNodeMix"); tint.data_type = 'RGBA'
    tint.inputs[6].default_value = (0.86, 0.92, 1.0, 1); tint.inputs[7].default_value = (1.0, 0.82, 0.62, 1)
    hi = N.new("ShaderNodeMath"); hi.operation = 'GREATER_THAN'; hi.inputs[1].default_value = 0.88
    L.new(attr.outputs["Fac"], hi.inputs[0]); L.new(hi.outputs[0], tint.inputs[0])
    col = N.new("ShaderNodeMix"); col.data_type = 'RGBA'; col.blend_type = 'MULTIPLY'; col.inputs[0].default_value = 1
    cval = N.new("ShaderNodeCombineColor")
    for i in range(3): L.new(gfloor.outputs[0], cval.inputs[i])
    L.new(cval.outputs[0], col.inputs[6]); L.new(tint.outputs[2], col.inputs[7])
    L.new(col.outputs[2], bsdf.inputs["Base Color"])
    # roughness per plate
    fr = N.new("ShaderNodeMath"); fr.operation = 'MULTIPLY'; fr.inputs[1].default_value = 7.31
    L.new(attr.outputs["Fac"], fr.inputs[0])
    fr2 = N.new("ShaderNodeMath"); fr2.operation = 'FRACT'; L.new(fr.outputs[0], fr2.inputs[0])
    rr = N.new("ShaderNodeMapRange"); rr.inputs[3].default_value = 0.28; rr.inputs[4].default_value = 0.72
    L.new(fr2.outputs[0], rr.inputs[0]); L.new(rr.outputs[0], bsdf.inputs["Roughness"])
    bsdf.inputs["Metallic"].default_value = 0.4
    # micro bump
    nz2 = N.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 1.6; nz2.inputs["Detail"].default_value = 4
    L.new(tc.outputs["Object"], nz2.inputs["Vector"])
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.08
    L.new(nz2.outputs["Fac"], bump.inputs["Height"]); L.new(bump.outputs[0], bsdf.inputs["Normal"])
    L.new(bsdf.outputs[0], out.inputs[0])
    return m

def mk_simple(name, base, rough, metal):
    m, nt, out = node_mat(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*base, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    nt.links.new(b.outputs[0], out.inputs[0]); return m

def mk_emit(name, c1, c2, strength, var=True):
    m, nt, out = node_mat(name)
    N, L = nt.nodes, nt.links
    e = N.new("ShaderNodeEmission")
    attr = N.new("ShaderNodeAttribute"); attr.attribute_name = "prand"; attr.attribute_type = 'GEOMETRY'
    mix = N.new("ShaderNodeMix"); mix.data_type = 'RGBA'
    mix.inputs[6].default_value = (*c1, 1); mix.inputs[7].default_value = (*c2, 1)
    L.new(attr.outputs["Fac"], mix.inputs[0]); L.new(mix.outputs[2], e.inputs["Color"])
    st = N.new("ShaderNodeMapRange"); st.inputs[3].default_value = strength * (0.35 if var else 1); st.inputs[4].default_value = strength * (1.3 if var else 1)
    L.new(attr.outputs["Fac"], st.inputs[0]); L.new(st.outputs[0], e.inputs["Strength"])
    m["base_strength"] = strength
    L.new(e.outputs[0], out.inputs[0]); return m

def mk_engine_inner():
    m, nt, out = node_mat("M_EngineInner")
    N, L = nt.nodes, nt.links
    attr = N.new("ShaderNodeAttribute"); attr.attribute_name = "glow_t"; attr.attribute_type = 'GEOMETRY'
    inv = N.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1
    L.new(attr.outputs["Fac"], inv.inputs[1])
    pw = N.new("ShaderNodeMath"); pw.operation = 'POWER'; pw.inputs[1].default_value = 2.2
    L.new(inv.outputs[0], pw.inputs[0])
    st = N.new("ShaderNodeMath"); st.operation = 'MULTIPLY_ADD'; st.inputs[1].default_value = 3; st.inputs[2].default_value = 0.12
    L.new(pw.outputs[0], st.inputs[0])
    st.name = "EngineStrength"
    cr = N.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (0.9, 0.96, 1.0, 1); cr.color_ramp.elements[1].color = (0.05, 0.25, 1.0, 1)
    L.new(attr.outputs["Fac"], cr.inputs[0])
    e = N.new("ShaderNodeEmission"); L.new(cr.outputs[0], e.inputs["Color"]); L.new(st.outputs[0], e.inputs["Strength"])
    L.new(e.outputs[0], out.inputs[0]); return m

def mk_plume():
    m, nt, out = node_mat("M_Plume")
    N, L = nt.nodes, nt.links
    attr = N.new("ShaderNodeAttribute"); attr.attribute_name = "glow_t"; attr.attribute_type = 'GEOMETRY'
    inv = N.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1
    L.new(attr.outputs["Fac"], inv.inputs[1])
    pw = N.new("ShaderNodeMath"); pw.operation = 'POWER'; pw.inputs[1].default_value = 2.5
    L.new(inv.outputs[0], pw.inputs[0])
    lw = N.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
    fac = N.new("ShaderNodeMath"); fac.operation = 'SUBTRACT'; fac.inputs[0].default_value = 1
    L.new(lw.outputs["Facing"], fac.inputs[1])
    f2 = N.new("ShaderNodeMath"); f2.operation = 'POWER'; f2.inputs[1].default_value = 1.5
    L.new(fac.outputs[0], f2.inputs[0])
    mm = N.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'
    L.new(pw.outputs[0], mm.inputs[0]); L.new(f2.outputs[0], mm.inputs[1])
    st = N.new("ShaderNodeMath"); st.operation = 'MULTIPLY'; st.inputs[1].default_value = 6.0; st.name = "PlumeStrength"
    L.new(mm.outputs[0], st.inputs[0])
    e = N.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (0.25, 0.5, 1.0, 1)
    L.new(st.outputs[0], e.inputs["Strength"])
    tr = N.new("ShaderNodeBsdfTransparent")
    add = N.new("ShaderNodeAddShader"); L.new(e.outputs[0], add.inputs[0]); L.new(tr.outputs[0], add.inputs[1])
    L.new(add.outputs[0], out.inputs[0])
    return m

M_HULL = mk_hull()
M_DARK = mk_simple("M_Dark", (0.012, 0.013, 0.015), 0.55, 0.6)
M_WIN = mk_emit("M_Window", (1.0, 0.62, 0.32), (1.0, 0.9, 0.75), 28)
M_TEAL = mk_emit("M_Teal", (0.02, 0.75, 0.7), (0.1, 0.95, 0.9), 22)
M_ENG = mk_engine_inner()
M_CORE = mk_emit("M_EngineCore", (0.75, 0.88, 1.0), (0.85, 0.93, 1.0), 220, var=False)
M_PLUME = mk_plume()
MATS = [M_HULL, M_DARK, M_WIN, M_TEAL, M_ENG, M_CORE, M_PLUME]
HULL, DARK, WIN, TEAL, ENG, CORE, PLUME = range(7)

# ---------------------------------------------------------------- scene reset
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
scn = bpy.context.scene
coll = bpy.data.collections.new("Ship"); scn.collection.children.link(coll)
root = bpy.data.objects.new("ShipRoot", None); coll.objects.link(root)

# ---------------------------------------------------------------- loft
def alloc_counts(sec, spacing):
    n = len(sec); out = []
    for i in range(n):
        a, b = Vector(sec[i]), Vector(sec[(i + 1) % n])
        out.append(max(1, round((b - a).length / spacing)))
    return out

def resample(sec, counts):
    pts = []; n = len(sec)
    for i in range(n):
        a, b = Vector(sec[i]), Vector(sec[(i + 1) % n])
        for k in range(counts[i]):
            pts.append(a.lerp(b, k / counts[i]))
    return pts

def loft(bm, ys, secfn, spacing, cap_inset=0):
    ref = secfn(ys[len(ys) // 2]); counts = alloc_counts(ref, spacing)
    rings = []
    for y in ys:
        rings.append([bm.verts.new((p.x, y, p.y)) for p in resample(secfn(y), counts)])
    side = []
    n = len(rings[0]); ni = len(rings) - 1
    starts = [sum(counts[:e]) for e in range(len(counts))]
    edge_of = {}
    for e, (st, c) in enumerate(zip(starts, counts)):
        for j in range(st, st + c): edge_of[j] = (st, st + c)
    used = set()
    for i in range(ni):
        for j in range(n):
            if (i, j) in used: continue
            a = R.choice((1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 6)); b = R.choice((1, 1, 1, 2, 2, 3))
            st, en = edge_of[j]
            a = min(a, ni - i); b = min(b, en - j)
            while b > 1 and any((ii, jj) in used for ii in range(i, i + a) for jj in range(j, j + b)): b -= 1
            while a > 1 and any((ii, jj) in used for ii in range(i, i + a) for jj in range(j, j + b)): a -= 1
            for ii in range(i, i + a):
                for jj in range(j, j + b): used.add((ii, jj))
            i1, j1 = i + a, j + b
            loop = [rings[i][jj % n] for jj in range(j, j1 + 1)]
            loop += [rings[ii][j1 % n] for ii in range(i + 1, i1 + 1)]
            loop += [rings[i1][jj % n] for jj in range(j1 - 1, j - 1, -1)]
            loop += [rings[ii][j % n] for ii in range(i1 - 1, i, -1)]
            side.append(bm.faces.new(loop))
    c0 = bm.faces.new(rings[0]); c1 = bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=side + [c0, c1])
    return side, [c0, c1]

def stations(a, b, step):
    n = max(2, int(round((b - a) / step)) + 1)
    return [a + (b - a) * i / (n - 1) for i in range(n)]

bm = bmesh.new()
PR = bm.faces.layers.float.new("prand")
GL = bm.verts.layers.float.new("glow_t")

ys = stations(L0, 340, 7.0) + stations(343.5, L1, 3.5)[0:]
hull_side, hull_caps = loft(bm, ys, hull_sec, 7.0)

# superstructure: stepped ridge blocks (y0, y1, base offset above hull top, height, bottom/top half-width fraction)
blocks = [
    (-392, -150, -1.5, 16, 0.66, 0.58), (-140, 60, -1.5, 13, 0.63, 0.56), (70, 262, -1.5, 9, 0.60, 0.54),
    (-378, -205, 14.0, 14, 0.42, 0.36), (-196, -45, 11.0, 11, 0.40, 0.34), (-36, 130, 7.0, 8, 0.36, 0.30),
    (-352, -238, 27.5, 16, 0.24, 0.19), (-230, -118, 21.5, 11, 0.22, 0.18),
    (-334, -296, 43.0, 22, 0.13, 0.10), (-322, -306, 64.0, 10, 0.07, 0.05),
    # side sponsons (armor belts) low on the flanks
]
block_side, block_caps = [], []
for (y0, y1, off, th, bwf, twf) in blocks:
    def sec(y, off=off, th=th, bwf=bwf, twf=twf):
        w = hw(y); zb = htop(y) + off
        bw, tw = bwf * w, twf * w
        return [(bw, zb), (bw, zb + 0.72 * th), (tw, zb + th), (-tw, zb + th), (-bw, zb + 0.72 * th), (-bw, zb)]
    s, c = loft(bm, stations(y0, y1, 6.0), sec, 6.0)
    block_side += s; block_caps += c

# side sponsons
for sgn in (1, -1):
    for (y0, y1) in ((-380, -120), (-100, 150), (170, 300)):
        def sec(y, sgn=sgn):
            w, zb, H = hw(y), zbot(y), htop(y); hh = H - zb
            z0 = zb + 0.26 * hh; z1 = zb + 0.52 * hh
            pts = [(w - 1, z0), (w + 5, z0 + 2), (w + 5.5, z1 - 2.5), (w - 1, z1)]
            if sgn < 0: pts = [(-x, z) for (x, z) in reversed(pts)]
            return pts
        s, c = loft(bm, stations(y0, y1, 6.0), sec, 6.0)
        block_side += s; block_caps += c

# engine housing
def eh_sec(y):
    return [(80, -6), (92, 6), (92, 62), (80, 74), (-80, 74), (-92, 62), (-92, 6), (-80, -6)]
eh_side, eh_caps = loft(bm, stations(-432, -398, 6.0), eh_sec, 7.0)

bm.faces.ensure_lookup_table()

# plates: inset every side face, random depth, extrude some
plate_faces = hull_side + block_side + eh_side
res = bmesh.ops.inset_individual(bm, faces=plate_faces, thickness=0.32, depth=0.0, use_even_offset=True)
for f in res["faces"]: f[PR] = 0.0
from mathutils import noise as mnoise
def band(c):  # large armor-section tone, ~40-90 BU blocks
    k = (int((c.y + 1000) // 46), int((c.z + 300) // 22), int((c.x + 500) // 38))
    return random.Random(hash(k)).random()
def dens(c):  # greeble density field: clean armor zones vs dense machinery zones
    v = mnoise.noise(Vector((c.x / 55.0, c.y / 70.0, c.z / 30.0)) + Vector((3.1, 7.7, 1.3)))
    return max(0.0, min(1.0, 0.5 + 0.9 * v))
def plate_val(c):
    return 0.08 + 0.92 * (0.55 * band(c) + 0.45 * R.random())
raise_faces = []
for f in plate_faces:
    f[PR] = plate_val(f.calc_center_median())
    d = R.choice((-0.25, -0.12, 0.0, 0.0, 0.1, 0.2))
    n = f.normal.copy()
    for v in f.verts: v.co += n * d
    if R.random() < 0.16: raise_faces.append(f)
ex = bmesh.ops.extrude_discrete_faces(bm, faces=raise_faces)
for f in ex["faces"]:
    h = R.uniform(0.25, 1.0); n = f.normal.copy()
    for v in f.verts: v.co += n * h
    f[PR] = plate_val(f.calc_center_median())
plate_faces = [f for f in plate_faces if f.is_valid] + ex["faces"]

# caps: armored insets
for cap in hull_caps[1:] + block_caps + eh_caps[1:]:
    cur = [cap]
    for k in range(3 if cap is hull_caps[1] else 1):
        r = bmesh.ops.inset_region(bm, faces=cur, thickness=2.4 if cap is hull_caps[1] else 0.8, depth=-1.2 if k % 2 == 0 else 0.8)
        for f in r["faces"]: f[PR] = 0.0
        for f in cur: f[PR] = R.random()
bm.normal_update()

# collect face info for greebles before writing mesh
finfo = []
for f in plate_faces:
    if not f.is_valid: continue
    n = f.normal.copy(); c = f.calc_center_median()
    M = frame(n)
    t, b = M.col[0], M.col[1]
    us = [(v.co - c).dot(t) for v in f.verts]; vs = [(v.co - c).dot(b) for v in f.verts]
    finfo.append((c, n, M, max(us) - min(us), max(vs) - min(vs)))
prow_c = hull_caps[1].calc_center_median(); prow_n = hull_caps[1].normal.copy()

me = bpy.data.meshes.new("Ship_Hull"); bm.to_mesh(me); bm.free()
for m in MATS: me.materials.append(m)
hull_ob = bpy.data.objects.new("Ship_Hull", me); coll.objects.link(hull_ob)
print("hull faces", len(me.polygons), "t=%.1f" % (time.time() - T0))

# ---------------------------------------------------------------- greebles
G = Acc()   # hull-colour greebles + dark
W = Acc()   # emissive windows + teal strips

def kit_small(c, M, su, sv, n=5):
    for _ in range(R.randint(1, n)):
        x = R.uniform(-.42, .42) * su; y = R.uniform(-.42, .42) * sv
        G.box(c + M @ Vector((x, y, 0)), M, R.uniform(.15, 1.0), R.uniform(.15, 1.3), R.uniform(.06, .55),
              mat=DARK if R.random() < .25 else HULL)

def kit_medium(c, M, su, sv):
    x = R.uniform(-.25, .25) * su; y = R.uniform(-.25, .25) * sv
    sx, sy, sz = R.uniform(1.2, max(1.3, .55 * su)), R.uniform(1.2, max(1.3, .55 * sv)), R.uniform(.3, 1.9)
    p = c + M @ Vector((x, y, 0))
    G.box(p, M, sx, sy, sz)
    # stacked detail on top
    if R.random() < .6:
        G.box(p + M @ Vector((R.uniform(-.2, .2) * sx, R.uniform(-.2, .2) * sy, sz)), M, sx * R.uniform(.3, .7), sy * R.uniform(.3, .7), R.uniform(.2, 1.5))
    if R.random() < .4:
        for k in range(R.randint(3, 8)):  # vent slats
            G.box(p + M @ Vector((-sx / 2 + (k + .5) * sx / 8, 0, sz)), M, .12, sy * .8, .3, mat=DARK)

def kit_pipes(c, M, su, sv):
    n = R.randint(2, 5); r = R.uniform(.18, .55); y0 = R.uniform(-.3, .3) * sv
    t = M.col[0]; nn = M.col[2]; b = M.col[1]
    for k in range(n):
        off = b * (y0 + k * r * 2.3) + nn * (r + .05)
        G.cyl(c - t * su * .5 + off, c + t * su * .5 + off, r, r, seg=8, mat=HULL if k % 2 else DARK, caps=False)

def kit_fins(c, M, su, sv, big=False):
    n = R.randint(6, 14); h = R.uniform(4, 9) if big else R.uniform(.8, 2.2)
    ln = R.uniform(.6, 1.0) * sv * (1.8 if big else 1)
    for k in range(n):
        G.box(c + M @ Vector((-su * .45 + k * su * .9 / n, 0, 0)), M, .14 if not big else .3, ln, h, mat=HULL)

def kit_mast(c, M):
    h = R.uniform(12, 38); r = R.uniform(.25, .55); nn = M.col[2]
    G.cyl(c, c + nn * h, r * 1.6, r * .5, seg=6)
    for k in range(R.randint(2, 5)):
        z = h * R.uniform(.35, .95); L = R.uniform(2, 6)
        G.cyl(c + nn * z - M.col[0] * L / 2, c + nn * z + M.col[0] * L / 2, .12, .12, seg=4, caps=False)
    W.quad(c + nn * h, M, .9, .9, .05, WIN, 1.0)
    W.quad(c + nn * h * .7, M, .6, .6, .05, TEAL, 1.0)

def kit_bay(c, M, su, sv):
    sx, sy = su * R.uniform(1.6, 2.6), sv * R.uniform(1.2, 2.2)
    G.box(c, M, sx, sy, .25, mat=DARK)            # dark floor
    for (x, y, a, b2) in ((0, sy / 2, sx, .8), (0, -sy / 2, sx, .8), (sx / 2, 0, .8, sy), (-sx / 2, 0, .8, sy)):
        G.box(c + M @ Vector((x, y, 0)), M, a, b2, 2.2)   # frame
    for k in range(R.randint(4, 9)):  # warm interior lights
        W.quad(c + M @ Vector((-sx * .4 + k * sx * .8 / 8, sy * .35, .3)), M, .5, .25, .02, WIN, R.random())
    W.box(c + M @ Vector((0, -sy / 2, 2.2)), M, sx * .9, .2, .1, mat=TEAL, pr=.5)

def kit_windows(c, M, su, sv, dens):
    rows = R.randint(1, 3); sp = R.uniform(.7, 1.2)
    for r in range(rows):
        y = (r - (rows - 1) / 2) * R.uniform(1.0, 1.8)
        if abs(y) > sv * .45: continue
        n = int(su * .9 / sp)
        for k in range(n):
            if R.random() > dens: continue
            x = -su * .45 + (k + .5) * sp
            W.quad(c + M @ Vector((x, y, 0)), M, sp * .5, .28, .06, WIN, R.random())

up_faces = []
for (c, n, M, su, sv) in finfo:
    side = abs(n.z) < 0.55; top = n.z >= 0.55; bot = n.z <= -0.55
    r = R.random(); D = dens(c)
    if top and r < 0.012: kit_fins(c, M, su, sv, big=True); continue
    if top and r < 0.02: up_faces.append((c, M)); continue
    if (bot or side) and r < 0.012: kit_bay(c, M, su, sv); continue
    nt_, nb_ = max(1, round(su / 7.5)), max(1, round(sv / 7.5))
    cu, cv = su / nt_, sv / nb_
    for iu in range(nt_):
        for iv in range(nb_):
            cc = c + M @ Vector((-su / 2 + (iu + .5) * cu, -sv / 2 + (iv + .5) * cv, 0))
            D = dens(cc)
            if R.random() < 0.1 + 0.85 * D: kit_small(cc, M, cu, cv, 2 + int(8 * D))
            if R.random() < 0.35 * D * D: kit_medium(cc, M, cu, cv)
            if R.random() < 0.2 * D: kit_pipes(cc, M, cu, cv)
            if R.random() < 0.06 * D: kit_fins(cc, M, cu, cv)
    wp = 0.42 if side else (0.16 if bot else 0.10)
    if R.random() < wp: kit_windows(c, M, su, sv, R.uniform(.3, .85))
    if R.random() < 0.012:  # lone bright beacon
        W.quad(c + n * 0.08, M, 1.0, 1.0, .1, WIN, 1.0)
for (c, M) in up_faces[: 140]:
    kit_mast(c, M)

# flank pipe bundles (continuous, follow hull)
for sgn in (1, -1):
    yy = stations(-395, 330, 7.0)
    for zf, rr in ((0.57, 1.3), (0.6, 0.8), (0.63, 1.0), (0.19, 0.9)):
        for a, b in zip(yy, yy[1:]):
            if R.random() < 0.08: continue
            def P(y):
                w, zb, H = hw(y), zbot(y), htop(y)
                return Vector((sgn * (w + rr + 0.4), y, zb + zf * (H - zb)))
            G.cyl(P(a), P(b), rr, rr, seg=10, mat=DARK if zf > 0.6 else HULL, caps=False)
        for y in yy[::3]:  # clamps
            w, zb, H = hw(y), zbot(y), htop(y)
            G.box(Vector((sgn * (w + 1.0), y, zb + zf * (H - zb))), frame(Vector((sgn, 0, 0))), 4.5, 1.2, 3.0)

# teal running lights along hull corners + keel
def corner_pts(y):
    w, zb, H = hw(y), zbot(y), htop(y); hh = H - zb
    return {"bot": (0.82 * w + .3, zb - .3), "upper": (w + .4, zb + 0.62 * hh + .2), "top": (0.78 * w + .3, H + .3)}
yy = stations(-396, 398, 3.5)
for key in ("bot", "top"):
    for sgn in (1, -1):
        for i, (a, b) in enumerate(zip(yy, yy[1:])):
            if (i % 9) in (6, 7, 8): continue
            pa, pb = corner_pts(a)[key], corner_pts(b)[key]
            W.cyl((sgn * pa[0], a, pa[1]), (sgn * pb[0], b, pb[1]), .22, .22, seg=6, mat=TEAL, pr=.6)
for x in (-12, 12):  # keel strips on belly
    for i, (a, b) in enumerate(zip(yy, yy[1:])):
        if (i % 6) in (4, 5): continue
        W.cyl((x, a, zbot(a) - .5), (x, b, zbot(b) - .5), .28, .28, seg=6, mat=TEAL, pr=.5)
# belly warm landing-light rows
for y in stations(-380, 370, 9):
    for x in (-60, -30, 30, 60):
        if R.random() < .5:
            W.quad(Vector((x, y, zbot(y) - .55)), frame(Vector((0, 0, -1))), .9, .9, 0, WIN, 1.0)

# prow armor: big layered plates on the blunt face
Mp = frame(prow_n, Vector((1, 0, 0)))
for k, v in enumerate((-8.5, -5.5, -2.5, 0.5, 3.5, 6.5)):     # layered armored ram
    wdt = 68 * (1 - 0.05 * abs(v)); dep = 5.5 - 0.45 * abs(v)
    for seg in (-1, 0, 1):
        G.box(prow_c + Mp @ Vector((seg * wdt / 3, v, 0)), Mp, wdt / 3 - .5, 2.7, dep, pr=R.random())
    G.box(prow_c + Mp @ Vector((0, v, dep)), Mp, 9, 2.4, 1.5, mat=DARK)
G.box(prow_c + Mp @ Vector((0, -2.5, 0)), Mp, 40, 5, 7.0)             # central ram slab
for k in range(30):
    p = prow_c + Mp @ Vector((R.uniform(-30, 30), R.uniform(-9, 9), 3))
    G.box(p, Mp, R.uniform(1, 5), R.uniform(.6, 2), R.uniform(.3, 1.6), mat=DARK if R.random() < .4 else HULL)
for sgn in (1, -1):
    for v in (-7, 7):
        W.quad(prow_c + Mp @ Vector((sgn * 30, v, 4.6)), Mp, 2.2, .5, 0.02, TEAL, .5)
for k, v in enumerate((-8.5, -5.5, -2.5, 0.5, 3.5, 6.5)):     # window rows across the armor
    dep = 5.5 - 0.45 * abs(v)
    for x in range(-32, 33):
        if R.random() < 0.45 and abs(x) > 5:
            W.quad(prow_c + Mp @ Vector((x * 1.0, v + R.choice((-0.6, 0.6)), dep + .03)), Mp, .45, .3, 0, WIN, R.random())
for sgn in (1, -1):
    W.quad(prow_c + Mp @ Vector((sgn * 22, 6, 3.2)), Mp, 3, 1.2, 0, WIN, 1.0)

# ---------------------------------------------------------------- engines
E = Acc()
eng_centers = []
for z in (14.0, 54.0):
    for x in (-58.0, 0.0, 58.0):
        o = Vector((x, -432.0, z)); eng_centers.append(o)
        outer = [(16.5, 2, 0), (19.0, 0, 0), (20.5, -5, 0), (21.2, -24, 0), (22.4, -28, 0), (22.4, -31, 0), (19.6, -31.5, 0)]
        G.lathe(outer, o, seg=64, mat=HULL, pr=0.35)
        inner = [(19.6, -31.5, 1.0), (17.2, -22, 0.75), (14.2, -12, 0.45), (11.2, -3, 0.15), (9.5, 2, 0.0)]
        E.lathe(inner, o, seg=64, mat=ENG, pr=0.5)
        # ribs
        for yo in (-8, -14, -20):
            G.lathe([(21.4, yo + .8, 0), (22.0, yo + .4, 0), (22.0, yo - .4, 0), (21.4, yo - .8, 0)], o, seg=64, mat=DARK, pr=.2)
        # actuators around the bell
        for k in range(8):
            a = 2 * math.pi * k / 8
            d = Vector((math.cos(a), 0, math.sin(a)))
            G.cyl(o + d * 23.5 + Vector((0, 4, 0)), o + d * 22.4 + Vector((0, -18, 0)), .7, .5, seg=8, mat=DARK)
        # throat core disc + spike
        E.cyl(o + Vector((0, 2.5, 0)), o + Vector((0, 1.5, 0)), 9.6, 9.6, seg=48, mat=CORE, pr=1)

Mr = frame(Vector((0, -1, 0)), Vector((1, 0, 0)))
for k in range(700):   # rear face machinery between the nozzles
    x, z = R.uniform(-90, 90), R.uniform(-5, 73)
    if min((Vector((x, z)) - Vector((c.x, c.z))).length for c in eng_centers) < 23.5: continue
    G.box(Vector((x, -432.3, z)), Mr, R.uniform(.8, 7), R.uniform(.8, 5), R.uniform(.3, 3.5), mat=DARK if R.random() < .35 else HULL)
    if R.random() < .06: W.quad(Vector((x, -432.4, z)), Mr, .6, .6, 0.02, WIN, R.random())
for z in (-5.5, 73.5):
    for i in range(-11, 12):
        W.quad(Vector((i * 7.8, -432.5, z)), Mr, 3.5, .5, 0.02, TEAL, .5) if i % 3 else None
eng_ob = E.to_object("Ship_EngineGlow", MATS, coll, smooth=True)
# plumes (separate so shots can scale/hide them)
P = Acc()
for o in eng_centers:
    P.lathe([(18.5, -31, 0.0), (19.8, -55, 0.35), (16.0, -110, 0.75), (6.0, -170, 1.0)], o, seg=48, mat=PLUME, pr=.5)
    P.lathe([(9.0, -20, 0.0), (8.0, -45, 0.45), (2.0, -95, 1.0)], o, seg=32, mat=PLUME, pr=.5)
plume_ob = P.to_object("Ship_Plumes", MATS, coll, smooth=True)
plume_ob.visible_shadow = False
for i, o in enumerate(eng_centers):
    ld = bpy.data.lights.new(f"EngineLight_{i}", 'POINT'); ld.energy = 2.5e6; ld.color = (0.55, 0.75, 1.0)
    ld.shadow_soft_size = 14
    lo = bpy.data.objects.new(f"EngineLight_{i}", ld); lo.location = o + Vector((0, -110, 0)); coll.objects.link(lo)
    lo.parent = root

# ---------------------------------------------------------------- landing claws
LEG_SITES = [(-62, -262), (-62, -30), (-62, 205), (62, -262), (62, -30), (62, 205)]
legs = []
for li, (lx, ly) in enumerate(LEG_SITES):
    s = 1 if lx > 0 else -1
    A = Acc()
    def V(x, y, z): return Vector((s * x, y, z))
    Mz = frame(Vector((0, 0, -1)))
    A.box(V(0, 0, 1.5), Mz, 26, 22, 4, mat=DARK, pr=.1)          # bay frame (inside belly)
    A.box(V(0, 0, 0), Mz, 18, 16, 6, mat=HULL)                    # hip housing
    hip, knee, ank = V(2, 0, -8), V(16, 0, -38), V(20, 0, -70)
    A.cyl(hip + Vector((0, -7, 0)), hip + Vector((0, 7, 0)), 5.2, 5.2, seg=20, mat=HULL)
    A.cyl(hip, knee, 5.0, 4.2, seg=16, mat=HULL)                  # upper strut
    for k in range(4):                                            # armor collars
        p = hip.lerp(knee, .2 + .18 * k); q = hip.lerp(knee, .26 + .18 * k)
        A.cyl(p, q, 5.6, 5.6, seg=16, mat=DARK)
    for dy in (-6.5, 6.5):                                        # hydraulic rams
        a0, a1 = V(-3, dy, -4), V(13, dy, -31)
        A.cyl(a0, a0.lerp(a1, .6), 2.0, 2.0, seg=12, mat=DARK)
        A.cyl(a0.lerp(a1, .55), a1, 1.1, 1.1, seg=12, mat=HULL, pr=.95)
        A.sphere(a1, 1.8, mat=DARK)
    A.cyl(knee + Vector((0, -7.5, 0)), knee + Vector((0, 7.5, 0)), 6.0, 6.0, seg=20, mat=HULL)
    A.cyl(knee, knee.lerp(ank, .55), 4.6, 4.6, seg=16, mat=HULL)  # lower sleeve
    A.cyl(knee.lerp(ank, .5), ank, 3.2, 3.2, seg=16, mat=HULL, pr=.92)  # telescoping rod
    for dy in (-5, 5):
        b0, b1 = V(13, dy, -30), V(19, dy, -60)
        A.cyl(b0, b0.lerp(b1, .55), 1.5, 1.5, seg=10, mat=DARK)
        A.cyl(b0.lerp(b1, .5), b1, .8, .8, seg=10, mat=HULL, pr=.95)
    A.cyl(ank + Vector((0, 0, 2)), ank + Vector((0, 0, -4)), 7.0, 7.5, seg=24, mat=HULL)  # foot hub
    A.cyl(ank + Vector((0, 0, -4)), ank + Vector((0, 0, -5.5)), 7.5, 5.0, seg=24, mat=DARK)
    for k in range(3):                                            # 3 talons
        a = math.radians(120 * k + (0 if s > 0 else 180))
        d = Vector((math.cos(a), math.sin(a), 0))
        pts = [ank + d * 5 + Vector((0, 0, -2)), ank + d * 10 + Vector((0, 0, -3.2)), ank + d * 15 + Vector((0, 0, -6.0)),
               ank + d * 18.5 + Vector((0, 0, -9.6)), ank + d * 19.6 + Vector((0, 0, -11.2))]
        rad = [3.0, 2.6, 1.9, 1.0, 0.15]
        for i in range(4):
            A.cyl(pts[i], pts[i + 1], rad[i], rad[i + 1], seg=12, mat=HULL if i < 2 else DARK, pr=.4)
            A.sphere(pts[i], rad[i] * 1.02, mat=HULL, pr=.4)
        A.cyl(ank + d * 6 + Vector((0, 0, 1)), pts[2], 1.0, .8, seg=8, mat=DARK)   # talon ram
    # lights on leg
    A.cyl(hip.lerp(knee, .1) + Vector((0, 0, 0)), hip.lerp(knee, .14), 5.25, 5.25, seg=16, mat=TEAL, pr=.5)
    A.box(knee + V(4, 0, 0), frame(Vector((s, 0, 0))), 1.2, 1.2, .4, mat=WIN, pr=1)
    A.box(ank + V(7.2, 0, 1), frame(Vector((s, 0, 0))), 1.0, 1.0, .3, mat=WIN, pr=1)
    lo = A.to_object(f"Leg_{li}", MATS, coll)
    # re-origin at hip: geometry built in world-ish coords around (0,0); place
    lo.location = Vector((lx, ly, zbot(ly)))
    lo.scale = (1.6, 1.6, 1.15)
    lo["side"] = s
    legs.append(lo)

g_ob = G.to_object("Ship_Greebles", MATS, coll)
w_ob = W.to_object("Ship_Lights", MATS, coll)
for ob in coll.objects:
    if ob is not root and ob.parent is None: ob.parent = root

scn["leg_ground_z"] = -81.2 * 1.15  # claw tips below belly when deployed
print("greeble faces", len(g_ob.data.polygons), "light faces", len(w_ob.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "ship.blend"), compress=True)
print("saved ship.blend t=%.1f" % (time.time() - T0))
