r"""Raining Eggs, zone 7 (Thunder Peaks) as Blender meshes.

  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P gen_thunder.py   -> out\RainingEggsThunder.fbx + out\thunder_*.png

Meshes (Roblox axes, origin on the ground, front = -Z):
  Map_Peak1, Map_Peak2 (30 wide, 40 tall) + Map_PeakNeon1, Map_PeakNeon2 (glowing veins + tip),
  Map_LightningRod (30 tall, stretch Y) + Map_RodOrb (Neon, centre origin), Map_TeslaTower + Map_TeslaTowerNeon
"""
import bpy, bmesh, math, sys, pathlib, random

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from blib import *          # noqa: F401,F403
import blib

OUT = HERE / 'out'
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
MAT = reset()
R = random.Random(71)
SLATE, METAL, COPPER, YEL = (86, 92, 120), (150, 156, 178), (230, 150, 60), (255, 226, 60)


def peak(k):
    b, n = B(), B()
    rng = random.Random(500 + k)
    rcyl(b, (0, 20, 0), 14, 40, SLATE, segs=7, r2=1.6, yaw=rng.uniform(0, 50))
    rcyl(b, (4, 14, 3), 10, 28, shade(SLATE, 0.92), segs=6, r2=1.2, yaw=rng.uniform(0, 50))
    rcyl(b, (-5, 11, -2), 9, 22, shade(SLATE, 1.08), segs=6, r2=1.0, yaw=rng.uniform(0, 50))
    for j in range(9):                                                       # crags
        a = j * math.tau / 9 + rng.uniform(-0.2, 0.2)
        h = rng.uniform(10, 26)
        r = 15 * (1 - h / 46)
        rcyl(b, (r * 1.05 * math.cos(a), h / 2, r * 1.05 * math.sin(a)), rng.uniform(5, 9), h, shade(SLATE, rng.uniform(0.8, 1.15)), segs=5, r2=0.6, yaw=rng.uniform(0, 70))
    for j in range(7):                                                       # boulders at the foot
        a = rng.uniform(0, math.tau)
        rico(b, (15.5 * math.cos(a), 1.2, 15.5 * math.sin(a)), rng.uniform(1.8, 3.6), shade(SLATE, rng.uniform(0.75, 0.95)), (1, 0.7, 1), 1)
    for j in range(3):                                                       # snow-like pale ledges
        y = 14 + j * 8
        r = 15 * (1 - y / 42) + 0.4
        rcyl(b, (0, y, 0), r, 0.5, (190, 196, 220), segs=7, yaw=j * 20)
    for j in range(4):                                                       # glowing zig-zag veins
        a = j * math.tau / 4 + 0.4
        y, pts = 2, []
        while y < 34:
            r = 15 * (1 - y / 42) + 0.25
            pts.append((r * math.cos(a), y, r * math.sin(a)))
            a += rng.uniform(-0.25, 0.25)
            y += rng.uniform(4, 7)
        for p0, p1 in zip(pts, pts[1:]):
            rbeam(n, p0, p1, 0.45, YEL, 0.02)
    for j in range(5):                                                       # crystal tip
        a = j * math.tau / 5
        rcyl(n, (0.9 * math.cos(a), 39.5, 0.9 * math.sin(a)), 0.7, 4.5, (255, 240, 120), segs=5, r2=0.05, rx=math.degrees(math.sin(a)) * 0.4, rz=math.degrees(math.cos(a)) * 0.4)
    rcyl(n, (0, 40.5, 0), 1.1, 6, (255, 250, 170), segs=5, r2=0.05)
    return [b.finish(f'Map_Peak{k + 1}', (0, 0, 0), MAT), n.finish(f'Map_PeakNeon{k + 1}', (0, 0, 0), MAT)]


def rod():
    b = B()
    rcyl(b, (0, 0.6, 0), 2.6, 1.2, (60, 64, 80), segs=8)
    rcyl(b, (0, 1.6, 0), 1.8, 0.8, (80, 86, 104), segs=8)
    for j in range(4):                                                       # guy wires
        a = j * math.tau / 4 + 0.4
        rbeam(b, (2.4 * math.cos(a), 1.2, 2.4 * math.sin(a)), (0.3 * math.cos(a), 12, 0.3 * math.sin(a)), 0.12, (120, 124, 140), 0)
    rcyl(b, (0, 15.5, 0), 0.5, 27, METAL, segs=8, r2=0.35)
    for j in range(4):                                                       # copper coils
        rcyl(b, (0, 16 + j * 2.2, 0), 1.7 - j * 0.25, 0.7, COPPER, segs=12)
    rcyl(b, (0, 29.3, 0), 0.25, 1.6, METAL, segs=6, r2=0.05)
    return b.finish('Map_LightningRod', (0, 0, 0), MAT)


def rod_orb():
    b = B()
    rico(b, (0, 0, 0), 1.3, (255, 236, 80), (1, 1, 1), 2)
    for j in range(5):
        a = j * math.tau / 5
        rbeam(b, (0, 0, 0), (2.4 * math.cos(a), R.uniform(-1, 1.4), 2.4 * math.sin(a)), 0.18, (255, 250, 180), 0)
    return b.finish('Map_RodOrb', (0, 0, 0), MAT)


def tesla():
    b, n = B(), B()
    rcyl(b, (0, 2, 0), 12, 4, (60, 64, 84), segs=8)
    rcyl(b, (0, 4.4, 0), 9, 0.8, YEL, segs=8)                               # hazard ring
    H = 46
    legs = []
    for j in range(4):                                                       # lattice legs
        a = j * math.tau / 4 + math.pi / 4
        p0, p1 = (7.5 * math.cos(a), 4.8, 7.5 * math.sin(a)), (1.6 * math.cos(a), H, 1.6 * math.sin(a))
        rbeam(b, p0, p1, 1.0, METAL, 0.1)
        legs.append((p0, p1))
    for lvl in range(8):                                                     # cross braces
        t0, t1 = lvl / 8, (lvl + 1) / 8
        for j in range(4):
            (a0, a1), (b0, b1) = legs[j], legs[(j + 1) % 4]
            lerp = lambda p, q, t: tuple(p[i] + (q[i] - p[i]) * t for i in range(3))
            rbeam(b, lerp(a0, a1, t0), lerp(b0, b1, t1), 0.35, shade(METAL, 0.8), 0.03)
            rbeam(b, lerp(b0, b1, t0), lerp(a0, a1, t1), 0.35, shade(METAL, 0.8), 0.03)
            rbeam(b, lerp(a0, a1, t1), lerp(b0, b1, t1), 0.4, shade(METAL, 0.9), 0.03)
    for j in range(5):                                                       # copper coil stack
        rcyl(b, (0, H + 1 + j * 2.6, 0), 6 - j * 1.0, 1.4, COPPER, segs=16)
        rcyl(b, (0, H + 1 + j * 2.6, 0), 6.1 - j * 1.0, 0.3, shade(COPPER, 0.7), segs=16)
    rcyl(b, (0, H + 8, 0), 0.8, 8, METAL, segs=8)
    rico(n, (0, H + 17, 0), 5.5, (255, 240, 110), (1, 1, 1), 2)             # glowing orb
    for j in range(8):                                                       # electric arcs
        a = j * math.tau / 8
        p = (0, H + 17, 0)
        for s in range(3):
            q = (p[0] + 3.2 * math.cos(a) + R.uniform(-1, 1), p[1] + R.uniform(-2.5, 2.5), p[2] + 3.2 * math.sin(a) + R.uniform(-1, 1))
            rbeam(n, p, q, 0.35, (255, 250, 200), 0)
            p = q
    return [b.finish('Map_TeslaTower', (0, 0, 0), MAT), n.finish('Map_TeslaTowerNeon', (0, 0, 0), MAT)]


objs = peak(0) + peak(1) + [rod(), rod_orb()] + tesla()
save_meta(HERE.parent / 'game')
print('triangles:', {o.name: len(o.data.polygons) for o in objs})
if 'nofbx' not in ARGS:
    print('wrote', blib.export(objs, OUT / 'RainingEggsThunder.fbx'))

# ---------------------------------------------------------------- preview scene (storm)
sc, cam = scene_setup(sky=(0.3, 0.32, 0.45, 1), ground=(0.1, 0.11, 0.17, 1))
for o in objs:
    o.hide_render = True
by = {o.name: o for o in objs}
glow = glow_material(5)
road = B()
rbox(road, (0, 0.05, 40), (18, 0.1, 240), (150, 156, 184), 0)
for k in range(10):
    rbox(road, (R.choice((-1, 1)) * R.uniform(14, 60), 0.08, R.uniform(-20, 100)), (R.uniform(6, 14), 0.1, 0.8), YEL, 0, yaw=R.uniform(0, 180))
ro = road.finish('Road', (0, 0, 0), MAT)
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


put('Map_TeslaTower', (48, 0, 66))
put('Map_TeslaTowerNeon', (48, 0, 66), mat=glow)
for k, (x, z, base, h) in enumerate(((-56, 60, 34, 54), (-70, 10, 26, 36), (80, 10, 30, 44), (-30, 110, 30, 60), (90, 104, 24, 30))):
    put(f'Map_Peak{k % 2 + 1}', (x, 0, z), k * 40, sv=(base / 30, h / 40, base / 30))
    put(f'Map_PeakNeon{k % 2 + 1}', (x, 0, z), k * 40, sv=(base / 30, h / 40, base / 30), mat=glow)
for k, (x, z, h) in enumerate(((16, 6, 26), (-18, 30, 34), (20, 44, 22), (-16, 84, 30))):
    put('Map_LightningRod', (x, 0, z), sv=(1, h / 30, 1))
    put('Map_RodOrb', (x, h + 3, z), mat=glow)
if 'norender' not in ARGS:
    shot(sc, cam, OUT / 'thunder_scene.png', (4, 44, -64), (0, 14, 50), (1800, 1000), 26)
    shot(sc, cam, OUT / 'thunder_tesla.png', (14, 46, 10), (48, 42, 66), (1200, 1000), 28)
