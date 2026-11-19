r"""Raining Eggs: 5 back baskets the player BUYS in the shop (no upgrades) and wears on the back.

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


sets = [b1(), b2(), b3(), b4(), b5()]
objs = [o for s in sets for o in s]
blib.META.pop('Basket_Dummy', None)
save_meta(HERE.parent / 'game')
print('triangles:', {o.name: len(o.data.polygons) for o in objs})
if 'nofbx' not in ARGS:
    print('wrote', blib.export(objs, OUT / 'RainingEggsBaskets.fbx'))

# ---------------------------------------------------------------- preview
dm = dummy()
sc, cam = scene_setup(sky=(0.62, 0.8, 1.0, 1), ground=(0.35, 0.7, 0.3, 1))
sc.eevee.taa_render_samples = 64
glow = glow_material(3)
for o in objs + [dm]:
    o.hide_render = True
for k, s in enumerate(sets):
    x = (k - 2) * 12.0
    place(dm, f'D{k}', (x, 3, 0), 25)
    for o in s:
        p = place(o, o.name + '_p', (x, 3, 0), 25)
        if 'Neon' in o.name:
            p.data = p.data.copy()
            p.data.materials.clear()
            p.data.materials.append(glow)
if 'norender' not in ARGS:
    for k in range(5):
        x = (k - 2) * 12.0
        shot(sc, cam, OUT / f'basket_{k + 1}.png', (x + 5.5, 7.0, 9.5), (x + 0.4, 3.0, 1.8), (900, 1000), 50)
