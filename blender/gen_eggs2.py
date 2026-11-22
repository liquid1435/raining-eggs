"""Raining Eggs - new themed eggs (v2): one smooth egg per zone + Gold / Rotten / Storm, vertex coloured, with 3D decor.
  blender -b -P gen_eggs2.py -- [nofbx] [norender]
Names stay Egg_1..Egg_10, Egg_Gold, Egg_Rotten, Egg_Storm (the game picks them up after import + harvest_meshes.py).
Renders -> out/eggs2_*.png, FBX -> RainingEggsEggs2.fbx (+ copy on the Desktop/RAINING EGGS NOU)."""
import bpy, bmesh, math, random, sys, pathlib, os, shutil
from mathutils import Vector, Matrix, Euler

HERE = pathlib.Path(__file__).resolve().parent
ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
R, TOP = 1.5, 1.38
WHITE = (255, 255, 255)


def lin(c):
    f = lambda v: v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (f(c[0] / 255), f(c[1] / 255), f(c[2] / 255), 1.0)


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def mix(c, d, k):
    k = max(0.0, min(1.0, k))
    return tuple(int(a + (b - a) * k) for a, b in zip(c, d))


def tri(x):  # triangle wave -1..1
    x = x / (2 * math.pi)
    return 4 * abs(x - math.floor(x + 0.5)) - 1


def unit(th, t):
    s = math.sqrt(max(0.0, 1 - t * t))
    return Vector((math.cos(th) * s, math.sin(th) * s, t))


def angd(a, b):  # angle between two unit vectors
    return math.acos(max(-1.0, min(1.0, a.dot(b))))


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


LIGHT = Vector((-0.45, -0.55, 0.7)).normalized()  # cartoon highlight, upper left front


TW, TH, SHELL_V = 1024, 1024, 0.875   # texture: shell in v 0..0.875, colour swatches in the strip above


class Egg:
    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UV')
        self.ribs = 0.0
        self.swatch = {}
        self.pattern = None
        self.shine = True

    def sw(self, c):
        """uv of a solid colour swatch (decor parts)"""
        c = tuple(int(v) for v in c)
        if c not in self.swatch:
            self.swatch[c] = len(self.swatch)
        i = self.swatch[c]
        return ((i % 32) * 32 + 16) / TW, (SHELL_V * TH + (i // 32) * 32 + 16) / TH

    def face_col(self, f, c):
        u, v = self.sw(c)
        for l in f.loops:
            l[self.uv].uv = (u, v)

    def shell_col(self, th, t):
        c = unit(th, t)
        col = self.pattern(th, t, c)
        col = shade(col, 0.86 + 0.14 * (t + 1) / 2)
        if self.shine:
            d = c.dot(LIGHT)
            if d > 0.955:
                col = mix(col, WHITE, 0.75)
            elif d > 0.935:
                col = mix(col, WHITE, 0.75 * (d - 0.935) / 0.02)
        return col

    # --- the egg itself
    def deform(self, u, ribs=None):
        ribs = self.ribs if ribs is None else ribs
        th = math.atan2(u.y, u.x)
        r = R * (1 + ribs * math.cos(8 * th) * math.sqrt(max(0, 1 - u.z * u.z)))
        k = 1 - 0.12 * u.z * u.z if u.z > 0 else 1.0
        return Vector((u.x * r * k, u.y * r * k, u.z * R * (TOP if u.z > 0 else 1.0)))

    def shell(self, pattern, seg=72, rings=44, flat=False, shine=True, ribs=0.0):
        self.ribs = ribs
        vs = bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=rings, radius=1)['verts']
        un = {v: v.co.normalized() for v in vs}
        for v in vs:
            v.co = self.deform(un[v])
        self.pattern, self.shine = pattern, shine
        for f in {f for v in vs for f in v.link_faces}:
            f.smooth = not flat
            fc = sum((un[v] for v in f.verts), Vector()).normalized()
            fth = math.atan2(fc.y, fc.x)
            uvs = []
            for l in f.loops:
                u3 = un[l.vert]
                th = math.atan2(u3.y, u3.x) if abs(u3.z) < 0.999 else fth
                uu = (th + math.pi) / math.tau
                uvs.append([uu, (math.asin(max(-1, min(1, u3.z))) + math.pi / 2) / math.pi * SHELL_V])
            us = [a[0] for a in uvs]
            if max(us) - min(us) > 0.5:  # face across the seam
                for a in uvs:
                    if a[0] < 0.5:
                        a[0] += 1
            for l, a in zip(f.loops, uvs):
                l[self.uv].uv = a

    def surf(self, th, t, off=0.0):
        u = unit(th, t)
        p = self.deform(u)
        n = Vector((p.x / R ** 2, p.y / R ** 2, p.z / (R * (TOP if u.z > 0 else 1.0)) ** 2)).normalized()
        return p + n * off, n

    # --- decor primitives (flat vertex colour)
    def paint(self, verts, c, smooth=True):
        for f in {f for v in verts for f in v.link_faces}:
            f.smooth = smooth
            self.face_col(f, c)

    @staticmethod
    def M(loc, sc=(1, 1, 1), rot=(0, 0, 0), normal=None):
        r = normal.to_track_quat('Z', 'Y').to_matrix().to_4x4() if normal is not None else Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()
        if normal is not None and rot != (0, 0, 0):
            r = r @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()
        return Matrix.Translation(loc) @ r @ Matrix.Diagonal((*sc, 1))

    def sph(self, loc, r, c, rot=(0, 0, 0), seg=16, normal=None, smooth=True):
        r = r if isinstance(r, tuple) else (r, r, r)
        vs = bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=max(6, seg * 5 // 8), radius=1, matrix=self.M(loc, r, rot, normal))['verts']
        self.paint(vs, c, smooth)

    def cone(self, loc, r1, r2, h, c, rot=(0, 0, 0), seg=12, sc=(1, 1, 1), normal=None, smooth=False):
        vs = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r1, radius2=r2, depth=h, matrix=self.M(loc, sc, rot, normal))['verts']
        self.paint(vs, c, smooth)

    def gem(self, loc, r, h, c, normal=None, rot=(0, 0, 0), seg=6):
        """cut gem: wide crown + pointed pavilion, flat shaded"""
        bm = self.bm
        m = self.M(loc, (1, 1, 1), rot, normal)
        top = [bm.verts.new(m @ Vector((r * 0.6 * math.cos(a), r * 0.6 * math.sin(a), h * 0.35))) for a in [k * math.tau / seg for k in range(seg)]]
        mid = [bm.verts.new(m @ Vector((r * math.cos(a), r * math.sin(a), 0))) for a in [(k + 0.5) * math.tau / seg for k in range(seg)]]
        tip = bm.verts.new(m @ Vector((0, 0, -h * 0.65)))
        fs = [bm.faces.new(top)]
        for k in range(seg):
            fs.append(bm.faces.new((top[k], mid[k], top[(k + 1) % seg])))
            fs.append(bm.faces.new((top[(k + 1) % seg], mid[k], mid[(k + 1) % seg])))
            fs.append(bm.faces.new((mid[k], tip, mid[(k + 1) % seg])))
        fs[0].normal_flip()
        bmesh.ops.recalc_face_normals(bm, faces=fs)
        self.paint(top + mid + [tip], c, False)
        for f in fs[1::3]:  # lighter crown facets
            self.face_col(f, mix(c, WHITE, 0.45))

    def star(self, loc, r, depth, c, normal=None, rot=(0, 0, 0), points=5):
        bm = self.bm
        m = self.M(loc, (1, 1, 1), rot, normal)
        ring = []
        for k in range(points * 2):
            a = math.pi / 2 + k * math.pi / points
            rr = r if k % 2 == 0 else r * 0.45
            ring.append((rr * math.cos(a), rr * math.sin(a)))
        f_ = [bm.verts.new(m @ Vector((x, y, depth))) for x, y in ring]
        b_ = [bm.verts.new(m @ Vector((x, y, -depth * 0.3))) for x, y in ring]
        cf = bm.verts.new(m @ Vector((0, 0, depth * 1.6)))     # puffy front
        cb = bm.verts.new(m @ Vector((0, 0, -depth * 0.3)))
        n = len(ring)
        fs = []
        for k in range(n):
            j = (k + 1) % n
            fs.append(bm.faces.new((cf, f_[k], f_[j])))
            fs.append(bm.faces.new((cb, b_[j], b_[k])))
            fs.append(bm.faces.new((f_[k], b_[k], b_[j], f_[j])))
        bmesh.ops.recalc_face_normals(bm, faces=fs)
        self.paint(f_ + b_ + [cf, cb], c, False)

    def torus(self, loc, R1, r2, c, rot=(0, 0, 0), seg=40, segr=10, normal=None, wobble=None):
        bm = self.bm
        m = self.M(loc, (1, 1, 1), rot, normal)
        grid = []
        for i in range(seg):
            a = i * math.tau / seg
            rr = r2 * (wobble(a) if wobble else 1)
            row = []
            for j in range(segr):
                b = j * math.tau / segr
                row.append(bm.verts.new(m @ Vector(((R1 + rr * math.cos(b)) * math.cos(a), (R1 + rr * math.cos(b)) * math.sin(a), rr * math.sin(b)))))
            grid.append(row)
        fs = []
        for i in range(seg):
            for j in range(segr):
                fs.append(bm.faces.new((grid[i][j], grid[(i + 1) % seg][j], grid[(i + 1) % seg][(j + 1) % segr], grid[i][(j + 1) % segr])))
        bmesh.ops.recalc_face_normals(bm, faces=fs)
        self.paint([v for r in grid for v in r], c, True)

    def leaf(self, loc, size, c, normal, rot=(0, 0, 0)):
        self.sph(loc, (size * 0.42, size * 0.13, size), c, rot=rot, normal=normal, seg=14)

    def texture(self, name):
        import numpy as np
        px = np.zeros((TH, TW, 4), dtype=np.float32)
        px[..., 3] = 1
        rows = int(SHELL_V * TH)
        for j in range(rows):
            t = math.sin(((j + 0.5) / rows) * math.pi - math.pi / 2)
            for i in range(TW):
                th = ((i + 0.5) / TW) * math.tau - math.pi
                px[j, i, :3] = lin(self.shell_col(th, t))[:3]
        for c, k in self.swatch.items():
            x0, y0 = (k % 32) * 32, rows + (k // 32) * 32
            px[y0:y0 + 32, x0:x0 + 32, :3] = lin(c)[:3]
        img = bpy.data.images.new('Tex_' + name, TW, TH)
        img.pixels.foreach_set(px.ravel())
        img.filepath_raw = str(HERE / 'out' / 'eggtex' / f'{name}.png')
        img.file_format = 'PNG'
        img.save()
        m = bpy.data.materials.new('M_' + name)
        m.use_nodes = True
        b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        b.inputs['Roughness'].default_value = 0.32
        tn = m.node_tree.nodes.new('ShaderNodeTexImage')
        tn.image = img
        m.node_tree.links.new(tn.outputs['Color'], b.inputs['Base Color'])
        return m

    def finish(self, name, x, y, mat):
        mat = self.texture(name)
        bm = self.bm
        zmin = min(v.co.z for v in bm.verts)
        bmesh.ops.translate(bm, vec=(0, 0, -zmin), verts=bm.verts)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(name, me)
        ob.location = (x, y, 0)
        bpy.context.scene.collection.objects.link(ob)
        me.materials.append(mat)
        return ob


# ======================================================================= the eggs
def dots(c, centres, rad):
    return any(angd(c, d) < rad for d in centres)


def fib(n, tmin=-1.0, tmax=1.0, seed=0):
    rng = random.Random(seed)
    out = []
    for k in range(n):
        t = tmin + (tmax - tmin) * (k + 0.5) / n
        th = k * 2.39996 + rng.uniform(-0.25, 0.25)
        out.append(unit(th, t))
    return out


def egg_meadow():  # 1 Sunny Meadow: cream, green zig-zag grass band, yellow dots, sprout + daisy on top
    e = Egg()
    CREAM, GRASS, GRASS2, SUN = (252, 244, 220), (110, 200, 80), (70, 160, 60), (255, 214, 70)
    sp = fib(14, 0.35, 0.9, 1)

    def pat(th, t, c):
        g = -0.38 + 0.13 * tri(th * 9)
        if t < g:
            return GRASS2 if t < g - 0.22 else GRASS
        if dots(c, sp, 0.13):
            return SUN
        return CREAM
    e.shell(pat)
    tip, n = e.surf(0, 1)
    e.cone(tip + Vector((0, 0, 0.15)), 0.09, 0.07, 0.4, (90, 170, 60), seg=8, smooth=True)
    for s in (-1, 1):
        e.leaf(tip + Vector((s * 0.42, 0, 0.32)), 0.55, GRASS, None, rot=(0, s * 62, 0))
    # daisy on the side
    p, n = e.surf(-1.1, 0.25, 0.02)
    for k in range(8):
        a = k * math.tau / 8
        e.sph(p + (Matrix.Rotation(a, 3, n) @ n.orthogonal().normalized()) * 0.28, (0.2, 0.1, 0.06), WHITE, normal=n, rot=(0, 0, math.degrees(a)), seg=10)
    e.sph(p + n * 0.05, (0.16, 0.16, 0.09), SUN, normal=n, seg=12)
    return e


def egg_mushroom():  # 2 Mushroom Grove: purple cap with white dots over a cream stem, tiny mushrooms at the base
    e = Egg()
    CAP, CAP2, STEM, DOT = (175, 105, 255), (130, 70, 220), (252, 238, 222), (255, 255, 255)
    sp = fib(10, 0.3, 0.95, 2)

    def pat(th, t, c):
        edge = 0.12 + 0.07 * math.cos(th * 6)
        if t > edge:
            if dots(c, sp, 0.17):
                return DOT
            return CAP if t > edge + 0.06 else CAP2
        return STEM if t > -0.7 else (236, 214, 200)
    e.shell(pat)
    for k, th in enumerate((-1.9, -0.9, 0.4)):
        p, n = e.surf(th, -0.78, -0.05)
        s = 0.8 + 0.25 * k
        base = Vector((p.x * 1.18, p.y * 1.18, 0.0 - R + 0.18 * s))
        e.cone(base, 0.12 * s, 0.1 * s, 0.4 * s, STEM, seg=10, smooth=True)
        e.sph(base + Vector((0, 0, 0.25 * s)), (0.3 * s, 0.3 * s, 0.17 * s), (255, 90, 120) if k % 2 else CAP, seg=14)
        e.sph(base + Vector((0.12 * s, -0.12 * s, 0.37 * s)), 0.05 * s, DOT, seg=8)
    return e


def egg_candy():  # 3 Candy Canyon: swirl stripes, white icing drips, sprinkles, cherry
    e = Egg()
    PINK, HOT, ICE = (255, 160, 195), (255, 95, 160), (255, 252, 250)

    def pat(th, t, c):
        drip = 0.38 - 0.3 * max(0.0, math.cos(th * 7)) ** 6 - 0.08 * max(0.0, math.cos(th * 7 + 1.3)) ** 8
        if t > drip:
            return ICE
        return HOT if math.sin(th * 5 + t * 7) > 0.25 else PINK
    e.shell(pat)
    rng = random.Random(3)
    cols = [(255, 80, 80), (80, 190, 255), (255, 220, 60), (120, 220, 90), (190, 120, 255)]
    for k in range(26):
        th, t = rng.uniform(-math.pi, math.pi), rng.uniform(0.5, 0.93)
        p, n = e.surf(th, t, 0.02)
        e.sph(p, (0.045, 0.14, 0.045), cols[k % len(cols)], normal=n, rot=(90, 0, rng.uniform(0, 180)), seg=8)
    tip, n = e.surf(0, 1)
    e.sph(tip + Vector((0, 0, 0.3)), 0.32, (230, 30, 60), seg=18)
    e.sph(tip + Vector((-0.1, -0.13, 0.42)), 0.07, (255, 170, 180), seg=8)
    e.cone(tip + Vector((0.1, 0, 0.75)), 0.035, 0.03, 0.55, (90, 160, 60), rot=(0, 20, 0), seg=6)
    return e


def egg_toy():  # 4 Toy Town: red with blue band + yellow dots, yellow cap, 3D stars, wind-up key
    e = Egg()
    RED, BLUE, YEL = (240, 64, 64), (60, 135, 255), (255, 214, 50)
    bd = [unit(k * math.tau / 10, -0.05) for k in range(10)]

    def pat(th, t, c):
        if t > 0.74:
            return YEL
        if abs(t + 0.05) < 0.15:
            return YEL if dots(c, bd, 0.07) else BLUE
        if abs(t + 0.05) < 0.19:
            return WHITE
        return RED
    e.shell(pat)
    for th, t in ((-1.5, 0.42), (-0.6, -0.5), (2.0, 0.35), (0.9, -0.5)):
        p, n = e.surf(th, t, 0.02)
        e.star(p, 0.34, 0.07, YEL, normal=n)
    p, n = e.surf(math.pi / 2, 0.1, 0.0)   # key at the back
    e.cone(p + n * 0.25, 0.08, 0.08, 0.5, (190, 190, 205), normal=n, seg=10, smooth=True)
    for s in (-1, 1):
        side = n.cross(Vector((0, 0, 1))).normalized()
        e.sph(p + n * 0.55 + side * s * 0.3, (0.3, 0.07, 0.22), (200, 200, 215), normal=n, rot=(90, 0, 0), seg=14)
    return e


def egg_crystal():  # 5 Crystal Coast: faceted aqua gem egg with crystal shards
    e = Egg()
    DEEP, LIGHT_, ICE = (30, 140, 230), (110, 225, 255), (210, 250, 255)

    def pat(th, t, c):
        k = (t + 1) / 2
        base = mix(DEEP, LIGHT_, k)
        f = math.sin(th * 7) * math.cos(t * 9)
        return mix(base, ICE, 0.45) if f > 0.55 else base
    e.shell(pat, seg=18, rings=12, flat=True)
    rng = random.Random(5)
    for k in range(11):  # cluster round the bottom, leaning out and up
        a = k * math.tau / 11 + rng.uniform(-0.15, 0.15)
        h = rng.uniform(0.7, 1.25)
        c = (150, 120, 255) if k % 3 == 0 else (100, 235, 255)
        base = Vector((1.05 * math.cos(a), 1.05 * math.sin(a), -R + 0.25))
        d = Vector((math.cos(a) * 0.55, math.sin(a) * 0.55, 1)).normalized()
        e.cone(base + d * h * 0.5, 0.2, 0.0, h, c, normal=d, seg=6)
    tip, n = e.surf(0, 1)
    for k in range(5):  # crown
        a = k * math.tau / 5
        d = Vector((math.cos(a) * 0.4, math.sin(a) * 0.4, 1)).normalized() if k else Vector((0, 0, 1))
        h = 0.9 if k == 0 else 0.6
        c = (210, 250, 255) if k == 0 else (150, 120, 255)
        e.cone(tip + Vector((0.25 * math.cos(a), 0.25 * math.sin(a), -0.2)) * (1 if k else 0) + d * h * 0.45, 0.17, 0.0, h, c, normal=d, seg=6)
    return e


def egg_spooky():  # 6 Spooky Hollow: pumpkin with a glowing jack-o-lantern face, stem and leaf
    e = Egg()
    OR, OR2, GLOW, STEM = (255, 140, 30), (210, 90, 20), (255, 236, 110), (100, 120, 50)
    F = -math.pi / 2  # face looks to -Y

    def pat(th, t, c):
        u, v = wrap(th - F), t
        for s in (-1, 1):  # eyes: triangles
            du, dv = u - s * 0.36, v - 0.24
            if -0.1 < dv < 0.12 and abs(du) < 0.16 * (0.12 - dv) / 0.22:
                return GLOW
        if abs(u) < 0.07 and -0.02 < v < 0.08 and abs(u) < 0.07 * (0.08 - v) / 0.1:
            return GLOW  # nose
        if abs(u) < 0.5:  # smile: between two curves, with two square teeth
            top = -0.13 - 0.12 * (1 - (u / 0.5) ** 2) + 0.02
            bot = -0.2 - 0.16 * (1 - (u / 0.5) ** 2)
            if bot < v < top and not (0.12 < abs(u) < 0.24 and v > top - 0.07):
                return GLOW
        k = (math.cos(th * 8) + 1) / 2
        return mix(OR2, OR, k ** 0.5)
    e.shell(pat, ribs=0.045)
    tip, n = e.surf(0, 1)
    e.cone(tip + Vector((0.05, 0, 0.2)), 0.16, 0.09, 0.5, STEM, rot=(0, 14, 0), seg=8)
    e.leaf(tip + Vector((-0.35, 0.1, 0.12)), 0.45, (90, 170, 60), None, rot=(0, -70, 30))
    return e


def egg_thunder():  # 7 Thunder Peaks: navy egg, yellow bolts, storm cloud cap
    e = Egg()
    NAVY, NAVY2, YEL, CLOUD = (34, 42, 84), (24, 28, 58), (255, 226, 60), (150, 160, 200)

    def pat(th, t, c):
        for k in range(3):
            u = wrap(th - k * math.tau / 3)
            line = 0.16 * tri(t * 11) + 0.08 * t
            if abs(u - line) < 0.085 and t < 0.62 and t > -0.75:
                return YEL
        return NAVY if math.sin(th * 3 + t * 4) > 0 else NAVY2
    e.shell(pat)
    tip, n = e.surf(0, 1)
    for k in range(7):
        a = k * math.tau / 7
        e.sph(tip + Vector((0.55 * math.cos(a), 0.55 * math.sin(a), -0.45 + 0.08 * (k % 2))), 0.42, CLOUD if k % 2 else (175, 185, 220), seg=14)
    e.sph(tip + Vector((0, 0, -0.1)), 0.55, (185, 195, 230), seg=16)
    return e


def egg_neon():  # 8 Neon City: dark egg with neon grid + glowing ring
    e = Egg()
    DARK, PINK, CYAN = (32, 22, 56), (255, 60, 210), (60, 240, 255)

    def pat(th, t, c):
        if abs(math.sin(t * math.pi * 3)) < 0.12:
            return PINK
        if abs(math.sin(th * 4)) < 0.1 * (1.2 - abs(t)):
            return CYAN
        return DARK
    e.shell(pat)
    p, n = e.surf(0, 0.0)
    e.torus(Vector((0, 0, 0.05)), R * 1.2, 0.09, CYAN, rot=(12, 0, 0), seg=48)
    tip, n = e.surf(0, 1)
    e.sph(tip + Vector((0, 0, 0.12)), 0.2, PINK, seg=12)
    return e


def egg_cloud():  # 9 Cloud Kingdom: white egg, pastel band, feather wings, golden halo
    e = Egg()
    PINKP, BLUEP = (255, 190, 220), (170, 215, 255)
    sp = fib(12, -0.9, -0.35, 9)

    def pat(th, t, c):
        w = 0.05 * math.sin(th * 8)
        if abs(t - 0.05 - w) < 0.1:
            return PINKP
        if dots(c, sp, 0.12):
            return BLUEP
        return (252, 252, 255)
    e.shell(pat)
    for s in (-1, 1):
        base = Vector((s * R * 0.92, 0.25, 0.35))
        for k in range(4):
            e.sph(base + Vector((s * (0.35 + 0.22 * k), 0.1, 0.38 - 0.2 * k)), (0.42 - 0.05 * k, 0.12, 0.2), (255, 255, 255) if k % 2 == 0 else (236, 242, 255),
                  rot=(0, s * (25 + 18 * k), 0), seg=14)
    tip, n = e.surf(0, 1)
    e.torus(tip + Vector((0, 0, 0.5)), 0.62, 0.08, (255, 214, 60), rot=(8, 0, 0), seg=36)
    return e


def egg_golden_nest():  # 10 Golden Nest: gold egg, gem band, royal crown
    e = Egg()
    G1, G2 = (255, 204, 40), (240, 160, 20)

    def pat(th, t, c):
        if abs(t + 0.1) < 0.11:
            return (190, 30, 60)
        return G1 if math.sin(th * 8) * math.sin(t * 7) > 0 else G2
    e.shell(pat)
    cols = [(60, 140, 255), (60, 220, 120), (255, 255, 255)]
    for k in range(8):
        p, n = e.surf(k * math.tau / 8, -0.1, 0.03)
        e.gem(p, 0.16, 0.2, cols[k % 3], normal=-n)
    tip, n = e.surf(0, 1)
    c0 = tip + Vector((0, 0, -0.25))
    e.cone(c0 + Vector((0, 0, 0.2)), 0.72, 0.8, 0.4, G1, seg=24, smooth=True)
    for k in range(6):
        a = k * math.tau / 6
        q = c0 + Vector((0.75 * math.cos(a), 0.75 * math.sin(a), 0.55))
        e.cone(q, 0.2, 0.02, 0.45, G1, rot=(math.degrees(-0.25 * math.sin(a)), math.degrees(0.25 * math.cos(a)), 0), seg=8)
        e.sph(q + Vector((0, 0, 0.26)), 0.09, (255, 245, 180), seg=8)
        e.gem(c0 + Vector((0.8 * math.cos(a + 0.52), 0.8 * math.sin(a + 0.52), 0.2)), 0.1, 0.12, (220, 30, 70), normal=-Vector((math.cos(a + 0.52), math.sin(a + 0.52), 0)))
    return e


def egg_gold():  # Golden egg: shiny diamond-quilted gold with white diamonds
    e = Egg()
    G1, G2, G3 = (255, 214, 50), (255, 180, 20), (255, 240, 150)

    def pat(th, t, c):
        a, b = th * 8 / math.pi, t * 6
        u, v = (a + b) % 2, (a - b) % 2
        if min(u, 2 - u) < 0.12 or min(v, 2 - v) < 0.12:
            return G3
        return G1 if (math.floor(a + b) + math.floor(a - b)) % 2 == 0 else G2
    e.shell(pat)
    for k in range(6):
        p, n = e.surf(k * math.tau / 6 + 0.3, -0.05 + 0.25 * (k % 2), 0.03)
        e.gem(p, 0.2, 0.26, (225, 245, 255), normal=-n)
    tip, n = e.surf(0, 1)
    e.star(tip + Vector((0, 0, 0.35)), 0.38, 0.09, (255, 250, 210), rot=(90, 0, 0))
    return e


def egg_rotten():  # Rotten egg: olive blotches, dark cracks, slime drips, warts
    e = Egg()
    OL, OL2, CRK, SLIME = (128, 140, 70), (92, 104, 48), (48, 40, 30), (150, 220, 60)

    def pat(th, t, c):
        u = wrap(th + 0.4)
        if abs(u - 0.12 * tri(t * 13)) < 0.04 and t > -0.2:
            return CRK
        if abs(wrap(th - 2.4) - 0.1 * tri(t * 15)) < 0.035 and t < 0.4:
            return CRK
        if t < -0.62 + 0.12 * max(0, math.cos(th * 6)) ** 4:
            return SLIME
        n = math.sin(th * 3 + t * 5) + math.sin(th * 5 - t * 7) + math.sin(t * 9)
        return OL2 if n > 1.0 else OL
    e.shell(pat, shine=False)
    rng = random.Random(7)
    for k in range(12):
        p, n = e.surf(rng.uniform(-math.pi, math.pi), rng.uniform(-0.5, 0.85), -0.03)
        e.sph(p, rng.uniform(0.1, 0.18), (110, 124, 56), seg=10)
    return e


def egg_storm():  # Storm egg: violet swirl, yellow bolts, ring of dark clouds
    e = Egg()
    V1, V2, YEL = (100, 50, 200), (155, 95, 255), (255, 232, 70)

    def pat(th, t, c):
        for k in range(4):
            u = wrap(th - k * math.tau / 4)
            if abs(u - 0.15 * tri(t * 12)) < 0.07 and -0.6 < t < 0.7:
                return YEL
        return V2 if math.sin(th * 3 - t * 6) > 0.2 else V1
    e.shell(pat)
    for k in range(14):
        a = k * math.tau / 14
        r = 0.36 if k % 2 else 0.3
        e.sph(Vector((1.85 * math.cos(a), 1.85 * math.sin(a), -0.1 + 0.1 * math.sin(a * 2))), (r, r, r * 0.8), (200, 190, 240) if k % 2 else (165, 150, 220), seg=14)
    p, n = e.surf(-1.2, 0.3, 0.05)
    tip, n2 = e.surf(0, 1)
    e.star(tip + Vector((0, 0, 0.3)), 0.32, 0.08, YEL, rot=(90, 0, 0), points=4)
    return e


# ======================================================================= v208: WORLD 2 eggs (zones 11-20, space)
def starry(c, base, density=0.06, col=(255, 255, 255), seed=1):
    """sparse star dots on the shell: deterministic from the direction"""
    h = math.sin(c.x * 127.1 + c.y * 311.7 + c.z * 74.7 + seed) * 43758.5453
    return col if (h - math.floor(h)) < density else base


def egg_cosmic_nest():  # 11 Cosmic Nest: deep violet night sky, pink nebula band, stars, cyan ring, gold star on top
    e = Egg()
    V1, V2, PINK = (52, 30, 120), (90, 50, 180), (255, 110, 220)

    def pat(th, t, c):
        band = math.sin(th * 2 + t * 5)
        base = mix(V1, V2, (t + 1) / 2)
        if abs(t - 0.15 * math.sin(th * 3)) < 0.16:
            base = mix(base, PINK, 0.6 + 0.3 * band)
        return starry(c, base, 0.07, (255, 250, 210), 3)
    e.shell(pat)
    e.torus(Vector((0, 0, -0.1)), R * 1.22, 0.07, (90, 230, 255), rot=(14, 6, 0), seg=56)
    for k in range(5):
        a = k * math.tau / 5 + 0.4
        q = Vector((R * 1.22 * math.cos(a), R * 1.22 * math.sin(a), -0.1 + 0.3 * math.sin(a)))
        e.star(q, 0.16, 0.06, (255, 230, 120), rot=(90, 0, math.degrees(a)), points=5)
    tip, n = e.surf(0, 1)
    e.star(tip + Vector((0, 0, 0.32)), 0.4, 0.1, (255, 214, 60), rot=(90, 0, 0), points=5)
    return e


def egg_moon_craters():  # 12 Moon Craters: grey moon with dark craters, crater rims, little crescent moon on top
    e = Egg()
    G1, G2, DARKG = (196, 200, 214), (160, 165, 182), (110, 114, 132)
    craters = fib(14, -0.85, 0.8, 12)

    def pat(th, t, c):
        for k, d in enumerate(craters):
            r = 0.2 + 0.08 * (k % 3)
            a = angd(c, d)
            if a < r * 0.7:
                return DARKG
            if a < r:
                return G1
        return G1 if math.sin(th * 5 + t * 3) > 0 else G2
    e.shell(pat)
    for d in craters[:8]:  # raised rims of the big craters
        p, n = e.surf(math.atan2(d.y, d.x), d.z, 0.0)
        e.torus(p, 0.2, 0.05, (210, 214, 228), normal=n, seg=20, segr=6)
    tip, n = e.surf(0, 1)
    e.sph(tip + Vector((0, 0, 0.42)), 0.38, (255, 236, 150), seg=18)
    e.sph(tip + Vector((0.16, 0, 0.5)), 0.33, (196, 200, 214), seg=18)   # bites the crescent out
    return e


def egg_nebula_reef():  # 13 Nebula Reef: teal to pink waves, glowing bubbles, a starfish
    e = Egg()
    TEAL, PINK, LIGHT2 = (40, 190, 200), (255, 120, 210), (190, 255, 245)

    def pat(th, t, c):
        w = math.sin(th * 4 + t * 7) * 0.12
        k = min(1, max(0, (t + w + 1) / 2))
        base = mix(TEAL, PINK, k)
        return mix(base, LIGHT2, 0.5) if abs(math.sin((t + w) * 9)) < 0.12 else base
    e.shell(pat)
    rng = random.Random(13)
    for k in range(9):
        th, t = rng.uniform(-math.pi, math.pi), rng.uniform(-0.6, 0.8)
        p, n = e.surf(th, t, 0.04)
        e.sph(p, rng.uniform(0.09, 0.18), (200, 250, 255), seg=12)
    p, n = e.surf(1.2, 0.05, 0.03)
    e.star(p, 0.42, 0.1, (255, 150, 90), normal=n, points=5)
    tip, n = e.surf(0, 1)
    e.sph(tip + Vector((0, 0, 0.2)), 0.22, (190, 255, 245), seg=12)
    return e


def egg_asteroid_belt():  # 14 Asteroid Belt: rocky brown-grey egg with an orbit of little rocks
    e = Egg()
    R1, R2, R3 = (140, 120, 104), (104, 92, 84), (180, 160, 140)

    def pat(th, t, c):
        f = math.sin(th * 6 + math.sin(t * 5) * 2) * math.cos(t * 8 + th)
        return R3 if f > 0.6 else (R1 if f > -0.2 else R2)
    e.shell(pat, seg=24, rings=16, flat=True)
    rng = random.Random(14)
    for k in range(16):
        a = k * math.tau / 16 + rng.uniform(-0.1, 0.1)
        rr = R * 1.3 + rng.uniform(-0.1, 0.12)
        q = Vector((rr * math.cos(a), rr * math.sin(a), 0.15 * math.sin(a * 2)))
        s_ = rng.uniform(0.1, 0.22)
        e.gem(q, s_, s_ * 1.3, (rng.choice((150, 125, 175)),) * 3, normal=Vector((math.cos(a), math.sin(a), 0.4)).normalized(), seg=5)
    tip, n = e.surf(0, 1)
    e.gem(tip + Vector((0, 0, 0.2)), 0.3, 0.45, (255, 190, 90), seg=6)
    return e


def egg_solar_forge():  # 15 Solar Forge: dark rock with glowing lava cracks, flame on top
    e = Egg()
    ROCK, ROCK2, LAVA, HOT = (60, 34, 30), (84, 46, 36), (255, 110, 20), (255, 220, 80)

    def pat(th, t, c):
        crack = abs(math.sin(th * 5 + math.sin(t * 6) * 1.4)) * abs(math.sin(t * 7 + th * 2))
        if crack < 0.08:
            return HOT
        if crack < 0.18:
            return LAVA
        return ROCK if math.sin(th * 3 + t * 9) > 0 else ROCK2
    e.shell(pat)
    tip, n = e.surf(0, 1)
    e.cone(tip + Vector((0, 0, 0.35)), 0.42, 0.0, 0.9, (255, 120, 30), seg=10)
    e.cone(tip + Vector((0, 0, 0.3)), 0.26, 0.0, 0.7, (255, 220, 80), seg=10)
    for k in range(4):
        a = k * math.tau / 4
        e.cone(tip + Vector((0.32 * math.cos(a), 0.32 * math.sin(a), 0.1)), 0.16, 0.0, 0.45, (255, 150, 40),
               rot=(math.degrees(-0.4 * math.sin(a)), math.degrees(0.4 * math.cos(a)), 0), seg=8)
    return e


def egg_comet_glacier():  # 16 Comet Glacier: icy blue with frost bands, ice crystals around the top
    e = Egg()
    ICE1, ICE2, FROST = (150, 210, 255), (100, 170, 240), (235, 250, 255)

    def pat(th, t, c):
        if abs(math.sin(t * 6 + math.sin(th * 5) * 0.6)) < 0.14:
            return FROST
        return starry(c, mix(ICE2, ICE1, (t + 1) / 2), 0.05, FROST, 7)
    e.shell(pat)
    tip, n = e.surf(0, 1)
    for k in range(6):
        a = k * math.tau / 6
        d = Vector((math.cos(a) * 0.45, math.sin(a) * 0.45, 1)).normalized()
        e.cone(tip + Vector((0.3 * math.cos(a), 0.3 * math.sin(a), -0.25)) + d * 0.3, 0.14, 0.0, 0.65, (210, 245, 255), normal=d, seg=6)
    e.cone(tip + Vector((0, 0, 0.45)), 0.18, 0.0, 0.95, (240, 252, 255), seg=6)
    return e


def egg_alien_jungle():  # 17 Alien Jungle: lime egg with purple spots, alien leaves, antennae with glowing balls
    e = Egg()
    LIME, LIME2, PURP = (130, 230, 70), (90, 190, 60), (170, 80, 230)
    sp = fib(16, -0.9, 0.75, 17)

    def pat(th, t, c):
        if dots(c, sp, 0.2):
            return PURP
        return LIME if math.sin(th * 7) * math.sin(t * 6) > 0 else LIME2
    e.shell(pat)
    for k in range(5):
        a = k * math.tau / 5
        p, n = e.surf(a, -0.75, 0.02)
        e.leaf(p, 0.75, (60, 170, 120) if k % 2 else (200, 90, 240), n, rot=(0, 0, math.degrees(a)))
    tip, n = e.surf(0, 1)
    for sx in (-1, 1):
        q = tip + Vector((sx * 0.25, 0, -0.05))
        e.cone(q + Vector((sx * 0.1, 0, 0.35)), 0.05, 0.04, 0.7, (90, 190, 60), rot=(0, sx * 15, 0), seg=8)
        e.sph(q + Vector((sx * 0.2, 0, 0.75)), 0.14, (255, 120, 240), seg=12)
    return e


def egg_black_hole():  # 18 Black Hole: black egg with a purple swirl and a glowing tilted accretion ring
    e = Egg()
    BLK, VIO, VIO2 = (14, 10, 26), (120, 50, 220), (200, 120, 255)

    def pat(th, t, c):
        sw = math.sin(th * 2 - t * 9)
        if sw > 0.85:
            return VIO2
        if sw > 0.55:
            return VIO
        return starry(c, BLK, 0.04, (190, 170, 255), 11)
    e.shell(pat)
    e.torus(Vector((0, 0, 0.0)), R * 1.3, 0.11, (210, 140, 255), rot=(22, 0, 0), seg=64)
    e.torus(Vector((0, 0, 0.0)), R * 1.48, 0.05, (255, 170, 90), rot=(22, 0, 0), seg=64)
    tip, n = e.surf(0, 1)
    e.sph(tip + Vector((0, 0, 0.16)), 0.2, (210, 140, 255), seg=12)
    return e


def egg_star_station():  # 19 Star Station: white metal panels, blue light lines, antenna dish
    e = Egg()
    W1, W2, BLUE, GREYD = (228, 232, 240), (190, 196, 210), (60, 170, 255), (90, 96, 112)

    def pat(th, t, c):
        if abs(math.sin(t * math.pi * 3)) < 0.05 or abs(math.sin(th * 3)) < 0.03:
            return GREYD
        if abs(math.sin(t * math.pi * 3 + 1.2)) < 0.06:
            return BLUE
        return W1 if math.sin(th * 3) > 0 else W2
    e.shell(pat, seg=24, rings=18, flat=True)
    for k in range(6):
        p, n = e.surf(k * math.tau / 6, 0.05, 0.03)
        e.sph(p, 0.08, (120, 220, 255), seg=8)
    tip, n = e.surf(0, 1)
    e.cone(tip + Vector((0, 0, 0.3)), 0.05, 0.04, 0.7, GREYD, seg=8)
    e.cone(tip + Vector((0, 0, 0.62)), 0.36, 0.06, 0.18, W1, seg=20)
    e.sph(tip + Vector((0, 0, 0.82)), 0.09, (255, 80, 80), seg=8)
    return e


def egg_galaxy_throne():  # 20 Galaxy Throne: royal galaxy (dark blue, gold stars, swirl) with a gold crown + gems
    e = Egg()
    NAVY, BLUE2, GOLDC, MAG = (20, 22, 70), (60, 50, 160), (255, 210, 70), (220, 90, 255)

    def pat(th, t, c):
        sw = math.sin(th * 2 + t * 6)
        base = mix(NAVY, BLUE2, max(0, sw))
        if sw > 0.9:
            base = mix(base, MAG, 0.5)
        if abs(t + 0.1) < 0.08:
            return GOLDC
        return starry(c, base, 0.08, (255, 236, 150), 20)
    e.shell(pat)
    for k in range(8):
        p, n = e.surf(k * math.tau / 8, -0.1, 0.03)
        e.gem(p, 0.15, 0.2, [(255, 80, 200), (90, 220, 255), (255, 255, 255)][k % 3], normal=-n)
    tip, n = e.surf(0, 1)
    c0 = tip + Vector((0, 0, -0.25))
    e.cone(c0 + Vector((0, 0, 0.2)), 0.72, 0.8, 0.4, GOLDC, seg=24, smooth=True)
    for k in range(6):
        a = k * math.tau / 6
        q = c0 + Vector((0.75 * math.cos(a), 0.75 * math.sin(a), 0.55))
        e.star(q + Vector((0, 0, 0.1)), 0.17, 0.06, GOLDC, rot=(90, 0, math.degrees(a)), points=5)
    e.star(c0 + Vector((0, 0, 0.95)), 0.3, 0.08, (255, 240, 170), rot=(90, 0, 0), points=5)
    return e


def egg_secret():  # v224: SECRET EGG (the rare event egg): royal violet, gold lattice, magenta gems, crystal crown, orbiting orbs
    e = Egg()
    V1, V2, GOLDL, MAG = (64, 20, 120), (118, 46, 210), (255, 206, 80), (255, 90, 220)

    def pat(th, t, c):
        a = math.sin(th * 4 + t * 6.0)
        b = math.sin(th * 4 - t * 6.0)
        if abs(a) < 0.07 or abs(b) < 0.07:
            return GOLDL
        return mix(V1, V2, 0.5 + 0.5 * math.sin(t * 3 + th))
    e.shell(pat)
    for k in range(8):  # gems where the gold lines cross round the middle
        p, n = e.surf(k * math.tau / 8 + math.tau / 16, 0.0, 0.03)
        e.gem(p, 0.15, 0.22, MAG if k % 2 == 0 else (130, 230, 255), normal=-n)
    tip, n = e.surf(0, 1)
    for k in range(6):  # crown of violet crystals + a big pink one
        a = k * math.tau / 6
        d = Vector((math.cos(a) * 0.5, math.sin(a) * 0.5, 1)).normalized()
        e.cone(tip + Vector((0.32 * math.cos(a), 0.32 * math.sin(a), -0.28)) + d * 0.3, 0.15, 0.0, 0.7, (190, 120, 255), normal=d, seg=6)
    e.cone(tip + Vector((0, 0, 0.5)), 0.22, 0.0, 1.05, (255, 150, 240), seg=6)
    for k in range(10):  # floating orbs on a tilted ring
        a = k * math.tau / 10
        e.sph(Vector((R * 1.35 * math.cos(a), R * 1.35 * math.sin(a), 0.25 * math.sin(a) - 0.1)), 0.13, MAG if k % 2 else GOLDL, seg=12)
    e.torus(Vector((0, 0, -0.1)), R * 1.35, 0.035, (220, 170, 255), rot=(10, 0, 0), seg=60)
    return e


EGGS_W2 = [('Egg_11', egg_cosmic_nest), ('Egg_12', egg_moon_craters), ('Egg_13', egg_nebula_reef), ('Egg_14', egg_asteroid_belt),
           ('Egg_15', egg_solar_forge), ('Egg_16', egg_comet_glacier), ('Egg_17', egg_alien_jungle), ('Egg_18', egg_black_hole),
           ('Egg_19', egg_star_station), ('Egg_20', egg_galaxy_throne)]

EGGS = [('Egg_1', egg_meadow), ('Egg_2', egg_mushroom), ('Egg_3', egg_candy), ('Egg_4', egg_toy), ('Egg_5', egg_crystal),
        ('Egg_6', egg_spooky), ('Egg_7', egg_thunder), ('Egg_8', egg_neon), ('Egg_9', egg_cloud), ('Egg_10', egg_golden_nest),
        ('Egg_Gold', egg_gold), ('Egg_Rotten', egg_rotten), ('Egg_Storm', egg_storm)]
if 'w2' in ARGS:  # v208: only the world 2 eggs (own FBX + renders)
    EGGS = EGGS_W2
if 'secret' in ARGS:  # v224: only the SECRET EGG
    EGGS = [('Egg_Secret', egg_secret)]

# ======================================================================= scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
MAT = bpy.data.materials.new('VertexColour')
MAT.use_nodes = True
nt = MAT.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
vc = nt.nodes.new('ShaderNodeVertexColor')
vc.layer_name = 'Col'
nt.links.new(vc.outputs['Color'], bsdf.inputs['Base Color'])
bsdf.inputs['Roughness'].default_value = 0.32

(HERE / 'out' / 'eggtex').mkdir(exist_ok=True)
objs = []
for k, (name, fn) in enumerate(EGGS):
    objs.append(fn().finish(name, (k % 7) * 5.0, -(k // 7) * 6.0, MAT))
print('tris:', {o.name: len(o.data.polygons) for o in objs})

if 'nofbx' not in ARGS:
    for o in bpy.data.objects:
        o.select_set(o in objs)
    bpy.context.view_layer.objects.active = objs[0]
    fbx = HERE / 'out' / ('RainingEggsSecretEgg.fbx' if 'secret' in ARGS else 'RainingEggsEggsW2.fbx' if 'w2' in ARGS else 'RainingEggsEggs2.fbx')
    bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, object_types={'MESH'}, apply_scale_options='FBX_SCALE_UNITS',
                             mesh_smooth_type='FACE', colors_type='NONE', add_leaf_bones=False, bake_anim=False, path_mode='COPY', embed_textures=True)
    desk = pathlib.Path(os.environ['USERPROFILE']) / 'Desktop' / 'RAINING EGGS NOU' / fbx.name
    shutil.copyfile(fbx, desk)
    print('fbx ->', desk)

if 'norender' not in ARGS:
    sc = bpy.context.scene
    try:
        sc.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError:
        sc.render.engine = 'BLENDER_EEVEE'
    sc.view_settings.view_transform = 'Standard'
    sc.render.film_transparent = False
    w = bpy.data.worlds.new('W')
    sc.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs[0].default_value = (0.62, 0.8, 1.0, 1)
    bg.inputs[1].default_value = 1.0
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
    sun.data.energy = 3.2
    sun.data.angle = math.radians(10)
    sun.rotation_euler = (math.radians(50), 0, math.radians(-35))
    sc.collection.objects.link(sun)
    # ground (soft lilac, like the hatch stand)
    gm = bpy.data.meshes.new('G')
    gb = bmesh.new()
    bmesh.ops.create_grid(gb, x_segments=1, y_segments=1, size=400)
    gb.to_mesh(gm)
    gb.free()
    gmat = bpy.data.materials.new('G')
    gmat.use_nodes = True
    next(n for n in gmat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (0.55, 0.5, 0.85, 1)
    gm.materials.append(gmat)
    g = bpy.data.objects.new('Ground', gm)
    sc.collection.objects.link(g)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    sc.collection.objects.link(cam)
    sc.camera = cam
    out = HERE / 'out'

    def shot(path, eye, target, res, lens):
        cam.location = Vector(eye)
        cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat('-Z', 'Y').to_euler()
        cam.data.lens = lens
        sc.render.resolution_x, sc.render.resolution_y = res
        sc.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)

    # lineup: all eggs in two rows
    shot(out / ('eggsecret_all.png' if 'secret' in ARGS else 'eggsw2_all.png' if 'w2' in ARGS else 'eggs2_all.png'), (15, -46, 13), (15, -3, 1.4), (1800, 1000), 40)
    # close-ups, one by one
    for o in objs:
        for q in objs:
            q.hide_render = q is not o
        c = o.location + Vector((0, 0, 2.0))
        shot(out / f'eggs2_{o.name}.png', tuple(c + Vector((-2.2, -8.5, 1.6))), tuple(c), (700, 700), 50)
    for q in objs:
        q.hide_render = False
