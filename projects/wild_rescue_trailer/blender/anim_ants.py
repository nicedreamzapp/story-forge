"""Animated metal-plated ant swarm for WILD RESCUE (2026-11-01 evening rebuild).
The 10/31 ant read as a BEETLE (a big plate over a fat body). This one is built to read as an ANT at a glance:
three distinct body segments (head, long narrow thorax, gaster) joined by a pinched waist (a thin petiole node),
thin elbowed antennae, six thin three-part legs, and a SMALL shiny metal plate riveted on the gaster only.
Two leg poses (alternating tripods) are swapped per ant by a gait clock, so walking ants step.

Motion lives in a geometry-nodes tree driven by the scene frame (so Cycles motion blur sees it):
  pos(t) = base + dir * clamp(t - t0, 0, t1 - t0)   (+ lift that decays to 0 at t1, - sink that rises out by t0+0.3)
  walkers ray-cast down onto the ground every frame so they stay on the sand / ties; an ant whose ground drops away
  (the canyon lip) is removed rather than floating.  Visible when t >= tv.
Usage: blender -b train.blend -P anim_ants.py -- ground|river|bridge [--test]"""
import sys, os, math, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
from common import setup_render, look_at, RENDERS, flat_mat, ramp_mat, ellipsoid, sphere, cyl_between, join
from track import MACRO, h_train

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
TEST = "--test" in argv
shot = [a for a in argv if not a.startswith("--")][0]
sc = bpy.context.scene; cam = sc.camera
FPS = 24; HANDLE = 6
def nfr(sec): return int(round(sec * FPS)) + 2 * HANDLE

# ------------------------------------------------------------------ the ant (x forward, z up, ~0.3 m long at scale 1)
BODY = flat_mat("antv2_body", (0.42, 0.06, 0.025), rough=0.28, coat=0.8)
LEG = flat_mat("antv2_leg", (0.24, 0.04, 0.02), rough=0.35, coat=0.5)
PLATE = ramp_mat("antv2_plate", 'noise', ((0.0, (0.86, 0.88, 0.92)), (1.0, (0.99, 0.99, 1.0))), rough=0.13, metal=1.0,
                 bump=0.3, bump_dist=0.002, scale=14, detail=2)
WHITE = flat_mat("antv2_eye", (0.97, 0.97, 0.95), rough=0.15, coat=1.0)
PUPIL = flat_mat("antv2_pupil", (0.01, 0.01, 0.01), rough=0.1, coat=1.0)

def build_ant(name, phase):
    p = []
    zc = 0.075
    # head (rounded, slightly heart-shaped from above) + mandibles
    p.append(ellipsoid("h", (0.042, 0.04, 0.036), (0.125, 0, zc + 0.018), (0, 0.15, 0), BODY, 20))
    for s in (-1, 1):
        p.append(cyl_between("md", (0.155, s * 0.016, zc - 0.002), (0.178, s * 0.004, zc - 0.012), 0.006, 0.003, BODY, 6))
        ec = Vector((0.142, s * 0.03, zc + 0.032))
        p.append(sphere("e", 0.016, ec, WHITE, 12))
        p.append(sphere("ep", 0.008, ec + Vector((0.01, s * 0.007, 0.002)), PUPIL, 8))
    # neck + long narrow thorax (mesosoma), humped
    p.append(cyl_between("nk", (0.1, 0, zc + 0.012), (0.075, 0, zc + 0.006), 0.011, 0.012, BODY, 8))
    p.append(ellipsoid("th", (0.048, 0.021, 0.023), (0.04, 0, zc + 0.004), (0, 0.12, 0), BODY, 16))
    p.append(ellipsoid("th2", (0.022, 0.02, 0.018), (0.002, 0, zc + 0.012), (0, -0.3, 0), BODY, 12))
    # pinched waist: thin stalk + petiole node + thin stalk
    p.append(cyl_between("w1", (-0.012, 0, zc + 0.006), (-0.03, 0, zc + 0.01), 0.0055, 0.005, BODY, 8))
    p.append(ellipsoid("pt", (0.009, 0.009, 0.014), (-0.034, 0, zc + 0.016), (0, 0.2, 0), BODY, 10))
    p.append(cyl_between("w2", (-0.038, 0, zc + 0.012), (-0.05, 0, zc + 0.014), 0.005, 0.006, BODY, 8))
    # gaster (big rounded abdomen), tipped up a little
    p.append(ellipsoid("ga", (0.066, 0.046, 0.043), (-0.112, 0, zc + 0.022), (0, -0.25, 0), BODY, 22))
    # small shiny metal plate on the gaster only, with four rivets
    p.append(ellipsoid("pl", (0.05, 0.036, 0.008), (-0.108, 0, zc + 0.062), (0, -0.18, 0), PLATE, 24))
    for (rx, ry) in ((-0.08, 0.019), (-0.08, -0.019), (-0.135, 0.017), (-0.135, -0.017)):
        p.append(sphere("rv", 0.0045, (rx, ry, zc + 0.069 - (rx + 0.108) * 0.18), PLATE, 6))
    # thin elbowed antennae: scape up-and-out, funiculus forward-and-down, tiny club
    for s in (-1, 1):
        a0 = Vector((0.15, s * 0.014, zc + 0.04))
        a1 = a0 + Vector((-0.004, s * 0.028, 0.055))
        a2 = a1 + Vector((0.07, s * 0.022, -0.012))
        p.append(cyl_between("an1", a0, a1, 0.0032, 0.003, LEG, 6))
        p.append(sphere("anj", 0.0036, a1, LEG, 6))
        p.append(cyl_between("an2", a1, a2, 0.003, 0.0026, LEG, 6))
        p.append(ellipsoid("anc", (0.009, 0.0045, 0.0045), a2 + Vector((0.006, 0, -0.001)), (0, 0.2, 0), LEG, 8))
    # six thin legs (coxa -> femur up to a high knee -> tibia down to the foot); alternating tripods swing
    hips = ((0.066, 0.1), (0.04, 0.0), (0.016, -0.1))     # (hip x, foot x offset)
    for i, (hx, fo) in enumerate(hips):
        for s in (-1, 1):
            tri = (i % 2 == 0) == (s > 0)          # tripod A = front-right, mid-left, hind-right
            sw = (0.035 if tri else -0.035) * (1 if phase == 0 else -1)
            hip = Vector((hx, s * 0.016, zc - 0.008))
            knee = Vector((hx + fo * 0.5 + sw * 0.5, s * 0.075, zc + 0.045))
            foot = Vector((hx + fo + sw, s * 0.115, 0.002 + (0.012 if sw > 0 else 0.0)))
            p.append(cyl_between("l1", hip, knee, 0.0042, 0.0036, LEG, 6))
            p.append(sphere("lk", 0.004, knee, LEG, 6))
            p.append(cyl_between("l2", knee, foot, 0.0036, 0.0022, LEG, 6))
    ob = join(name, p, (0, 0, 0))
    ob.location = (0, 0, -1000)
    return ob

ANT_A = build_ant("antv2_A", 0); ANT_B = build_ant("antv2_B", 1)
src_coll = bpy.data.collections.get("ant_src") or bpy.data.collections.new("ant_src")
for o in (ANT_A, ANT_B):
    for c in o.users_collection: c.objects.unlink(o)
    src_coll.objects.link(o)

# ------------------------------------------------------------------ instancer with the motion tree
def instancer(name, P, coll, ground_objs):
    """P: dict of per-point lists: base(vec), rot(euler), scl, dir(vec), t0, t1, tv, lift, sink, gait, phase, ray"""
    me = bpy.data.meshes.new(name)
    me.from_pydata(P["base"], [], [])
    def attr(nm, typ, vals):
        a = me.attributes.new(nm, typ, 'POINT')
        if typ == 'FLOAT_VECTOR': a.data.foreach_set('vector', [c for v in vals for c in v])
        else: a.data.foreach_set('value', vals)
    attr("rot", 'FLOAT_VECTOR', P["rot"]); attr("dir", 'FLOAT_VECTOR', P["dir"])
    for k in ("scl", "t0", "t1", "tv", "lift", "sink", "gait", "phase", "ray"):
        attr(k, 'FLOAT', P[k])
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob)
    ng = bpy.data.node_groups.new(name + "_gn", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N, L = ng.nodes, ng.links
    gi = N.new('NodeGroupInput'); go = N.new('NodeGroupOutput')
    def A(nm, typ='FLOAT'):
        n_ = N.new('GeometryNodeInputNamedAttribute'); n_.data_type = typ; n_.inputs['Name'].default_value = nm
        return n_.outputs['Attribute']
    def M(op, a, b=None, c=None):
        n_ = N.new('ShaderNodeMath'); n_.operation = op
        for i_, v in enumerate((a, b, c)):
            if v is None: continue
            if isinstance(v, (int, float)): n_.inputs[i_].default_value = v
            else: L.new(v, n_.inputs[i_])
        return n_.outputs[0]
    def V(op, a, b=None, scale=None):
        n_ = N.new('ShaderNodeVectorMath'); n_.operation = op
        L.new(a, n_.inputs[0])
        if b is not None:
            if isinstance(b, (tuple, list)): n_.inputs[1].default_value = b
            else: L.new(b, n_.inputs[1])
        if scale is not None:
            if isinstance(scale, (int, float)): n_.inputs['Scale'].default_value = scale
            else: L.new(scale, n_.inputs['Scale'])
        return n_.outputs['Vector'] if op != 'LENGTH' else n_.outputs['Value']
    def XYZ(x, y, z):
        n_ = N.new('ShaderNodeCombineXYZ')
        for i_, v in enumerate((x, y, z)):
            if isinstance(v, (int, float)): n_.inputs[i_].default_value = v
            else: L.new(v, n_.inputs[i_])
        return n_.outputs[0]
    st = N.new('GeometryNodeInputSceneTime')
    t = M('DIVIDE', M('SUBTRACT', st.outputs['Frame'], 1.0), float(FPS))
    t0, t1, tv = A("t0"), A("t1"), A("tv")
    tau = M('MINIMUM', M('MAXIMUM', M('SUBTRACT', t, t0), 0.0), M('SUBTRACT', t1, t0))
    pos0 = N.new('GeometryNodeInputPosition').outputs[0]
    p = V('ADD', pos0, V('SCALE', A("dir", 'FLOAT_VECTOR'), scale=tau))
    # lift decays to 0 at t1; sink rises out of the sand between t0 and t0 + 0.3 s
    span = M('MAXIMUM', M('SUBTRACT', t1, t0), 1e-3)
    prog = M('MINIMUM', M('DIVIDE', tau, span), 1.0)
    rise = M('MINIMUM', M('MAXIMUM', M('DIVIDE', M('SUBTRACT', t, t0), 0.3), 0.0), 1.0)
    rise = M('MULTIPLY', M('MULTIPLY', rise, rise), M('SUBTRACT', 3.0, M('MULTIPLY', rise, 2.0)))   # smoothstep
    dz = M('SUBTRACT', M('MULTIPLY', A("lift"), M('SUBTRACT', 1.0, prog)), M('MULTIPLY', A("sink"), M('SUBTRACT', 1.0, rise)))
    # ray-cast onto the ground for walkers
    gjoin = N.new('GeometryNodeJoinGeometry')
    for g in ground_objs:
        oi = N.new('GeometryNodeObjectInfo'); oi.transform_space = 'RELATIVE'; oi.inputs['Object'].default_value = g
        L.new(oi.outputs['Geometry'], gjoin.inputs[0])
    rc = N.new('GeometryNodeRaycast')
    L.new(gjoin.outputs[0], rc.inputs['Target Geometry'])
    L.new(V('ADD', p, (0, 0, 1.5)), rc.inputs['Source Position'])
    rc.inputs['Ray Direction'].default_value = (0, 0, -1); rc.inputs['Ray Length'].default_value = 6.0
    sp_ = N.new('ShaderNodeSeparateXYZ'); L.new(p, sp_.inputs[0])
    sh = N.new('ShaderNodeSeparateXYZ'); L.new(rc.outputs['Hit Position'], sh.inputs[0])
    ray = A("ray")
    zr = M('ADD', M('MULTIPLY', ray, sh.outputs['Z']), M('MULTIPLY', M('SUBTRACT', 1.0, ray), sp_.outputs['Z']))
    pnew = XYZ(sp_.outputs['X'], sp_.outputs['Y'], M('ADD', zr, dz))
    setp = N.new('GeometryNodeSetPosition')
    L.new(gi.outputs[0], setp.inputs['Geometry']); L.new(pnew, setp.inputs['Position'])
    # delete: not yet visible, or a walker whose ground fell away (canyon lip) / missed
    drop = M('SUBTRACT', sp_.outputs['Z'], sh.outputs['Z'])
    gone = M('MULTIPLY', ray, M('MAXIMUM', M('GREATER_THAN', drop, 0.6), M('SUBTRACT', 1.0, rc.outputs['Is Hit'])))
    hidden = M('MAXIMUM', M('LESS_THAN', t, tv), gone)
    dl = N.new('GeometryNodeDeleteGeometry'); dl.domain = 'POINT'
    L.new(setp.outputs[0], dl.inputs['Geometry']); L.new(M('GREATER_THAN', hidden, 0.5), dl.inputs['Selection'])
    m2p = N.new('GeometryNodeMeshToPoints'); L.new(dl.outputs[0], m2p.inputs['Mesh'])
    iop = N.new('GeometryNodeInstanceOnPoints'); L.new(m2p.outputs['Points'], iop.inputs['Points'])
    pj = N.new('GeometryNodeJoinGeometry')
    for src in (ANT_B, ANT_A):
        oi = N.new('GeometryNodeObjectInfo'); oi.inputs['Object'].default_value = src; oi.inputs['As Instance'].default_value = True
        L.new(oi.outputs['Geometry'], pj.inputs[0])
    L.new(pj.outputs[0], iop.inputs['Instance'])
    iop.inputs['Pick Instance'].default_value = True
    gidx = M('MODULO', M('FLOOR', M('ADD', M('MULTIPLY', M('MULTIPLY', t, A("gait")), 2.0), A("phase"))), 2.0)
    L.new(gidx, iop.inputs['Instance Index'])
    e2r = N.new('FunctionNodeEulerToRotation'); L.new(A("rot", 'FLOAT_VECTOR'), e2r.inputs['Euler'])
    L.new(e2r.outputs['Rotation'], iop.inputs['Rotation'])
    L.new(A("scl"), iop.inputs['Scale'])
    L.new(iop.outputs['Instances'], go.inputs[0])
    mod = ob.modifiers.new("ants", 'NODES'); mod.node_group = ng
    print("INSTANCER", name, len(P["base"]), flush=True)
    return ob

def newP():
    return {k: [] for k in ("base", "rot", "scl", "dir", "t0", "t1", "tv", "lift", "sink", "gait", "phase", "ray")}
def add(P, base, rot, scl, dir=(0, 0, 0), t0=0.0, t1=99.0, tv=-99.0, lift=0.0, sink=0.0, gait=0.0, phase=0.0, ray=0.0):
    for k, v in (("base", tuple(base)), ("rot", tuple(rot)), ("scl", scl), ("dir", tuple(dir)), ("t0", t0), ("t1", t1), ("tv", tv),
                 ("lift", lift), ("sink", sink), ("gait", gait), ("phase", phase), ("ray", ray)):
        P[k].append(v)

def hide_colls(names):
    for c in bpy.data.collections:
        if c.name in names: c.hide_render = True; c.hide_viewport = True

def mesh_points(obname):
    me = bpy.data.objects[obname].data
    n_ = len(me.vertices)
    co = [0.0] * (3 * n_); me.vertices.foreach_get('co', co)
    rot = [0.0] * (3 * n_); me.attributes['rot'].data.foreach_get('vector', rot)
    scl = [0.0] * n_; me.attributes['scl'].data.foreach_get('value', scl)
    return [(Vector(co[3 * i:3 * i + 3]), tuple(rot[3 * i:3 * i + 3]), scl[i]) for i in range(n_)]

rnd = random.Random(11)
mx, my = MACRO
SHOTS = {
    "ground": dict(cut="c06a_ground", sec=1.2, samples=48),
    "river": dict(cut="c06b_river", sec=1.6, samples=40),
    "bridge": dict(cut="c07a_bridge", sec=1.2, samples=40),
}
S = SHOTS[shot]; n = nfr(S["sec"]); T_END = (n - 1) / FPS
P = newP()
if shot == "ground":
    # B21: macro on the sand; the desert floor starts to move as ants push up out of it and march off toward the canyon
    hide_colls(("ants_river", "ants_bridge", "train"))
    bpy.data.objects["ant_macro"].hide_render = True
    coll = bpy.data.collections["ants_macro"]
    ground = [bpy.data.objects["macro_sand"]]
    for _ in range(2600):
        lx = rnd.uniform(-0.35, 2.7); ly = rnd.uniform(-1.25, 1.35)
        # keep the frame readable: thinner in the extreme foreground
        if lx < 0.0 and rnd.random() < 0.5: continue
        te = (rnd.random() ** 0.8) * (T_END + 0.4) - 0.45          # some already out at frame 1, more every frame
        yaw = rnd.gauss(0.0, 0.45)
        spd = rnd.uniform(0.1, 0.19)
        s_ = rnd.uniform(0.15, 0.2)
        add(P, (mx + lx, my + ly, 0.0), (0, 0, yaw), s_, (math.cos(yaw) * spd, math.sin(yaw) * spd, 0), t0=te + 0.2, t1=99.0,
            tv=te - 0.02, sink=0.045, gait=rnd.uniform(5.0, 7.0), phase=rnd.random() * 2, ray=1.0)
    cam_loc = (mx - 0.95, my + 0.05, 0.3 + h_train(mx - 0.95, my) + 0.03); tgt = (mx + 0.35, my + 0.1, h_train(mx, my) + 0.02)
    lens, fstop, focus = 40, 2.8, 1.05
elif shot == "river":
    # B22: a river of ants pouring across the desert toward the canyon; each ant walks along its own heading
    hide_colls(("ants_macro", "train"))
    bpy.data.objects["ant_river"].hide_render = True; bpy.data.objects["ant_bridge"].hide_render = True
    coll = bpy.data.collections["ants_river"]
    ground = [bpy.data.objects[nm] for nm in ("terrain", "ties", "ballast_near")]
    for (c, rot, s_) in mesh_points("ant_river"):
        yaw = rot[2]; spd = rnd.uniform(1.6, 2.4)
        add(P, c, rot, s_, (math.cos(yaw) * spd, math.sin(yaw) * spd, 0), t0=-0.5, t1=99.0, gait=rnd.uniform(6.5, 8.5),
            phase=rnd.random() * 2, ray=1.0)
    cam_loc, tgt, lens, fstop, focus = (-41.0, -15.0, 5.0), (-4.0, -1.2, -1.0), 26, None, None
else:
    # B24: the bridge links up live: two fronts grow out from the rims and meet mid-gap near the end of the cut;
    # each arriving ant crawls along the top of the built span into its slot
    hide_colls(("ants_macro", "train"))
    bpy.data.objects["ant_river"].hide_render = True; bpy.data.objects["ant_bridge"].hide_render = True
    coll = bpy.data.collections["ants_bridge"]
    ground = [bpy.data.objects["terrain"]]
    GAP0, GAP1 = -0.1, 28.1; MID = (GAP0 + GAP1) / 2
    F0, GROW, TRAVEL, CRAWL = 9.4, 3.4, 0.45, 1.7     # front distance from each rim at frame 1 (m), growth m/s
    for (c, rot, s_) in mesh_points("ant_bridge"):
        if c.x <= GAP0 + 0.15 or c.x >= GAP1 - 0.15:     # rim anchors and the climbers on the rim faces: always there
            add(P, c, rot, s_, gait=rnd.uniform(0.0, 3.0), phase=rnd.random() * 2, t0=-9, t1=-9)
            continue
        d = min(c.x - GAP0, GAP1 - c.x)
        ta = (d - F0) / GROW + rnd.gauss(0, 0.05)
        if ta <= 0:
            add(P, c, rot, s_, gait=rnd.choice((0.0, 0.0, 1.5)), phase=rnd.random() * 2, t0=-9, t1=-9)
            continue
        sgn = 1.0 if c.x < MID else -1.0
        dvec = Vector((sgn * CRAWL, 0, 0))
        base = c - dvec * TRAVEL
        yaw = 0.0 if sgn > 0 else math.pi
        # crawling ants face their way; they settle into the slot's pose on arrival (pose swap hidden by the gait)
        add(P, base, (rot[0] * 0.3, rot[1] * 0.3, yaw + rnd.gauss(0, 0.2)), s_, tuple(dvec), t0=ta - TRAVEL, t1=ta,
            tv=ta - TRAVEL, lift=0.16, gait=7.0, phase=rnd.random() * 2)
    cam_loc, tgt, lens, fstop, focus = (10.0, -24, 5.0), (13.0, 0, -1.4), 28, None, None

instancer("antv2_" + shot, P, coll, ground)
look_at(cam, cam_loc, tgt, lens, fstop, focus)
setup_render(sc, 1664 if not TEST else 832, 960 if not TEST else 480, S["samples"] if not TEST else 8)
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.render.fps = FPS; sc.frame_start, sc.frame_end = 1, n
outdir = os.path.join(RENDERS, f"_frames_T_{S['cut']}" + ("_test" if TEST else "")); os.makedirs(outdir, exist_ok=True)
sc.render.filepath = os.path.join(outdir, "f_")
t0_ = time.time()
if TEST:
    for f in (1, n // 2, n):
        sc.frame_set(f); sc.render.filepath = os.path.join(outdir, f"f_{f:04d}"); bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
print(f"ANIM_TIME {S['cut']} frames={n} {time.time() - t0_:.1f}s", flush=True)
