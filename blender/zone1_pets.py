r"""Zone 1 (Sunny Meadow): 10 low-poly studded pets, one render each + a labelled sheet.
  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P zone1_pets.py
"""
import bpy, math, sys, pathlib, hashlib
from mathutils import Vector
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lowpoly_lib as LL
from lowpoly_lib import LP, rgb, two_tone, quadruped, bird_t, WHITE, BLACK

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / 'out' / 'zone1'
OUT.mkdir(parents=True, exist_ok=True)


def spots(base, spot, k=0.9):
    def f(c, n):
        h = int(hashlib.md5(f'{round(c.x * 1.3)},{round(c.y * 1.1)},{round(c.z * 1.2)}'.encode()).hexdigest()[:2], 16)
        return spot if h < 256 * (1 - k) else base
    return f


def bunny(P):
    W_, G_, PK = rgb(245, 245, 250), rgb(220, 222, 232), rgb(255, 160, 190)
    q = quadruped(P, two_tone(W_, G_), L=2.2, W=0.9, H=0.85, leg=0.5, legr=0.24, neck=0.1, head=(0.62, 0.62, 0.6), snout=(0.32, 0.25, 0.22),
                  snout_col=W_, hoof=G_, head_up=0.25)
    hc = q['hc']
    for sx in (-1, 1):
        b = Vector((sx * 0.28, hc.y + 0.15, hc.z + 0.45))
        P.loft([(tuple(b), 0.17, 0.1), (tuple(b + Vector((sx * 0.12, 0.15, 0.7))), 0.2, 0.1), (tuple(b + Vector((sx * 0.2, 0.3, 1.25))), 0.08, 0.06)], W_, n=6)
        P.loft([(tuple(b + Vector((0, -0.07, 0.15))), 0.09, 0.03), (tuple(b + Vector((sx * 0.12, 0.08, 0.7))), 0.12, 0.03)], PK, n=6, cap0=False)
    P.loft([((0, 1.1, 1.15), 0.32, 0.32), ((0, 1.35, 1.2), 0.3, 0.3), ((0, 1.5, 1.2), 0.1, 0.1)], WHITE, n=6)


def sheep(P):
    WOOL, FACE = rgb(250, 246, 232), rgb(60, 55, 60)
    q = quadruped(P, FACE, L=2.8, W=1.0, H=1.0, leg=0.9, legr=0.2, head=(0.5, 0.6, 0.55), snout=(0.32, 0.28, 0.25), hoof=BLACK, head_up=0.15,
                  ears=(0.45, 0.1, -0.05, 0.13))
    z0 = q['z0']
    for (x, y, z, r) in ((0, -0.7, 0.35, 0.95), (0, 0.3, 0.4, 1.0), (0, 1.1, 0.3, 0.85), (0.55, -0.2, 0.1, 0.7), (-0.55, -0.2, 0.1, 0.7),
                         (0.5, 0.8, 0.1, 0.65), (-0.5, 0.8, 0.1, 0.65), (0, -0.1, 0.8, 0.7), (0, -1.2, 0.5, 0.55)):
        P.loft([((x, y, z0 + z - r), r * 0.5, r * 0.5), ((x, y, z0 + z - r * 0.4), r * 0.95, r * 0.95), ((x, y, z0 + z + r * 0.3), r * 0.8, r * 0.8),
                ((x, y, z0 + z + r * 0.75), r * 0.3, r * 0.3)], WOOL, n=7, rot=0.3)
    hc = q['hc']
    P.loft([((0, hc.y + 0.1, hc.z + 0.42), 0.38, 0.2), ((0, hc.y + 0.3, hc.z + 0.55), 0.3, 0.16)], WOOL, n=6)


def cow(P):
    WH, BK, PK, HN = rgb(248, 248, 248), rgb(40, 38, 44), rgb(255, 170, 180), rgb(240, 230, 200)
    q = quadruped(P, spots(WH, BK, 0.62), L=3.4, W=1.25, H=1.2, leg=1.3, legr=0.3, head=(0.68, 0.75, 0.7), snout=(0.55, 0.42, 0.35),
                  snout_col=PK, ears=(0.5, 0.05, 0.05, 0.16), ear_col=WH, tail=(0.6, -1.2, 0.08, BK))
    hc = q['hc']
    for sx in (-1, 1):
        P.chain([(sx * 0.5, hc.y + 0.15, hc.z + 0.5), (sx * 0.8, hc.y + 0.1, hc.z + 0.7), (sx * 0.85, hc.y - 0.05, hc.z + 1.0)], [0.12, 0.09, 0.03], HN, n=5)
    P.loft([((0, 0.7, 1.35), 0.38, 0.25), ((0, 0.75, 1.15), 0.3, 0.2)], PK, n=6)            # udder


def bee(P):
    Y, K, WG = rgb(255, 205, 40), rgb(40, 34, 40), rgb(200, 235, 255)
    z = 2.0
    stripes = lambda c, n: K if int((c.y + 3) * 2.2) % 2 == 0 and c.y > -0.3 else Y
    P.loft([((0, -0.2, z), 0.4, 0.4), ((0, 0.2, z + 0.05), 1.0, 0.95), ((0, 0.9, z), 1.1, 1.0), ((0, 1.6, z - 0.15), 0.85, 0.8),
            ((0, 2.1, z - 0.3), 0.3, 0.3)], stripes, n=8)
    P.cone((0, 2.1, z - 0.3), (0, 2.55, z - 0.45), 0.14, K, n=4)
    P.loft([((0, -0.1, z + 0.1), 0.6, 0.6), ((0, -0.6, z + 0.25), 0.75, 0.75), ((0, -1.1, z + 0.2), 0.55, 0.55)], K, n=8)
    for sx in (-1, 1):
        P.eye((sx * 0.62, -1.0, z + 0.4), sx, 0.2)
        P.chain([(sx * 0.25, -1.0, z + 0.7), (sx * 0.45, -1.35, z + 1.3), (sx * 0.7, -1.4, z + 1.55)], [0.05, 0.05, 0.05], K, n=4)
        P.loft([((sx * 0.7, -1.4, z + 1.55), 0.12, 0.12), ((sx * 0.75, -1.45, z + 1.7), 0.08, 0.08)], K, n=5)
        P.tri((sx * 0.4, 0.0, z + 0.8), (sx * 0.4, 0.8, z + 0.85), (sx * 2.3, 0.9, z + 1.9), WG, 0.04)
        P.tri((sx * 0.4, 0.4, z + 0.75), (sx * 0.4, 1.0, z + 0.7), (sx * 1.7, 1.5, z + 1.0), WG, 0.04)
        for k in range(3):
            P.limb((sx * 0.5, -0.3 + k * 0.4, z - 0.6), (sx * 0.65, -0.4 + k * 0.4, z - 1.3), 0.06, 0.05, K, n=4)


def fox(P):
    OR, WH, BK = rgb(250, 120, 40), rgb(250, 245, 238), rgb(50, 36, 34)
    body = two_tone(OR, WH, -0.35)
    q = quadruped(P, body, L=2.8, W=0.85, H=0.8, leg=1.0, legr=0.18, head=(0.6, 0.6, 0.55), snout=(0.3, 0.25, 0.55), snout_col=WH, hoof=BK,
                  ears=(0.18, 0.1, 0.65, 0.2), ear_col=OR, head_up=0.3)
    hc = q['hc']
    for sx in (-1, 1):
        P.tri((sx * 0.55, hc.y - 0.2, hc.z - 0.3), (sx * 0.62, hc.y + 0.1, hc.z - 0.35), (sx * 0.85, hc.y + 0.05, hc.z - 0.75), WH, 0.06)   # cheek fluff
    tb = Vector((0, 1.4, q['z0'] + 0.1))
    P.loft([(tuple(tb), 0.25, 0.25), (tuple(tb + Vector((0, 0.6, 0.3))), 0.55, 0.55), (tuple(tb + Vector((0, 1.3, 0.75))), 0.55, 0.55),
            (tuple(tb + Vector((0, 1.8, 1.05))), 0.4, 0.4), (tuple(tb + Vector((0, 2.1, 1.2))), 0.05, 0.05)],
           lambda c, n: WH if c.y > tb.y + 1.55 else OR, n=7)


def boar(P):
    BR, DK, TK = rgb(110, 76, 58), rgb(70, 46, 36), rgb(250, 242, 220)
    q = quadruped(P, two_tone(BR, rgb(150, 110, 85)), L=3.2, W=1.25, H=1.25, leg=0.9, legr=0.28, neck=0.1, head=(0.75, 0.75, 0.75),
                  snout=(0.45, 0.4, 0.55), snout_col=rgb(200, 140, 120), ears=(0.25, 0.2, 0.45, 0.2), ear_col=DK, tail=(0.4, 0.3, 0.07, DK), head_up=0.0)
    sn = q['sn']
    for sx in (-1, 1):
        P.chain([(sx * 0.4, sn.y - 0.2, sn.z - 0.2), (sx * 0.62, sn.y - 0.45, sn.z + 0.1), (sx * 0.6, sn.y - 0.55, sn.z + 0.5)], [0.1, 0.08, 0.02], TK, n=5)
    for k in range(9):                                                   # bristle ridge along the back
        y = -1.6 + k * 0.38
        z = q['z0'] + q['H'] * 0.95 - abs(k - 3) * 0.04
        P.cone((0, y, z - 0.15), (0, y + 0.3, z + 0.55 - (k % 2) * 0.2), 0.22, DK, n=4)


def owl(P):
    BR, CR, DK = rgb(180, 130, 80), rgb(250, 240, 220), rgb(110, 76, 50)
    bird_t(P, BR, CR, DK, H=1.6, W=1.15, beak_col=rgb(240, 200, 120))
    P.loft([((0, -1.62, 3.05), 0.8, 0.62), ((0, -1.75, 3.05), 0.7, 0.52)], CR, n=8)          # light facial disc
    for sx in (-1, 1):                                                   # ear tufts + big eyes on the disc
        P.cone((sx * 0.45, -1.15, 3.55), (sx * 0.7, -1.0, 4.2), 0.2, DK, n=4)
        P.loft([((sx * 0.33, -1.76, 3.12), 0.24, 0.24), ((sx * 0.33, -1.82, 3.12), 0.22, 0.22)], rgb(255, 170, 40), n=8)
        P.box((sx * 0.33, -1.86, 3.12), (0.12, 0.03, 0.12), BLACK)
        P.box((sx * 0.29, -1.9, 3.18), (0.04, 0.02, 0.04), WHITE)


def bear(P):
    BR, LT, DK = rgb(120, 78, 48), rgb(200, 160, 120), rgb(60, 40, 30)
    q = quadruped(P, BR, L=3.6, W=1.6, H=1.55, leg=1.1, legr=0.42, neck=0.1, head=(0.95, 0.85, 0.9), snout=(0.5, 0.42, 0.45), snout_col=LT,
                  hoof=DK, head_up=0.15, tail=(0.2, 0.1, 0.18))
    hc = q['hc']
    for sx in (-1, 1):
        P.loft([((sx * 0.75, hc.y + 0.3, hc.z + 0.7), 0.26, 0.12), ((sx * 0.8, hc.y + 0.32, hc.z + 1.0), 0.22, 0.1)], BR, n=6)
    P.loft([((0, -1.3, q['z0'] + 1.45), 0.9, 0.5), ((0, -0.6, q['z0'] + 1.75), 1.1, 0.55), ((0, 0.2, q['z0'] + 1.5), 0.9, 0.4)], BR, n=7)   # shoulder hump
    P.glow = True                                                         # Epic: glowing honey drips
    for x, y in ((0.3, -0.6), (-0.4, 0.1), (0.1, 0.6)):
        P.loft([((x, y, q['z0'] + 1.75), 0.28, 0.12), ((x, y - 0.05, q['z0'] + 1.55), 0.1, 0.1)], rgb(255, 190, 40), n=6)
    P.glow = False


def stag(P):
    GD, LT, AN = rgb(255, 196, 60), rgb(255, 240, 200), rgb(255, 250, 200)
    q = quadruped(P, two_tone(GD, LT, -0.3), L=3.0, W=0.95, H=0.95, leg=1.8, legr=0.18, neck=0.9, head=(0.55, 0.7, 0.55), snout=(0.32, 0.28, 0.45),
                  snout_col=LT, hoof=rgb(130, 90, 40), ears=(0.5, 0.15, 0.15, 0.14), head_up=0.9, tail=(0.25, 0.25, 0.12, LT))
    hc = q['hc']
    P.glow = True                                                         # Legendary: glowing antlers
    for sx in (-1, 1):
        b = Vector((sx * 0.25, hc.y + 0.15, hc.z + 0.5))
        main = [b, b + Vector((sx * 0.3, 0.1, 0.6)), b + Vector((sx * 0.75, 0.3, 1.2)), b + Vector((sx * 1.05, 0.5, 1.9))]
        P.chain([tuple(p) for p in main], [0.09, 0.08, 0.07, 0.03], AN, n=5)
        for k, p in enumerate(main[1:3]):
            P.chain([tuple(p), tuple(p + Vector((sx * 0.1, -0.35, 0.5 + k * 0.15)))], [0.06, 0.02], AN, n=4)
        P.chain([tuple(main[2]), tuple(main[2] + Vector((sx * 0.55, 0.2, 0.25)))], [0.06, 0.02], AN, n=4)
    P.glow = False


def lion(P):
    GD, MN, LT, MN2 = rgb(240, 170, 70), rgb(200, 80, 30), rgb(255, 230, 180), rgb(255, 140, 40)
    q = quadruped(P, two_tone(GD, LT, -0.35), L=3.8, W=1.35, H=1.3, leg=1.6, legr=0.34, neck=0.3, head=(0.85, 0.85, 0.85), snout=(0.5, 0.42, 0.45),
                  snout_col=LT, hoof=rgb(170, 110, 50), head_up=0.4, tail=(1.0, -0.4, 0.1))
    hc = q['hc']
    # big mane: a ring of cones around the head, two layers
    for layer, (r, ln, col) in enumerate(((1.35, 1.1, MN), (1.0, 0.85, MN2))):
        for k in range(12):
            a = 2 * math.pi * k / 12
            d = Vector((math.cos(a), 0, math.sin(a)))
            base = hc + Vector((0, 0.2 + layer * 0.12, 0.05)) + d * r * 0.55
            P.cone(base, base + d * ln + Vector((0, 0.2, 0)), 0.48 - layer * 0.1, col, n=4)
    P.glow = True                                                          # Mythic: blazing tail tip + crown of light
    tt = Vector((0, q['L'] * 0.52 + 1.0, q['z0'] - 0.3))
    P.cone(tt, tt + Vector((0, 0.3, 0.9)), 0.3, rgb(255, 200, 60), n=5)
    for k in range(6):
        a = 2 * math.pi * k / 6
        P.cone(hc + Vector((math.cos(a) * 0.45, math.sin(a) * 0.45 + 0.1, 1.15)), hc + Vector((math.cos(a) * 0.55, math.sin(a) * 0.55 + 0.1, 1.65)),
               0.12, rgb(255, 230, 90), n=4)
    P.glow = False


PETS = [('Meadow Bunny', 'Common', bunny), ('Fluffy Sheep', 'Common', sheep), ('Spotted Cow', 'Common', cow),
        ('Bumble Bee', 'Uncommon', bee), ('Red Fox', 'Uncommon', fox), ('Wild Boar', 'Rare', boar), ('Barn Owl', 'Rare', owl),
        ('Honey Grizzly', 'Epic', bear), ('Golden Stag', 'Legendary', stag), ('Sun Lion', 'Mythic', lion)]

if __name__ == '__main__':
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc, cam = LL.stage()
    for i, (name, rar, fn) in enumerate(PETS):
        P = LP(name, smooth=True)
        fn(P)
        sm, px = LL.make_both(P)
        for o in bpy.data.objects:
            if o.type == 'MESH' and o.name != 'Plane':
                o.hide_render = o not in (sm,)
        LL.shoot(sc, cam, sm, OUT / f'{i + 1:02d}_3d.png')
        sm.hide_render, px.hide_render = True, False
        LL.shoot(sc, cam, px, OUT / f'{i + 1:02d}.png')
        px.hide_render = True
        print(name, len(px.data.polygons), 'faces')
    print('done')
