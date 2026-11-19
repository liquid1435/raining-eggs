r"""Raining Eggs, zone 9 (Cloud Kingdom) as Blender meshes.

  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P gen_cloud.py   -> out\RainingEggsCloud.fbx + out\cloud_*.png

Meshes (Roblox axes, origin on the ground, front = -Z):
  Map_Rainbow (radius 74 arc in the X-Y plane), Map_Puff1, Map_Puff2, Map_Pillar (20 tall) + Map_PillarOrb (Neon, centre),
  Map_SkyCastle, Map_CloudStep (14 x 3 x 11, centre origin), Map_Star (Neon, centre)
"""
import bpy, bmesh, math, sys, pathlib, random

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from blib import *          # noqa: F401,F403
import blib

OUT = HERE / 'out'
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
MAT = reset()
R = random.Random(91)
RB = [(244, 70, 70), (255, 150, 40), (255, 222, 50), (90, 210, 90), (70, 150, 250), (160, 100, 250)]
CLOUD, CLOUD2, MARBLE, BLUE = (250, 252, 255), (226, 236, 255), (246, 246, 250), (90, 150, 250)


def puff_cluster(b, centre, s, rng, n=6, segs=14):
    x0, y0, z0 = centre
    for j in range(n):
        a = j * math.tau / n + rng.uniform(-0.3, 0.3)
        r = s * rng.uniform(0.35, 0.6)
        d = s * rng.uniform(0.25, 0.55)
        rball(b, (x0 + d * math.cos(a), y0 + r * 0.25, z0 + d * math.sin(a)), r, CLOUD if j % 2 else CLOUD2, (1, 0.8, 1), segs, segs // 2 + 1)
    rball(b, (x0, y0 + s * 0.35, z0), s * 0.55, CLOUD, (1, 0.85, 1), segs + 2, segs // 2 + 2)


def rainbow():
    b = B()
    n = 40
    for bi, col in enumerate(RB):
        r = 74 - bi * 3.2
        for k in range(n):
            a0, a1 = k * math.pi / n, (k + 1) * math.pi / n
            p0 = (r * math.cos(a0), r * math.sin(a0) - 2, 0)
            p1 = (r * math.cos(a1), r * math.sin(a1) - 2, 0)
            rplank(b, p0, p1, 4, 3.3, col, 0)
    rng = random.Random(3)
    for sx in (-1, 1):                                                        # clouds at both feet
        puff_cluster(b, (sx * 66, 0, 0), 16, rng, 7)
    return b.finish('Map_Rainbow', (0, 0, 0), MAT)


def puff(k):
    b = B()
    puff_cluster(b, (0, 0, 0), 9, random.Random(10 + k), 6 + k)
    return b.finish(f'Map_Puff{k + 1}', (0, 0, 0), MAT)


def pillar():
    b = B()
    rbox(b, (0, 0.5, 0), (7, 1, 7), GOLD, 0.15)
    rcyl(b, (0, 1.4, 0), 3.2, 0.8, GOLD, segs=16)
    rcyl(b, (0, 11, 0), 1.8, 18.4, MARBLE, segs=16)
    for j in range(12):                                                       # flutes
        a = j * math.tau / 12
        rbox(b, (1.8 * math.cos(a), 11, 1.8 * math.sin(a)), (0.25, 17.6, 0.25), shade(MARBLE, 0.88), 0, yaw=-math.degrees(a))
    rcyl(b, (0, 20.4, 0), 2.6, 0.8, GOLD, segs=16)
    rbox(b, (0, 21.3, 0), (6, 1, 6), GOLD, 0.15)
    for sx in (-1, 1):                                                        # ionic scrolls
        rcyl(b, (sx * 2.8, 20.5, 0), 0.9, 6, GOLD, axis='Z', segs=12)
        rcyl(b, (sx * 3.1, 20.5, 0), 0.45, 6.1, shade(GOLD, 0.8), axis='Z', segs=10)
    rcyl(b, (0, 22.2, 0), 1.0, 0.8, GOLD, segs=12)
    return b.finish('Map_Pillar', (0, 0, 0), MAT)


def pillar_orb():
    b = B()
    rico(b, (0, 0, 0), 1.3, (255, 240, 130), (1, 1, 1), 2)
    return b.finish('Map_PillarOrb', (0, 0, 0), MAT)


def castle():
    b = B()
    rng = random.Random(5)
    for j in range(12):                                                       # cloud bank under it
        puff_cluster(b, (rng.uniform(-26, 26), -1, rng.uniform(-17, 17)), rng.uniform(8, 13), rng, 4, 8)
    rbox(b, (0, 8, 0), (46, 16, 30), MARBLE, 0.3)
    for y in (5, 11):
        rbox(b, (0, y, -15.05), (45, 0.3, 0.15), shade(MARBLE, 0.9), 0)
    for k in range(8):                                                        # crenellations
        rbox(b, (-20 + k * 5.8, 17.5, -14), (3, 3, 2.6), MARBLE, 0.15)
        rbox(b, (-20 + k * 5.8, 17.5, 14), (3, 3, 2.6), MARBLE, 0.15)
    rbox(b, (0, 6, -15.2), (10, 12, 0.8), GOLD, 0.2)                          # golden gate
    rcyl(b, (0, 12, -15.2), 5, 0.8, GOLD, axis='Z', segs=16)
    rbox(b, (0, 5.4, -15.5), (7.4, 10.8, 0.4), (120, 170, 255), 0.1)
    rcyl(b, (0, 10.8, -15.5), 3.7, 0.4, (120, 170, 255), axis='Z', segs=14)
    for j in range(5):
        rbox(b, (-3 + j * 1.5, 6.4, -15.75), (0.25, 10, 0.2), GOLD, 0)
    for k in range(4):                                                        # stairs
        rbox(b, (0, 0.3 + k * 0.6, -19.5 + k * 1.2), (12 - k, 0.6, 2.2), MARBLE, 0.1)
    for wx in (-15, -8, 8, 15):                                               # arched windows
        rbox(b, (wx, 9, -15.1), (2.6, 4.4, 0.3), BLUE, 0.05)
        rcyl(b, (wx, 11.2, -15.1), 1.3, 0.3, BLUE, axis='Z', segs=10)
    for tx, tz, th in ((-23, -6, 34), (23, -6, 34), (0, 6, 46)):              # towers
        rcyl(b, (tx, th / 2, tz), 6, th, MARBLE, segs=14)
        rcyl(b, (tx, th + 0.6, tz), 6.8, 1.2, shade(MARBLE, 0.92), segs=14)
        for j in range(10):
            a = j * math.tau / 10
            rbox(b, (tx + 6.3 * math.cos(a), th + 2, tz + 6.3 * math.sin(a)), (1.6, 2, 1.4), MARBLE, 0.1, yaw=-math.degrees(a))
        rcyl(b, (tx, th + 9, tz), 6.4, 12, BLUE, segs=14, r2=0.3)
        for j in range(3):
            rcyl(b, (tx, th * (0.35 + j * 0.2), tz - 6.0), 0.9, 0.3, BLUE, axis='Z', segs=10)
        rball(b, (tx, th + 15.6, tz), 1.2, GOLD, segs=10, rings=6)
        rcyl(b, (tx, th + 18, tz), 0.15, 4, INK, segs=4)
        rplank(b, (tx, th + 19.6, tz), (tx + 3.4, th + 19, tz), 1.6, 0.1, (255, 110, 170), 0)   # flag
    return b.finish('Map_SkyCastle', (0, 0, 0), MAT)


def cloud_step():
    b = B()
    rng = random.Random(8)
    rbox(b, (0, 0, 0), (12, 2.4, 9), CLOUD, 1.0)
    for j in range(9):
        a = j * math.tau / 9
        rball(b, (6 * math.cos(a), rng.uniform(-0.4, 0.4), 4.6 * math.sin(a)), rng.uniform(1.6, 2.4), CLOUD2 if j % 2 else CLOUD, (1, 0.7, 1), 12, 7)
    for j in range(3):
        rball(b, (rng.uniform(-3, 3), 1.4, rng.uniform(-2, 2)), rng.uniform(1.8, 2.6), CLOUD, (1, 0.6, 1), 12, 7)
    return b.finish('Map_CloudStep', (0, 0, 0), MAT)


def star():
    b = B()
    pts = []
    for j in range(10):
        a = math.pi / 2 + j * math.pi / 5
        r = 1.2 if j % 2 == 0 else 0.5
        pts.append((r * math.cos(a), r * math.sin(a)))
    bm = b.bm
    for z in (-0.25, 0.25):
        pass
    front = [bm.verts.new((x, 0.25, y)) for x, y in pts]
    back = [bm.verts.new((x, -0.25, y)) for x, y in pts]
    cf, cb = bm.verts.new((0, 0.45, 0)), bm.verts.new((0, -0.45, 0))
    for j in range(10):
        k = (j + 1) % 10
        bm.faces.new((cf, front[j], front[k]))
        bm.faces.new((cb, back[k], back[j]))
        bm.faces.new((front[j], back[j], back[k], front[k]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    b.paint(front + back + [cf, cb], (255, 236, 110))
    return b.finish('Map_Star', (0, 0, 0), MAT)


objs = [rainbow(), puff(0), puff(1), pillar(), pillar_orb(), castle(), cloud_step(), star()]
save_meta(HERE.parent / 'game')
print('triangles:', {o.name: len(o.data.polygons) for o in objs})
if 'nofbx' not in ARGS:
    print('wrote', blib.export(objs, OUT / 'RainingEggsCloud.fbx'))

# ---------------------------------------------------------------- preview scene
sc, cam = scene_setup(sky=(0.62, 0.8, 1.0, 1), ground=(0.92, 0.95, 1.0, 1))
for o in objs:
    o.hide_render = True
by = {o.name: o for o in objs}
glow = glow_material(4)
road = B()
rbox(road, (0, 0.05, 40), (18, 0.1, 240), (255, 236, 170), 0)
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


put('Map_Rainbow', (0, 0, 40), 0, 0.8)
put('Map_SkyCastle', (-52, 0, 82), 15)
for k, (x, z, h) in enumerate(((16, 0, 14), (-16, 16, 20), (18, 56, 26), (-18, 70, 14), (40, 30, 20))):
    put('Map_Pillar', (x, 0, z), 0, sv=(1, h / 20, 1))
    put('Map_PillarOrb', (x, h * 1.12 + 3, z), mat=glow)
for k in range(10):
    put(f'Map_Puff{k % 2 + 1}', (R.choice((-1, 1)) * R.uniform(20, 80), 0, R.uniform(-10, 110)), R.uniform(0, 360), R.uniform(0.8, 1.6))
for k in range(4):
    put('Map_CloudStep', (R.uniform(20, 60), R.uniform(12, 30), R.uniform(10, 90)), R.uniform(0, 90))
for k in range(16):
    put('Map_Star', (R.uniform(-80, 80), R.uniform(20, 60), R.uniform(0, 110)), 0, 1.4, mat=glow)
if 'norender' not in ARGS:
    shot(sc, cam, OUT / 'cloud_scene.png', (4, 40, -66), (0, 20, 50), (1800, 1000), 24)
    shot(sc, cam, OUT / 'cloud_castle.png', (-14, 36, 28), (-52, 24, 82), (1400, 1000), 30)
