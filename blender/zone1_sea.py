r"""Zone 1 (Sunny Meadow) - special creatures (sharks, octopuses, jellyfish, rays, squid, serpents) with a meadow twist.
  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P zone1_sea.py -- [index ...]
Smooth professional models (metaballs) -> out\zone1s\NN_3d.png
"""
import bpy, math, sys, pathlib, hashlib, random
from mathutils import Vector
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lowpoly_lib as LL
from metapet import MB, pixelate, pixelate2, pixelate3, rgb, WHITE, BLACK

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / 'out' / 'zone1s'
OUT.mkdir(parents=True, exist_ok=True)
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
LEAF, LEAF2 = rgb(90, 200, 70), rgb(60, 160, 50)
PETAL, POLLEN = rgb(255, 255, 255), rgb(255, 210, 40)


# ---------------------------------------------------------------- meadow decorations (detail meshes)
def clover(m, c, s=1.0, rot=0.0, col=LEAF):
    for k in range(3):
        a = rot + k * 2 * math.pi / 3
        d = Vector((math.cos(a), math.sin(a), 0))
        m.sphere(Vector(c) + d * 0.2 * s, 0.17 * s, col, (1.0, 1.0, 0.3), (0, 0, math.degrees(a)))
    m.tube([Vector(c), Vector(c) + Vector((0, 0.05, -0.25 * s))], [0.03 * s, 0.03 * s], LEAF2, 6)


def daisy(m, c, s=1.0, petal=PETAL, mid=POLLEN, tilt=(0, 0, 0)):
    c = Vector(c)
    for k in range(9):
        a = k * 2 * math.pi / 9
        d = Vector((math.cos(a), math.sin(a), 0))
        m.sphere(c + d * 0.24 * s, 0.13 * s, petal, (1.7, 0.7, 0.25), (tilt[0], tilt[1], math.degrees(a)))
    m.sphere(c + Vector((0, 0, 0.04 * s)), 0.13 * s, mid, (1, 1, 0.55))


def grass(m, c, n=5, h=0.5, col=LEAF):
    rng = random.Random(int(abs(c[0] * 100 + c[1] * 37 + c[2] * 11)))
    for k in range(n):
        o = Vector((rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), 0))
        m.cone(Vector(c) + o, Vector(c) + o * 2.5 + Vector((0, 0, h * rng.uniform(0.7, 1.2))), 0.05, col, segs=6, rings=3)


def two_tone(top, belly, split=-0.15):
    return lambda p, n, c: (belly if n.z < split else top) if c == top else c


# ---------------------------------------------------------------- body templates
def shark(m, top, belly, z=1.4, L=1.0, fin=None, tail=None, mouth=True):
    """smooth shark floating above the ground; returns key points"""
    S = L
    m.ell((0, -0.2 * S, z), 0.62 * S, (0.95, 2.2, 0.95), top)                   # body
    m.ell((0, -1.25 * S, z - 0.05), 0.48 * S, (0.95, 1.2, 0.8), top)            # snout
    m.ell((0, 1.35 * S, z + 0.05), 0.3 * S, (0.8, 1.6, 0.8), top)               # tail stalk
    m.ell((0, 0.1 * S, z + 0.75 * S), 0.32 * S, (0.12, 0.85, 1.6), fin or top, rot=(-30, 0, 0))     # dorsal fin
    m.sym(m.ell, (0.75 * S, -0.5 * S, z - 0.35 * S), 0.32 * S, (1.7, 0.8, 0.12), fin or top, rot=(0, -25, -20))   # pectorals
    m.ell((0, 1.95 * S, z + 0.55 * S), 0.32 * S, (0.12, 0.6, 1.7), tail or top, rot=(-35, 0, 0))   # tail lobes
    m.ell((0, 1.9 * S, z - 0.3 * S), 0.26 * S, (0.12, 0.55, 1.3), tail or top, rot=(40, 0, 0))
    m.ell((0, 0.9 * S, z - 0.45 * S), 0.16 * S, (0.12, 0.6, 1.0), fin or top, rot=(35, 0, 0))      # anal fin
    hc = Vector((0, -1.35 * S, z + 0.05))
    for s in (-1, 1):
        m.eye((s * 0.42 * S, -1.45 * S, z + 0.22 * S), s, 0.15 * S)
        for k in range(3):                                                       # gills
            m.sphere((s * 0.6 * S, -0.75 * S + k * 0.16 * S, z), 0.03 * S, LL.rgb(40, 40, 50) if hasattr(LL, 'rgb') else BLACK, (0.5, 0.6, 5))
    if mouth:
        m.sphere((0, -1.62 * S, z - 0.32 * S), 0.32 * S, rgb(110, 20, 40), (1.0, 0.55, 0.25), (-10, 0, 0))
        for k in range(7):
            a = math.pi * k / 6
            p = Vector((math.cos(a) * 0.27 * S, -1.62 * S - math.sin(a) * 0.13 * S, z - 0.27 * S))
            m.cone(p, p + Vector((0, 0, -0.14 * S)), 0.045 * S, WHITE, segs=6, rings=2)
    m.paint_fn = two_tone(top, belly)
    return {'top': Vector((0, 0, z + 0.62 * S)), 'head': hc, 'z': z}


def octopus(m, col, under, z=1.2, R=1.0, curl=1.0):
    m.ell((0, 0.15, z + 1.15 * R), 0.75 * R, (1.0, 1.0, 1.25), col, rot=(-15, 0, 0))   # mantle
    m.ball((0, -0.1, z + 0.35 * R), 0.62 * R, col)                                 # under body
    for i in range(8):                                                              # arms melt into the body
        a = 2 * math.pi * i / 8 + math.pi / 8
        d = Vector((math.cos(a), math.sin(a), 0))
        prev = Vector((0, 0, z + 0.25 * R)) + d * 0.35 * R
        for k in range(1, 9):
            t = k / 8
            p = d * (0.35 + 1.9 * t) * R + Vector((0, 0, max(0.15, z * (1 - t) ** 1.6) + 0.12))
            if t > 0.7:
                u = (t - 0.7) / 0.3
                p = p + Vector((0, 0, math.sin(u * math.pi * 0.9) * 0.45 * R * curl)) - d * u * u * 0.35 * R * curl
            m.cap(tuple(prev), tuple(p), (0.26 * (1 - t) + 0.07) * R, col)
            prev = p
    for s in (-1, 1):
        m.eye((s * 0.45 * R, -0.65 * R, z + 0.8 * R), s, 0.22 * R)
    m.paint_fn = lambda p, n, c: (under if (n.z < -0.35 and p.z < z + 0.5) else c) if c == col else c
    return {'top': Vector((0, 0.15, z + 2.15 * R)), 'z': z}


def jelly(m, dome, z=2.0, R=1.0, tent=rgb(255, 230, 140)):
    m.ell((0, 0, z), 0.95 * R, (1.0, 1.0, 0.72), dome)
    m.ball((0, 0, z - 0.75 * R), 0.75 * R, dome, neg=True)                         # hollow underside
    for k in range(10):                                                           # frill bumps
        a = 2 * math.pi * k / 10
        m.ball((math.cos(a) * 0.95 * R, math.sin(a) * 0.95 * R, z - 0.42 * R), 0.22 * R, dome)
    for k in range(8):                                                            # wavy tentacles (glowing)
        a = 2 * math.pi * k / 8 + 0.2
        r0 = 0.55 * R
        pts = [Vector((math.cos(a) * r0 + math.sin(j * 0.9 + k) * 0.12, math.sin(a) * r0 + math.cos(j * 0.9 + k) * 0.12, z - 0.4 * R - j * 0.24 * R)) for j in range(7)]
        m.tube(pts, [0.05 * R] * 6 + [0.02 * R], tent, 8)
    for s in (-1, 1):
        m.eye((s * 0.38 * R, -0.85 * R, z + 0.05 * R), s, 0.17 * R)
    return {'top': Vector((0, 0, z + 0.7 * R)), 'z': z}


def manta(m, top, belly, z=1.3, W=1.0):
    m.ell((0, 0, z), 0.8 * W, (2.6, 1.4, 0.32), top)                             # flat wing body
    m.sym(m.ell, (1.55 * W, 0.15, z + 0.12), 0.45 * W, (1.6, 0.8, 0.22), top, rot=(0, -12, -15))   # wing tips
    m.sym(m.ell, (0.45 * W, -1.05 * W, z - 0.05), 0.22 * W, (0.5, 1.0, 0.5), top)  # head horns (cephalic fins)
    m.tube([(0, 1.0 * W, z), (0, 1.9 * W, z + 0.15), (0, 2.7 * W, z + 0.05)], [0.08 * W, 0.05 * W, 0.02 * W], top, 8)
    for s in (-1, 1):
        m.eye((s * 0.6 * W, -0.98 * W, z + 0.12), s, 0.13 * W)
    m.paint_fn = two_tone(top, belly, -0.3)
    return {'top': Vector((0, 0, z + 0.3)), 'z': z}


def squid(m, col, z=1.0, L=1.0, fin=None):
    m.ell((0, 0.4 * L, z + 1.2 * L), 0.5 * L, (0.85, 0.85, 2.4), col, rot=(-25, 0, 0))   # long mantle
    m.sym(m.ell, (0.45 * L, 1.1 * L, z + 2.35 * L), 0.4 * L, (1.2, 0.5, 0.12), fin or col, rot=(-25, 0, 30))
    m.ball((0, -0.2 * L, z), 0.48 * L, col)                                        # head
    for i in range(8):
        a = 2 * math.pi * i / 8
        d = Vector((math.cos(a) * 0.8, math.sin(a) * 0.8 - 0.4, 0))
        pts = [Vector((0, -0.2 * L, z - 0.3 * L)) + d * 0.3 * L]
        for k in range(1, 6):
            pts.append(pts[0] + d * 0.45 * k * L + Vector((0, 0, -0.18 * k * L + (0.1 * k * k * 0.06) * L)))
        m.tube(pts, [0.12 * L, 0.1 * L, 0.08 * L, 0.06 * L, 0.04 * L, 0.02 * L], col, 8)
    for s in (-1, 1):
        m.eye((s * 0.38 * L, -0.55 * L, z + 0.12 * L), s, 0.17 * L)
    return {'top': Vector((0, 0.95 * L, z + 2.3 * L)), 'z': z}


def serpent(m, col, belly, z=1.0, L=1.0, n=11):
    pts = []
    for k in range(n):
        t = k / (n - 1)
        pts.append(Vector((math.sin(t * 5.0) * 0.8 * L, (2.4 - 3.2 * t) * L, (0.5 + 3.2 * t ** 1.4) * L)))   # rears up in an S
    for k, p in enumerate(pts):
        m.ball(tuple(p), (0.42 + 0.22 * k / n) * L, col)
    hc = pts[-1] + Vector((0, -0.45 * L, 0.25 * L))
    m.ell(tuple(hc), 0.62 * L, (0.9, 1.35, 0.8), col)
    m.ell(tuple(hc + Vector((0, -0.55 * L, -0.25 * L))), 0.42 * L, (0.85, 1.2, 0.5), col)    # jaw
    for s in (-1, 1):
        m.eye(tuple(hc + Vector((s * 0.42 * L, -0.45 * L, 0.25 * L))), s, 0.17 * L)
        m.cone(hc + Vector((s * 0.3 * L, 0.2 * L, 0.45 * L)), hc + Vector((s * 0.55 * L, 0.75 * L, 1.0 * L)), 0.12 * L, rgb(250, 240, 200))
        for k in range(4):
            p = hc + Vector((s * 0.25 * L, -0.95 * L + k * 0.15 * L, -0.15 * L))
            m.cone(p, p + Vector((0, 0, -0.17 * L)), 0.04 * L, WHITE, segs=6, rings=2)
    m.paint_fn = two_tone(col, belly, -0.3)
    return {'pts': pts, 'hc': hc, 'top': hc + Vector((0, 0, 0.6 * L))}


# ---------------------------------------------------------------- the 10 Sunny Meadow creatures
def clover_shark():
    m = MB('Clover Shark')
    k = shark(m, rgb(92, 196, 80), rgb(236, 250, 220), fin=rgb(70, 165, 60))
    clover(m, k['top'] + Vector((0, -0.4, 0.06)), 1.4, 0.3)
    clover(m, Vector((0.9, -0.55, 1.05)), 0.8, 1.0)
    return m


def daisy_octopus():
    m = MB('Daisy Octopus')
    k = octopus(m, rgb(255, 150, 200), rgb(255, 225, 238))
    daisy(m, k['top'] + Vector((0, 0, -0.05)), 1.6)
    return m


def grass_crab():
    m = MB('Meadow Crab')
    C, D = rgb(150, 210, 80), rgb(110, 170, 60)
    m.ell((0, 0, 0.95), 0.9, (1.25, 1.0, 0.55), C)                              # shell
    for i in range(3):
        y = -0.3 + i * 0.35
        m.sym(m.cap, (0.95, y, 0.85), (1.55, y + 0.1, 0.65), 0.13, D)
        m.sym(m.cap, (1.55, y + 0.1, 0.65), (1.8, y + 0.15, 0.05), 0.1, D)
    m.sym(m.cap, (0.75, -0.75, 0.95), (1.1, -1.25, 1.15), 0.16, C)              # arms
    m.sym(m.ell, (1.2, -1.55, 1.25), 0.32, (1.0, 1.3, 0.8), D)                  # claws
    for s in (-1, 1):
        m.tube([(s * 0.3, -0.75, 1.2), (s * 0.35, -0.85, 1.65)], [0.05, 0.05], D, 8)
        m.eye((s * 0.35, -0.88, 1.75), s, 0.15)
    grass(m, (0, 0.1, 1.35), 9, 0.6)
    daisy(m, (0.35, 0.3, 1.45), 0.7)
    return m


def honey_jelly():
    m = MB('Honey Jellyfish')
    HN = rgb(255, 196, 50)
    k = jelly(m, HN, tent=rgb(255, 236, 140))

    def comb(p, n, c):                                                         # honeycomb pattern
        if c != HN or p.z < 1.7:
            return c
        h = (int(p.x * 3.4 + (int(p.y * 3.4) % 2) * 0.5) + int(p.y * 3.4)) % 3
        return rgb(240, 160, 20) if h == 0 else c
    m.paint_fn = comb
    m.glow_cols = [rgb(255, 236, 140)]
    return m


def leaf_manta():
    m = MB('Leaf Manta')
    k = manta(m, rgb(70, 170, 70), rgb(220, 245, 200))
    for s in (-1, 1):                                                           # leaf veins
        m.tube([(0, -0.4, 1.58), (s * 1.0, 0.0, 1.55), (s * 1.9, 0.3, 1.45)], [0.035, 0.03, 0.02], rgb(40, 120, 40), 6)
    daisy(m, (0, -0.3, 1.6), 0.6)
    return m


def bumble_shark():
    m = MB('Bumble Shark')
    Y, K = rgb(255, 205, 40), rgb(40, 34, 40)
    k = shark(m, Y, rgb(255, 240, 190), fin=K, tail=K)
    base = m.paint_fn
    m.paint_fn = lambda p, n, c: (K if (c == Y and n.z >= -0.15 and int((p.y + 3) / 0.45) % 2 == 0 and -1.0 < p.y < 1.5) else base(p, n, c))
    for s in (-1, 1):
        m.sphere((s * 0.55, -0.1, 2.25), 0.45, rgb(210, 238, 255), (1.8, 0.9, 0.12), (0, s * -35, s * 25))
    m.tube([(0, -1.2, 1.9), (0.15, -1.45, 2.4)], [0.035, 0.03], K, 6)
    m.sphere((0.15, -1.47, 2.45), 0.07, K)
    return m


def tulip_squid():
    m = MB('Tulip Squid')
    k = squid(m, rgb(240, 70, 90), fin=rgb(255, 130, 150))
    t = k['top']
    for kk in range(5):                                                         # tulip crown
        a = kk * 2 * math.pi / 5
        m.sphere(t + Vector((math.cos(a) * 0.2, math.sin(a) * 0.2, 0.25)), 0.22, rgb(255, 100, 150), (0.7, 0.7, 1.5), (math.cos(a) * 15, math.sin(a) * 15, 0))
    m.tube([t + Vector((0, 0, -0.1)), t + Vector((0, 0, 0.1))], [0.06, 0.06], LEAF2, 6)
    return m


def pollen_dragon():
    m = MB('Pollen Sea Dragon')
    k = serpent(m, rgb(120, 200, 90), rgb(240, 250, 200), L=0.9)
    for p in k['pts'][2::2]:                                                    # leafy frills
        for s in (-1, 1):
            m.sphere(p + Vector((s * 0.45, 0, 0.15)), 0.22, LEAF, (1.6, 0.5, 0.18), (0, s * -30, s * 30))
    for p in k['pts'][1::3]:
        m.sphere(p + Vector((0, 0, 0.5)), 0.09, POLLEN)                         # glowing pollen
    m.glow_cols = [POLLEN]
    return m


def sun_kraken():
    m = MB('Sun Kraken')
    GD, LT, FL = rgb(255, 196, 50), rgb(255, 236, 170), rgb(255, 230, 90)
    k = octopus(m, GD, LT, R=1.35)
    t = k['top']
    for kk in range(12):                                                        # sun crown, glowing rays
        a = kk * 2 * math.pi / 12
        d = Vector((math.cos(a), 0.0, math.sin(a))) if False else Vector((math.cos(a), math.sin(a), 0))
        m.cone(t + d * 0.55 + Vector((0, 0, -0.2)), t + d * 1.1 + Vector((0, 0, 0.35)), 0.12, FL, segs=8)
    m.sphere(t + Vector((0, 0, 0.05)), 0.32, FL, (1, 1, 0.5))
    m.glow_cols = [FL]
    return m


def meadow_leviathan():
    m = MB('Meadow Leviathan')
    k = serpent(m, rgb(70, 150, 60), rgb(230, 240, 190), L=1.35, n=13)
    for p in k['pts'][1:-1]:                                                    # grass and flowers growing on its back
        grass(m, p + Vector((0, 0, 0.35)), 5, 0.55)
    for i, p in enumerate(k['pts'][2:-1:3]):
        daisy(m, p + Vector((0.2, 0, 0.6)), 0.6, petal=[PETAL, rgb(255, 120, 170), rgb(170, 140, 255)][i % 3])
    for s in (-1, 1):                                                           # glowing sun eyes
        m.sphere(k['hc'] + Vector((s * 0.6, -0.55, 0.35)), 0.09, rgb(255, 230, 90))
    m.sphere(k['top'] + Vector((0, 0, 0.6)), 0.35, rgb(255, 230, 90))           # sun orb above the head
    m.glow_cols = [rgb(255, 230, 90)]
    return m


PETS = [('Clover Shark', 'Common', clover_shark), ('Daisy Octopus', 'Common', daisy_octopus), ('Meadow Crab', 'Common', grass_crab),
        ('Honey Jellyfish', 'Uncommon', honey_jelly), ('Leaf Manta', 'Uncommon', leaf_manta), ('Bumble Shark', 'Rare', bumble_shark),
        ('Tulip Squid', 'Rare', tulip_squid), ('Pollen Sea Dragon', 'Epic', pollen_dragon), ('Sun Kraken', 'Legendary', sun_kraken),
        ('Meadow Leviathan', 'Mythic', meadow_leviathan)]

if __name__ == '__main__':
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc, cam = LL.stage()
    nums = [int(a) for a in args if a.isdigit()]
    pick = nums or range(1, 11)
    for i in pick:
        name, rar, fn = PETS[i - 1]
        mb = fn()
        body = mb.build()
        for o in bpy.data.objects:
            if o.type == 'MESH' and o.name != 'Plane':
                o.hide_render = o is not body
        if 'px' not in args:
            LL.shoot(sc, cam, body, OUT / f'{i:02d}_3d.png')
        px = pixelate3(mb)
        body.hide_render, px.hide_render = True, False
        LL.shoot(sc, cam, px, OUT / f'{i:02d}_px.png')
        px.hide_render = True
        print(name, len(body.data.polygons), '->', len(px.data.polygons))
    print('done')
