"""blender -b -P build_train.py -> train.blend (circus steam train, track ending at a canyon gap, steel-plated ants)
Track runs +X; near rails end at x=-0.3 (rim x=0), far rails resume at x=28.3."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from common import _finish
from track import *
from track import h_train as H

sc = reset_scene()
setup_render(sc)
world_sky(0.55)
sun((-0.45, -0.7, 0.5), energy=6.5, angle_deg=8)

D = desert_mats()
RED = flat_mat("loco_red", (0.75, 0.04, 0.03), rough=0.28, coat=0.6)
GOLD = flat_mat("gold", (1.0, 0.7, 0.28), rough=0.2, metal=1.0)
BRASS = flat_mat("brass", (0.95, 0.66, 0.26), rough=0.14, metal=1.0)
STEEL = flat_mat("steel_polished", (0.75, 0.76, 0.78), rough=0.18, metal=1.0)
IRON = flat_mat("iron", (0.12, 0.12, 0.13), rough=0.45, metal=0.9)
BLACK = flat_mat("black_paint", (0.03, 0.03, 0.035), rough=0.3, coat=0.5)
GUNMETAL = flat_mat("gunmetal", (0.12, 0.12, 0.14), rough=0.3, metal=0.7)
COAL = ramp_mat("coal", 'noise', ((0.3, (0.01, 0.01, 0.01)), (0.7, (0.06, 0.06, 0.07))), rough=0.4, scale=18, bump=1.0)
LAMP = flat_mat("lamp", (1, 0.9, 0.6), rough=0.1, emit=(1, 0.8, 0.45), emit_str=4)
CREAM = flat_mat("cream", (0.96, 0.9, 0.75), rough=0.4)
TIE = wood_mat("tie_wood", (0.22, 0.14, 0.09), (0.42, 0.3, 0.2), 'X', rough=0.85, coat=0.0, bump=0.3)
RAIL = flat_mat("rail_steel", (0.5, 0.45, 0.42), rough=0.35, metal=1.0)
BALLAST = ramp_mat("ballast", 'voronoi_edge', ((0.0, (0.25, 0.18, 0.14)), (0.08, (0.55, 0.45, 0.38)), (1.0, (0.68, 0.58, 0.5))),
                   rough=0.9, scale=28, bump=0.8, bump_dist=0.02, haze=900)
STRIPES = {}
def stripe_mat(name, c1, c2):
    return ramp_mat(name, 'wave_x', ((0.0, c1), (0.5, c2)), rough=0.3, scale=0.26, constant=True, coat=0.5, detail=0)
CR, CY, CB = (0.78, 0.04, 0.03), (1.0, 0.72, 0.05), (0.03, 0.18, 0.75)

# ------------------------------------------------------------------ terrain + canyon
env = new_coll("env"); set_coll(env)
m, nt, b = nodes_mat("terrain")
N, L = nt.nodes, nt.links
# sand vs strata by height and slope
geo = N.new('ShaderNodeNewGeometry')
sep = N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Position'], sep.inputs[0])
sepn = N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Normal'], sepn.inputs[0])
f1 = N.new('ShaderNodeMapRange'); f1.inputs['From Min'].default_value = -0.4; f1.inputs['From Max'].default_value = -1.2
L.new(sep.outputs['Z'], f1.inputs['Value'])
f2 = N.new('ShaderNodeMapRange'); f2.inputs['From Min'].default_value = 0.85; f2.inputs['From Max'].default_value = 0.6
L.new(sepn.outputs['Z'], f2.inputs['Value'])
mx = N.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'
L.new(f1.outputs['Result'], mx.inputs[0]); L.new(f2.outputs['Result'], mx.inputs[1])
wave = N.new('ShaderNodeTexWave'); wave.wave_type = 'BANDS'; wave.bands_direction = 'Z'
wave.inputs['Scale'].default_value = 0.04; wave.inputs['Distortion'].default_value = 2.0; wave.inputs['Detail'].default_value = 4
tcn = N.new('ShaderNodeTexCoord'); L.new(tcn.outputs['Object'], wave.inputs['Vector'])
strata = (( 0.0, (0.5, 0.13, 0.05)), (0.18, (0.78, 0.3, 0.11)), (0.34, (0.95, 0.56, 0.3)), (0.5, (0.62, 0.19, 0.07)),
          (0.66, (0.96, 0.72, 0.46)), (0.82, (0.75, 0.27, 0.1)), (1.0, (0.45, 0.12, 0.05)))
crs = N.new('ShaderNodeValToRGB')
els = crs.color_ramp.elements
els[0].position, els[0].color = strata[0][0], (*strata[0][1], 1)
els[1].position, els[1].color = strata[-1][0], (*strata[-1][1], 1)
for p_, c_ in strata[1:-1]:
    e = els.new(p_); e.color = (*c_, 1)
L.new(wave.outputs['Fac'], crs.inputs['Fac'])
nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.35; nz.inputs['Detail'].default_value = 8
L.new(tcn.outputs['Object'], nz.inputs['Vector'])
crn = N.new('ShaderNodeValToRGB')
crn.color_ramp.elements[0].position = 0.0; crn.color_ramp.elements[0].color = (0.62, 0.26, 0.1, 1)
crn.color_ramp.elements[1].position = 1.0; crn.color_ramp.elements[1].color = (0.92, 0.57, 0.29, 1)
L.new(nz.outputs['Fac'], crn.inputs['Fac'])
# blend colours with a colour ramp driven by mask: use MixShader of two principled
b.inputs['Roughness'].default_value = 0.9
L.new(crn.outputs['Color'], b.inputs['Base Color'])
b2 = N.new('ShaderNodeBsdfPrincipled'); b2.inputs['Roughness'].default_value = 0.85
dk = N.new('ShaderNodeMapRange'); dk.inputs['From Min'].default_value = -0.4; dk.inputs['From Max'].default_value = -8.0
dk.inputs['To Min'].default_value = 1.0; dk.inputs['To Max'].default_value = 0.05
L.new(sep.outputs['Z'], dk.inputs['Value'])
cxyz = N.new('ShaderNodeCombineXYZ')
for i_ in range(3):
    L.new(dk.outputs['Result'], cxyz.inputs[i_])
vm = N.new('ShaderNodeVectorMath'); vm.operation = 'MULTIPLY'
L.new(crs.outputs['Color'], vm.inputs[0]); L.new(cxyz.outputs[0], vm.inputs[1])
L.new(vm.outputs[0], b2.inputs['Base Color'])
nz2 = N.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = 1.5; nz2.inputs['Detail'].default_value = 6
L.new(tcn.outputs['Object'], nz2.inputs['Vector'])
bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.6; bp.inputs['Distance'].default_value = 0.4
L.new(nz2.outputs['Fac'], bp.inputs['Height']); L.new(bp.outputs['Normal'], b2.inputs['Normal'])
bps = N.new('ShaderNodeBump'); bps.inputs['Strength'].default_value = 0.2; bps.inputs['Distance'].default_value = 0.05
L.new(nz.outputs['Fac'], bps.inputs['Height']); L.new(bps.outputs['Normal'], b.inputs['Normal'])
out = [n for n in N if n.type == 'OUTPUT_MATERIAL'][0]
ms = N.new('ShaderNodeMixShader')
L.new(mx.outputs[0], ms.inputs[0]); L.new(b.outputs[0], ms.inputs[1]); L.new(b2.outputs[0], ms.inputs[2])
L.new(ms.outputs[0], out.inputs['Surface'])
# haze on top: temporarily rename so add_haze finds the mix output
b.name = 'bsdf_sand'
ms.name = 'Principled BSDF'
add_haze(m, 1100)
TERRAIN = m

xs = axis_samples([(-750, -60, 6), (-60, -36, 1.0), (-36, 64, 0.25), (64, 100, 1.0), (100, 750, 6)])
ys = axis_samples([(-750, -130, 6), (-130, 130, 0.6), (130, 750, 6)])
print("terrain grid", len(xs), "x", len(ys))
grid_mesh("terrain", xs, ys, H, TERRAIN, flat_steep=0.85)
mesas_ring(D['strata'], [(0, 460, 80, 95), (14, 680, 160, 120), (-18, 540, 70, 80), (35, 600, 110, 70), (-40, 720, 180, 110),
                         (70, 520, 70, 90), (110, 800, 200, 85), (150, 620, 90, 65), (185, 700, 140, 105), (215, 520, 70, 80),
                         (250, 900, 260, 120), (290, 580, 90, 75), (320, 760, 160, 95), (-8, 330, 35, 50), (25, 360, 45, 40)])

def avoid(x, y):
    xn, xf = rims(y)
    return track_dist(x, y) < 6 or (xn - 4 < x < xf + 4) or river_dist(x, y) < 9 or (abs(x - MACRO.x) < 6 and abs(y - MACRO.y) < 6)

RIVER = [(-340, -150, 12), (-250, -122, 12), (-170, -84, 11), (-105, -50, 9), (-58, -24, 7.5), (-24, -9, 6), (-7, -3.2, 4.8), (-0.4, -0.9, 4.2)]
def river_dist(x, y):
    best = 1e9
    for (ax, ay, _), (bx, by, _) in zip(RIVER[:-1], RIVER[1:]):
        a = Vector((ax, ay)); b_ = Vector((bx, by)); p = Vector((x, y))
        ab = b_ - a; t = max(0, min(1, (p - a).dot(ab) / ab.length_squared))
        best = min(best, (a + ab * t - p).length)
    return best

scatter("rocks", 900, (-320, 320, -320, 320), H, avoid, 'rock', D['rock'], 11)
scatter("bushes", 700, (-320, 320, -320, 320), H, avoid, 'bush', D['bush'], 12)
scatter("cacti", 45, (-200, 200, -200, 200), H, lambda x, y: avoid(x, y) or track_dist(x, y) < 14, 'cactus', D['cactus'], 13)

# ------------------------------------------------------------------ track
trk = new_coll("track"); set_coll(trk)
RAIL_PROF = [(-0.065, 0.0), (0.065, 0.0), (0.065, 0.012), (0.012, 0.022), (0.009, 0.105), (0.036, 0.115),
             (0.036, 0.15), (-0.036, 0.15), (-0.036, 0.115), (-0.009, 0.105), (-0.012, 0.022), (-0.065, 0.012)]
BALLAST_PROF = [(-1.75, -0.08), (1.75, -0.08), (1.35, 0.26), (-1.35, 0.26)]

def sweep(name, pts2d, heads, prof, lat_off, z0, mat):
    bm = bmesh.new()
    rings = []
    for p, hd in zip(pts2d, heads):
        nrm = Vector((-hd.y, hd.x))
        ring = []
        for (u, v) in prof:
            q = p + nrm * (lat_off + u)
            ring.append(bm.verts.new((q.x, q.y, z0 + v)))
        rings.append(ring)
    n = len(prof)
    for a, b_ in zip(rings[:-1], rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b_[j], b_[i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _finish(name, bm, mat)

def near_samples():
    ss_ = [0.0, 5.0] + [10.0 * k for k in range(1, 17)] + [S1 + 2.0 * k for k in range(0, int(R_ARC * PHI / 2) + 1)] + [S1 + R_ARC * PHI + 20 * k for k in range(1, 18)]
    return sorted(set(ss_))
S_N = near_samples()
PN = [P(s) for s in S_N]
HN = [heading(s) for s in S_N]
PF = [Vector((x, 0.0)) for x in (FAR_RAIL_X, FAR_RAIL_X + 5, 60, 150, 300, 500, 750)]
HF = [Vector((1.0, 0.0))] * len(PF)
TIE_TOP = RAIL_TOP - 0.15
for side in (-1, 1):
    sweep(f"rail_near{side}", PN, HN, RAIL_PROF, side * RAIL_Y, TIE_TOP, RAIL)
    sweep(f"rail_far{side}", PF, HF, RAIL_PROF, side * RAIL_Y, TIE_TOP, RAIL)
# ballast ends just short of the rim
PB = [P(s) for s in S_N[1:]]; PB[0] = P(0.25)
sweep("ballast_near", [P(0.2)] + PB[1:], [heading(0.2)] + HN[2:], BALLAST_PROF, 0.0, 0.0, BALLAST)
sweep("ballast_far", [Vector((28.2, 0))] + PF[1:], HF, BALLAST_PROF, 0.0, 0.0, BALLAST)
# ties (one mesh)
bm = bmesh.new()
rnd = random.Random(5)
def add_tie(p, hd):
    yaw = math.atan2(hd.y, hd.x) + rnd.uniform(-0.03, 0.03)
    M = Matrix.Translation((p.x, p.y, TIE_TOP - 0.08)) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Diagonal((0.24, 2.6, 0.16, 1))
    bmesh.ops.create_cube(bm, size=1.0, matrix=M)
    for sd in (-1, 1):  # tie plates + spikes
        q = p + Vector((-hd.y, hd.x)) * (sd * RAIL_Y)
        M2 = Matrix.Translation((q.x, q.y, TIE_TOP + 0.008)) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Diagonal((0.2, 0.3, 0.016, 1))
        bmesh.ops.create_cube(bm, size=1.0, matrix=M2)
s = 0.32
while s < 980:
    add_tie(P(s), heading(s)); s += 0.62
x = FAR_RAIL_X + 0.3
while x < 750:
    add_tie(Vector((x, 0.0)), Vector((1.0, 0.0))); x += 0.62
_finish("ties", bm, TIE)

# ------------------------------------------------------------------ train
trn = new_coll("train"); set_coll(trn)

def wheel(name, x, side, R, nsp, spoke_mat, z=None, crank=None):
    parts = []
    y = side * RAIL_Y
    zc = R if z is None else z
    parts.append(tube(name + "_tire", R - 0.07, R, 0.13, (x, y, zc), mat=STEEL, seg=56))
    parts.append(tube(name + "_flange", R - 0.02, R + 0.05, 0.025, (x, y - side * 0.055, zc), mat=STEEL, seg=56))
    parts.append(tube(name + "_rim", R - 0.12, R - 0.065, 0.1, (x, y, zc), mat=spoke_mat, seg=56))
    parts.append(cyl(name + "_hub", 0.14, 0.12, 0.2, (x, y + side * 0.02, zc), mat=BRASS, axis='Y', seg=20))
    for i in range(nsp):
        a = 2 * math.pi * i / nsp
        d = Vector((math.cos(a), 0, math.sin(a)))
        parts.append(cyl_between(name + "_sp", Vector((x, y, zc)) + d * 0.1, Vector((x, y, zc)) + d * (R - 0.1), 0.032, 0.026, spoke_mat, 8))
    if crank is not None:
        a = crank + math.pi
        cw = Vector((x, y + side * 0.01, zc)) + Vector((math.cos(a), 0, math.sin(a))) * (R * 0.55)
        parts.append(box(name + "_cw", (R * 0.55, 0.09, R * 0.32), cw, (0, -a, 0), spoke_mat, 0.02))
    return parts

def build_loco():
    p = []
    RD, RS = 0.78, 0.42
    TH = math.radians(40)
    for side in (-1, 1):
        cr = TH if side > 0 else TH + math.pi / 2
        pins = []
        for ax in (0.9, -0.9):
            p += wheel(f"drv{ax}{side}", ax, side, RD, 14, RED, crank=cr)
            pin = Vector((ax + 0.34 * math.cos(cr), side * 0.88, RD + 0.34 * math.sin(cr)))
            pins.append(pin)
            p.append(cyl(f"pin", 0.05, 0.05, 0.14, pin, mat=STEEL, axis='Y', seg=12))
        for ax in (3.85, 2.9):
            p += wheel(f"lead{ax}{side}", ax, side, RS, 8, RED)
        # side rod + main rod + guides + cylinder
        a, b_ = pins[0] + Vector((0, side * 0.03, 0)), pins[1] + Vector((0, side * 0.03, 0))
        p.append(box("siderod", ((a - b_).length + 0.2, 0.05, 0.12), (a + b_) / 2, (0, 0, 0), STEEL, 0.015))
        xh = Vector((2.05, side * 0.98, 1.0))
        p.append(cyl_between("mainrod", xh, pins[0] + Vector((0, side * 0.08, 0)), 0.05, 0.045, STEEL, 10))
        p.append(box("crosshead", (0.25, 0.12, 0.2), xh, (0, 0, 0), STEEL, 0.01))
        for dz in (-0.12, 0.12):
            p.append(box("guide", (1.0, 0.05, 0.05), (2.4, side * 0.98, 1.0 + dz), (0, 0, 0), STEEL))
        p.append(cyl("cylinder", 0.32, 0.32, 1.0, (3.25, side * 1.0, 1.0), mat=RED, axis='X', seg=24))
        for dx in (-0.5, 0.5):
            p.append(tube("cyl_ring", 0.3, 0.345, 0.07, (3.25 + dx, side * 1.0, 1.0), mat=BRASS, axis='X', seg=24))
        p.append(box("valvechest", (0.9, 0.36, 0.38), (3.25, side * 1.0, 1.48), (0, 0, 0), RED, 0.03))
        p.append(box("runboard", (5.6, 0.42, 0.06), (0.85, side * 1.12, 1.68), (0, 0, 0), BLACK))
        p.append(box("runboard_trim", (5.6, 0.04, 0.12), (0.85, side * 1.33, 1.66), (0, 0, 0), GOLD))
    p.append(box("frame", (7.7, 0.84, 0.4), (0.55, 0, 0.98), (0, 0, 0), IRON))
    # boiler
    p.append(cyl("boiler", 0.72, 0.72, 5.1, (0.65, 0, 2.45), mat=RED, axis='X', seg=40))
    for bx in (-1.5, -0.4, 0.7, 1.8, 2.9):
        p.append(tube("band", 0.715, 0.75, 0.09, (bx, 0, 2.45), mat=GOLD, axis='X', seg=40))
    p.append(cyl("smokebox", 0.76, 0.76, 1.1, (3.75, 0, 2.45), mat=GUNMETAL, axis='X', seg=40))
    p.append(tube("sb_ring", 0.62, 0.79, 0.08, (4.3, 0, 2.45), mat=BRASS, axis='X', seg=40))
    p.append(cyl("sb_door", 0.62, 0.58, 0.08, (4.33, 0, 2.45), mat=GUNMETAL, axis='X', seg=40))
    p.append(sphere("sb_knob", 0.09, (4.4, 0, 2.45), BRASS))
    p.append(lathe("stack", [(0.24, 2.9), (0.22, 3.5), (0.25, 3.9), (0.4, 4.35), (0.56, 4.72), (0.6, 4.82), (0.6, 4.95), (0.5, 5.0)],
                   (3.6, 0, 0), mat=RED, seg=36))
    p.append(tube("stack_rim", 0.58, 0.64, 0.12, (3.6, 0, 4.88), mat=GOLD, axis='Z', seg=36))
    p.append(tube("stack_base", 0.24, 0.32, 0.12, (3.6, 0, 3.25), mat=GOLD, axis='Z', seg=36))
    p.append(cyl("stack_soot", 0.52, 0.52, 0.02, (3.6, 0, 4.985), mat=BLACK, seg=36))
    p.append(box("lamp", (0.45, 0.48, 0.5), (4.12, 0, 3.55), (0, 0, 0), RED, 0.03))
    p.append(box("lamp_top", (0.5, 0.52, 0.06), (4.12, 0, 3.83), (0, 0, 0), BRASS))
    p.append(cyl("lamp_lens", 0.17, 0.17, 0.04, (4.36, 0, 3.55), mat=LAMP, axis='X', seg=24))
    p.append(tube("lamp_ring", 0.16, 0.2, 0.05, (4.36, 0, 3.55), mat=BRASS, axis='X', seg=24))
    p.append(lathe("dome", [(0.42, 2.95), (0.38, 3.3), (0.32, 3.5), (0.18, 3.63), (0.0001, 3.67)], (1.4, 0, 0), mat=BRASS, seg=32))
    p.append(lathe("sanddome", [(0.32, 3.0), (0.3, 3.3), (0.22, 3.43), (0.0001, 3.48)], (0.2, 0, 0), mat=RED, seg=32))
    p.append(tube("sand_ring", 0.29, 0.33, 0.06, (0.2, 0, 3.3), mat=GOLD, axis='Z', seg=32))
    # bell
    p.append(cyl("bellpost", 0.03, 0.03, 0.4, (2.45, 0, 3.3), mat=BRASS, seg=10))
    p.append(lathe("bell", [(0.0001, 0.3), (0.06, 0.29), (0.1, 0.24), (0.11, 0.12), (0.14, 0.04), (0.17, 0.0)], (2.45, 0, 3.2), mat=BRASS, seg=32))
    # whistle (on boiler top, just ahead of the cab)
    wx = -0.75
    p.append(cyl("wh_pipe", 0.05, 0.05, 0.36, (wx, 0, 3.27), mat=BRASS, seg=16))
    p.append(sphere("wh_valve", 0.085, (wx, 0, 3.47), BRASS, 18))
    p.append(lathe("wh_bell", [(0.05, 3.52), (0.08, 3.55), (0.08, 3.98), (0.085, 4.0), (0.06, 4.05), (0.03, 4.1), (0.0001, 4.13)], (wx, 0, 0), mat=BRASS, seg=32))
    for zz in (3.62, 3.78, 3.92):
        p.append(tube("wh_rib", 0.078, 0.092, 0.025, (wx, 0, zz), mat=BRASS, axis='Z', seg=32))
    p.append(box("wh_mouth", (0.02, 0.1, 0.035), (wx + 0.08, 0, 3.6), (0, 0, 0), BLACK))
    p.append(cyl_between("wh_lever", (wx, 0, 3.5), (wx - 0.35, 0.0, 3.62), 0.012, mat=BRASS))
    p.append(cyl_between("wh_cord", (wx - 0.35, 0, 3.62), (-1.95, 0.0, 3.62), 0.006, mat=BLACK))
    # cab
    p.append(box("cab_front", (0.08, 2.6, 2.25), (-1.92, 0, 2.82), (0, 0, 0), RED))
    for side in (-1, 1):
        p.append(box("cab_side", (1.6, 0.07, 1.15), (-2.7, side * 1.3, 2.28), (0, 0, 0), RED))
        p.append(box("cab_trim", (1.64, 0.09, 0.07), (-2.7, side * 1.3, 2.86), (0, 0, 0), GOLD))
        p.append(box("cab_trim", (1.64, 0.09, 0.07), (-2.7, side * 1.3, 1.73), (0, 0, 0), GOLD))
        for px in (-1.95, -2.7, -3.45):
            p.append(box("cab_post", (0.1, 0.08, 1.0), (px, side * 1.3, 3.36), (0, 0, 0), RED))
        p.append(box("cab_header", (1.64, 0.08, 0.16), (-2.7, side * 1.3, 3.9), (0, 0, 0), GOLD))
    p.append(box("cab_back", (0.06, 2.6, 0.9), (-3.47, 0, 2.15), (0, 0, 0), RED))
    p.append(box("cab_floor", (1.6, 2.6, 0.08), (-2.7, 0, 1.7), (0, 0, 0), BLACK))
    p.append(cyl("cab_roof", 1.62, 1.62, 1.95, (-2.7, 0, 3.97), mat=BLACK, axis='X', seg=40, squash=(1, 1, 0.24)))
    p.append(box("cab_roof_trim", (1.98, 3.0, 0.05), (-2.7, 0, 3.98), (0, 0, 0), GOLD))
    # pilot / cowcatcher
    p.append(box("buffer", (0.22, 2.4, 0.36), (4.45, 0, 1.12), (0, 0, 0), RED, 0.02))
    p.append(box("buffer_trim", (0.24, 2.44, 0.05), (4.45, 0, 1.31), (0, 0, 0), GOLD))
    p.append(box("coupler", (0.3, 0.2, 0.16), (4.62, 0, 1.0), (0, 0, 0), BRASS))
    for i in range(11):
        yy = -1.0 + 0.2 * i
        u = abs(yy) / 1.05
        p.append(cyl_between("slat", (4.5, yy, 0.98), (5.35 - 0.85 * u, yy * 1.02, 0.1), 0.03, mat=RED, seg=6))
    for sd in (-1, 1):
        p.append(cyl_between("pilot_edge", (5.37, 0, 0.1), (4.5, sd * 1.07, 0.1), 0.04, mat=BRASS, seg=8))
    p.append(cyl("pilot_top", 0.045, 0.045, 2.2, (4.52, 0, 0.98), mat=BRASS, axis='Y', seg=10))
    return join("loco", p, (0, 0, 0))

def bogie(prefix, x0):
    p = []
    for ax in (-0.55, 0.55):
        for side in (-1, 1):
            p += wheel(f"{prefix}w{ax}{side}", x0 + ax, side, 0.42, 6, IRON)
    for side in (-1, 1):
        p.append(box("bogie_frame", (1.9, 0.12, 0.28), (x0, side * 0.93, 0.5), (0, 0, 0), IRON, 0.02))
        p.append(sphere("axlebox", 0.09, (x0 - 0.55, side * 0.99, 0.42), BRASS, 10))
        p.append(sphere("axlebox", 0.09, (x0 + 0.55, side * 0.99, 0.42), BRASS, 10))
    p.append(box("bolster", (0.3, 2.0, 0.22), (x0, 0, 0.78), (0, 0, 0), IRON))
    return p

def build_tender():
    p = []
    p.append(box("t_body", (4.6, 2.6, 1.5), (0, 0, 2.0), (0, 0, 0), RED, 0.04))
    for z in (1.27, 2.73):
        p.append(box("t_trim", (4.64, 2.64, 0.08), (0, 0, z), (0, 0, 0), GOLD))
    p.append(box("t_panel", (2.6, 2.64, 0.7), (0, 0, 2.0), (0, 0, 0), flat_mat("t_panel", (1.0, 0.72, 0.05), 0.3, coat=0.5)))
    p.append(ellipsoid("coal", (2.0, 1.15, 0.45), (0.3, 0, 2.7), (0, 0, 0), COAL, 24))
    p.append(box("t_frame", (4.8, 2.0, 0.3), (0, 0, 1.12), (0, 0, 0), IRON))
    p += bogie("tb1", 1.5); p += bogie("tb2", -1.5)
    p.append(box("t_coupler", (0.5, 0.2, 0.16), (2.55, 0, 1.0), (0, 0, 0), BRASS))
    return join("tender", p, (0, 0, 0))

def build_car(name, c1, c2, roof_col, k):
    p = []
    sm = stripe_mat(f"stripes_{name}", c1, c2)
    p.append(box("c_body", (9.6, 2.8, 2.5), (0, 0, 2.6), (0, 0, 0), sm, 0.03))
    for z in (1.4, 3.82):
        p.append(box("c_trim", (9.66, 2.86, 0.14), (0, 0, z), (0, 0, 0), GOLD, 0.02))
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.append(box("c_post", (0.14, 0.14, 2.5), (sx * 4.8, sy * 1.4, 2.6), (0, 0, 0), GOLD, 0.02))
    for sy in (-1, 1):
        p.append(box("c_frame", (4.5, 0.05, 1.45), (0, sy * 1.42, 2.6), (0, 0, 0), GOLD, 0.02))
        p.append(box("c_panel", (4.2, 0.05, 1.2), (0, sy * 1.44, 2.6), (0, 0, 0), CREAM, 0.02))
        for sx in (-3.6, 3.6):
            p.append(sphere("c_star", 0.25, (sx, sy * 1.43, 2.6), GOLD, 16))
    rm = flat_mat(f"roof_{name}", roof_col, 0.3, coat=0.5)
    p.append(cyl("c_roof", 1.58, 1.58, 9.9, (0, 0, 3.86), mat=rm, axis='X', seg=48, squash=(1, 1, 0.28)))
    p.append(cyl("c_roofcap", 0.12, 0.12, 9.9, (0, 0, 4.3), mat=GOLD, axis='X', seg=12))
    p.append(box("c_under", (9.4, 2.2, 0.3), (0, 0, 1.2), (0, 0, 0), IRON))
    p += bogie(f"{name}b1", 3.5); p += bogie(f"{name}b2", -3.5)
    p.append(box("c_coupler", (0.6, 0.2, 0.16), (5.05, 0, 1.0), (0, 0, 0), BRASS))
    return join(name, p, (0, 0, 0))

build_loco(); build_tender()
for k, (c1, c2, rc) in enumerate([(CR, CY, CB), (CB, CY, CR), (CY, CR, CB), (CB, (0.97, 0.95, 0.9), CR)]):
    build_car(f"car{k + 1}", c1, c2, rc, k)
place_train(215.0)

# ------------------------------------------------------------------ ants
def build_ant():
    p = []
    BODY = flat_mat("ant_body", (0.16, 0.05, 0.03), rough=0.3, coat=0.7)
    PLATE = ramp_mat("ant_plate", 'noise', ((0.0, (0.85, 0.87, 0.9)), (1.0, (0.97, 0.97, 0.98))), rough=0.1, metal=1.0,
                     bump=0.6, bump_dist=0.004, scale=9, detail=2)
    WHITE = flat_mat("ant_eye_white", (0.97, 0.97, 0.95), rough=0.2, coat=1.0)
    PUPIL = flat_mat("ant_pupil", (0.01, 0.01, 0.01), rough=0.1, coat=1.0)
    STRAP = flat_mat("ant_strap", (0.08, 0.05, 0.03), rough=0.5)
    zc = 0.07
    p.append(ellipsoid("a_head", (0.05, 0.045, 0.042), (0.115, 0, zc + 0.012), (0, 0, 0), BODY, 18))
    p.append(ellipsoid("a_thorax", (0.055, 0.032, 0.032), (0.035, 0, zc), (0, 0, 0), BODY, 16))
    p.append(sphere("a_petiole", 0.018, (-0.025, 0, zc - 0.002), BODY, 10))
    p.append(ellipsoid("a_abdomen", (0.08, 0.058, 0.052), (-0.1, 0, zc + 0.008), (0, -0.12, 0), BODY, 20))
    for s in (-1, 1):
        ec = Vector((0.145, s * 0.028, zc + 0.03))
        p.append(sphere("a_eye", 0.022, ec, WHITE, 14))
        p.append(sphere("a_pupil", 0.011, ec + Vector((0.013, s * 0.008, 0.002)), PUPIL, 10))
        a0 = Vector((0.14, s * 0.018, zc + 0.05)); a1 = a0 + Vector((0.01, s * 0.03, 0.06)); a2 = a1 + Vector((0.07, s * 0.02, 0.0))
        p.append(cyl_between("a_ant1", a0, a1, 0.005, mat=BODY, seg=6))
        p.append(cyl_between("a_ant2", a1, a2, 0.005, 0.004, BODY, 6))
        p.append(sphere("a_antk", 0.008, a2, BODY, 8))
        for (hx, fx) in ((0.06, 0.13), (0.035, 0.03), (0.01, -0.08)):
            hip = Vector((hx, s * 0.025, zc - 0.01)); knee = Vector(((hx + fx) / 2, s * 0.085, zc + 0.03)); foot = Vector((fx, s * 0.12, 0.003))
            p.append(cyl_between("a_leg1", hip, knee, 0.007, 0.006, BODY, 6))
            p.append(cyl_between("a_leg2", knee, foot, 0.006, 0.004, BODY, 6))
    # strapped steel plate on the back
    p.append(ellipsoid("a_plate", (0.115, 0.07, 0.022), (-0.045, 0, zc + 0.048), (0, -0.05, 0), PLATE, 28))
    for (sx, sr) in ((0.03, (0.012, 0.037, 0.04)), (-0.09, (0.012, 0.06, 0.057))):
        p.append(ellipsoid("a_strap", sr, (sx, 0, zc + 0.006), (0, 0, 0), STRAP, 16))
    for (rx, ry) in ((0.05, 0.045), (0.05, -0.045), (-0.14, 0.045), (-0.14, -0.045)):
        p.append(sphere("a_rivet", 0.006, (rx, ry, zc + 0.063), PLATE, 8))
    ob = join("ant_src", p, (0, 0, 0))
    ob.location = (0, 0, -1000)
    return ob
antc = new_coll("ant_src"); set_coll(antc)
ANT = build_ant()

def instancer(name, pts, rots, scales, coll):
    set_coll(coll)
    me = bpy.data.meshes.new(name)
    me.from_pydata(pts, [], [])
    a = me.attributes.new("rot", 'FLOAT_VECTOR', 'POINT')
    a.data.foreach_set('vector', [c for r in rots for c in r])
    s_ = me.attributes.new("scl", 'FLOAT', 'POINT')
    s_.data.foreach_set('value', scales)
    ob = bpy.data.objects.new(name, me)
    link(ob)
    ng = bpy.data.node_groups.new(name + "_gn", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    Nn, Ln = ng.nodes, ng.links
    gi = Nn.new('NodeGroupInput'); go = Nn.new('NodeGroupOutput')
    m2p = Nn.new('GeometryNodeMeshToPoints')
    iop = Nn.new('GeometryNodeInstanceOnPoints')
    oi = Nn.new('GeometryNodeObjectInfo'); oi.inputs['Object'].default_value = ANT
    try:
        oi.inputs['As Instance'].default_value = True
    except Exception:
        pass
    nr = Nn.new('GeometryNodeInputNamedAttribute'); nr.data_type = 'FLOAT_VECTOR'; nr.inputs['Name'].default_value = "rot"
    ns = Nn.new('GeometryNodeInputNamedAttribute'); ns.data_type = 'FLOAT'; ns.inputs['Name'].default_value = "scl"
    e2r = Nn.new('FunctionNodeEulerToRotation')
    Ln.new(gi.outputs[0], m2p.inputs['Mesh'])
    Ln.new(m2p.outputs['Points'], iop.inputs['Points'])
    Ln.new(oi.outputs['Geometry'], iop.inputs['Instance'])
    Ln.new(nr.outputs['Attribute'], e2r.inputs['Euler'])
    Ln.new(e2r.outputs['Rotation'], iop.inputs['Rotation'])
    Ln.new(ns.outputs['Attribute'], iop.inputs['Scale'])
    Ln.new(iop.outputs['Instances'], go.inputs[0])
    mod = ob.modifiers.new("ants", 'NODES')
    mod.node_group = ng
    print("INSTANCER", name, len(pts))
    return ob

rnd = random.Random(42)
# (1) ant river
pts, rots, scl = [], [], []
cum = []
for (ax, ay, aw), (bx, by, bw) in zip(RIVER[:-1], RIVER[1:]):
    a = Vector((ax, ay)); b_ = Vector((bx, by))
    seg = b_ - a; Ls = seg.length; hd = seg.normalized(); nrm = Vector((-hd.y, hd.x))
    steps = int(Ls / 0.35)
    for i in range(steps):
        t = i / steps
        c = a + seg * t
        w = aw + (bw - aw) * t
        # meander
        c = c + nrm * (2.0 * math.sin(c.length / 23.0))
        n = int(w * 0.35 * 9.0 * rnd.uniform(0.8, 1.2))
        for _ in range(n):
            u = rnd.gauss(0, 0.32)
            if abs(u) > 0.55:
                continue
            q = c + nrm * (u * w) + hd * rnd.uniform(-0.18, 0.18)
            xn, xf = rims(q.y)
            if q.x > xn - 0.15:
                continue
            z = H(q.x, q.y)
            if track_dist(q.x, q.y) < 1.9:
                z = max(z, TIE_TOP + 0.0)   # crawling over the ties
            yaw = math.atan2(hd.y, hd.x) + rnd.gauss(0, 0.35)
            pts.append((q.x, q.y, z)); rots.append((rnd.gauss(0, 0.06), rnd.gauss(0, 0.06), yaw)); scl.append(rnd.uniform(0.85, 1.15))
riv = new_coll("ants_river")
instancer("ant_river", pts, rots, scl, riv)

# (2) ant bridge across the gap, under the rail ends
pts, rots, scl = [], [], []
GAP0, GAP1, BW = -0.1, 28.1, 2.1
def zbridge(x):
    t = (x - GAP0) / (GAP1 - GAP0)
    return -0.32 - 2.3 * math.sin(math.pi * max(0, min(1, t)))
for layer in range(4):
    x = GAP0
    while x <= GAP1:
        y = -BW
        while y <= BW:
            xx = x + rnd.uniform(-0.08, 0.08); yy = y + rnd.uniform(-0.05, 0.05)
            edge = abs(yy) / BW
            zz = zbridge(xx) - layer * 0.1 - 0.12 * edge ** 2 + rnd.uniform(-0.02, 0.02)
            slope = math.atan2(zbridge(xx + 0.2) - zbridge(xx - 0.2), 0.4)
            yaw = (0 if rnd.random() < 0.5 else math.pi) + rnd.gauss(0, 0.45)
            pitch = -slope if abs(yaw) < 1.6 else slope
            pts.append((xx, yy, zz)); rots.append((rnd.gauss(0, 0.35), pitch + rnd.gauss(0, 0.25), yaw)); scl.append(rnd.uniform(0.9, 1.15))
            y += 0.17
        x += 0.24
# hanging chains under the bridge
for _ in range(110):
    xx = rnd.uniform(GAP0 + 1.5, GAP1 - 1.5); yy = rnd.uniform(-BW * 0.9, BW * 0.9)
    z0 = zbridge(xx) - 0.35
    for k in range(rnd.randint(2, 7)):
        pts.append((xx + rnd.uniform(-0.03, 0.03), yy + rnd.uniform(-0.03, 0.03), z0 - k * 0.27))
        rots.append((rnd.gauss(0, 0.3), math.pi / 2 + rnd.gauss(0, 0.2), rnd.uniform(0, 6.28))); scl.append(rnd.uniform(0.9, 1.1))
# anchors climbing the rim faces at both ends
for (x0, sgn) in ((0.0, -1), (28.0, 1)):
    for _ in range(900):
        yy = rnd.uniform(-BW - 0.4, BW + 0.4)
        zz = rnd.uniform(-1.4, 0.0)
        xx = x0 + sgn * rnd.uniform(-0.05, 0.12) * (1 if zz < -0.05 else 0)
        if zz > -0.06:   # on the rim top
            xx = x0 + sgn * rnd.uniform(0.0, 1.3); zz = H(xx, yy) if not (abs(yy) < 1.9) else max(H(xx, yy), 0.0)
            rot = (rnd.gauss(0, 0.1), rnd.gauss(0, 0.1), (math.pi if sgn < 0 else 0) * 0 + (0 if sgn < 0 else math.pi) + rnd.gauss(0, 0.5))
        else:
            rot = (rnd.gauss(0, 0.3), (-math.pi / 2 if sgn < 0 else math.pi / 2) * 0 + math.pi / 2 * (1 if rnd.random() < 0.5 else -1), rnd.uniform(0, 6.28))
        pts.append((xx, yy, zz)); rots.append(rot); scl.append(rnd.uniform(0.9, 1.1))
brg = new_coll("ants_bridge")
instancer("ant_bridge", pts, rots, scl, brg)

# (3) macro patch: fine sand, pebbles, emerging ants (B21) + a marching column (B23)
mac = new_coll("ants_macro"); set_coll(mac)
EMERGE = [(0.15, 0.0, 0.06, 0.55), (0.42, -0.28, 0.035, 0.4), (0.55, 0.3, 0.08, 0.7), (0.9, -0.05, 0.02, 0.25), (0.75, 0.55, 0.05, 0.5)]
def h_macro(x, y):
    lx, ly = x - MACRO.x, y - MACRO.y
    h = H(x, y) + 0.03
    h += 0.008 * math.sin((lx * 0.9 + ly * 0.35) * 22 + 3 * noise.noise(Vector((lx, ly, 0.5))))
    h += 0.012 * noise.noise(Vector((lx * 3, ly * 3, 2.0)))
    for (ex, ey, sink, tilt) in EMERGE:
        d2 = (lx - ex) ** 2 + (ly - ey) ** 2
        h += 0.045 * math.exp(-d2 / (2 * 0.09 ** 2))
    return h
FINE = ramp_mat("sand_fine", 'noise', ((0.0, (0.62, 0.27, 0.1)), (0.5, (0.82, 0.43, 0.19)), (1.0, (0.93, 0.6, 0.32))),
                rough=0.92, bump=0.6, bump_dist=0.004, scale=40, detail=10)
mxs = [MACRO.x + i * 0.02 for i in range(-125, 151)]
mys = [MACRO.y + j * 0.02 for j in range(-125, 151)]
grid_mesh("macro_sand", mxs, mys, h_macro, FINE, flat_steep=-2)
bm = bmesh.new()
rp = random.Random(9)
for _ in range(700):
    lx, ly = rp.uniform(-2.4, 2.9), rp.uniform(-2.4, 2.9)
    r = rp.choice([0.004, 0.006, 0.008, 0.012, 0.018, 0.03]) * rp.uniform(0.7, 1.3)
    x_, y_ = MACRO.x + lx, MACRO.y + ly
    M = Matrix.Translation((x_, y_, h_macro(x_, y_) + r * 0.3)) @ Euler((rp.random(), rp.random(), rp.random() * 6)).to_matrix().to_4x4() @ Matrix.Diagonal((r * 1.3, r, r * 0.7, 1))
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0, matrix=M)
for f in bm.faces:
    f.smooth = True
PEB = ramp_mat("pebbles", 'noise', ((0.3, (0.3, 0.09, 0.04)), (0.5, (0.62, 0.36, 0.2)), (0.7, (0.45, 0.15, 0.07))), rough=0.6, scale=25, coat=0.2)
_finish("pebbles", bm, PEB)
pts, rots, scl = [], [], []
for (ex, ey, sink, tilt) in EMERGE:
    x_, y_ = MACRO.x + ex, MACRO.y + ey
    yaw = math.pi + rp.choice((-1, 1)) * rp.uniform(0.7, 1.2)
    pts.append((x_, y_, h_macro(x_, y_) - sink)); rots.append((0, -tilt, yaw)); scl.append(1.0)
for i in range(16):   # marching column toward -X (toward the B23 camera)
    x_ = MACRO.x + i * 0.36 + rp.uniform(-0.03, 0.03); y_ = MACRO.y + 1.6 + 0.06 * math.sin(i * 1.3)
    pts.append((x_, y_, (h_macro if x_ < MACRO.x + 2.9 else H)(x_, y_) - 0.004)); rots.append((0, 0, math.pi + rp.gauss(0, 0.12))); scl.append(1.08 if i == 0 else 1.0)
instancer("ant_macro", pts, rots, scl, mac)

cam = camera()
look_at(cam, (-9.0, 0.0, 1.35), (6.0, 0.0, -1.6), 22)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "train.blend"))
print("SAVED train.blend")
