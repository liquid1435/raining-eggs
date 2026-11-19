r"""Raining Eggs: 20 back baskets the player BUYS in the shop (no upgrades) and wears on the back.

  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P gen_baskets.py [-- nofbx]  -> out\RainingEggsBaskets.fbx + out\baskets_*.png

Meshes (Roblox axes, origin = TORSO CENTRE of an R6 torso 2x2x1, character faces -Z, basket hangs on +Z):
  Basket_1..5 (body + straps), BasketNeon_3..5 (glow parts), Basket_Dummy (preview only)
"""
import bpy, bmesh, math, sys, pathlib, random

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from blib import *          # noqa: F401,F403
import blib

OUT = HERE / 'out'
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
MAT = reset()
EGGC = [((255, 120, 150), WHITE), ((120, 200, 255), (255, 214, 60)), ((255, 214, 60), (255, 90, 120)),
        ((150, 230, 120), WHITE), ((190, 130, 255), (255, 240, 120))]
LEATHER, BUCKLE = (120, 72, 40), (230, 200, 120)


def P(a, r, y, cz):
    return (r * math.cos(a), y, cz + r * math.sin(a))


def woven(b, cz, y0, h, rb, rt, rows, segs, c1, c2, depth=0.05, thick=0.16):
    """woven wall: rows x segs small planks around a cone, alternating in/out like wicker"""
    for i in range(rows):
        t = (i + 0.5) / rows
        y = y0 + h * t
        r = rb + (rt - rb) * t
        tilt = math.degrees(math.atan2(rt - rb, h))
        for j in range(segs):
            a = (j + 0.5) * math.tau / segs
            o = depth if (i + j) % 2 == 0 else -depth
            x, _, z = P(a, r + o, y, cz)
            w = math.tau * r / segs * 1.08
            rbox(b, (x, y, z), (w, h / rows * 0.94, thick), c1 if (i + j) % 2 == 0 else c2, 0.03,
                 yaw=-math.degrees(a) - 90, rx=-tilt)


def ring(b, cz, y, r, tr, c, segs=20):
    """round rim made of tube pieces"""
    for j in range(segs):
        a0, a1 = j * math.tau / segs, (j + 1.15) * math.tau / segs
        rtube(b, P(a0, r, y, cz), P(a1, r, y, cz), tr, c, segs=6)


def straps(b, cz, rt, top, c=LEATHER, buckle=BUCKLE):
    """two straps from the basket over the shoulders down the chest"""
    for sx in (-0.5, 0.5):
        zb = cz - rt + 0.05
        rplank(b, (sx, top - 0.2, zb), (sx, 1.06, 0.55), 0.3, 0.08, c)
        rplank(b, (sx, 1.06, 0.55), (sx, 1.06, -0.55), 0.3, 0.08, c)
        rplank(b, (sx, 1.06, -0.55), (sx, -0.7, -0.56), 0.3, 0.08, c)
        rbox(b, (sx, 0.1, -0.62), (0.38, 0.3, 0.06), buckle, 0.03)
    rplank(b, (-0.5, -0.2, -0.57), (0.5, -0.2, -0.57), 0.2, 0.06, c)


def eggs(b, cz, y, r, n, seed):
    rng = random.Random(seed)
    for k in range(n):
        a = k * math.tau / n + rng.uniform(-0.3, 0.3)
        rr = r * (0.45 if k % 2 else 0.1 if k == 0 else 0.55)
        c, s = EGGC[(k + seed) % 5]
        egg(b, P(a, rr, y + rng.uniform(0, 0.15), cz), 0.3, c, s)


def basket_shell(b, cz, rb, rt, h, y0, c1, c2, rim, floor, rows=6, segs=16):
    rcyl(b, (0, y0 + 0.08, cz), rb, 0.16, floor, segs=segs)
    woven(b, cz, y0 + 0.1, h, rb, rt, rows, segs, c1, c2)
    ring(b, cz, y0 + h + 0.12, rt + 0.06, 0.11, rim)
    ring(b, cz, y0 + 0.14, rb + 0.06, 0.09, rim)
    rcyl(b, (0, y0 + h * 0.75, cz), rt * 0.97, 0.1, shade(c2, 0.6), segs=segs)      # dark inner floor for the eggs


# ---------------------------------------------------------------- 1. Wicker Basket
def b1():
    b = B()
    rb, rt, h, y0 = 0.8, 1.05, 2.0, -1.3
    cz = 0.55 + rt + 0.05
    basket_shell(b, cz, rb, rt, h, y0, (214, 150, 80), (176, 112, 52), (150, 92, 40), (120, 76, 36))
    straps(b, cz, rt, y0 + h)
    eggs(b, cz, y0 + h * 0.8, rt * 0.8, 3, 1)
    return [b.finish('Basket_1', (0, 0, 0), MAT)]


# ---------------------------------------------------------------- 2. Picnic Basket (checker cloth + flowers)
def b2():
    b = B()
    rb, rt, h, y0 = 0.9, 1.15, 2.1, -1.35
    cz = 0.55 + rt + 0.05
    basket_shell(b, cz, rb, rt, h, y0, (240, 196, 120), (206, 150, 80), (190, 110, 50), (150, 90, 40), rows=6, segs=18)
    top = y0 + h + 0.1
    for j in range(18):                                   # checker cloth hanging over the rim
        a = (j + 0.5) * math.tau / 18
        x, _, z = P(a, rt + 0.12, top - 0.25, cz)
        for k in range(2):
            c = (230, 50, 60) if (j + k) % 2 == 0 else WHITE
            rbox(b, (x, top - 0.12 - k * 0.3, z), (math.tau * rt / 18 * 1.12, 0.3, 0.06), c, 0.02, yaw=-math.degrees(a) - 90)
    for k, (fa, fc) in enumerate(((0.5, (255, 220, 60)), (2.0, (255, 120, 180)), (3.6, (140, 200, 255)))):  # flowers on the side
        x, y, z = P(fa, rt + 0.1, y0 + h * 0.45, cz)
        for p in range(5):
            pa = p * math.tau / 5
            rball(b, (x + 0.14 * math.cos(pa), y + 0.14 * math.sin(pa), z), 0.09, fc, (1, 1, 0.5), 6, 4)
        rball(b, (x, y, z), 0.07, (255, 170, 40), segs=6, rings=4)
    straps(b, cz, rt, y0 + h, (200, 60, 60), (240, 240, 240))
    eggs(b, cz, y0 + h * 0.82, rt * 0.8, 5, 2)
    return [b.finish('Basket_2', (0, 0, 0), MAT)]


# ---------------------------------------------------------------- 3. Tech Pack (metal bucket + glow stripes)
def b3():
    b, n = B(), B()
    rb, rt, h, y0 = 0.95, 1.15, 2.2, -1.4
    cz = 0.55 + rt + 0.05
    steel, steel2, blue = (190, 200, 214), (140, 150, 170), (60, 120, 230)
    rcyl(b, (0, y0 + h / 2, cz), rt, h, steel, segs=24, r2=None)
    rcyl(b, (0, y0 + 0.4, cz), rb + 0.08, 0.8, blue, segs=24, r2=rt * 0.93)
    for yy in (y0 + 0.9, y0 + h - 0.15):
        rcyl(b, (0, yy, cz), rt + 0.07, 0.2, steel2, segs=24)
    for j in range(12):                                   # rivets
        x, y, z = P(j * math.tau / 12, rt + 0.08, y0 + h - 0.15, cz)
        rball(b, (x, y, z), 0.06, (240, 240, 250), segs=6, rings=4)
    for yy in (y0 + 1.25, y0 + 1.6):                      # glow stripes
        rcyl(n, (0, yy, cz), rt + 0.03, 0.09, (60, 230, 255), segs=24)
    rcyl(b, (0, y0 + h - 0.05, cz), rt - 0.1, 0.1, (40, 44, 60), segs=24)          # dark inside top
    for sx in (-1, 1):                                    # side thrusters
        x = sx * (rt + 0.15)
        rcyl(b, (x, y0 + 0.9, cz), 0.22, 1.1, steel2, segs=12)
        rcyl(b, (x, y0 + 0.25, cz), 0.26, 0.2, blue, segs=12, r2=0.16)
        rcyl(n, (x, y0 + 0.12, cz), 0.14, 0.1, (60, 230, 255), segs=12)
    rtube(b, (0.6, y0 + h, cz + 0.6), (0.75, y0 + h + 0.8, cz + 0.75), 0.04, steel2)  # antenna
    rball(n, (0.75, y0 + h + 0.85, cz + 0.75), 0.1, (255, 70, 90), segs=8, rings=5)
    straps(b, cz, rt, y0 + h, (50, 56, 80), (60, 230, 255))
    eggs(b, cz, y0 + h - 0.05, rt * 0.8, 6, 3)
    return [b.finish('Basket_3', (0, 0, 0), MAT), n.finish('BasketNeon_3', (0, 0, 0), MAT)]


# ---------------------------------------------------------------- 4. Crystal Basket
def b4():
    b, n = B(), B()
    rb, rt, h, y0 = 0.95, 1.25, 2.2, -1.4
    cz = 0.55 + rt + 0.05
    basket_shell(b, cz, rb, rt, h, y0, (150, 90, 230), (110, 60, 190), (230, 210, 255), (80, 40, 140), rows=6, segs=18)
    top = y0 + h + 0.12
    rng = random.Random(4)
    for j in range(9):                                    # crystal shards around the rim
        a = j * math.tau / 9
        x, _, z = P(a, rt + 0.05, top, cz)
        hh = rng.uniform(0.6, 1.1)
        c = (200, 140, 255) if j % 2 else (130, 220, 255)
        rcyl(n, (x, top + hh / 2, z), 0.18, hh, c, segs=5, r2=0.02, rz=rng.uniform(-18, 18), rx=rng.uniform(-18, 18))
    for k, a in enumerate((0.6, 2.2, 3.9, 5.2)):        # gems set in the wall
        x, y, z = P(a, rt * 0.9 + 0.12, y0 + h * 0.5, cz)
        rico(n, (x, y, z), 0.16, (255, 120, 220) if k % 2 else (120, 240, 255), (1, 1.3, 1), 1)
    straps(b, cz, rt, y0 + h, (90, 50, 160), (200, 160, 255))
    eggs(b, cz, y0 + h * 0.82, rt * 0.8, 7, 4)
    return [b.finish('Basket_4', (0, 0, 0), MAT), n.finish('BasketNeon_4', (0, 0, 0), MAT)]


# ---------------------------------------------------------------- 5. Royal Golden Basket (crown + wings)
def b5():
    b, n = B(), B()
    rb, rt, h, y0 = 1.0, 1.3, 2.3, -1.45
    cz = 0.55 + rt + 0.05
    basket_shell(b, cz, rb, rt, h, y0, (255, 216, 70), (246, 186, 40), (255, 244, 180), (200, 140, 30), rows=7, segs=20)
    top = y0 + h + 0.12
    for j in range(8):                                    # crown spikes with gems
        a = j * math.tau / 8
        x, _, z = P(a, rt + 0.05, top, cz)
        rcyl(b, (x, top + 0.3, z), 0.2, 0.6, (255, 214, 70), segs=4, r2=0.03)
        rball(n, (x, top + 0.66, z), 0.1, (255, 60, 80) if j % 2 else (80, 200, 255), segs=8, rings=5)
    for k in range(10):                                   # ruby band
        x, y, z = P(k * math.tau / 10 + 0.3, rt * 0.88 + 0.15, y0 + h * 0.45, cz)
        rico(n, (x, y, z), 0.12, (255, 50, 80), sub=1)
    for sx in (-1, 1):                                    # little angel wings on the sides
        for f in range(4):
            rball(b, (sx * (rt + 0.5 + f * 0.22), y0 + h * 0.75 + f * 0.18 - (f * f) * 0.05, cz + 0.15),
                  0.42 - f * 0.06, WHITE, (1.4, 0.45, 0.2), 10, 6, rz=sx * (25 + f * 8))
    straps(b, cz, rt, y0 + h, (170, 30, 50), (255, 214, 60))
    eggs(b, cz, y0 + h * 0.84, rt * 0.8, 8, 5)
    rball(n, (0, y0 + h * 0.84 + 0.2, cz), 0.32, (255, 240, 140), (1, 1.3, 1), 10, 8)  # glowing golden egg in the middle
    return [b.finish('Basket_5', (0, 0, 0), MAT), n.finish('BasketNeon_5', (0, 0, 0), MAT)]


def dummy():
    b = B()
    rbox(b, (0, 0, 0), (2, 2, 1), (40, 110, 220), 0.06)
    rbox(b, (0, 1.6, 0), (1.2, 1.2, 1.2), (250, 210, 60), 0.15)
    rbox(b, (-0.25, 1.75, -0.61), (0.16, 0.28, 0.02), INK, 0.01)
    rbox(b, (0.25, 1.75, -0.61), (0.16, 0.28, 0.02), INK, 0.01)
    for sx in (-1.5, 1.5):
        rbox(b, (sx, 0, 0), (1, 2, 1), (250, 210, 60), 0.06)
    for sx in (-0.5, 0.5):
        rbox(b, (sx, -2, 0), (1, 2, 1), (120, 190, 70), 0.06)
    return b.finish('Basket_Dummy', (0, 0, 0), MAT)



# ================================================================ 20 baskets: each one holds ONE egg more
def smooth(b, cz, rb, rt, h, y0, c, rim, segs=24):
    hs = h * 0.76                                         # solid part (the eggs sit on its top), thin wall above
    rm = rb + (rt - rb) * hs / h
    rcyl(b, (0, y0 + hs / 2 + 0.1, cz), rb, hs, c, segs=segs, r2=rm)
    wall = h - hs + 0.05
    for j in range(segs):
        a = (j + 0.5) * math.tau / segs
        r = (rm + rt) / 2 - 0.05
        x, _, z = P(a, r, y0 + 0.1 + hs + wall / 2 - 0.05, cz)
        rbox(b, (x, y0 + 0.1 + hs + wall / 2 - 0.05, z), (math.tau * r / segs * 1.12, wall, 0.12), c, 0.0, yaw=-math.degrees(a) - 90)
    ring(b, cz, y0 + h + 0.12, rt + 0.04, 0.12, rim, segs)
    rcyl(b, (0, y0 + 0.1 + hs, cz), rm * 0.97, 0.04, shade(c, 0.45), segs=segs)


def woven_rows(b, cz, rb, rt, h, y0, rows_c, rim, segs=18):
    rcyl(b, (0, y0 + 0.08, cz), rb, 0.16, shade(rows_c[0], 0.7), segs=segs)
    rows = len(rows_c)
    tilt = math.degrees(math.atan2(rt - rb, h))
    for i, c in enumerate(rows_c):
        t = (i + 0.5) / rows
        yy, r = y0 + 0.1 + h * t, rb + (rt - rb) * t
        for j in range(segs):
            a = (j + 0.5) * math.tau / segs
            o = 0.05 if (i + j) % 2 == 0 else -0.05
            x, _, z = P(a, r + o, yy, cz)
            rbox(b, (x, yy, z), (math.tau * r / segs * 1.08, h / rows * 0.94, 0.16), c if (i + j) % 2 == 0 else shade(c, 0.8), 0.03,
                 yaw=-math.degrees(a) - 90, rx=-tilt)
    ring(b, cz, y0 + h + 0.12, rt + 0.06, 0.11, rim)
    ring(b, cz, y0 + 0.14, rb + 0.06, 0.09, rim)
    rcyl(b, (0, y0 + h * 0.75, cz), rt * 0.97, 0.1, shade(rows_c[0], 0.4), segs=segs)


def around(n, r, y, cz, off=0.0):
    return [P(j * math.tau / n + off, r, y, cz) for j in range(n)]


def stars(n, pts, c, s=0.18):
    for (x, y, z) in pts:
        for rz in (0, 36, 72, 108, 144):
            rbox(n, (x, y, z), (s * 1.8, s * 0.45, s * 0.45), c, 0.02, rz=rz)


def dome(b, pos, r, h, c, segs=12, rings=6):
    x, y, z = pos
    vs = bmesh.ops.create_uvsphere(b.bm, u_segments=segs, v_segments=rings, radius=1, matrix=M(pos, scale=(r, h, r)))['verts']
    bmesh.ops.delete(b.bm, geom=[v for v in vs if v.co.z < y - 1e-4], context='VERTS')
    b.paint([v for v in vs if v.is_valid], c)


def make(k, body, deco=None, strap=(LEATHER, BUCKLE)):
    b, n = B(), B()
    t = (k - 1) / 19
    rb, rt, h, y0 = 0.78 + 0.22 * t, 1.0 + 0.3 * t, 1.9 + 0.4 * t, -1.25 - 0.2 * t
    cz = 0.55 + rt + 0.05
    body(b, n, cz, rb, rt, h, y0)
    if deco:
        deco(b, n, cz, rb, rt, h, y0, y0 + h + 0.12)
    straps(b, cz, rt, y0 + h, *strap)
    eggs(b, cz, y0 + h * 0.8 + 0.1, rt * 0.75, 3 + k // 3, k)
    out = [b.finish(f'Basket_{k}', (0, 0, 0), MAT)]
    if n.n:
        out.append(n.finish(f'BasketNeon_{k}', (0, 0, 0), MAT))
    return out


def W(c1, rim, rows=6):
    return lambda b, n, cz, rb, rt, h, y0: woven_rows(b, cz, rb, rt, h, y0, [c1] * rows, rim)


def S(c, rim):
    return lambda b, n, cz, rb, rt, h, y0: smooth(b, cz, rb, rt, h, y0, c, rim)


def metal(c, c2):
    def f(b, n, cz, rb, rt, h, y0):
        smooth(b, cz, rb, rt, h, y0, c, c2)
        rcyl(b, (0, y0 + 0.5, cz), rb + (rt - rb) * 0.5 / h + 0.06, 0.18, c2, segs=24)
        ring(b, cz, y0 + h - 0.1, rt + 0.02, 0.1, c2, 24)
    return f


def d_straw(b, n, cz, rb, rt, h, y0, top):
    rng = random.Random(2)
    for (x, y, z) in around(22, rt + 0.05, top, cz):
        rbox(b, (x, y + 0.15, z), (0.05, 0.4, 0.05), (250, 220, 110), 0.01, rz=rng.uniform(-35, 35), rx=rng.uniform(-35, 35))


def d_picnic(b, n, cz, rb, rt, h, y0, top):
    for j in range(18):
        a = (j + 0.5) * math.tau / 18
        x, _, z = P(a, rt + 0.12, top, cz)
        for q in range(2):
            rbox(b, (x, top - 0.12 - q * 0.3, z), (math.tau * rt / 18 * 1.12, 0.3, 0.06), (230, 50, 60) if (j + q) % 2 == 0 else WHITE, 0.02, yaw=-math.degrees(a) - 90)


def flower(b, x, y, z, c, s=0.14):
    for p in range(5):
        pa = p * math.tau / 5
        rball(b, (x + s * math.cos(pa), y + s * math.sin(pa), z), s * 0.65, c, (1, 1, 0.5), 6, 4)
    rball(b, (x, y, z), s * 0.5, (255, 190, 40), segs=6, rings=4)


def d_flowers(b, n, cz, rb, rt, h, y0, top):
    cs = [(255, 120, 180), (255, 230, 70), (140, 200, 255), (255, 255, 255)]
    for j, (x, y, z) in enumerate(around(10, rt + 0.1, top + 0.05, cz)):
        rball(b, (x, y - 0.05, z), 0.16, (90, 190, 80), (1.4, 0.5, 1), 6, 4)
        flower(b, x, y + 0.12, z, cs[j % 4], 0.16)


def d_honey(b, n, cz, rb, rt, h, y0, top):
    rng = random.Random(5)
    for (x, y, z) in around(14, rt + 0.03, top - 0.25, cz):
        rball(b, (x, y - rng.uniform(0.1, 0.5), z), 0.14, (255, 176, 30), (1, rng.uniform(2, 4), 1), 6, 5)
    x, y, z = P(1.2, rt + 0.15, y0 + h * 0.5, cz)
    rball(b, (x, y, z), 0.22, (255, 214, 40), (1.3, 1, 1), 8, 6)
    for q in (-1, 1):
        rbox(b, (x + q * 0.1, y, z), (0.06, 0.3, 0.3), INK, 0.01)
    rball(b, (x, y + 0.22, z), 0.14, (230, 240, 255), (1.4, 0.4, 1), 6, 4)


def d_mush(b, n, cz, rb, rt, h, y0, top):
    for (x, y, z) in around(7, rt + 0.05, top + 0.05, cz, 0.3):
        rcyl(b, (x, y + 0.12, z), 0.08, 0.25, CREAM, segs=8)
        dome(b, (x, y + 0.24, z), 0.28, 0.2, (230, 50, 50), 10, 5)
        rball(b, (x + 0.1, y + 0.4, z), 0.05, WHITE, segs=5, rings=3)


def d_candy(b, n, cz, rb, rt, h, y0, top):
    cs = [(255, 90, 120), (120, 200, 255), (255, 214, 60), (150, 230, 120), (190, 130, 255)]
    for j, (x, y, z) in enumerate(around(12, rt + 0.04, top + 0.08, cz)):
        rball(b, (x, y, z), 0.17, cs[j % 5], segs=8, rings=5)
    for q in range(3):
        rcyl(b, (0, y0 + 0.5 + q * h * 0.28, cz), rb + (rt - rb) * (0.2 + q * 0.28) + 0.04, 0.12, WHITE, segs=24)


def d_pail(b, n, cz, rb, rt, h, y0, top):
    for k2 in range(9):
        a = math.radians(8 + 164 * k2 / 8)
        rbox(b, ((rt - 0.05) * math.cos(a), top + 0.6 * math.sin(a), cz), (0.14, 0.14, 0.14), (255, 214, 60), 0.03, rz=math.degrees(a))
    for (x, y, z) in around(4, rt + 0.06, y0 + h * 0.5, cz, 0.8):
        stars(b, [(x, y, z)], (255, 240, 120), 0.14)


def d_cookie(b, n, cz, rb, rt, h, y0, top):
    rng = random.Random(9)
    for _ in range(26):
        a, yy = rng.uniform(0, math.tau), rng.uniform(y0 + 0.3, y0 + h - 0.1)
        rr = rb + (rt - rb) * (yy - y0) / h
        rball(b, P(a, rr + 0.03, yy, cz), 0.09, (90, 50, 30), (1, 1, 1), 6, 4)


def d_pumpkin_body(b, n, cz, rb, rt, h, y0):
    for j in range(12):
        x, y, z = P(j * math.tau / 12, rt * 0.82, y0 + h / 2, cz)
        rball(b, (x, y, z), rt * 0.32, (255, 130, 30) if j % 2 else (240, 110, 20), (1, h / (rt * 0.64) * 0.98, 1), 10, 8)
    rcyl(b, (0, y0 + h * 0.8, cz), rt * 0.8, 0.1, (60, 30, 10), segs=20)
    ring(b, cz, y0 + h + 0.05, rt * 0.85, 0.1, (90, 160, 50))


def d_pumpkin(b, n, cz, rb, rt, h, y0, top):
    x, y, z = P(math.pi / 2 + 0.15, rt * 1.12, y0 + h * 0.5, cz)
    for q in (-1, 1):
        rbox(n, (x + q * 0.28, y + 0.2, z), (0.22, 0.22, 0.05), (255, 220, 60), 0.01, rz=45)
    rbox(n, (x, y - 0.2, z), (0.6, 0.14, 0.05), (255, 220, 60), 0.01)
    for (xx, yy, zz) in around(5, rt * 0.85, top - 0.1, cz, 0.6):
        rball(b, (xx, yy, zz), 0.2, (90, 170, 60), (1.2, 0.3, 0.8), 6, 4)


def d_ice(b, n, cz, rb, rt, h, y0, top):
    rng = random.Random(11)
    for (x, y, z) in around(10, rt + 0.02, top, cz):
        rbox(b, (x, y + 0.1, z), (0.32, 0.32, 0.32), (200, 240, 255), 0.06, rz=rng.uniform(0, 40), yaw=rng.uniform(0, 90))
    for (x, y, z) in around(14, rt + 0.03, top - 0.2, cz, 0.2):
        rcyl(b, (x, y - 0.2, z), 0.07, 0.4, (220, 248, 255), segs=5, r2=0.01, rx=180)


def d_tech(b, n, cz, rb, rt, h, y0, top):
    for yy in (y0 + h * 0.55, y0 + h * 0.72):
        rcyl(n, (0, yy, cz), rb + (rt - rb) * (yy - y0) / h + 0.03, 0.09, (60, 230, 255), segs=24)
    for (x, y, z) in around(12, rt + 0.06, top - 0.15, cz):
        rball(b, (x, y, z), 0.06, (240, 240, 250), segs=6, rings=4)
    for sx in (-1, 1):
        x = sx * (rt + 0.15)
        rcyl(b, (x, y0 + 0.9, cz), 0.22, 1.1, (140, 150, 170), segs=12)
        rcyl(n, (x, y0 + 0.28, cz), 0.15, 0.1, (60, 230, 255), segs=12)
    rtube(b, (0.6, top, cz + 0.6), (0.75, top + 0.8, cz + 0.75), 0.04, (140, 150, 170))
    rball(n, (0.75, top + 0.85, cz + 0.75), 0.1, (255, 70, 90), segs=8, rings=5)


def d_shell(b, n, cz, rb, rt, h, y0, top):
    cs = [(255, 200, 210), (255, 240, 220), (255, 170, 140)]
    for j, (x, y, z) in enumerate(around(8, rt + 0.1, y0 + h * 0.35, cz, 0.2)):
        yy = y + (j % 2) * h * 0.3
        for f in range(5):
            rball(b, (x + (f - 2) * 0.06, yy + 0.02 * abs(f - 2), z), 0.1, cs[j % 3], (0.5, 1.6, 0.6), 6, 4, rz=(f - 2) * 18)
    for (x, y, z) in around(12, rt + 0.04, top + 0.04, cz):
        rball(b, (x, y, z), 0.1, WHITE, segs=8, rings=5)


def d_lava(b, n, cz, rb, rt, h, y0, top):
    rng = random.Random(14)
    for j in range(10):
        a = j * math.tau / 10 + rng.uniform(-0.2, 0.2)
        p0 = P(a, rb + 0.06, y0 + 0.3, cz)
        p1 = P(a + rng.uniform(-0.4, 0.4), (rb + rt) / 2 + 0.06, y0 + h * 0.5, cz)
        p2 = P(a + rng.uniform(-0.4, 0.4), rt + 0.06, y0 + h - 0.1, cz)
        rtube(n, p0, p1, 0.05, (255, 120, 20), segs=5)
        rtube(n, p1, p2, 0.05, (255, 160, 30), segs=5)
    for (x, y, z) in around(8, rt, top + 0.1, cz):
        rico(b, (x, y, z), 0.2, (60, 50, 50), (1, 1.3, 1), 1)


def bolt(n, x, y, z, s, c):
    rbox(n, (x - 0.05 * s, y + 0.25 * s, z), (0.18 * s, 0.6 * s, 0.06), c, 0.01, rz=-25)
    rbox(n, (x + 0.05 * s, y - 0.25 * s, z), (0.18 * s, 0.6 * s, 0.06), c, 0.01, rz=-25)
    rbox(n, (x, y, z), (0.4 * s, 0.14 * s, 0.06), c, 0.01)


def d_thunder(b, n, cz, rb, rt, h, y0, top):
    for a in (math.pi / 2 + 0.6, math.pi / 2 - 0.6, math.pi / 2 + 1.8):
        x, y, z = P(a, rt + 0.12, y0 + h * 0.5, cz)
        bolt(n, x, y, z, 1.0, (255, 230, 60))
    for (x, y, z) in around(6, rt, top, cz):
        rcyl(b, (x, y + 0.3, z), 0.06, 0.6, (120, 120, 140), segs=6)
        rball(n, (x, y + 0.65, z), 0.1, (160, 220, 255), segs=8, rings=5)


def d_neon(b, n, cz, rb, rt, h, y0, top):
    for q, c in enumerate(((255, 60, 200), (60, 230, 255), (255, 60, 200))):
        yy = y0 + 0.4 + q * h * 0.3
        rcyl(n, (0, yy, cz), rb + (rt - rb) * (yy - y0) / h + 0.03, 0.08, c, segs=24)
    ring(n, cz, top, rt + 0.06, 0.07, (60, 230, 255))
    stars(n, [P(math.pi / 2 + 0.2, rt + 0.1, y0 + h * 0.5, cz)], (255, 240, 120), 0.2)


def d_cloud(b, n, cz, rb, rt, h, y0, top):
    rng = random.Random(17)
    for (x, y, z) in around(12, rt + 0.1, top, cz):
        rball(b, (x, y + rng.uniform(-0.05, 0.1), z), rng.uniform(0.25, 0.34), WHITE, segs=10, rings=7)
    for (x, y, z) in around(9, rb + 0.1, y0 + 0.2, cz, 0.3):
        rball(b, (x, y, z), 0.24, (235, 240, 255), segs=10, rings=7)
    for sx in (-1, 1):
        for f in range(3):
            rball(b, (sx * (rt + 0.45 + f * 0.2), y0 + h * 0.7 + f * 0.12, cz + 0.1), 0.36 - f * 0.06, WHITE, (1.4, 0.45, 0.2), 10, 6, rz=sx * (25 + f * 8))


def d_crystal(b, n, cz, rb, rt, h, y0, top):
    rng = random.Random(4)
    for j, (x, y, z) in enumerate(around(9, rt + 0.05, top, cz)):
        hh = rng.uniform(0.5, 0.95)
        rcyl(n, (x, y + hh / 2, z), 0.16, hh, (200, 140, 255) if j % 2 else (130, 220, 255), segs=5, r2=0.02, rz=rng.uniform(-18, 18), rx=rng.uniform(-18, 18))
    for q, a in enumerate((0.6, 2.2, 3.9, 5.2)):
        rico(n, P(a, rt * 0.9 + 0.12, y0 + h * 0.5, cz), 0.15, (255, 120, 220) if q % 2 else (120, 240, 255), (1, 1.3, 1), 1)


def d_rainbow(b, n, cz, rb, rt, h, y0, top):
    stars(n, around(6, rt + 0.15, top + 0.25, cz, 0.3), (255, 240, 120), 0.16)


def d_royal(b, n, cz, rb, rt, h, y0, top):
    for j, (x, y, z) in enumerate(around(8, rt + 0.05, top, cz)):
        rcyl(b, (x, y + 0.3, z), 0.2, 0.6, (255, 214, 70), segs=4, r2=0.03)
        rball(n, (x, y + 0.66, z), 0.1, (255, 60, 80) if j % 2 else (80, 200, 255), segs=8, rings=5)
    for (x, y, z) in around(10, rt * 0.88 + 0.15, y0 + h * 0.45, cz, 0.3):
        rico(n, (x, y, z), 0.12, (255, 50, 80), sub=1)
    for sx in (-1, 1):
        for f in range(4):
            rball(b, (sx * (rt + 0.5 + f * 0.22), y0 + h * 0.75 + f * 0.18 - f * f * 0.05, cz + 0.15), 0.42 - f * 0.06, WHITE, (1.4, 0.45, 0.2), 10, 6, rz=sx * (25 + f * 8))
    rball(n, (0, y0 + h * 0.84 + 0.2, cz), 0.3, (255, 240, 140), (1, 1.3, 1), 10, 8)


BASKETS = [  # name, body, deco, straps
    ("Old Basket", W((200, 140, 76), (150, 92, 40)), None, (LEATHER, BUCKLE)),
    ("Straw Basket", W((240, 210, 120), (200, 160, 70)), d_straw, (LEATHER, BUCKLE)),
    ("Picnic Basket", W((236, 190, 116), (190, 110, 50)), d_picnic, ((200, 60, 60), WHITE)),
    ("Flower Basket", W((120, 200, 100), (80, 150, 60)), d_flowers, ((90, 150, 60), (255, 230, 70))),
    ("Honey Pot", S((255, 184, 40), (200, 120, 20)), d_honey, (LEATHER, (255, 214, 60))),
    ("Mushroom Basket", W((236, 70, 70), (250, 240, 220)), d_mush, ((150, 40, 40), WHITE)),
    ("Candy Bucket", S((255, 150, 190), WHITE), d_candy, ((255, 90, 140), WHITE)),
    ("Sand Pail", S((70, 150, 255), (255, 214, 60)), d_pail, ((40, 90, 200), (255, 214, 60))),
    ("Cookie Jar", S((226, 176, 110), (180, 120, 60)), d_cookie, ((110, 66, 40), (226, 176, 110))),
    ("Pumpkin Pack", d_pumpkin_body, d_pumpkin, ((60, 40, 30), (255, 140, 30))),
    ("Ice Bucket", S((170, 220, 255), WHITE), d_ice, ((80, 140, 200), WHITE)),
    ("Tech Pack", metal((190, 200, 214), (140, 150, 170)), d_tech, ((50, 56, 80), (60, 230, 255))),
    ("Ocean Basket", W((60, 190, 200), (240, 230, 200)), d_shell, ((30, 120, 140), (255, 200, 210))),
    ("Lava Basket", S((70, 56, 56), (40, 30, 30)), d_lava, ((50, 40, 40), (255, 120, 20))),
    ("Thunder Pack", metal((90, 70, 150), (60, 50, 100)), d_thunder, ((50, 40, 90), (255, 230, 60))),
    ("Neon Basket", S((40, 36, 60), (20, 18, 30)), d_neon, ((30, 28, 44), (255, 60, 200))),
    ("Cloud Basket", W((235, 240, 255), (200, 215, 255)), d_cloud, ((180, 200, 240), WHITE)),
    ("Crystal Basket", W((150, 90, 230), (230, 210, 255)), d_crystal, ((90, 50, 160), (200, 160, 255))),
    ("Rainbow Basket", (lambda b, n, cz, rb, rt, h, y0: woven_rows(b, cz, rb, rt, h, y0, RAINBOW[:7], WHITE, 20)), d_rainbow, (WHITE, (255, 214, 60))),
    ("Royal Basket", W((255, 216, 70), (255, 244, 180), 7), d_royal, ((170, 30, 50), (255, 214, 60))),
]


def price(k):
    if k == 1:
        return 0
    v = 100 * 2.2 ** (k - 2)
    m = 10 ** max(0, len(str(int(v))) - 2)
    return int(round(v / m) * m)


sets = [make(k + 1, body, deco, st) for k, (name, body, deco, st) in enumerate(BASKETS)]
objs = [o for s in sets for o in s]
save_meta(HERE.parent / 'game')
import json
(OUT / 'baskets20.json').write_text(json.dumps([{'k': k + 1, 'name': nm, 'cap': 3 + k, 'price': price(k + 1)} for k, (nm, *_) in enumerate(BASKETS)], indent=1))
print('triangles total:', sum(len(o.data.polygons) for o in objs), 'max', max(len(o.data.polygons) for o in objs))
if 'nofbx' not in ARGS:
    print('wrote', blib.export(objs, OUT / 'RainingEggsBaskets.fbx'))

dm = dummy()
sc, cam = scene_setup(sky=(0.62, 0.8, 1.0, 1), ground=(0.35, 0.7, 0.3, 1))
sc.eevee.taa_render_samples = 48
glow = glow_material(3)
for o in objs + [dm]:
    o.hide_render = True
for k, s in enumerate(sets):
    x = k * 12.0
    place(dm, f'D{k}', (x, 3, 0), 25)
    for o in s:
        p = place(o, o.name + '_p', (x, 3, 0), 25)
        if 'Neon' in o.name:
            p.data = p.data.copy()
            p.data.materials.clear()
            p.data.materials.append(glow)
if 'norender' not in ARGS:
    for k in range(len(sets)):
        x = k * 12.0
        shot(sc, cam, OUT / f'b20_{k + 1:02d}.png', (x + 5.5, 7.0, 9.5), (x + 0.4, 3.0, 1.8), (600, 660), 50)

if 'icons' in ARGS:                                       # transparent basket-only pictures for the shop UI
    sc.render.film_transparent = True
    for o in list(bpy.data.objects):
        if o.name.startswith('D') and o.name[1:].isdigit():
            o.hide_render = True
        if o.name == 'Ground':
            o.hide_render = True
    for k in range(len(sets)):
        x = k * 12.0
        shot(sc, cam, OUT / f'icon_{k + 1:02d}.png', (x + 3.2, 7.2, 9.0), (x + 0.75, 3.0, 2.2), (512, 512), 60)
