"""c03b_wheel (B13_wheel_close framing): the fire-wagon's front-left wheel rolling over desert dirt, rig-correct.
  * the whole wagon (rig_root) travels -X at constant speed; every wheel turns by distance travelled / R about its own
    axle (R = 1.1 m, the iron tyre's outer radius), so the contact point is at rest on the ground: no slip
  * speed is chosen so a 14-spoke wheel turns 9 deg a frame (< half the 25.7 deg spoke spacing): the spokes can never
    strobe backwards; Cycles motion blur (shutter 0.5) smears them
  * the camera rides with the wagon (B13 position), so the wheel holds frame and the ground streams past under it
  * dust: volume puffs kicked off the tyre where it leaves the ground, left behind in the world (fx.volume_puffs)
Usage: blender -b wagon.blend -P anim_wheel.py -- [--test]"""
import sys, os, math, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
from common import setup_render, look_at, RENDERS
from fx import volume_puffs   # soft surface puffs (fx.puff_mat)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
TEST = "--test" in argv
sc = bpy.context.scene; cam = sc.camera
FPS = 24; HANDLE = 6; CUT = "c03b_wheel"; SEC = 0.9
n = int(round(SEC * FPS)) + 2 * HANDLE
R = 1.1
DEG_PER_FRAME = 9.0
v = math.radians(DEG_PER_FRAME) * R * FPS          # m/s
for c in bpy.data.collections:
    if c.name in ("barn", "dust"): c.hide_render = True
for nm in ("elephant1", "elephant2"):
    o = bpy.data.objects.get(nm)
    if o: o.hide_render = True
root = bpy.data.objects["rig_root"]
wheels = [o for o in bpy.data.objects if o.name.startswith("wheel")]
base_rot = {w.name: tuple(w.rotation_euler) for w in wheels}
# ground check under the path of the front-left contact point
ground = bpy.data.objects["ground"]
dg = bpy.context.evaluated_depsgraph_get()
gz = []
for f in range(1, n + 1):
    d = v * (f - 1) / FPS
    hit, loc, nor, idx = ground.evaluated_get(dg).ray_cast(Vector((-1.5 - d, -1.45, 5.0)), Vector((0, 0, -1)))
    gz.append(loc.z if hit else None)
print("GROUND_Z under FL contact: min %.3f max %.3f" % (min(gz), max(gz)), "v=%.2f m/s" % v, flush=True)
z0 = sum(gz) / len(gz)
CAM_REL, TGT_REL = Vector((-2.75, -2.95, 0.32)), Vector((-1.3, -1.45, 1.15))
for f in range(0, n + 2):   # keys past each end: motion blur on the first/last frame
    t = (f - 1) / FPS
    d = v * t
    root.location = (-d, 0, 0); root.keyframe_insert("location", frame=f)
    for w in wheels:
        rx, ry, rz = base_rot[w.name]
        sgn = -1.0 if abs(rz) < 0.1 else 1.0      # right-side wheels are spun 180 deg about Z (local Y flipped)
        w.rotation_euler = (rx, ry + sgn * d / R, rz); w.keyframe_insert("rotation_euler", frame=f)
    off = Vector((-d, 0, 0)) + Vector((0, 0, 0.012 * math.sin(t * 9.0)))   # tiny ride bob on the camera
    look_at(cam, CAM_REL + off, TGT_REL + Vector((-d, 0, 0)), 20)
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
# dust kicked up behind the front-left tyre (and the rear-left one further back)
rr = random.Random(5); births = []
fr = -24.0
while fr <= n + 1:
    d = v * (fr - 1) / FPS
    for wx, amt in ((-1.5, 1.0), (1.6, 0.8)):
        if rr.random() > amt: continue
        p0 = Vector((wx - d + 0.3 + rr.uniform(0, 0.25), -1.45 + rr.uniform(-0.12, 0.12), z0 + 0.06))
        u0 = Vector((rr.uniform(-0.6, 0.9), rr.uniform(-0.9, 0.2), rr.uniform(0.7, 1.6)))
        births.append(dict(f=fr, p0=p0, u0=u0, k=1.8, r0=0.07, grow=0.55 + rr.uniform(0, 0.35), life=1.5, dens=1.1,
                           dmul=rr.uniform(0.6, 1.0)))
    fr += 0.5
volume_puffs("dust_kick", births, range(0, n + 2), FPS, color=(0.86, 0.6, 0.4), coll=bpy.data.collections["rig"], buoy=0.15)
setup_render(sc, 1664 if not TEST else 832, 960 if not TEST else 480, 48 if not TEST else 8)
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.5
sc.render.fps = FPS; sc.frame_start, sc.frame_end = 1, n
outdir = os.path.join(RENDERS, f"_frames_T_{CUT}" + ("_test" if TEST else "")); os.makedirs(outdir, exist_ok=True)
sc.render.filepath = os.path.join(outdir, "f_")
t0 = time.time()
if TEST:
    for f in (1, n // 2, n):
        sc.frame_set(f); sc.render.filepath = os.path.join(outdir, f"f_{f:04d}"); bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
print(f"ANIM_TIME {CUT} frames={n} {time.time() - t0:.1f}s", flush=True)
