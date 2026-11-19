r"""Raining Eggs, zone 1 (Sunny Meadow) + plaza greenery as Blender meshes.

  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P gen_meadow.py   -> out\RainingEggsMeadow.fbx + out\meadow_*.png

Meshes (Roblox axes, origin on the ground at the model centre, front = -Z):
  Map_Windmill, Map_WindmillBlades (turned by the game client), Map_Barn, Map_Pond, Map_PondWater (transparent in game),
  Map_TreeRound, Map_TreeFruit, Map_TreePine, Map_Rock1, Map_Rock2, Map_HayBale, Map_Flowers1, Map_Flowers2, Map_FenceWhite
"""
import bpy, bmesh, math, sys, pathlib, random
from mathutils import Vector

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from blib import *          # noqa: F401,F403
import blib

OUT = HERE / 'out'
OUT.mkdir(exist_ok=True)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
MAT = reset()
R = random.Random(7)

STONE, BARK, LEAF, PINE = (172, 166, 156), (128, 84, 52), (74, 176, 70), (46, 138, 84)
SAND, WATER, DEEP = (236, 220, 170), (80, 178, 238), (36, 104, 176)
RED, REDDK, ROOF = (206, 60, 52), (160, 42, 38), (118, 52, 46)


def prism(b, pts, z0, z1, c):
    """flat shape (points in Roblox x-y) pushed from z0 to z1"""
    bm = b.bm
    front = [bm.verts.new((x, -z0, y)) for x, y in pts]
    back = [bm.verts.new((x, -z1, y)) for x, y in pts]
    faces = [bm.faces.new(front), bm.faces.new(list(reversed(back)))]
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        faces.append(bm.faces.new((front[i], back[i], back[j], front[j])))
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    b.paint(front + back, c)


def panel(b, p0, p1, depth, z, c, thick=0.7, strips=0, strip_col=None):
    """roof board from p0 to p1 (Roblox x-y), depth along z; optional raised shingle strips"""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    a = math.degrees(math.atan2(y1 - y0, x1 - x0))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rbox(b, (cx, cy, z), (L, thick, depth), c, 0.12, rz=a)
    nx, ny = -math.sin(math.radians(a)), math.cos(math.radians(a))
    for k in range(strips):
        t = -L / 2 + L * (k + 0.5) / strips
        ux, uy = math.cos(math.radians(a)), math.sin(math.radians(a))
        rbox(b, (cx + ux * t + nx * thick * 0.55, cy + uy * t + ny * thick * 0.55, z), (L / strips * 0.86, 0.22, depth - 0.2), strip_col or shade(c, 1.15), 0.06, rz=a)


def window(b, pos, yaw=0.0, w=2.4, h=3.0):
    x, y, z = pos
    rbox(b, (x, y, z), (w, h, 0.5), WHITE, 0.08, yaw=yaw)
    rbox(b, (x, y, z), (w - 0.6, h - 0.6, 0.56), (78, 120, 180), 0.04, yaw=yaw)
    rbox(b, (x, y, z), (0.2, h - 0.6, 0.6), WHITE, 0, yaw=yaw)
    rbox(b, (x, y, z), (w - 0.6, 0.2, 0.6), WHITE, 0, yaw=yaw)
    rbox(b, (x, y - h / 2 - 0.15, z), (w + 0.4, 0.3, 0.8), WHITE, 0.05, yaw=yaw)


# ---------------------------------------------------------------- windmill
def windmill():
    b = B()
    rcyl(b, (0, 1.5, 0), 8.8, 3, STONE, segs=8)
    for k in range(16):                                        # stone blocks around the base
        a = k * math.tau / 16
        rbox(b, (8.5 * math.sin(a), 1.5 + (0.75 if k % 2 else -0.75), -8.5 * math.cos(a)), (2.6, 1.3, 0.6), shade(STONE, R.uniform(0.85, 1.1)), 0.15, yaw=math.degrees(a))
    rad = lambda y: 7.6 - (y - 3) / 31 * 2.4
    rcyl(b, (0, 18.5, 0), 7.6, 31, CREAM, segs=8, r2=5.2)
    for y in (11, 19):
        rcyl(b, (0, y, 0), rad(y) + 0.3, 0.7, (160, 112, 70), segs=8)
    for y, angs in ((13, (90, -90, 180)), (21, (0, 90, -90))):
        for a in angs:
            r = rad(y) + 0.05
            window(b, (r * math.sin(math.radians(a)), y, -r * math.cos(math.radians(a))), yaw=-a)
    # door, arch and steps
    rbox(b, (0, 4.6, -8.75), (4.8, 6.2, 0.6), WHITE, 0.1)
    rcyl(b, (0, 7.7, -8.75), 2.4, 0.6, WHITE, axis='Z', segs=12)
    rbox(b, (0, 4.4, -8.95), (3.8, 5.6, 0.5), WOOD, 0.06)
    rcyl(b, (0, 7.2, -8.95), 1.9, 0.5, WOOD, axis='Z', segs=12)
    for k in range(4):
        rbox(b, (-1.35 + k * 0.9, 4.6, -9.22), (0.12, 5.4, 0.1), WOOD2, 0)
    rball(b, (1.2, 4.4, -9.3), 0.22, GOLD, segs=6, rings=4)
    rbox(b, (0, 0.3, -10.4), (6, 0.6, 2.4), STONE, 0.12)
    # balcony
    rcyl(b, (0, 25, 0), 7.6, 0.6, WOOD, segs=12)
    for k in range(16):
        a = k * math.tau / 16
        rbox(b, (7.2 * math.sin(a), 26.2, -7.2 * math.cos(a)), (0.3, 1.8, 0.3), WOOD2, 0.04)
        a2 = a + math.tau / 32
        rbox(b, (7.15 * math.sin(a2), 27.1, -7.15 * math.cos(a2)), (2.9, 0.28, 0.28), WOOD2, 0.04, yaw=-math.degrees(a2))
    # cap
    rcyl(b, (0, 34.3, 0), 6.5, 0.8, REDDK, segs=8)
    rcyl(b, (0, 38.6, 0), 6.3, 8, RED, segs=8, r2=0.7)
    for k in range(8):                                         # ridges on the cap
        a = (k + 0.5) * math.tau / 8
        rbeam(b, (6.35 * math.sin(a), 34.7, -6.35 * math.cos(a)), (0.75 * math.sin(a), 42.5, -0.75 * math.cos(a)), 0.4, REDDK)
    rcyl(b, (0, 43.4, 0), 0.25, 2, WOOD2, segs=6)
    rball(b, (0, 44.6, 0), 0.6, GOLD, segs=8, rings=6)
    rcyl(b, (0, 31, -6.6), 0.7, 3.4, WOOD2, axis='Z', segs=8)          # shaft out to the hub
    body = b.finish('Map_Windmill', (0, 0, 0), MAT)

    s = B()                                                    # blades: centred on the hub so they can spin
    hub = (0, 31, -8.6)
    rcyl(s, hub, 1.5, 1.4, RED, axis='Z', segs=12)
    rball(s, (0, 31, -9.4), 0.8, WHITE, segs=8, rings=6)
    for k in range(4):
        a = math.radians(20 + k * 90)
        ux, uy = -math.sin(a), math.cos(a)
        vx, vy = math.cos(a), math.sin(a)
        rz = math.degrees(a)
        rbox(s, (hub[0] + ux * 8.4, hub[1] + uy * 8.4, hub[2]), (0.8, 15.6, 0.5), WOOD2, 0.08, rz=rz)
        for t in (5, 15.2):
            rbox(s, (hub[0] + ux * t + vx * 1.9, hub[1] + uy * t + vy * 1.9, hub[2] - 0.05), (3.6, 0.3, 0.4), WOOD, 0.04, rz=rz)
        rbox(s, (hub[0] + ux * 10.1 + vx * 3.6, hub[1] + uy * 10.1 + vy * 3.6, hub[2] - 0.05), (0.3, 10.5, 0.4), WOOD, 0.04, rz=rz)
        rbox(s, (hub[0] + ux * 10.1 + vx * 1.9, hub[1] + uy * 10.1 + vy * 1.9, hub[2] + 0.05), (3.2, 10, 0.18), (250, 246, 236), 0.03, rz=rz)
        for t in (7.6, 10.1, 12.6):
            rbox(s, (hub[0] + ux * t + vx * 1.9, hub[1] + uy * t + vy * 1.9, hub[2] - 0.1), (3.3, 0.2, 0.3), WOOD, 0, rz=rz)
    blades = s.finish('Map_WindmillBlades', (0, 0, 0), MAT)
    return [body, blades]


# ---------------------------------------------------------------- barn
def barn():
    b = B()
    rbox(b, (0, 0.5, 0), (31.4, 1, 23.4), STONE, 0.2)
    rbox(b, (0, 7.5, 0), (30, 13, 22), RED, 0.1)
    for x in range(-14, 15, 2):                                # plank grooves front / back
        for z in (-11.05, 11.05):
            rbox(b, (x, 7.5, z), (0.16, 12.6, 0.12), REDDK, 0)
    for z in range(-10, 11, 2):
        for x in (-15.05, 15.05):
            rbox(b, (x, 7.5, z), (0.12, 12.6, 0.16), REDDK, 0)
    for sx in (-1, 1):
        for sz in (-1, 1):
            rbox(b, (sx * 15, 7.6, sz * 11), (1, 13.4, 1), WHITE, 0.1)
    rbox(b, (0, 14.1, 0), (30.8, 0.6, 22.8), WHITE, 0.08)
    gable = [(-15, 14.3), (15, 14.3), (10.2, 21.4), (0, 25.6), (-10.2, 21.4)]
    prism(b, gable, -10.9, 10.9, RED)
    for z in (-11.1, 11.1):                                    # white trim around the gables
        for p0, p1 in zip(gable[1:], gable[2:] + [gable[0]]):
            panel(b, p0, p1, 0.5, z, WHITE, 0.6)
    # gambrel roof with shingle strips
    for sx in (-1, 1):
        panel(b, (sx * 15.9, 13.8), (sx * 10.4, 21.7), 23.8, 0, ROOF, 0.8, 4)
        panel(b, (sx * 10.4, 21.7), (0, 26.0), 23.8, 0, ROOF, 0.8, 4)
    rbox(b, (0, 26.2, 0), (1.2, 0.9, 24.2), WHITE, 0.15)
    # big doors with white X braces
    rbox(b, (0, 6.3, -11.15), (13, 11.2, 0.5), WHITE, 0.1)
    for sx in (-1, 1):
        x = sx * 3
        rbox(b, (x, 6.1, -11.35), (5.7, 10.2, 0.4), REDDK, 0.05)
        for rz in (30.1, -30.1):
            rbox(b, (x, 6.1, -11.6), (0.55, 11.0, 0.3), WHITE, 0.04, rz=rz)
        for y in (1.25, 10.95):
            rbox(b, (x, y, -11.6), (5.7, 0.5, 0.3), WHITE, 0.04)
        rbox(b, (x - sx * 2.6, 6.1, -11.6), (0.5, 10.2, 0.3), WHITE, 0.04)
    rbox(b, (0, 6.1, -11.6), (0.5, 10.2, 0.32), WHITE, 0.04)
    # hayloft door, hay and pulley beam
    rbox(b, (0, 19.0, -11.2), (6.4, 5.4, 0.5), WHITE, 0.08)
    rbox(b, (0, 18.8, -11.3), (5.2, 4.4, 0.5), (60, 40, 30), 0.04)
    for k in range(6):
        rbox(b, (-2 + k * 0.8, 17.4 + R.uniform(0, 0.8), -11.5), (0.9, 1.4, 0.5), (240, 204, 90), 0.08, rz=R.uniform(-20, 20))
    rbox(b, (0, 23.4, -12.6), (0.8, 0.8, 4.2), WOOD2, 0.08)
    rbox(b, (0, 21.6, -14.3), (0.12, 3.4, 0.12), (220, 200, 160), 0)
    rbox(b, (0, 19.8, -14.3), (0.7, 0.5, 0.5), INK, 0.05)
    # side windows, lamp, weathervane, ramp
    for sx in (-1, 1):
        for z in (-5, 5):
            window(b, (sx * 15.15, 8.4, z), yaw=90, w=3.2, h=3.4)
    rbox(b, (7.8, 10.2, -11.5), (0.9, 1.2, 0.9), (255, 214, 110), 0.1)
    rbox(b, (7.8, 10.95, -11.5), (1.2, 0.3, 1.2), INK, 0.05)
    rcyl(b, (0, 27.7, 0), 0.15, 3, INK, segs=6)
    rbox(b, (0, 28.6, 0), (3.6, 0.3, 0.25), INK, 0.03)
    rbox(b, (1.9, 28.6, 0), (0.6, 0.9, 0.2), INK, 0.03, rz=45)
    rball(b, (0, 29.3, 0), 0.4, GOLD, segs=8, rings=5)
    rbox(b, (0, 0.5, -13.2), (12.6, 0.6, 3.4), WOOD, 0.1, rx=8)
    return [b.finish('Map_Barn', (0, 0, 0), MAT)]


# ---------------------------------------------------------------- pond
def pond():
    b, w = B(), B()
    rcyl(b, (0, 0.14, 0), 1, 0.28, SAND, segs=32, scale=(23, 1, 17))
    rcyl(b, (0, 0.16, 0), 1, 0.3, shade(SAND, 0.86), segs=32, scale=(21.2, 1, 15.2))
    rcyl(b, (0, 0.18, 0), 1, 0.3, DEEP, segs=28, scale=(19.6, 1, 13.6))
    rcyl(b, (0, 0.2, 0), 1, 0.3, shade(DEEP, 0.75), segs=24, scale=(13, 1, 8))
    rcyl(w, (0, 0.42, 0), 1, 0.2, WATER, segs=32, scale=(20.2, 1, 14.2))
    for k in range(22):                                        # rocks along the shore (gap for the dock)
        a = k * math.tau / 22 + R.uniform(-0.08, 0.08)
        if abs(math.sin(a)) < 0.3 and math.cos(a) > 0:
            continue
        s = R.uniform(0.9, 2.2)
        x, z = 20.6 * math.cos(a), 14.8 * math.sin(a)
        rico(b, (x, s * 0.35, z), s, shade(STONE, R.uniform(0.82, 1.12)), (1, 0.6, 0.85), 1, yaw=R.uniform(0, 90))
        if R.random() < 0.35:
            rico(b, (x, s * 0.75, z), s * 0.55, (96, 190, 84), (1, 0.3, 1), 1)
    for cx, cz in ((-15, -9), (-6, 12.4), (12, -11.5)):       # reeds and cattails
        for _ in range(7):
            x, z, h = cx + R.uniform(-1.6, 1.6), cz + R.uniform(-1, 1), R.uniform(2.6, 4.6)
            rcyl(b, (x, h / 2, z), 0.12, h, (80, 160, 70), segs=5)
            if R.random() < 0.6:
                rcyl(b, (x, h - 0.4, z), 0.28, 1.1, (130, 84, 50), segs=6)
            else:
                rbox(b, (x + 0.4, h * 0.6, z), (0.18, h * 0.7, 0.4), (110, 190, 80), 0.02, rz=-20)
    for x, z in ((-8, -3), (-3, 5), (5, -6), (-11, 6), (2, 2), (9, 4)):   # lily pads + flowers
        rcyl(b, (x, 0.58, z), 1.3, 0.1, (70, 170, 70), segs=10)
        if R.random() < 0.6:
            for k in range(5):
                a = k * math.tau / 5
                rball(b, (x + 0.35 * math.cos(a), 0.85, z + 0.35 * math.sin(a)), 0.32, (255, 150, 200), (1, 0.6, 1), 6, 4)
            rball(b, (x, 0.95, z), 0.22, (255, 220, 80), segs=6, rings=4)
    # wooden dock on the +X side
    for k in range(12):
        x = 13.4 + k * 0.95
        rbox(b, (x, 1.0, 0), (0.88, 0.34, 4.6), shade(WOOD, R.uniform(0.9, 1.08)), 0.05)
    for x in (13.6, 18.8, 24):
        for z in (-2.1, 2.1):
            rcyl(b, (x, 0.6, z), 0.32, 2.2, WOOD2, segs=6)
    rbox(b, (18.8, 1.35, -2.4), (11.4, 0.3, 0.3), WOOD2, 0.04)
    # ducks
    for x, z, s, c in ((-4, -1, 1.0, WHITE), (-1.6, -2.4, 0.6, (255, 220, 60)), (-2.4, 0.4, 0.6, (255, 220, 60))):
        rball(b, (x, 0.75 * s + 0.3, z), 1.0 * s, c, (1.0, 0.75, 1.35), 10, 7)
        rball(b, (x, 1.6 * s + 0.3, z - 0.9 * s), 0.6 * s, c, segs=8, rings=6)
        rbox(b, (x, 1.5 * s + 0.3, z - 1.55 * s), (0.5 * s, 0.22 * s, 0.6 * s), (255, 150, 40), 0.04)
        for sx in (-1, 1):
            rball(b, (x + sx * 0.32 * s, 1.75 * s + 0.3, z - 1.35 * s), 0.12 * s, INK, segs=6, rings=4)
        rbox(b, (x, 1.0 * s + 0.3, z + 1.25 * s), (0.6 * s, 0.4 * s, 0.6 * s), c, 0.05, rx=-30)
    return [b.finish('Map_Pond', (0, 0, 0), MAT), w.finish('Map_PondWater', (0, 0, 0), MAT)]


# ---------------------------------------------------------------- trees, rocks, hay, flowers, fence
def tree(kind):
    b = B()
    r = random.Random(hash(kind) % 997)
    if kind == 'Pine':
        rcyl(b, (0, 2, 0), 0.9, 4, BARK, segs=7, r2=0.7)
        for k, (rr, h, y) in enumerate(((5.6, 6, 6), (4.6, 5.2, 9.4), (3.5, 4.6, 12.4), (2.3, 4, 15.2))):
            rcyl(b, (0, y, 0), rr, h, shade(PINE, 0.9 + 0.08 * k), segs=8, r2=0.3, yaw=k * 22)
        return [b.finish('Map_TreePine', (0, 0, 0), MAT)]
    for k in range(4):                                         # roots
        a = k * math.tau / 4 + 0.4
        rbox(b, (1.1 * math.cos(a), 0.4, 1.1 * math.sin(a)), (1.6, 0.8, 0.8), shade(BARK, 0.85), 0.15, yaw=-math.degrees(a))
    rcyl(b, (0, 4.5, 0), 1.0, 9, BARK, segs=7, r2=0.7)
    rbox(b, (1.3, 7.2, 0), (2.4, 0.7, 0.7), BARK, 0.1, rz=30)
    rbox(b, (-1.2, 8.2, 0.4), (2.2, 0.6, 0.6), BARK, 0.1, rz=-35)
    blobs = [(0, 12.4, 0, 4.8)] + [(3.6 * math.cos(a), 11.2 + r.uniform(-0.6, 0.8), 3.6 * math.sin(a), r.uniform(2.8, 3.4))
                                    for a in (k * math.tau / 5 + 0.3 for k in range(5))] + [(0.4, 15.8, -0.3, 3.2), (-1.6, 14.6, 1.6, 2.6)]
    for x, y, z, rr in blobs:
        c = shade(LEAF, 0.86 + (y - 10) * 0.05 + r.uniform(-0.04, 0.04))
        rico(b, (x, y, z), rr, c, (1, 0.9, 1), 1, yaw=r.uniform(0, 60))
    if kind == 'Fruit':
        for k in range(10):
            a, yy = r.uniform(0, math.tau), r.uniform(10.5, 15)
            rr = 4.4 if yy < 13 else 3.4
            rball(b, (rr * math.cos(a), yy, rr * math.sin(a)), 0.45, (232, 56, 60), segs=6, rings=5)
    return [b.finish('Map_Tree' + kind, (0, 0, 0), MAT)]


def rock(k):
    b = B()
    r = random.Random(30 + k)
    parts = ((0, 1.1, 0, 2.6, (1.1, 0.75, 0.95)), (1.6, 0.8, 1.1, 1.7, (1, 0.9, 1)), (-1.9, 0.5, 0.8, 1.2, (1, 0.8, 1))) if k == 1 else \
            ((0, 1.6, 0, 2.2, (0.9, 1.3, 0.9)), (1.8, 0.8, -0.6, 1.5, (1, 0.9, 1)), (-1.3, 0.6, 1.4, 1.0, (1, 0.9, 1)))
    for x, y, z, rr, sc in parts:
        rico(b, (x, y, z), rr, shade(STONE, r.uniform(0.85, 1.08)), sc, 1, yaw=r.uniform(0, 90))
    rico(b, (-0.3, parts[0][1] + parts[0][3] * parts[0][4][1] * 0.75, 0.1), 1.3, (96, 190, 84), (1, 0.28, 0.9), 1)
    return [b.finish(f'Map_Rock{k}', (0, 0, 0), MAT)]


def hay():
    b = B()
    rcyl(b, (0, 2.5, 0), 2.5, 5, (238, 200, 90), axis='X', segs=14)
    for sx in (-1, 1):
        rcyl(b, (sx * 2.5, 2.5, 0), 1.8, 0.12, (250, 222, 130), axis='X', segs=14)
        rcyl(b, (sx * 2.56, 2.5, 0), 0.8, 0.12, (214, 170, 70), axis='X', segs=10)
        rcyl(b, (sx * 1.3, 2.5, 0), 2.56, 0.26, (168, 116, 56), axis='X', segs=14)
    for k in range(6):
        rbox(b, (R.uniform(-2, 2), 4.95, R.uniform(-0.8, 0.8)), (0.12, 0.12, 1.4), (250, 222, 130), 0, yaw=R.uniform(0, 180), rx=R.uniform(-15, 15))
    return [b.finish('Map_HayBale', (0, 0, 0), MAT)]


def flowers(k):
    b = B()
    r = random.Random(50 + k)
    cols = [(255, 90, 90), (255, 214, 50), WHITE, (255, 120, 190), (130, 120, 255)]
    for _ in range(9):                                         # grass tufts
        rbox(b, (r.uniform(-2, 2), 0.6, r.uniform(-2, 2)), (0.25, r.uniform(0.9, 1.6), 0.25), (90, 180, 70), 0.02, rz=r.uniform(-20, 20), yaw=r.uniform(0, 90))
    for i in range(5):
        x, z, h = r.uniform(-1.8, 1.8), r.uniform(-1.8, 1.8), r.uniform(1.6, 2.6)
        c = cols[(i + k * 2) % 5]
        rcyl(b, (x, h / 2, z), 0.1, h, (70, 160, 70), segs=5)
        rbox(b, (x + 0.35, h * 0.4, z), (0.6, 0.12, 0.3), (100, 190, 80), 0.02, rz=20)
        if (i + k) % 3 == 0:                                   # tulip
            rball(b, (x, h + 0.35, z), 0.5, c, (1, 1.3, 1), 8, 5)
        else:                                                  # daisy
            for j in range(6):
                a = j * math.tau / 6
                rball(b, (x + 0.48 * math.cos(a), h, z + 0.48 * math.sin(a)), 0.32, c, (1, 0.45, 1), 6, 4)
            rball(b, (x, h + 0.1, z), 0.26, (255, 210, 60), segs=6, rings=4)
    return [b.finish(f'Map_Flowers{k}', (0, 0, 0), MAT)]


def fence():
    b = B()
    for sx in (-1, 1):
        rbox(b, (sx * 3, 1.8, 0), (0.7, 3.6, 0.7), WHITE, 0.08)
        rcyl(b, (sx * 3, 3.95, 0), 0.5, 0.7, WHITE, segs=4, r2=0.05, yaw=45)
    for y in (1.3, 2.8):
        rbox(b, (0, y, 0), (6.2, 0.5, 0.3), WHITE, 0.06)
    for x in (-1.5, 0, 1.5):
        rbox(b, (x, 2.05, 0.05), (0.5, 2.6, 0.2), shade(WHITE, 0.96), 0.05)
    return [b.finish('Map_FenceWhite', (0, 0, 0), MAT)]


objs = windmill() + barn() + pond() + tree('Round') + tree('Fruit') + tree('Pine') + rock(1) + rock(2) + hay() + flowers(1) + flowers(2) + fence()
save_meta(HERE.parent / 'game')
print('triangles:', {o.name: len(o.data.polygons) for o in objs})
if 'nofbx' not in ARGS:
    print('wrote', blib.export(objs, OUT / 'RainingEggsMeadow.fbx'))

# ---------------------------------------------------------------- preview: a little meadow scene
sc, cam = scene_setup(ground=(0.28, 0.6, 0.18, 1))
for o in objs:
    o.hide_render = True
by = {o.name: o for o in objs}
water = bpy.data.materials.new('Water')
water.use_nodes = True
pb = water.node_tree.nodes['Principled BSDF']
pb.inputs['Base Color'].default_value = (0.2, 0.55, 0.9, 1)
pb.inputs['Roughness'].default_value = 0.05
pb.inputs['Alpha'].default_value = 0.6
water.blend_method = 'BLEND' if hasattr(water, 'blend_method') else None
road = B()
rbox(road, (0, 0.05, 40), (18, 0.1, 220), (238, 222, 180), 0)
road_o = road.finish('Road', (0, 0, 0), MAT)
blib.META.pop('Road', None)
lay = [('Map_Windmill', (34, 0, 30), 0), ('Map_WindmillBlades', (34, 0, 30), 0), ('Map_Barn', (-46, 0, 62), 20),
       ('Map_Pond', (-30, 0, 8), 0), ('Map_PondWater', (-30, 0, 8), 0)]
for x in range(-74, -18, 6):
    lay.append(('Map_FenceWhite', (x + 3, 0, 40), 0))
for k, (x, z) in enumerate(((-70, 20), (-64, 90), (-14, 92), (22, 80), (60, 70), (66, 20), (54, -10), (-60, -12), (20, 112), (-90, 60), (88, 48))):
    lay.append((('Map_TreeRound', 'Map_TreeFruit', 'Map_TreePine')[k % 3], (x, 0, z), k * 37))
for k, (x, z) in enumerate(((16, 4), (48, 52), (-8, 40), (14, 60))):
    lay.append(('Map_HayBale', (x, 0, z), k * 50))
for k, (x, z) in enumerate(((-52, 30), (40, -2), (-6, 70), (62, 96))):
    lay.append((f'Map_Rock{k % 2 + 1}', (x, 0, z), k * 70))
for k in range(26):
    lay.append((f'Map_Flowers{k % 2 + 1}', (R.uniform(-80, 80) if k % 3 else R.uniform(12, 30), 0, R.uniform(-30, 100)), R.uniform(0, 360)))
for name, pos, yaw in lay:
    o = place(by[name], name + '_p', pos, yaw)
    if name == 'Map_PondWater':
        o.data = o.data.copy()
        o.data.materials.clear()
        o.data.materials.append(water)
if 'norender' not in ARGS:
    pass
    shot(sc, cam, OUT / 'meadow_scene.png', (6, 34, -62), (-4, 6, 34), (1800, 1000), 30)
    shot(sc, cam, OUT / 'meadow_windmill.png', (62, 26, -16), (34, 22, 30), (1200, 1000), 35)
    shot(sc, cam, OUT / 'meadow_barn.png', (-22, 20, 18), (-46, 12, 62), (1400, 1000), 35)
    shot(sc, cam, OUT / 'meadow_pond.png', (-6, 22, -26), (-30, 0, 8), (1400, 1000), 35)
