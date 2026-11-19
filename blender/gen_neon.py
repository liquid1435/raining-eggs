r"""Raining Eggs, zone 8 (Neon City) as Blender meshes.

  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P gen_neon.py   -> out\RainingEggsNeon.fbx + out\neon_*.png

Meshes (Roblox axes, origin on the ground, front = -Z):
  Map_Tower1..3 (22 x 60 x 17, stretched per building) + Map_TowerNeon1..5 (strips, one per neon colour),
  Map_NeonLamp + Map_NeonOrb1..5 (centre origin), Map_Arcade + Map_ArcadeNeon1..5, Map_HoverCar + Map_HoverCarNeon1..5,
  Map_HoloArch, Map_HoloEgg (centre origin, transparent), Map_HoloRing (Neon, centre origin)
"""
import bpy, bmesh, math, sys, pathlib, random

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from blib import *          # noqa: F401,F403
import blib

OUT = HERE / 'out'
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
MAT = reset()
R = random.Random(81)
NEON = [(60, 240, 255), (255, 70, 200), (160, 110, 255), (120, 255, 140), (255, 220, 60)]
DARK, DARK2, GLASS = (34, 36, 58), (48, 50, 78), (70, 90, 140)


def tower(k):
    b = B()
    rng = random.Random(900 + k)
    W, H, D = 22, 60, 17
    rbox(b, (0, H / 2, 0), (W, H, D), (DARK[0] + k * 6, DARK[1] + k * 6, DARK[2] + k * 8), 0.3)
    for y in range(4, H - 4, 4):                                              # windows on 4 sides
        for x in range(-8, 9, 4):
            lit = rng.random() < 0.45
            c = (255, 230, 150) if lit else GLASS
            rbox(b, (x, y + 1.5, -D / 2 - 0.05), (2.6, 2.4, 0.2), c, 0)
            rbox(b, (x, y + 1.5, D / 2 + 0.05), (2.6, 2.4, 0.2), (255, 230, 150) if rng.random() < 0.45 else GLASS, 0)
        for z in range(-6, 7, 4):
            for sx in (-1, 1):
                rbox(b, (sx * (W / 2 + 0.05), y + 1.5, z), (0.2, 2.4, 2.6), (255, 230, 150) if rng.random() < 0.4 else GLASS, 0)
    for y in (0.8, H * 0.33, H * 0.66):                                       # ledges
        rbox(b, (0, y, 0), (W + 0.8, 0.8, D + 0.8), DARK2, 0.1)
    rbox(b, (0, H + 0.6, 0), (W + 1, 1.2, D + 1), DARK2, 0.15)                 # roof
    if k == 0:
        rcyl(b, (0, H + 6, 0), 0.4, 10, (140, 150, 180), segs=6)
        rball(b, (0, H + 11.4, 0), 0.7, (255, 80, 80), segs=8, rings=5)
    elif k == 1:
        rcyl(b, (5, H + 4, 3), 2.6, 5, (90, 90, 110), segs=10)
        for sx in (-1, 1):
            rbox(b, (5 + sx * 1.8, H + 1.8, 3), (0.4, 3, 0.4), (90, 90, 110), 0)
        rbox(b, (-5, H + 2.2, -2), (5, 2.2, 4), (110, 114, 130), 0.2)
    else:
        rbox(b, (0, H + 4, 0), (12, 7, 9), DARK2, 0.3)
        rcyl(b, (0, H + 10, 0), 3, 5, DARK2, segs=6, r2=0.4)
    rbox(b, (0, 4, -D / 2 - 0.3), (8, 7, 0.6), GLASS, 0.1)                    # entrance
    rbox(b, (0, 8, -D / 2 - 1.6), (10, 0.5, 3), DARK2, 0.08)
    return b.finish(f'Map_Tower{k + 1}', (0, 0, 0), MAT)


def tower_neon(k):
    n = B()
    c = NEON[k]
    W, H, D = 22, 60, 17
    for y in (H * 0.33 + 0.9, H * 0.66 + 0.9):
        rbox(n, (0, y, -D / 2 - 0.45), (W + 0.6, 0.35, 0.2), c, 0)
        for sx in (-1, 1):
            rbox(n, (sx * (W / 2 + 0.45), y, 0), (0.2, 0.35, D + 0.6), c, 0)
    for sx in (-1, 1):                                                        # vertical edge strips
        for sz in (-1, 1):
            rbox(n, (sx * (W / 2 + 0.2), H / 2, sz * (D / 2 + 0.2)), (0.35, H - 2, 0.35), c, 0)
    rbox(n, (0, H + 1.3, -D / 2 - 0.55), (W + 1, 0.3, 0.2), c, 0)
    rbox(n, (0, 8.4, -D / 2 - 3.15), (10, 0.25, 0.2), c, 0)
    return n.finish(f'Map_TowerNeon{k + 1}', (0, 0, 0), MAT)


def lamp():
    b = B()
    rcyl(b, (0, 0.4, 0), 1.2, 0.8, (60, 64, 90), segs=8)
    rcyl(b, (0, 7, 0), 0.35, 13, (60, 64, 90), segs=8, r2=0.25)
    rtube(b, (0, 13.4, 0), (0, 14.4, -1.2), 0.25, (60, 64, 90), 6)
    rcyl(b, (0, 14.3, -1.2), 1.4, 0.4, (60, 64, 90), segs=8)
    return b.finish('Map_NeonLamp', (0, 0, 0), MAT)


def orb(k):
    b = B()
    rico(b, (0, 0, 0), 1.3, NEON[k], (1, 0.8, 1), 2)
    return b.finish(f'Map_NeonOrb{k + 1}', (0, 0, 0), MAT)


def arcade():
    b = B()
    rbox(b, (0, 2.6, 0), (4, 5.2, 3.4), (50, 52, 80), 0.2)
    rbox(b, (0, 5.2, -0.5), (4, 2.6, 2.4), (50, 52, 80), 0.2, rx=-20)
    rbox(b, (0, 6.9, 0), (4.4, 1.4, 3.6), (40, 42, 64), 0.15)
    rbox(b, (0, 3.9, -1.9), (3.8, 0.6, 1.2), (70, 74, 110), 0.1, rx=15)        # control deck
    rcyl(b, (-0.9, 4.4, -2.1), 0.15, 0.8, INK, segs=6)
    rball(b, (-0.9, 4.85, -2.1), 0.32, (240, 60, 60), segs=8, rings=5)
    for j, c in enumerate(((255, 220, 60), (60, 200, 255), (120, 255, 140))):
        rcyl(b, (0.3 + j * 0.6, 4.25, -2.15), 0.22, 0.2, c, segs=8)
    rbox(b, (0, 1.2, -1.72), (1.6, 1.0, 0.1), (30, 30, 40), 0.02)             # coin slot
    for sx in (-1, 1):
        rbox(b, (sx * 2.05, 3.6, 0), (0.12, 6.2, 3.2), (230, 80, 200), 0.02)    # side art stripe
    return b.finish('Map_Arcade', (0, 0, 0), MAT)


def arcade_neon(k):
    n = B()
    c = NEON[k]
    rbox(n, (0, 5.3, -1.75), (3.0, 2.0, 0.2), c, 0.04, rx=-20)                # screen
    rbox(n, (0, 6.9, -1.85), (3.8, 1.0, 0.2), mix(c, (255, 255, 255), 0.3), 0.03)   # marquee
    return n.finish(f'Map_ArcadeNeon{k + 1}', (0, 0, 0), MAT)


def hover_car():
    b = B()
    rbox(b, (0, 0.8, 0), (5, 1.6, 10), (70, 74, 104), 0.5)
    rbox(b, (0, 2.1, 0.6), (4, 1.4, 5), (150, 220, 255), 0.5)
    rbox(b, (0, 1.0, -5.1), (4.4, 0.5, 0.3), (255, 240, 200), 0.05)          # headlights strip
    rbox(b, (0, 1.0, 5.1), (4.4, 0.5, 0.3), (255, 60, 60), 0.05)
    for sx in (-1, 1):
        rbox(b, (sx * 3.0, 0.6, 2.6), (1.2, 0.5, 3), (60, 64, 90), 0.15)     # side fins
    return b.finish('Map_HoverCar', (0, 0, 0), MAT)


def hover_neon(k):
    n = B()
    rbox(n, (0, -0.15, 0), (5.2, 0.3, 10.2), NEON[k], 0.1)
    for sx in (-1, 1):
        rbox(n, (sx * 2.55, 0.9, 0), (0.15, 0.25, 9.4), NEON[k], 0)
    return n.finish(f'Map_HoverCarNeon{k + 1}', (0, 0, 0), MAT)


def holo():
    a, e, r = B(), B(), B()
    for sx in (-1, 1):
        x = sx * 16
        rbox(a, (x, 15, 0), (4, 30, 4), (50, 52, 80), 0.3)
        for y in range(4, 28, 6):
            rbox(a, (x, y, 0), (4.4, 0.6, 4.4), (70, 74, 110), 0.1)
        rbox(a, (x, 0.6, 0), (6, 1.2, 6), (40, 42, 64), 0.2)
    rbox(a, (0, 31, 0), (37, 2, 4), (50, 52, 80), 0.3)
    rcyl(a, (0, 33, 0), 3, 2, (70, 74, 110), segs=10)                       # projector
    rcyl(a, (0, 34.4, 0), 1.6, 1, (60, 240, 255), segs=10)
    vs = bmesh.ops.create_uvsphere(e.bm, u_segments=24, v_segments=14, radius=1, matrix=M((0, 0, 0)))['verts']
    for v in vs:                                                              # egg shape: wider at the bottom
        z = v.co.z
        k = 1.0 - 0.18 * z
        v.co.x *= 8.5 * k
        v.co.y *= 8.5 * k
        v.co.z *= 10.5
    e.paint(vs, (90, 245, 255))
    for j in range(7):                                                        # scan lines
        y = -8 + j * 2.6
        rr = 8.5 * math.sqrt(max(0.05, 1 - (y / 10.5) ** 2)) * (1.0 - 0.18 * y / 10.5) + 0.1
        rcyl(e, (0, y, 0), rr, 0.25, (200, 255, 255), segs=24)
    rcyl(r, (0, 0, 0), 15, 0.8, (255, 70, 200), axis='Z', segs=36)
    rcyl(r, (0, 0, 0), 13.6, 0.82, (40, 20, 60), axis='Z', segs=36)
    return [a.finish('Map_HoloArch', (0, 0, 0), MAT), e.finish('Map_HoloEgg', (0, 0, 0), MAT), r.finish('Map_HoloRing', (0, 0, 0), MAT)]


objs = [tower(k) for k in range(3)] + [tower_neon(k) for k in range(5)] + [lamp()] + [orb(k) for k in range(5)] + [arcade()] + \
       [arcade_neon(k) for k in range(5)] + [hover_car()] + [hover_neon(k) for k in range(5)] + holo()
save_meta(HERE.parent / 'game')
print('triangles:', {o.name: len(o.data.polygons) for o in objs})
if 'nofbx' not in ARGS:
    print('wrote', blib.export(objs, OUT / 'RainingEggsNeon.fbx'))

# ---------------------------------------------------------------- preview scene (night)
sc, cam = scene_setup(sky=(0.05, 0.05, 0.14, 1), ground=(0.04, 0.045, 0.08, 1))
for o in objs:
    o.hide_render = True
by = {o.name: o for o in objs}
glow = glow_material(5)
holo_m = bpy.data.materials.new('Holo')
holo_m.use_nodes = True
pb = holo_m.node_tree.nodes['Principled BSDF']
pb.inputs['Base Color'].default_value = (0.3, 0.9, 1, 1)
pb.inputs['Emission Color'].default_value = (0.3, 0.9, 1, 1)
pb.inputs['Emission Strength'].default_value = 1.5
pb.inputs['Alpha'].default_value = 0.5
road = B()
rbox(road, (0, 0.05, 40), (18, 0.1, 240), (70, 74, 100), 0)
ro = road.finish('Road', (0, 0, 0), MAT)
grid = B()
for z in range(-20, 120, 20):
    for sx in (-1, 1):
        rbox(grid, (sx * 60, 0.07, z), (100, 0.1, 0.5), NEON[(z // 20) % 2], 0)
gr = grid.finish('Grid', (0, 0, 0), MAT)
gr.data.materials.clear()
gr.data.materials.append(glow)
for k in ('Road', 'Grid'):
    blib.META.pop(k, None)


def put(name, pos, yaw=0, s=1.0, sv=None, mat=None):
    o = place(by[name], name + '_p', pos, yaw, s)
    if sv:
        o.scale = (sv[0], sv[2], sv[1])
    if mat:
        o.data = o.data.copy()
        o.data.materials.clear()
        o.data.materials.append(mat)
    return o


j = 0
for sx in (-1, 1):
    for z in (10, 40, 70, 100):
        for row, x in enumerate((32, 62)):
            w, d, h = R.uniform(18, 26), R.uniform(14, 20), R.uniform(26, 50) + row * 22
            sv = (w / 22, h / 60, d / 17)
            put(f'Map_Tower{j % 3 + 1}', (sx * x, 0, z), 90 * -sx, sv=sv)
            put(f'Map_TowerNeon{j % 5 + 1}', (sx * x, 0, z), 90 * -sx, sv=sv, mat=glow)
            j += 1
for k, z in enumerate((0, 24, 48, 80)):
    for sx in (-1, 1):
        put('Map_NeonLamp', (sx * 13, 0, z), 90 * sx)
        put(f'Map_NeonOrb{(k + sx) % 5 + 1}', (sx * 13, 13.6, z - 0), mat=glow)
for k, (x, z) in enumerate(((-17, 14), (-17, 20), (18, 58), (18, 64))):
    put('Map_Arcade', (x, 0, z), 90 if x < 0 else -90)
    put(f'Map_ArcadeNeon{k + 1}', (x, 0, z), 90 if x < 0 else -90, mat=glow)
for k in range(5):
    x, y, z, yy = R.uniform(-40, 40), R.uniform(24, 46), R.uniform(10, 100), R.uniform(0, 360)
    put('Map_HoverCar', (x, y, z), yy)
    put(f'Map_HoverCarNeon{k + 1}', (x, y, z), yy, mat=glow)
put('Map_HoloArch', (0, 0, 76))
put('Map_HoloEgg', (0, 45, 76), mat=holo_m)
put('Map_HoloRing', (0, 45, 76), mat=glow)
if 'norender' not in ARGS:
    shot(sc, cam, OUT / 'neon_scene.png', (0, 30, -40), (0, 24, 60), (1800, 1000), 24)
