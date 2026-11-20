r"""Raining Eggs: the 10 zone entrance arches (zone signs) as bevelled vertex-coloured meshes, one theme per zone.

  blender -b -P gen_zone_signs.py                 -> out/RainingEggsZoneSigns.fbx + out/zonesign_*.png
  blender -b -P gen_zone_signs.py -- nofbx        (renders only)      -- norender   (fbx only)
                                                  + entries Map_ZoneArch_<n> / Map_ZoneArchNeon_<n> in ../game/props_meta.json

Meshes per zone n (1..10): Map_ZoneArch_<n> (everything solid-looking) and Map_ZoneArchNeon_<n> (bulbs, glowing bits;
Material Neon in the game). Both are soft (CanCollide=false); map/gen_map.py adds invisible collision boxes for the pillars
and the board, plus the text panels (SurfaceGui) that sit in the frames: the zone name on the board, the zone number on the crest.

Built in Roblox axes around the arch centre on the road (players come from -Z). Blender (x, y, z) = Roblox (x, -z, y).
The layout numbers (ARCH, below) are repeated in map/gen_map.py zone_arch(): change both together.
The pillars stand on the road edges; the opening between them (18 wide, 15.6 high) holds the server's glowing zone gate (Config C.GATE: 18 x 15).
"""
import bpy, bmesh, math, sys, pathlib, json, shutil, os
from mathutils import Matrix, Vector

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / 'out'
OUT.mkdir(exist_ok=True)
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
T = Matrix.Translation


def lin(c):
    f = lambda v: v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (f(c[0] / 255), f(c[1] / 255), f(c[2] / 255), 1.0)


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def mix(c, d, k):
    return tuple(int(a + (b - a) * k) for a, b in zip(c, d))


WHITE, CREAM, INK = (245, 247, 252), (250, 240, 214), (34, 30, 48)
GOLD, GOLD2 = (255, 204, 40), (222, 150, 20)
BULB = (255, 244, 190)

# (key, light colour c1, dark colour c2, theme) - colours = ZONES in map/gen_map.py
ZONES = [
    ('Meadow', (120, 210, 90), (60, 150, 60), 'meadow'),
    ('Mushroom', (190, 130, 255), (98, 70, 170), 'mushroom'),
    ('Candy', (255, 130, 180), (220, 70, 130), 'candy'),
    ('Toy', (255, 204, 40), (240, 90, 60), 'toy'),
    ('Crystal', (80, 220, 250), (40, 130, 210), 'crystal'),
    ('Spooky', (255, 140, 40), (84, 62, 110), 'spooky'),
    ('Thunder', (255, 220, 60), (70, 76, 104), 'thunder'),
    ('Neon', (255, 70, 200), (90, 60, 200), 'neon'),
    ('Cloud', (150, 200, 255), (90, 130, 240), 'cloud'),
    ('Golden', (255, 210, 60), (220, 130, 20), 'golden'),
]


def arch_layout(n):
    """P = pillar centre |x|, Y0 = board bottom, H = board height (zone 1 = the big RAINING EGGS title arch)"""
    return (12.0, 20.0, 12.0) if n == 1 else (11.3, 15.6, 10.0)   # pillars stand on the road edges (ROADW 18; gate C.GATE.width 18 between them)


# ---------------------------------------------------------------- mesh builder (same style as gen_shops.py)
class B:
    def __init__(self):
        self.bm = bmesh.new()
        self.col = self.bm.loops.layers.color.new('Col')

    def paint(self, verts, c, flat=False):
        cl, top, low = lin(c), lin(shade(c, 1.12)), lin(shade(c, 0.84))
        for f in {f for v in verts for f in v.link_faces}:
            f.normal_update()
            k = f.normal.z
            for l in f.loops:
                l[self.col] = cl if flat else (top if k > 0.6 else low if k < -0.3 else cl)

    def box(self, size, mat, c, bevel=0.1):
        res = bmesh.ops.create_cube(self.bm, size=1, matrix=mat @ Matrix.Diagonal((*size, 1)))
        verts = res['verts']
        w = min(bevel, min(size) * 0.3)
        if w > 0.015:
            edges = list({e for v in verts for e in v.link_edges})
            verts = bmesh.ops.bevel(self.bm, geom=edges, offset=w, offset_type='OFFSET', segments=1, affect='EDGES', profile=0.5)['verts']
            verts = list({v for v in verts} | {v for f in {f for v in verts for f in v.link_faces} for v in f.verts})
        self.paint(verts, c)

    def cyl(self, r, h, mat, c, segs=10, r2=None):
        verts = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=segs, radius1=r, radius2=r if r2 is None else r2, depth=h, matrix=mat)['verts']
        self.paint(verts, c)

    def ball(self, r, mat, c, segs=10, rings=7):
        verts = bmesh.ops.create_uvsphere(self.bm, u_segments=segs, v_segments=rings, radius=r, matrix=mat)['verts']
        self.paint(verts, c)

    def finish(self, name, loc):
        bm = self.bm
        bmesh.ops.triangulate(bm, faces=bm.faces)
        lo = Vector((min(v.co.x for v in bm.verts), min(v.co.y for v in bm.verts), min(v.co.z for v in bm.verts)))
        hi = Vector((max(v.co.x for v in bm.verts), max(v.co.y for v in bm.verts), max(v.co.z for v in bm.verts)))
        c, s = (lo + hi) / 2, hi - lo
        META[name] = {'centre': [round(c.x, 4), round(c.z, 4), round(-c.y, 4)], 'size': [round(s.x, 4), round(s.z, 4), round(s.y, 4)]}
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(name, me)
        ob.location = loc
        bpy.context.scene.collection.objects.link(ob)
        me.materials.append(MAT)
        return ob


def M(pos, yaw=0.0, rx=0.0, rz=0.0, scale=None):
    """matrix from a Roblox position (+ yaw about Y, tilt about X, roll about Z, degrees)"""
    x, y, z = pos
    m = T((x, -z, y)) @ Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Rotation(math.radians(rx), 4, 'X') @ Matrix.Rotation(math.radians(-rz), 4, 'Y')
    if scale:
        sx, sy, sz = scale
        m = m @ Matrix.Diagonal((sx, sz, sy, 1))
    return m


def rbox(b, pos, size, c, bevel=0.1, **rot):           # box in Roblox axes (size = x, y, z)
    b.box((size[0], size[2], size[1]), M(pos, **rot), c, bevel)


def rcyl(b, pos, r, h, c, axis='Y', segs=10, r2=None, **rot):
    m = M(pos, **rot)
    if axis == 'Z':
        m = m @ Matrix.Rotation(math.radians(90), 4, 'X')
    elif axis == 'X':
        m = m @ Matrix.Rotation(math.radians(90), 4, 'Y')
    b.cyl(r, h, m, c, segs, r2)


def rball(b, pos, r, c, scale=(1, 1, 1), segs=10, rings=7):
    b.ball(r, M(pos, scale=scale), c, segs, rings)


def egg(b, pos, s, c, spot=None):
    rball(b, pos, s, c, (1, 1.3, 1), 10, 8)
    if spot:
        x, y, z = pos
        for dz in (-1, 1):
            rball(b, (x - 0.35 * s, y + 0.35 * s, z + dz * 0.75 * s), 0.25 * s, spot, segs=6, rings=4)
            rball(b, (x + 0.4 * s, y - 0.1 * s, z + dz * 0.78 * s), 0.2 * s, spot, segs=6, rings=4)


# ---------------------------------------------------------------- themed ornaments (about s*4 studs tall, base at pos)
def o_meadow(b, n, pos, s, c1, c2):
    x, y, z = pos
    rcyl(b, (x, y + 1.2 * s, z), 0.18 * s, 2.4 * s, (70, 150, 60), segs=6)
    for sx in (-1, 1):
        rbox(b, (x + sx * 0.55 * s, y + 1.1 * s, z), (1.0 * s, 0.18 * s, 0.5 * s), (90, 190, 70), 0.05, rz=sx * 30)
    cy = y + 2.9 * s
    for k in range(6):
        a = k * math.pi / 3
        rball(b, (x + math.cos(a) * 0.75 * s, cy + math.sin(a) * 0.75 * s, z), 0.5 * s, WHITE if k % 2 else (255, 236, 250), (1, 1, 0.55), 8, 5)
    rball(b, (x, cy, z), 0.48 * s, (255, 210, 50), (1, 1, 0.8), 8, 5)


def o_mushroom(b, n, pos, s, c1, c2):
    x, y, z = pos
    rcyl(b, (x, y + 0.9 * s, z), 0.55 * s, 1.8 * s, CREAM, segs=8, r2=0.45 * s)
    rcyl(b, (x, y + 2.15 * s, z), 1.75 * s, 0.7 * s, (235, 70, 90), segs=10, r2=1.1 * s)
    rball(b, (x, y + 2.55 * s, z), 1.15 * s, (235, 70, 90), (1, 0.55, 1), 10, 5)
    for k in range(6):
        a = k * math.pi / 3 + 0.3
        rball(b, (x + math.cos(a) * 1.05 * s, y + 2.65 * s, z + math.sin(a) * 1.05 * s), 0.22 * s, WHITE, segs=6, rings=4)
    rball(b, (x, y + 3.2 * s, z), 0.28 * s, WHITE, segs=6, rings=4)
    for k in range(3):                                     # tiny glowing spores
        a = k * 2.1
        rball(n, (x + math.cos(a) * 1.9 * s, y + (1.2 + k * 0.6) * s, z + math.sin(a) * 1.0 * s), 0.16 * s, mix(c1, WHITE, 0.4), segs=6, rings=4)


def o_candy(b, n, pos, s, c1, c2):
    x, y, z = pos
    rcyl(b, (x, y + 1.3 * s, z), 0.14 * s, 2.6 * s, WHITE, segs=6)
    cy = y + 3.0 * s
    for k, (r, c) in enumerate(((1.45, c2), (1.15, WHITE), (0.85, c1), (0.55, WHITE), (0.28, c2))):
        rcyl(b, (x, cy, z), r * s, (0.5 + 0.04 * k) * s, c, axis='Z', segs=14)
    rball(b, (x, cy - 1.5 * s, z), 0.2 * s, c1, segs=6, rings=4)
    for sx in (-1, 1):                                     # wrapped sweets at the foot
        rball(b, (x + sx * 0.9 * s, y + 0.35 * s, z), 0.35 * s, (255, 230, 90) if sx < 0 else (120, 220, 255), (1.3, 1, 1), 8, 5)


def o_toy(b, n, pos, s, c1, c2):
    x, y, z = pos
    cols = ((240, 90, 60), (60, 160, 255), (255, 204, 40))
    for k, (dx, c) in enumerate(((-0.5, cols[0]), (0.55, cols[1]), (0.0, cols[2]))):
        h = 1.15 * s
        yy = y + (0 if k < 2 else h) + h / 2
        xx = x + dx * s * (1 if k < 2 else 0)
        rbox(b, (xx, yy, z), (h, h, h), c, 0.12 * s, yaw=k * 12)
        for sx in (-1, 1):
            for sz in (-1, 1):
                rcyl(b, (xx + sx * 0.27 * s, yy + h / 2 + 0.08 * s, z + sz * 0.27 * s), 0.16 * s, 0.18 * s, shade(c, 1.1), segs=6)
    rball(b, (x, y + 2.75 * s, z), 0.45 * s, WHITE, segs=8, rings=5)          # a little ball on top


def o_crystal(b, n, pos, s, c1, c2):
    x, y, z = pos
    rcyl(b, (x, y + 0.25 * s, z), 1.2 * s, 0.5 * s, shade(c2, 0.8), segs=6)
    for dx, h, tilt, c in ((0, 3.4, 0, c1), (-0.75, 2.2, -22, mix(c1, WHITE, 0.3)), (0.75, 2.5, 20, c2)):
        rcyl(b, (x + dx * s, y + 0.4 * s + h * s / 2, z), 0.5 * s, h * s, c, segs=6, r2=0.38 * s, rz=tilt)
        rcyl(n, (x + dx * s + math.sin(math.radians(tilt)) * h * s * 0.55, y + 0.4 * s + h * s * 1.02, z), 0.38 * s, 0.7 * s,
             mix(c1, WHITE, 0.55), segs=6, r2=0.0, rz=tilt)


def o_spooky(b, n, pos, s, c1, c2):
    x, y, z = pos
    cy = y + 1.15 * s
    for k in range(5):                                     # ribbed pumpkin
        rball(b, (x + (k - 2) * 0.42 * s, cy, z), 1.0 * s, shade((255, 140, 40), 1.0 - abs(k - 2) * 0.06), (0.62, 0.95, 1.05), 10, 6)
    rcyl(b, (x, cy + 1.1 * s, z), 0.18 * s, 0.6 * s, (90, 130, 50), segs=6, rz=10)
    for dz in (-1, 1):                                     # glowing face front and back
        for sx in (-1, 1):
            rbox(n, (x + sx * 0.42 * s, cy + 0.25 * s, z + dz * 1.0 * s), (0.36 * s, 0.32 * s, 0.12 * s), (255, 230, 90), 0.03, rz=sx * 25)
        rbox(n, (x, cy - 0.35 * s, z + dz * 1.0 * s), (0.95 * s, 0.22 * s, 0.12 * s), (255, 230, 90), 0.03)


def o_thunder(b, n, pos, s, c1, c2):
    x, y, z = pos
    cy = y + 2.6 * s
    for dx, r in ((-0.8, 0.75), (0.1, 1.0), (0.95, 0.7)):  # storm cloud
        rball(b, (x + dx * s, cy + (r - 0.75) * 0.5 * s, z), r * s, (150, 156, 184), segs=8, rings=6)
    for k, (dx, dy, rz) in enumerate(((0.15, -1.0, -28), (-0.15, -1.75, 28), (0.15, -2.45, -28))):
        rbox(n, (x + dx * s, cy + dy * s, z), (0.34 * s, 0.95 * s, 0.3 * s), (255, 236, 80), 0.04, rz=rz)
    rcyl(n, (x + 0.05 * s, cy - 2.95 * s, z), 0.22 * s, 0.4 * s, (255, 236, 80), segs=6, r2=0.0, rx=180)


def o_neon(b, n, pos, s, c1, c2):
    x, y, z = pos
    rbox(b, (x, y + 0.3 * s, z), (1.2 * s, 0.6 * s, 1.2 * s), (40, 36, 70), 0.08)
    rcyl(b, (x, y + 1.1 * s, z), 0.12 * s, 1.2 * s, (40, 36, 70), segs=6)
    cy = y + 2.6 * s
    for k in range(12):                                    # neon ring
        a = k * math.pi / 6
        rbox(n, (x + math.cos(a) * 1.15 * s, cy + math.sin(a) * 1.15 * s, z), (0.62 * s, 0.22 * s, 0.22 * s), c1, 0.04, rz=math.degrees(a) + 90)
    for k in range(5):                                     # star inside it
        a = math.pi / 2 + k * 2 * math.pi / 5
        rbox(n, (x + math.cos(a) * 0.4 * s, cy + math.sin(a) * 0.4 * s, z), (0.2 * s, 0.75 * s, 0.2 * s), (120, 240, 255), 0.04, rz=math.degrees(a) - 90)


def o_cloud(b, n, pos, s, c1, c2):
    x, y, z = pos
    cy = y + 1.4 * s
    for dx, dy, r in ((-0.9, 0, 0.75), (0, 0.35, 1.0), (0.9, 0, 0.75), (0, -0.25, 0.8)):
        rball(b, (x + dx * s, cy + dy * s, z), r * s, WHITE, segs=8, rings=6)
    for sx in (-1, 1):                                     # little golden wings
        for k in range(3):
            rbox(b, (x + sx * (1.6 + k * 0.35) * s, cy + (0.7 + k * 0.25) * s, z), ((1.0 - k * 0.2) * s, 0.32 * s, 0.16 * s), GOLD, 0.04, rz=sx * (25 + k * 12))
    rball(n, (x, cy + 1.6 * s, z), 0.3 * s, (255, 246, 170), segs=6, rings=4)


def o_golden(b, n, pos, s, c1, c2):
    x, y, z = pos
    rcyl(b, (x, y + 0.45 * s, z), 1.3 * s, 0.9 * s, GOLD, segs=10)
    for k in range(5):
        a = k * 2 * math.pi / 5
        px, pz = x + math.cos(a) * 1.05 * s, z + math.sin(a) * 1.05 * s
        rcyl(b, (px, y + 1.25 * s, pz), 0.32 * s, 0.8 * s, GOLD, segs=5, r2=0.0)
        rball(n, (px, y + 1.7 * s, pz), 0.14 * s, (255, 90, 120) if k % 2 else (90, 200, 255), segs=6, rings=4)
    egg(b, (x, y + 2.35 * s, z), 0.62 * s, (255, 226, 110), WHITE)


ORN = {'meadow': o_meadow, 'mushroom': o_mushroom, 'candy': o_candy, 'toy': o_toy, 'crystal': o_crystal,
       'spooky': o_spooky, 'thunder': o_thunder, 'neon': o_neon, 'cloud': o_cloud, 'golden': o_golden}


# ---------------------------------------------------------------- one arch
def arch(num, c1, c2, theme):
    body, neon = B(), B()
    P, Y0, H = arch_layout(num)
    big = num == 1
    W = 2 * P + 8                                          # board width
    D = 3.0                                                # board depth
    lt, dk = mix(c1, WHITE, 0.35), shade(c2, 0.78)
    orn = ORN[theme]

    # pillars: plinth, step, shaft with bands and an egg emblem, capital
    for sx in (-1, 1):
        x = sx * P
        pw = 4.6 if not big else 6.0
        rbox(body, (x, 0.8, 0), (pw + 2.2, 1.6, pw + 2.2), c2, 0.3)
        rbox(body, (x, 1.9, 0), (pw + 1.2, 0.6, pw + 1.2), lt, 0.2)
        sh = Y0 - 3.6
        rbox(body, (x, 2.2 + sh / 2, 0), (pw, sh, pw), WHITE, 0.35)
        for cx in (-1, 1):                                 # corner trims
            for cz in (-1, 1):
                rbox(body, (x + cx * (pw / 2 - 0.05), 2.2 + sh / 2, cz * (pw / 2 - 0.05)), (0.55, sh, 0.55), lt, 0.12)
        for k in range(2 if not big else 3):                  # coloured bands
            rbox(body, (x, 3.6 + k * (sh - 2.4) / (1 if not big else 2), 0), (pw + 0.3, 0.8, pw + 0.3), c1, 0.18)
        ym = 2.2 + sh / 2 + 0.3
        for dz in (-1, 1):                                 # inset panel + egg emblem, front and back
            rbox(body, (x, ym, dz * (pw / 2 + 0.06)), (pw * 0.62, sh * 0.42, 0.16), lt, 0.05)
            egg(body, (x, ym, dz * (pw / 2 + 0.22)), 0.62 if not big else 0.8, c1, WHITE)
        rbox(body, (x, Y0 - 0.7, 0), (pw + 1.4, 1.4, pw + 1.4), c2, 0.25)
        rbox(body, (x, Y0 - 1.55, 0), (pw + 0.8, 0.3, pw + 0.8), lt, 0.08)
        # lanterns on the front and back of each pillar (the road side is the gate opening now)
        for dz in (-1, 1):
            lz = dz * (pw / 2 + 0.55)
            rbox(body, (x, Y0 - 3.0, lz), (0.5, 0.25, 0.5), INK, 0.04)
            rbox(neon, (x, Y0 - 3.7, lz), (0.75, 1.1, 0.75), BULB, 0.08)
            rbox(body, (x, Y0 - 4.35, lz), (0.95, 0.25, 0.95), INK, 0.05)

    # the board: chunky core, a proud frame in front and at the back, end scrolls with finials
    yc = Y0 + H / 2
    rbox(body, (0, yc, 0), (W, H, D), c2, 0.45)
    for dz in (-1, 1):
        zf = dz * (D / 2 + 0.35)
        rbox(body, (0, Y0 + H - 0.7, zf), (W + 0.4, 1.4, 0.7), lt, 0.2)
        rbox(body, (0, Y0 + 0.7, zf), (W + 0.4, 1.4, 0.7), lt, 0.2)
        for sx in (-1, 1):
            rbox(body, (sx * (W / 2 - 0.5), yc, zf), (1.4, H, 0.7), lt, 0.2)
            rbox(body, (sx * (W / 2 - 0.5), Y0 + H - 0.7, zf + dz * 0.2), (1.9, 1.9, 0.5), c1, 0.2)   # corner studs
            rbox(body, (sx * (W / 2 - 0.5), Y0 + 0.7, zf + dz * 0.2), (1.9, 1.9, 0.5), c1, 0.2)
        # marquee bulbs along the top and bottom frame bars
        cnt = int((W - 4) / 2.0)
        for k in range(cnt + 1):
            bx = -(W - 4) / 2 + k * (W - 4) / cnt
            for by in (Y0 + H - 0.7, Y0 + 0.7):
                rball(neon, (bx, by, zf + dz * 0.42), 0.27, BULB, segs=6, rings=4)
    for sx in (-1, 1):                                     # end scrolls
        ex = sx * (W / 2 + 0.9)
        rbox(body, (ex, yc, 0), (1.8, H + 1.0, D + 1.0), c1, 0.4)
        rbox(body, (ex + sx * 0.2, yc, 0), (1.2, H - 2.0, D + 1.4), lt, 0.25)
        for ey in (Y0 - 0.2, Y0 + H + 0.2):
            rball(body, (ex, ey, 0), 1.0, c2, segs=8, rings=6)
            rball(body, (ex, ey + (0.8 if ey > yc else -0.8), 0), 0.45, lt, segs=6, rings=4)

    # crest above the middle: a hexagon badge with a white rim (the zone number panel goes on it in gen_map.py)
    cr = 3.4 if not big else 4.4
    cy = Y0 + H + cr * 0.72
    rcyl(body, (0, cy, 0), cr + 0.6, D + 0.6, WHITE, axis='Z', segs=6, rz=0)
    rcyl(body, (0, cy, 0), cr, D + 1.2, c1, axis='Z', segs=6, rz=0)
    for dz in (-1, 1):                                     # glowing rim dots on the badge
        for k in range(6):
            a = k * math.pi / 3 + math.pi / 6
            rball(neon, (math.cos(a) * (cr + 0.3), cy + math.sin(a) * (cr + 0.3), dz * (D / 2 + 0.4)), 0.3, BULB, segs=6, rings=4)
    for sx in (-1, 1):                                     # ribbons from the badge to the board
        rbox(body, (sx * (cr + 1.3), Y0 + H + 0.55, 0), (3.2, 1.1, D - 0.4), c1, 0.2, rz=sx * -14)
        rbox(body, (sx * (cr + 3.4), Y0 + H + 0.25, 0), (1.4, 0.7, D - 0.6), lt, 0.15, rz=sx * -24)

    # themed ornaments: one on each top corner of the board, one smaller pair on the plinths
    s = 1.75 if not big else 2.3
    for sx in (-1, 1):
        orn(body, neon, (sx * (W / 2 - 1.6), Y0 + H, 0), s, c1, c2)
        orn(body, neon, (sx * (P + (4.6 if not big else 5.8)), 0, -0.4), 1.05 if not big else 1.3, c1, c2)
    return body, neon


META = {}
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
MAT = bpy.data.materials.new('VertexColour')
MAT.use_nodes = True
nt = MAT.node_tree
attr = nt.nodes.new('ShaderNodeVertexColor')
attr.layer_name = 'Col'
nt.links.new(attr.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
nt.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.6

objs, neons, LOCS = [], [], []
for i, (key, c1, c2, theme) in enumerate(ZONES):
    num = i + 1
    body, neon = arch(num, c1, c2, theme)
    loc = ((i % 5) * 90, -(i // 5) * 70, 0)
    LOCS.append(loc)
    objs.append(body.finish(f'Map_ZoneArch_{num}', loc))
    o = neon.finish(f'Map_ZoneArchNeon_{num}', loc)
    objs.append(o)
    neons.append(o)

pm_path = HERE.parent / 'game' / 'props_meta.json'
pm = json.loads(pm_path.read_text(encoding='utf-8')) if pm_path.exists() else {}
pm.update(META)
pm_path.write_text(json.dumps(pm, indent=1), encoding='utf-8')
tris = {o.name: len(o.data.polygons) for o in objs}
print('triangles:', tris)
assert max(tris.values()) < 20000, 'a mesh is over the Roblox triangle limit'

if 'nofbx' not in ARGS:
    for o in bpy.data.objects:
        o.select_set(o in objs)
    bpy.context.view_layer.objects.active = objs[0]
    fbx = OUT / 'RainingEggsZoneSigns.fbx'
    bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, object_types={'MESH'}, apply_scale_options='FBX_SCALE_UNITS',
                             mesh_smooth_type='FACE', colors_type='SRGB', add_leaf_bones=False, bake_anim=False)
    home = os.environ.get('USERPROFILE') or os.environ.get('HOME')
    desk = pathlib.Path(home) / 'Desktop' / fbx.name
    shutil.copyfile(fbx, desk)
    print('wrote', fbx.stat().st_size // 1024, 'KB ->', desk)
    # one small file per zone too (2 meshes each): Studio's upload can time out on 20 meshes at once
    one = desk.parent / 'RainingEggsZoneSigns'
    one.mkdir(exist_ok=True)
    for i in range(len(ZONES)):
        pair = objs[2 * i:2 * i + 2]
        for o in bpy.data.objects:
            o.select_set(o in pair)
        bpy.context.view_layer.objects.active = pair[0]
        f1 = one / f'ZoneSign_{i + 1}.fbx'
        bpy.ops.export_scene.fbx(filepath=str(f1), use_selection=True, object_types={'MESH'}, apply_scale_options='FBX_SCALE_UNITS',
                                 mesh_smooth_type='FACE', colors_type='SRGB', add_leaf_bones=False, bake_anim=False)
    print('wrote', len(ZONES), 'zone files ->', one)

# ---------------------------------------------------------------- preview renders
if 'norender' not in ARGS:
    sc = bpy.context.scene
    for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            pass
    sc.view_settings.view_transform = 'Standard'
    sc.world = bpy.data.worlds.new('W')
    sc.world.use_nodes = True
    sc.world.node_tree.nodes['Background'].inputs[0].default_value = (0.55, 0.78, 1.0, 1)
    sc.world.node_tree.nodes['Background'].inputs[1].default_value = 0.9
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
    sun.data.energy = 3.4
    sun.data.angle = math.radians(8)
    sun.rotation_euler = (math.radians(48), 0, math.radians(200))
    sc.collection.objects.link(sun)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    cam.data.lens = 40
    sc.collection.objects.link(cam)
    sc.camera = cam
    gm = bpy.data.meshes.new('G')
    gb = bmesh.new()
    bmesh.ops.create_grid(gb, x_segments=1, y_segments=1, size=600)
    gb.to_mesh(gm)
    gb.free()
    gmat = bpy.data.materials.new('G')
    gmat.use_nodes = True
    gmat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.25, 0.55, 0.16, 1)
    gm.materials.append(gmat)
    sc.collection.objects.link(bpy.data.objects.new('Ground', gm))
    g = bpy.data.materials.new('Glow')
    g.use_nodes = True
    a = g.node_tree.nodes.new('ShaderNodeVertexColor')
    a.layer_name = 'Col'
    em = g.node_tree.nodes.new('ShaderNodeEmission')
    em.inputs['Strength'].default_value = 3
    g.node_tree.links.new(a.outputs['Color'], em.inputs['Color'])
    g.node_tree.links.new(em.outputs['Emission'], g.node_tree.nodes['Material Output'].inputs['Surface'])
    for o in neons:
        o.data.materials.clear()
        o.data.materials.append(g)

    # stand-in text panels (in the game these are SurfaceGuis made by gen_map.py), so the previews read like the real thing
    FONT = None
    for fp in ('/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf', 'C:/Windows/Fonts/ARLRDBD.TTF'):   # close to the game's FredokaOne
        if os.path.exists(fp):
            FONT = bpy.data.fonts.load(fp)
            break

    def panel(loc, num, c1, c2):
        P, Y0, H = arch_layout(num)
        W = 2 * P + 8
        pm_ = bpy.data.materials.new(f'P{num}')
        pm_.use_nodes = True
        pm_.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = lin(shade(c1, 0.95))
        bpy.ops.mesh.primitive_cube_add(size=1, location=(loc[0], loc[1], Y0 + H / 2))
        ob = bpy.context.active_object
        ob.scale = (W - 2.6, 3.2, H - 2.8)
        ob.data.materials.append(pm_)
        name = ['RAINING EGGS', 'MUSHROOM GROVE', 'CANDY CANYON', 'TOY TOWN', 'CRYSTAL COAST', 'SPOOKY HOLLOW',
                'THUNDER PEAKS', 'NEON CITY', 'CLOUD KINGDOM', 'GOLDEN NEST'][num - 1]
        bpy.ops.object.text_add(location=(loc[0], loc[1] + 1.65, Y0 + H / 2), rotation=(math.radians(90), 0, math.radians(180)))
        t = bpy.context.active_object
        t.data.body = name
        t.data.align_x = 'CENTER'
        t.data.align_y = 'CENTER'
        if FONT:
            t.data.font = FONT
        t.data.extrude = 0.05
        # same fit as the game's SurfaceGui (one line, TextScaled, 3.5 % side padding): as big as fits the frame
        t.data.size = 1.0
        bpy.context.view_layer.update()
        fit_w, fit_h = (W - 2.6) * (1 - 2 * 0.035), (H - 2.8) * 0.72 * 0.8
        t.data.size = min(fit_w / max(t.dimensions.x, 0.01), fit_h / max(t.dimensions.y, 0.01))
        tm = bpy.data.materials.new(f'T{num}')
        tm.use_nodes = True
        tm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (1, 1, 1, 1)
        t.data.materials.append(tm)
        cr = 3.4 if num > 1 else 4.4
        bpy.ops.object.text_add(location=(loc[0], loc[1] + 2.3, Y0 + H + cr * 0.72 - cr * 0.4), rotation=(math.radians(90), 0, math.radians(180)))
        t2 = bpy.context.active_object
        t2.data.body = str(num)
        t2.data.align_x = 'CENTER'
        if FONT:
            t2.data.font = FONT
        t2.data.size = cr * 1.15
        t2.data.materials.append(tm)
        return [ob, t, t2]

    PANEL = {}
    for i, (key, c1, c2, theme) in enumerate(ZONES):
        PANEL[i] = panel(LOCS[i], i + 1, c1, c2)

    def shot(name, tgt, dist, h, side=0.35, res=(1300, 900), keep=()):
        for o in bpy.data.objects:
            if o.type in ("MESH", "FONT") and o.name != "Ground":
                o.hide_render = o not in keep
        tgt = Vector(tgt)
        cam.location = Vector((tgt.x + dist * side, tgt.y + dist, h))
        cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.resolution_x, sc.render.resolution_y = res
        sc.render.filepath = str(OUT / f'zonesign_{name}.png')
        bpy.ops.render.render(write_still=True)

    only = [a for a in ARGS if a.isdigit()]
    for i, (key, _, _, _) in enumerate(ZONES):
        if only and str(i + 1) not in only:
            continue
        P, Y0, H = arch_layout(i + 1)
        keep = [objs[2 * i], objs[2 * i + 1]] + PANEL[i]
        shot(f'{i + 1}_{key}', (LOCS[i][0], LOCS[i][1], Y0 * 0.85), 62 if i else 100, 12 if i else 16, keep=keep)
