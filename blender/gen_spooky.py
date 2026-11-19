r"""Raining Eggs, zone 6 (Spooky Hollow) as Blender meshes.

  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P gen_spooky.py   -> out\RainingEggsSpooky.fbx + out\spooky_*.png

Meshes (Roblox axes, origin on the ground, front = -Z):
  Map_DeadTree1, Map_DeadTree2 (18 tall), Map_Pumpkin, Map_PumpkinLit + Map_PumpkinLitNeon (5 wide),
  Map_Tomb1..3, Map_GraveFence (43 long), Map_HauntedHouse + Map_HauntedHouseNeon, Map_Ghost (centre origin),
  Map_SpookyLantern + Map_SpookyLanternNeon
"""
import bpy, bmesh, math, sys, pathlib, random

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from blib import *          # noqa: F401,F403
import blib

OUT = HERE / 'out'
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
MAT = reset()
R = random.Random(61)
D, STONE, ORANGE = (56, 44, 52), (150, 154, 168), (255, 132, 30)
HP, ROOF, GLOWY, GREEN = (84, 62, 110), (40, 34, 52), (255, 220, 90), (140, 255, 150)


def dead_tree(k):
    b = B()
    rng = random.Random(100 + k)
    for j in range(5):                                                        # roots
        a = j * math.tau / 5 + rng.uniform(-0.2, 0.2)
        rtube(b, (0, 1.2, 0), (2.8 * math.cos(a), 0, 2.8 * math.sin(a)), 0.7, D, 6, 0.25)
    pts = [(0, 0, 0)]
    for j in range(1, 7):                                                     # crooked trunk
        pts.append((rng.uniform(-0.8, 0.8) + (0.6 * j if k else -0.3 * j) * 0.3, j * 3, rng.uniform(-0.6, 0.6)))
    for j in range(6):
        rtube(b, pts[j], pts[j + 1], 1.5 - j * 0.18, shade(D, 1 + (j % 2) * 0.12), 7, 1.5 - (j + 1) * 0.18)
    rbox(b, (pts[2][0], 5.4, -1.1), (1.0, 1.4, 0.4), (20, 14, 20), 0.2)       # hollow
    def branch(p, d, ln, r, depth):
        if depth == 0 or r < 0.12:
            return
        e = (p[0] + d[0] * ln, p[1] + d[1] * ln, p[2] + d[2] * ln)
        rtube(b, p, e, r, D, 6, r * 0.6)
        for s in (-1, 1):
            a = rng.uniform(0.4, 0.9) * s
            nd = (d[0] * math.cos(a) - d[2] * math.sin(a), d[1] * 0.8 + 0.25, d[0] * math.sin(a) + d[2] * math.cos(a))
            L = math.sqrt(sum(v * v for v in nd))
            branch(e, tuple(v / L for v in nd), ln * 0.65, r * 0.6, depth - 1)
    for j in range(4):
        a = j * math.tau / 4 + rng.uniform(0, 0.8)
        p = pts[rng.randint(3, 6)]
        branch(p, (math.cos(a) * 0.8, 0.6, math.sin(a) * 0.8), rng.uniform(4, 6), 0.75, 3)
    return b.finish(f'Map_DeadTree{k + 1}', (0, 0, 0), MAT)


def pumpkin(lit):
    b, n = B(), B()
    for j in range(8):                                                        # ribs
        a = j * math.tau / 8
        rball(b, (1.0 * math.cos(a), 2.1, 1.0 * math.sin(a)), 1.9, shade(ORANGE, 0.94 + (j % 2) * 0.08), (0.7, 0.85, 0.7), 10, 7)
    rball(b, (0, 2.1, 0), 2.2, ORANGE, (1, 0.8, 1), 12, 8)
    rtube(b, (0, 3.6, 0), (0.3, 4.6, 0.1), 0.35, (70, 130, 60), 6, 0.25)
    rplank(b, (0.2, 3.9, 0.3), (1.6, 4.0, 1.2), 1.2, 0.1, (80, 160, 70))
    for t in range(6):                                                        # curly vine
        a0, a1 = t * 1.1, (t + 1) * 1.1
        rtube(b, (-0.6 + 0.5 * math.cos(a0), 3.9 + t * 0.12, 0.5 * math.sin(a0)), (-0.6 + 0.5 * math.cos(a1), 3.9 + (t + 1) * 0.12, 0.5 * math.sin(a1)), 0.07, (70, 130, 60), 4)
    if lit:                                                                   # carved face (glows)
        for sx in (-1, 1):
            rcyl(n, (sx * 0.9, 2.6, -2.15), 0.55, 0.3, GLOWY, axis='Z', segs=3, rz=180)
        rcyl(n, (0, 2.0, -2.3), 0.3, 0.3, GLOWY, axis='Z', segs=3)
        for j in range(5):
            rbox(n, (-1.2 + j * 0.6, 1.3 + (0.25 if j % 2 else 0), -2.15), (0.5, 0.45, 0.3), GLOWY, 0.02)
        return [b.finish('Map_PumpkinLit', (0, 0, 0), MAT), n.finish('Map_PumpkinLitNeon', (0, 0, 0), MAT)]
    n.bm.free()
    return [b.finish('Map_Pumpkin', (0, 0, 0), MAT)]


def tomb(k):
    b = B()
    rbox(b, (0, 0.2, -0.6), (4, 0.4, 5.4), (80, 70, 60), 0.1)                # dirt mound
    if k == 0:                                                                # rounded RIP stone
        rbox(b, (0, 2.3, 0), (3.4, 4.6, 1.0), STONE, 0.12)
        rcyl(b, (0, 4.6, 0), 1.7, 1.0, STONE, axis='Z', segs=14)
        for j, ch in enumerate(('R', 'I', 'P')):
            rbox(b, (-0.9 + j * 0.9, 3.6, -0.52), (0.55, 0.9, 0.08), shade(STONE, 0.65), 0)
        rico(b, (1.2, 0.6, -0.6), 0.6, (96, 150, 84), (1, 0.5, 1), 1)
    elif k == 1:                                                              # cross
        rbox(b, (0, 0.4, 0), (2.4, 0.8, 1.4), STONE, 0.1)
        rbox(b, (0, 3.2, 0), (0.9, 5.4, 0.8), STONE, 0.1)
        rbox(b, (0, 4.4, 0), (3.2, 0.9, 0.8), STONE, 0.1)
    else:                                                                     # tilted cracked slab
        rbox(b, (0, 2.0, 0), (3.2, 4.0, 0.9), shade(STONE, 0.9), 0.15, rz=8, rx=-6)
        rbox(b, (0.6, 4.2, 0.1), (1.6, 0.8, 0.9), shade(STONE, 0.9), 0.15, rz=-14)
        rbox(b, (-0.3, 2.6, -0.48), (0.12, 2.4, 0.1), shade(STONE, 0.6), 0, rz=20)
    return b.finish(f'Map_Tomb{k + 1}', (0, 0, 0), MAT)


def grave_fence():
    b = B()
    for j in range(15):
        x = -21 + j * 3
        rbox(b, (x, 2.4, 0), (0.3, 4.8, 0.3), INK, 0.02)
        rcyl(b, (x, 5.1, 0), 0.3, 0.7, INK, segs=4, r2=0.02)
    for y in (1.0, 3.6):
        rbox(b, (0, y, 0), (43, 0.35, 0.3), INK, 0.02)
    for sx in (-1, 1):
        rbox(b, (sx * 21.5, 3, 0), (1.2, 6, 1.2), STONE, 0.15)
        rball(b, (sx * 21.5, 6.6, 0), 0.7, STONE, segs=8, rings=5)
    return b.finish('Map_GraveFence', (0, 0, 0), MAT)


def haunted_house():
    b, n = B(), B()
    rbox(b, (0, 0.6, 0), (36, 1.2, 28), STONE, 0.2)
    rbox(b, (0, 11.6, 0), (34, 21, 26), HP, 0.15, rz=1.2)
    for y in range(2, 22, 2):                                                 # siding lines
        rbox(b, (0, y, -13.05), (33.8, 0.18, 0.1), shade(HP, 0.75), 0)
    for sx in (-1, 1):
        for sz in (-1, 1):
            rbox(b, (sx * 17, 11.6, sz * 13), (0.9, 21.4, 0.9), shade(HP, 0.7), 0.1)
    # windows with crooked shutters (glass glows)
    for wx, wy in ((-10, 15), (10, 15), (-10, 6.5), (10, 6.5)):
        rbox(b, (wx, wy, -13.1), (4.8, 6, 0.4), ROOF, 0.08)
        rbox(n, (wx, wy, -13.3), (3.8, 5, 0.3), GLOWY, 0.04)
        rbox(b, (wx, wy, -13.45), (0.25, 5, 0.2), ROOF, 0)
        rbox(b, (wx, wy + 0.4, -13.45), (3.8, 0.25, 0.2), ROOF, 0)
        for sx in (-1, 1):
            rbox(b, (wx + sx * 3.1, wy, -13.3), (1.4, 5.6, 0.25), (60, 46, 76), 0.05, rz=sx * R.uniform(3, 12))
    rbox(b, (-10, 6.5, -13.6), (5.2, 0.5, 0.2), (120, 90, 60), 0.02, rz=25)   # boarded window
    rbox(b, (-10, 6.5, -13.65), (5.2, 0.5, 0.2), (120, 90, 60), 0.02, rz=-20)
    # porch: steps, posts, roof
    for k in range(3):
        rbox(b, (0, 0.4 + k * 0.5, -15.4 + k * 0.9), (10 - k, 0.5, 2.2), (110, 84, 60), 0.08)
    rbox(b, (0, 5.4, -13.3), (5, 9, 0.6), (40, 30, 30), 0.08)                # door
    rcyl(b, (0, 10, -13.3), 2.5, 0.6, (40, 30, 30), axis='Z', segs=10)
    rball(b, (1.6, 5.4, -13.7), 0.3, GOLD, segs=6, rings=4)
    for sx in (-1, 1):
        rbox(b, (sx * 5.5, 6.6, -17.6), (0.6, 11, 0.6), (110, 84, 60), 0.06)
    rbox(b, (0, 12.4, -15.6), (13, 0.6, 5.4), ROOF, 0.1, rx=-12)
    # main roof: steep with shingle strips + crooked ridge
    for sx in (-1, 1):
        x0, y0, x1, y1 = sx * 18.4, 21.2, 0, 35.8
        L = math.hypot(x1 - x0, y1 - y0)
        a = math.degrees(math.atan2(y1 - y0, x1 - x0))
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        nx, ny = -uy * sx * -1, ux * sx * -1
        if ny < 0:
            nx, ny = -nx, -ny
        rbox(b, ((x0 + x1) / 2, (y0 + y1) / 2, 0), (L, 0.8, 29.4), ROOF, 0.12, rz=a)
        for j in range(6):                                                   # shingle rows
            t = -L / 2 + L * (j + 0.5) / 6
            rbox(b, ((x0 + x1) / 2 + ux * t + nx * 0.45, (y0 + y1) / 2 + uy * t + ny * 0.45, R.uniform(-0.4, 0.4)),
                 (L / 6 * 0.9, 0.25, 29), shade(ROOF, 1.1 + (j % 2) * 0.12), 0.06, rz=a)
    rbox(b, (0, 35.4, 0), (1.4, 1.0, 29.4), ROOF, 0.1, rz=4)
    prism_pts = [(-17, 22), (17, 22), (0, 35.5)]
    for z in (-13.05, 13.05):                                                 # gable walls
        bm = b.bm
        vs = [bm.verts.new((x, -z, y)) for x, y in prism_pts]
        f = bm.faces.new(vs if z < 0 else list(reversed(vs)))
        b.paint(vs, shade(HP, 0.92))
    rcyl(n, (0, 27.5, -13.2), 1.8, 0.3, GLOWY, axis='Z', segs=12)             # round attic window
    rcyl(b, (0, 27.5, -13.1), 2.2, 0.4, ROOF, axis='Z', segs=12)
    # tower with pointed roof
    rbox(b, (12, 30, 4), (9, 16, 9), shade(HP, 0.88), 0.12)
    rbox(n, (12, 32, -0.6), (3, 4, 0.3), (140, 255, 150), 0.04)
    rcyl(b, (12, 38.6, 4), 7.4, 1.0, ROOF, segs=4, yaw=45)
    rcyl(b, (12.4, 45, 4), 6.6, 12, ROOF, segs=4, r2=0.2, yaw=45, rz=-4)
    rbeam(b, (12.9, 50.8, 4), (13.2, 54, 4), 0.2, INK, 0.02)
    for j in range(5):                                                        # bats on the tower tip
        rbox(b, (13.2 + (j - 2) * 0.6, 53 + abs(j - 2) * -0.3, 4), (0.6, 0.2, 0.3), INK, 0.02)
    rbox(b, (-11, 34, 7), (3, 8, 3), STONE, 0.15, rz=-3)                      # chimney
    rbox(b, (-11, 38.2, 7), (3.8, 0.8, 3.8), shade(STONE, 0.8), 0.1, rz=-3)
    for j in range(5):                                                        # cobwebs at corners
        rbeam(b, (-17, 21.6, -13.2), (-17 + 1.2 * j, 21.6 - 3, -13.2), 0.08, (220, 220, 230), 0)
    return [b.finish('Map_HauntedHouse', (0, 0, 0), MAT), n.finish('Map_HauntedHouseNeon', (0, 0, 0), MAT)]


def ghost():
    b = B()
    W = (240, 244, 255)
    rball(b, (0, 1.4, 0), 2.5, W, (1, 1.1, 1), 16, 10)
    rcyl(b, (0, -0.8, 0), 2.45, 2.6, W, segs=16, r2=2.5)
    for j in range(8):                                                        # wavy hem
        a = j * math.tau / 8
        rball(b, (2.2 * math.cos(a), -2.1, 2.2 * math.sin(a)), 0.75, W, (1, 1.3, 1), 8, 5)
    for sx in (-1, 1):
        rball(b, (sx * 0.9, 1.9, -2.15), 0.45, INK, (1, 1.4, 0.6), 8, 6)
        rball(b, (sx * 2.6, 0.2, -0.4), 0.7, W, (1.4, 0.7, 0.8), 8, 5)       # arms
    rball(b, (0, 0.8, -2.3), 0.4, INK, (1.2, 1, 0.5), 8, 5)                  # "oooh" mouth
    rball(b, (-1.3, 1.3, -2.1), 0.3, (255, 160, 190), (1, 0.6, 0.4), 6, 4)
    rball(b, (1.3, 1.3, -2.1), 0.3, (255, 160, 190), (1, 0.6, 0.4), 6, 4)
    return b.finish('Map_Ghost', (0, 0, 0), MAT)


def lantern():
    b, n = B(), B()
    rbox(b, (0, 0.4, 0), (1.6, 0.8, 1.6), INK, 0.1)
    rcyl(b, (0, 5, 0), 0.25, 9, INK, segs=6)
    for t in range(8):                                                        # curl at the top
        a0, a1 = t * 0.6, (t + 1) * 0.6
        rtube(b, (0.6 * math.sin(a0), 9 + 0.6 * (1 - math.cos(a0)), 0), (0.6 * math.sin(a1), 9 + 0.6 * (1 - math.cos(a1)), 0), 0.15, INK, 5)
    rbox(b, (0, 8.0, 0), (2.8, 0.3, 2.8), INK, 0.05)
    rcyl(b, (0, 11.4, 0), 1.9, 1.2, INK, segs=4, r2=0.3, yaw=45)
    for dx, dz in ((-1.1, -1.1), (1.1, -1.1), (-1.1, 1.1), (1.1, 1.1)):
        rbox(b, (dx, 9.4, dz), (0.2, 2.6, 0.2), INK, 0)
    rbox(n, (0, 9.4, 0), (1.9, 2.4, 1.9), GREEN, 0.12)
    return [b.finish('Map_SpookyLantern', (0, 0, 0), MAT), n.finish('Map_SpookyLanternNeon', (0, 0, 0), MAT)]


objs = [dead_tree(0), dead_tree(1)] + pumpkin(False) + pumpkin(True) + [tomb(k) for k in range(3)] + [grave_fence()] + \
       haunted_house() + [ghost()] + lantern()
save_meta(HERE.parent / 'game')
print('triangles:', {o.name: len(o.data.polygons) for o in objs})
if 'nofbx' not in ARGS:
    print('wrote', blib.export(objs, OUT / 'RainingEggsSpooky.fbx'))

# ---------------------------------------------------------------- preview scene (dusk)
sc, cam = scene_setup(sky=(0.22, 0.2, 0.36, 1), ground=(0.06, 0.09, 0.08, 1))
for o in objs:
    o.hide_render = True
by = {o.name: o for o in objs}
glow = glow_material(5)
gm = bpy.data.materials.new('Ghostly')
gm.use_nodes = True
gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.9, 0.92, 1, 1)
gm.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value = (0.5, 0.55, 0.7, 1)
gm.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 0.6
road = B()
rbox(road, (0, 0.05, 40), (18, 0.1, 240), (128, 116, 140), 0)
road.finish('Road', (0, 0, 0), MAT)
blib.META.pop('Road', None)


def put(name, pos, yaw=0, s=1.0, mat=None):
    o = place(by[name], name + '_p', pos, yaw, s)
    if mat:
        o.data = o.data.copy()
        o.data.materials.clear()
        o.data.materials.append(mat)
    return o


put('Map_HauntedHouse', (-46, 0, 60), 10)
put('Map_HauntedHouseNeon', (-46, 0, 60), 10, mat=glow)
for k in range(10):
    put(f'Map_Tomb{k % 3 + 1}', (30 + (k % 5) * 7, 0, 30 + (k // 5) * 8), R.uniform(-10, 10))
put('Map_GraveFence', (44, 0, 24))
for k, (x, z) in enumerate(((-20, 6), (20, 70), (60, 80), (-70, 20), (-14, 100), (74, 4))):
    put(f'Map_DeadTree{k % 2 + 1}', (x, 0, z), k * 70, R.uniform(0.9, 1.3))
for k in range(14):
    x, z, s = R.choice((-1, 1)) * R.uniform(11, 50), R.uniform(-20, 100), R.uniform(0.6, 1.3)
    if k % 3 == 0:
        put('Map_PumpkinLit', (x, 0, z), 0, s)
        put('Map_PumpkinLitNeon', (x, 0, z), 0, s, glow)
    else:
        put('Map_Pumpkin', (x, 0, z), R.uniform(0, 360), s)
for k in range(5):
    put('Map_Ghost', (R.uniform(-40, 40), R.uniform(8, 20), R.uniform(10, 90)), R.uniform(-30, 30), 1.0, gm)
for k in range(4):
    z = 10 + k * 22
    put('Map_SpookyLantern', (12, 0, z))
    put('Map_SpookyLanternNeon', (12, 0, z), mat=glow)
if 'norender' not in ARGS:
    shot(sc, cam, OUT / 'spooky_scene.png', (6, 40, -60), (0, 8, 46), (1800, 1000), 26)
    shot(sc, cam, OUT / 'spooky_house.png', (-16, 26, 18), (-46, 20, 60), (1400, 1000), 32)
