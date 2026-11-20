"""blender -b -P build_wagon.py  -> wagon.blend  (fire-wagon, team, crew proxies, firehouse barn, desert)
Wagon faces -X (team out in front at negative X, wagon behind)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from common import _finish

sc = reset_scene()
setup_render(sc)
world_sky(0.55)
sun((0.62, -0.5, 0.42), energy=6.5, angle_deg=8)

# ------------------------------------------------------------------ materials
D = desert_mats()
RED = wood_mat("red_paint", (0.42, 0.02, 0.015), (0.72, 0.05, 0.03), 'X', rough=0.32, coat=0.4, bump=0.04)
REDZ = wood_mat("red_paint_z", (0.42, 0.02, 0.015), (0.72, 0.05, 0.03), 'Z', rough=0.32, coat=0.4, bump=0.04)
OAK = wood_mat("oak", (0.34, 0.16, 0.06), (0.62, 0.36, 0.15), 'Z', rough=0.45, coat=0.3)
WHEELWOOD = wood_mat("wheel_wood", (0.45, 0.22, 0.07), (0.78, 0.5, 0.2), 'X', rough=0.4, coat=0.35)
GOLD = flat_mat("gold", (1.0, 0.7, 0.28), rough=0.22, metal=1.0)
BRASS = flat_mat("brass", (0.95, 0.66, 0.26), rough=0.16, metal=1.0)
IRON = flat_mat("iron", (0.16, 0.16, 0.18), rough=0.42, metal=1.0)
LEATHER = flat_mat("leather", (0.22, 0.09, 0.035), rough=0.55)
BLACKLEATHER = flat_mat("black_leather", (0.03, 0.025, 0.025), rough=0.35, coat=0.3)
CANVAS = ramp_mat("canvas", 'noise', ((0.3, (0.7, 0.62, 0.45)), (0.7, (0.88, 0.8, 0.62))), rough=0.85, scale=40, bump=0.2, bump_dist=0.003)
GLASS = flat_mat("lamp_glass", (1.0, 0.8, 0.45), rough=0.1, emit=(1.0, 0.65, 0.3), emit_str=3.0)
EYE = flat_mat("eye", (0.01, 0.01, 0.01), rough=0.08, coat=1.0)
HOOF = flat_mat("hoof", (0.08, 0.06, 0.05), rough=0.5)
CREAM = flat_mat("cream", (0.95, 0.88, 0.72), rough=0.4)
PINK = flat_mat("pink", (0.95, 0.55, 0.5), rough=0.5)
HORSE1 = flat_mat("horse_chestnut", (0.48, 0.2, 0.07), rough=0.45)
HORSE2 = flat_mat("horse_bay", (0.3, 0.13, 0.05), rough=0.45)
MANE = flat_mat("mane", (0.08, 0.04, 0.02), rough=0.6)
CAMEL = flat_mat("camel", (0.78, 0.55, 0.3), rough=0.6)
COW = ramp_mat("cow_spots", 'noise', ((0.48, (0.02, 0.02, 0.02)), (0.5, (0.95, 0.94, 0.9))), rough=0.5, scale=1.1, detail=2, constant=True)
GIRAFFE = ramp_mat("giraffe", 'voronoi_edge', ((0.0, (0.98, 0.88, 0.62)), (0.05, (0.98, 0.88, 0.62)), (0.07, (0.78, 0.38, 0.1)), (1.0, (0.62, 0.27, 0.06))), rough=0.55, scale=3.2)
GIRAFFE_DARK = flat_mat("giraffe_dark", (0.3, 0.15, 0.05), rough=0.6)
ELE = ramp_mat("elephant", 'noise', ((0.3, (0.36, 0.37, 0.42)), (0.7, (0.5, 0.5, 0.55))), rough=0.7, scale=3, bump=0.3, bump_dist=0.01)
BEAR = flat_mat("bear", (0.36, 0.18, 0.07), rough=0.6)
BEARLIGHT = flat_mat("bear_muzzle", (0.75, 0.55, 0.32), rough=0.6)
DOG = flat_mat("dog", (0.85, 0.6, 0.3), rough=0.55)
DOGDARK = flat_mat("dog_ears", (0.45, 0.25, 0.1), rough=0.55)
HELMET = flat_mat("helmet_red", (0.75, 0.04, 0.02), rough=0.25, coat=0.8)
NOSE = flat_mat("nose", (0.03, 0.02, 0.02), rough=0.2, coat=0.6)
BLANKET = ramp_mat("blanket", 'wave_x', ((0.45, (0.7, 0.05, 0.04)), (0.55, (1.0, 0.72, 0.22))), rough=0.6, scale=1.6, constant=True)

# ------------------------------------------------------------------ environment
env = new_coll("env"); set_coll(env)
def h_wagon(x, y):
    return dunes(x, y, 1.6) * smoothstep(9, 45, abs(y))
xs = axis_samples([(-450, -70, 5), (-70, 50, 0.6), (50, 450, 5)])
ys = axis_samples([(-450, -40, 5), (-40, 40, 0.6), (40, 450, 5)])
grid_mesh("ground", xs, ys, h_wagon, D['sand'])
mesas_ring(D['strata'], [(10, 520, 90, 70), (35, 700, 140, 95), (70, 480, 60, 110), (110, 800, 200, 80), (150, 600, 80, 60),
                         (185, 650, 120, 100), (215, 450, 50, 85), (250, 900, 250, 120), (290, 560, 90, 75), (325, 750, 150, 90),
                         (200, 330, 40, 55), (160, 380, 55, 45), (230, 300, 30, 40)])
avoid = lambda x, y: (abs(y) < 11 and -60 < x < 40) or (-2 < x < 25 and abs(y) < 14)
scatter("rocks", 900, (-300, 300, -300, 300), h_wagon, avoid, 'rock', D['rock'], 1)
scatter("bushes", 700, (-300, 300, -300, 300), h_wagon, avoid, 'bush', D['bush'], 2)
scatter("cacti", 40, (-160, 160, -160, 160), h_wagon, lambda x, y: avoid(x, y) or (abs(y) < 18), 'cactus', D['cactus'], 3)

# ------------------------------------------------------------------ barn (front wall at x=1.5, doors open toward -X)
barn = new_coll("barn"); set_coll(barn)
STONE = ramp_mat("redrock_walls", 'wave_z', ((0.0, (0.5, 0.15, 0.06)), (0.35, (0.78, 0.32, 0.13)), (0.6, (0.9, 0.5, 0.26)), (1.0, (0.62, 0.2, 0.08))),
                 rough=0.85, bump=0.6, bump_dist=0.05, scale=0.9, distortion=6.0, detail=4)
ROOF = ramp_mat("roof", 'wave_y', ((0.4, (0.32, 0.1, 0.05)), (0.6, (0.5, 0.18, 0.08))), rough=0.75, scale=2.2, bump=0.4, constant=False)
FLOOR = wood_mat("barn_floor", (0.18, 0.09, 0.04), (0.32, 0.17, 0.08), 'X', rough=0.7, coat=0.0)
CREAMPAINT = flat_mat("cream_paint", (0.95, 0.85, 0.62), rough=0.4)
bx0, bx1 = 1.5, 21.0
box("pierL", (0.7, 4.0, 9.0), (bx0 + 0.35, -7.5, 4.5), mat=STONE, bevel=0.04)
box("pierR", (0.7, 4.0, 9.0), (bx0 + 0.35, 7.5, 4.5), mat=STONE, bevel=0.04)
box("lintel", (0.7, 11.2, 0.6), (bx0 + 0.35, 0, 8.8), mat=STONE)
box("sideL", (bx1 - bx0, 0.7, 9.0), ((bx0 + bx1) / 2, -9.15, 4.5), mat=STONE)
box("sideR", (bx1 - bx0, 0.7, 9.0), ((bx0 + bx1) / 2, 9.15, 4.5), mat=STONE)
box("back", (0.7, 19.0, 9.0), (bx1, 0, 4.5), mat=STONE)
box("floor", (bx1 - bx0, 18.0, 0.06), ((bx0 + bx1) / 2, 0, 0.03), mat=FLOOR)
for gx in (bx0 + 0.35, bx1):
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in [(gx - 0.35, -9.5, 9.0), (gx - 0.35, 9.5, 9.0), (gx - 0.35, 0, 13.2),
                                   (gx + 0.35, -9.5, 9.0), (gx + 0.35, 9.5, 9.0), (gx + 0.35, 0, 13.2)]]
    bm.faces.new((v[0], v[1], v[2])); bm.faces.new((v[5], v[4], v[3]))
    bm.faces.new((v[0], v[3], v[4], v[1])); bm.faces.new((v[1], v[4], v[5], v[2])); bm.faces.new((v[2], v[5], v[3], v[0]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _finish("gable", bm, STONE)
ang = math.atan2(4.4, 10.0)
for s in (-1, 1):
    box("roof", (bx1 - bx0 + 1.6, 11.2, 0.3), ((bx0 + bx1) / 2, s * 5.0, 11.1), (-s * ang, 0, 0), ROOF)
box("ridge", (bx1 - bx0 + 1.6, 0.5, 0.35), ((bx0 + bx1) / 2, 0, 13.3), mat=GOLD)
box("cupola", (2.2, 2.2, 1.8), (9.0, 0, 14.0), mat=RED, bevel=0.05)
cyl("cupola_roof", 1.8, 0.05, 1.6, (9.0, 0, 15.7), (0, 0, math.pi / 4), ROOF, 4)
sphere("cupola_ball", 0.2, (9.0, 0, 16.6), GOLD)
# door frame beams and sign
box("frameL", (0.3, 0.4, 8.6), (bx0 - 0.05, -5.6, 4.3), mat=RED)
box("frameR", (0.3, 0.4, 8.6), (bx0 - 0.05, 5.6, 4.3), mat=RED)
box("frameT", (0.3, 11.6, 0.4), (bx0 - 0.05, 0, 8.6), mat=RED)
box("sign", (0.12, 7.0, 1.4), (bx0 - 0.02, 0, 10.2), mat=RED, bevel=0.03)
box("sign_trim", (0.08, 7.3, 1.7), (bx0 + 0.03, 0, 10.2), mat=GOLD)
def door(name, hinge_y, sgn, theta):
    parts = []
    W, Hh = 5.4, 8.4
    for k in range(6):
        parts.append(box(f"{name}_pl{k}", (0.12, W / 6 - 0.02, Hh), (0, sgn * (W / 6 * (k + 0.5)), Hh / 2), mat=REDZ))
    for zc in (0.25, Hh / 2, Hh - 0.25):
        parts.append(box(f"{name}_rail", (0.06, W, 0.3), (-0.08, sgn * W / 2, zc), mat=CREAMPAINT))
    parts.append(box(f"{name}_sL", (0.06, 0.3, Hh), (-0.08, sgn * 0.15, Hh / 2), mat=CREAMPAINT))
    parts.append(box(f"{name}_sR", (0.06, 0.3, Hh), (-0.08, sgn * (W - 0.15), Hh / 2), mat=CREAMPAINT))
    for (z0, z1) in ((0.25, Hh / 2), (Hh / 2, Hh - 0.25)):
        a = Vector((-0.09, sgn * 0.15, z0)); b = Vector((-0.09, sgn * (W - 0.15), z1))
        parts.append(cyl_between(f"{name}_x", a, b, 0.11, mat=CREAMPAINT, seg=4))
        a = Vector((-0.09, sgn * 0.15, z1)); b = Vector((-0.09, sgn * (W - 0.15), z0))
        parts.append(cyl_between(f"{name}_x", a, b, 0.11, mat=CREAMPAINT, seg=4))
    for zc in (1.2, Hh - 1.2):
        parts.append(box(f"{name}_hinge", (0.05, 1.4, 0.18), (-0.1, sgn * 0.7, zc), mat=IRON))
    ob = join(name, parts, (0, 0, 0))
    ob.location = (bx0 - 0.15, hinge_y, 0.0)
    ob.rotation_euler = (0, 0, sgn * theta)
    return ob
door("doorL", -5.5, 1, math.radians(112))
door("doorR", 5.5, -1, math.radians(112))
pl = bpy.data.lights.new("barn_glow", 'POINT'); pl.energy = 1200; pl.color = (1.0, 0.7, 0.4); pl.shadow_soft_size = 2.0
plo = bpy.data.objects.new("barn_glow", pl); link(plo); plo.location = (12, 0, 6.5)

# ------------------------------------------------------------------ rig root
rigc = new_coll("rig"); set_coll(rigc)
ROOT = empty("rig_root")
rig_objs = []

# ------------------------------------------------------------------ wheels
R_WHEEL = 1.1
def wheel(name, center, nsp=14):
    parts = []
    parts.append(tube(name + "_tire", R_WHEEL - 0.055, R_WHEEL, 0.14, mat=IRON, seg=72))
    parts.append(tube(name + "_felloe", R_WHEEL - 0.2, R_WHEEL - 0.05, 0.11, mat=WHEELWOOD, seg=72))
    hub_prof = [(0.07, -0.34), (0.13, -0.33), (0.17, -0.26), (0.2, -0.12), (0.21, 0.0), (0.2, 0.12), (0.17, 0.26), (0.13, 0.33), (0.07, 0.35)]
    parts.append(lathe(name + "_hub", hub_prof, mat=BRASS, axis='Y', seg=32))
    parts.append(tube(name + "_hubband", 0.205, 0.235, 0.06, mat=BRASS, seg=32))
    parts.append(cyl(name + "_cap", 0.09, 0.05, 0.08, (0, 0.38, 0), mat=BRASS, axis='Y', seg=20))
    parts.append(cyl(name + "_capi", 0.09, 0.05, 0.08, (0, -0.38, 0), (math.pi, 0, 0), BRASS, axis='Y', seg=20))
    for i in range(nsp):
        a = 2 * math.pi * i / nsp
        d = Vector((math.cos(a), 0, math.sin(a)))
        parts.append(cyl_between(f"{name}_sp{i}", d * 0.19, d * (R_WHEEL - 0.17), 0.04, 0.03, WHEELWOOD, 10))
    for i in range(nsp):
        a = 2 * math.pi * (i + 0.5) / nsp
        parts.append(sphere(f"{name}_bolt{i}", 0.022, (math.cos(a) * (R_WHEEL - 0.03), 0.075, math.sin(a) * (R_WHEEL - 0.03)), BRASS, 8))
    ob = join(name, parts, (0, 0, 0))
    ob.location = center
    return ob
WHEELS = []
for nm, x in (("wheelF", -1.5), ("wheelR", 1.6)):
    for side, y in (("L", -1.45), ("R", 1.45)):
        w = wheel(f"{nm}{side}", (x, y, R_WHEEL))
        if side == "R":
            w.rotation_euler = (0, 0, math.pi)
        WHEELS.append(w)

# ------------------------------------------------------------------ wagon body
P = []
FLOOR_Z = 1.51
P.append(box("bed_floor", (5.0, 2.2, 0.12), (0, 0, FLOOR_Z - 0.06), mat=OAK))
for y in (-0.8, 0.8):
    P.append(box("sill", (5.2, 0.16, 0.2), (0, y, FLOOR_Z - 0.22), mat=RED))
for x in (-1.5, 1.6):
    P.append(box("bolster", (0.24, 2.5, 0.18), (x, 0, R_WHEEL + 0.12), mat=RED, bevel=0.02))
    P.append(cyl("axle", 0.065, 0.065, 3.3, (x, 0, R_WHEEL), mat=IRON, axis='Y', seg=16))
    P.append(box("spring", (1.0, 0.12, 0.1), (x, -0.8, R_WHEEL + 0.25), mat=IRON, bevel=0.02))
    P.append(box("spring", (1.0, 0.12, 0.1), (x, 0.8, R_WHEEL + 0.25), mat=IRON, bevel=0.02))
P.append(box("reach", (3.2, 0.14, 0.14), (0.05, 0, R_WHEEL + 0.05), mat=RED))
# side walls: 3 planks + gold trim + posts
for s in (-1, 1):
    for k in range(3):
        P.append(box("plank", (5.0, 0.06, 0.18), (0, s * 1.13, FLOOR_Z + 0.1 + k * 0.2), mat=RED, bevel=0.008))
    P.append(box("trim_top", (5.06, 0.11, 0.06), (0, s * 1.13, FLOOR_Z + 0.63), mat=GOLD, bevel=0.01))
    P.append(box("pinstripe", (5.0, 0.068, 0.025), (0, s * 1.13, FLOOR_Z + 0.2), mat=GOLD))
    for x in (-2.45, -1.2, 0.05, 1.3, 2.45):
        P.append(box("post", (0.1, 0.1, 0.7), (x, s * 1.15, FLOOR_Z + 0.3), mat=RED, bevel=0.01))
        P.append(sphere("knob", 0.07, (x, s * 1.15, FLOOR_Z + 0.72), BRASS, 12))
for k in range(3):
    P.append(box("tail_plank", (0.06, 2.2, 0.18), (2.47, 0, FLOOR_Z + 0.1 + k * 0.2), mat=RED, bevel=0.008))
P.append(box("tail_trim", (0.1, 2.32, 0.06), (2.47, 0, FLOOR_Z + 0.63), mat=GOLD))
# driver's bench + dash + footboard
P.append(box("seat_box", (0.6, 2.1, 0.8), (-2.05, 0, FLOOR_Z + 0.4), mat=RED, bevel=0.02))
P.append(box("seat_trim", (0.62, 2.12, 0.05), (-2.05, 0, FLOOR_Z + 0.55), mat=GOLD))
P.append(box("cushion", (0.58, 2.0, 0.1), (-2.05, 0, 2.35), mat=BLACKLEATHER, bevel=0.04))
P.append(box("backrest", (0.08, 2.1, 0.55), (-1.71, 0, 2.67), mat=RED, bevel=0.02))
P.append(box("back_trim", (0.1, 2.14, 0.05), (-1.71, 0, 2.95), mat=GOLD))
P.append(box("footboard", (0.62, 2.1, 0.06), (-2.66, 0, 1.84), mat=OAK))
P.append(box("dash", (0.07, 2.2, 0.75), (-2.98, 0, 1.92), (0, math.radians(-12), 0), RED, 0.01))
P.append(box("dash_trim", (0.09, 2.24, 0.05), (-3.05, 0, 2.29), (0, math.radians(-12), 0), GOLD))
for s in (-1, 1):
    P.append(box("dash_side", (0.5, 0.06, 0.6), (-2.72, s * 1.07, 1.75), mat=RED))
P.append(box("under_dash", (0.5, 1.6, 0.25), (-2.72, 0, 1.68), mat=RED))
# bell on gooseneck post
bx, by = -2.88, -0.95
P.append(cyl_between("bellpost", (bx + 0.1, by, 1.85), (bx, by, 3.15), 0.035, mat=BRASS))
P.append(cyl_between("bellarm", (bx, by, 3.15), (bx - 0.35, by, 3.15), 0.03, mat=BRASS))
bell_prof = [(0.0001, 0.42), (0.07, 0.41), (0.12, 0.35), (0.14, 0.2), (0.17, 0.08), (0.23, 0.0), (0.22, -0.015)]
P.append(lathe("bell", bell_prof, (bx - 0.35, by, 2.62), mat=BRASS, seg=40))
P.append(sphere("clapper", 0.05, (bx - 0.35, by, 2.6), IRON, 10))
P.append(cyl("bellyoke", 0.04, 0.04, 0.12, (bx - 0.35, by, 3.08), mat=BRASS))
# lanterns
for s in (-1, 1):
    lx, ly = -3.0, s * 1.08
    P.append(cyl("lamp_base", 0.09, 0.11, 0.08, (lx, ly, 2.33), mat=BRASS, seg=16))
    P.append(cyl("lamp_glass", 0.09, 0.09, 0.22, (lx, ly, 2.48), mat=GLASS, seg=16))
    P.append(cyl("lamp_cap", 0.11, 0.02, 0.14, (lx, ly, 2.66), mat=BRASS, seg=16))
    P.append(cyl_between("lamp_arm", (lx, ly, 2.3), (-2.95, ly, 2.0), 0.02, mat=BRASS))
# oak water barrels with brass hoops (on bed, rear)
barrel_prof = [(0.33, 0.0), (0.37, 0.15), (0.4, 0.5), (0.37, 0.85), (0.33, 1.0)]
def barrel_r(z):
    return 0.33 + 0.07 * math.sin(math.pi * z)
for y in (-0.55, 0.55):
    P.append(lathe("barrel", barrel_prof, (1.95, y, FLOOR_Z), mat=OAK, seg=28))
    P.append(cyl("barrel_lid", 0.33, 0.33, 0.02, (1.95, y, FLOOR_Z + 1.0), mat=OAK, seg=28))
    for z in (0.08, 0.3, 0.7, 0.92):
        P.append(tube("hoop", barrel_r(z) - 0.005, barrel_r(z) + 0.018, 0.045, (1.95, y, FLOOR_Z + z), mat=BRASS, seg=28, axis='Z'))
    P.append(cyl("spigot", 0.03, 0.03, 0.18, (1.95 - 0.42, y, FLOOR_Z + 0.2), mat=BRASS, axis='X', seg=10))
# hose reel at rear
P.append(box("reel_step", (0.9, 2.3, 0.08), (2.95, 0, FLOOR_Z - 0.3), mat=OAK))
for s in (-1, 1):
    P.append(box("reel_bracket", (0.9, 0.08, 0.7), (2.85, s * 1.0, FLOOR_Z + 0.05), (0, math.radians(-20), 0), RED))
    P.append(cyl("reel_flange", 0.58, 0.58, 0.05, (3.1, s * 0.86, FLOOR_Z + 0.35), mat=BRASS, axis='Y', seg=40))
P.append(cyl("reel_drum", 0.3, 0.3, 1.7, (3.1, 0, FLOOR_Z + 0.35), mat=RED, axis='Y', seg=32))
for k in range(8):
    yy = -0.72 + k * 0.205
    P.append(torus("hose_wrap", 0.4, 0.1, (3.1, yy, FLOOR_Z + 0.35), mat=CANVAS, axis='Y', seg=40, rseg=10))
P.append(sphere("nozzle_tip", 0.05, (3.1, 0.75, FLOOR_Z + 0.85), BRASS))
# flat coiled hose on bed front corner + one hanging coil
for k in range(3):
    P.append(torus("coil", 0.32 + k * 0.09, 0.045, (-1.25, -0.6, FLOOR_Z + 0.05 + k * 0.01), mat=CANVAS, seg=36, rseg=8))
P.append(cyl("coil_nozzle", 0.04, 0.02, 0.35, (-1.25, -0.2, FLOOR_Z + 0.08), (math.pi / 2, 0, 0.3), BRASS, seg=12))
# tongue + hounds
TONGUE_TIP = Vector((-13.75, 0, 1.12))
P.append(cyl_between("tongue", (-1.5, 0, 1.0), TONGUE_TIP, 0.075, 0.06, OAK, 12))
for s in (-1, 1):
    P.append(cyl_between("hound", (-1.5, s * 0.8, 1.05), (-3.3, 0, 1.02), 0.045, mat=OAK))
P.append(cyl("tongue_ring", 0.08, 0.08, 0.12, TONGUE_TIP, mat=BRASS, axis='X'))
WAGON = join("wagon_body", P, (0, 0, 0))

# ------------------------------------------------------------------ animal proxies
def leg(parts, nm, hip, foot, r, mat, knee_fwd=0.0):
    hip, foot = Vector(hip), Vector(foot)
    mid = (hip + foot) / 2 + Vector((knee_fwd, 0, 0))
    parts.append(cyl_between(nm + "u", hip, mid, r * 1.35, r, mat, 12))
    parts.append(sphere(nm + "k", r * 1.05, mid, mat, 10))
    parts.append(cyl_between(nm + "l", mid, foot + Vector((0, 0, 0.1)), r, r * 0.85, mat, 12))
    parts.append(cyl(nm + "h", r * 0.95, r * 1.12, 0.12, foot + Vector((0, 0, 0.06)), (0, 0, 0), HOOF, 12))

GALLOP = [(-0.55, 0.42, -0.28), (0.1, 0.0, 0.0), (-0.25, 0.0, 0.0), (0.45, 0.18, 0.18)]
TROT = [(-0.35, 0.25, -0.18), (0.2, 0.0, 0.0), (-0.25, 0.0, 0.0), (0.35, 0.2, 0.15)]
STAND = [(0, 0, 0)] * 4

def quad(name, x, y, gz, A, pose=GALLOP, mirror=False):
    L, RY, RZ, H = A['L'], A['RY'], A['RZ'], A['H']
    bc = gz + H - RZ
    parts = []
    m = A['mat']
    parts.append(ellipsoid(name + "_body", (L / 2, RY, RZ), (x, y, bc), (0, A.get('pitch', 0), 0), m, 28))
    hipz = bc - RZ * 0.15
    legpos = [(x - L * 0.32, y - RY * 0.55), (x - L * 0.32, y + RY * 0.55), (x + L * 0.32, y - RY * 0.55), (x + L * 0.32, y + RY * 0.55)]
    pz = list(pose)
    if mirror:
        pz = [pz[1], pz[0], pz[3], pz[2]]
    for i, ((lx, ly), (dx, lift, kf)) in enumerate(zip(legpos, pz)):
        hipx = lx
        foot = (lx + dx * (H / 1.6), ly, gz + lift * (H / 1.6))
        leg(parts, f"{name}_leg{i}", (hipx, ly, hipz + (0.15 * RZ if i < 2 else 0)), foot, A['leg_r'] * (1.0 if i < 2 else 1.08), m, kf)
    nb = Vector((x - L * 0.4, y, bc + RZ * 0.45))
    if A.get('camel'):
        mid = nb + Vector((-A['neck_len'] * 0.55, 0, -0.15))
        end = mid + Vector((-0.25, 0, A['neck_len'] * 0.55))
        parts.append(cyl_between(name + "_neck1", nb, mid, A['neck_r'], A['neck_r'] * 0.85, m, 14))
        parts.append(sphere(name + "_neckj", A['neck_r'] * 0.86, mid, m, 12))
        parts.append(cyl_between(name + "_neck2", mid, end, A['neck_r'] * 0.85, A['neck_r'] * 0.7, m, 14))
    else:
        a = math.radians(A['neck_ang'])
        end = nb + Vector((-math.cos(a), 0, math.sin(a))) * A['neck_len']
        parts.append(cyl_between(name + "_neck", nb, end, A['neck_r'], A['neck_r'] * 0.72, m, 14))
    ha = math.radians(A['head_ang'])
    hd = Vector((-math.cos(ha), 0, -math.sin(ha)))
    hl, hr = A['head_len'], A['head_r']
    hc = end + hd * hl * 0.25 + Vector((0, 0, hr * 0.3))
    parts.append(ellipsoid(name + "_head", (hl * 0.42, hr, hr * 1.05), hc, (0, -ha, 0), m, 20))
    muz = hc + hd * hl * 0.38
    parts.append(ellipsoid(name + "_muzzle", (hl * 0.3, hr * 0.82, hr * 0.8), muz, (0, -ha, 0), A.get('muzzle_mat', m), 18))
    for s in (-1, 1):
        parts.append(sphere(name + "_eye", hr * 0.2, hc + hd * hl * 0.05 + Vector((0, s * hr * 0.86, hr * 0.38)), EYE, 10))
        parts.append(sphere(name + "_nostril", hr * 0.1, muz + hd * hl * 0.27 + Vector((0, s * hr * 0.35, 0.0)), NOSE, 8))
        ebase = hc - hd * hl * 0.2 + Vector((0, s * hr * 0.6, hr * 0.85))
        el = A['ear']
        ear = cyl(name + "_ear", hr * 0.28, 0.01, el, ebase + Vector((0, s * el * 0.25, el * 0.45)), (s * -0.5, 0, 0), m, 10)
        ear.scale = (0.6, 1, 1)
        parts.append(ear)
        if A.get('horns'):
            parts.append(cyl_between(name + "_horn", ebase + Vector((0.05, 0, -0.05)), ebase + Vector((-0.08, s * 0.22, 0.12)), 0.035, 0.012, CREAM, 8))
        if A.get('ossicones'):
            ob = ebase + Vector((0.04, -s * hr * 0.25, 0.0))
            parts.append(cyl_between(name + "_oss", ob, ob + Vector((0, 0, 0.22)), 0.035, 0.03, m, 10))
            parts.append(sphere(name + "_ossk", 0.05, ob + Vector((0, 0, 0.24)), GIRAFFE_DARK, 10))
    if A.get('mane'):
        parts.append(cyl_between(name + "_mane", nb + Vector((0.05, 0, A['neck_r'] * 0.8)), end + Vector((0.08, 0, hr * 0.9)), A['neck_r'] * 0.45, A['neck_r'] * 0.3, A['mane'], 10))
    if A.get('hump'):
        parts.append(ellipsoid(name + "_hump", (L * 0.2, RY * 0.72, 0.45), (x + 0.05, y, bc + RZ * 0.75), (0, 0, 0), m, 20))
    tb = Vector((x + L * 0.49, y, bc + RZ * 0.35))
    tl = A.get('tail', 0.6)
    parts.append(cyl_between(name + "_tail", tb, tb + Vector((0.35, 0, -tl)), 0.045, 0.03, m, 8))
    parts.append(ellipsoid(name + "_tuft", (0.07, 0.07, 0.15), tb + Vector((0.37, 0, -tl - 0.08)), (0, 0.3, 0), A.get('mane', m), 10))
    ob = join(name, parts, (x, y, gz))
    pts = dict(bc=bc, collar=nb, back=Vector((x - L * 0.05, y, bc + RZ)), bit=muz, head=hc, hd=hd)
    return ob, pts

HORSE = dict(L=2.1, RY=0.37, RZ=0.42, H=1.62, leg_r=0.065, neck_len=0.95, neck_ang=52, neck_r=0.21, head_len=0.62, head_r=0.16,
             head_ang=55, ear=0.18, mane=MANE, tail=0.7)
CAMELA = dict(L=2.3, RY=0.4, RZ=0.45, H=1.9, leg_r=0.07, neck_len=1.1, neck_r=0.15, head_len=0.6, head_r=0.15, head_ang=10,
              ear=0.1, camel=True, hump=True, mat=CAMEL, tail=0.5)
COWA = dict(L=2.15, RY=0.46, RZ=0.5, H=1.42, leg_r=0.075, neck_len=0.45, neck_ang=22, neck_r=0.26, head_len=0.55, head_r=0.2,
            head_ang=40, ear=0.14, horns=True, mat=COW, muzzle_mat=PINK, tail=0.75)
GIRA = dict(L=2.0, RY=0.32, RZ=0.45, H=2.35, leg_r=0.06, neck_len=2.8, neck_ang=74, neck_r=0.17, head_len=0.6, head_r=0.14,
            head_ang=25, ear=0.14, ossicones=True, mat=GIRAFFE, mane=GIRAFFE_DARK, tail=0.9)

TEAM = {}
PAIRS = [("cow", -5.0, COWA), ("camel", -8.85, CAMELA), ("horse", -12.75, HORSE)]
for nm, x, A in PAIRS:
    for side, y in (("L", -0.78), ("R", 0.78)):
        AA = dict(A)
        if nm == "horse":
            AA['mat'] = HORSE1 if side == "L" else HORSE2
        ob, pts = quad(f"{nm}{side}", x + (0.12 if side == "R" else 0), y, 0.0, AA, GALLOP, mirror=(side == "R"))
        TEAM[(nm, side)] = (ob, pts, AA, x + (0.12 if side == "R" else 0), y)

GIRAFFES = []
for side, y in (("L", -0.5), ("R", 0.5)):
    ob, pts = quad(f"giraffe{side}", 0.5 if side == "L" else -0.2, y, FLOOR_Z, GIRA, STAND)
    GIRAFFES.append(ob)

# elephants
def elephant(name, x, y, mirror=False):
    parts = []
    bc = 2.15
    parts.append(ellipsoid(name + "_body", (1.75, 0.95, 1.05), (x, y, bc), (0, 0, 0), ELE, 32))
    pose = TROT if not mirror else [TROT[1], TROT[0], TROT[3], TROT[2]]
    lp = [(x - 1.05, y - 0.5), (x - 1.05, y + 0.5), (x + 1.05, y - 0.5), (x + 1.05, y + 0.5)]
    for i, ((lx, ly), (dx, lift, kf)) in enumerate(zip(lp, pose)):
        hip = Vector((lx, ly, bc - 0.3)); foot = Vector((lx + dx * 1.2, ly, lift * 1.1))
        mid = (hip + foot) / 2 + Vector((kf, 0, 0))
        parts.append(cyl_between(name + "_lu", hip, mid, 0.36, 0.31, ELE, 16))
        parts.append(sphere(name + "_lk", 0.31, mid, ELE, 14))
        parts.append(cyl_between(name + "_ll", mid, foot + Vector((0, 0, 0.12)), 0.31, 0.32, ELE, 16))
        parts.append(cyl(name + "_foot", 0.33, 0.34, 0.14, foot + Vector((0, 0, 0.07)), (0, 0, 0), CREAM, 16))
    hc = Vector((x - 2.0, y, 2.75))
    parts.append(sphere(name + "_head", 0.78, hc, ELE, 28))
    tr = [hc + Vector((-0.55, 0, -0.25)), Vector((x - 2.85, y, 1.8)), Vector((x - 2.95, y, 1.2)), Vector((x - 3.0, y, 0.75)),
          Vector((x - 3.25, y, 0.5)), Vector((x - 3.5, y, 0.6)), Vector((x - 3.6, y, 0.8))]
    rr = [0.3, 0.24, 0.19, 0.15, 0.12, 0.1, 0.08]
    for i in range(len(tr) - 1):
        parts.append(cyl_between(name + "_trunk", tr[i], tr[i + 1], rr[i], rr[i + 1], ELE, 14))
        parts.append(sphere(name + "_tj", rr[i + 1], tr[i + 1], ELE, 12))
    for s in (-1, 1):
        parts.append(cyl_between(name + "_tusk", hc + Vector((-0.6, s * 0.32, -0.45)), hc + Vector((-1.0, s * 0.36, -0.95)), 0.08, 0.03, CREAM, 10))
        ear = ellipsoid(name + "_ear", (0.1, 0.72, 0.85), hc + Vector((0.25, s * 0.85, 0.0)), (0, 0, s * -0.55), ELE, 20)
        parts.append(ear)
        parts.append(sphere(name + "_eye", 0.08, hc + Vector((-0.55, s * 0.5, 0.18)), EYE, 10))
        # barrel on each side
        bx_ = x - 0.05; by_ = y + s * 1.4
        parts.append(lathe(name + "_barrel", [(0.36, -0.6), (0.41, -0.35), (0.44, 0.0), (0.41, 0.35), (0.36, 0.6)], (bx_, by_, bc + 0.05), mat=OAK, axis='X', seg=28))
        for zz in (-0.5, -0.2, 0.2, 0.5):
            rr_ = 0.36 + 0.08 * math.cos(math.pi * zz / 1.2)
            parts.append(tube(name + "_hoop", rr_ - 0.005, rr_ + 0.02, 0.05, (bx_ + zz, by_, bc + 0.05), mat=BRASS, axis='X', seg=28))
        parts.append(cyl(name + "_nozzle", 0.05, 0.03, 0.3, (bx_ - 0.75, by_, bc + 0.05), mat=BRASS, axis='X', seg=12))
        parts.append(box(name + "_strap", (0.12, 0.06, 0.95), (bx_ + 0.3, y + s * 1.05, bc + 0.55), (s * -0.35, 0, 0), LEATHER))
        parts.append(box(name + "_strap", (0.12, 0.06, 0.95), (bx_ - 0.4, y + s * 1.05, bc + 0.55), (s * -0.35, 0, 0), LEATHER))
    parts.append(ellipsoid(name + "_band", (0.85, 0.99, 1.09), (x, y, bc), (0, 0, 0), BLANKET, 32))
    parts.append(cyl_between(name + "_tail", Vector((x + 1.7, y, bc + 0.3)), Vector((x + 1.95, y, bc - 0.6)), 0.06, 0.04, ELE, 8))
    return join(name, parts, (x, y, 0))
ELEPHANTS = [elephant("elephant1", -8.2, -3.75), elephant("elephant2", 5.6, -3.75, mirror=True)]

# bear + dog on the bench
def bear(x, y):
    p = []
    seat = 2.4
    p.append(ellipsoid("b_body", (0.45, 0.55, 0.62), (x, y, seat + 0.55), (0, 0.1, 0), BEAR, 28))
    p.append(ellipsoid("b_belly", (0.2, 0.4, 0.45), (x - 0.3, y, seat + 0.5), (0, 0.1, 0), BEARLIGHT, 20))
    hc = Vector((x - 0.1, y, seat + 1.42))
    p.append(sphere("b_head", 0.36, hc, BEAR, 28))
    p.append(ellipsoid("b_muzzle", (0.16, 0.15, 0.12), hc + Vector((-0.32, 0, -0.08)), (0, 0, 0), BEARLIGHT, 16))
    p.append(sphere("b_nose", 0.06, hc + Vector((-0.47, 0, -0.03)), NOSE, 10))
    for s in (-1, 1):
        p.append(sphere("b_ear", 0.11, hc + Vector((0.02, s * 0.26, 0.28)), BEAR, 12))
        p.append(sphere("b_eye", 0.045, hc + Vector((-0.3, s * 0.13, 0.1)), EYE, 10))
        sh = Vector((x - 0.05, y + s * 0.45, seat + 0.95))
        hand = Vector((x - 0.58, y + s * 0.2, seat + 0.62))
        p.append(cyl_between("b_arm", sh, hand, 0.14, 0.12, BEAR, 14))
        p.append(sphere("b_paw", 0.13, hand, BEAR, 14))
        hip = Vector((x - 0.05, y + s * 0.3, seat + 0.18)); knee = Vector((x - 0.6, y + s * 0.32, seat + 0.15))
        foot = Vector((x - 0.75, y + s * 0.32, 1.9))
        p.append(cyl_between("b_thigh", hip, knee, 0.2, 0.17, BEAR, 14))
        p.append(sphere("b_knee", 0.17, knee, BEAR, 12))
        p.append(cyl_between("b_shin", knee, foot + Vector((0, 0, 0.08)), 0.15, 0.13, BEAR, 14))
        p.append(ellipsoid("b_foot", (0.17, 0.11, 0.08), foot + Vector((-0.05, 0, 0.0)), (0, 0, 0), BEAR, 12))
    p.append(ellipsoid("b_helmet", (0.33, 0.31, 0.2), hc + Vector((0.03, 0, 0.26)), (0, 0, 0), HELMET, 24))
    p.append(ellipsoid("b_brim", (0.5, 0.4, 0.03), hc + Vector((0.12, 0, 0.17)), (0, 0.12, 0), HELMET, 24))
    p.append(box("b_badge", (0.04, 0.16, 0.18), hc + Vector((-0.3, 0, 0.32)), (0, 0.4, 0), BRASS, 0.01))
    return join("bear", p, (x, y, seat)), [Vector((x - 0.6, y - 0.2, seat + 0.65)), Vector((x - 0.6, y + 0.2, seat + 0.65))]
BEAR_OB, HANDS = bear(-2.15, -0.45)

def dog(x, y):
    p = []
    seat = 2.4
    p.append(ellipsoid("d_haunch", (0.28, 0.22, 0.17), (x + 0.05, y, seat + 0.15), (0, 0, 0), DOG, 20))
    p.append(ellipsoid("d_torso", (0.2, 0.18, 0.42), (x - 0.02, y, seat + 0.5), (0, -0.25, 0), DOG, 20))
    p.append(cyl_between("d_neck", (x - 0.1, y, seat + 0.78), (x - 0.18, y, seat + 1.05), 0.09, 0.075, DOG, 12))
    hc = Vector((x - 0.22, y, seat + 1.12))
    p.append(ellipsoid("d_head", (0.17, 0.13, 0.13), hc, (0, 0, 0), DOG, 18))
    p.append(ellipsoid("d_snout", (0.15, 0.07, 0.07), hc + Vector((-0.2, 0, -0.04)), (0, 0.1, 0), DOG, 14))
    p.append(sphere("d_nose", 0.035, hc + Vector((-0.35, 0, -0.03)), NOSE, 10))
    for s in (-1, 1):
        p.append(ellipsoid("d_ear", (0.06, 0.03, 0.16), hc + Vector((0.04, s * 0.14, -0.06)), (s * 0.25, 0, 0), DOGDARK, 12))
        p.append(sphere("d_eye", 0.028, hc + Vector((-0.11, s * 0.08, 0.05)), EYE, 8))
        p.append(cyl_between("d_fleg", (x - 0.12, y + s * 0.08, seat + 0.45), (x - 0.25, y + s * 0.08, seat + 0.04), 0.045, 0.04, DOG, 10))
        p.append(ellipsoid("d_paw", (0.07, 0.045, 0.035), (x - 0.28, y + s * 0.08, seat + 0.03), (0, 0, 0), DOG, 10))
        p.append(cyl_between("d_hleg", (x - 0.05, y + s * 0.16, seat + 0.1), (x - 0.4, y + s * 0.16, seat + 0.06), 0.05, 0.04, DOG, 10))
        p.append(cyl_between("d_hleg2", (x - 0.4, y + s * 0.16, seat + 0.06), (x - 0.55, y + s * 0.16, 1.9), 0.04, 0.035, DOG, 10))
    p.append(cyl_between("d_tail", (x + 0.3, y, seat + 0.12), (x + 0.55, y + 0.1, seat + 0.35), 0.035, 0.02, DOG, 8))
    p.append(ellipsoid("d_helmet", (0.17, 0.15, 0.1), hc + Vector((0.03, 0, 0.12)), (0, 0, 0), HELMET, 18))
    p.append(ellipsoid("d_brim", (0.26, 0.2, 0.02), hc + Vector((0.08, 0, 0.07)), (0, 0.12, 0), HELMET, 18))
    return join("dog", p, (x, y, seat))
DOG_OB = dog(-2.1, 0.55)

# ------------------------------------------------------------------ harness
H = []
for (nm, side), (ob, pts, A, ax, ay) in TEAM.items():
    L, RY, RZ = A['L'], A['RY'], A['RZ']
    bc = pts['bc']
    H.append(ellipsoid(f"collar_{nm}{side}", (0.1, RY * 0.8, RZ * 0.85), pts['collar'] + Vector((0.05, 0, -0.05)), (0, 0.5, 0), LEATHER, 20))
    H.append(ellipsoid(f"girth_{nm}{side}", (0.06, RY * 1.05, RZ * 1.05), (ax - L * 0.1, ay, bc), (0, 0, 0), LEATHER, 24))
    H.append(ellipsoid(f"breech_{nm}{side}", (0.05, RY * 1.04, RZ * 0.8), (ax + L * 0.3, ay, bc - RZ * 0.05), (0, 0.6, 0), LEATHER, 20))
    H.append(ellipsoid(f"bridle_{nm}{side}", (0.03, A['head_r'] * 0.9, A['head_r'] * 0.88), pts['bit'] - pts['hd'] * 0.05, (0, 0.4, 0), LEATHER, 16))
    xe = ax + L / 2 + 0.45
    for s in (-1, 1):
        a = (ax - L * 0.37, ay + s * RY * 0.82, bc + RZ * 0.12)
        m = (ax, ay + s * RY * 1.09, bc - RZ * 0.25)
        e = (xe, ay + s * 0.36, 0.98)
        poly_curve(f"trace_{nm}{side}{s}", [a, m, e], 0.024, BLACKLEATHER)
        H.append(sphere("buckle", 0.04, a, BRASS, 10))
    H.append(cyl("singletree", 0.04, 0.04, 0.8, (xe, ay, 0.98), mat=OAK, axis='Y', seg=10))
    H.append(cyl("singletree_tip", 0.045, 0.045, 0.06, (xe, ay - 0.4, 0.98), mat=IRON, axis='Y', seg=10))
    H.append(cyl("singletree_tip", 0.045, 0.045, 0.06, (xe, ay + 0.4, 0.98), mat=IRON, axis='Y', seg=10))
for nm, x, A in PAIRS:
    xe = x + 0.06 + A['L'] / 2 + 0.45
    # tongue height at xe
    t = (xe - (-1.5)) / (TONGUE_TIP.x + 1.5)
    tz = 1.0 + t * (TONGUE_TIP.z - 1.0)
    H.append(box("evener", (0.08, 1.75, 0.08), (xe + 0.12, 0, 0.98), mat=OAK, bevel=0.01))
    for s in (-0.78, 0.78):
        H.append(cyl_between("link", (xe + 0.12, s, 0.98), (xe, s, 0.98), 0.02, mat=IRON))
    H.append(cyl_between("clevis", (xe + 0.12, 0, 0.98), (xe + 0.12, 0, tz), 0.03, mat=IRON))
# neck yoke for horses
hx = TEAM[("horse", "L")][1]['collar']
H.append(cyl("neckyoke", 0.05, 0.05, 1.7, (TONGUE_TIP.x, 0, TONGUE_TIP.z + 0.05), mat=OAK, axis='Y', seg=12))
for side in ("L", "R"):
    c = TEAM[("horse", side)][1]['collar']
    H.append(cyl_between("yoke_strap", (TONGUE_TIP.x, c.y, TONGUE_TIP.z + 0.05), c + Vector((0.05, 0, -0.35)), 0.025, mat=BLACKLEATHER))
HARNESS = join("harness", H, (0, 0, 0))
# reins: bear hands -> terrets on cow, camel, horse backs -> horse bit
for side, hand in (("L", HANDS[0]), ("R", HANDS[1])):
    pts = [hand]
    for nm in ("cow", "camel", "horse"):
        ob, pp, A, ax, ay = TEAM[(nm, side)]
        top = pp['back'] + Vector((0, 0, 0.06))
        if nm == "camel":
            top = Vector((ax - 0.75, ay, pp['bc'] + A['RZ'] + 0.12))
        pts.append(top)
    bit = TEAM[("horse", side)][1]['bit']
    pts.append(bit)
    full = []
    for i in range(len(pts) - 1):
        seg = sag_points(pts[i], pts[i + 1], 0.12 if i == 0 else 0.06, 8)
        full.extend(seg if i == 0 else seg[1:])
    poly_curve(f"rein{side}", full, 0.013, BLACKLEATHER)

# parent everything in the rig collection to the root
for ob in list(rigc.objects):
    if ob is not ROOT:
        parent_keep(ob, ROOT)

# ------------------------------------------------------------------ dust puffs (B12 only)
dust = new_coll("dust"); set_coll(dust)
dm = bpy.data.materials.new("dust_vol")
try:
    dm.use_nodes = True
except Exception:
    pass
N, Lk = dm.node_tree.nodes, dm.node_tree.links
for n in list(N):
    if n.type == 'BSDF_PRINCIPLED':
        N.remove(n)
out = [n for n in N if n.type == 'OUTPUT_MATERIAL'][0]
tc = N.new('ShaderNodeTexCoord'); vl = N.new('ShaderNodeVectorMath'); vl.operation = 'LENGTH'
Lk.new(tc.outputs['Object'], vl.inputs[0])
mr = N.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 1.0; mr.inputs['From Max'].default_value = 0.2
Lk.new(vl.outputs['Value'], mr.inputs['Value'])
nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.5; nz.inputs['Detail'].default_value = 3
Lk.new(tc.outputs['Object'], nz.inputs['Vector'])
mul = N.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
Lk.new(mr.outputs['Result'], mul.inputs[0]); Lk.new(nz.outputs['Fac'], mul.inputs[1])
mul2 = N.new('ShaderNodeMath'); mul2.operation = 'MULTIPLY'; mul2.inputs[1].default_value = 1.6
Lk.new(mul.outputs[0], mul2.inputs[0])
pv = N.new('ShaderNodeVolumePrincipled'); pv.inputs['Color'].default_value = (0.9, 0.62, 0.4, 1)
Lk.new(mul2.outputs[0], pv.inputs['Density'])
Lk.new(pv.outputs[0], out.inputs['Volume'])
rnd = random.Random(7)
for i, (px, py, r) in enumerate([(2.8, -1.8, 1.6), (3.6, 1.6, 1.5), (-0.4, -2.2, 1.2), (-4.0, -1.6, 1.1), (-7.6, -1.5, 1.2),
                                  (-11.2, -1.3, 1.0), (6.5, -4.0, 1.8), (-2.5, -5.2, 1.3), (5.0, 0.0, 2.0)]):
    ob = ellipsoid(f"dust{i}", (1, 1, 1), (px, py, r * 0.55), mat=dm, seg=16)
    ob.scale = (r * 1.4, r, r * 0.7)

sc.cycles.volume_step_rate = 4.0
sc.cycles.volume_max_steps = 64
cam = camera()
look_at(cam, (-26, -16, 1.5), (-4, 0, 2.5), 28)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "wagon.blend"))
print("SAVED wagon.blend")
