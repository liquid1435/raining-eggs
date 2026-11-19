r"""Raining Eggs, zone 10 (Golden Nest) as Blender meshes.

  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P gen_golden.py   -> out\RainingEggsGolden.fbx + out\golden_*.png

Meshes (Roblox axes, origin on the ground, front = -Z):
  Map_GoldenNest (100 wide, open at the front), Map_GoldenEgg (10 tall, centre origin), Map_TreeGold,
  Map_Treasure1..4 (gem colour), Map_Pedestal
"""
import bpy, bmesh, math, sys, pathlib, random

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from blib import *          # noqa: F401,F403
import blib

OUT = HERE / 'out'
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
MAT = reset()
R = random.Random(101)
BROWN, DBROWN, TWIG3 = (124, 84, 52), (92, 60, 38), (150, 104, 60)
GOLD2, STRAW, GEMS = (255, 214, 70), (240, 210, 120), [(240, 60, 90), (70, 200, 255), (120, 240, 140), (190, 110, 255)]


def nest():
    b = B()
    rng = random.Random(7)
    rcyl(b, (0, 0.25, 0), 50, 0.5, (236, 180, 60), segs=40)                  # golden ground disc
    rcyl(b, (0, 0.6, 0), 42, 0.6, STRAW, segs=36)                            # straw lining
    for j in range(60):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(4, 40)
        rbox(b, (r * math.cos(a), 1.0, r * math.sin(a)), (rng.uniform(3, 6), 0.25, 0.3), shade(STRAW, rng.uniform(0.85, 1.1)), 0, yaw=rng.uniform(0, 180))
    for ring, (r, y, n) in enumerate(((44, 2, 34), (47, 5.6, 34), (45, 9.2, 32), (48, 12.6, 30), (46, 15.6, 28))):
        for k in range(n):
            a = k * 360 / n + ring * 7
            if 250 < a % 360 < 290:
                continue
            ln = rng.uniform(14, 20)
            ar = math.radians(a)
            cx, cz = r * math.cos(ar), r * math.sin(ar)
            tx, tz = -math.sin(ar), math.cos(ar)                              # tangent
            tw = rng.uniform(-0.35, 0.35)
            dx, dz = tx * math.cos(tw) - math.cos(ar) * math.sin(tw), tz * math.cos(tw) - math.sin(ar) * math.sin(tw)
            dy = rng.uniform(-0.15, 0.15)
            p0 = (cx - dx * ln / 2, y - dy * ln / 2, cz - dz * ln / 2)
            p1 = (cx + dx * ln / 2, y + dy * ln / 2, cz + dz * ln / 2)
            c = rng.choice((BROWN, DBROWN, TWIG3))
            rtube(b, p0, p1, rng.uniform(1.4, 1.9), c, 7)
            if rng.random() < 0.3:                                            # small twig sticking out
                q = (cx + math.cos(ar) * 3, y + rng.uniform(1, 3), cz + math.sin(ar) * 3)
                rtube(b, (cx, y, cz), q, 0.4, c, 5, 0.15)
            if rng.random() < 0.15:                                           # a leaf
                rplank(b, (cx, y + 1.6, cz), (cx + math.cos(ar) * 2.4, y + 2.2, cz + math.sin(ar) * 2.4), 1.4, 0.15, (120, 180, 70), 0)
    return b.finish('Map_GoldenNest', (0, 0, 0), MAT)


def golden_egg():
    b = B()
    vs = bmesh.ops.create_uvsphere(b.bm, u_segments=28, v_segments=18, radius=1, matrix=M((0, 0, 0)))['verts']
    for v in vs:
        z = v.co.z
        k = 1.0 - 0.16 * z
        v.co.x *= 3.6 * k
        v.co.y *= 3.6 * k
        v.co.z *= 5.0
    b.paint(vs, (255, 200, 40))
    for j in range(3):                                                        # decorative bands
        y = -1.6 + j * 1.6
        rr = 3.6 * math.sqrt(max(0.05, 1 - (y / 5) ** 2)) * (1 - 0.16 * y / 5) + 0.05
        rcyl(b, (0, y, 0), rr, 0.35, (255, 246, 190), segs=28)
    for j in range(10):                                                       # gems on the middle band
        a = j * math.tau / 10
        rr = 3.6 * (1 - 0.16 * 0) + 0.1
        rico(b, (rr * math.cos(a), 0, rr * math.sin(a)), 0.35, GEMS[j % 4], (1, 1, 0.6), 1, yaw=-math.degrees(a))
    return b.finish('Map_GoldenEgg', (0, 0, 0), MAT)


def tree_gold():
    b = B()
    r = random.Random(17)
    TR, LF = (250, 240, 220), (255, 190, 40)
    for k in range(4):
        a = k * math.tau / 4 + 0.4
        rbox(b, (1.1 * math.cos(a), 0.4, 1.1 * math.sin(a)), (1.6, 0.8, 0.8), shade(TR, 0.85), 0.15, yaw=-math.degrees(a))
    rcyl(b, (0, 4.5, 0), 1.0, 9, TR, segs=7, r2=0.7)
    rbox(b, (1.3, 7.2, 0), (2.4, 0.7, 0.7), TR, 0.1, rz=30)
    blobs = [(0, 12.4, 0, 4.8)] + [(3.6 * math.cos(a), 11.2 + r.uniform(-0.6, 0.8), 3.6 * math.sin(a), r.uniform(2.8, 3.4))
                                    for a in (k * math.tau / 5 + 0.3 for k in range(5))] + [(0.4, 15.8, -0.3, 3.2)]
    for x, y, z, rr in blobs:
        rico(b, (x, y, z), rr, shade(LF, 0.88 + (y - 10) * 0.04), (1, 0.9, 1), 1, yaw=r.uniform(0, 60))
    for k in range(8):                                                        # sparkly fruit
        a, yy = r.uniform(0, math.tau), r.uniform(10.5, 15)
        rball(b, (4.2 * math.cos(a), yy, 4.2 * math.sin(a)), 0.45, (255, 250, 220), segs=6, rings=5)
    return b.finish('Map_TreeGold', (0, 0, 0), MAT)


def treasure(k):
    b = B()
    rng = random.Random(300 + k)
    for j in range(7):                                                        # coin stacks
        x, z = rng.uniform(-2.6, 2.6), rng.uniform(-2.6, 2.6)
        for h in range(rng.randint(2, 6)):
            rcyl(b, (x, 0.2 + h * 0.36, z), 0.8, 0.34, GOLD if h % 2 == 0 else GOLD2, segs=12)
    for j in range(14):                                                       # loose coins
        a, r = rng.uniform(0, math.tau), rng.uniform(1, 4)
        rcyl(b, (r * math.cos(a), 0.12, r * math.sin(a)), 0.7, 0.2, GOLD2, segs=10, rx=rng.uniform(-15, 15))
    for j in range(3):                                                        # gold bars
        rbox(b, (rng.uniform(-2, 2), 0.5 + j * 0.9, rng.uniform(-2, 2)), (2.4, 0.9, 1.1), GOLD, 0.2, yaw=rng.uniform(0, 180))
    rico(b, (0, 3.6, 0), 1.6, GEMS[k], (1, 1.15, 1), 1)                       # the gem on top
    rico(b, (-0.5, 4.3, -0.9), 0.4, (255, 255, 255), (1, 1, 0.6), 1)
    return b.finish(f'Map_Treasure{k + 1}', (0, 0, 0), MAT)


def pedestal():
    b = B()
    rcyl(b, (0, 0.5, 0), 5.4, 1, (236, 236, 244), segs=16)
    rcyl(b, (0, 3.4, 0), 4.3, 4.8, (246, 246, 250), segs=16)
    for j in range(12):
        a = j * math.tau / 12
        rbox(b, (4.3 * math.cos(a), 3.4, 4.3 * math.sin(a)), (0.3, 4.6, 0.3), (226, 226, 236), 0, yaw=-math.degrees(a))
    rcyl(b, (0, 6.5, 0), 5.6, 1, GOLD, segs=16)
    rcyl(b, (0, 7.15, 0), 2.6, 0.3, (255, 236, 150), segs=16)
    return b.finish('Map_Pedestal', (0, 0, 0), MAT)


objs = [nest(), golden_egg(), tree_gold()] + [treasure(k) for k in range(4)] + [pedestal()]
save_meta(HERE.parent / 'game')
print('triangles:', {o.name: len(o.data.polygons) for o in objs})
if 'nofbx' not in ARGS:
    print('wrote', blib.export(objs, OUT / 'RainingEggsGolden.fbx'))

# ---------------------------------------------------------------- preview scene
sc, cam = scene_setup(sky=(1.0, 0.92, 0.7, 1), ground=(1.0, 0.68, 0.16, 1))
for o in objs:
    o.hide_render = True
by = {o.name: o for o in objs}
gold = bpy.data.materials.new('GoldShiny')
gold.use_nodes = True
pb = gold.node_tree.nodes['Principled BSDF']
vc = gold.node_tree.nodes.new('ShaderNodeVertexColor')
vc.layer_name = 'Col'
gold.node_tree.links.new(vc.outputs['Color'], pb.inputs['Base Color'])
pb.inputs['Metallic'].default_value = 0.6
pb.inputs['Roughness'].default_value = 0.25
road = B()
rbox(road, (0, 0.05, 30), (18, 0.1, 240), (255, 244, 200), 0)
road.finish('Road', (0, 0, 0), MAT)
blib.META.pop('Road', None)


def put(name, pos, yaw=0, s=1.0, mat=None):
    o = place(by[name], name + '_p', pos, yaw, s)
    if mat:
        o.data = o.data.copy()
        o.data.materials.clear()
        o.data.materials.append(mat)
    return o


put('Map_GoldenNest', (0, 0, 92))
put('Map_GoldenEgg', (0, 33, 92), 0, 6.6, gold)
for k, (x, z) in enumerate(((-70, 40), (70, 30), (-90, 80), (90, 90), (-64, 120))):
    put('Map_TreeGold', (x, 0, z), k * 50, R.uniform(1.0, 1.5))
for k, (x, z) in enumerate(((-24, 10), (26, 16), (-40, 30), (40, 40))):
    put(f'Map_Treasure{k + 1}', (x, 0, z), k * 60, 1.2)
for sx in (-1, 1):
    for k in range(2):
        put('Map_Pedestal', (sx * (24 + k * 22), 0, 58))
if 'norender' not in ARGS:
    shot(sc, cam, OUT / 'golden_scene.png', (0, 46, -46), (0, 18, 70), (1800, 1000), 24)
