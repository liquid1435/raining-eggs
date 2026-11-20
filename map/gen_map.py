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
    if shape == 'Disc':                     # real round part (shop circles)
        shape = 'Cylinder'
    elif shape == 'Cylinder':               # voxel style: no round shapes
        shape = 'Block'
        size = (size[0], size[1] * 0.88, size[2] * 0.88)
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
    """voxel ball: a stack of square layers"""
    if d <= 2.4:
        return blk(x, y - d * 0.4, z, d * 0.8, d * 0.8, d * 0.8, col, mat, **kw)
    n = 3 if d < 5 else (5 if d < 13 else 7)
    h = d / n
    mid = None
    for k in range(n):
        yk = -d / 2 + (k + 0.5) * h
        w = d * math.sqrt(max(0.0, 1 - (2 * yk / d) ** 2)) * 0.96
        p = blk(x, y + yk - h / 2, z, w, h, w, col, mat, **kw)
        if k == n // 2:
            mid = p
    return mid


def light(p, color, rng_=16, br=1.5):
    p.setdefault('lights', []).append(dict(kind='PointLight', c=list(color), range=rng_, br=br))


def sign(p, face, title, sub=None, fg=(255, 255, 255), bg1=(60, 110, 255), bg2=(30, 60, 200), stroke=(14, 20, 48), pps=20, pad=0.04):
    p.setdefault('signs', []).append(dict(face=face, title=title, sub=sub, fg=list(fg), bg1=list(bg1), bg2=list(bg2), stroke=list(stroke), pps=pps, pad=pad))


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


NC = dict(cancollide=False)
CIRCLES = []  # (x, z, radius) of the shop circles
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
_MESHDB = None


def mesh_db():
    """Blender meshes the user imported (game\\meshes.json) + where they sit (game\\props_meta.json)"""
    global _MESHDB
    if _MESHDB is None:
        gdir = pathlib.Path(__file__).resolve().parent.parent / 'game'
        ids = json.loads((gdir / 'meshes.json').read_text(encoding='utf-8')) if (gdir / 'meshes.json').exists() else {}
        pm = json.loads((gdir / 'props_meta.json').read_text(encoding='utf-8')) if (gdir / 'props_meta.json').exists() else {}
        _MESHDB = (ids, pm)
    return _MESHDB


def has_mesh(*names):
    ids, pm = mesh_db()
    return all(n in ids and n in pm for n in names)


SOFT_MESH = ('Water', 'ChocoRiver', 'PondWater', 'TidePoolWater', 'DuckTubWater', 'Flowers', 'Spore', 'Puff', 'Star', 'Orb',
             'GlowMush', 'Shell', 'Neon', 'Holo', 'Rainbow',
             # v102: irregular shapes collide as one big box in Roblox (players stood in the air next to tree crowns),
             # so they are soft and keep their own fitted helper box (trunk / base) instead
             'Tree', 'Palm', 'Lolli', 'Crystal', 'IceCream', 'CandyCane', 'Teddy', 'Lighthouse', 'Tower', 'Windmill',
             'Tesla', 'Peak', 'Mush', 'HoverCar', 'Throne', 'StackRings', 'LightningRod', 'Ghost', 'SkyCastle', 'Arcade', 'Cake',
             'Haunted', 'Barn', 'Shop', 'Pond', 'TidePool', 'DuckTub')   # v115: ponds have tall reeds -> a box over the water   # v113: houses / shops have pointed roofs; their stepped helper boxes collide instead


def soft_mesh(name):
    """decorative meshes players walk through (lights, flat water, arches, tree crowns: trees get an invisible trunk)"""
    return any(k in name for k in SOFT_MESH)


def mpart(name, x, y0, z, yaw=0.0, s=1.0, mat='SmoothPlastic', pname=None, sv=None, **kw):
    """place a Blender mesh with its origin (ground, model centre) at x, y0, z; sv = stretch per axis"""
    m = mesh_db()[1][name]
    c = m['centre']
    k = sv or (s, s, s)
    # Roblox imports the Blender meshes turned 180 degrees (checked: ShopNeon sits at +Z of Shop in the import) -> turn back about the box centre
    cf = C(x, y0, z) * R(0, yaw, 0) * C(c[0] * k[0], c[1] * k[1], c[2] * k[2]) * R(0, 180, 0)
    kw.setdefault('cancollide', not soft_mesh(name) and (name.startswith('Fence') or max(v * f for v, f in zip(m['size'], k)) >= 3))   # small props stay soft; fences are box-shaped, solid by their own shape
    return part([v * f for v, f in zip(m['size'], k)], cf, (255, 255, 255), mat, name=pname or name[4:], mesh=name, **kw)


TREE_MESHES = ('Map_TreeRound', 'Map_TreeFruit', 'Map_TreePine')


def tree(x, z, s=1.0, leaf=(74, 176, 70), trunk=BROWN):
    r = type(rng)(int(x * 7 + z * 13))          # own dice: layout of the zones stays the same
    s *= r.uniform(0.9, 1.15)
    if leaf[1] > leaf[0] and has_mesh(*TREE_MESHES):          # green trees -> Blender trees
        mpart(r.choice(TREE_MESHES), x, 0, z, r.uniform(0, 360), s)
        blk(x, 0, z, 1.25 * s, 9 * s, 1.25 * s, trunk, transparency=1)   # trunk only, fitted to the mesh trunk
        return
    th = r.uniform(6, 8) * s
    blk(x, 0, z, 3.4 * s, 1 * s, 3.4 * s, shade(trunk, 0.85), 'Wood')                 # root flare
    blk(x, 0, z, 2 * s, th, 2 * s, trunk, 'Wood')
    blk(x + 1.3 * s, th * 0.55, z, 2.2 * s, 0.9 * s, 0.9 * s, shade(trunk, 0.92), 'Wood', **NC)   # branch
    blk(x + 2.6 * s, th * 0.55 - 0.4 * s, z, 2.4 * s, 2 * s, 2.4 * s, shade(leaf, 1.12), 'Grass', **NC)
    if r.random() < 0.3:                                                              # pine: stepped cone
        prof, lh = (9, 7.4, 5.8, 4.2, 2.6, 1.2), 2.3 * s
    else:                                                                             # round crown
        prof, lh = (5.4, 8.4, 9.6, 8.8, 6.6, 3.6), 1.9 * s
    y = th - 1.2 * s
    for k, w in enumerate(prof):
        c = shade(leaf, 0.84 + 0.075 * k)                                             # dark below, sunny on top
        blk(x, y + k * lh, z, w * s, lh, w * s, c, 'Grass', yaw=45 if k % 2 else 0)
    ym = y + 2.2 * lh
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):                                 # side puffs
        if r.random() < 0.8:
            blk(x + dx * 4.3 * s, ym + r.uniform(-1.5, 1) * s, z + dz * 4.3 * s, 3.4 * s, 3 * s, 3.4 * s,
                shade(leaf, r.uniform(0.95, 1.2)), 'Grass', **NC)
    fruit = r.choice(((240, 70, 70), (255, 190, 60), (255, 150, 200), None))
    if fruit:
        for _ in range(4):
            a = r.uniform(0, 6.283)
            blk(x + math.cos(a) * 4.6 * s, ym + r.uniform(-1, 3) * s, z + math.sin(a) * 4.6 * s, 1 * s, 1 * s, 1 * s, fruit, **NC)


def flower(x, z, col):
    r = type(rng)(int(x * 11 + z * 17))
    if has_mesh('Map_Flowers1', 'Map_Flowers2'):
        mpart(r.choice(('Map_Flowers1', 'Map_Flowers2')), x, 0, z, r.uniform(0, 360), r.uniform(0.8, 1.1), noshadow=True)
        return
    h, g = r.uniform(1.6, 2.8), (70, 160, 70)
    blk(x, 0, z, 0.4, h, 0.4, g, **NC)
    blk(x + 0.55, h * 0.35, z, 0.9, 0.3, 0.5, shade(g, 1.15), **NC)                  # leaf
    blk(x - 0.9, 0, z + 0.5, 0.35, 0.9, 0.35, shade(g, 1.2), **NC)                   # grass blades
    blk(x - 0.5, 0, z + 0.9, 0.35, 1.3, 0.35, g, **NC)
    if r.random() < 0.35:                                                             # tulip
        blk(x, h, z, 1.1, 1.3, 1.1, col, **NC)
        blk(x, h + 1.3, z, 0.6, 0.5, 0.6, shade(col, 1.2), **NC)
    else:                                                                             # daisy: 4 petals + centre
        blk(x, h, z, 2.5, 0.55, 0.9, col, **NC)
        blk(x, h, z, 0.9, 0.55, 2.5, col, **NC)
        blk(x, h + 0.2, z, 1.0, 0.7, 1.0, (255, 214, 60), **NC)


def rock(x, z, s, col):
    if has_mesh('Map_Rock1', 'Map_Rock2'):
        yaw = rng.uniform(0, 90)
        rng.uniform(0, 90)                       # same dice use as the block rock, so the rest of the layout stays put
        k = rng.uniform(0, 90)
        mpart('Map_Rock1' if k < 45 else 'Map_Rock2', x, 0, z, yaw * 4, s)
        blk(x, 0, z, 4.2 * s, 2.6 * s, 3.6 * s, col, 'Slate', transparency=1)
        return
    blk(x, 0, z, 4.6 * s, 1.4 * s, 4 * s, shade(col, 0.86), 'Slate', yaw=rng.uniform(0, 90))
    blk(x, 1.2 * s, z, 3.6 * s, 1.6 * s, 3 * s, col, 'Slate', yaw=rng.uniform(0, 90))
    blk(x + 1.2 * s, 0, z + 0.8 * s, 2.4 * s, 3.8 * s, 2.4 * s, shade(col, 1.12), 'Slate', yaw=rng.uniform(0, 90))
    blk(x + 1.2 * s, 3.8 * s, z + 0.8 * s, 1.5 * s, 0.6 * s, 1.5 * s, shade(col, 1.25), 'Slate', **NC)
    blk(x - 0.4 * s, 2.8 * s, z - 0.2 * s, 2.2 * s, 0.4 * s, 1.8 * s, (96, 190, 84), 'Grass', **NC)   # moss
    blk(x - 2.8 * s, 0, z + 1.6 * s, 1.2 * s, 0.9 * s, 1.2 * s, shade(col, 1.05), 'Slate', **NC)      # pebble


def cloud(x, y, z, s, col):
    """Neon = lit the same from every side, so the underside is not dark; no shadows on the map"""
    CL = dict(cancollide=False, noshadow=True)
    col = shade(col, 0.86)
    blk(x, y, z, 30 * s, 8 * s, 18 * s, col, 'Neon', **CL)
    blk(x - 4 * s, y + 6 * s, z, 18 * s, 7 * s, 13 * s, shade(col, 1.04), 'Neon', **CL)
    blk(x + 13 * s, y + 3 * s, z + 2 * s, 14 * s, 7 * s, 12 * s, col, 'Neon', **CL)
    blk(x - 15 * s, y + 2 * s, z - 2 * s, 12 * s, 6 * s, 11 * s, shade(col, 0.97), 'Neon', **CL)


EGG_PROF = {5: [0.62, 0.92, 1.0, 0.84, 0.52], 9: [0.5, 0.74, 0.9, 0.98, 1.0, 0.94, 0.82, 0.64, 0.4]}


def egg(x, y, z, s, col, spot=None, beam=False, mat='SmoothPlastic', n=5, name='DemoEgg'):
    """voxel egg with two stripes; y = centre of the fat part (as before), about 3.9*s tall"""
    prof = EGG_PROF[n]
    h = 3.9 * s / n
    yb = y - 1.5 * s
    for k, w in enumerate(prof):
        blk(x, yb + k * h, z, 3 * s * w, h, 3 * s * w, col, mat, name=name, **NC)
    if spot:
        for k in ((1, 3) if n == 5 else (2, 4, 6)):
            w = 3 * s * prof[k] + 0.14 * s
            blk(x, yb + k * h + h * 0.3, z, w, h * 0.4, w, spot, mat, **NC)
    if beam:
        vcyl(x, y + 2.4 * s, z, 90, 1.6 * s, col, 'Neon', transparency=0.72, **NC)


def tiles(z0, z1, ground, par=0, T=14):
    """checkerboard floor (thin overlay tiles on every second square)"""
    c2 = shade(ground, 0.9)
    nx = int((HALF * 2 + 48) // T) + 1
    for iz, z in enumerate(range(int(z0), int(z1), T)):
        for ix in range(nx):
            if (ix + iz + par) % 2 == 0:
                blk(-(HALF + 24) + ix * T + T / 2, 0, z + T / 2, T, 0.1, T, c2, 'Plastic', **NC)


def wall_run(z0, z1, ground, cliff, H=30):
    """straight checker dirt walls on both sides with a jagged grass cap (Throw Food For Animals look)"""
    for sx in (-1, 1):
        for k, z in enumerate(range(int(z0), int(z1), 20)):
            ln = min(20, z1 - z)
            for row in range(2):
                blk(sx * (HALF + 12), -4 + row * (H + 4) / 2, z + ln / 2, 24, (H + 4) / 2, ln,
                    cliff if (k + row) % 2 == 0 else shade(cliff, 1.13), 'Plastic')
            blk(sx * (HALF + 11), H, z + ln / 2, 26, 4, ln, ground, 'Plastic')
            for q in range(2):
                ex = 0   # v107 (user: 'why is it not uniform'): one even grass band, no up-and-down steps
                blk(sx * (HALF - 0.7), H - 3 - ex, z + ln * (0.25 + 0.5 * q), 1.6, 3 + ex, ln / 2, ground, 'Plastic', **NC)
        blk(sx * (HALF + 25), 0, (z0 + z1) / 2, 2, 120, z1 - z0, WHITE, transparency=1, name='Wall')


def patches(z0, z1, col, n=46, y=0.0):
    return                                  # voxel style uses the checkerboard instead
    for _ in range(n):
        w, d = rng.choice((6, 8, 10, 14)), rng.choice((6, 8, 10, 14))
        blk(side_x(12, 166), y, rng.uniform(z0 + 8, z1 - 8), w, 0.14, d, col, **NC)


def arch_layout(n):
    """same numbers as arch_layout() in blender/gen_zone_signs.py: P = pillar centre |x|, Y0 = board bottom, H = board height"""
    return (12.0, 20.0, 12.0) if n == 1 else (11.3, 15.6, 10.0)   # pillars stand on the road edges (ROADW 18; gate C.GATE.width 18 between them)


def zone_arch(n, z, front, back, c1, c2, sub=None):
    """the Blender zone arch (blender/gen_zone_signs.py): soft meshes + invisible collision boxes + the text panels in its frames"""
    body, glow = f'Map_ZoneArch_{n}', f'Map_ZoneArchNeon_{n}'
    if not has_mesh(body, glow):
        return False
    P, Y0, H = arch_layout(n)
    big = n == 1
    W, D, pw = 2 * P + 8, 3.0, (6.0 if big else 4.6)
    mpart(body, 0, 0, z, cancollide=False)
    mpart(glow, 0, 0, z, mat='Neon', cancollide=False)
    INV = dict(transparency=1)
    for sx in (-1, 1):                                                    # what you bump into: pillars, plinths, board ends
        blk(sx * P, 0, z, pw + 2.2, 2.2, pw + 2.2, c2, **INV)
        blk(sx * P, 2.2, z, pw, Y0 - 2.2, pw, c2, **INV)
    blk(0, Y0, z, W + 3.6, H, D + 1.0, c2, **INV)
    # the zone name on the board (front = players coming from -Z) and the zone number on the crest
    b = blk(0, Y0 + 1.4, z, W - 2.6, H - 2.8, 3.2, INK)
    sign(b, 'Front', front, sub, bg1=shade(c1, 1.04), bg2=shade(c2, 0.95), pps=16 if big else 20, pad=0.035)
    sign(b, 'Back', back, None, bg1=shade(c1, 1.04), bg2=shade(c2, 0.95), pps=16 if big else 20, pad=0.035)
    cr = 4.4 if big else 3.4
    k = cr * 1.2
    nb = blk(0, Y0 + H + cr * 0.72 - k / 2, z, k, k, D + 1.3, INK)
    sign(nb, 'Front', str(n), None, bg1=shade(c1, 1.08), bg2=c1, pps=20, pad=0.0)
    sign(nb, 'Back', str(n), None, bg1=shade(c1, 1.08), bg2=c1, pps=20, pad=0.0)
    return True


def gate(z, title, sub, c1, c2, pill=WHITE, n=None):
    """arch over the road at the start of a zone, sign faces the players coming from -Z"""
    if n and zone_arch(n, z, title, title, c1, c2):
        for sx in (-1, 1):                                                # border line with flags across the whole width
            blk(sx * (HALF + 14) / 2 + sx * 2, 0, z, HALF - 18, 0.3, 2.4, c1, **NC)
            for x in range(34, HALF - 4, 28):
                blk(sx * x, 0, z, 0.8, 9, 0.8, WHITE, **NC)
                blk(sx * x + 2.2, 6, z, 4, 2.6, 0.4, c1, **NC)
        return
    for sx in (-1, 1):
        blk(sx * 14, 0, z, 5, 22, 5, pill)
        blk(sx * 14, 0, z, 6, 2, 6, c2)
        blk(sx * 14, 10, z, 5.4, 2, 5.4, c1)
        blk(sx * 14, 22, z, 6.4, 2, 6.4, c2)
        egg(sx * 14, 26.2, z, 1.5, c1, WHITE)
    b = blk(0, 15, z, 34, 8, 3, c2)
    # no speed line; text kept between the pillars (they cover ~11..17 studs of each side of the 34-stud panel)
    sign(b, 'Front', title, None, bg1=c1, bg2=c2, pad=0.2)
    sign(b, 'Back', title, None, bg1=c1, bg2=c2, pad=0.2)
    # border line with flags across the whole width
    for sx in (-1, 1):
        blk(sx * (HALF + 14) / 2 + sx * 2, 0, z, HALF - 18, 0.3, 2.4, c1, **NC)
        for x in range(34, HALF - 4, 28):
            blk(sx * x, 0, z, 0.8, 9, 0.8, WHITE, **NC)
            blk(sx * x + 2.2, 6, z, 4, 2.6, 0.4, c1, **NC)


def zone_base(i, ground, gmat, road, cliff, dirt=DIRT):
    z0 = i * ZL
    zc = z0 + ZL / 2
    blk(0, -4, zc, HALF * 2 + 48, 4, ZL, ground, 'Plastic')
    blk(0, -13, zc, HALF * 2 + 40, 9, ZL - 2, dirt, 'Plastic')
    tiles(z0, z0 + ZL, ground)
    blk(0, 0, zc, ROADW, 0.3, ZL, road, 'Plastic')
    for sx in (-1, 1):
        blk(sx * (ROADW / 2 + 0.6), 0, zc, 1.2, 0.7, ZL, shade(road, 0.8), 'Plastic')
    for z in range(int(z0) + 10, int(z0 + ZL), 20):          # dashed centre line
        blk(0, 0.3, z, 1.2, 0.06, 9, shade(road, 1.25), 'Plastic', **NC)
    for sx in (-1, 1):                                        # stepped ledge under the cliffs
        blk(sx * (HALF - 4), 0, zc, 8, 7, ZL, shade(cliff, 0.88), 'Plastic')
        blk(sx * (HALF - 4.5), 7, zc, 9, 1.5, ZL, shade(ground, 1.08), 'Plastic')
    wall_run(z0, z0 + ZL, ground, cliff)
    return z0, zc


def egg_sky(z0, cloudcol, eggs):
    """clouds above the zone + a few eggs frozen in mid-fall (the game script replaces them)"""
    for k in range(5):
        cloud(rng.uniform(-130, 130), rng.uniform(88, 116), z0 + 14 + k * 27, rng.uniform(0.9, 1.4), cloudcol)
    for k in range(11):
        col, spot = rng.choice(eggs)
        rng.uniform(-150, 150), rng.uniform(4, 78), rng.uniform(z0 + 10, z0 + ZL - 10), rng.choice((1.0, 1.0, 1.3))  # keep the dice the same
        continue  # no frozen decor eggs: the game drops real ones (their brown spots stayed floating)
        egg(rng.uniform(-150, 150), rng.uniform(4, 78), rng.uniform(z0 + 10, z0 + ZL - 10), rng.choice((1.0, 1.0, 1.3)), col, spot,
            beam=(k == 0))


# ------------------------------------------------------------------ home: bases + plaza
BASE_COLS = [((240, 70, 70), 'RED'), ((255, 150, 40), 'ORANGE'), ((255, 214, 50), 'YELLOW'), ((90, 200, 80), 'GREEN'),
             ((60, 200, 230), 'CYAN'), ((70, 120, 250), 'BLUE'), ((160, 100, 250), 'PURPLE'), ((255, 120, 190), 'PINK')]


PET_COLS = [((255, 170, 60), WHITE), ((240, 240, 245), (255, 150, 190)), ((120, 90, 60), (230, 200, 160)),
            ((255, 220, 70), (255, 140, 40)), ((120, 200, 255), WHITE), ((190, 130, 255), (255, 230, 90))]


def demo_pet(x, y, z, cols):
    """tiny voxel animal facing +Z (placeholder until the real pets exist)"""
    c1, c2 = cols
    for sx in (-1, 1):
        for sz in (-1, 1):
            blk(x + sx * 0.8, y, z + sz * 1.1, 0.7, 1, 0.7, shade(c1, 0.8), name='DemoPet', **NC)
        blk(x + sx * 0.8, y + 4.3, z + 1.6, 0.6, 0.8, 0.5, c1, **NC)
        blk(x + sx * 0.55, y + 3.2, z + 2.9, 0.4, 0.4, 0.2, INK, **NC)
    blk(x, y + 1, z, 2.4, 1.8, 3.4, c1, name='DemoPet', **NC)
    blk(x, y + 1, z, 2.5, 0.7, 2.2, c2, **NC)
    blk(x, y + 2.3, z + 1.8, 2.1, 2, 2, c1, name='DemoPet', **NC)
    blk(x, y + 2.5, z + 2.9, 1, 0.7, 0.4, c2, **NC)
    blk(x, y + 1.8, z - 1.9, 0.6, 0.6, 0.8, c2, **NC)


WOOD = (222, 150, 66)
WOOD2 = (186, 112, 50)


def base(i):
    """a plot of the normal checker grass with a plain wooden fence; pets stand inside and earn on their own"""
    bx = -147 + i * 42
    zf, zb = -60, -112
    zc = (zf + zb) / 2
    prng = random.Random(500 + i)
    with group(f'Base{i + 1}', unique=False):
        blk(bx, 0, zc, 34, 0.1, zf - zb, (118, 204, 84), 'Plastic', name='PenFloor', transparency=1, **NC)   # marks the pen area for scripts
        col = BASE_COLS[i][0]
        dk, lt = shade(col, 0.7), tuple(int(v + (255 - v) * 0.55) for v in col)
        STONE, STONE2 = (232, 236, 246), (196, 202, 220)
        # the name floats in the air above the pen (the game script puts the text on this invisible part)
        blk(bx, 16, zc, 1, 1, 1, WHITE, name='OwnerSign', transparency=1, **NC)
        # stone curb under the fence

        # fence = the user's model gard.lua (post 2x6x2 with cap, 2 planks, small decor squares)
        G_POST, G_RAIL, G_DET = (170, 116, 58), (228, 180, 86), (190, 140, 52)
        FY = 0                                                  # straight on the grass, like the model

        # Blender meshes (once the user imported them: ids in game\meshes.json, sizes in game\props_meta.json)
        gdir = pathlib.Path(__file__).resolve().parent.parent / 'game'
        ids = json.loads((gdir / 'meshes.json').read_text(encoding='utf-8')) if (gdir / 'meshes.json').exists() else {}
        pm = json.loads((gdir / 'props_meta.json').read_text(encoding='utf-8')) if (gdir / 'props_meta.json').exists() else {}
        use_mesh = 'Fence_Post' in ids and 'Fence_Rail' in ids and 'Fence_Rail' in pm

        def post(x, z):
            if use_mesh:
                m = pm['Fence_Post']
                part(m['size'], C(x, FY + m['centre'][1], z), (255, 255, 255), name='FencePost', mesh='Fence_Post')
                blk(x, FY, z, 2, 6, 2, G_POST, 'Plastic', name='FenceWall', transparency=1, **NC)      # (v102: the mesh itself is solid now)
                return
            blk(x, FY, z, 2, 6, 2, G_POST, 'Plastic')
            blk(x, FY + 6, z, 2.3, 0.4, 2.3, G_RAIL, 'Plastic', noshadow=True, **NC)
            for y in (2, 4.2):
                blk(x, FY + y - 0.35, z, 2.12, 0.7, 0.7, G_DET, 'Plastic', noshadow=True, **NC)
                blk(x, FY + y - 0.35, z, 0.7, 0.7, 2.12, G_DET, 'Plastic', noshadow=True, **NC)

        def rail(x, z, L, along_x):
            if use_mesh:
                m = pm['Fence_Rail']
                k = max(1, round(L / 10))                       # the mesh is 10 long: tile it, stretch each piece a little
                seg = L / k
                for j in range(k):
                    t = -L / 2 + seg * (j + 0.5)
                    cf = C(x + (t if along_x else 0), FY + m['centre'][1], z + (0 if along_x else t))
                    part((seg, m['size'][1], m['size'][2]), cf if along_x else cf * R(0, 90, 0), (255, 255, 255), name='FenceRail', mesh='Fence_Rail')
                blk(x, FY, z, L if along_x else 0.8, 5, 0.8 if along_x else L, G_RAIL, 'Plastic', name='Fence', transparency=1, **NC)
                return
            n = max(1, int(L / 2))
            for y in (2, 4.2):
                blk(x, FY + y - 0.6, z, L if along_x else 0.8, 1.2, 0.8 if along_x else L, G_RAIL, 'Plastic', name='Fence')
                for k in range(n):
                    t = -L / 2 + L / n * (k + 0.5)
                    if along_x:
                        blk(x + t, FY + y - 0.25, z, 0.5, 0.5, 0.92, G_DET, 'Plastic', noshadow=True, **NC)
                    else:
                        blk(x, FY + y - 0.25, z + t, 0.92, 0.5, 0.5, G_DET, 'Plastic', noshadow=True, **NC)

        FW_POST, FW_RAIL = (112, 72, 40), (228, 164, 62)          # the colours of the Blender fence (dark posts, golden rails)

        def pillar(x, z, h=7.5):
            # v103 (user): the entrance has the same wood colours as the fence
            blk(x, 0, z, 2.8, 1, 2.8, shade(FW_POST, 0.85), 'Wood')
            blk(x, 1, z, 2.2, h - 1, 2.2, FW_POST, 'Wood')
            blk(x, h - 2.2, z, 2.4, 0.9, 2.4, FW_RAIL, 'Wood')
            blk(x, h, z, 2.8, 0.6, 2.8, shade(FW_POST, 0.85), 'Wood')

        def lamp(x, z, y):
            p = blk(x, y, z, 1.3, 1.3, 1.3, (255, 240, 170), 'Neon', **NC)
            light(p, (255, 230, 160), 18, 1.2)
            blk(x, y + 1.3, z, 1.7, 0.4, 1.7, dk, **NC)

        for k in range(1, 5):
            for sx in (-1, 1):
                post(bx + sx * 17, zb + k * 10.4)
        for k in range(1, 3):
            post(bx - 17 + k * 34 / 3, zb)
        for sx in (-1, 1):
            post(bx + sx * 11.5, zf)
            rail(bx + sx * 17, zc, zf - zb, False)
            rail(bx + sx * 11.5, zf, 11, True)
            for z in (zb, zf):                                  # corners = plain fence posts (no stone, no lamps)
                post(bx + sx * 17, z)
            # (v109: user removed the gate at the pen entrance: no pillars / beam, just the opening in the fence)
            post(bx + sx * 6.0, zf)                             # v110: end post where the front rail stops (no cut-off fence)
        rail(bx, zb, 34, True)
        blk(bx, 0.02, zf, 10.4, 0.12, 5, lt, **NC)              # door mat
        blk(bx, 0.03, zf, 8.6, 0.12, 3.4, col, **NC)
        # hay and water at the back fence
        for hx, hz, hy in ((-13.5, zb + 3, 0), (-10.4, zb + 3, 0), (-12, zb + 3, 2.2)):
            blk(bx + hx, hy, hz, 3, 2.2, 2.6, (238, 200, 96), **NC)
            blk(bx + hx, hy + 0.8, hz, 3.1, 0.35, 2.7, (200, 150, 70), **NC)
        blk(bx + 11.5, 0, zb + 2.8, 6, 1.6, 2.6, WOOD2)
        blk(bx + 11.5, 1.2, zb + 2.8, 5.2, 0.5, 1.8, (90, 190, 250), **NC)
        # speed trainer in the front corner
        # invisible marker: the game script builds a TreadmillPack model here (console towards the back fence)
        blk(bx - 11.5, 0, zf - 8.5, 7.6, 0.8, 14.6, (40, 44, 60), name='Treadmill', transparency=1, **NC)
        # sign on the side fence next to the treadmill: TREADMILL / LEVEL n / next price (text = game script, face +X into the pen)
        # upgrade panel on the FRONT fence, right in front of the treadmill, facing the plaza (+Z = Back face)
        # (invisible here: only the owner's client shows its own board)
        blk(bx - 14.25, 1.45, zf + 1.15, 5.3, 3.5, 0.25, (255, 200, 60), 'SmoothPlastic', name='TreadSignBack', transparency=1, **NC)
        blk(bx - 14.25, 1.5, zf + 1.35, 5.1, 3.4, 0.2, (28, 24, 58), 'SmoothPlastic', name='TreadSign', transparency=1, **NC)


SHOP_KEY = {'BASKETS': 'Baskets', 'LUCK SHOP': 'Luck', 'SELL': 'Sell', 'INDEX': 'Index'}


def stall_mesh(x, z, title, sub, col, key, ids, pm):
    """the Blender shop (blender\\gen_shops.py) + invisible collision boxes, ShopPad, sign text, lights, vendor"""
    r = type(rng)(int(x * 3 + 500))
    INV = dict(transparency=1)
    with group('Shop'):
        for nm, mat in ((f'Shop_{key}', 'SmoothPlastic'), (f'ShopNeon_{key}', 'Neon')):
            if nm in ids and nm in pm:
                c = pm[nm]['centre']
                part(pm[nm]['size'], C(x + c[0], c[1], z + c[2]) * R(0, 180, 0), (255, 255, 255), mat, name='ShopMesh', mesh=nm, **NC)  # Roblox imports Blender meshes turned 180 -> turn back about the box centre
        blk(x, 0, z, 24, 0.7, 16, col, **INV)                                   # floor you walk on
        # shop zone = a HALF circle joined to the shop front, in the shop colour (step in = shop menu)
        cx, cz, rad, N = x, z - 8, 12.0, 24
        for i in range(N):
            a = math.pi * (i + 0.5) / N                                         # 0..pi, out of the shop front (-Z)
            yaw = math.degrees(math.atan2(math.cos(a), -math.sin(a)))
            w = 2 * rad * math.sin(math.pi / (2 * N)) * 1.12
            part((w, 0.56, rad - 0.4), C(cx + (rad - 0.4) / 2 * math.cos(a), 0.28, cz - (rad - 0.4) / 2 * math.sin(a)) * R(0, yaw, 0), col, 'SmoothPlastic', name='ShopZone', **NC)
            part((w * 1.04, 0.64, 0.8), C(cx + (rad - 0.4) * math.cos(a), 0.32, cz - (rad - 0.4) * math.sin(a)) * R(0, yaw, 0), tuple(int(v + (255 - v) * 0.45) for v in col), 'Neon', name='ShopZone', **NC)
        part((0.3, 2 * rad, 2 * rad), C(cx, 0.15, cz) * R(0, 0, 90), col, 'SmoothPlastic', 'Disc', name='ShopPad', transparency=1, **NC)
        CIRCLES.extend([(x, z - 16, 4.5), (x - 6, z - 13, 4.5), (x + 6, z - 13, 4.5)])
        blk(x, 0.6, z - 4, 18, 4.6, 3.4, col, **INV)                            # counter
        blk(x, 0.6, z + 6, 20, 13, 1, col, **INV)                               # back wall
        for sx in (-1, 1):
            blk(x + sx * 9.5, 0.6, z, 0.8, 5, 10, col, **INV)                    # side walls
            for pz in (-5.5, 5.5):
                blk(x + sx * 9.5, 0.6, z + pz, 1.4, 13, 1.4, col, **INV)         # posts
            light(blk(x + sx * 9.5, 7.4, z - 6.9, 1.4, 1.9, 1.4, col, **INV, **NC), (255, 220, 140), 20, 1.4)
        for cx, cy, cs in ((-13.4, 0, 3.6), (-13.6, 0, 2.6)):                    # crates + flower pot
            blk(x + cx, cy, z - 3 + (4.2 if cs == 2.6 else 0), cs, cs * (1.8 if cs == 3.6 else 1), cs, col, **INV)
        blk(x + 13.4, 0, z - 3, 3.6, 2.7, 3.6, col, **INV)
        sb = blk(x, 16.5, z - 7.1, 18, 5, 1.2, INK)                               # the text panel inside the mesh frame
        sign(sb, 'Front', title, sub, bg1=shade(col, 1.08), bg2=shade(col, 0.68))
    with group('Vendor'):
        blk(x - 5.6, 0.6, z + 0.4, 4.4, 2.6, 3.2, WOOD, 'WoodPlanks')
        blk(x - 5.6, 3.0, z + 0.4, 4.7, 0.2, 3.5, WOOD2, 'Wood')
        person(x - 5.6, 3.2, z + 0.4, 1.3, col, r)


def stall(x, z, title, sub, col, prop):
    gdir = pathlib.Path(__file__).resolve().parent.parent / 'game'
    ids = json.loads((gdir / 'meshes.json').read_text(encoding='utf-8')) if (gdir / 'meshes.json').exists() else {}
    pm = json.loads((gdir / 'props_meta.json').read_text(encoding='utf-8')) if (gdir / 'props_meta.json').exists() else {}
    key = SHOP_KEY.get(title)
    if key and f'Shop_{key}' in ids and f'Shop_{key}' in pm:
        return stall_mesh(x, z, title, sub, col, key, ids, pm)
    r = type(rng)(int(x * 3 + 500))
    dk, lt = shade(col, 0.72), shade(col, 1.15)
    with group('Shop'):
        # floor: coloured trim, cream tiles, welcome mat (ShopPad = touch trigger for the game script)
        blk(x, 0, z, 24, 0.5, 16, dk)
        blk(x, 0, z, 22, 0.7, 14, (236, 226, 204))
        for k in range(5):
            blk(x - 8.8 + k * 4.4, 0.7, z - 1 + (3 if k % 2 else -3), 4.4, 0.06, 6, (222, 208, 180), **NC)
        blk(x, 0, z - 10.5, 12, 0.2, 5, WHITE, **NC)
        blk(x, 0, z - 10.5, 11, 0.3, 4, col, name='ShopPad', **NC)
        # counter: planks, striped front panels, coloured trim, cream top
        blk(x, 0.6, z - 4, 18, 4, 3, BROWN, 'WoodPlanks')
        for k in range(9):
            blk(x - 8 + k * 2, 1.1, z - 5.6, 2, 3, 0.25, col if k % 2 == 0 else WHITE, **NC)
        blk(x, 0.6, z - 5.6, 18.4, 0.5, 0.5, dk, **NC)
        blk(x, 4.2, z - 4, 18.6, 0.4, 3.5, dk)
        blk(x, 4.6, z - 4, 19.6, 0.6, 4.4, CREAM)
        # posts with coloured feet and caps
        for sx in (-1, 1):
            for pz in (-5.5, 5.5):
                blk(x + sx * 9.5, 0.6, z + pz, 1.2, 13, 1.2, WOOD2, 'Wood')
                blk(x + sx * 9.5, 0.6, z + pz, 1.9, 1.4, 1.9, col)
                blk(x + sx * 9.5, 12.4, z + pz, 1.9, 1.2, 1.9, col)
            # hanging lantern + side wall rail
            blk(x + sx * 9.5, 9.6, z - 6.9, 0.25, 2.2, 0.25, INK, **NC)
            light(blk(x + sx * 9.5, 8, z - 6.9, 1.5, 1.7, 1.5, (255, 226, 130), 'Neon', **NC), (255, 220, 140), 20, 1.4)
            blk(x + sx * 9.5, 0.6, z, 0.6, 5, 9.8, shade(col, 0.9))
            blk(x + sx * 9.5, 5.6, z, 1, 0.5, 10.2, CREAM)
        # back wall with two shelves full of goods
        blk(x, 0.6, z + 6, 20, 13, 1, shade(col, 0.8))
        blk(x, 0.6, z + 5.4, 20, 2.4, 0.3, dk, **NC)
        for sy in (6.2, 9.8):
            blk(x, sy, z + 4.8, 18, 0.45, 1.8, WOOD, 'Wood', **NC)
            for k in range(7):
                gx, gc = x - 7.5 + k * 2.5, r.choice(RAINBOW)
                if r.random() < 0.5:
                    egg(gx, sy + 0.45 + 0.66, z + 4.8, 0.44, gc, WHITE, name='Decor')
                else:
                    h = r.uniform(1.1, 2)
                    blk(gx, sy + 0.45, z + 4.8, 1.5, h, 1.2, gc, **NC)
                    blk(gx, sy + 0.45 + h * 0.4, z + 4.8, 1.56, h * 0.25, 1.26, WHITE, **NC)
        # striped awning with a scalloped front edge
        for k in range(10):
            c = col if k % 2 == 0 else WHITE
            part((2.2, 0.8, 15), C(x - 9.9 + k * 2.2, 14.6, z - 1) * R(-12, 0, 0), c)
            vh = 1.9 if k % 2 == 0 else 1.3
            blk(x - 9.9 + k * 2.2, 12.9 - vh, z - 8.3, 2.2, vh, 0.5, c, **NC)
        blk(x, 15.9, z + 6.2, 22.4, 0.9, 1.4, dk, **NC)                        # roof ridge
        # sign on two supports, eggs on its ends
        for sx in (-1, 1):
            blk(x + sx * 8, 13, z - 7, 0.8, 3.6, 0.8, WOOD2, 'Wood', **NC)
            egg(x + sx * 8, 21.9 + 1.35, z - 7, 0.9, lt, WHITE, name='Decor')
        blk(x, 16.2, z - 7, 19, 5.6, 1, col)
        sb = blk(x, 16.5, z - 7.1, 18, 5, 1.2, INK)
        sign(sb, 'Front', title, sub, bg1=shade(col, 1.08), bg2=shade(col, 0.68))
        # outside: crates on the left, potted bush on the right
        for cx, cy, cs, cyaw in ((-13.4, 0, 3.6, 8), (-13.1, 3.6, 2.8, -14), (-13.6, 0, 2.6, 30)):
            cz = z - 3 + (4.2 if cs == 2.6 else 0)
            blk(x + cx, cy, cz, cs, cs, cs, WOOD, 'WoodPlanks', yaw=cyaw)
            blk(x + cx, cy + cs, cz, cs + 0.3, 0.3, cs + 0.3, WOOD2, 'Wood', yaw=cyaw, **NC)
        blk(x + 13.4, 0, z - 3, 3, 2.2, 3, (206, 110, 70))
        blk(x + 13.4, 2.2, z - 3, 3.5, 0.5, 3.5, (226, 130, 86), **NC)
        blk(x + 13.4, 2.7, z - 3, 4, 3, 4, (74, 176, 70), 'Grass', **NC)
        blk(x + 13.4, 5.7, z - 3, 2.8, 2.2, 2.8, (96, 200, 84), 'Grass', yaw=45, **NC)
        for dx, dz in ((1.6, -1.8), (-1.5, 1.2), (0.4, 0.2)):
            blk(x + 13.4 + dx, 5.4 + dz * 0.3, z - 3 + dz, 0.9, 0.9, 0.9, lt, **NC)
        prop(x + 3, z - 4)
    with group('Vendor'):
        blk(x - 5.6, 0.6, z + 0.4, 4.4, 2.6, 3.2, WOOD, 'WoodPlanks')                # crate the vendor stands on
        blk(x - 5.6, 3.0, z + 0.4, 4.7, 0.2, 3.5, WOOD2, 'Wood')
        person(x - 5.6, 3.2, z + 0.4, 1.3, col, r)


def person(x, y, z, s, col, r):
    """real Roblox R6 character (Humanoid rig, round head, classic face) dressed as a shopkeeper, facing -Z"""
    skin, pants = r.choice(SKINS), r.choice(((60, 80, 150), (70, 70, 80), (120, 84, 52)))
    hair = r.choice(HAIRS)
    for sx, nm in ((-1, 'Left Leg'), (1, 'Right Leg')):
        blk(x + sx * 0.5 * s, y, z, 1 * s, 2 * s, 1 * s, pants, 'Plastic', name=nm)
    blk(x, y + 2 * s, z, 2 * s, 2 * s, 1 * s, WHITE, 'Plastic', name='Torso', rig=True)
    blk(x, y + 2 * s, z, 2 * s, 2 * s, 1 * s, WHITE, name='HumanoidRootPart', transparency=1, **NC)
    blk(x - 1.5 * s, y + 2 * s, z, 1 * s, 2 * s, 1 * s, skin, 'Plastic', name='Left Arm')
    part((1 * s, 2 * s, 1 * s), C(x + 1.95 * s, y + 4.58 * s, z) * R(0, 0, -30), skin, 'Plastic', name='Right Arm')   # waving
    blk(x, y + 4 * s, z, 2 * s, 1 * s, 1 * s, skin, 'Plastic', name='Head', headmesh=True, face=True)
    # clothes: sleeves, apron with bib and pocket, cap with brim and badge, hair at the back
    blk(x - 1.5 * s, y + 3.2 * s, z, 1.06 * s, 0.82 * s, 1.06 * s, WHITE, name='Sleeve', **NC)
    part((1.06 * s, 0.82 * s, 1.06 * s), C(x + 1.72 * s, y + 4.17 * s, z) * R(0, 0, -30), WHITE, name='Sleeve', **NC)
    blk(x, y + 0.9 * s, z - 0.54 * s, 1.9 * s, 2.3 * s, 0.1 * s, col, name='Apron', **NC)
    blk(x, y + 3.2 * s, z - 0.54 * s, 1.1 * s, 0.7 * s, 0.1 * s, col, name='Apron', **NC)
    blk(x, y + 1.7 * s, z - 0.6 * s, 0.9 * s, 0.6 * s, 0.08 * s, shade(col, 0.75), name='Apron', **NC)
    blk(x, y + 3.0 * s, z, 2.04 * s, 0.22 * s, 1.04 * s, shade(col, 0.75), name='Apron', **NC)          # belt / strings
    hy = y + 4 * s
    blk(x, hy + 0.2 * s, z + 0.42 * s, 1.3 * s, 0.75 * s, 0.5 * s, hair, name='Hair', **NC)
    blk(x, hy + 0.9 * s, z, 1.36 * s, 0.5 * s, 1.36 * s, col, name='Cap', **NC)
    blk(x, hy + 0.9 * s, z - 0.95 * s, 1.2 * s, 0.14 * s, 0.6 * s, shade(col, 0.75), name='Cap', **NC)
    blk(x, hy + 1.0 * s, z - 0.7 * s, 0.45 * s, 0.28 * s, 0.05 * s, WHITE, name='Cap', **NC)


SKINS = [(255, 214, 170), (240, 190, 140), (200, 140, 96), (150, 100, 66)]
HAIRS = [(70, 46, 30), (30, 26, 30), (230, 180, 70), (190, 80, 40), (120, 70, 180)]


def person_voxel(x, y, z, s, col, r):
    """OLD blocky shopkeeper facing -Z: apron and cap in the stall colour, one arm waving"""
    skin, hair, pants = r.choice(SKINS), r.choice(HAIRS), r.choice(((60, 80, 150), (70, 70, 80), (120, 84, 52)))
    kw = dict(name='Vendor')
    for sx in (-1, 1):
        blk(x + sx * 0.5 * s, y, z, 0.95 * s, 2 * s, 1 * s, pants, **kw)
        blk(x + sx * 0.5 * s, y, z - 0.1 * s, 1 * s, 0.45 * s, 1.25 * s, INK, **kw)          # shoes
    blk(x, y + 2 * s, z, 2 * s, 2 * s, 1 * s, WHITE, **kw)                                   # shirt
    blk(x, y + 2 * s, z - 0.55 * s, 1.5 * s, 1.5 * s, 0.12 * s, col, **kw)                   # apron
    blk(x, y + 2.3 * s, z - 0.62 * s, 0.7 * s, 0.5 * s, 0.1 * s, shade(col, 0.75), **kw)     # pocket
    blk(x, y + 3.5 * s, z - 0.55 * s, 0.9 * s, 0.5 * s, 0.12 * s, col, **kw)                 # apron bib
    blk(x - 1.5 * s, y + 3.1 * s, z, 1 * s, 0.9 * s, 1 * s, WHITE, **kw)                     # left sleeve + arm
    blk(x - 1.5 * s, y + 2 * s, z, 0.9 * s, 1.1 * s, 0.9 * s, skin, **kw)
    part((1 * s, 1 * s, 1 * s), C(x + 1.6 * s, y + 3.7 * s, z) * R(0, 0, -30), WHITE, **kw)  # right arm waves
    part((0.9 * s, 1.3 * s, 0.9 * s), C(x + 2.15 * s, y + 4.65 * s, z) * R(0, 0, -30), skin, **kw)
    hy = y + 4 * s
    blk(x, hy, z, 1.3 * s, 1.3 * s, 1.3 * s, skin, **kw)                                     # head
    for sx in (-1, 1):
        blk(x + sx * 0.3 * s, hy + 0.65 * s, z - 0.67 * s, 0.2 * s, 0.3 * s, 0.06 * s, INK, **kw)        # eyes
        blk(x + sx * 0.48 * s, hy + 0.36 * s, z - 0.67 * s, 0.22 * s, 0.14 * s, 0.05 * s, (255, 150, 150), **kw)  # cheeks
    blk(x, hy + 0.25 * s, z - 0.67 * s, 0.5 * s, 0.12 * s, 0.06 * s, INK, **kw)              # smile
    for sx in (-1, 1):
        blk(x + sx * 0.3 * s, hy + 0.33 * s, z - 0.67 * s, 0.12 * s, 0.12 * s, 0.06 * s, INK, **kw)
    blk(x, hy + 0.5 * s, z + 0.4 * s, 1.44 * s, 0.9 * s, 0.7 * s, hair, **kw)                # hair back + top
    blk(x, hy + 1.2 * s, z, 1.44 * s, 0.25 * s, 1.44 * s, hair, **kw)
    blk(x, hy + 1.4 * s, z, 1.5 * s, 0.5 * s, 1.5 * s, col, **kw)                            # cap
    blk(x, hy + 1.4 * s, z - 1 * s, 1.3 * s, 0.16 * s, 0.7 * s, shade(col, 0.75), **kw)      # cap brim
    blk(x, hy + 1.55 * s, z - 0.76 * s, 0.5 * s, 0.3 * s, 0.05 * s, WHITE, **kw)             # badge


def prop_basket(x, z):
    for bx, w, h, ec in ((-3.4, 3.6, 2.2, (90, 190, 250)), (1.8, 5, 3, (255, 120, 190))):
        d, y = 3.2, 5.2
        blk(x + bx, y, z, w, h, d, (224, 172, 96), 'Plastic')
        for k in (0.2, 0.6):                                                   # weave bands
            blk(x + bx, y + h * k, z, w + 0.12, h * 0.16, d + 0.12, (186, 130, 62), **NC)
        blk(x + bx, y + h, z, w + 0.5, 0.45, d + 0.5, (150, 100, 50))          # rim
        for sx in (-1, 1):                                                     # handle
            blk(x + bx + sx * w / 2, y + h, z, 0.4, 2.6, 0.4, (150, 100, 50), **NC)
        blk(x + bx, y + h + 2.6, z, w + 0.4, 0.4, 0.4, (150, 100, 50), **NC)
        egg(x + bx - w * 0.2, y + h + 0.6, z, 0.55, ec, WHITE, name='Decor')
        egg(x + bx + w * 0.22, y + h + 0.4, z, 0.5, GOLD, WHITE, name='Decor')


def prop_clover(x, z):
    for dx, dy in ((-1.6, 0), (1.6, 0), (0, 1.6), (0, -1.6)):
        blk(x + dx, 7.4 + dy, z, 2.8, 2.8, 1, (70, 210, 90), **NC)
    blk(x, 5.2, z, 0.6, 2.4, 0.6, (50, 150, 60), **NC)
    blk(x + 4.6, 5.2, z, 3, 3, 3, WHITE, yaw=20)
    blk(x - 4.6, 5.2, z, 3, 3, 3, (255, 80, 80), yaw=-25)


def prop_coins(x, z):
    for k in range(5):
        vcyl(x - 5 + k * 2.5, 5.2, z, 0.6 + 0.6 * (k % 3), 2.4, GOLD, 'Foil')
    blk(x + 4.5, 5.2, z, 3.4, 2.6, 2.6, (60, 190, 90))


def prop_book(x, z):
    blk(x, 5.2, z, 6, 1.2, 4.4, (90, 110, 240), yaw=12)
    blk(x, 6.4, z, 5.4, 0.8, 4, CREAM, yaw=12)
    egg(x - 4.8, 6.6, z, 0.9, (160, 100, 250), GOLD)
    egg(x + 4.8, 6.6, z, 0.9, (60, 200, 230), WHITE)


def home():
    G, G2 = (118, 204, 84), (102, 188, 72)
    with group('Ground', unique=False):
        blk(0, -4, -64, HALF * 2 + 48, 4, 128, G, 'Plastic')
        blk(0, -13, -64, HALF * 2 + 40, 9, 126, DIRT, 'Slate')
        patches(-58, 0, G2, 26)
        blk(0, 0, -49, HALF * 2 - 8, 0.3, 18, (240, 228, 196))          # promenade in front of the bases
        blk(0, 0, -29, ROADW, 0.3, 58, (240, 228, 196))
        vcyl(0, 0, -30, 0.35, 46, (232, 216, 178))
        vcyl(0, 0.35, -30, 0.1, 38, (246, 236, 208), **NC)
        wall_run(-128, 0, G, (150, 106, 70))
        tiles(-126, 0, G, par=1)
        DW = (150, 106, 70)                                                # back wall: same dirt checker + grass cap
        for k, x in enumerate(range(-HALF - 24, HALF + 24, 20)):
            for row in range(2):
                blk(x + 10, -4 + row * 17, -138, 20, 17, 24, DW if (k + row) % 2 == 0 else shade(DW, 1.13), 'Plastic')
            blk(x + 10, 30, -137, 20, 4, 26, G, 'Plastic')
            for q in range(2):
                ex = 0   # v107 (user: 'why is it not uniform'): one even grass band, no up-and-down steps
                blk(x + 5 + q * 10, 27 - ex, -125.3, 10, 3 + ex, 1.6, G, 'Plastic', **NC)
            if k % 3 == 1:
                tree(x + 10, -138, 1.4)
        blk(0, 0, -125, HALF * 2 + 48, 120, 2, WHITE, transparency=1, name='Wall')
    for i in range(8):
        base(i)
    with group('Plaza', unique=False):
        sp = blk(0, 0.35, -44, 12, 0.6, 12, (255, 255, 255), 'Neon', spawn=True)
        blk(0, 0.3, -44, 15, 0.3, 15, GOLD)
        # cracked giant egg statue
        vcyl(0, 0.4, -22, 2.4, 18, (214, 220, 236), 'Marble')
        vcyl(0, 2.8, -22, 1.2, 14, WHITE, 'Marble')
        egg(0, 10.4, -22, 5, CREAM, (255, 120, 190), n=9)
        stall(-52, -16, 'BASKETS', 'catch more eggs', (255, 150, 40), prop_basket)
        stall(52, -16, 'LUCK SHOP', 'better eggs fall on you', (70, 200, 90), prop_clover)
        stall(-96, -16, 'SELL', 'pets and eggs for cash', (255, 204, 40), prop_coins)
        stall(96, -16, 'INDEX', 'every pet you found', (120, 110, 250), prop_book)
        for x, t, s, c in ((-140, 'TOP LUCK', 'rarest hatch today', (160, 100, 250)), (140, 'TOP CATCHERS', 'most eggs caught', (60, 190, 230))):
            key = 'Luck' if x < 0 else 'Catch'
            bn = 'Map_LuckBoard2' if x < 0 else 'Map_CatchBoard'
            if has_mesh(bn, bn.replace('Board', 'BoardNeon')):
                # Blender wall panel (blender\gen_luckboard.py) against the plaza side wall: TOP LUCK left, TOP CATCHERS right,
                # facing into the plaza; the game's screen sits in the gold frame
                sx = -1 if x < 0 else 1
                wx, wz, yaw = sx * (HALF - 1.9), -49, 90 * sx          # in line with the paved promenade (z -49); R() yaw: +90 = front to +X on the right... (checked in Studio: -90*sx showed the back)
                mpart(bn, wx, 0, wz, yaw)
                mpart(bn.replace('Board', 'BoardNeon'), wx, 0, wz, yaw, mat='Neon')
                blk(wx, 0, wz, 32, 21, 3.4, INK, yaw=yaw, transparency=1)              # what players bump into
                b = blk(wx - sx * 1.15, 10.6 - 6.5, wz, 20, 13, 0.3, INK, yaw=yaw, name='Leaderboard', **NC)
                sign(b, 'Front', t, s, bg1=shade(c, 1.05), bg2=shade(c, 0.6), pps=16)
                continue
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
        z0, zc = zone_base(i, G, 'Grass', (238, 222, 180), (150, 106, 70))
        patches(z0, z0 + ZL, G2)
        for _ in range(22):
            tree(side_x(18, 160), rng.uniform(z0 + 8, z0 + ZL - 8), rng.uniform(0.8, 1.5), rng.choice(((74, 176, 70), (96, 196, 70), (60, 160, 80))))
        for _ in range(80):
            flower(side_x(12, 164), rng.uniform(z0 + 4, z0 + ZL - 4), rng.choice(((255, 90, 90), (255, 214, 50), WHITE, (255, 120, 190), (130, 120, 255))))
        BL = has_mesh('Map_HayBale', 'Map_Windmill', 'Map_WindmillBlades', 'Map_Barn', 'Map_Pond', 'Map_PondWater', 'Map_FenceWhite')
        for _ in range(9):                                   # hay bales
            x, z = side_x(20, 150), rng.uniform(z0 + 10, z0 + ZL - 10)
            yaw = rng.uniform(0, 180)
            if BL:
                mpart('Map_HayBale', x, 0, z, yaw)
                part((5, 5, 5), C(x, 2.5, z) * R(0, yaw, 0), (240, 204, 90), 'Sand', transparency=1)
            else:
                part((5, 5, 5), C(x, 2.5, z) * R(0, yaw, 0), (240, 204, 90), 'Sand', 'Cylinder')
        if BL:                                               # Blender pond, windmill (blades turn in the client), barn, fence
            px, pz = -88, z0 + 52
            mpart('Map_Pond', px, 0, pz)
            mpart('Map_PondWater', px, 0, pz, transparency=0.25, reflectance=0.15)
            blk(px + 18.8, 0, pz, 11.4, 1.17, 4.6, WOOD, transparency=1)                  # the dock you can walk on
            wx, wz = 92, z0 + 70
            mpart('Map_Windmill', wx, 0, wz)
            mpart('Map_WindmillBlades', wx, 0, wz, pname='WindmillBlades')
            blk(wx, 0, wz, 15, 34, 15, CREAM, transparency=1)
            bx, bz = -120, z0 + 108
            mpart('Map_Barn', bx, 0, bz)
            blk(bx, 0, bz, 31, 15, 23, RED, transparency=1)
            blk(bx, 15, bz, 22, 10, 22, RED, transparency=1)
            for x in range(-147, -84, 6):
                mpart('Map_FenceWhite', x, 0, z0 + 90)
            blk(-117, 0, z0 + 90, 66, 4, 0.8, WHITE, transparency=1)
        # pond
        if BL:
            pass
        else:
            meadow_blocks(z0)
        for _ in range(8):
            rock(side_x(20, 160), rng.uniform(z0 + 6, z0 + ZL - 6), rng.uniform(0.8, 1.6), (150, 154, 170))
        egg_sky(z0, WHITE, [(CREAM, (150, 200, 120)), (CREAM, BROWN), ((180, 230, 150), WHITE)])


def meadow_blocks(z0):
    if True:
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


# ------------------------------------------------------------------ zone 2: Mushroom Grove
MUSH_CAPS = [(232, 60, 70), (255, 140, 40), (236, 80, 190), (70, 190, 220)]


def mushroom(x, z, h, d, cap, dots=WHITE, glow=False):
    yaw = (x * 37 + z * 11) % 360
    if glow and has_mesh('Map_GlowMush', 'Map_GlowMushNeon'):
        mpart('Map_GlowMush', x, 0, z, yaw, d / 3)
        mpart('Map_GlowMushNeon', x, 0, z, yaw, d / 3, 'Neon')
        return
    if not glow and cap in MUSH_CAPS and has_mesh('Map_MushStem', 'Map_MushCap1', 'Map_MushCap2', 'Map_MushCap3', 'Map_MushCap4'):
        mpart('Map_MushStem', x, 0, z, yaw, sv=(d / 10, h / 10, d / 10))
        mpart(f'Map_MushCap{MUSH_CAPS.index(cap) + 1}', x, h, z, yaw, d / 10)
        blk(x, 0, z, d * 0.3, h, d * 0.3, CREAM, transparency=1)
        blk(x, h, z, d, d * 0.2, d, cap, name='Bounce', transparency=1)        # the cap still bounces you
        blk(x, h + d * 0.2, z, d * 0.6, d * 0.12, d * 0.6, cap, transparency=1)
        return
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
        BL = has_mesh('Map_MushHouse', 'Map_MushHouseNeon', 'Map_Log', 'Map_Spore1', 'Map_Spore2')
        if BL:
            hx, hz = 96, z0 + 76
            mpart('Map_MushHouse', hx, 0, hz)
            mpart('Map_MushHouseNeon', hx, 0, hz, mat='Neon')
            blk(hx, 0, hz, 22, 30, 22, CREAM, transparency=1)
            blk(hx, 30, hz, 62, 6, 62, (232, 60, 70), name='Bounce', transparency=1)
            blk(hx, 36, hz, 46, 7, 46, (232, 60, 70), transparency=1)
            blk(hx, 43, hz, 28, 4, 28, (232, 60, 70), transparency=1)
            for sx in (-1, 1):
                light(blk(hx + sx * 6.4, 6.6, hz - 14.4, 1, 1.6, 1, WHITE, transparency=1, **NC), (255, 220, 120), 18, 1.2)
            for _ in range(7):
                x, z = side_x(20, 150), rng.uniform(z0 + 10, z0 + ZL - 10)
                L, yaw = rng.uniform(10, 18), rng.uniform(0, 180)
                mpart('Map_Log', x, 0, z, yaw, sv=(L / 14, 1, 1))
                part((L, 3.4, 3.4), C(x, 1.7, z) * R(0, yaw, 0), DBROWN, 'Wood', transparency=1)
            for _ in range(34):
                x, y, z, d = rng.uniform(-160, 160), rng.uniform(6, 40), rng.uniform(z0 + 4, z0 + ZL - 4), rng.uniform(0.5, 1.1)
                c = rng.choice(((140, 255, 240), (220, 170, 255)))
                mpart('Map_Spore1' if c[0] < 200 else 'Map_Spore2', x, y, z, 0, d, 'Neon')
            egg_sky(z0, (214, 196, 250), [((190, 130, 255), WHITE), ((232, 60, 70), WHITE), ((90, 240, 230), (98, 84, 170))])
            return
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
CANDY_CS = [(255, 90, 120), (120, 200, 255), (255, 214, 60), (150, 230, 120), (190, 130, 255), (255, 150, 50)]


def lollipop(x, z, h, d, c1, c2):
    if c1 in CANDY_CS and has_mesh('Map_LolliStick', 'Map_LolliTop1'):
        mpart('Map_LolliStick', x, 0, z, sv=(1, h / 10, 1))
        mpart(f'Map_LolliTop{CANDY_CS.index(c1) + 1}', x, h + d / 2 - 1, z, 90, d / 10)
        blk(x, 0, z, 0.9, h, 0.9, WHITE, transparency=1)
        part((1.6, d * 0.9, d * 0.9), C(x, h + d / 2 - 1, z) * R(0, 90, 0), c1, transparency=1)
        return
    vcyl(x, 0, z, h, 0.9, WHITE)
    for k, (dd, t, c) in enumerate(((d, 1.6, c1), (d * 0.68, 2.0, c2), (d * 0.36, 2.4, c1), (d * 0.12, 2.8, c2))):
        part((t, dd, dd), C(x, h + d / 2 - 1, z) * R(0, 90, 0), c, 'SmoothPlastic', 'Cylinder')


def candy_cane(x, z, n, yaw=0):
    if has_mesh('Map_CandyCane'):
        mpart('Map_CandyCane', x, 0, z, yaw, n / 6)
        part((2.1, n * 2 + 2, 2.1), C(x, (n * 2 + 2) / 2, z), WHITE, transparency=1)
        return
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
        if has_mesh('Map_ChocoRiver', 'Map_WaferBridge', 'Map_Gumdrop1', 'Map_IceCream1', 'Map_Cake', 'Map_CakeNeon'):
            return candy_mesh(z0, rz_, cs)
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


def candy_mesh(z0, rz_, cs):
    """Candy Canyon with the Blender meshes (same dice order as the block version, so the layout stays the same)"""
    for sx in (-1, 1):
        mpart('Map_ChocoRiver', sx * 96, 0, rz_)
    mpart('Map_WaferBridge', 0, 0, rz_)
    blk(0, 0, rz_, ROADW + 4, 1.6, 24, (240, 200, 130), transparency=1)
    for sx in (-1, 1):
        blk(sx * (ROADW / 2 + 1.5), 1.6, rz_, 1, 3, 24, (255, 120, 150), transparency=1)
    for _ in range(20):
        c1, c2 = rng.sample(cs, 2)
        lollipop(side_x(18, 160), rng.choice((rng.uniform(z0 + 8, rz_ - 16), rng.uniform(rz_ + 16, z0 + ZL - 8))), rng.uniform(9, 20), rng.uniform(8, 15), c1, c2)
    for _ in range(12):
        candy_cane(side_x(18, 160), rng.choice((rng.uniform(z0 + 8, rz_ - 16), rng.uniform(rz_ + 16, z0 + ZL - 8))), rng.randint(4, 9), rng.choice((0, 90, 180, 270)))
    for _ in range(40):                                   # gumdrops
        d = rng.uniform(2.4, 6)
        x = side_x(12, 164)
        z = rng.choice((rng.uniform(z0 + 4, rz_ - 14), rng.uniform(rz_ + 14, z0 + ZL - 4)))
        c = rng.choice(cs)
        mpart(f'Map_Gumdrop{cs.index(c) + 1}', x, 0, z, (x * 13) % 360, d / 4)
        blk(x, 0, z, d * 0.8, d * 0.6, d * 0.8, c, transparency=1)
    for _ in range(9):                                    # ice cream cones
        x, z = side_x(22, 150), rng.choice((rng.uniform(z0 + 10, rz_ - 18), rng.uniform(rz_ + 18, z0 + ZL - 10)))
        cols = rng.sample(cs, 3)
        mpart(f'Map_IceCream{cs.index(cols[0]) % 3 + 1}', x, 0, z, (z * 7) % 360)
        blk(x, 0, z, 5, 20, 5, cols[0], transparency=1)
    cx, cz = -98, z0 + 110                                 # giant cake
    for _ in range(30):
        rng.choice(cs)
    mpart('Map_Cake', cx, 0, cz)
    mpart('Map_CakeNeon', cx, 0, cz, mat='Neon')
    for k, d in enumerate((40, 30, 21)):
        blk(cx, k * 9, cz, d, 9, d, (255, 240, 230), transparency=1)
    for a in range(0, 360, 60):
        light(blk(cx + 8 * math.cos(math.radians(a)), 32.6, cz + 8 * math.sin(math.radians(a)), 1, 1, 1, WHITE, transparency=1, **NC), (255, 200, 90), 12, 1)
    egg_sky(z0, (255, 226, 240), [((255, 150, 180), WHITE), ((120, 200, 255), (255, 214, 60)), ((255, 214, 60), (255, 90, 120))])


# ------------------------------------------------------------------ zone 4: Crystal Coast
CRYSTAL_CS = [(80, 230, 255), (190, 120, 255), (255, 110, 210), (110, 255, 200)]


def crystal(x, z, h, col, big=True):
    if col in CRYSTAL_CS and has_mesh('Map_Crystal1', 'Map_CrystalCluster1'):
        rng.uniform(-14, 14)
        yaw = rng.uniform(0, 90)
        rng.uniform(-14, 14)
        k = CRYSTAL_CS.index(col) + 1
        if big:
            for _ in range(rng.randint(2, 4)):            # same dice count as the block crystal
                for _ in range(6):
                    rng.random()
            mpart(f'Map_CrystalCluster{k}', x, 0, z, yaw * 4, h / 20, transparency=0.08, reflectance=0.25)
            blk(x, 0, z, h * 0.3, h * 0.9, h * 0.3, col, transparency=1)
        else:
            mpart(f'Map_Crystal{k}', x, 0, z, yaw * 4, h / 4, transparency=0.08, reflectance=0.25)
        return
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
    if has_mesh('Map_Palm'):
        mpart('Map_Palm', x, 0, z, (lean + 0.5) * 360, h / 18)
        blk(x, 0, z, 2.2, h, 2.2, (176, 132, 84), transparency=1)
        return
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
        BL = has_mesh('Map_TidePool', 'Map_TidePoolWater', 'Map_Lighthouse', 'Map_LighthouseNeon', 'Map_Throne', 'Map_Starfish', 'Map_Shell1', 'Map_Shell2')
        for (px, pz, w, d) in ((-104, z0 + 40, 70, 44), (88, z0 + 96, 80, 50), (112, z0 + 30, 44, 30), (-70, z0 + 112, 50, 30)):
            if BL:
                mpart('Map_TidePool', px, 0, pz, sv=(w / 60, 1, d / 40))
                mpart('Map_TidePoolWater', px, 0, pz, sv=(w / 60, 1, d / 40), transparency=0.25, reflectance=0.2)
                continue
            blk(px, 0, pz, w, 0.25, d, (120, 226, 230), 'Glass', transparency=0.2, **NC)
            blk(px, 0.05, pz, w - 8, 0.3, d - 8, (70, 200, 230), 'Glass', transparency=0.2, **NC)
        for _ in range(26):
            crystal(side_x(18, 160), rng.uniform(z0 + 8, z0 + ZL - 8), rng.uniform(8, 30), rng.choice(cs))
        for _ in range(40):
            crystal(side_x(12, 164), rng.uniform(z0 + 4, z0 + ZL - 4), rng.uniform(2, 5), rng.choice(cs), big=False)
        for _ in range(16):
            palm(side_x(18, 160), rng.uniform(z0 + 8, z0 + ZL - 8), rng.choice((15, 18, 21)))
        if BL:
            return crystal_mesh_rest(z0, cs)
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


def crystal_mesh_rest(z0, cs):
    """Crystal Coast: lighthouse, crystal throne, shells with the Blender meshes (same dice order)"""
    lx, lz = -124, z0 + 78
    mpart('Map_Lighthouse', lx, 0, lz)
    mpart('Map_LighthouseNeon', lx, 0, lz, mat='Neon')
    blk(lx, 0, lz, 26, 3, 26, (150, 154, 170), transparency=1)
    blk(lx, 3, lz, 14, 43, 14, WHITE, transparency=1)
    light(blk(lx, 46, lz, 7, 6, 7, WHITE, transparency=1, **NC), (255, 240, 170), 60, 3)
    for k in range(9):                                    # crystal throne cluster
        a = k * 40
        crystal(104 + 12 * math.cos(math.radians(a)), z0 + 64 + 12 * math.sin(math.radians(a)), rng.uniform(20, 44), cs[k % 4])
    mpart('Map_Throne', 104, 0, z0 + 64, 180)
    blk(104, 0, z0 + 64, 8, 9, 8, (160, 120, 255), transparency=1)
    SHELL = {(255, 150, 120): 'Map_Starfish', (255, 240, 230): 'Map_Shell1', (255, 190, 90): 'Map_Shell2'}
    for _ in range(18):                                   # shells / starfish
        x, z = side_x(12, 164), rng.uniform(z0 + 4, z0 + ZL - 4)
        c, yaw = rng.choice(((255, 150, 120), (255, 240, 230), (255, 190, 90))), rng.uniform(0, 90)
        mpart(SHELL[c], x, 0, z, yaw * 4, 1.4)
    egg_sky(z0, (232, 248, 255), [((80, 230, 255), WHITE), ((190, 120, 255), (80, 230, 255)), ((255, 110, 210), WHITE)])


# ------------------------------------------------------------------ zone 5: Thunder Peaks
def peak(x, z, base, h, col):
    if has_mesh('Map_Peak1', 'Map_Peak2', 'Map_PeakNeon1', 'Map_PeakNeon2'):
        for _ in range(6):                                # same dice use as the block peak
            rng.uniform(0.8, 1.1)
            rng.choice((0, 0, 12, -12))
            rng.uniform(-0.06, 0.06)
            rng.uniform(-0.06, 0.06)
        k = int(abs(x)) % 2 + 1
        sv, yaw = (base / 30, h / 40, base / 30), (z * 7) % 360
        mpart(f'Map_Peak{k}', x, 0, z, yaw, sv=sv)
        mpart(f'Map_PeakNeon{k}', x, 0, z, yaw, 'Neon', sv=sv)
        blk(x, 0, z, base * 0.75, h * 0.45, base * 0.75, col, transparency=1)
        blk(x, h * 0.45, z, base * 0.4, h * 0.35, base * 0.4, col, transparency=1)
        return
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
            if has_mesh('Map_LightningRod', 'Map_RodOrb'):
                mpart('Map_LightningRod', x, 0, z, (x * 3) % 90, sv=(1, (h + 2) / 30, 1))
                light(mpart('Map_RodOrb', x, h + 3, z, 0, 1, 'Neon'), (255, 230, 90), 26, 2)
                blk(x, 0, z, 2.4, h + 2, 2.4, (190, 196, 214), transparency=1)
                continue
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
        if has_mesh('Map_TeslaTower', 'Map_TeslaTowerNeon'):
            mpart('Map_TeslaTower', tx, 0, tz)
            t = mpart('Map_TeslaTowerNeon', tx, 0, tz, mat='Neon')
            light(t, (255, 236, 110), 60, 4)
            blk(tx, 0, tz, 22, 4, 22, (60, 64, 84), transparency=1)
            blk(tx, 4, tz, 10, 54, 10, (96, 102, 130), transparency=1)
        else:
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
    if has_mesh('Map_Rainbow'):
        mpart('Map_Rainbow', xc, 0, z, 0, radius / 74, pname='Rainbow')
        return
    n = 26
    for bi, col in enumerate(RAINBOW):
        r = radius - bi * bw
        seg = math.pi * r / n * 1.06
        for k in range(n):
            a = (k + 0.5) * 180 / n
            part((seg, bw, depth), C(xc + r * math.cos(math.radians(a)), r * math.sin(math.radians(a)) - 2, z) * R(0, 0, a + 90), col, name='Rainbow', **NC)


def puff(x, z, s):
    if has_mesh('Map_Puff1', 'Map_Puff2'):
        mpart('Map_Puff1' if int(abs(x)) % 2 else 'Map_Puff2', x, 0, z, (z * 5) % 360, s)
        blk(x, 0, z, 12 * s, 4.5 * s, 10 * s, WHITE, transparency=1)
        return
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
            if has_mesh('Map_Pillar', 'Map_PillarOrb'):
                mpart('Map_Pillar', x, 0, z, 0, sv=(1, (h + 3) / 22.6, 1))
                light(mpart('Map_PillarOrb', x, h + 5, z, 0, 1, 'Neon'), (255, 236, 150), 18, 1.2)
                blk(x, 0, z, 3.6, h + 3, 3.6, WHITE, transparency=1)
                continue
            vcyl(x, 0, z, 1.6, 6, GOLD, 'Foil')
            vcyl(x, 1.6, z, h, 3.6, WHITE, 'Marble')
            vcyl(x, h + 1.6, z, 1.4, 6, GOLD, 'Foil')
            s = sph(x, h + 5, z, 2.4, (255, 240, 130), 'Neon', **NC)
            light(s, (255, 236, 150), 18, 1.2)
        # sky castle
        cx, cz = -110, z0 + 72
        if has_mesh('Map_SkyCastle', 'Map_CloudStep', 'Map_Star'):
            mpart('Map_SkyCastle', cx, 0, cz)
            blk(cx, 0, cz, 46, 16, 30, WHITE, transparency=1)
            for tx, th in ((-23, 34), (23, 34), (0, 46)):
                blk(cx + tx, 0, cz + (6 if tx == 0 else -6), 12, th, 12, WHITE, transparency=1)
            for _ in range(9):                                # floating cloud steps
                x, z, y = side_x(24, 150), rng.uniform(z0 + 10, z0 + ZL - 10), rng.uniform(14, 40)
                w, d = rng.uniform(10, 18), rng.uniform(8, 14)
                mpart('Map_CloudStep', x, y + 1.5, z, 0, sv=(w / 14, 1.2, d / 11))
                blk(x, y, z, w, 3, d, WHITE, name='CloudStep', transparency=1)
            for _ in range(26):                               # stars
                mpart('Map_Star', rng.uniform(-160, 160), rng.uniform(20, 70), rng.uniform(z0 + 4, z0 + ZL - 4), 0, 1.0, 'Neon')
            egg_sky(z0, WHITE, [(WHITE, (255, 150, 200)), ((255, 222, 50), WHITE), ((150, 200, 255), (255, 240, 130))])
            return
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
        if has_mesh('Map_GoldenNest', 'Map_GoldenEgg', 'Map_TreeGold', 'Map_Treasure1', 'Map_Pedestal'):
            return golden_mesh(z0, nx, nz, G)
        vcyl(nx, 0, nz, 0.5, 100, (236, 180, 60), **NC)
        for ring, (r, y, n) in enumerate(((44, 2, 30), (47, 5.6, 30), (45, 9.2, 28), (48, 12.6, 26))):   # twig nest ring, open at the front
            for k in range(n):
                a = k * 360 / n + ring * 7
                if 250 < a % 360 < 290:
                    continue
                part((rng.uniform(15, 22), 3.6, 3.6), C(nx + r * math.cos(math.radians(a)), y, nz + r * math.sin(math.radians(a))) *
                     R(0, -(a + 90) + rng.uniform(-22, 22), rng.uniform(-10, 10)), rng.choice((BROWN, DBROWN, (150, 104, 60))), 'Wood', 'Cylinder')
        egg(nx, 26, nz, 17, GOLD, (255, 246, 190), mat='Foil', n=9)
        b = vcyl(nx, 70, nz, 400, 12, (255, 240, 150), 'Neon', transparency=0.7, **NC)
        light(b, (255, 230, 120), 60, 3)
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


def golden_mesh(z0, nx, nz, G):
    """Golden Nest with the Blender meshes (same dice order as the block version)"""
    INV = dict(transparency=1)
    mpart('Map_GoldenNest', nx, 0, nz)
    for ring, (r, y, n) in enumerate(((44, 2, 30), (47, 5.6, 30), (45, 9.2, 28), (48, 12.6, 26))):   # collision ring, open at the front
        for k in range(n):
            a = k * 360 / n + ring * 7
            if 250 < a % 360 < 290:
                continue
            ln = rng.uniform(15, 22)
            yaw = -(a + 90) + rng.uniform(-22, 22)
            rng.uniform(-10, 10)
            rng.choice((BROWN, DBROWN, (150, 104, 60)))
            part((ln, 3.6, 3.6), C(nx + r * math.cos(math.radians(a)), y, nz + r * math.sin(math.radians(a))) * R(0, yaw, 0), BROWN, **INV)
    mpart('Map_GoldenEgg', nx, 33.5, nz, 0, 6.6, reflectance=0.3, pname='GoldenEgg')
    blk(nx, 0, nz, 40, 64, 40, GOLD, name='GoldenEggBlock', **INV)
    b = vcyl(nx, 70, nz, 400, 12, (255, 240, 150), 'Neon', transparency=0.7, name='GoldenBeam', **NC)
    light(b, (255, 230, 120), 60, 3)
    for _ in range(20):                                   # golden trees
        x, z, s = side_x(60, 160), rng.uniform(z0 + 8, z0 + ZL - 8), rng.uniform(0.9, 1.6)
        r = type(rng)(int(x * 7 + z * 13))
        s *= r.uniform(0.9, 1.15)
        mpart('Map_TreeGold', x, 0, z, r.uniform(0, 360), s)
        blk(x, 0, z, 2 * s, 9 * s, 2 * s, (250, 240, 220), **INV)
    GEMS = ((240, 60, 90), (70, 200, 255), (120, 240, 140), (190, 110, 255))
    for _ in range(16):                                   # treasure piles
        x, z = side_x(16, 160), rng.uniform(z0 + 6, z0 + 44)
        for k in range(rng.randint(4, 9)):
            rng.uniform(-3, 3)
            rng.choice((0, 0, 1.6))
            rng.uniform(-3, 3)
            rng.uniform(0, 90)
        c = rng.choice(GEMS)
        mpart(f'Map_Treasure{GEMS.index(c) + 1}', x, 0, z, (x * 9) % 360, 1.1)
        blk(x, 0, z, 5, 2.4, 5, GOLD, **INV)
    # v111: 10 altars, one per zone (5 each side, zone 1 nearest the middle on the left). Players put one egg of each
    # zone on its altar; with all 10 the giant golden egg sinks into the ground and a portal opens (game script).
    for n in range(1, 11):
        sx, k = (-1 if n <= 5 else 1), (n - 1) % 5
        x, z = sx * (62 + k * 22), z0 + 58
        mpart('Map_Pedestal', x, 0, z, pname=f'AltarMesh{n}')
        blk(x, 0, z, 9, 7, 9, WHITE, name=f'EggAltar{n}', **INV)
    ez = z0 + ZL + 12                                     # end wall with a rising sun
    for x in range(-HALF - 24, HALF + 25, 24):
        h = rng.choice((40, 52, 64, 76))
        blk(x + 12, -4, ez, 24, h + 4, 24, (190, 130, 40), 'Slate')
        blk(x + 12, h, ez, 24, 2, 24, G)
    vcyl(0, 0, 0, 0.1, 0.1, G, **NC)
    part((4, 150, 150), C(0, 70, ez + 16) * R(0, 90, 0), (255, 226, 90), 'Neon', 'Cylinder', name='Sun', **NC)
    blk(0, 0, z0 + ZL + 1, HALF * 2 + 48, 120, 2, WHITE, transparency=1, name='Wall')
    egg_sky(z0, (255, 244, 200), [(GOLD, WHITE), ((255, 240, 150), GOLD), (RAINBOW[5], GOLD)])


# ------------------------------------------------------------------ zone: Toy Town
TOY =[(240, 70, 70), (255, 204, 40), (70, 190, 90), (70, 130, 250), (255, 140, 40), (190, 100, 250)]


def z_toy(i):
    G = (130, 200, 255)
    with group(f'Zone{i + 1}_ToyTown', unique=False):
        z0, zc = zone_base(i, G, 'SmoothPlastic', (255, 250, 236), (240, 90, 80), (70, 120, 220))
        for _ in range(60):                                   # play-mat tiles
            blk(side_x(14, 162), 0, rng.uniform(z0 + 8, z0 + ZL - 8), 10, 0.14, 10, rng.choice(TOY), **NC)
        if has_mesh('Map_ToyBlock1', 'Map_Dice', 'Map_StackRings', 'Map_Crayon1', 'Map_Ball1', 'Map_TrainTrack', 'Map_TrainEngine',
                    'Map_TrainCar1', 'Map_Teddy', 'Map_DuckTub', 'Map_DuckTubWater'):
            return toy_mesh(z0, G)
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


def toy_mesh(z0, G):
    """Toy Town with the Blender meshes (same dice order as the block version)"""
    INV = dict(transparency=1)
    for _ in range(16):                                   # towers of toy blocks
        x, z = side_x(20, 156), rng.uniform(z0 + 10, z0 + ZL - 10)
        y = 0
        for k in range(rng.randint(1, 4)):
            s = rng.choice((8, 10, 12)) - k
            bx, bz, c, yaw = x + rng.uniform(-1.5, 1.5), z + rng.uniform(-1.5, 1.5), rng.choice(TOY), rng.choice((0, 15, -20, 30))
            mpart(f'Map_ToyBlock{TOY.index(c) + 1}', bx, y, bz, yaw, s / 10)
            blk(bx, y, bz, s, s, s, c, yaw=yaw, **INV)
            y += s
    for _ in range(8):                                    # dice
        x, z, s = side_x(20, 156), rng.uniform(z0 + 10, z0 + ZL - 10), rng.choice((7, 9))
        mpart('Map_Dice', x, 0, z, (x * 7) % 90, s / 7)
        blk(x, 0, z, s, s, s, WHITE, **INV)
    for _ in range(9):                                    # stacking rings
        x, z = side_x(20, 156), rng.uniform(z0 + 10, z0 + ZL - 10)
        mpart('Map_StackRings', x, 0, z, (z * 11) % 360)
        blk(x, 0, z, 9, 14, 9, CREAM, **INV)
    for _ in range(12):                                   # crayons
        x, z, h, c = side_x(16, 160), rng.uniform(z0 + 8, z0 + ZL - 8), rng.uniform(12, 20), rng.choice(TOY)
        mpart(f'Map_Crayon{TOY.index(c) + 1}', x, 0, z, (x * 5) % 60, sv=(1, (h + 3.2) / 15.4, 1))
        blk(x, 0, z, 3, h + 3, 3, c, **INV)
    for _ in range(18):                                   # bouncy balls
        d = rng.uniform(3, 7)
        x, z, c = side_x(14, 162), rng.uniform(z0 + 6, z0 + ZL - 6), rng.choice(TOY)
        mpart(f'Map_Ball{TOY.index(c) + 1}', x, d / 2, z, (z * 9) % 360, d)
        blk(x, d * 0.1, z, d * 0.8, d * 0.8, d * 0.8, c, name='Bounce', **INV)
    tx, tz = 98, z0 + 72                                  # toy train on a round track
    mpart('Map_TrainTrack', tx, 0, tz)
    for k in range(5):
        a = math.radians(200 + k * 24)
        x, z = tx + 33 * math.cos(a), tz + 33 * math.sin(a)
        mpart('Map_TrainEngine' if k == 0 else f'Map_TrainCar{k}', x, 0, z, -math.degrees(a))
        part((8, 6, 13), C(x, 0, z) * R(0, -math.degrees(a), 0) * C(0, 4.4, 0), TOY[k % 6], name='Train', **INV)
    bx, bz = -106, z0 + 80                                # giant teddy bear
    mpart('Map_Teddy', bx, 0, bz)
    blk(bx, 0, bz, 26, 28, 26, (176, 120, 70), **INV)
    blk(bx, 28, bz, 18, 16, 18, (176, 120, 70), **INV)
    dx, dz = -70, z0 + 28                                 # rubber duck in a tub
    mpart('Map_DuckTub', dx, 0, dz)
    mpart('Map_DuckTubWater', dx, 0, dz, transparency=0.3, reflectance=0.1)
    blk(dx, 0, dz, 34, 5, 24, WHITE, **INV)
    blk(dx, 5, dz, 12, 14, 12, (255, 220, 50), **INV)
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
        if has_mesh('Map_DeadTree1', 'Map_DeadTree2', 'Map_Pumpkin', 'Map_PumpkinLit', 'Map_PumpkinLitNeon', 'Map_Tomb1', 'Map_GraveFence',
                    'Map_HauntedHouse', 'Map_HauntedHouseNeon', 'Map_Ghost', 'Map_SpookyLantern', 'Map_SpookyLanternNeon'):
            return spooky_mesh(z0)
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


def spooky_mesh(z0):
    """Spooky Hollow with the Blender meshes (same dice order as the block version)"""
    INV = dict(transparency=1)
    for _ in range(26):                                   # dead trees
        x, z, h = side_x(18, 160), rng.uniform(z0 + 8, z0 + ZL - 8), rng.uniform(12, 24)
        for _ in range(16):
            rng.random()
        mpart('Map_DeadTree1' if int(abs(x)) % 2 else 'Map_DeadTree2', x, 0, z, (z * 13) % 360, h / 18)
        blk(x, 0, z, 2.6, h, 2.6, (56, 44, 52), **INV)
    for k in range(34):                                   # pumpkins (every third one is a lit jack-o-lantern)
        x, z, d = side_x(13, 162), rng.uniform(z0 + 5, z0 + ZL - 5), rng.uniform(2.6, 7)
        if k % 3 == 0:
            mpart('Map_PumpkinLit', x, 0, z, 0, d / 5)
            mpart('Map_PumpkinLitNeon', x, 0, z, 0, d / 5, 'Neon')
            light(blk(x, d * 0.4, z - d * 0.3, 0.5, 0.5, 0.5, WHITE, **INV, **NC), (255, 170, 60), d * 3, 1.5)
        else:
            mpart('Map_Pumpkin', x, 0, z, (x * 17) % 360, d / 5)
        blk(x, 0, z, d * 0.8, d * 0.8, d * 0.8, (255, 132, 30), **INV)
    for gx, gz in ((96, z0 + 36), (-60, z0 + 104)):       # graveyards
        for k in range(14):
            x, z = gx + (k % 5) * 7 - 14, gz + (k // 5) * 8
            yaw = rng.uniform(-10, 10)
            mpart(f'Map_Tomb{k % 3 + 1}', x, 0, z, yaw)
            blk(x, 0, z, 3.4, 5.4, 1.2, (150, 154, 168), yaw=yaw, **INV)
        mpart('Map_GraveFence', gx, 0, gz - 6)
        blk(gx, 0, gz - 6, 43, 5, 0.6, INK, **INV)
    hx, hz = -104, z0 + 52                                # haunted house
    mpart('Map_HauntedHouse', hx, 0, hz)
    mpart('Map_HauntedHouseNeon', hx, 0, hz, mat='Neon')
    blk(hx, 0, hz, 34, 22, 26, (84, 62, 110), **INV)
    blk(hx, 22, hz, 26, 9, 26, (40, 34, 52), **INV)
    blk(hx + 12, 22, hz + 4, 9, 16, 9, (40, 34, 52), **INV)
    for wx, wy in ((-10, 12), (10, 12), (-10, 4), (10, 4)):
        light(blk(hx + wx, wy, hz - 14, 1, 1, 1, WHITE, **INV, **NC), (255, 190, 70), 24, 1.6)
    for _ in range(14):                                   # ghosts (they float, see the client)
        x, y, z = side_x(16, 156), rng.uniform(5, 26), rng.uniform(z0 + 8, z0 + ZL - 8)
        mpart('Map_Ghost', x, y + 1.0, z, (x * 7) % 60 - 30, transparency=0.2, pname='Ghost')
    for _ in range(12):                                   # lanterns
        x, z = side_x(12, 40), rng.uniform(z0 + 6, z0 + ZL - 6)
        mpart('Map_SpookyLantern', x, 0, z)
        mpart('Map_SpookyLanternNeon', x, 0, z, mat='Neon')
        blk(x, 0, z, 0.8, 9, 0.8, INK, **INV)
        light(blk(x, 9, z, 1, 1, 1, WHITE, **INV, **NC), (140, 255, 150), 26, 1.6)
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
        if has_mesh('Map_Tower1', 'Map_TowerNeon1', 'Map_NeonLamp', 'Map_NeonOrb1', 'Map_Arcade', 'Map_ArcadeNeon1', 'Map_HoverCar',
                    'Map_HoverCarNeon1', 'Map_HoloArch', 'Map_HoloEgg', 'Map_HoloRing'):
            return neon_mesh(z0, NEON)
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


def neon_mesh(z0, NEON):
    """Neon City with the Blender meshes (same dice order as the block version)"""
    INV = dict(transparency=1)
    names = ['EGGS', 'ARCADE', '24/7', 'LUCKY', 'HATCH', 'RARE', 'PETS', 'OPEN']
    k = 0
    for sx in (-1, 1):                                    # towers, fronts turned to the road
        for z in range(int(z0) + 16, int(z0 + ZL) - 10, 26):
            for row, x in enumerate((60, 104, 146)):
                if rng.random() < 0.18:
                    continue
                w, d, h = rng.uniform(18, 26), rng.uniform(14, 20), rng.uniform(26, 50) + row * 22
                c = NEON[k % 5]
                tx = sx * (x + rng.uniform(-5, 5))
                sv = (d / 22, h / 60, w / 17)
                if row < 2:                               # only the outer row of towers: room to run (dice kept the same)
                    k += 1
                    continue
                mpart(f'Map_Tower{k % 3 + 1}', tx, 0, z, 90 * sx, sv=sv)
                mpart(f'Map_TowerNeon{k % 5 + 1}', tx, 0, z, 90 * sx, mat='Neon', sv=sv)
                blk(tx, 0, z, w, h, d, (30, 32, 52), **INV)
                k += 1
    for _ in range(12):                                   # street lamps
        x, z = rng.choice((-1, 1)) * rng.uniform(14, 40), rng.uniform(z0 + 6, z0 + ZL - 6)
        c = rng.choice(NEON)
        mpart('Map_NeonLamp', x, 0, z)
        light(mpart(f'Map_NeonOrb{NEON.index(c) + 1}', x, 13.4, z - 1.2, 0, 1, 'Neon'), c, 30, 2)
        blk(x, 0, z, 0.8, 14, 0.8, (60, 64, 90), **INV)
    for _ in range(10):                                   # arcade machines
        x, z, c = rng.choice((-1, 1)) * rng.uniform(16, 44), rng.uniform(z0 + 8, z0 + ZL - 8), rng.choice(NEON)
        yaw = -90 if x < 0 else 90
        mpart('Map_Arcade', x, 0, z, yaw)
        mpart(f'Map_ArcadeNeon{NEON.index(c) + 1}', x, 0, z, yaw, mat='Neon')
        blk(x, 0, z, 3.4, 7.6, 4, (50, 52, 80), **INV)
    for _ in range(9):                                    # hover cars
        x, y, z, c = rng.uniform(-150, 150), rng.uniform(34, 74), rng.uniform(z0 + 8, z0 + ZL - 8), rng.choice(NEON)
        mpart('Map_HoverCar', x, y, z, (x * 3) % 360)
        mpart(f'Map_HoverCarNeon{NEON.index(c) + 1}', x, y, z, (x * 3) % 360, mat='Neon')
    hz = z0 + 76                                          # hologram egg in a ring, over the road
    mpart('Map_HoloArch', 0, 0, hz)
    for sx in (-1, 1):
        blk(sx * 16, 0, hz, 4, 30, 4, (50, 52, 80), **INV)
    blk(0, 30, hz, 37, 2, 4, (50, 52, 80), **INV)
    mpart('Map_HoloEgg', 0, 45, hz, transparency=0.4, pname='Hologram')
    light(mpart('Map_HoloRing', 0, 45, hz, mat='Neon'), NEON[0], 60, 3)
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


LAMPS = []
LAMP_METAL = (46, 50, 60)
LAMP_WARM = (255, 214, 150)


def street_lamp(x, z, toward, accent):
    """road lamp (user, 19 Nov: 'more professional and realistic'): metal base, round pole with a collar,
    an arm over the road with a brace, and a lantern (cap, warm glass, bulb, zone-colour band) giving warm light.
    toward = +1 / -1: the side of the road the arm points to."""
    M = LAMP_METAL
    # v115 (user: lamps stood in the egg / on bridges / through fences): skip a lamp whose post or lantern would sit
    # inside something already built there (anything taller than the floor, near the post or under the lantern)
    hx0 = x + toward * 3.3
    for p in PARTS:
        s, (px, py, pz) = p['size'], p['p']
        if p.get('transparency', 0) > 0.9 and not p.get('mesh'):
            continue
        top, bottom = py + s[1] / 2, py - s[1] / 2
        if top < 0.9 or bottom > 12 or max(s) > 300:             # floors, sky things, the long side walls
            continue
        r = max(s[0], s[2]) / 2
        for qx, qy0 in ((x, 0), (hx0, 8)):
            if abs(px - qx) < r + 1.2 and abs(pz - z) < r + 1.2 and top > qy0:
                return
    blk(x, 0, z, 2.4, 0.5, 2.4, shade(M, 0.85), 'Metal')                      # base plate
    blk(x, 0.5, z, 1.7, 1.4, 1.7, M, 'Metal')                                 # plinth
    blk(x, 1.9, z, 2.0, 0.3, 2.0, shade(M, 1.2), 'Metal', **NC)              # plinth lip
    vcyl(x, 2.2, z, 9.6, 0.62, M, 'Metal')                                    # pole
    vcyl(x, 6.4, z, 0.4, 0.95, shade(M, 1.25), 'Metal', **NC)                 # collar
    vcyl(x, 11.8, z, 0.6, 0.9, shade(M, 1.15), 'Metal', **NC)                 # top finial
    ax = x + toward * 1.7
    blk(ax, 11.2, z, 3.6, 0.35, 0.4, M, 'Metal', **NC)                        # arm over the road
    for i, (dx, dy) in enumerate(((0.55, 10.2), (1.1, 10.6), (1.6, 10.95))):  # brace under the arm (curved, stepped)
        blk(x + toward * dx, dy, z, 0.5, 0.3, 0.3, M, 'Metal', **NC)
    hx = x + toward * 3.3
    blk(hx, 10.7, z, 0.25, 0.5, 0.25, M, 'Metal', **NC)                       # hanger
    blk(hx, 10.25, z, 1.9, 0.35, 1.9, shade(M, 1.1), 'Metal', **NC)           # lantern cap
    blk(hx, 10.05, z, 1.4, 0.2, 1.4, accent, 'Neon', **NC)                    # zone-colour band
    blk(hx, 8.8, z, 1.35, 1.25, 1.35, LAMP_WARM, 'Glass', transparency=0.35, **NC)   # warm glass
    light(blk(hx, 9.1, z, 0.6, 0.6, 0.6, (255, 236, 200), 'Neon', **NC), LAMP_WARM, 22, 1.4)   # bulb + warm light
    blk(hx, 8.6, z, 1.6, 0.25, 1.6, shade(M, 1.1), 'Metal', **NC)             # lantern bottom


def scenery():
    """hero egg per zone, road lamps, background hills and floating islands (no empty horizon)"""
    cols = [((120, 210, 90), (60, 150, 60))] + [(z[2], z[3]) for z in ZONES]
    with group('Scenery', unique=False):
        for j, (c1, c2) in enumerate(cols):
            z0 = (j - 1) * ZL                               # j = 0 is the home area
            for sx in (-1, 1):
                for _ in range(2):
                    x, z = sx * rng.uniform(280, 430), z0 + rng.uniform(15, 125)
                    w, h = rng.uniform(90, 150), rng.uniform(14, 22)
                    for k, (f, c) in enumerate(((1, shade(c2, 0.75)), (0.74, c2), (0.5, shade(c2, 1.18)), (0.27, c1))):
                        blk(x, -24 + k * h, z, w * f, h, w * f, c, 'Plastic', **NC)
            if j == 0:
                continue
            hs = 1 if j % 2 else -1
            hz, s = z0 + ZL * 0.72, 15
            blk(hs * (HALF + 12), 34, hz, 30, 3, 30, c2, 'Plastic')
            egg(hs * (HALF + 12), 37 + 1.5 * s, hz, s, c1, WHITE, n=9, name='HeroEgg')
            fx, fy, fz = -hs * rng.uniform(240, 300), rng.uniform(55, 90), z0 + rng.uniform(30, 110)
            blk(fx, fy, fz, 44, 4, 44, shade(c1, 0.95), 'Plastic', **NC)
            for k, w in enumerate((36, 26, 14)):
                blk(fx, fy - 6 * (k + 1), fz, w, 6, w, shade(DIRT, 1 - 0.1 * k), 'Plastic', **NC)
            egg(fx, fy + 10, fz, 4, WHITE, c2, name='Decor')
            for sx in (-1, 1):
                for k in range(5):
                    lz = z0 + 14 + k * 28
                    if j == len(cols) - 1 and abs(lz - (z0 + 92)) < 58:
                        continue    # v114: no lamps inside the Golden Nest (they stood in the nest / the giant egg)
                    LAMPS.append((sx * 12, lz, -sx, c1))   # built after the zones (to skip spots already taken)



# ------------------------------------------------------------------ v119: WORLD 2 (space, high above the map)
# Cosmic Nest (free through the Golden Portal), Moon Craters, Nebula Reef, then a COMING SOON wall.
# Built at height 0 like world 1 and lifted by WORLD2['y'] at the end. Keep in sync with C.COSMIC in game/Config.lua
# (y 900, half width 130, exit portal at z -28, zone k of world 2 = z (k-1)*140 .. k*140).
WORLD2 = dict(y=900, half=HALF, zones=3)   # v120: same width as world 1
W2_UNDER = ((8, 10), (30, 14), (58, 16), (88, 20))


def w2_floor(z0, z1, c1, c2, under):
    """floating floor between z0 and z1: two-shade strips on top, a rocky underside"""
    H = WORLD2['half']
    with group('Ground', unique=False):
        for k, z in enumerate(range(int(z0), int(z1), 10)):
            blk(0, -4, z + 5, H * 2, 4, 10, c1 if k % 2 else c2, 'Slate', name='SpaceGround')
    for k, (inset, h) in enumerate(W2_UNDER):
        y = -4 - sum(hh for _, hh in W2_UNDER[:k + 1])
        blk(0, y, (z0 + z1) / 2, H * 2 - inset * 2, h, (z1 - z0) - inset, shade(under, 1 - 0.1 * k), 'Slate', **NC)


def w2_walls(z0, z1, top, cliff):
    """v120 (user: 'the walls exactly like in world 1'): the world 1 checker walls + the stepped ledge under them"""
    zc, ln = (z0 + z1) / 2, z1 - z0
    for sx in (-1, 1):
        blk(sx * (HALF - 4), 0, zc, 8, 7, ln, shade(cliff, 0.88), 'Plastic')
        blk(sx * (HALF - 4.5), 7, zc, 9, 1.5, ln, shade(top, 1.08), 'Plastic')
    wall_run(z0, z1, top, cliff)


def w2_dots(cr, z0, z1, cols, n=60):
    H = WORLD2['half']
    for _ in range(n):
        blk(cr.uniform(-H + 4, H - 4), 0, cr.uniform(z0 + 2, z1 - 2), 1, 0.15, 1, cr.choice(cols), 'Neon', **NC)


def w2_cosmic(cr, z0):
    CYAN, PINK, VIO, DARK = (90, 230, 255), (255, 110, 220), (170, 110, 255), (30, 22, 58)
    H = WORLD2['half']
    with group('Zone11_CosmicNest', unique=False):
        w2_floor(-56, z0 + 140, (54, 40, 96), (70, 52, 122), DARK)
        w2_walls(-56, z0 + 140, (90, 60, 160), (44, 30, 84))
        for k, x in enumerate(range(-HALF - 24, HALF + 24, 24)):    # back wall (behind the exit portal), same checker look
            for row in range(2):
                blk(x + 12, -4 + row * 17, -68, 24, 17, 24, (44, 30, 84) if (k + row) % 2 == 0 else shade((44, 30, 84), 1.13), 'Plastic')
            blk(x + 12, 30, -68, 24, 4, 26, (90, 60, 160), 'Plastic')
        blk(0, 0, -58, HALF * 2 + 48, 120, 2, WHITE, transparency=1, name='Wall')
        w2_dots(cr, -50, z0 + 140, (CYAN, PINK, (255, 240, 150), WHITE), 120)
        for _ in range(12):                                   # glowing cracks
            x, z, yaw = cr.uniform(-H + 20, H - 20), cr.uniform(z0 + 30, z0 + 130), cr.uniform(0, 180)
            for j in range(4):
                blk(x + j * 3 * math.cos(math.radians(yaw)), 0, z + j * 3 * math.sin(math.radians(yaw)), 3.4, 0.2, 0.7, VIO, 'Neon',
                    yaw=-yaw + cr.uniform(-25, 25), **NC)
        for k in range(10):                                   # crystal clusters along both edges
            sx = -1 if k % 2 == 0 else 1
            x, z = sx * cr.uniform(H - 40, H - 22), z0 + 10 + k * 12 + cr.uniform(-4, 4)
            col = cr.choice((CYAN, PINK, VIO))
            for j in range(cr.randint(3, 5)):
                h = cr.uniform(8, 22)
                part((cr.uniform(2.5, 4.5), h, cr.uniform(2.5, 4.5)), C(x + cr.uniform(-4, 4), h / 2 - 1, z + cr.uniform(-4, 4)) *
                     R(cr.uniform(-18, 18), cr.uniform(0, 90), cr.uniform(-18, 18)), col, 'Glass', transparency=0.15)
            light(blk(x, 0, z, 2, 2, 2, col, 'Neon', **NC), col, 24, 2)
        zc = z0 + 84                                          # the Cosmic Egg on a floating ring
        for j in range(16):
            a = j * 6.283 / 16
            blk(math.cos(a) * 16, 2, zc + math.sin(a) * 16, 6, 1.2, 3, VIO if j % 2 else CYAN, 'Neon', yaw=-math.degrees(a), **NC)
        vcyl(0, 0, zc, 2, 22, DARK, 'Slate')
        egg(0, 16, zc, 4.2, (120, 70, 230), CYAN, mat='Glass', n=9, name='CosmicEgg')
        light(vcyl(0, 24, zc, 300, 8, VIO, 'Neon', transparency=0.75, name='CosmicBeam', **NC), VIO, 60, 3)
        # exit portal pad at z -28 (the portal itself is Codex's GoldenPortalVFX, made by the game client)
        vcyl(0, 0, -28, 0.3, 30, DARK, 'Slate', **NC)
        vcyl(0, 0.05, -28, 0.3, 24, VIO, 'Neon', name='ExitPad', **NC)
        b = blk(0, 0, -50, 34, 7, 2, DARK, 'Slate')
        sign(b, 'Back', 'BACK TO THE GOLDEN NEST', 'walk into the portal', fg=(255, 255, 255), bg1=(120, 70, 230), bg2=(60, 30, 140), pps=16)


def w2_moon(cr, z0):
    GREY, GREY2, DARK, RED = (176, 180, 194), (196, 200, 212), (90, 92, 108), (240, 70, 70)
    H = WORLD2['half']
    with group('Zone12_MoonCraters', unique=False):
        w2_floor(z0, z0 + 140, GREY, GREY2, DARK)
        w2_walls(z0, z0 + 140, GREY2, (110, 114, 132))
        w2_dots(cr, z0, z0 + 140, (WHITE, (170, 220, 255)), 40)
        for k in range(9):                                    # craters: raised rims of blocks around a dark hole
            x, z, r = cr.choice((-1, 1)) * cr.uniform(28, H - 20), cr.uniform(z0 + 18, z0 + 122), cr.uniform(6, 13)
            blk(x, -0.2, z, r * 1.5, 0.3, r * 1.5, DARK, 'Slate', **NC)
            n = int(r * 1.4)
            for j in range(n):
                a = j * 6.283 / n
                blk(x + math.cos(a) * r, 0, z + math.sin(a) * r, 4, cr.uniform(1.2, 2.6), 4, GREY2, 'Slate', yaw=-math.degrees(a))
        for _ in range(14):                                   # moon rocks
            x, z, s = cr.choice((-1, 1)) * cr.uniform(20, H - 6), cr.uniform(z0 + 6, z0 + 134), cr.uniform(2, 5)
            blk(x, 0, z, s * 1.4, s, s * 1.2, cr.choice((GREY, DARK, (140, 144, 160))), 'Slate', yaw=cr.uniform(0, 90))
        for sx in (-1, 1):                                    # flags
            x, z = sx * 60, z0 + 70
            blk(x, 0, z, 0.6, 14, 0.6, WHITE, 'Metal')
            blk(x + sx * 3.2, 10, z, 6, 4, 0.3, (70, 130, 250) if sx < 0 else RED, **NC)
        rx, rz = 92, z0 + 104                                 # small rocket
        blk(rx, 0, rz, 6, 18, 6, WHITE, 'Metal')
        blk(rx, 18, rz, 4.4, 4, 4.4, RED)
        blk(rx, 22, rz, 2.4, 3, 2.4, RED)
        for sx, sz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            blk(rx + sx * 4, 0, rz + sz * 4, 2.2 if sx else 1, 6, 1 if sx else 2.2, RED)
        blk(rx - 3.05, 12, rz, 0.2, 3, 3, (90, 230, 255), 'Neon', **NC)
        egg(-92, 8, z0 + 30, 2.2, (220, 225, 245), (120, 140, 255), beam=True, name='Decor')


def w2_nebula(cr, z0):
    TEAL, TEAL2, DEEP = (30, 70, 96), (38, 86, 116), (16, 30, 52)
    PINK, CYAN, GOLDN = (255, 110, 220), (90, 240, 230), (255, 220, 120)
    H = WORLD2['half']
    with group('Zone13_NebulaReef', unique=False):
        w2_floor(z0, z0 + 140, TEAL, TEAL2, DEEP)
        w2_walls(z0, z0 + 140, (60, 150, 170), (22, 52, 80))
        w2_dots(cr, z0, z0 + 140, (PINK, CYAN, GOLDN), 90)
        for _ in range(18):                                   # glowing coral: stacked neon branches
            x, z = cr.choice((-1, 1)) * cr.uniform(18, H - 8), cr.uniform(z0 + 8, z0 + 132)
            col = cr.choice((PINK, CYAN, (190, 120, 255), GOLDN))
            h = 0
            for j in range(cr.randint(3, 6)):
                hh = cr.uniform(2.5, 4.5)
                blk(x + cr.uniform(-1.2, 1.2), h, z + cr.uniform(-1.2, 1.2), 1.6, hh, 1.6, col, 'Neon')
                h += hh * 0.9
            blk(x + 1.8, h * 0.5, z, 3, 1.2, 1.2, col, 'Neon', **NC)
        for _ in range(9):                                    # floating jellyfish (soft, up in the air)
            x, y, z = cr.uniform(-H + 20, H - 20), cr.uniform(18, 40), cr.uniform(z0 + 15, z0 + 125)
            col = cr.choice((PINK, CYAN, (190, 120, 255)))
            sph(x, y, z, cr.uniform(6, 10), col, 'Glass', transparency=0.25, **NC)
            for j in range(4):
                a = j * 1.57 + 0.6
                blk(x + math.cos(a) * 2, y - 9, z + math.sin(a) * 2, 0.5, 6, 0.5, col, 'Neon', **NC)
        for _ in range(30):                                   # bubbles
            sph(cr.uniform(-H + 6, H - 6), cr.uniform(4, 50), cr.uniform(z0 + 4, z0 + 136), cr.uniform(1, 2.2), (200, 250, 255), 'Glass',
                transparency=0.5, **NC)
        egg(92, 8, z0 + 40, 2.2, PINK, CYAN, beam=True, name='Decor')
        # end of world 2 for now: a solid wall with COMING SOON
        ze = z0 + 140
        b = blk(0, 0, ze + 1, H * 2 + 20, 60, 2, (40, 24, 80), 'Slate', name='Wall')
        sign(b, 'Front', 'COMING SOON', 'new zones are on the way', fg=(255, 236, 90), bg1=(120, 70, 230), bg2=(40, 20, 100), pps=8)
        for sx in (-1, 1):
            blk(sx * (H - 14), 0, ze - 2, 8, 64, 8, (60, 40, 120), 'Slate')
            blk(sx * (H - 14), 64, ze - 2, 9, 3, 9, PINK, 'Neon')
        blk(0, 60, ze + 1, H * 2 + 20, 240, 2, WHITE, transparency=1, name='Wall')



# v121 (user: "details and things on the walls, everything like in world 1, only with a space theme")
W2_THEMES = [  # (name, c1 = bright, c2 = deep, road, accent glow)
    ('cosmic', (170, 110, 255), (60, 36, 120), (40, 30, 80), (90, 230, 255)),
    ('moon', (210, 214, 228), (110, 114, 132), (70, 72, 90), (120, 200, 255)),
    ('nebula', (255, 110, 220), (22, 70, 100), (20, 46, 70), (90, 240, 230)),
]


def w2_road(z0, z1, road, glow):
    """the world 1 road, space style: dark road, glowing edges, glowing dashes"""
    zc, ln = (z0 + z1) / 2, z1 - z0
    blk(0, 0, zc, ROADW, 0.3, ln, road, 'Slate')
    for sx in (-1, 1):
        blk(sx * (ROADW / 2 + 0.6), 0, zc, 1.2, 0.7, ln, glow, 'Neon')
    for z in range(int(z0) + 10, int(z1), 20):
        blk(0, 0.3, z, 1.2, 0.06, 9, glow, 'Neon', **NC)


def w2_lamp(x, z, glow, dark):
    blk(x, 0, z, 1.6, 1, 1.6, dark, 'Slate')
    blk(x, 1, z, 0.8, 9, 0.8, dark, 'Metal')
    blk(x, 10, z, 2.4, 0.6, 2.4, dark, 'Metal')
    light(blk(x, 10.6, z, 1.8, 1.8, 1.8, glow, 'Neon', **NC), glow, 18, 1.5)


def w2_on_wall(cr, kind, x, z, c1, c2, glow):
    """one decoration standing on the top of a side wall (wall top at y 34)"""
    y = 34
    if kind == 'cosmic':          # crystal cluster
        for j in range(cr.randint(2, 4)):
            h = cr.uniform(5, 12)
            part((cr.uniform(1.8, 3), h, cr.uniform(1.8, 3)), C(x + cr.uniform(-3, 3), y + h / 2, z + cr.uniform(-3, 3)) *
                 R(cr.uniform(-15, 15), cr.uniform(0, 90), cr.uniform(-15, 15)), cr.choice((c1, glow, (255, 110, 220))), 'Glass',
                 transparency=0.15)
    elif kind == 'moon':          # dome / antenna / satellite dish
        r = cr.random()
        if r < 0.4:
            sph(x, y + 2, z, 8, (230, 232, 240), 'SmoothPlastic')
            blk(x, y, z - 4.2, 2.4, 3, 0.6, glow, 'Neon', **NC)
        elif r < 0.7:
            blk(x, y, z, 0.6, 12, 0.6, (200, 204, 216), 'Metal')
            light(blk(x, y + 12, z, 1.2, 1.2, 1.2, (255, 70, 70), 'Neon', **NC), (255, 70, 70), 10, 1)
        else:
            blk(x, y, z, 1.2, 5, 1.2, (150, 154, 170), 'Metal')
            part((7, 0.6, 7), C(x, y + 6.5, z) * R(35, 0, 0), (225, 228, 238), 'Metal')
            blk(x, y + 7, z + 1.6, 0.4, 3, 0.4, glow, 'Neon', **NC)
    else:                         # nebula coral + glowing pod
        h = 0
        col = cr.choice((c1, glow, (255, 220, 120)))
        for j in range(cr.randint(3, 5)):
            hh = cr.uniform(2, 3.5)
            blk(x + cr.uniform(-1, 1), y + h, z + cr.uniform(-1, 1), 1.4, hh, 1.4, col, 'Neon')
            h += hh * 0.9
        sph(x + 3, y + 1.6, z + 2, 3, cr.choice((c1, glow)), 'Glass', transparency=0.3, **NC)


def w2_scenery(cr):
    """everything world 1 has around and on its zones (scenery()), in space colours"""
    H = WORLD2['half']
    for j, (kind, c1, c2, road, glow) in enumerate(W2_THEMES):
        z0 = j * ZL
        z_road0 = -56 if j == 0 else z0
        with group(f'W2Scenery{j + 1}', unique=False):
            w2_road(z_road0, z0 + ZL, road, glow)
            # road lamps (not inside the Cosmic Egg ring)
            for sx in (-1, 1):
                for k in range(5):
                    lz = z0 + 14 + k * 28
                    if j == 0 and abs(lz - 84) < 26:
                        continue
                    w2_lamp(sx * 12, lz, glow, shade(c2, 0.7))
            # things standing on top of both side walls
            for sx in (-1, 1):
                for k in range(6):
                    w2_on_wall(cr, kind, sx * (HALF + 11 + cr.uniform(-5, 5)), z0 + 10 + k * 23 + cr.uniform(-4, 4), c1, c2, glow)
            # hero egg on a wall platform (world 1: one big egg per zone, sides take turns)
            hs = 1 if j % 2 == 0 else -1
            hz, sz = z0 + ZL * 0.72, 15
            blk(hs * (HALF + 12), 34, hz, 30, 3, 30, c2, 'Plastic')
            blk(hs * (HALF + 12), 37, hz, 31, 0.4, 31, glow, 'Neon', **NC)
            egg(hs * (HALF + 12), 37 + 1.5 * sz, hz, sz, c1, glow, n=9, name='HeroEgg')
            # stepped space rocks behind the walls (world 1: hills), with glowing crystal tops
            for sx in (-1, 1):
                for _ in range(2):
                    x, z = sx * cr.uniform(280, 430), z0 + cr.uniform(15, 125)
                    w, h = cr.uniform(90, 150), cr.uniform(14, 22)
                    for k, (f, c) in enumerate(((1, shade(c2, 0.6)), (0.74, shade(c2, 0.8)), (0.5, c2), (0.27, c1))):
                        blk(x, -24 + k * h, z, w * f, h, w * f, c, 'Slate', **NC)
                    blk(x, -24 + 4 * h, z, w * 0.12, 6, w * 0.12, glow, 'Neon', **NC)
            # floating asteroid with a small egg (world 1: floating island)
            fx, fy, fz = -hs * cr.uniform(240, 300), cr.uniform(55, 90), z0 + cr.uniform(30, 110)
            blk(fx, fy, fz, 44, 4, 44, c2, 'Slate', **NC)
            blk(fx, fy + 4, fz, 44.4, 0.4, 44.4, glow, 'Neon', **NC)
            for k, w in enumerate((36, 26, 14)):
                blk(fx, fy - 6 * (k + 1), fz, w, 6, w, shade(c2, 0.8 - 0.1 * k), 'Slate', **NC)
            egg(fx, fy + 10, fz, 4, WHITE, glow, name='Decor')
            # little rocks and glowing bits along the foot of the walls (fills the edges like world 1 props)
            for sx in (-1, 1):
                for k in range(8):
                    x, z = sx * cr.uniform(H - 30, H - 14), z0 + 8 + k * 17 + cr.uniform(-4, 4)
                    s2 = cr.uniform(2, 4)
                    blk(x, 0, z, s2 * 1.3, s2, s2, shade(c2, cr.uniform(0.8, 1.2)), 'Slate', yaw=cr.uniform(0, 90))
                    if cr.random() < 0.5:
                        blk(x, s2, z, 0.8, 0.8, 0.8, glow, 'Neon', **NC)


def world2():
    cr = random.Random(119)
    start = len(PARTS)
    w2_cosmic(cr, 0)
    w2_moon(cr, 140)
    w2_nebula(cr, 280)
    w2_scenery(random.Random(121))
    with group('Gates', unique=False):
        gate(140, 'MOON CRATERS', None, (200, 205, 220), (120, 130, 160))
        gate(280, 'NEBULA REEF', None, (255, 110, 220), (90, 240, 230))
    keep = [q for q in PARTS[start:] if not ('Gates' in q['g'] and abs(q['p'][0]) > WORLD2['half'])]   # no flags in the void
    PARTS[start:] = keep
    with group('Zone11_CosmicNest', unique=False):           # sky: planets, a ringed giant, a moon and stars (far away)
        def planet(x, y, z, d, col, band=None):
            sph(x, y, z, d, col, 'SmoothPlastic', **NC)
            if band:
                blk(x, y - d * 0.08, z, d * 1.02, d * 0.14, d * 1.02, band, 'SmoothPlastic', **NC)
        planet(380, 140, 120, 140, (255, 150, 80), (255, 210, 140))
        for j in range(24):
            a = j * 6.283 / 24
            part((22, 2, 7), C(380 + math.cos(a) * 120, 140 + math.sin(a) * 20, 120 + math.sin(a) * 120) *
                 R(0, -math.degrees(a), 10), (255, 230, 170), 'Neon', transparency=0.3, **NC)
        planet(-400, 190, 330, 90, (80, 150, 255), (120, 230, 255))
        planet(-180, 280, -260, 46, (225, 225, 235))
        planet(260, 70, 560, 34, (255, 110, 220))
        for _ in range(140):
            a, e = cr.uniform(0, 6.283), cr.uniform(0.05, 1.2)
            d, s = cr.uniform(480, 640), cr.uniform(1.5, 4)
            blk(math.cos(a) * math.cos(e) * d, -60 + math.sin(e) * d, 210 + math.sin(a) * math.cos(e) * d, s, s, s,
                cr.choice((WHITE, (255, 240, 170), (170, 220, 255))), 'Neon', **NC)
    for p in PARTS[start:]:                                   # lift everything into space
        p['p'][1] = round(p['p'][1] + WORLD2['y'], 3)
    print('world 2:', len(PARTS) - start, 'parts')


def build():
    home()
    scenery()
    for i, (name, sub, c1, c2, fn) in enumerate(ZONES):
        fn(i)
        with group('Gates', unique=False):
            if i == 0 and zone_arch(1, 0, 'RAINING EGGS', name, c1, c2, sub='catch  •  hatch  •  get lucky'):
                pass                                                      # the Blender title arch (zone 1)
            elif i == 0:
                # big title arch between the plaza and the first zone
                for sx in (-1, 1):
                    blk(sx * 30, 0, 0, 7, 30, 7, WHITE)
                    for k, c in enumerate(RAINBOW):
                        blk(sx * 30, 3 + k * 4.4, 0, 7.6, 2.2, 7.6, c)
                    egg(sx * 30, 34.5, 0, 2.6, WHITE, RAINBOW[0 if sx < 0 else 4])
                b = blk(0, 20, 0, 52, 11, 4, INK)
                sign(b, 'Front', 'RAINING EGGS', 'catch  •  hatch  •  get lucky', fg=(255, 236, 90), bg1=(90, 170, 255), bg2=(60, 90, 230), pps=16)
                sign(b, 'Back', name, None, bg1=c1, bg2=c2, pps=16)
            else:
                gate(i * ZL, name, sub, c1, c2, n=i + 1)
    with group('Water', unique=False):
        for sx in (-1, 1):
            for zc in (-380, 1660):
                blk(sx * 1020, -24, zc, 2040, 2, 2040, (36, 120, 205), name='Sea', **NC)


def clear_circles():
    """remove props whose centre is inside a shop circle (keeps the ground, the circle itself and big floor parts)"""
    keep = []
    for p in PARTS:
        x, y, z = p['p']
        inside = any((x - cx) ** 2 + (z - cz) ** 2 < r * r for cx, cz, r in CIRCLES)
        floor = y - p['size'][1] / 2 < 0.05 and p['size'][1] < 1.2 and max(p['size'][0], p['size'][2]) > 20
        if inside and y < 40 and p.get('name') not in ('ShopPad', 'ShopZone') and p.get('shape') != 'Cylinder' and not floor and not p['g'].endswith('Ground'):
            continue
        keep.append(p)
    print('shop circles: removed', len(PARTS) - len(keep), 'parts')
    PARTS[:] = keep


def solidify():
    """user (19 Nov): players must not walk or look through blocks. Decorative blocks built with NC become solid again,
    except: lights (Neon), see-through parts, very thin or tiny bits, the sea, gates (the server opens them), pads/zones."""
    SKIP_NAMES = ('Sea', 'ShopZone', 'ShopPad', 'PenFloor', 'Wall', 'Collect')
    n = 0
    for p in PARTS:
        if p.get('cancollide') is not False or p.get('mesh'):
            continue
        s = p['size']
        name = p.get('name') or ''
        # user 19 Nov: "any object, not only the big egg" -> everything visible is solid; only invisible helpers,
        # the sea and the glowing / see-through parts of the gates (the server opens the gates) stay soft
        # v100: big things are solid; small or flat bits (flowers, grass, stripes, thin trims) stay soft,
        # otherwise players get stuck between objects (user, 19 Nov)
        if (p.get('transparency', 0) > 0.5 or any(k in name for k in SKIP_NAMES) or max(s) < 3 or min(s) < 0.4
                or ('Gates' in p['g'] and (p['m'] == 'Neon' or p.get('transparency', 0) > 0.2))):
            continue
        del p['cancollide']
        n += 1
    print('solidify: made', n, 'blocks solid')
    # v101 (user: "hitboxes exactly on the body, not half a stud away"): the old invisible boxes put round meshes
    # ("what the player bumps into") are bigger than the mesh. The meshes collide by their own shape now, so an
    # invisible box that sits on a solid mesh stops colliding. Gameplay parts (walls, bounce caps, pads) stay.
    boxes = []
    for p in PARTS:
        if p.get('mesh') and p.get('cancollide') is not False:
            r = max(p['size']) / 2 + 0.5
            boxes.append((p['p'], r))
    KEEP = ('Wall', 'Bounce', 'PenFloor', 'ShopPad', 'ShopZone', 'Treadmill', 'Collect', 'HumanoidRootPart')
    off = 0
    for p in PARTS:
        if p.get('mesh') or p.get('cancollide') is False or p.get('transparency', 0) < 0.99 or 'Gates' in p['g']:
            continue
        if any(k in (p.get('name') or '') for k in KEEP):
            continue
        x, y, z = p['p']
        if any(abs(x - c[0]) < r and abs(z - c[2]) < r and abs(y - c[1]) < r + max(p['size']) for c, r in boxes):
            p['cancollide'] = False
            off += 1
    print('invisible boxes on solid meshes switched off:', off)


if __name__ == '__main__':
    build()
    with group('Scenery', unique=False):
        for args in LAMPS:
            street_lamp(*args)
    world2()
    clear_circles()
    solidify()
    spawn = [p for p in PARTS if p.get('spawn')]
    out = {'parts': PARTS, 'spawn': spawn[0]['p'] if spawn else [0, 1, 0]}
    (HERE / 'map.json').write_text(json.dumps(out), encoding='utf-8')
    groups = {}
    for p in PARTS:
        g = (p['g'].split('/')[1] if '/' in p['g'] else p['g']).split('#')[0]
        groups[g] = groups.get(g, 0) + 1
    print(len(PARTS), 'parts', groups)
