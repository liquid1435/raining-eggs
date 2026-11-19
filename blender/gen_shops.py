r"""Raining Eggs: the 4 plaza shops (BASKETS, LUCK SHOP, SELL, INDEX) as bevelled vertex-coloured meshes.

  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P gen_shops.py   -> out\RainingEggsShops.fbx + out\shop_*.png
                                                                          + entries in ..\game\props_meta.json

Meshes per shop: Shop_<Key> (everything solid) and ShopNeon_<Key> (lantern glass + string lights, Material Neon in the game).
Built in Roblox axes around the stall centre on the ground (front = -Z, same layout as stall() in map\gen_map.py,
so the game's ShopPad, sign text panel, vendor and collision boxes stay where they were).
Blender (x, y, z) = Roblox (x, -z, y).
"""
import bpy, bmesh, math, sys, pathlib, json, shutil, os, random
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
WOOD, WOOD2, GOLD = (184, 124, 70), (138, 90, 50), (255, 200, 40)
RAINBOW = [(255, 90, 90), (255, 160, 50), (255, 220, 60), (110, 220, 90), (80, 180, 255), (170, 110, 255), (255, 120, 200)]


class B:
    def __init__(self):
        self.bm = bmesh.new()
        self.col = self.bm.loops.layers.color.new('Col')
        self.n = 0

    def paint(self, verts, c, flat=False):
        cl, top, low = lin(c), lin(shade(c, 1.12)), lin(shade(c, 0.84))
        for f in {f for v in verts for f in v.link_faces}:
            f.normal_update()
            k = f.normal.z
            for l in f.loops:
                l[self.col] = cl if flat else (top if k > 0.6 else low if k < -0.3 else cl)
        self.n += 1

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
        rball(b, (x - 0.35 * s, y + 0.35 * s, z - 0.75 * s), 0.25 * s, spot, segs=6, rings=4)
        rball(b, (x + 0.4 * s, y - 0.1 * s, z - 0.78 * s), 0.2 * s, spot, segs=6, rings=4)


def crate(b, pos, s, yaw):
    x, y, z = pos
    rbox(b, (x, y + s / 2, z), (s, s, s), WOOD, 0.12, yaw=yaw)
    for k in (-1, 1):                                    # corner frame + planks
        for j in (-1, 1):
            c, sn = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
            ox, oz = k * s / 2 * 0.92, j * s / 2 * 0.92
            rbox(b, (x + ox * c + oz * sn, y + s / 2, z - ox * sn + oz * c), (0.36, s + 0.04, 0.36), WOOD2, 0.05, yaw=yaw)
    rbox(b, (x, y + s * 0.5, z), (s + 0.06, 0.3, s + 0.06), WOOD2, 0.05, yaw=yaw)
    rbox(b, (x, y + s + 0.1, z), (s + 0.2, 0.22, s + 0.2), WOOD2, 0.06, yaw=yaw)


# ---------------------------------------------------------------- the stall (shared shape)
def stall(key, col, mascot):
    body, neon = B(), B()
    r = random.Random(hash(key) % 1000)
    dk, lt = shade(col, 0.72), mix(col, WHITE, 0.25)
    # floor
    rbox(body, (0, 0.25, 0), (24, 0.5, 16), dk, 0.18)
    rbox(body, (0, 0.6, 0), (22, 0.2, 14), CREAM, 0.06)
    for i in range(5):
        for j in range(3):
            if (i + j) % 2:
                rbox(body, (-8.8 + i * 4.4, 0.71, -4.6 + j * 4.6), (4.3, 0.04, 4.5), shade(CREAM, 0.92), 0)
    rbox(body, (0, 0.15, -9.6), (12.4, 0.3, 3.2), CREAM, 0.08)                            # front step
    # back wall: planks, darker wainscot, round window
    rbox(body, (0, 7.1, 6), (20, 13, 1), shade(col, 0.82), 0.12)
    for k in range(10):
        rbox(body, (-9 + k * 2, 7.6, 5.42), (0.14, 11.4, 0.2), shade(col, 0.68), 0)
    rbox(body, (0, 1.9, 5.35), (20, 2.4, 0.4), dk, 0.08)
    rbox(body, (0, 3.15, 5.25), (20.2, 0.3, 0.55), CREAM, 0.06)
    # side walls with cream caps and a lattice of diamonds
    for sx in (-1, 1):
        rbox(body, (sx * 9.5, 3.1, 0), (0.8, 5, 10), shade(col, 0.9), 0.1)
        rbox(body, (sx * 9.5, 5.85, 0), (1.1, 0.5, 10.3), CREAM, 0.08)
        for k in range(4):
            rbox(body, (sx * 9.95, 3.2, -3.6 + k * 2.4), (0.12, 1.1, 1.1), lt, 0.04, rx=45)
    # posts: round wood with coloured feet, bands and caps
    for sx in (-1, 1):
        for pz in (-5.5, 5.5):
            rcyl(body, (sx * 9.5, 7.1, pz), 0.62, 13, WOOD, segs=10)
            rcyl(body, (sx * 9.5, 1.3, pz), 1.0, 1.4, col, segs=10)
            rcyl(body, (sx * 9.5, 2.1, pz), 0.85, 0.25, CREAM, segs=10)
            rcyl(body, (sx * 9.5, 12.9, pz), 1.0, 1.0, col, segs=10)
    # counter: wood body, striped slats with bumps, trims, cream top
    rbox(body, (0, 2.6, -4), (18, 4, 3), WOOD, 0.14)
    for k in range(9):
        c = col if k % 2 == 0 else WHITE
        rbox(body, (-8 + k * 2, 2.55, -5.62), (1.84, 2.9, 0.26), c, 0.06)
        rcyl(body, (-8 + k * 2, 4.0, -5.62), 0.9, 0.26, c, axis='Z', segs=12)
    rbox(body, (0, 0.9, -5.7), (18.4, 0.5, 0.5), dk, 0.08)
    rbox(body, (0, 4.4, -4), (18.6, 0.4, 3.5), dk, 0.08)
    rbox(body, (0, 4.9, -4), (19.6, 0.6, 4.4), CREAM, 0.16)
    # on the counter: till with bell, bowl of eggs
    rbox(body, (6.2, 5.9, -3.6), (2.6, 1.4, 1.8), dk, 0.14)
    rbox(body, (6.2, 6.8, -3.9), (2.2, 0.5, 0.9), INK, 0.08, rx=-25)
    rcyl(body, (4.4, 5.35, -4.3), 0.5, 0.1, GOLD, segs=10)
    rball(body, (4.4, 5.55, -4.3), 0.38, GOLD, (1, 0.8, 1), 8, 5)
    rcyl(body, (-6, 5.5, -4), 1.5, 0.8, WOOD2, segs=12, r2=1.9)
    for k, (dx, dz) in enumerate(((-0.6, -0.3), (0.6, -0.1), (0, 0.5))):
        egg(body, (-6 + dx, 6.3, -4 + dz), 0.55, RAINBOW[(k * 2 + len(key)) % 7], WHITE)
    # flower box along the counter front
    rbox(body, (0, 0.95, -6.6), (16, 0.9, 1.1), WOOD2, 0.1)
    for k in range(9):
        rball(body, (-7.2 + k * 1.8, 1.6, -6.6), 0.55, (90, 190, 80), (1, 0.8, 1), 8, 5)
        rball(body, (-7.2 + k * 1.8 + 0.3, 1.95, -6.9), 0.28, RAINBOW[k % 7], segs=6, rings=4)
    # shelves with eggs and jars
    for sy in (6.2, 9.8):
        rbox(body, (0, sy, 4.8), (18, 0.45, 1.8), WOOD, 0.08)
        for sx in (-7, 0, 7):
            rbox(body, (sx, sy - 0.6, 5.3), (0.4, 0.8, 0.8), WOOD2, 0.05)
        for k in range(7):
            gx, gc = -7.5 + k * 2.5, r.choice(RAINBOW)
            if r.random() < 0.55:
                egg(body, (gx, sy + 0.95, 4.8), 0.55, gc, WHITE)
            else:
                h = r.uniform(1.1, 1.8)
                rcyl(body, (gx, sy + 0.22 + h / 2, 4.8), 0.6, h, mix(gc, WHITE, 0.15), segs=10)
                rcyl(body, (gx, sy + 0.32 + h, 4.8), 0.66, 0.24, WHITE, segs=10)
    # striped awning (tilted 12 degrees), side boards, scalloped front edge, ridge
    for k in range(10):
        c = col if k % 2 == 0 else WHITE
        rbox(body, (-9.9 + k * 2.2, 14.6, -1), (2.2, 0.5, 15), c, 0.06, rx=-12)
        rbox(body, (-9.9 + k * 2.2, 12.5, -8.45), (2.2, 1.0, 0.45), c, 0.05)
        rbox(body, (-9.9 + k * 2.2, 11.8, -8.45), (1.4, 0.5, 0.44), c, 0.05)
    for sx in (-1, 1):
        rbox(body, (sx * 11.05, 14.4, -1), (0.3, 1.0, 15.3), dk, 0.06, rx=-12)
    rbox(body, (0, 13.05, -8.45), (22.2, 0.25, 0.5), dk, 0.04)
    rbox(body, (0, 16.2, 6.3), (22.6, 1.0, 1.6), dk, 0.14)
    # string of light bulbs under the scallops
    rbox(body, (0, 11.3, -8.5), (21.6, 0.08, 0.08), INK, 0)
    for k in range(12):
        x = -10.4 + k * 1.9
        rbox(body, (x, 11.1, -8.5), (0.22, 0.25, 0.22), INK, 0.03)
        rball(neon, (x, 10.7, -8.5), 0.3, RAINBOW[k % 7], (1, 1.25, 1), 8, 5)
    # lanterns on the front posts
    for sx in (-1, 1):
        x = sx * 9.5
        rbox(body, (x, 10.2, -6.9), (0.2, 1.7, 0.2), INK, 0)
        rbox(body, (x, 9.35, -6.9), (1.9, 0.35, 1.9), INK, 0.08)
        rbox(body, (x, 7.05, -6.9), (1.9, 0.35, 1.9), INK, 0.08)
        for dx, dz in ((-0.8, -0.8), (0.8, -0.8), (-0.8, 0.8), (0.8, 0.8)):
            rbox(body, (x + dx, 8.2, -6.9 + dz), (0.2, 2.0, 0.2), INK, 0)
        rbox(neon, (x, 8.2, -6.9), (1.4, 1.95, 1.4), (255, 222, 120), 0.12)
    # sign: two posts, wooden backing, coloured frame with gold bolts (the text panel is a Roblox part in front)
    for sx in (-1, 1):
        rbox(body, (sx * 8, 14.8, -7), (0.8, 3.6, 0.8), WOOD2, 0.08)
    rbox(body, (0, 19, -6.6), (19.4, 5.8, 0.8), WOOD2, 0.12)
    for y in (16.15, 21.85):
        rbox(body, (0, y, -7.15), (19.8, 0.7, 1.5), col, 0.14)
    for sx in (-1, 1):
        rbox(body, (sx * 9.55, 19, -7.15), (0.7, 6.4, 1.5), col, 0.14)
        for y in (16.15, 21.85):
            rbox(body, (sx * 9.55, y, -7.95), (0.55, 0.55, 0.2), GOLD, 0.06)
        egg(body, (sx * 9.55, 23.4, -7.1), 0.95, lt, WHITE)
    # outside: crates on the left, potted bush on the right (same spots as the old block stall)
    for cx, cy, cs, cyaw in ((-13.4, 0, 3.6, 8), (-13.1, 3.6, 2.8, -14), (-13.6, 0, 2.6, 30)):
        crate(body, (cx, cy, -3 + (4.2 if cs == 2.6 else 0)), cs, cyaw)
    rcyl(body, (13.4, 1.1, -3), 1.5, 2.2, (206, 110, 70), segs=10, r2=1.8)
    rcyl(body, (13.4, 2.45, -3), 1.95, 0.5, (226, 130, 86), segs=10)
    for dx, dy, dz, rr in ((0, 4.3, 0, 2.1), (-0.9, 5.6, 0.4, 1.4), (0.9, 5.4, -0.5, 1.5), (0, 6.6, 0, 1.1)):
        rball(body, (13.4 + dx, dy, -3 + dz), rr, (74, 176, 70), segs=10, rings=7)
    for dx, dy, dz in ((1.6, 5.2, -1.8), (-1.5, 6.0, -1.2), (0.4, 7.2, -0.9)):
        rball(body, (13.4 + dx, dy, -3 + dz), 0.35, lt, segs=6, rings=4)
    mascot(body, neon, col)
    return body, neon


# ---------------------------------------------------------------- mascots on top of each sign
def m_basket(b, n, col):
    y, z = 22.4, -7
    rcyl(b, (0, y + 1.3, z), 2.4, 2.6, (214, 140, 60), segs=12, r2=3.1)
    for k in range(3):
        rcyl(b, (0, y + 0.45 + k * 0.85, z), 2.5 + 0.22 * k + 0.12, 0.22, (160, 96, 36), segs=12)
    rcyl(b, (0, y + 2.65, z), 3.25, 0.35, (230, 168, 90), segs=12)
    for k in range(9):                                       # handle: an arc of small blocks
        a = math.radians(10 + 160 * k / 8)
        rbox(b, (2.9 * math.cos(a), y + 2.7 + 3.0 * math.sin(a), z), (0.6, 0.6, 0.6), (190, 120, 50), 0.08, rz=math.degrees(a))
    for k, (dx, dz) in enumerate(((-1.2, 0.2), (1.1, -0.3), (0, 0.9), (0.2, -0.9))):
        egg(b, (dx, y + 3.2, z + dz), 0.8, RAINBOW[k * 2 % 7], WHITE)


def m_clover(b, n, col):
    y, z = 25.4, -7
    g, g2 = (80, 200, 90), (120, 230, 120)
    rbox(b, (0.8, y - 2.4, z), (0.5, 3.4, 0.5), (60, 150, 60), 0.1, rz=-18)
    for dx, dy in ((-1.3, 1.3), (1.3, 1.3), (-1.3, -1.3), (1.3, -1.3)):
        rball(b, (dx, y + dy, z), 1.55, g, (1, 1, 0.45), 12, 8)
        rball(b, (dx * 0.8 - 0.3, y + dy * 0.8 + 0.3, z - 0.55), 0.45, g2, (1, 1, 0.4), 8, 5)
    rball(b, (0, y, z), 0.9, shade(g, 0.85), (1, 1, 0.5), 10, 6)
    for dx, dy in ((-3.6, 2.4), (3.4, 2.8), (3.8, -1.2)):
        for rz in (0, 45):
            rbox(n, (dx, y + dy, z), (0.9, 0.24, 0.24), (255, 246, 170), 0.04, rz=rz)
            rbox(n, (dx, y + dy, z), (0.24, 0.9, 0.24), (255, 246, 170), 0.04, rz=rz)


def m_coins(b, n, col):
    y, z = 22.4, -7
    for sx, h in ((-2.4, 4), (2.6, 6), (0.4, 3)):
        for k in range(h):
            rcyl(b, (sx + (k % 2) * 0.1, y + 0.2 + k * 0.42, z + 0.8), 1.0, 0.36, GOLD if k % 2 == 0 else (240, 176, 30), segs=12)
    rcyl(b, (0, y + 3.0, z - 0.2), 2.2, 0.55, GOLD, axis='Z', segs=16)               # big standing coin
    rcyl(b, (0, y + 3.0, z - 0.5), 1.55, 0.1, (232, 160, 20), axis='Z', segs=16)
    rbox(b, (0, y + 3.0, z - 0.6), (0.5, 2.0, 0.12), (255, 236, 140), 0.04)
    rbox(b, (0, y + 3.5, z - 0.6), (1.3, 0.4, 0.12), (255, 236, 140), 0.04)
    rbox(b, (0, y + 2.5, z - 0.6), (1.3, 0.4, 0.12), (255, 236, 140), 0.04)
    for dx, dy in ((-2.9, 4.6), (2.8, 5.0)):
        for rz in (0, 45):
            rbox(n, (dx, y + dy, z), (0.9, 0.24, 0.24), (255, 246, 170), 0.04, rz=rz)
            rbox(n, (dx, y + dy, z), (0.24, 0.9, 0.24), (255, 246, 170), 0.04, rz=rz)


def m_book(b, n, col):
    y, z = 23.2, -7.2
    cover = (100, 90, 230)
    for sx in (-1, 1):
        rbox(b, (sx * 2.0, y + 0.2, z), (4.2, 0.4, 3.6), cover, 0.1, rz=sx * 14)
        rbox(b, (sx * 1.95, y + 0.65, z), (3.8, 0.55, 3.2), CREAM, 0.08, rz=sx * 14)
        for k in range(3):
            rbox(b, (sx * 2.0, y + 0.98 + sx * 0.0, z - 0.9 + k * 0.9), (2.6, 0.04, 0.14), (190, 180, 220), 0, rz=sx * 14)
    rbox(b, (0, y + 0.3, z), (0.5, 0.6, 3.6), shade(cover, 0.75), 0.08)
    rbox(b, (0.6, y - 0.6, z - 1.6), (0.4, 1.8, 0.1), (240, 70, 90), 0.02)                # bookmark
    egg(b, (-3.0, y + 2.6, z), 0.8, (160, 100, 250), GOLD)
    egg(b, (3.0, y + 2.6, z), 0.8, (60, 200, 230), WHITE)
    for dx, dy in ((0, 4.2),):
        for rz in (0, 45):
            rbox(n, (dx, y + dy, z), (1.1, 0.28, 0.28), (255, 246, 170), 0.04, rz=rz)
            rbox(n, (dx, y + dy, z), (0.28, 1.1, 0.28), (255, 246, 170), 0.04, rz=rz)


SHOPS = [('Baskets', (255, 150, 40), m_basket), ('Luck', (70, 200, 90), m_clover),
         ('Sell', (255, 204, 40), m_coins), ('Index', (120, 110, 250), m_book)]

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

objs, neons = [], []
for i, (key, col, mascot) in enumerate(SHOPS):
    body, neon = stall(key, col, mascot)
    loc = (i * 34, 0, 0)
    objs.append(body.finish('Shop_' + key, loc))
    o = neon.finish('ShopNeon_' + key, loc)
    objs.append(o)
    neons.append(o)

pm_path = HERE.parent / 'game' / 'props_meta.json'
pm = json.loads(pm_path.read_text(encoding='utf-8')) if pm_path.exists() else {}
pm.update(META)
pm_path.write_text(json.dumps(pm, indent=1), encoding='utf-8')
tris = {o.name: len(o.data.polygons) for o in objs}
print('triangles:', tris)

if 'nofbx' not in ARGS:
    for o in bpy.data.objects:
        o.select_set(o in objs)
    bpy.context.view_layer.objects.active = objs[0]
    fbx = OUT / 'RainingEggsShops.fbx'
    bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, object_types={'MESH'}, apply_scale_options='FBX_SCALE_UNITS',
                             mesh_smooth_type='FACE', colors_type='SRGB', add_leaf_bones=False, bake_anim=False)
    desk = pathlib.Path(os.environ['USERPROFILE']) / 'Desktop' / 'RAINING EGGS NOU' / fbx.name
    shutil.copyfile(fbx, desk)
    print('wrote', fbx.stat().st_size // 1024, 'KB ->', desk)

# ---------------------------------------------------------------- preview renders
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE_NEXT'
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
bmesh.ops.create_grid(gb, x_segments=1, y_segments=1, size=400)
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
try:
    sc.eevee.use_shadows = True
    sc.eevee.use_raytracing = False
except Exception:
    pass


def shot(name, cx, dist, h, tz, res=(1400, 1050), side=0.55):
    tgt = Vector((cx, 0, tz))
    cam.location = Vector((cx + dist * side, dist, h))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = str(OUT / f'shop_{name}.png')
    bpy.ops.render.render(write_still=True)


if 'norender' not in ARGS:
    for i, (key, _, _) in enumerate(SHOPS):
        shot(key, i * 34, 50, 22, 13)
    shot('all', 51, 115, 48, 8, (1800, 900), 0.15)
