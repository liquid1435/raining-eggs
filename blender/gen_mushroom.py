r"""Raining Eggs, zone 2 (Mushroom Grove) as Blender meshes.

  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P gen_mushroom.py   -> out\RainingEggsMushroom.fbx + out\mushroom_*.png

Meshes (Roblox axes, origin on the ground / at the cap base, front = -Z):
  Map_MushStem (10 tall, 3 wide: the game stretches it), Map_MushCap1..4 (10 wide, sits on top of the stem),
  Map_GlowMush + Map_GlowMushNeon (small glowing cluster, ~3 wide), Map_MushHouse + Map_MushHouseNeon,
  Map_Log (14 long along X), Map_Spore1, Map_Spore2 (1 wide, Neon)
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
R = random.Random(11)
STEM, GILL, DBROWN = (250, 236, 210), (240, 200, 196), (92, 60, 38)
CAPS = [(232, 60, 70), (255, 140, 40), (236, 80, 190), (70, 190, 220)]
GLOW = [(90, 240, 230), (190, 130, 255), (130, 255, 150)]


def dome(b, pos, r, h, c, segs=20, rings=10):
    """half ellipsoid (flat side down) at a Roblox position"""
    x, y, z = pos
    res = bmesh.ops.create_uvsphere(b.bm, u_segments=segs, v_segments=rings, radius=1, matrix=M(pos, scale=(r, h, r)))
    vs = res['verts']
    low = [v for v in vs if v.co.z < y - 1e-4]
    bmesh.ops.delete(b.bm, geom=low, context='VERTS')
    vs = [v for v in vs if v.is_valid]
    edges = [e for e in {e for v in vs for e in v.link_edges} if e.is_boundary]
    bmesh.ops.holes_fill(b.bm, edges=edges, sides=0)
    b.paint(vs, c)


def spots(b, pos, r, h, n, c, rng, size=0.12):
    x0, y0, z0 = pos
    for k in range(n):
        th = rng.uniform(0.2, 0.95)
        ph = rng.uniform(0, math.tau) if k else 0
        if k == 0:
            th = 0
        x, y, z = r * math.sin(th) * math.cos(ph), h * math.cos(th), r * math.sin(th) * math.sin(ph)
        nx, ny, nz = x / r ** 2, y / h ** 2, z / r ** 2                     # surface normal of the dome
        tilt = math.degrees(math.atan2(math.hypot(nx, nz), ny))
        rcyl(b, (x0 + x * 1.005, y0 + y * 1.005, z0 + z * 1.005), r * size * rng.uniform(0.8, 1.3), 0.06 * r, c,
             segs=12, yaw=180 - math.degrees(ph), rz=tilt)


def stem():
    b = B()
    rcyl(b, (0, 5, 0), 1.5, 10, STEM, segs=12, r2=1.25)
    rcyl(b, (0, 0.4, 0), 1.75, 0.8, shade(STEM, 0.92), segs=12, r2=1.5)
    rcyl(b, (0, 7.6, 0), 1.6, 0.5, shade(STEM, 0.95), segs=12)               # little skirt
    for k in range(5):
        a = k * math.tau / 5
        rbox(b, (1.3 * math.cos(a), 5, 1.3 * math.sin(a)), (0.18, 8.5, 0.18), shade(STEM, 0.9), 0, yaw=-math.degrees(a))
    return b.finish('Map_MushStem', (0, 0, 0), MAT)


def cap(k):
    b = B()
    c = CAPS[k]
    rcyl(b, (0, 0.15, 0), 4.7, 0.3, GILL, segs=20)
    for j in range(16):
        a = j * math.tau / 16
        rbox(b, (2.6 * math.cos(a), 0.02, 2.6 * math.sin(a)), (4, 0.08, 0.12), shade(GILL, 0.85), 0, yaw=-math.degrees(a))
    dome(b, (0, 0.2, 0), 5, 3.2, c)
    rcyl(b, (0, 0.35, 0), 5.02, 0.3, shade(c, 0.8), segs=20)
    spots(b, (0, 0.2, 0), 5, 3.2, 9, WHITE, random.Random(k), 0.15)
    return b.finish(f'Map_MushCap{k + 1}', (0, 0, 0), MAT)


def glow_cluster():
    b, n = B(), B()
    for k, (x, z, h, rr) in enumerate(((0, 0, 2.6, 1.5), (1.6, 0.9, 1.6, 1.0), (-1.3, 1.1, 1.2, 0.8))):
        rcyl(b, (x, h / 2, z), rr * 0.28, h, STEM, segs=8, r2=rr * 0.22)
        dome(n, (x, h, z), rr, rr * 0.7, GLOW[k], 12, 6)
        for j in range(3):
            a = j * math.tau / 3 + k
            rball(b, (x + rr * 0.55 * math.cos(a), h + rr * 0.45, z + rr * 0.55 * math.sin(a)), rr * 0.13, WHITE, (1, 0.5, 1), 6, 4)
    for _ in range(5):
        rbox(b, (R.uniform(-2, 2), 0.3, R.uniform(-2, 2)), (0.2, R.uniform(0.6, 1.2), 0.2), (120, 110, 200), 0.02, rz=R.uniform(-20, 20))
    return [b.finish('Map_GlowMush', (0, 0, 0), MAT), n.finish('Map_GlowMushNeon', (0, 0, 0), MAT)]


def house():
    b, n = B(), B()
    rcyl(b, (0, 15, 0), 12, 30, STEM, segs=18, r2=10.6)
    for y in (6, 13, 20, 27):                                  # soft rings on the stem
        rr = 12 - y / 30 * 1.4
        rcyl(b, (0, y, 0), rr + 0.15, 0.4, shade(STEM, 0.93), segs=18)
    rcyl(b, (0, 0.6, 0), 12.8, 1.2, (170, 160, 150), segs=18)
    # door: stone arch, wooden door, steps
    rbox(b, (0, 5, -11.7), (8, 9.6, 1.2), (180, 170, 160), 0.2)
    rcyl(b, (0, 9.8, -11.7), 4, 1.2, (180, 170, 160), axis='Z', segs=14)
    rbox(b, (0, 4.8, -12.2), (6, 8.6, 0.6), (150, 96, 56), 0.08)
    rcyl(b, (0, 9.1, -12.2), 3, 0.6, (150, 96, 56), axis='Z', segs=14)
    for k in range(5):
        rbox(b, (-2.4 + k * 1.2, 6.5, -12.55), (0.14, 8.4, 0.1), (118, 72, 40), 0)
    rball(b, (2.0, 5.2, -12.6), 0.35, GOLD, segs=8, rings=5)
    for k in range(3):
        rbox(b, (0, 0.25 + k * 0.5, -14.6 + k * 1.1), (9 - k, 0.5, 2.4), (170, 160, 150), 0.12)
    # round windows (glass glows)
    for y, a in ((12, 45), (12, -45), (21, 0), (21, 140), (12, 180)):
        rr = 12 - y / 30 * 1.4
        x, z = rr * math.sin(math.radians(a)), -rr * math.cos(math.radians(a))
        rcyl(b, (x, y, z), 2.1, 0.8, (150, 96, 56), axis='Z', segs=14, yaw=-a)
        rcyl(n, (x * 1.02, y, z * 1.02), 1.6, 0.6, (255, 220, 120), axis='Z', segs=14, yaw=-a)
        rbox(b, (x * 1.05, y, z * 1.05), (3.2, 0.25, 0.3), (150, 96, 56), 0, yaw=-a)
        rbox(b, (x * 1.05, y, z * 1.05), (0.25, 3.2, 0.3), (150, 96, 56), 0, yaw=-a)
    # balcony on the side
    rcyl(b, (9.5, 17, -5), 4, 0.6, (150, 96, 56), segs=10, scale=(1, 1, 1))
    for k in range(8):
        a = math.radians(-80 + k * 25)
        rbox(b, (9.5 + 3.8 * math.cos(a), 18.1, -5 + 3.8 * math.sin(a)), (0.3, 1.8, 0.3), (118, 72, 40), 0.04)
    rbox(b, (12.4, 19.0, -5), (0.3, 0.3, 7), (118, 72, 40), 0.04)
    # cap: red dome with white spots, gills underneath, chimney
    rcyl(b, (0, 30.3, 0), 29.5, 0.6, GILL, segs=28)
    dome(b, (0, 30.4, 0), 31, 17, (232, 60, 70), 28, 12)
    rcyl(b, (0, 30.8, 0), 31.05, 0.8, (190, 44, 56), segs=28)
    spots(b, (0, 30.4, 0), 31, 17, 13, WHITE, random.Random(5), 0.14)
    rbox(b, (-12, 44, 6), (3.4, 9, 3.4), (170, 160, 150), 0.3)
    rbox(b, (-12, 48.8, 6), (4.2, 0.9, 4.2), (140, 132, 124), 0.2)
    # lanterns on posts by the door + flower pots + little mushrooms around the base
    for sx in (-1, 1):
        x = sx * 6.4
        rbox(b, (x, 3, -14.4), (0.5, 6, 0.5), INK, 0.05)
        rbox(b, (x, 6.4, -14.4), (1.6, 0.3, 1.6), INK, 0.05)
        rbox(n, (x, 7.4, -14.4), (1.1, 1.6, 1.1), (255, 222, 120), 0.1)
        rbox(b, (x, 8.4, -14.4), (1.7, 0.4, 1.7), INK, 0.05)
        rcyl(b, (sx * 9.5, 1.0, -12), 1.2, 2.0, (206, 110, 70), segs=10, r2=1.5)
        for j in range(4):
            rball(b, (sx * 9.5 + R.uniform(-0.8, 0.8), 2.4 + R.uniform(0, 0.6), -12 + R.uniform(-0.8, 0.8)), 0.45, RAINBOW[(j + sx) % 7], segs=6, rings=4)
    for k in range(9):
        a = math.radians(30 + k * 36)
        x, z = 13.6 * math.sin(a), -13.6 * math.cos(a)
        h = R.uniform(1.2, 2.6)
        rcyl(b, (x, h / 2, z), 0.35, h, STEM, segs=8)
        dome(b, (x, h, z), 1.1, 0.8, CAPS[k % 4], 10, 5)
    return [b.finish('Map_MushHouse', (0, 0, 0), MAT), n.finish('Map_MushHouseNeon', (0, 0, 0), MAT)]


def log():
    b = B()
    rcyl(b, (0, 1.7, 0), 1.7, 14, DBROWN, axis='X', segs=12)
    for sx in (-1, 1):
        rcyl(b, (sx * 7.02, 1.7, 0), 1.45, 0.1, (196, 150, 100), axis='X', segs=12)
        rcyl(b, (sx * 7.05, 1.7, 0), 0.9, 0.1, (60, 38, 24), axis='X', segs=10)
    for k in range(10):
        a = k * math.tau / 10
        rbox(b, (R.uniform(-6, 6), 1.7 + 1.62 * math.cos(a), 1.62 * math.sin(a)), (R.uniform(2, 4), 0.16, 0.2), shade(DBROWN, 0.8), 0, rx=-math.degrees(a))
    for x in (-3.5, 2.5):
        rico(b, (x, 3.3, 0.2), 1.6, (96, 170, 84), (1.3, 0.3, 0.9), 2)
    for x, c in ((-1, CAPS[0]), (0.4, CAPS[1]), (4.4, CAPS[0])):
        rcyl(b, (x, 3.8, -0.3), 0.18, 0.9, STEM, segs=6)
        dome(b, (x, 4.2, -0.3), 0.55, 0.4, c, 8, 4)
    return b.finish('Map_Log', (0, 0, 0), MAT)


def spore(k):
    b = B()
    rico(b, (0, 0, 0), 0.5, ((140, 255, 240), (220, 170, 255))[k], (1, 1, 1), 2)
    return b.finish(f'Map_Spore{k + 1}', (0, 0, 0), MAT)


objs = [stem()] + [cap(k) for k in range(4)] + glow_cluster() + house() + [log(), spore(0), spore(1)]
save_meta(HERE.parent / 'game')
print('triangles:', {o.name: len(o.data.polygons) for o in objs})
if 'nofbx' not in ARGS:
    print('wrote', blib.export(objs, OUT / 'RainingEggsMushroom.fbx'))

# ---------------------------------------------------------------- preview scene
sc, cam = scene_setup(sky=(0.62, 0.66, 0.95, 1), ground=(0.2, 0.15, 0.42, 1))
for o in objs:
    o.hide_render = True
by = {o.name: o for o in objs}
glow = glow_material(4)
road = B()
rbox(road, (0, 0.05, 40), (18, 0.1, 240), (196, 176, 236), 0)
road.finish('Road', (0, 0, 0), MAT)
blib.META.pop('Road', None)


def put(name, pos, yaw=0, s=1.0, sv=None):
    o = place(by[name], name + '_p', pos, yaw, s)
    if sv:
        o.scale = (sv[0], sv[2], sv[1])
    if 'Neon' in name or 'Spore' in name:
        o.data = o.data.copy()
        o.data.materials.clear()
        o.data.materials.append(glow)
    return o


put('Map_MushHouse', (40, 0, 60))
put('Map_MushHouseNeon', (40, 0, 60))
for k, (x, z, h, d) in enumerate(((-34, 30, 14, 18), (-60, 76, 22, 24), (-20, 96, 10, 13), (70, 6, 12, 15), (-74, 6, 18, 20))):
    put('Map_MushStem', (x, 0, z), sv=(d / 10, h / 10, d / 10))
    put(f'Map_MushCap{k % 4 + 1}', (x, h, z), k * 40, d / 10)
for k in range(16):
    x, z = R.choice((-1, 1)) * R.uniform(12, 70), R.uniform(-30, 100)
    yy, ss = R.uniform(0, 360), R.uniform(0.8, 1.3)
    put('Map_GlowMush', (x, 0, z), yy, ss)
    put('Map_GlowMushNeon', (x, 0, z), yy, ss)
for x, z, yaw in ((-24, 0, 30), (22, 22, -50), (-46, 52, 80)):
    put('Map_Log', (x, 0, z), yaw)
for k in range(24):
    put(f'Map_Spore{k % 2 + 1}', (R.uniform(-70, 70), R.uniform(6, 34), R.uniform(-20, 100)), 0, R.uniform(0.6, 1.2))
if 'norender' not in ARGS:
    shot(sc, cam, OUT / 'mushroom_scene.png', (-4, 40, -70), (4, 10, 40), (1800, 1000), 28)
    shot(sc, cam, OUT / 'mushroom_house.png', (6, 26, 4), (40, 22, 60), (1400, 1000), 30)
