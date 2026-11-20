"""blender -b wagon.blend -P shots.py -- B12 B13 ...   (or train.blend with train shots)
   blender -b wagon.blend -P shots.py -- anim_wagon      (48 PNG frames -> renders/_frames_A_wagon_track)
   Optional flags: --preview (624x360, 12 samples, writes renders/_preview_<shot>.png)"""
import sys, os, math, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
from common import setup_render, look_at, render_still, RENDERS

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
PREVIEW = "--preview" in argv
argv = [a for a in argv if not a.startswith("--")]
sc = bpy.context.scene
cam = sc.camera

def vis(hide=(), show=()):
    for c in bpy.data.collections:
        c.hide_render = c.name in hide
    for o in bpy.data.objects:
        o.hide_render = o.name in hide

WAGON_SHOTS = {
    "B12_wagon_burst": dict(cam=(-25.0, -10.5, 1.2), tgt=(-11.0, 0.0, 2.6), lens=24, hide=(), root=(-7.0, 0, 0), move={"elephant1": (1.3, -3.9), "elephant2": (7.0, -2.8)}),
    "B13_wheel_close": dict(cam=(-2.75, -2.95, 0.32), tgt=(-1.3, -1.45, 1.15), lens=20, hide=("barn", "dust", "elephant1", "elephant2")),
    "B14_team_front": dict(cam=(-19.5, -6.0, 0.9), tgt=(-8.5, 0.4, 1.9), lens=28, hide=("barn", "dust")),
    "B15_wagon_side": dict(cam=(-3.6, -21, 4.6), tgt=(-3.6, 0, 2.6), lens=30, move={"elephant1": (-6.4, -3.9), "elephant2": (5.7, -3.9)}, hide=("barn", "dust")),
    "B16_bench": dict(cam=(-6.6, 0.0, 1.5), tgt=(-2.2, -0.1, 2.72), lens=20, fstop=2.8, focus=4.5, hide=("barn", "dust")),
}

TRAIN_SHOTS = {}
try:
    from track import train_shots
    TRAIN_SHOTS = train_shots()
except Exception as e:
    if "train" in bpy.data.filepath:
        raise

ALL = {**WAGON_SHOTS, **TRAIN_SHOTS}

def do_shot(name):
    S = ALL[name]
    vis(S.get('hide', ()), S.get('show', ()))
    bpy.data.objects.get("rig_root") and setattr(bpy.data.objects["rig_root"], "location", S.get('root', (0, 0, 0)))
    for nm, (x, y) in S.get('move', {}).items():
        o = bpy.data.objects[nm]
        o.location.x, o.location.y = x, y
    if 'setup' in S:
        S['setup']()
    look_at(cam, S['cam'], S['tgt'], S['lens'], S.get('fstop'), S.get('focus'), S.get('roll', 0.0))
    if PREVIEW:
        setup_render(sc, 624, 360, 12)
        return render_still(sc, os.path.join(RENDERS, f"_preview_{name}.png"))
    setup_render(sc, 1248, 720, S.get('samples', 48))
    return render_still(sc, os.path.join(RENDERS, f"{name}.png"))

def anim_wagon():
    """camera tracks alongside the wagon moving -X at 8 m/s; wheels roll at v/R."""
    vis(("barn", "dust"))
    root = bpy.data.objects["rig_root"]
    wheels = [o for o in bpy.data.objects if o.name.startswith("wheel")]
    base_rot = {w.name: tuple(w.rotation_euler) for w in wheels}
    R = 1.1; v = 8.0; fps = 24
    sc.render.fps = fps
    sc.frame_start, sc.frame_end = 1, 48
    for f in range(1, 49):
        t = (f - 1) / fps
        d = v * t
        root.location = (-d, 0, 0)
        root.keyframe_insert("location", frame=f)
        for w in wheels:
            rx, ry, rz = base_rot[w.name]
            # right-side wheels are spun 180deg about Z, so their local Y points the other way
            sgn = -1.0 if abs(rz) < 0.1 else 1.0
            w.rotation_euler = (rx, ry + sgn * d / R, rz)
            w.keyframe_insert("rotation_euler", frame=f)
        cx = -2.0 - 7.2 * t
        cam.location = (cx, -15.5, 2.6)
        look_at(cam, (cx, -15.5, 2.6), (cx - 2.5 - 0.8 * t, 0, 2.7), 30)
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)
    return "A_wagon_track"

def anim_track():
    from track import place_train
    vis(("train", "ants_river", "ants_bridge", "ants_macro"))
    sc.render.fps = 24
    sc.frame_start, sc.frame_end = 1, 48
    x0, x1 = -70.0, -2.4
    for f in range(1, 49):
        t = (f - 1) / 47.0
        e = 1 - (1 - t) ** 3
        x = x0 + (x1 - x0) * e
        z = 0.95 - 0.15 * e
        look_at(cam, (x, 0.0, z), (x + 12, 0, z - 1.2 - 1.0 * e), 22)
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)
    return "A_track_end_rush"

for a in argv:
    if a in ("anim_wagon", "anim_track"):
        name = anim_wagon() if a == "anim_wagon" else anim_track()
        setup_render(sc, 832, 480, 32)
        outdir = os.path.join(RENDERS, f"_frames_{name}")
        os.makedirs(outdir, exist_ok=True)
        sc.render.filepath = os.path.join(outdir, "f_")
        t0 = time.time()
        bpy.ops.render.render(animation=True)
        print(f"ANIM_TIME {name} {time.time() - t0:.1f}s ({(time.time() - t0) / 48:.1f}s/frame)")
    else:
        do_shot(a)
