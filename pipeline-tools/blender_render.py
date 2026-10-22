"""blender_render.py — photoreal product footage from the exact CAD (GLB), the PRIMARY promo source.

WHY THIS EXISTS (promo format, 2026-10-22): the Sitka promo that worked was rendered in Blender
Cycles straight from the CAD GLBs with PBR materials and HDRI light. A render of the real CAD
cannot invent a leg or drop a part, so it is the footage every other source is judged against
(frozen rule 28: "Blender first"). The Sitka engine (sitka-video/blender/engine.py) was tied to
that product's rig; this is the generic version every promo can use: GLB(s) in, a motivated
camera move, PBR presets per material/object name, studio or HDRI world, PNG frames out, plus
an optional flat object-ID pass so callouts can be checked against the real part's pixels.

Runs INSIDE Blender (5.x), headless:
  blender -b --factory-startup -noaudio --python pipeline-tools/blender_render.py -- SPEC.json [--preview]

SPEC.json (one shot; bin/make-promo writes it from promo.json "blender" entries, paths absolute):
  {"id": "l01_hero_orbit", "glb": ["/abs/sitka_chair.glb"], "out": "/abs/acquired/blender/l01_hero_orbit",
   "world": "studio" | "hdri", "hdri": "/abs/studio.exr", "hdri_strength": 1.0, "hdri_rot": 0,
   "camera": {"move": "orbit"|"push"|"pull"|"truck"|"crane"|"static", "lens": 50,
              "start_deg": -35, "end_deg": 20, "elev_deg": 8, "dist": null (auto),
              "amount": 0.25, "target": null (auto: bbox center) | [x, y, z], "frame_fill": 0.8},
   "frames": 120, "fps": 30, "res": [1920, 1080], "engine": "CYCLES"|"EEVEE", "samples": 48,
   "materials": {"carbon*": "carbon", "alu": "aluminum", "body": "mannequin"},  # fnmatch on material OR object name
   "ids": true}
Material presets: carbon, carbon_gloss, aluminum, titanium, anodized_orange, steel, fabric, foam,
glass_fiber, rubber, plastic_matte, mannequin, glow_teal. Unmatched materials keep the GLB's own.

Writes: <out>/beauty_0001.png..., <out>/ids_0001.png... (when "ids"), <out>/ids.json
({"#rrggbb": "object name"}), <out>/render_meta.json (camera, materials applied, engine, samples,
Blender version). Exit code 0 = every frame written; nonzero = read the log.
"""
import fnmatch
import json
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not argv:
    raise SystemExit("blender_render.py: give SPEC.json after --")
SPEC = json.load(open(argv[0]))
PREVIEW = "--preview" in argv
OUT = SPEC["out"]
os.makedirs(OUT, exist_ok=True)


# ------------------------------------------------------------------ materials
def principled(name, color, metal=0.0, rough=0.5, coat=0.0, sheen=0.0, emit=None, bump=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if coat:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.05
    if sheen:
        b.inputs["Sheen Weight"].default_value = sheen
    if emit:
        b.inputs["Emission Color"].default_value = (*emit[0], 1.0)
        b.inputs["Emission Strength"].default_value = emit[1]
    if bump:   # procedural micro-structure: twill for carbon, weave for fabric, cells for foam
        kind, scale, strength = bump
        tc = nt.nodes.new("ShaderNodeTexCoord")
        if kind == "wave":
            tex = nt.nodes.new("ShaderNodeTexWave")
            tex.inputs["Scale"].default_value = scale
            tex.inputs["Distortion"].default_value = 0.0
        elif kind == "voronoi":
            tex = nt.nodes.new("ShaderNodeTexVoronoi")
            tex.inputs["Scale"].default_value = scale
        else:
            tex = nt.nodes.new("ShaderNodeTexNoise")
            tex.inputs["Scale"].default_value = scale
        nt.links.new(tc.outputs["Object"], tex.inputs["Vector"])
        bn = nt.nodes.new("ShaderNodeBump")
        bn.inputs["Strength"].default_value = strength
        bn.inputs["Distance"].default_value = 0.002
        out_name = "Distance" if kind == "voronoi" else "Fac"
        nt.links.new(tex.outputs[out_name], bn.inputs["Height"])
        nt.links.new(bn.outputs["Normal"], b.inputs["Normal"])
    return m


PRESETS = {
    "carbon": lambda: principled("pv_carbon", (0.018, 0.018, 0.02), rough=0.32, coat=1.0, bump=("wave", 900, 0.15)),
    "carbon_gloss": lambda: principled("pv_carbon_gloss", (0.012, 0.012, 0.014), rough=0.18, coat=1.0, bump=("wave", 900, 0.1)),
    "aluminum": lambda: principled("pv_aluminum", (0.80, 0.81, 0.83), metal=1.0, rough=0.28, bump=("noise", 400, 0.03)),
    "titanium": lambda: principled("pv_titanium", (0.55, 0.53, 0.50), metal=1.0, rough=0.35),
    "anodized_orange": lambda: principled("pv_anod_orange", (0.95, 0.32, 0.04), metal=1.0, rough=0.3),
    "steel": lambda: principled("pv_steel", (0.62, 0.62, 0.63), metal=1.0, rough=0.22),
    "fabric": lambda: principled("pv_fabric", (0.05, 0.055, 0.06), rough=0.85, sheen=0.6, bump=("wave", 1400, 0.25)),
    "foam": lambda: principled("pv_foam", (0.07, 0.07, 0.075), rough=0.95, bump=("voronoi", 700, 0.3)),
    "glass_fiber": lambda: principled("pv_glassfiber", (0.75, 0.72, 0.62), rough=0.15, coat=1.0),
    "rubber": lambda: principled("pv_rubber", (0.02, 0.02, 0.02), rough=0.7),
    "plastic_matte": lambda: principled("pv_plastic", (0.08, 0.08, 0.085), rough=0.6),
    "mannequin": lambda: principled("pv_mannequin", (0.42, 0.42, 0.43), rough=0.75),
    "glow_teal": lambda: principled("pv_glow_teal", (0.05, 0.6, 0.55), rough=0.4, emit=((0.15, 0.85, 0.75), 3.0)),
}
_made = {}


def preset(name):
    if name not in PRESETS:
        raise SystemExit(f"unknown material preset '{name}' (known: {', '.join(sorted(PRESETS))})")
    if name not in _made:
        _made[name] = PRESETS[name]()
    return _made[name]


# ------------------------------------------------------------------ scene
bpy.ops.wm.read_factory_settings(use_empty=True)
for g in SPEC["glb"]:
    bpy.ops.import_scene.gltf(filepath=g)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
if not meshes:
    raise SystemExit("no meshes imported from " + ", ".join(SPEC["glb"]))

applied = {}
rules = SPEC.get("materials", {})
for o in meshes:
    for slot in o.material_slots:
        mname = slot.material.name if slot.material else ""
        for pat, pre in rules.items():
            if fnmatch.fnmatch(mname.lower(), pat.lower()) or fnmatch.fnmatch(o.name.lower(), pat.lower()):
                slot.material = preset(pre)
                applied[f"{o.name}/{mname}"] = pre
                break

# bounds in world space
bpy.context.view_layer.update()
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center = (lo + hi) / 2
size = max((hi - lo).length, 1e-3)
cam_spec = SPEC.get("camera", {})
target = Vector(cam_spec["target"]) if cam_spec.get("target") else center
scene = bpy.context.scene

# ground: a shadow catcher (hdri) or a dark sweep (studio)
bpy.ops.mesh.primitive_plane_add(size=size * 40, location=(center.x, center.y, lo.z))
ground = bpy.context.active_object
ground.name = "pv_ground"
world_kind = SPEC.get("world", "studio")
if world_kind == "hdri":
    # a real ground under the product (a shadow catcher alone left the product floating over the
    # HDRI's far-away ground): earthy, rough, bumped, fading to transparent into the HDRI beyond
    # ~3x the product size so the horizon stays the photo's own
    gm = principled("pv_ground", (0.20, 0.17, 0.13), rough=0.9, bump=("noise", 60, 0.35))   # sandy, so thin dark parts read against it
    gn = gm.node_tree.nodes
    tc_, mp_, gr_ = gn.new("ShaderNodeTexCoord"), gn.new("ShaderNodeMapping"), gn.new("ShaderNodeTexGradient")
    gr_.gradient_type = "SPHERICAL"
    mp_.inputs["Scale"].default_value = (1 / (3.0 * size), 1 / (3.0 * size), 1)
    tr = gn.new("ShaderNodeBsdfTransparent")
    mx_ = gn.new("ShaderNodeMixShader")
    gm.node_tree.links.new(tc_.outputs["Object"], mp_.inputs["Vector"])
    gm.node_tree.links.new(mp_.outputs["Vector"], gr_.inputs["Vector"])
    gm.node_tree.links.new(gr_.outputs["Fac"], mx_.inputs["Fac"])
    gm.node_tree.links.new(tr.outputs["BSDF"], mx_.inputs[1])
    gm.node_tree.links.new(gn["Principled BSDF"].outputs["BSDF"], mx_.inputs[2])
    gm.node_tree.links.new(mx_.outputs["Shader"], gn["Material Output"].inputs["Surface"])
    gm.blend_method = "HASHED" if hasattr(gm, "blend_method") else None
    ground.data.materials.append(gm)
else:
    fm = principled("pv_floor", (0.02, 0.02, 0.022), rough=0.5)
    fm.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.25
    # the sweep fades to pure black away from the product (shader mix, so reflections fade
    # too), so no horizon line shows behind the product
    nt_ = fm.node_tree
    fn = nt_.nodes
    tc_, mp_, gr_ = fn.new("ShaderNodeTexCoord"), fn.new("ShaderNodeMapping"), fn.new("ShaderNodeTexGradient")
    gr_.gradient_type = "SPHERICAL"
    mp_.inputs["Scale"].default_value = (1 / (1.6 * size), 1 / (1.6 * size), 1)   # fade radius 1.6x the product
    black = fn.new("ShaderNodeEmission")
    black.inputs["Strength"].default_value = 0.0
    mx_ = fn.new("ShaderNodeMixShader")
    nt_.links.new(tc_.outputs["Object"], mp_.inputs["Vector"])
    nt_.links.new(mp_.outputs["Vector"], gr_.inputs["Vector"])
    nt_.links.new(gr_.outputs["Fac"], mx_.inputs["Fac"])
    nt_.links.new(black.outputs["Emission"], mx_.inputs[1])
    nt_.links.new(fn["Principled BSDF"].outputs["BSDF"], mx_.inputs[2])
    nt_.links.new(mx_.outputs["Shader"], fn["Material Output"].inputs["Surface"])
    ground.data.materials.append(fm)

# world
w = bpy.data.worlds.new("pv_world")
scene.world = w
w.use_nodes = True
wn = w.node_tree
bg = wn.nodes["Background"]
if SPEC.get("hdri"):
    env = wn.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(SPEC["hdri"])
    mp = wn.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value[2] = math.radians(float(SPEC.get("hdri_rot", 0)))
    tc = wn.nodes.new("ShaderNodeTexCoord")
    wn.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    wn.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    wn.links.new(env.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = float(SPEC.get("hdri_strength", 1.0 if world_kind == "hdri" else 0.25))
if world_kind == "studio":
    # the HDRI lights the product, the camera sees near-black (the Sitka studio look)
    lp = wn.nodes.new("ShaderNodeLightPath")
    dark = wn.nodes.new("ShaderNodeBackground")
    dark.inputs["Color"].default_value = (0.004, 0.004, 0.005, 1)
    mix = wn.nodes.new("ShaderNodeMixShader")
    wn.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
    wn.links.new(bg.outputs["Background"], mix.inputs[1])
    wn.links.new(dark.outputs["Background"], mix.inputs[2])
    wn.links.new(mix.outputs["Shader"], wn.nodes["World Output"].inputs["Surface"])
    # key + orange and teal rims
    for name, loc, color, power in (("key", (1.2, -1.4, 1.3), (1.0, 0.97, 0.92), 120),
                                    ("rim_orange", (-1.6, 1.2, 0.9), (1.0, 0.45, 0.12), 160),
                                    ("rim_teal", (1.6, 1.4, 1.1), (0.2, 0.85, 0.8), 140)):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy = power * size ** 2
        ld.color = color
        ld.size = size * 0.6
        lo_ = bpy.data.objects.new(name, ld)
        scene.collection.objects.link(lo_)
        lo_.location = center + Vector(loc) * size
        lo_.rotation_euler = (target - lo_.location).to_track_quat("-Z", "Y").to_euler()

# camera
cd = bpy.data.cameras.new("pv_cam")
cd.lens = float(cam_spec.get("lens", 50))
cd.sensor_width = 36
cam = bpy.data.objects.new("pv_cam", cd)
scene.collection.objects.link(cam)
scene.camera = cam
fov = 2 * math.atan(cd.sensor_width / 2 / cd.lens) * (9 / 16)   # vertical fov at 16:9
fill = float(cam_spec.get("frame_fill", 0.8))
dist = float(cam_spec.get("dist") or (size * 0.5 / fill) / math.tan(fov / 2))
elev = math.radians(float(cam_spec.get("elev_deg", 8)))
a0 = math.radians(float(cam_spec.get("start_deg", -35)))
a1 = math.radians(float(cam_spec.get("end_deg", 20)))
amount = float(cam_spec.get("amount", 0.25))
move = cam_spec.get("move", "orbit")
nf = int(SPEC.get("frames", 120))


def ease(u):
    return u * u * (3 - 2 * u)


def cam_at(u):
    """camera location + look target at normalized time u (0..1); every move eases in/out."""
    e = ease(u)
    ang, d, tgt, el = a0, dist, target.copy(), elev
    if move == "orbit":
        ang = a0 + (a1 - a0) * e
    elif move == "push":
        d = dist * (1 - amount * e)
    elif move == "pull":
        d = dist * (1 - amount * (1 - e))
    elif move == "crane":
        el = elev + math.radians(25) * amount * 4 * (e - 0.5)
    pos = tgt + Vector((d * math.cos(el) * math.sin(ang), -d * math.cos(el) * math.cos(ang), d * math.sin(el)))
    if move == "truck":   # slide sideways, keep looking ahead (parallax)
        side = Vector((math.cos(ang), math.sin(ang), 0)) * dist * amount * (e - 0.5) * 2
        pos += side
        tgt = tgt + side * 0.6
    return pos, tgt


for f in range(nf):
    pos, tgt = cam_at(f / max(1, nf - 1))
    cam.location = pos
    cam.rotation_euler = (tgt - pos).to_track_quat("-Z", "Y").to_euler()
    cam.keyframe_insert("location", frame=f + 1)
    cam.keyframe_insert("rotation_euler", frame=f + 1)

# render settings
rx, ry = SPEC.get("res", [1920, 1080])
scene.render.resolution_x, scene.render.resolution_y = int(rx), int(ry)
scene.render.resolution_percentage = 50 if PREVIEW else 100
scene.render.fps = int(SPEC.get("fps", 30))
scene.frame_start, scene.frame_end = 1, nf
engine = SPEC.get("engine", "CYCLES").upper()
if engine == "CYCLES":
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    try:
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for dev in prefs.devices:
            dev.use = True
        scene.cycles.device = "GPU"
    except Exception as e:  # noqa: BLE001 — CPU still renders, just slower; say so
        print(f"blender_render: Metal unavailable ({e}); rendering on CPU")
    scene.cycles.samples = int(SPEC.get("samples", 48)) if not PREVIEW else 12
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.use_denoising = True
else:
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [
        e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False

scene.render.filepath = os.path.join(OUT, "beauty_")
bpy.ops.render.render(animation=True)

ids = {}
if SPEC.get("ids", True):
    # flat object-ID pass (Workbench, no AA): one exact colour per object, for callout masks
    import colorsys
    for k, o in enumerate(sorted(meshes, key=lambda o: o.name)):
        h = (k * 0.61803398875) % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, 0.55 + 0.45 * ((k * 7) % 3) / 2, 0.55 + 0.45 * ((k * 5) % 2))
        q = tuple(round(c * 255) for c in (r, g, b))
        o.color = (q[0] / 255, q[1] / 255, q[2] / 255, 1)
        ids["#%02x%02x%02x" % q] = o.name
    ground.hide_render = True
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "FLAT"
    scene.display.shading.color_type = "OBJECT"
    scene.display.render_aa = "OFF"
    scene.display_settings.display_device = "sRGB"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.filepath = os.path.join(OUT, "ids_")
    bpy.ops.render.render(animation=True)
    json.dump(ids, open(os.path.join(OUT, "ids.json"), "w"), indent=1)

json.dump({"blender": bpy.app.version_string, "engine": engine, "samples": SPEC.get("samples", 48),
           "preview": PREVIEW, "frames": nf, "fps": scene.render.fps, "res": [rx, ry],
           "camera": {"move": move, "lens": cd.lens, "dist": round(dist, 4), "start_deg": math.degrees(a0),
                      "end_deg": math.degrees(a1), "elev_deg": math.degrees(elev), "amount": amount,
                      "target": [round(v, 4) for v in target]},
           "materials": applied, "world": world_kind, "hdri": os.path.basename(SPEC.get("hdri") or ""),
           "objects": len(meshes)}, open(os.path.join(OUT, "render_meta.json"), "w"), indent=1)
print(f"blender_render: wrote {nf} frames to {OUT}")
