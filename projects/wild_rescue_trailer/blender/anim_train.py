"""Mechanically correct train animations for WILD RESCUE (2026-11-01, Matt 10:45 AM: "the wheels are moving under the
train unnaturally"). AI i2v never animates the wheels in a close or medium train shot; Blender does, with real motion:
  * every vehicle mesh (joined at build time) is split into loose parts; the parts of each wheel (tire, flange, rim,
    spokes, hub, crank pin, counterweight) go under an axle pivot that turns by distance travelled / wheel radius
    (rotation about the vehicle's local +Y; the top of the wheel moves forward)
  * the loco side rods ride the crank pins (pure translation, they stay level), the main rod pivots on a crosshead that
    slides in its guides (rod length kept), so the motion linkage is physically consistent
  * every vehicle rides the rails via track.P (the same path the rails were swept on), constant speed, wheels locked to
    the rails: no slip, no drift, the bodies riding on their wheels
  * Cycles motion blur (shutter 0.5) so fast spokes smear like a camera would see them
Usage: blender -b train.blend -P anim_train.py -- <shot> [--test]   shots: rails | edge | wide | whistle
Frames -> renders/_frames_T_<cut_id>/f_####.png at 1664x960 (2x the 832x480 cut source), cut frames + 6 handles each side."""
import sys, os, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
from common import setup_render, look_at, RENDERS
from track import P, VEHICLES, RAIL_TOP

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
TEST = "--test" in argv
shot = [a for a in argv if not a.startswith("--")][0]
sc = bpy.context.scene; cam = sc.camera
FPS = 24
RAIL_Y = 0.754
# wheel table in vehicle-local coords: (x, z_centre, R). y = +/- RAIL_Y. z=0 is the rail top.
WHEELS = {"loco": [(0.9, 0.78, 0.78), (-0.9, 0.78, 0.78), (3.85, 0.42, 0.42), (2.9, 0.42, 0.42)],
          "tender": [(x0 + a, 0.42, 0.42) for x0 in (1.5, -1.5) for a in (-0.55, 0.55)]}
for k in range(4):
    WHEELS[f"car{k + 1}"] = [(x0 + a, 0.42, 0.42) for x0 in (3.5, -3.5) for a in (-0.55, 0.55)]
RD, TH, PIN = 0.78, math.radians(40), 0.34

def hide(names):
    for c in bpy.data.collections:
        c.hide_render = c.name in names
        c.hide_viewport = c.name in names

def split(ob):
    """loose parts of one joined vehicle -> list of objects (mesh coords stay vehicle-local)."""
    for o in bpy.context.view_layer.objects: o.select_set(False)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
    return [o for o in bpy.context.selected_objects]

def bbox(o):
    vs = [v.co for v in o.data.vertices]
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return lo, hi, [v.copy() for v in vs]

rig = {}
for name, _, _ in VEHICLES:
    ob = bpy.data.objects[name]
    coll = ob.users_collection[0]
    root = bpy.data.objects.new(f"{name}_root", None); coll.objects.link(root)
    parts = split(ob)
    piv, side_rods, main_rods, crossheads = {}, [], [], []
    for (x, z, R) in WHEELS[name]:
        for s in (-1, 1):
            e = bpy.data.objects.new(f"{name}_axle_{x}_{s}", None); coll.objects.link(e)
            e.parent = root; e.location = (x, s * RAIL_Y, z); e.rotation_mode = 'XYZ'
            piv[(x, s)] = (e, R)
    for o in parts:
        lo, hi, vs = bbox(o)
        c = (lo + hi) / 2; size = hi - lo
        o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0); o.parent = root
        home = None
        for (x, s), (e, R) in piv.items():
            zc = e.location.z
            if all((v.x - x) ** 2 + (v.z - zc) ** 2 <= (R + 0.07) ** 2 and abs(v.y - s * RAIL_Y) <= 0.25 for v in vs):
                home = (e, x, s, zc); break
        if home:
            e, x, s, zc = home
            o.parent = e; o.location = (-x, -s * RAIL_Y, -zc)
            continue
        if name == "loco":
            s = 1 if c.y > 0 else -1
            if 1.6 < size.x < 2.4 and 0.8 < abs(c.y) < 1.0 and 0.3 < c.z < 1.3 and size.z < 0.3:
                side_rods.append((o, s))
            elif size.x > 0.5 and abs(c.y) > 0.85 and 1.9 < hi.x < 2.2 and lo.x > 0.6 and size.z > 0.1 and size.y < 0.25:
                main_rods.append((o, s, lo, hi))
            elif abs(c.x - 2.05) < 0.05 and abs(abs(c.y) - 0.98) < 0.05 and abs(c.z - 1.0) < 0.05:
                crossheads.append((o, s))
    rig[name] = dict(root=root, piv=piv, side_rods=side_rods, main_rods=main_rods, crossheads=crossheads)
    print(f"[rig] {name}: {len(parts)} parts, wheels {sum(1 for o in parts if o.parent and o.parent.name.startswith(name + '_axle'))}, "
          f"side rods {len(side_rods)}, main rods {len(main_rods)}, crossheads {len(crossheads)}", flush=True)

# main rods: re-parent to a pivot at the crosshead end
XH = {}
for o, s, lo, hi in rig["loco"]["main_rods"]:
    xh = Vector((2.05, s * 0.98, 1.0))
    e = bpy.data.objects.new(f"mainrod_piv_{s}", None); rig["loco"]["root"].users_collection[0].objects.link(e)
    e.parent = rig["loco"]["root"]; e.location = xh
    o.parent = e; o.location = -xh
    XH[s] = (e, o)

def crank(s): return TH if s > 0 else TH + math.pi / 2
def pin(ax, s, th):
    a = crank(s) - th
    return Vector((ax + PIN * math.cos(a), s * 0.88, RD + PIN * math.sin(a)))

def pose(s0, dist):
    """put every vehicle on the rails with its centre at track distance s0 (as track.place_train) and turn every wheel
    by dist / R (dist = metres travelled since the shot started)."""
    for name, off, wb in VEHICLES:
        r = rig[name]["root"]; sc_ = s0 - off
        pf, pr = P(sc_ - wb), P(sc_ + wb); c = (pf + pr) / 2
        r.location = (c.x, c.y, RAIL_TOP); r.rotation_euler = (0, 0, math.atan2(pf.y - pr.y, pf.x - pr.x))
        for (x, s), (e, R) in rig[name]["piv"].items():
            e.rotation_euler = (0, dist / R, 0)
    th = dist / RD
    for o, s in rig["loco"]["side_rods"]:
        d = pin(0.9, s, th) - pin(0.9, s, 0.0); o.location = (d.x, 0, d.z)
    for s, (e, o) in XH.items():
        p0 = pin(0.9, s, 0.0) + Vector((0, s * 0.08, 0)); xh0 = Vector((2.05, s * 0.98, 1.0))
        L = math.hypot(p0.x - xh0.x, p0.z - xh0.z)
        p = pin(0.9, s, th)
        xc = p.x + math.sqrt(max(1e-6, L * L - (1.0 - p.z) ** 2))
        e.location = (xc, s * 0.98, 1.0)
        a0 = math.atan2(p0.z - xh0.z, p0.x - xh0.x); a1 = math.atan2(p.z - 1.0, p.x - xc)
        e.rotation_euler = (0, -(a1 - a0), 0)
    for o, s in rig["loco"]["crossheads"]:
        p = pin(0.9, s, th); p0 = pin(0.9, s, 0.0) + Vector((0, s * 0.08, 0)); xh0 = Vector((2.05, s * 0.98, 1.0))
        L = math.hypot(p0.x - xh0.x, p0.z - xh0.z)
        o.location = (p.x + math.sqrt(max(1e-6, L * L - (1.0 - p.z) ** 2)) - 2.05, 0, 0)

ANTS = ("ants_river", "ants_bridge", "ants_macro", "ant_src")
# 2026-11-01 evening rebuild: 1664x960, frames = cut frames + 6-frame handles each side (cut seconds from beats.json)
HANDLE = 6
def nfr(sec): return int(round(sec * FPS)) + 2 * HANDLE
SHOTS = {
    # c02a_rails 0.8 s: low, riding alongside the drivers as the loco screams along (B07 framing, camera travels with it)
    # shutter 0.75: at 11 m/s a driver turns 34 deg a frame (14 spokes = 25.7 deg apart), so the spokes smear into a disc
    # the way a film camera sees them instead of strobing; crank pins, counterweights and rods stay readable
    "rails": dict(cut="c02a_rails", sec=0.8, v=11.0, s_end=60.0, cam_rel=(1.1, -2.55, 0.5), tgt_rel=(-0.8, -0.6, 0.95),
                  lens=28, fstop=4.0, focus=2.4, drift=-0.6, shutter=0.75),
    # c07h_edge 1.2 s: static low camera at the rim (B31 framing), the lead wheels roll onto the last ties at the end
    "edge": dict(cut="c07h_edge", sec=1.2, v=2.6, s_end=4.3, cam=(-3.6, -3.4, 2.2), tgt=(1.0, 0.4, -0.8), lens=20, fstop=8.0,
                 focus=4.2),
    # c04a_train 1.5 s: wide, the circus train barrels across the desert, slow push in (B17 framing)
    "wide": dict(cut="c04a_train", sec=1.5, v=15.0, s_end=185.0, cam=(-248, -40, 18), tgt=(-200, 10, 0), lens=42, push=0.22, smoke=True),
    # c07d_whistle 0.8 s: B27 framing, the brass whistle blasting a jet of steam, camera riding with the moving loco
    "whistle": dict(cut="c07d_whistle", sec=0.8, v=7.0, s_end=60.0, cam_rel=(0.35, -2.35, 4.05), tgt_rel=(-0.95, 0.0, 4.1),
                    lens=35, fstop=5.6, focus=2.6, drift=0.0, steam=True),
}
S = SHOTS[shot]
n = nfr(S["sec"])
hide(ANTS)
setup_render(sc, 1664 if not TEST else 832, 960 if not TEST else 480, S.get("samples", 32) if not TEST else 8)
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = S.get("shutter", 0.5)
sc.render.fps = FPS; sc.frame_start, sc.frame_end = 1, n
def s_at(f): return S["s_end"] + S["v"] * (n - f) / FPS
for f in range(0, n + 2):   # keys one frame past each end so motion blur on frames 1 and n has motion on both sides
    t = (f - 1) / FPS
    s0 = s_at(f)
    dist = S["v"] * t
    pose(s0, dist)
    for name in rig:
        r = rig[name]["root"]; r.keyframe_insert("location", frame=f); r.keyframe_insert("rotation_euler", frame=f)
        for (e, R) in rig[name]["piv"].values(): e.keyframe_insert("rotation_euler", frame=f)
    for o, s in rig["loco"]["side_rods"] + rig["loco"]["crossheads"]: o.keyframe_insert("location", frame=f)
    for e, o in XH.values(): e.keyframe_insert("location", frame=f); e.keyframe_insert("rotation_euler", frame=f)
    if "cam_rel" in S:   # camera rides with the loco (plus a slow drift back along the drivers)
        bpy.context.view_layer.update()
        L = rig["loco"]["root"]; M = L.matrix_world.copy()
        cl = M @ (Vector(S["cam_rel"]) + Vector((S["drift"] * t, 0, 0))); tl = M @ (Vector(S["tgt_rel"]) + Vector((S["drift"] * t, 0, 0)))
        bpy.context.view_layer.update()
        look_at(cam, cl, tl, S["lens"], S.get("fstop"), S.get("focus"))
    else:
        c0, t0 = Vector(S["cam"]), Vector(S["tgt"])
        k = S.get("push", 0.0) * t / max(1e-6, (n - 1) / FPS)
        look_at(cam, c0 + (t0 - c0) * k, t0, S["lens"], S.get("fstop"), S.get("focus"))
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
    bpy.context.view_layer.update()
def loco_M(fr):
    s0 = s_at(fr); pf, pr = P(s0 - 1.9), P(s0 + 1.9); c = (pf + pr) / 2
    return Matrix.Translation((c.x, c.y, RAIL_TOP)) @ Matrix.Rotation(math.atan2(pf.y - pr.y, pf.x - pr.x), 4, 'Z')
def emit(f_from, step, local, jet, rr, **kw):
    """puffs leave a loco-local point at loco velocity + a loco-local jet velocity (randomised by jet[1])"""
    births = []; fr = f_from
    while fr <= n + 1:
        M = loco_M(fr); R3 = M.to_3x3()
        p0 = M @ (Vector(local) + Vector([rr.uniform(-0.02, 0.02) for _ in range(3)]))
        u0 = (R3 @ Vector((1, 0, 0))).normalized() * S["v"] + R3 @ Vector([jv + rr.uniform(-js, js) for jv, js in zip(*jet)])
        births.append(dict(f=fr, p0=p0, u0=u0, **{k: (v_(rr) if callable(v_) else v_) for k, v_ in kw.items()}))
        fr += step
    return births
import random as _r
from fx import volume_puffs
if S.get("steam"):
    # steam leaves the whistle mouth at loco velocity + jet velocity, then air drag (k) brings it to rest in the world,
    # so it peels back off the moving whistle; each puff grows and thins out
    sc.cycles.volume_bounces = 1
    births = emit(-14.0, 0.34, (-0.66, 0.0, 3.62), ((2.0, 0.0, 6.5), (0.5, 0.6, 1.0)), _r.Random(7),
                  k=2.4, r0=0.07, grow=lambda r: 0.9 + r.uniform(0, 0.4), life=1.0, dens=2.2)
    volume_puffs("steam", births, range(0, n + 2), FPS, color=(0.97, 0.97, 0.98), coll=bpy.data.collections["train"])
if S.get("smoke"):
    # the stack's steam trail: puffs stay in the world as the train runs on, so the trail is v x life long
    sc.cycles.volume_bounces = 1
    births = emit(-48.0, 1.0, (3.6, 0.0, 5.05), ((0.0, 0.0, 3.2), (0.4, 0.4, 0.8)), _r.Random(3),
                  k=1.3, r0=0.35, grow=lambda r: 1.3 + r.uniform(0, 0.6), life=2.4, dens=1.6)
    volume_puffs("smoke", births, range(0, n + 2), FPS, color=(0.93, 0.92, 0.92), coll=bpy.data.collections["train"], buoy=0.4)
outdir = os.path.join(RENDERS, f"_frames_T_{S['cut']}" + ("_test" if TEST else "")); os.makedirs(outdir, exist_ok=True)
sc.render.filepath = os.path.join(outdir, "f_")
for f_ in (1, n):
    sc.frame_set(f_)
    print("DBG f", f_, "loco_root", tuple(round(x, 2) for x in rig["loco"]["root"].matrix_world.translation), "cam", tuple(round(x, 2) for x in cam.matrix_world.translation), flush=True)
if "--dry" in argv:
    raise SystemExit
t0 = time.time()
if TEST:
    for f in (1, n // 2, n):
        sc.frame_set(f); sc.render.filepath = os.path.join(outdir, f"f_{f:04d}"); bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
print(f"ANIM_TIME {S['cut']} frames={n} {time.time() - t0:.1f}s", flush=True)
