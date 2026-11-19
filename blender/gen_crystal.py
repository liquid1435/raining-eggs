r"""Raining Eggs, zone 5 (Crystal Coast) as Blender meshes.

  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P gen_crystal.py   -> out\RainingEggsCrystal.fbx + out\crystal_*.png

Meshes (Roblox axes, origin on the ground, front = -Z):
  Map_Crystal1..4 (single, 4 tall), Map_CrystalCluster1..4 (20 tall), Map_TidePool + Map_TidePoolWater (60 x 40),
  Map_Palm (18 tall), Map_Lighthouse + Map_LighthouseNeon, Map_Starfish, Map_Shell1, Map_Shell2, Map_Throne
"""
import bpy, bmesh, math, sys, pathlib, random
from mathutils import Vector

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from blib import *          # noqa: F401,F403
import blib

OUT = HERE / 'out'
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
MAT = reset()
R = random.Random(41)
CS = [(80, 230, 255), (190, 120, 255), (255, 110, 210), (110, 255, 200)]
SAND, ROCK, BARK = (246, 226, 168), (150, 154, 170), (176, 132, 84)


def prism(b, base, h, r, c, tip=0.3, tilt=(0, 0), yaw=0.0):
    """hexagonal crystal standing at base (Roblox), height h, radius r, pointed top; tilt = (rx, rz) degrees"""
    x, y, z = base
    m = M((x, y, z), yaw=yaw, rx=tilt[0], rz=tilt[1])
    from mathutils import Matrix
    body = m @ Matrix.Translation((0, 0, h * (1 - tip) / 2))
    b.cyl(r, h * (1 - tip), body, c, 6)
    top = m @ Matrix.Translation((0, 0, h * (1 - tip) + h * tip / 2))
    b.cyl(r, h * tip, top, mix(c, WHITE, 0.35), 6, 0.02)
    # light streak on one face
    streak = m @ Matrix.Translation((r * 0.75, 0, h * (1 - tip) * 0.55)) @ Matrix.Diagonal((0.12, r * 0.5, h * (1 - tip) * 0.7, 1))
    vs = bmesh.ops.create_cube(b.bm, size=1, matrix=streak)['verts']
    b.paint(vs, mix(c, WHITE, 0.7))


def crystal_single(k):
    b = B()
    prism(b, (0, -0.3, 0), 4, 0.6, CS[k], 0.35)
    return b.finish(f'Map_Crystal{k + 1}', (0, 0, 0), MAT)


def crystal_cluster(k):
    b = B()
    rng = random.Random(k)
    c = CS[k]
    for j in range(7):                                                       # rocky base
        a = j * math.tau / 7
        rico(b, (3.2 * math.cos(a), 0.2, 3.2 * math.sin(a)), rng.uniform(1.2, 2.0), shade(ROCK, rng.uniform(0.8, 1.05)), (1, 0.6, 1), 1)
    prism(b, (0, -0.5, 0), 20, 2.6, c, 0.28, (rng.uniform(-6, 6), rng.uniform(-6, 6)), rng.uniform(0, 60))
    for j in range(5):
        a = j * math.tau / 5 + rng.uniform(-0.3, 0.3)
        hh = 20 * rng.uniform(0.3, 0.6)
        prism(b, (2.6 * math.cos(a), -0.5, 2.6 * math.sin(a)), hh, hh * 0.13, shade(c, rng.uniform(0.85, 1.15)), 0.3,
              (math.degrees(math.sin(a)) * 0.45 * (-1), math.degrees(math.cos(a)) * 0.45), rng.uniform(0, 60))
    return b.finish(f'Map_CrystalCluster{k + 1}', (0, 0, 0), MAT)


def tide_pool():
    b, w = B(), B()
    rcyl(b, (0, 0.1, 0), 1, 0.2, shade(SAND, 0.88), segs=30, scale=(30, 1, 20))
    rcyl(b, (0, 0.15, 0), 1, 0.2, (60, 160, 200), segs=28, scale=(26, 1, 16.5))
    rcyl(b, (0, 0.18, 0), 1, 0.2, (40, 120, 180), segs=24, scale=(17, 1, 9))
    rcyl(w, (0, 0.45, 0), 1, 0.2, (110, 220, 235), segs=30, scale=(26.6, 1, 17))
    for j in range(30):                                                      # rocks around
        a = j * math.tau / 30 + R.uniform(-0.05, 0.05)
        s = R.uniform(1.0, 2.6)
        rico(b, (27.5 * math.cos(a), s * 0.3, 18 * math.sin(a)), s, shade(ROCK, R.uniform(0.8, 1.1)), (1, 0.55, 0.9), 1, yaw=R.uniform(0, 90))
    for x, z, c in ((-12, -4, (255, 110, 150)), (8, 6, (255, 150, 80)), (16, -6, (200, 120, 255)), (-4, 8, (255, 220, 90))):   # coral
        for j in range(5):
            a = j * math.tau / 5
            rtube(b, (x, 0.2, z), (x + 1.6 * math.cos(a), 2.4 + R.uniform(0, 1.4), z + 1.6 * math.sin(a)), 0.32, c, 6)
            rball(b, (x + 1.6 * math.cos(a), 2.6 + R.uniform(0, 1.2), z + 1.6 * math.sin(a)), 0.45, mix(c, WHITE, 0.3), segs=6, rings=4)
    for x, z in ((-6, -8), (20, 2), (-18, 6)):                                # sea weed
        for j in range(4):
            rbeam(b, (x + j * 0.6, 0.2, z), (x + j * 0.6 + R.uniform(-0.8, 0.8), R.uniform(2, 3.6), z), 0.3, (60, 170, 100), 0.04)
    return [b.finish('Map_TidePool', (0, 0, 0), MAT), w.finish('Map_TidePoolWater', (0, 0, 0), MAT)]


def palm():
    b = B()
    pts = []
    for k in range(9):                                                        # bent trunk
        t = k / 8
        pts.append((3.2 * t ** 2, 18 * t, 0))
    for k in range(8):
        r0, r1 = 1.15 - k * 0.06, 1.1 - (k + 1) * 0.06
        rtube(b, pts[k], pts[k + 1], r0, BARK if k % 2 == 0 else shade(BARK, 0.86), 8, r1)
        rtube(b, (pts[k + 1][0], pts[k + 1][1] - 0.25, 0), (pts[k + 1][0], pts[k + 1][1] + 0.05, 0), r1 + 0.18, shade(BARK, 0.75), 8)
    top = pts[-1]
    for j in range(3):                                                        # coconuts
        a = j * math.tau / 3
        rball(b, (top[0] + 0.9 * math.cos(a), top[1] - 0.9, 0.9 * math.sin(a)), 0.75, (120, 80, 50), segs=8, rings=6)
    for j in range(7):                                                        # fronds with leaflets
        a = j * math.tau / 7 + 0.2
        dx, dz = math.cos(a), math.sin(a)
        prev = (top[0], top[1] + 0.4, top[2])
        for s in range(6):
            t = (s + 1) / 6
            p = (top[0] + dx * 8.5 * t, top[1] + 0.4 + 2.4 * t - 5.6 * t * t, top[2] + dz * 8.5 * t)
            w = 2.6 * (1.15 - t) + 0.4
            rplank(b, prev, p, w, 0.16, (56 + s * 10, 150 + s * 8, 64 + s * 4), 0.02)
            rplank(b, prev, p, 0.22, 0.3, (40, 110, 50), 0.02)                    # midrib
            prev = p
    return b.finish('Map_Palm', (0, 0, 0), MAT)


def lighthouse():
    b, n = B(), B()
    RED = (236, 60, 70)
    for j in range(12):                                                       # rocks
        a = j * math.tau / 12
        rico(b, (11 * math.cos(a), 1.2, 11 * math.sin(a)), R.uniform(2.6, 4), shade(ROCK, R.uniform(0.8, 1.05)), (1, 0.7, 1), 1)
    rcyl(b, (0, 1.6, 0), 12, 3.2, ROCK, segs=12)
    rad = lambda y: 7.6 - (y - 3) / 42 * 2.8
    for k in range(7):
        y0 = 3.2 + k * 6
        rcyl(b, (0, y0 + 3, 0), rad(y0), 6, WHITE if k % 2 == 0 else RED, segs=16, r2=rad(y0 + 6))
    for y, a in ((10, 0), (22, 120), (34, 240)):                              # windows
        rr = rad(y) + 0.05
        x, z = rr * math.sin(math.radians(a)), -rr * math.cos(math.radians(a))
        rbox(b, (x, y, z), (1.6, 2.4, 0.5), INK, 0.08, yaw=-a)
        rbox(n, (x * 1.01, y, z * 1.01), (1.1, 1.8, 0.5), (255, 230, 140), 0.05, yaw=-a)
    rbox(b, (0, 5.6, -7.5), (3.4, 5, 0.8), (120, 80, 50), 0.1)                # door
    rcyl(b, (0, 8.1, -7.5), 1.7, 0.8, (120, 80, 50), axis='Z', segs=10)
    rcyl(b, (0, 45.6, 0), 6.4, 1, INK, segs=16)                               # gallery
    for j in range(20):
        a = j * math.tau / 20
        rbox(b, (6 * math.cos(a), 47.1, 6 * math.sin(a)), (0.25, 2, 0.25), INK, 0.03)
    for j in range(20):
        a0, a1 = j * math.tau / 20, (j + 1) * math.tau / 20
        rbeam(b, (6 * math.cos(a0), 48.1, 6 * math.sin(a0)), (6 * math.cos(a1), 48.1, 6 * math.sin(a1)), 0.25, INK, 0.02)
    rcyl(n, (0, 49.2, 0), 3.4, 6, (255, 240, 150), segs=12)                  # lamp room glass
    for j in range(8):
        a = j * math.tau / 8
        rbox(b, (3.5 * math.cos(a), 49.2, 3.5 * math.sin(a)), (0.3, 6, 0.3), INK, 0.03)
    rcyl(b, (0, 52.6, 0), 4.6, 0.8, RED, segs=16)
    rcyl(b, (0, 55, 0), 4.2, 4, RED, segs=16, r2=0.6)
    rball(b, (0, 57.4, 0), 0.8, GOLD, segs=8, rings=6)
    return [b.finish('Map_Lighthouse', (0, 0, 0), MAT), n.finish('Map_LighthouseNeon', (0, 0, 0), MAT)]


def starfish():
    b = B()
    c = (255, 150, 120)
    rball(b, (0, 0.25, 0), 0.5, c, (1, 0.5, 1), 10, 6)
    for j in range(5):
        a = j * math.tau / 5
        rtube(b, (0, 0.25, 0), (1.2 * math.cos(a), 0.18, 1.2 * math.sin(a)), 0.35, c, 6, 0.08)
        for t in (0.4, 0.7):
            rball(b, (1.2 * t * math.cos(a), 0.42, 1.2 * t * math.sin(a)), 0.08, mix(c, WHITE, 0.6), segs=4, rings=3)
    return b.finish('Map_Starfish', (0, 0, 0), MAT)


def shell(k):
    b = B()
    if k == 0:                                                               # spiral shell
        c = (255, 240, 230)
        for j in range(8):
            t = j / 7
            rball(b, (0.9 - t * 0.9, 0.35 + t * 0.55, 0), 0.62 - t * 0.42, shade(c, 1 - (j % 2) * 0.08), segs=10, rings=6)
    else:                                                                    # scallop
        c = (255, 190, 90)
        for j in range(7):
            a = math.radians(30 + j * 20)
            rtube(b, (0, 0.15, 0.6), (1.1 * math.cos(a), 0.25, 0.6 - 1.1 * math.sin(a)), 0.22, shade(c, 1 - (j % 2) * 0.12), 6, 0.3)
        rbox(b, (0, 0.12, 0.65), (0.6, 0.24, 0.35), shade(c, 0.85), 0.05)
    return b.finish(f'Map_Shell{k + 1}', (0, 0, 0), MAT)


def throne():
    b = B()
    rng = random.Random(77)
    rcyl(b, (0, 1, 0), 7, 2, (200, 200, 230), segs=6)
    rcyl(b, (0, 2.6, 0), 5.6, 1.2, (230, 230, 255), segs=6)
    rbox(b, (0, 5.2, 0.4), (7, 3.8, 6), (160, 120, 255), 0.3)                 # seat
    rbox(b, (0, 7.3, 0.4), (7.4, 0.6, 6.4), (255, 110, 210), 0.2)
    rbox(b, (0, 11, 3.2), (7.4, 11, 1.4), (160, 120, 255), 0.3)               # back
    for sx in (-1, 1):
        rbox(b, (sx * 3.6, 9, 0.4), (1, 2.4, 6), (120, 90, 220), 0.2)         # arms
        prism(b, (sx * 3.6, 9.6, -2.4), 3, 0.5, CS[0], 0.4)
    for j, x in enumerate((-3, -1.5, 0, 1.5, 3)):
        prism(b, (x, 16.2, 3.2), 4 + (2 - abs(j - 2)) * 2.2, 0.75, CS[j % 4], 0.35)
    rball(b, (0, 13, 2.4), 1.2, GOLD, segs=10, rings=6)
    return b.finish('Map_Throne', (0, 0, 0), MAT)


objs = [crystal_single(k) for k in range(4)] + [crystal_cluster(k) for k in range(4)] + tide_pool() + [palm()] + lighthouse() + \
       [starfish(), shell(0), shell(1), throne()]
save_meta(HERE.parent / 'game')
print('triangles:', {o.name: len(o.data.polygons) for o in objs})
if 'nofbx' not in ARGS:
    print('wrote', blib.export(objs, OUT / 'RainingEggsCrystal.fbx'))

# ---------------------------------------------------------------- preview scene
sc, cam = scene_setup(sky=(0.6, 0.85, 1.0, 1), ground=(0.92, 0.78, 0.45, 1))
for o in objs:
    o.hide_render = True
by = {o.name: o for o in objs}
glow = glow_material(4)
water = bpy.data.materials.new('Water')
water.use_nodes = True
water.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.3, 0.75, 0.85, 1)
water.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.05
road = B()
rbox(road, (0, 0.05, 40), (18, 0.1, 240), (255, 246, 214), 0)
road.finish('Road', (0, 0, 0), MAT)
blib.META.pop('Road', None)


def put(name, pos, yaw=0, s=1.0, sv=None, mat=None):
    o = place(by[name], name + '_p', pos, yaw, s)
    if sv:
        o.scale = (sv[0], sv[2], sv[1])
    if mat:
        o.data = o.data.copy()
        o.data.materials.clear()
        o.data.materials.append(mat)
    return o


put('Map_Lighthouse', (-56, 0, 74))
put('Map_LighthouseNeon', (-56, 0, 74), mat=glow)
put('Map_TidePool', (-34, 0, 14), sv=(0.8, 1, 0.8))
put('Map_TidePoolWater', (-34, 0, 14), sv=(0.8, 1, 0.8), mat=water)
put('Map_Throne', (46, 0, 70), 180)
for k in range(9):
    a = k * 40
    put(f'Map_CrystalCluster{k % 4 + 1}', (46 + 14 * math.cos(math.radians(a)), 0, 70 + 14 * math.sin(math.radians(a))), k * 30, R.uniform(0.9, 1.6))
for k, (x, z) in enumerate(((22, 10), (-20, 46), (60, 20), (30, 104))):
    put(f'Map_CrystalCluster{k % 4 + 1}', (x, 0, z), k * 50, R.uniform(0.6, 1.0))
for k, (x, z) in enumerate(((-18, -12), (16, 40), (-70, 40), (72, 46), (-26, 100), (20, 70))):
    put('Map_Palm', (x, 0, z), k * 60, R.uniform(0.9, 1.15))
for k in range(26):
    x, z = R.choice((-1, 1)) * R.uniform(11, 80), R.uniform(-24, 110)
    put(f'Map_Crystal{k % 4 + 1}', (x, 0, z), R.uniform(0, 360), R.uniform(0.6, 1.2)) if k % 2 else \
        put(('Map_Starfish', 'Map_Shell1', 'Map_Shell2')[k % 3], (x, 0, z), R.uniform(0, 360), 1.6)
if 'norender' not in ARGS:
    shot(sc, cam, OUT / 'crystal_scene.png', (4, 44, -64), (0, 10, 46), (1800, 1000), 26)
    shot(sc, cam, OUT / 'crystal_lighthouse.png', (-22, 34, 30), (-56, 26, 74), (1200, 1000), 32)
