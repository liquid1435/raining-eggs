r"""Raining Eggs - map generator (single source of truth).

  py gen_map.py            -> map.json
  blender -b --python render_map.py -- all     -> renders\*.png
  py to_rbxlx.py                               -> RAINING EGGS - HARTA.rbxlx

Units = Roblox studs, Y up. Layout (top view): one long island along +Z.
  z -122..-58  : row of 8 player bases (each under a giant umbrella), they face +Z
  z  -58..0    : plaza (spawn, shops, boards)
  z    0..980  : 7 zones of 140 studs, each with its own look, a gate arch and its own egg clouds
"""
import json
import math
import pathlib
import random

HERE = pathlib.Path(__file__).resolve().parent
rng = random.Random(20261111)


# ------------------------------------------------------------------ CFrame maths
def mmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def mvec(a, v):
    return [sum(a[i][k] * v[k] for k in range(3)) for i in range(3)]


I3 = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]


def rx(d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return [[1, 0, 0], [0, c, -s], [0, s, c]]


def ry(d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return [[c, 0, s], [0, 1, 0], [-s, 0, c]]


def rz(d):
    c, s = math.cos(math.radians(d)), math.sin(math.radians(d))
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


class CF:
    __slots__ = ('p', 'r')

    def __init__(self, x=0, y=0, z=0, r=None):
        self.p = [x, y, z]
        self.r = r or I3

    def __mul__(self, o):
        return CF(*[a + b for a, b in zip(self.p, mvec(self.r, o.p))], r=mmul(self.r, o.r))


def C(x=0, y=0, z=0):
    return CF(x, y, z)


def R(xd=0, yd=0, zd=0):
    return CF(r=mmul(mmul(rx(xd), ry(yd)), rz(zd)))


# ------------------------------------------------------------------ scene
PARTS = []
GROUP = ['Map']
_GID = [0]


class group:
    def __init__(self, name, unique=True):
        self.name, self.unique = name, unique

    def __enter__(self):
        _GID[0] += 1
        GROUP.append(f'{self.name}#{_GID[0]}' if self.unique else self.name)

    def __exit__(self, *a):
        GROUP.pop()


def part(size, cf, color, mat='SmoothPlastic', shape='Block', **kw):
    d = {'cls': 'Part', 'shape': shape, 'size': [round(s, 3) for s in size], 'p': [round(v, 3) for v in cf.p],
         'r': [round(v, 5) for row in cf.r for v in row], 'c': list(color), 'm': mat, 'g': '/'.join(GROUP)}
    d.update(kw)
    PARTS.append(d)
    return d


def blk(x, y0, z, sx, sy, sz, col, mat='SmoothPlastic', yaw=0, **kw):
    cf = C(x, y0 + sy / 2, z)
    if yaw:
        cf = cf * R(0, yaw, 0)
    return part((sx, sy, sz), cf, col, mat, **kw)


def vcyl(x, y0, z, h, d, col, mat='SmoothPlastic', **kw):
    return part((h, d, d), C(x, y0 + h / 2, z) * R(0, 0, 90), col, mat, 'Cylinder', **kw)


def sph(x, y, z, d, col, mat='SmoothPlastic', **kw):
    return part((d, d, d), C(x, y, z), col, mat, 'Ball', **kw)


def light(p, color, rng_=16, br=1.5):
    p.setdefault('lights', []).append(dict(kind='PointLight', c=list(color), range=rng_, br=br))


def sign(p, face, title, sub=None, fg=(255, 255, 255), bg1=(60, 110, 255), bg2=(30, 60, 200), stroke=(14, 20, 48), pps=20):
    p.setdefault('signs', []).append(dict(face=face, title=title, sub=sub, fg=list(fg), bg1=list(bg1), bg2=list(bg2), stroke=list(stroke), pps=pps))


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


NC = dict(cancollide=False)
WHITE = (245, 247, 252)
CREAM = (250, 240, 214)
BROWN = (124, 84, 52)
DBROWN = (92, 60, 38)
DIRT = (150, 106, 70)
GOLD = (255, 204, 40)
INK = (24, 28, 52)
RED = (240, 66, 66)

HALF = 176          # playable half width
ZL = 140            # zone length
ROADW = 18


def side_x(lo=16, hi=164):
    return rng.choice((-1, 1)) * rng.uniform(lo, hi)


# ------------------------------------------------------------------ shared props
def tree(x, z, s=1.0, leaf=(74, 176, 70), trunk=BROWN):
    blk(x, 0, z, 2 * s, 6 * s, 2 * s, trunk, 'Wood')
    blk(x, 5 * s, z, 7 * s, 4 * s, 7 * s, leaf, 'Grass')
    blk(x, 9 * s, z, 5 * s, 3 * s, 5 * s, shade(leaf, 1.1), 'Grass')
    blk(x, 12 * s, z, 2.6 * s, 2 * s, 2.6 * s, shade(leaf, 1.2), 'Grass')


def flower(x, z, col):
    blk(x, 0, z, 0.4, 1.6, 0.4, (70, 160, 70), **NC)
    blk(x, 1.6, z, 1.2, 1.2, 1.2, col, **NC)


def rock(x, z, s, col):
    blk(x, 0, z, 4 * s, 2.4 * s, 3.4 * s, col, 'Slate', yaw=rng.uniform(0, 90))
    blk(x + 1.2 * s, 0, z + 0.8 * s, 2.4 * s, 3.6 * s, 2.4 * s, shade(col, 1.12), 'Slate', yaw=rng.uniform(0, 90))


def cloud(x, y, z, s, col):
    blk(x, y, z, 30 * s, 8 * s, 18 * s, col, **NC)
    blk(x - 4 * s, y + 6 * s, z, 18 * s, 7 * s, 13 * s, shade(col, 1.04), **NC)
    blk(x + 13 * s, y + 3 * s, z + 2 * s, 14 * s, 7 * s, 12 * s, col, **NC)
    blk(x - 15 * s, y + 2 * s, z - 2 * s, 12 * s, 6 * s, 11 * s, shade(col, 0.97), **NC)


def egg(x, y, z, s, col, spot=None, beam=False):
    sph(x, y, z, 3.0 * s, col, name='DemoEgg', **NC)
    sph(x, y + 1.0 * s, z, 2.35 * s, col, name='DemoEgg', **NC)
    if spot:
        for k, a in enumerate((10, 80, 150, 220, 290, 45, 185, 320)):
            yy, rr = ((-0.45, 1.38), (0.35, 1.42), (1.25, 1.12))[k % 3]
            sph(x + rr * s * math.cos(math.radians(a)), y + yy * s, z + rr * s * math.sin(math.radians(a)), 0.62 * s, spot, **NC)
    if beam:
        vcyl(x, y + 2 * s, z, 90, 1.6 * s, col, 'Neon', transparency=0.72, **NC)


def patches(z0, z1, col, n=46, y=0.0):
    for _ in range(n):
        w, d = rng.choice((6, 8, 10, 14)), rng.choice((6, 8, 10, 14))
        blk(side_x(12, 166), y, rng.uniform(z0 + 8, z1 - 8), w, 0.14, d, col, **NC)


def gate(z, title, sub, c1, c2, pill=WHITE):
    """arch over the road at the start of a zone, sign faces the players coming from -Z"""
    for sx in (-1, 1):
        blk(sx * 14, 0, z, 5, 22, 5, pill)
        blk(sx * 14, 0, z, 6, 2, 6, c2)
        blk(sx * 14, 10, z, 5.4, 2, 5.4, c1)
        blk(sx * 14, 22, z, 6.4, 2, 6.4, c2)
        egg(sx * 14, 26.2, z, 1.5, c1, WHITE)
    b = blk(0, 15, z, 34, 8, 3, c2)
    sign(b, 'Front', title, sub, bg1=c1, bg2=c2)
    sign(b, 'Back', title, sub, bg1=c1, bg2=c2)
    # border line with flags across the whole width
    for sx in (-1, 1):
        blk(sx * (HALF + 14) / 2 + sx * 2, 0, z, HALF - 18, 0.3, 2.4, c1, **NC)
        for x in range(34, HALF - 4, 28):
            blk(sx * x, 0, z, 0.8, 9, 0.8, WHITE, **NC)
            blk(sx * x + 2.2, 6, z, 4, 2.6, 0.4, c1, **NC)


def zone_base(i, ground, gmat, road, cliff, dirt=DIRT):
    z0 = i * ZL
    zc = z0 + ZL / 2
    blk(0, -4, zc, HALF * 2 + 48, 4, ZL, ground, gmat)
    blk(0, -13, zc, HALF * 2 + 40, 9, ZL - 2, dirt, 'Slate')
    blk(0, 0, zc, ROADW, 0.3, ZL, road)
    for sx in (-1, 1):
        blk(sx * (ROADW / 2 + 0.6), 0, zc, 1.2, 0.7, ZL, shade(road, 0.8))
        for z in range(int(z0), int(z0 + ZL), 20):          # stepped cliffs = side walls
            h = rng.choice((10, 14, 18, 22, 28))
            blk(sx * (HALF + 12), -4, z + 10, 24, h + 4, 20, cliff, 'Slate')
            blk(sx * (HALF + 12), h, z + 10, 24, 2, 20, ground, gmat)
            if rng.random() < 0.6:
                blk(sx * (HALF - 3), -4, z + 10, 8, h * 0.45 + 4, 12, shade(cliff, 1.08), 'Slate')
        blk(sx * (HALF + 25), 0, zc, 2, 120, ZL, WHITE, transparency=1, name='Wall')
    return z0, zc


def egg_sky(z0, cloudcol, eggs):
    """clouds above the zone + a few eggs frozen in mid-fall (the game script replaces them)"""
    for k in range(5):
        cloud(rng.uniform(-130, 130), rng.uniform(88, 116), z0 + 14 + k * 27, rng.uniform(0.9, 1.4), cloudcol)
    for k in range(11):
        col, spot = rng.choice(eggs)
        egg(rng.uniform(-150, 150), rng.uniform(4, 78), rng.uniform(z0 + 10, z0 + ZL - 10), rng.choice((1.0, 1.0, 1.3)), col, spot,
            beam=(k == 0))


# ------------------------------------------------------------------ home: bases + plaza
BASE_COLS = [((240, 70, 70), 'RED'), ((255, 150, 40), 'ORANGE'), ((255, 214, 50), 'YELLOW'), ((90, 200, 80), 'GREEN'),
             ((60, 200, 230), 'CYAN'), ((70, 120, 250), 'BLUE'), ((160, 100, 250), 'PURPLE'), ((255, 120, 190), 'PINK')]


def base(i):
    col, _ = BASE_COLS[i]
    bx = -147 + i * 42
    zf, zb = -60, -112
    zc = (zf + zb) / 2
    with group(f'Base{i + 1}', unique=False):
        blk(bx, 0, zc, 34, 1, zf - zb, (236, 240, 248), name='Floor')
        for tz in range(zb + 4, zf, 8):                       # checker tiles
            for k, tx in enumerate(range(-12, 13, 8)):
                if (tz // 8 + k) % 2 == 0:
                    blk(bx + tx, 1, tz + 0.5, 8, 0.1, 8, shade(col, 1.0) if False else (218, 226, 242), **NC)
        for sx in (-1, 1):                                    # side fence
            blk(bx + sx * 17.5, 0, zc, 1.4, 4, zf - zb + 1.4, col)
            blk(bx + sx * 17.5, 4, zc, 2, 0.8, zf - zb + 2, WHITE)
            blk(bx + sx * 12, 0, zf, 3, 9, 3, col)             # gate posts
            egg(bx + sx * 12, 11.2, zf, 1.1, WHITE, col)
        back = blk(bx, 0, zb, 36.4, 12, 1.6, col)
        sign(back, 'Back', 'UPGRADES', 'basket  •  speed  •  luck', bg1=shade(col, 1.05), bg2=shade(col, 0.7), pps=14)
        blk(bx, 12, zb, 37, 1, 2.2, WHITE)
        gb = blk(bx, 9, zf, 27, 4, 1.4, col, name='OwnerSign')
        sign(gb, 'Back', f'NEST {i + 1}', 'EMPTY', bg1=shade(col, 1.05), bg2=shade(col, 0.7))
        sign(gb, 'Front', f'NEST {i + 1}', 'EMPTY', bg1=shade(col, 1.05), bg2=shade(col, 0.7))
        # giant umbrella
        ux, uz = bx, zb + 16
        vcyl(ux, 1, uz, 40, 2.2, (250, 250, 250), 'Metal')
        for k, (d, h) in enumerate(((46, 1.6), (38, 1.6), (29, 1.6), (19, 1.6), (9, 1.6))):
            vcyl(ux, 41 + k * 1.6, uz, h, d, col if k % 2 == 0 else WHITE, name='Umbrella')
        sph(ux, 49.6, uz, 2.6, GOLD)
        # 10 straw nests (pet slots) along the sides
        for sx in (-1, 1):
            for k in range(5):
                nz = zb + 8 + k * 9
                nx = bx + sx * 11.5
                vcyl(nx, 1, nz, 1.2, 6, (222, 180, 96), 'Sand', name='PetSlot')
                vcyl(nx, 2.2, nz, 0.5, 4.2, (190, 146, 70), 'Sand', **NC)
                blk(nx - sx * 4.4, 1, nz, 2.6, 0.3, 2.6, (90, 230, 110), 'Neon', name='Collect', **NC)
        # incubator
        ix, iz = bx, zb + 30
        vcyl(ix, 1, iz, 1.6, 9, shade(col, 0.8), name='Incubator')
        vcyl(ix, 2.6, iz, 0.6, 7.4, WHITE)
        sph(ix, 6.6, iz, 8, (190, 235, 255), 'Glass', transparency=0.55, **NC)
        egg(ix, 5.2, iz, 1.3, CREAM, col)
        hb = blk(ix, 11.5, iz, 9, 2.6, 0.8, INK)
        sign(hb, 'Back', 'HATCH', bg1=(255, 196, 40), bg2=(240, 130, 20), pps=24)
        blk(ix - 4.2, 1, iz, 0.6, 12, 0.6, WHITE)
        blk(ix + 4.2, 1, iz, 0.6, 12, 0.6, WHITE)
        # treadmill (speed training)
        tx, tz = bx - 5.5, zf - 8
        blk(tx, 1, tz, 5, 0.8, 9, (40, 44, 60), name='Treadmill')
        blk(tx, 1.8, tz, 4, 0.2, 8, (70, 76, 96), **NC)
        for sx in (-1, 1):
            blk(tx + sx * 2.3, 1, tz - 3.6, 0.5, 5, 0.5, col)
        tb = blk(tx, 5.4, tz - 3.6, 5.2, 2.2, 0.6, INK)
        sign(tb, 'Back', 'SPEED', bg1=(70, 200, 255), bg2=(40, 110, 240), pps=24)
        # basket rack
        rx_, rz_ = bx + 6, zf - 8
        blk(rx_, 1, rz_, 6, 0.6, 4, BROWN, 'Wood')
        vcyl(rx_, 1.6, rz_, 2.6, 4.4, (214, 160, 86), 'Sand', name='Basket')
        vcyl(rx_, 4.0, rz_, 0.5, 5, (176, 124, 60), 'Sand', **NC)


def stall(x, z, title, sub, col, prop):
    with group('Shop'):
        blk(x, 0, z, 22, 0.6, 14, (236, 226, 204))
        blk(x, 0.6, z - 4, 18, 4, 3, BROWN, 'WoodPlanks')
        blk(x, 4.6, z - 4, 19, 0.6, 4, CREAM)
        for sx in (-1, 1):
            blk(x + sx * 9.5, 0.6, z - 5.5, 1, 13, 1, WHITE)
            blk(x + sx * 9.5, 0.6, z + 5.5, 1, 13, 1, WHITE)
        blk(x, 0.6, z + 6, 20, 13, 1, shade(col, 0.8))
        for k in range(10):                                   # striped awning
            part((2.2, 0.8, 15), C(x - 9.9 + k * 2.2, 14.6, z - 1) * R(-12, 0, 0), col if k % 2 == 0 else WHITE)
        sb = blk(x, 16.5, z - 7, 18, 5, 1.2, INK)
        sign(sb, 'Front', title, sub, bg1=shade(col, 1.08), bg2=shade(col, 0.68))
        prop(x, z - 4)


def prop_basket(x, z):
    vcyl(x - 4, 5.2, z, 3, 5, (214, 160, 86), 'Sand')
    vcyl(x + 2, 5.2, z, 4.2, 6.6, (176, 124, 60), 'Sand')
    egg(x + 2, 10.2, z, 1.1, (255, 120, 190), WHITE)


def prop_clover(x, z):
    for dx, dy in ((-1.6, 0), (1.6, 0), (0, 1.6), (0, -1.6)):
        blk(x + dx, 7.4 + dy, z, 2.8, 2.8, 1, (70, 210, 90), **NC)
    blk(x, 5.2, z, 0.6, 2.4, 0.6, (50, 150, 60), **NC)
    blk(x + 5.5, 5.2, z, 3, 3, 3, WHITE, yaw=20)
    blk(x - 5.5, 5.2, z, 3, 3, 3, (255, 80, 80), yaw=-25)


def prop_coins(x, z):
    for k in range(5):
        vcyl(x - 5 + k * 2.5, 5.2, z, 0.6 + 0.6 * (k % 3), 2.4, GOLD, 'Foil')
    blk(x + 6, 5.2, z, 3.4, 2.6, 2.6, (60, 190, 90))


def prop_book(x, z):
    blk(x, 5.2, z, 6, 1.2, 4.4, (90, 110, 240), yaw=12)
    blk(x, 6.4, z, 5.4, 0.8, 4, CREAM, yaw=12)
    egg(x - 5.5, 6.6, z, 0.9, (160, 100, 250), GOLD)
    egg(x + 5.5, 6.6, z, 0.9, (60, 200, 230), WHITE)


def home():
    G, G2 = (118, 204, 84), (102, 188, 72)
    with group('Ground', unique=False):
        blk(0, -4, -64, HALF * 2 + 48, 4, 128, G, 'Grass')
        blk(0, -13, -64, HALF * 2 + 40, 9, 126, DIRT, 'Slate')
        patches(-58, 0, G2, 26)
        blk(0, 0, -49, HALF * 2 - 8, 0.3, 18, (240, 228, 196))          # promenade in front of the bases
        blk(0, 0, -29, ROADW, 0.3, 58, (240, 228, 196))
        vcyl(0, 0, -30, 0.35, 46, (232, 216, 178))
        vcyl(0, 0.35, -30, 0.1, 38, (246, 236, 208), **NC)
        for sx in (-1, 1):
            for z in range(-128, 0, 20):
                h = rng.choice((12, 16, 22, 28))
                blk(sx * (HALF + 12), -4, z + 10, 24, h + 4, 20, (128, 132, 150), 'Slate')
                blk(sx * (HALF + 12), h, z + 10, 24, 2, 20, G, 'Grass')
            blk(sx * (HALF + 25), 0, -64, 2, 120, 128, WHITE, transparency=1, name='Wall')
        for x in range(-HALF - 24, HALF + 25, 24):                         # back cliff behind the bases
            h = rng.choice((22, 28, 34, 40))
            blk(x + 12, -4, -136, 24, h + 4, 20, (128, 132, 150), 'Slate')
            blk(x + 12, h, -136, 24, 2, 20, G, 'Grass')
            if rng.random() < 0.5:
                tree(x + 12, -136 + rng.uniform(-4, 4), 1.3)
        blk(0, 0, -125, HALF * 2 + 48, 120, 2, WHITE, transparency=1, name='Wall')
    for i in range(8):
        base(i)
    with group('Plaza', unique=False):
        sp = blk(0, 0.35, -44, 12, 0.6, 12, (255, 255, 255), 'Neon', spawn=True)
        blk(0, 0.3, -44, 15, 0.3, 15, GOLD)
        # cracked giant egg statue
        vcyl(0, 0.4, -22, 2.4, 18, (214, 220, 236), 'Marble')
        vcyl(0, 2.8, -22, 1.2, 14, WHITE, 'Marble')
        sph(0, 11, -22, 15, CREAM)
        sph(0, 16.5, -22, 11.5, CREAM)
        for a, c in ((10, (255, 120, 190)), (100, (60, 200, 230)), (190, GOLD), (280, (160, 100, 250)), (55, (90, 200, 80))):
            sph(7.2 * math.cos(math.radians(a)), 10 + (a % 3), -22 + 7.2 * math.sin(math.radians(a)), 3.2, c)
        stall(-52, -16, 'BASKETS', 'catch more eggs', (255, 150, 40), prop_basket)
        stall(52, -16, 'LUCK SHOP', 'better eggs fall on you', (70, 200, 90), prop_clover)
        stall(-96, -16, 'SELL', 'pets and eggs for cash', (255, 204, 40), prop_coins)
        stall(96, -16, 'INDEX', 'every pet you found', (120, 110, 250), prop_book)
        for x, t, s, c in ((-140, 'TOP LUCK', 'rarest hatch today', (160, 100, 250)), (140, 'TOP CATCHERS', 'most eggs caught', (60, 190, 230))):
            blk(x, 0, -14, 2, 4, 2, WHITE)
            b = blk(x, 4, -14, 20, 14, 1.4, INK, name='Leaderboard')
            sign(b, 'Front', t, s, bg1=shade(c, 1.05), bg2=shade(c, 0.6), pps=16)
        for x in (-150, -120, -74, -30, 30, 74, 120, 150):
            tree(x, rng.uniform(-36, -30), rng.uniform(0.8, 1.1))
        for _ in range(40):
            flower(side_x(12, 160), rng.uniform(-38, -4), rng.choice(((255, 90, 90), (255, 214, 50), WHITE, (255, 120, 190))))


# ------------------------------------------------------------------ zone 1: Sunny Meadow
def z_meadow(i):
    G, G2 = (110, 200, 78), (94, 182, 66)
    with group(f'Zone{i + 1}_SunnyMeadow', unique=False):
        z0, zc = zone_base(i, G, 'Grass', (238, 222, 180), (130, 134, 152))
        patches(z0, z0 + ZL, G2)
        for _ in range(22):
            tree(side_x(18, 160), rng.uniform(z0 + 8, z0 + ZL - 8), rng.uniform(0.8, 1.5), rng.choice(((74, 176, 70), (96, 196, 70), (60, 160, 80))))
        for _ in range(80):
            flower(side_x(12, 164), rng.uniform(z0 + 4, z0 + ZL - 4), rng.choice(((255, 90, 90), (255, 214, 50), WHITE, (255, 120, 190), (130, 120, 255))))
        for _ in range(9):                                   # hay bales
            x, z = side_x(20, 150), rng.uniform(z0 + 10, z0 + ZL - 10)
            part((5, 5, 5), C(x, 2.5, z) * R(0, rng.uniform(0, 180), 0), (240, 204, 90), 'Sand', 'Cylinder')
        # pond
        px, pz = -88, z0 + 52
        blk(px, 0, pz, 46, 0.25, 34, (236, 220, 170), 'Sand')
        blk(px, 0.1, pz, 40, 0.3, 28, (70, 180, 240), 'Glass', **NC)
        blk(px - 6, 0.3, pz + 3, 4, 0.2, 4, (80, 190, 90), **NC)
        blk(px + 9, 0.3, pz - 6, 3, 0.2, 3, (80, 190, 90), **NC)
        # windmill
        wx, wz = 92, z0 + 70
        for k in range(6):
            blk(wx, k * 6, wz, 16 - k * 1.6, 6, 16 - k * 1.6, CREAM if k % 2 == 0 else (236, 222, 190))
        blk(wx, 36, wz, 10, 5, 10, RED)
        blk(wx, 41, wz, 6, 3, 6, shade(RED, 0.85))
        blk(wx, 0, wz - 8.2, 4, 7, 0.6, BROWN, 'Wood')
        for k in range(4):
            part((2.6, 22, 0.8), C(wx, 32, wz - 9.4) * R(0, 0, 25 + k * 90) * C(0, 12, 0), WHITE, name='Blade')
            part((1, 24, 0.5), C(wx, 32, wz - 9.0) * R(0, 0, 25 + k * 90) * C(0, 12, 0), BROWN, 'Wood')
        blk(wx, 31, wz - 9.2, 3, 3, 2, DBROWN)
        # barn
        bx, bz = -120, z0 + 108
        blk(bx, 0, bz, 30, 14, 22, (214, 64, 56), 'WoodPlanks')
        for k in range(5):
            blk(bx, 14 + k * 2.4, bz, 32 - k * 6.4, 2.4, 24, (120, 70, 52) if k else WHITE, 'Wood')
        blk(bx, 0, bz - 11.2, 9, 10, 0.6, WHITE)
        blk(bx, 0, bz - 11.4, 7, 9, 0.6, (150, 44, 40))
        for x in range(-150, -84, 6):                         # fence
            blk(x, 0, z0 + 90, 0.8, 4, 0.8, WHITE)
        blk(-118, 2.6, z0 + 90, 66, 0.6, 0.5, WHITE)
        blk(-118, 1.2, z0 + 90, 66, 0.6, 0.5, WHITE)
        for _ in range(8):
            rock(side_x(20, 160), rng.uniform(z0 + 6, z0 + ZL - 6), rng.uniform(0.8, 1.6), (150, 154, 170))
        egg_sky(z0, WHITE, [(CREAM, (150, 200, 120)), (CREAM, BROWN), ((180, 230, 150), WHITE)])


# ------------------------------------------------------------------ zone 2: Mushroom Grove
def mushroom(x, z, h, d, cap, dots=WHITE, glow=False):
    vcyl(x, 0, z, h, d * 0.3, CREAM)
    m = 'Neon' if glow else 'SmoothPlastic'
    blk(x, h, z, d, d * 0.2, d, cap, m, name='Bounce')
    blk(x, h + d * 0.2, z, d * 0.72, d * 0.17, d * 0.72, cap, m)
    blk(x, h + d * 0.37, z, d * 0.4, d * 0.12, d * 0.4, cap, m)
    if not glow:
        for dx, dz in ((-0.34, -0.3), (0.3, -0.34), (-0.3, 0.34), (0.36, 0.3)):
            blk(x + dx * d, h + d * 0.2, z + dz * d, d * 0.13, d * 0.06, d * 0.13, dots, **NC)
        blk(x, h + d * 0.49, z, d * 0.16, d * 0.04, d * 0.16, dots, **NC)


def z_mushroom(i):
    G, G2 = (98, 84, 170), (84, 70, 150)
    caps = [(232, 60, 70), (255, 140, 40), (236, 80, 190), (70, 190, 220)]
    with group(f'Zone{i + 1}_MushroomGrove', unique=False):
        z0, zc = zone_base(i, G, 'Grass', (196, 176, 236), (70, 62, 110), (72, 58, 96))
        patches(z0, z0 + ZL, G2)
        for _ in range(17):
            mushroom(side_x(22, 156), rng.uniform(z0 + 12, z0 + ZL - 12), rng.uniform(8, 24), rng.uniform(12, 24), rng.choice(caps))
        for _ in range(46):
            x, z = side_x(12, 164), rng.uniform(z0 + 4, z0 + ZL - 4)
            p = None
            mushroom(x, z, rng.uniform(1.4, 3), rng.uniform(2, 3.6), rng.choice(((90, 240, 230), (190, 130, 255), (130, 255, 150))), glow=True)
        # mega mushroom house
        hx, hz = 96, z0 + 76
        vcyl(hx, 0, hz, 30, 24, CREAM)
        blk(hx, 30, hz, 62, 10, 62, (232, 60, 70), name='Bounce')
        blk(hx, 40, hz, 46, 9, 46, (232, 60, 70))
        blk(hx, 49, hz, 26, 6, 26, (232, 60, 70))
        for dx, dz in ((-20, -18), (18, -20), (-18, 20), (22, 18), (0, 0)):
            blk(hx + dx, 40 if dx else 55, hz + dz, 8, 2, 8, WHITE, **NC)
        blk(hx, 0, hz - 12.2, 7, 11, 0.8, DBROWN, 'Wood')
        for sx in (-1, 1):
            w = blk(hx + sx * 7, 14, hz - 11.6, 4, 4, 0.8, (255, 230, 120), 'Neon')
            light(w, (255, 220, 120), 18, 1.2)
        for _ in range(7):                                    # fallen logs
            x, z = side_x(20, 150), rng.uniform(z0 + 10, z0 + ZL - 10)
            part((rng.uniform(10, 18), 3.4, 3.4), C(x, 1.7, z) * R(0, rng.uniform(0, 180), 0), DBROWN, 'Wood', 'Cylinder')
        for _ in range(34):                                   # glowing spores
            sph(rng.uniform(-160, 160), rng.uniform(6, 40), rng.uniform(z0 + 4, z0 + ZL - 4), rng.uniform(0.5, 1.1),
                rng.choice(((140, 255, 240), (220, 170, 255))), 'Neon', **NC)
        egg_sky(z0, (214, 196, 250), [((190, 130, 255), WHITE), ((232, 60, 70), WHITE), ((90, 240, 230), (98, 84, 170))])


# ------------------------------------------------------------------ zone 3: Candy Canyon
def lollipop(x, z, h, d, c1, c2):
    vcyl(x, 0, z, h, 0.9, WHITE)
    for k, (dd, t, c) in enumerate(((d, 1.6, c1), (d * 0.68, 2.0, c2), (d * 0.36, 2.4, c1), (d * 0.12, 2.8, c2))):
        part((t, dd, dd), C(x, h + d / 2 - 1, z) * R(0, 90, 0), c, 'SmoothPlastic', 'Cylinder')


def candy_cane(x, z, n, yaw=0):
    cf = C(x, 0, z) * R(0, yaw, 0)
    pts = [(0, k * 2 + 1) for k in range(n)] + [(2, n * 2 + 1), (4, n * 2 + 1), (6, n * 2 - 1)]
    for k, (dx, y) in enumerate(pts):
        part((2.1, 2.1, 2.1), cf * C(dx, y, 0), (236, 50, 60) if k % 2 == 0 else WHITE)


def z_candy(i):
    G, G2 = (255, 176, 208), (255, 206, 226)
    cs = [(255, 90, 120), (120, 200, 255), (255, 214, 60), (150, 230, 120), (190, 130, 255), (255, 150, 50)]
    with group(f'Zone{i + 1}_CandyCanyon', unique=False):
        z0, zc = zone_base(i, G, 'SmoothPlastic', (255, 244, 220), (150, 92, 62), (124, 76, 52))
        patches(z0, z0 + ZL, G2)
        # chocolate river across the zone + wafer bridge on the road
        rz_ = z0 + 66
        for sx in (-1, 1):
            blk(sx * 96, 0, rz_, 174, 0.2, 20, (110, 66, 40), **NC)
            blk(sx * 96, 0.1, rz_, 174, 0.25, 15, (140, 88, 52), 'Glass', **NC)
        blk(0, 0, rz_, ROADW + 4, 1.6, 24, (240, 200, 130), 'WoodPlanks')
        for sx in (-1, 1):
            blk(sx * (ROADW / 2 + 1.5), 1.6, rz_, 1, 3, 24, (255, 120, 150))
        for _ in range(20):
            c1, c2 = rng.sample(cs, 2)
            lollipop(side_x(18, 160), rng.choice((rng.uniform(z0 + 8, rz_ - 16), rng.uniform(rz_ + 16, z0 + ZL - 8))), rng.uniform(9, 20), rng.uniform(8, 15), c1, c2)
        for _ in range(12):
            candy_cane(side_x(18, 160), rng.choice((rng.uniform(z0 + 8, rz_ - 16), rng.uniform(rz_ + 16, z0 + ZL - 8))), rng.randint(4, 9), rng.choice((0, 90, 180, 270)))
        for _ in range(40):                                   # gumdrops
            d = rng.uniform(2.4, 6)
            sph(side_x(12, 164), d * 0.12, rng.choice((rng.uniform(z0 + 4, rz_ - 14), rng.uniform(rz_ + 14, z0 + ZL - 4))), d, rng.choice(cs))
        for _ in range(9):                                    # ice cream cones
            x, z = side_x(22, 150), rng.choice((rng.uniform(z0 + 10, rz_ - 18), rng.uniform(rz_ + 18, z0 + ZL - 10)))
            for k in range(4):
                vcyl(x, k * 2.2, z, 2.2, 2.2 + k * 1.3, (226, 170, 100), 'Sand')
            for k, c in enumerate(rng.sample(cs, 3)):
                sph(x, 11 + k * 3.6, z, 7 - k * 1.1, c)
        # giant cake
        cx, cz = -98, z0 + 110
        for k, (d, c) in enumerate(((44, (255, 240, 230)), (34, (255, 150, 180)), (24, (255, 240, 230)))):
            vcyl(cx, k * 9, cz, 9, d, c)
            vcyl(cx, k * 9 + 7.6, cz, 1.6, d + 1.6, (120, 70, 44) if k % 2 == 0 else WHITE)
            for a in range(0, 360, 45):
                sph(cx + (d / 2) * math.cos(math.radians(a + k * 20)), k * 9 + 9, cz + (d / 2) * math.sin(math.radians(a + k * 20)), 2.6, rng.choice(cs))
        sph(cx, 30, cz, 6, (236, 40, 60))
        for a in range(0, 360, 60):
            x, z = cx + 8 * math.cos(math.radians(a)), cz + 8 * math.sin(math.radians(a))
            vcyl(x, 27, z, 5, 0.8, rng.choice(cs))
            f = sph(x, 32.6, z, 1.2, (255, 210, 60), 'Neon', **NC)
            light(f, (255, 200, 90), 12, 1)
        egg_sky(z0, (255, 226, 240), [((255, 150, 180), WHITE), ((120, 200, 255), (255, 214, 60)), ((255, 214, 60), (255, 90, 120))])


# ------------------------------------------------------------------ zone 4: Crystal Coast
def crystal(x, z, h, col, big=True):
    w = h * 0.26
    part((w, h, w), C(x, h / 2 - 1, z) * R(rng.uniform(-14, 14), rng.uniform(0, 90), rng.uniform(-14, 14)), col, 'Glass', transparency=0.18)
    if big:
        for k in range(rng.randint(2, 4)):
            hh = h * rng.uniform(0.35, 0.65)
            a = rng.uniform(0, 6.28)
            part((hh * 0.26, hh, hh * 0.26), C(x + w * 1.1 * math.cos(a), hh / 2 - 1, z + w * 1.1 * math.sin(a)) *
                 R(rng.uniform(-28, 28), rng.uniform(0, 90), rng.uniform(-28, 28)), shade(col, rng.uniform(0.85, 1.15)), 'Glass', transparency=0.18)


def palm(x, z, h):
    lean = rng.uniform(-0.5, 0.5)
    for k in range(int(h // 3)):
        blk(x + lean * k, k * 3, z, 2.2 - k * 0.08, 3, 2.2 - k * 0.08, (176, 132, 84) if k % 2 == 0 else (156, 114, 70), 'Wood')
    tx = x + lean * (h // 3)
    for k in range(6):
        part((11, 0.8, 3.2), C(tx, h + 0.4, z) * R(0, k * 60 + 10, 0) * C(5.4, 0, 0) * R(0, 0, -18), (60, 180, 90), 'Grass', **NC)
    for a in (0, 120, 240):
        sph(tx + 1.4 * math.cos(math.radians(a)), h - 0.8, z + 1.4 * math.sin(math.radians(a)), 1.8, (120, 80, 50))


def z_crystal(i):
    G, G2 = (246, 226, 168), (236, 210, 146)
    cs = [(80, 230, 255), (190, 120, 255), (255, 110, 210), (110, 255, 200)]
    with group(f'Zone{i + 1}_CrystalCoast', unique=False):
        z0, zc = zone_base(i, G, 'Sand', (255, 246, 214), (96, 150, 190), (206, 180, 120))
        patches(z0, z0 + ZL, G2)
        for (px, pz, w, d) in ((-104, z0 + 40, 70, 44), (88, z0 + 96, 80, 50), (112, z0 + 30, 44, 30), (-70, z0 + 112, 50, 30)):
            blk(px, 0, pz, w, 0.25, d, (120, 226, 230), 'Glass', transparency=0.2, **NC)
            blk(px, 0.05, pz, w - 8, 0.3, d - 8, (70, 200, 230), 'Glass', transparency=0.2, **NC)
        for _ in range(26):
            crystal(side_x(18, 160), rng.uniform(z0 + 8, z0 + ZL - 8), rng.uniform(8, 30), rng.choice(cs))
        for _ in range(40):
            crystal(side_x(12, 164), rng.uniform(z0 + 4, z0 + ZL - 4), rng.uniform(2, 5), rng.choice(cs), big=False)
        for _ in range(16):
            palm(side_x(18, 160), rng.uniform(z0 + 8, z0 + ZL - 8), rng.choice((15, 18, 21)))
        # lighthouse
        lx, lz = -124, z0 + 78
        blk(lx, 0, lz, 26, 3, 26, (150, 154, 170), 'Slate')
        for k in range(7):
            vcyl(lx, 3 + k * 6, lz, 6, 15 - k * 1.2, WHITE if k % 2 == 0 else (236, 60, 70))
        vcyl(lx, 45, lz, 1, 13, INK)
        g = vcyl(lx, 46, lz, 6, 7, (255, 240, 150), 'Neon')
        light(g, (255, 240, 170), 60, 3)
        vcyl(lx, 52, lz, 1.2, 10, (236, 60, 70))
        vcyl(lx, 53.2, lz, 2.4, 5, (236, 60, 70))
        # crystal throne cluster
        for k in range(9):
            a = k * 40
            crystal(104 + 12 * math.cos(math.radians(a)), z0 + 64 + 12 * math.sin(math.radians(a)), rng.uniform(20, 44), cs[k % 4])
        for _ in range(18):                                   # shells / starfish
            blk(side_x(12, 164), 0, rng.uniform(z0 + 4, z0 + ZL - 4), 1.8, 0.5, 1.8, rng.choice(((255, 150, 120), (255, 240, 230), (255, 190, 90))), yaw=rng.uniform(0, 90), **NC)
        egg_sky(z0, (232, 248, 255), [((80, 230, 255), WHITE), ((190, 120, 255), (80, 230, 255)), ((255, 110, 210), WHITE)])


# ------------------------------------------------------------------ zone 5: Thunder Peaks
def peak(x, z, base, h, col):
    n = 6
    ox = oz = 0
    for k in range(n):
        s = base * (1 - k / (n + 0.6))
        blk(x + ox, k * h / n, z + oz, s, h / n, s * rng.uniform(0.8, 1.1), shade(col, 1 + k * 0.05), 'Slate', yaw=rng.choice((0, 0, 12, -12)))
        ox += rng.uniform(-0.06, 0.06) * base
        oz += rng.uniform(-0.06, 0.06) * base
    blk(x + ox, h - 0.4, z + oz, base * 0.16, 1.2, base * 0.16, (255, 226, 60), 'Neon', **NC)


def bolt(x, z, ytop, col=(255, 236, 80)):
    pts = [(x, ytop)]
    y = ytop
    while y > 1:
        y = max(0.5, y - rng.uniform(9, 15))
        pts.append((x + rng.uniform(-7, 7), y))
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        dx, dy = x2 - x1, y2 - y1
        ln = math.hypot(dx, dy)
        part((1.3, ln + 0.6, 1.3), C((x1 + x2) / 2, (y1 + y2) / 2, z) * R(0, 0, math.degrees(math.atan2(-dx, dy))), col, 'Neon', name='Bolt', **NC)
    f = sph(pts[-1][0], 1, z, 4, col, 'Neon', transparency=0.3, **NC)
    light(f, col, 40, 3)


def z_thunder(i):
    G, G2 = (78, 84, 108), (64, 70, 92)
    with group(f'Zone{i + 1}_ThunderPeaks', unique=False):
        z0, zc = zone_base(i, G, 'Slate', (150, 156, 184), (50, 54, 74), (44, 46, 62))
        patches(z0, z0 + ZL, G2)
        for _ in range(12):
            peak(side_x(40, 150), rng.uniform(z0 + 16, z0 + ZL - 16), rng.uniform(22, 40), rng.uniform(24, 62), (86, 92, 120))
        for _ in range(14):                                   # lightning rods
            x, z = side_x(16, 160), rng.uniform(z0 + 8, z0 + ZL - 8)
            h = rng.uniform(22, 38)
            vcyl(x, 0, z, 2, 5, (60, 64, 80), 'Metal')
            vcyl(x, 2, z, h, 1, (190, 196, 214), 'Metal')
            for k in range(3):
                vcyl(x, h * 0.55 + k * 2.6, z, 0.7, 3.4 - k * 0.6, (255, 190, 50), 'Metal')
            t = sph(x, h + 3, z, 2.6, (255, 236, 80), 'Neon')
            light(t, (255, 230, 90), 26, 2)
        for _ in range(26):                                   # glowing cracks + puddles
            blk(side_x(12, 164), 0, rng.uniform(z0 + 4, z0 + ZL - 4), rng.uniform(6, 16), 0.16, 0.8, (255, 226, 60), 'Neon', yaw=rng.uniform(0, 180), **NC)
        for _ in range(12):
            blk(side_x(14, 160), 0, rng.uniform(z0 + 6, z0 + ZL - 6), rng.uniform(8, 16), 0.15, rng.uniform(6, 12), (110, 150, 220), 'Glass', transparency=0.25, **NC)
        # tesla tower
        tx, tz = 108, z0 + 74
        blk(tx, 0, tz, 22, 4, 22, (60, 64, 84), 'Metal')
        for k in range(5):
            blk(tx, 4 + k * 9, tz, 12 - k * 1.8, 9, 12 - k * 1.8, (96, 102, 130) if k % 2 == 0 else (70, 76, 100), 'Metal')
        for k in range(3):
            vcyl(tx, 50 + k * 3.4, tz, 1.4, 20 - k * 5, (255, 190, 50), 'Metal')
        t = sph(tx, 64, tz, 9, (255, 240, 110), 'Neon')
        light(t, (255, 236, 110), 60, 4)
        # low storm clouds with bolts
        for k in range(7):
            x, z = rng.uniform(-140, 140), z0 + 12 + k * 18
            cloud(x, 56, z, rng.uniform(0.9, 1.3), (70, 74, 96))
            if k % 2 == 0:
                bolt(x + rng.uniform(-6, 6), z, 56)
        egg_sky(z0, (96, 100, 126), [((255, 226, 60), INK), ((110, 150, 255), (255, 236, 80)), ((70, 76, 100), (255, 226, 60))])


# ------------------------------------------------------------------ zone 6: Cloud Kingdom
RAINBOW = [(244, 70, 70), (255, 150, 40), (255, 222, 50), (90, 210, 90), (70, 150, 250), (160, 100, 250)]


def rainbow(xc, z, radius, bw=3.2, depth=4):
    n = 26
    for bi, col in enumerate(RAINBOW):
        r = radius - bi * bw
        seg = math.pi * r / n * 1.06
        for k in range(n):
            a = (k + 0.5) * 180 / n
            part((seg, bw, depth), C(xc + r * math.cos(math.radians(a)), r * math.sin(math.radians(a)) - 2, z) * R(0, 0, a + 90), col, name='Rainbow', **NC)


def puff(x, z, s):
    for dx, dz, d in ((0, 0, 9), (-5, 1, 7), (5, -1, 7.4), (1, 4, 6), (-2, -4, 6)):
        sph(x + dx * s, d * s * 0.22, z + dz * s, d * s, WHITE)


def z_cloud(i):
    G, G2 = (244, 248, 255), (214, 232, 255)
    with group(f'Zone{i + 1}_CloudKingdom', unique=False):
        z0, zc = zone_base(i, G, 'SmoothPlastic', (255, 236, 170), (198, 214, 244), (176, 196, 236))
        patches(z0, z0 + ZL, G2)
        rainbow(0, z0 + 30, 74)
        rainbow(0, z0 + 110, 60)
        for _ in range(30):
            puff(side_x(20, 160), rng.uniform(z0 + 6, z0 + ZL - 6), rng.uniform(0.8, 1.8))
        for _ in range(14):                                   # marble pillars with gold caps
            x, z = side_x(16, 150), rng.uniform(z0 + 8, z0 + ZL - 8)
            h = rng.choice((14, 20, 26))
            vcyl(x, 0, z, 1.6, 6, GOLD, 'Foil')
            vcyl(x, 1.6, z, h, 3.6, WHITE, 'Marble')
            vcyl(x, h + 1.6, z, 1.4, 6, GOLD, 'Foil')
            s = sph(x, h + 5, z, 2.4, (255, 240, 130), 'Neon', **NC)
            light(s, (255, 236, 150), 18, 1.2)
        # sky castle
        cx, cz = -110, z0 + 72
        blk(cx, 0, cz, 46, 16, 30, WHITE, 'Marble')
        for k in range(8):
            blk(cx - 20 + k * 5.8, 16, cz - 14, 3, 3, 2.6, WHITE, 'Marble')
        blk(cx, 0, cz - 15.2, 9, 12, 0.8, GOLD, 'Foil')
        for tx, th in ((-23, 34), (23, 34), (0, 46)):
            vcyl(cx + tx, 0, cz + (6 if tx == 0 else -6), th, 12, WHITE, 'Marble')
            for k in range(5):
                vcyl(cx + tx, th + k * 3, cz + (6 if tx == 0 else -6), 3, 14 - k * 3, (90, 150, 250))
            sph(cx + tx, th + 16.5, cz + (6 if tx == 0 else -6), 2.4, GOLD, 'Foil')
        for _ in range(9):                                    # floating cloud steps
            x, z, y = side_x(24, 150), rng.uniform(z0 + 10, z0 + ZL - 10), rng.uniform(14, 40)
            blk(x, y, z, rng.uniform(10, 18), 3, rng.uniform(8, 14), WHITE, name='CloudStep')
            blk(x + 2, y + 3, z, 7, 2.4, 6, (232, 242, 255), **NC)
        for _ in range(26):                                   # stars
            s = blk(rng.uniform(-160, 160), rng.uniform(20, 70), rng.uniform(z0 + 4, z0 + ZL - 4), 1.6, 1.6, 1.6, (255, 236, 110), 'Neon', yaw=45, **NC)
        egg_sky(z0, WHITE, [(WHITE, (255, 150, 200)), ((255, 222, 50), WHITE), ((150, 200, 255), (255, 240, 130))])


# ------------------------------------------------------------------ zone 7: Golden Nest
def z_golden(i):
    G, G2 = (255, 206, 70), (255, 226, 120)
    with group(f'Zone{i + 1}_GoldenNest', unique=False):
        z0, zc = zone_base(i, G, 'SmoothPlastic', (255, 244, 200), (190, 130, 40), (176, 116, 40))
        patches(z0, z0 + ZL, G2)
        nx, nz = 0, z0 + 92
        vcyl(nx, 0, nz, 0.5, 100, (236, 180, 60), **NC)
        for ring, (r, y, n) in enumerate(((44, 2, 30), (47, 5.6, 30), (45, 9.2, 28), (48, 12.6, 26))):   # twig nest ring, open at the front
            for k in range(n):
                a = k * 360 / n + ring * 7
                if 250 < a % 360 < 290:
                    continue
                part((rng.uniform(15, 22), 3.6, 3.6), C(nx + r * math.cos(math.radians(a)), y, nz + r * math.sin(math.radians(a))) *
                     R(0, -(a + 90) + rng.uniform(-22, 22), rng.uniform(-10, 10)), rng.choice((BROWN, DBROWN, (150, 104, 60))), 'Wood', 'Cylinder')
        sph(nx, 24, nz, 50, GOLD, 'Foil', name='GoldenEgg')
        sph(nx, 41, nz, 39, GOLD, 'Foil', name='GoldenEgg')
        b = vcyl(nx, 60, nz, 400, 12, (255, 240, 150), 'Neon', transparency=0.7, **NC)
        light(b, (255, 230, 120), 60, 3)
        for k in range(3):
            vcyl(nx, 14 + k * 16, nz, 1.2, 62 - k * 9, (255, 255, 220), 'Neon', transparency=0.5, **NC)
        for _ in range(20):                                   # golden trees
            tree(side_x(60, 160), rng.uniform(z0 + 8, z0 + ZL - 8), rng.uniform(0.9, 1.6), (255, 190, 40), (250, 240, 220))
        for _ in range(16):                                   # treasure piles
            x, z = side_x(16, 160), rng.uniform(z0 + 6, z0 + 44)
            for k in range(rng.randint(4, 9)):
                blk(x + rng.uniform(-3, 3), rng.choice((0, 0, 1.6)), z + rng.uniform(-3, 3), 1.8, 1.6, 1.8, GOLD, 'Foil', yaw=rng.uniform(0, 90))
            sph(x, 3.6, z, 2, rng.choice(((240, 60, 90), (70, 200, 255), (120, 240, 140), (190, 110, 255))), 'Glass', transparency=0.1)
        for sx in (-1, 1):                                    # 3 pedestals each side with secret eggs
            for k in range(3):
                x, z = sx * (70 + k * 26), z0 + 58
                vcyl(x, 0, z, 6, 9, WHITE, 'Marble')
                vcyl(x, 6, z, 1, 11, GOLD, 'Foil')
                egg(x, 9.4, z, 1.9, RAINBOW[(k + (3 if sx > 0 else 0)) % 6], WHITE, beam=True)
        # end wall with a rising sun
        ez = z0 + ZL + 12
        for x in range(-HALF - 24, HALF + 25, 24):
            h = rng.choice((40, 52, 64, 76))
            blk(x + 12, -4, ez, 24, h + 4, 24, (190, 130, 40), 'Slate')
            blk(x + 12, h, ez, 24, 2, 24, G)
        vcyl(0, 0, 0, 0.1, 0.1, G, **NC)
        part((4, 150, 150), C(0, 70, ez + 16) * R(0, 90, 0), (255, 226, 90), 'Neon', 'Cylinder', name='Sun', **NC)
        blk(0, 0, z0 + ZL + 1, HALF * 2 + 48, 120, 2, WHITE, transparency=1, name='Wall')
        egg_sky(z0, (255, 244, 200), [(GOLD, WHITE), ((255, 240, 150), GOLD), (RAINBOW[5], GOLD)])


# ------------------------------------------------------------------ zone: Toy Town
TOY = [(240, 70, 70), (255, 204, 40), (70, 190, 90), (70, 130, 250), (255, 140, 40), (190, 100, 250)]


def z_toy(i):
    G = (130, 200, 255)
    with group(f'Zone{i + 1}_ToyTown', unique=False):
        z0, zc = zone_base(i, G, 'SmoothPlastic', (255, 250, 236), (240, 90, 80), (70, 120, 220))
        for _ in range(60):                                   # play-mat tiles
            blk(side_x(14, 162), 0, rng.uniform(z0 + 8, z0 + ZL - 8), 10, 0.14, 10, rng.choice(TOY), **NC)
        for _ in range(16):                                   # towers of toy blocks
            x, z = side_x(20, 156), rng.uniform(z0 + 10, z0 + ZL - 10)
            y = 0
            for k in range(rng.randint(1, 4)):
                s = rng.choice((8, 10, 12)) - k
                blk(x + rng.uniform(-1.5, 1.5), y, z + rng.uniform(-1.5, 1.5), s, s, s, rng.choice(TOY), yaw=rng.choice((0, 15, -20, 30)))
                y += s
        for _ in range(8):                                    # dice
            x, z, s = side_x(20, 156), rng.uniform(z0 + 10, z0 + ZL - 10), rng.choice((7, 9))
            blk(x, 0, z, s, s, s, WHITE)
            for dx, dz in ((-0.25, -0.25), (0.25, 0.25), (0, 0), (-0.25, 0.25), (0.25, -0.25)):
                vcyl(x + dx * s, s, z + dz * s, 0.2, s * 0.16, INK, **NC)
        for _ in range(9):                                    # stacking rings
            x, z = side_x(20, 156), rng.uniform(z0 + 10, z0 + ZL - 10)
            vcyl(x, 0, z, 16, 1.4, CREAM)
            for k in range(5):
                vcyl(x, 0.4 + k * 2.6, z, 2.4, 11 - k * 1.8, TOY[k % 6])
        for _ in range(12):                                   # crayons
            x, z, h, c = side_x(16, 160), rng.uniform(z0 + 8, z0 + ZL - 8), rng.uniform(12, 20), rng.choice(TOY)
            vcyl(x, 0, z, h, 3, c)
            vcyl(x, h * 0.2, z, 1.6, 3.2, shade(c, 0.7))
            vcyl(x, h, z, 1.6, 2.2, c)
            vcyl(x, h + 1.6, z, 1.6, 1.2, c)
        for _ in range(18):                                   # bouncy balls
            d = rng.uniform(3, 7)
            sph(side_x(14, 162), d / 2, rng.uniform(z0 + 6, z0 + ZL - 6), d, rng.choice(TOY), name='Bounce')
        # toy train on a round track
        tx, tz = 98, z0 + 72
        vcyl(tx, 0, tz, 0.3, 74, (120, 84, 56), **NC)
        vcyl(tx, 0.3, tz, 0.1, 58, G, **NC)
        for k in range(5):
            a = math.radians(200 + k * 24)
            x, z = tx + 33 * math.cos(a), tz + 33 * math.sin(a)
            cf = C(x, 0, z) * R(0, -math.degrees(a), 0)
            c = TOY[k % 6]
            part((8, 6, 13), cf * C(0, 4.4, 0), c, name='Train')
            for sx in (-1, 1):
                for sz in (-1, 1):
                    part((1, 3.4, 3.4), cf * C(sx * 4.4, 1.9, sz * 4), INK, 'SmoothPlastic', 'Cylinder')
            if k == 0:
                part((7, 5, 6), cf * C(0, 10, -3), shade(c, 0.8))
                part((5, 2.4, 2.4), cf * C(0, 10, 4) * R(0, 0, 90), INK, 'SmoothPlastic', 'Cylinder')
        # giant teddy bear
        bx, bz = -106, z0 + 80
        TB = (176, 120, 70)
        sph(bx, 14, bz, 30, TB)
        sph(bx, 34, bz, 21, TB)
        sph(bx, 12, bz - 12, 14, (226, 180, 130))
        sph(bx, 31, bz - 9, 9, (226, 180, 130))
        sph(bx, 32.5, bz - 13.4, 3, INK)
        for sx in (-1, 1):
            sph(bx + sx * 8.5, 43, bz, 8, TB)
            sph(bx + sx * 4.4, 37, bz - 9.2, 2.2, INK)
            sph(bx + sx * 16, 20, bz - 4, 10, TB)
            sph(bx + sx * 10, 4, bz - 14, 12, TB)
        # rubber duck in a tub
        dx, dz = -70, z0 + 28
        blk(dx, 0, dz, 34, 5, 24, WHITE)
        blk(dx, 4.2, dz, 30, 1, 20, (90, 190, 250), 'Glass', transparency=0.2, **NC)
        sph(dx, 9, dz, 12, (255, 220, 50))
        sph(dx, 16, dz - 3, 8, (255, 220, 50))
        blk(dx, 14.6, dz - 8.4, 3.4, 1.6, 3.4, (255, 140, 40))
        egg_sky(z0, WHITE, [(TOY[0], WHITE), (TOY[3], TOY[1]), (TOY[2], WHITE)])


# ------------------------------------------------------------------ zone: Spooky Hollow
def pumpkin(x, z, d, lit=False):
    sph(x, d * 0.42, z, d, (255, 132, 30))
    sph(x - d * 0.3, d * 0.42, z, d * 0.8, (240, 116, 24))
    sph(x + d * 0.3, d * 0.42, z, d * 0.8, (240, 116, 24))
    blk(x, d * 0.86, z, d * 0.16, d * 0.26, d * 0.16, (70, 130, 60))
    if lit:
        for dx in (-0.2, 0.2):
            e = blk(x + dx * d, d * 0.5, z - d * 0.5, d * 0.16, d * 0.16, d * 0.1, (255, 230, 90), 'Neon', **NC)
        blk(x, d * 0.26, z - d * 0.5, d * 0.5, d * 0.1, d * 0.1, (255, 230, 90), 'Neon', **NC)
        light(e, (255, 170, 60), d * 3, 1.5)


def dead_tree(x, z, h):
    D = (56, 44, 52)
    blk(x, 0, z, 2.6, h, 2.6, D, 'Wood')
    for k in range(4):
        a = k * 90 + rng.uniform(0, 60)
        ln = rng.uniform(5, 10)
        part((ln, 1.3, 1.3), C(x, h * rng.uniform(0.55, 0.95), z) * R(0, a, 0) * R(0, 0, rng.uniform(20, 45)) * C(ln / 2, 0, 0), D, 'Wood')


def z_spooky(i):
    G, G2 = (64, 78, 74), (52, 64, 62)
    with group(f'Zone{i + 1}_SpookyHollow', unique=False):
        z0, zc = zone_base(i, G, 'Grass', (128, 116, 140), (46, 40, 60), (40, 34, 46))
        patches(z0, z0 + ZL, G2)
        for _ in range(26):
            dead_tree(side_x(18, 160), rng.uniform(z0 + 8, z0 + ZL - 8), rng.uniform(12, 24))
        for k in range(34):
            pumpkin(side_x(13, 162), rng.uniform(z0 + 5, z0 + ZL - 5), rng.uniform(2.6, 7), lit=(k % 3 == 0))
        for gx, gz in ((96, z0 + 36), (-60, z0 + 104)):       # graveyards
            for k in range(14):
                x, z = gx + (k % 5) * 7 - 14, gz + (k // 5) * 8
                blk(x, 0, z, 3.4, 4.6, 1.2, (150, 154, 168), 'Slate', yaw=rng.uniform(-10, 10))
                blk(x, 4.6, z, 2.4, 1.2, 1.2, (150, 154, 168), 'Slate')
            for k in range(7):
                blk(gx - 20 + k * 7, 0, gz - 6, 0.6, 5, 0.6, INK, 'Metal')
            blk(gx, 3.6, gz - 6, 43, 0.5, 0.4, INK, 'Metal')
        # haunted house
        hx, hz = -104, z0 + 52
        HP = (84, 62, 110)
        blk(hx, 0, hz, 34, 22, 26, HP, 'WoodPlanks')
        blk(hx + 12, 22, hz, 10, 16, 10, shade(HP, 0.9), 'WoodPlanks')
        for k in range(5):
            blk(hx, 22 + k * 2.6, hz, 38 - k * 7, 2.6, 30 - k * 4, (40, 34, 52), yaw=3)
            blk(hx + 12, 38 + k * 2.2, hz, 13 - k * 2.6, 2.2, 13 - k * 2.6, (40, 34, 52))
        blk(hx, 0, hz - 13.2, 6, 10, 0.6, (40, 30, 30), 'Wood')
        for wx, wy in ((-10, 12), (10, 12), (-10, 4), (10, 4), (12, 30)):
            w = blk(hx + wx, wy, hz - 13.2 if wy < 22 else hz - 5.2, 4, 5, 0.6, (255, 220, 90), 'Neon')
            light(w, (255, 190, 70), 24, 1.6)
        for _ in range(14):                                   # ghosts
            x, y, z = side_x(16, 156), rng.uniform(5, 26), rng.uniform(z0 + 8, z0 + ZL - 8)
            sph(x, y + 2.4, z, 5, WHITE, transparency=0.25, name='Ghost', **NC)
            vcyl(x, y - 1.6, z, 4, 5, WHITE, transparency=0.25, **NC)
            for sx in (-1, 1):
                sph(x + sx * 1, y + 2.8, z - 2.2, 0.9, INK, **NC)
        for _ in range(12):                                   # lanterns
            x, z = side_x(12, 40), rng.uniform(z0 + 6, z0 + ZL - 6)
            blk(x, 0, z, 0.8, 9, 0.8, INK, 'Metal')
            l = blk(x, 9, z, 2.4, 2.8, 2.4, (140, 255, 150), 'Neon')
            light(l, (140, 255, 150), 26, 1.6)
        part((3, 70, 70), C(-150, 96, z0 + 100) * R(0, 90, 0), (240, 240, 210), 'Neon', 'Cylinder', name='Moon', **NC)
        egg_sky(z0, (86, 80, 110), [((255, 132, 30), INK), ((150, 100, 220), (140, 255, 150)), (WHITE, INK)])


# ------------------------------------------------------------------ zone: Neon City
def z_neon(i):
    G = (38, 40, 58)
    NEON = [(60, 240, 255), (255, 70, 200), (160, 110, 255), (120, 255, 140), (255, 220, 60)]
    with group(f'Zone{i + 1}_NeonCity', unique=False):
        z0, zc = zone_base(i, G, 'SmoothPlastic', (70, 74, 100), (30, 30, 46), (26, 26, 40))
        for z in range(int(z0) + 10, int(z0 + ZL), 20):       # glowing grid on the floor
            for sx in (-1, 1):
                blk(sx * 92, 0, z, 150, 0.14, 0.6, NEON[(z // 20) % 2], 'Neon', **NC)
        for x in range(30, 170, 28):
            for sx in (-1, 1):
                blk(sx * x, 0, zc, 0.6, 0.14, ZL - 6, NEON[2], 'Neon', **NC)
        for sx in (-1, 1):                                    # road edge lights
            blk(sx * (ROADW / 2 + 1.6), 0.7, zc, 0.5, 0.3, ZL, NEON[0 if sx < 0 else 1], 'Neon', **NC)
        names = ['EGGS', 'ARCADE', '24/7', 'LUCKY', 'HATCH', 'RARE', 'PETS', 'OPEN']
        k = 0
        for sx in (-1, 1):                                    # towers
            for z in range(int(z0) + 16, int(z0 + ZL) - 10, 26):
                for row, x in enumerate((60, 104, 146)):
                    if rng.random() < 0.18:
                        continue
                    w, d, h = rng.uniform(18, 26), rng.uniform(14, 20), rng.uniform(26, 50) + row * 22
                    c = NEON[k % 5]
                    tx = sx * (x + rng.uniform(-5, 5))
                    blk(tx, 0, z, w, h, d, (30 + row * 6, 32 + row * 6, 52 + row * 8))
                    for y in range(6, int(h) - 3, 7):
                        blk(tx, y, z - d / 2 - 0.1, w * 0.8, 1.6, 0.4, c, 'Neon', **NC)
                        blk(tx - sx * (w / 2 + 0.1), y, z, 0.4, 1.6, d * 0.8, c, 'Neon', **NC)
                    blk(tx, h, z, w + 1, 0.8, d + 1, c, 'Neon', **NC)
                    if row == 0:
                        s = blk(tx, h * 0.45, z - d / 2 - 0.8, w * 0.9, 5, 0.8, INK)
                        sign(s, 'Front', names[k % 8], bg1=c, bg2=shade(c, 0.5), fg=WHITE, pps=14)
                        light(s, c, 36, 2)
                    k += 1
        for _ in range(12):                                   # street lamps
            x, z = rng.choice((-1, 1)) * rng.uniform(14, 40), rng.uniform(z0 + 6, z0 + ZL - 6)
            c = rng.choice(NEON)
            blk(x, 0, z, 0.8, 14, 0.8, (60, 64, 90), 'Metal')
            l = sph(x, 15.2, z, 2.6, c, 'Neon')
            light(l, c, 30, 2)
        for _ in range(10):                                   # arcade machines
            x, z, c = rng.choice((-1, 1)) * rng.uniform(16, 44), rng.uniform(z0 + 8, z0 + ZL - 8), rng.choice(NEON)
            blk(x, 0, z, 4, 7, 3.4, (50, 52, 80))
            blk(x, 4, z - 1.8, 3.2, 2.4, 0.3, c, 'Neon', **NC)
            blk(x, 7, z, 4.4, 1.2, 3.8, c, 'Neon', **NC)
        for _ in range(9):                                    # hover cars
            x, y, z, c = rng.uniform(-150, 150), rng.uniform(34, 74), rng.uniform(z0 + 8, z0 + ZL - 8), rng.choice(NEON)
            blk(x, y, z, 5, 1.6, 10, (60, 64, 90), **NC)
            blk(x, y + 1.6, z, 4, 1.4, 5, (150, 220, 255), 'Glass', transparency=0.3, **NC)
            blk(x, y - 0.4, z, 5.4, 0.4, 10.4, c, 'Neon', **NC)
        # hologram egg in a ring, over the road
        hx, hz = 0, z0 + 76
        for sx in (-1, 1):
            blk(sx * 16, 0, hz, 4, 30, 4, (50, 52, 80), 'Metal')
        blk(0, 30, hz, 36, 2, 4, (50, 52, 80), 'Metal')
        sph(hx, 44, hz, 17, NEON[0], 'Glass', transparency=0.45, name='Hologram', **NC)
        sph(hx, 50, hz, 13.4, NEON[0], 'Glass', transparency=0.45, **NC)
        r = part((1, 30, 30), C(hx, 45, hz) * R(0, 90, 0) * R(0, 0, 0), NEON[1], 'Neon', 'Cylinder', transparency=0.7, **NC)
        light(r, NEON[0], 60, 3)
        egg_sky(z0, (60, 56, 96), [(NEON[0], WHITE), (NEON[1], NEON[4]), (NEON[2], NEON[0])])


ZONES = [
    ('SUNNY MEADOW', 'START HERE', (120, 210, 90), (60, 150, 60), z_meadow),
    ('MUSHROOM GROVE', 'SPEED 500+', (190, 130, 255), (98, 70, 170), z_mushroom),
    ('CANDY CANYON', 'SPEED 5K+', (255, 130, 180), (220, 70, 130), z_candy),
    ('TOY TOWN', 'SPEED 40K+', (255, 204, 40), (240, 90, 60), z_toy),
    ('CRYSTAL COAST', 'SPEED 250K+', (80, 220, 250), (40, 130, 210), z_crystal),
    ('SPOOKY HOLLOW', 'SPEED 2M+', (255, 140, 40), (84, 62, 110), z_spooky),
    ('THUNDER PEAKS', 'SPEED 15M+', (255, 220, 60), (70, 76, 104), z_thunder),
    ('NEON CITY', 'SPEED 100M+', (255, 70, 200), (90, 60, 200), z_neon),
    ('CLOUD KINGDOM', 'SPEED 1B+', (150, 200, 255), (90, 130, 240), z_cloud),
    ('GOLDEN NEST', 'SPEED 25B+', (255, 210, 60), (220, 130, 20), z_golden),
]


def build():
    home()
    for i, (name, sub, c1, c2, fn) in enumerate(ZONES):
        fn(i)
        with group('Gates', unique=False):
            if i == 0:
                # big title arch between the plaza and the first zone
                for sx in (-1, 1):
                    blk(sx * 30, 0, 0, 7, 30, 7, WHITE)
                    for k, c in enumerate(RAINBOW):
                        blk(sx * 30, 3 + k * 4.4, 0, 7.6, 2.2, 7.6, c)
                    egg(sx * 30, 34.5, 0, 2.6, WHITE, RAINBOW[0 if sx < 0 else 4])
                b = blk(0, 20, 0, 52, 11, 4, INK)
                sign(b, 'Front', 'RAINING EGGS', 'catch  •  hatch  •  get lucky', fg=(255, 236, 90), bg1=(90, 170, 255), bg2=(60, 90, 230), pps=16)
                sign(b, 'Back', name, sub, bg1=c1, bg2=c2, pps=16)
            else:
                gate(i * ZL, name, sub, c1, c2)
    with group('Water', unique=False):
        for sx in (-1, 1):
            for zc in (-380, 1660):
                blk(sx * 1020, -24, zc, 2040, 2, 2040, (36, 120, 205), name='Sea', **NC)


if __name__ == '__main__':
    build()
    spawn = [p for p in PARTS if p.get('spawn')]
    out = {'parts': PARTS, 'spawn': spawn[0]['p'] if spawn else [0, 1, 0]}
    (HERE / 'map.json').write_text(json.dumps(out), encoding='utf-8')
    groups = {}
    for p in PARTS:
        g = (p['g'].split('/')[1] if '/' in p['g'] else p['g']).split('#')[0]
        groups[g] = groups.get(g, 0) + 1
    print(len(PARTS), 'parts', groups)
