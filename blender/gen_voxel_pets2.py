r"""Voxel pets v2: finer voxels (S per design unit), cleaner shapes, defined faces.
  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P gen_voxel_pets2.py -- preview
Design units: x = right, y = back (pets look towards -y), z = up. Every shape is rasterised at S voxels per unit.
"""
import bpy, bmesh, math, sys, colorsys, pathlib, hashlib

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / 'out'
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
S = 2                       # voxels per design unit
INK = (24, 20, 32)
WHITE = (250, 250, 252)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def sh(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


class Vox:
    def __init__(self):
        self.g = {}

    # all shape coordinates are design units (floats)
    def _rng(self, lo, hi):
        return range(math.floor(lo * S) - 1, math.ceil(hi * S) + 1)

    @staticmethod
    def c(i):
        return (i + 0.5) / S

    def ell(self, cx, cy, cz, rx, ry, rz, col, cut=None, only_empty=False):
        for x in self._rng(cx - rx, cx + rx):
            for y in self._rng(cy - ry, cy + ry):
                for z in self._rng(cz - rz, cz + rz):
                    X, Y, Z = self.c(x), self.c(y), self.c(z)
                    if ((X - cx) / rx) ** 2 + ((Y - cy) / ry) ** 2 + ((Z - cz) / rz) ** 2 <= 1:
                        if (not cut or cut(X, Y, Z)) and (not only_empty or (x, y, z) not in self.g):
                            self.g[(x, y, z)] = col

    def box(self, x0, y0, z0, x1, y1, z1, col):
        for x in self._rng(x0, x1):
            for y in self._rng(y0, y1):
                for z in self._rng(z0, z1):
                    X, Y, Z = self.c(x), self.c(y), self.c(z)
                    if x0 <= X < x1 and y0 <= Y < y1 and z0 <= Z < z1:
                        self.g[(x, y, z)] = col

    def line(self, p0, p1, r, col):
        n = int(max(abs(p1[i] - p0[i]) for i in range(3)) * S * 1.5) + 1
        for k in range(n + 1):
            t = k / n
            p = [p0[i] + (p1[i] - p0[i]) * t for i in range(3)]
            rr = r(t) if callable(r) else r
            self.ell(p[0], p[1], p[2], rr, rr, rr, col)

    def tri(self, p0, p1, p2, col, thick=0.5):
        """filled flat triangle (wing membranes, fins)"""
        L = max(math.dist(p0, p1), math.dist(p0, p2), math.dist(p1, p2))
        n = int(L * S * 2) + 2
        for i in range(n + 1):
            for j in range(n + 1 - i):
                a, b = i / n, j / n
                p = [p0[k] + (p1[k] - p0[k]) * a + (p2[k] - p0[k]) * b for k in range(3)]
                for dy in range(max(1, int(thick * S))):
                    self.g[(math.floor(p[0] * S), math.floor(p[1] * S) + dy, math.floor(p[2] * S))] = col

    def paint(self, test, col):
        """recolour existing voxels: test(X, Y, Z, old colour) in design units"""
        for k, old in list(self.g.items()):
            X, Y, Z = self.c(k[0]), self.c(k[1]), self.c(k[2])
            r = test(X, Y, Z, old)
            if r:
                self.g[k] = col(X, Y, Z, old) if callable(col) else col

    def front(self, x, z, y_from=-40):
        """design-unit y of the first voxel met when looking from the front at (x, z)"""
        xi, zi = math.floor(x * S), math.floor(z * S)
        ys = [k[1] for k in self.g if k[0] == xi and k[2] == zi]
        return (min(ys) / S) if ys else None

    def sym(self):
        """make it perfectly symmetric: copy the left side (x < 0) to the right"""
        for (x, y, z), col in list(self.g.items()):
            if x < 0:
                self.g[(-x - 1, y, z)] = col


def eyes(v, ex, ez, w=2.2, h=2.4, angry=True, look=0.0, pupil=1.2):
    """eyes stuck on the front surface at x = +-ex, z = ez"""
    for sx in (-1, 1):
        cx = sx * ex
        fy = min(v.front(cx + d, ez + e) or 0 for d in (-w / 2, 0, w / 2) for e in (0, h))
        y0 = fy - 0.5
        v.box(cx - w / 2, y0, ez, cx + w / 2, y0 + 1.2, ez + h, WHITE)
        px = cx - sx * (w / 2 - pupil) * 0.6 + look
        v.box(px - pupil / 2, y0 - 0.5, ez + 0.2, px + pupil / 2, y0 + 0.2, ez + 0.2 + pupil * 1.25, INK)
        v.box(px - pupil / 2, y0 - 0.5, ez + 0.2 + pupil * 0.75, px - pupil / 2 + 0.5, y0 + 0.2, ez + 0.2 + pupil * 1.25, WHITE)
        if angry:                                      # slanted brow, high on the outside
            for k in range(int(w * S) + 2):
                bx = cx - w / 2 - 0.5 / S + k / S
                t = (bx - (cx - w / 2)) / w
                rise = (1 - t) if sx > 0 else t
                v.box(bx, y0 - 0.5, ez + h - 0.1 + rise * 0.9, bx + 1 / S, y0 + 0.6, ez + h + 0.7 + rise * 0.9, INK)


# ================================================================ pets
def spike_hog():
    v = Vox()
    B, D, L, P = (176, 112, 74), (120, 72, 46), (226, 176, 136), (244, 156, 160)
    v.ell(0, 3, 7, 7.5, 9.5, 6.5, B)                                          # body
    v.paint(lambda X, Y, Z, o: Z < 4.5, L)                                    # light belly
    for lx, ly in ((-4.5, -2), (4.5, -2), (-4.5, 8), (4.5, 8)):              # legs + hooves
        v.box(lx - 1.6, ly - 1.6, 0, lx + 1.6, ly + 1.6, 4.5, D)
        v.box(lx - 1.7, ly - 1.7, 0, lx + 1.7, ly + 1.7, 1, INK)
    v.ell(0, -6, 8.5, 5.8, 5, 5.4, B)                                         # head
    v.box(-2.6, -12.2, 5.4, 2.6, -9.2, 9.4, P)                                # snout
    v.box(-1.6, -12.7, 6.6, -0.6, -12.1, 8.0, INK)                            # nostrils
    v.box(0.6, -12.7, 6.6, 1.6, -12.1, 8.0, INK)
    for sx in (-1, 1):
        v.line((sx * 2.4, -11, 5.6), (sx * 3.6, -12.4, 9.2), lambda t: 0.75 - 0.35 * t, (255, 246, 222))   # tusks
        v.line((sx * 4.2, -6, 12.6), (sx * 5.4, -5, 15.2), lambda t: 1.3 - 0.9 * t, D)                    # ears
    for k in range(7):                                                         # spiky mane down the back
        y = -6.5 + k * 2.6
        v.line((0, y, 12.6 - k * 0.35), (0, y + 1.6, 16.4 - k * 0.6), lambda t: 1.15 - 0.95 * t, (90, 52, 36))
    v.line((0, 12, 8), (0, 14, 10.5), 0.6, D)                                  # tail
    eyes(v, 2.3, 9.4, angry=True)
    v.sym()
    return v


def saber_cat():
    v = Vox()
    O, St, L = (250, 150, 46), (40, 30, 34), (255, 236, 210)
    v.ell(0, 4, 8, 6.2, 10, 5.6, O)                                           # body
    v.paint(lambda X, Y, Z, o: Z < 5.2, L)
    for lx, ly in ((-3.8, -2.4), (3.8, -2.4), (-3.8, 10), (3.8, 10)):
        v.box(lx - 1.6, ly - 1.6, 0, lx + 1.6, ly + 1.6, 6, O)
        v.box(lx - 1.7, ly - 2.0, 0, lx + 1.7, ly + 1.6, 1.0, L)
    v.ell(0, -6.5, 11, 6, 5.2, 5.2, O)                                         # big head
    v.box(-3, -12, 7.8, 3, -9.6, 10.6, L)                                      # muzzle
    v.box(-1, -12.5, 9.6, 1, -11.8, 10.8, (240, 110, 130))                     # nose
    for sx in (-1, 1):
        v.line((sx * 1.4, -11.8, 8.2), (sx * 1.6, -12.2, 4.4), lambda t: 0.75 - 0.4 * t, WHITE)   # saber fangs
        v.box(sx * 4.6 - 1.4, -7.5, 14.6, sx * 4.6 + 1.4, -5.5, 17.2, O)                         # ears
        v.box(sx * 4.6 - 0.7, -7.9, 15.2, sx * 4.6 + 0.7, -7.3, 16.6, (240, 140, 150))
    # tiger stripes: bands across the back and head
    v.paint(lambda X, Y, Z, o: o == O and Z > 6 and (int((Y + 30) * 0.8) % 3 == 0) and abs(X) < 5.6, St)
    v.paint(lambda X, Y, Z, o: o == O and Y < -8 and Z > 13.4 and abs(X) < 2.8 and int(X * 2) % 3 == 0, St)
    v.line((0, 13.5, 10), (0, 18, 15), 0.9, O)                                  # tail
    v.line((0, 18, 15), (0, 19, 17), 0.9, St)
    eyes(v, 2.4, 11.6, w=2.4, h=2.2, angry=True)
    v.sym()
    return v


def frost_shark():
    v = Vox()
    Bl, Bd, W = (70, 150, 235), (40, 92, 170), (236, 246, 255)
    v.ell(0, 2, 7, 6, 13, 5.6, Bl)                                             # body
    v.paint(lambda X, Y, Z, o: Z < 5.0, W)                                     # white belly
    v.paint(lambda X, Y, Z, o: Z > 10.6, Bd)
    v.ell(0, -9.5, 7, 5.6, 4.4, 5.0, Bl)                                       # snout
    v.paint(lambda X, Y, Z, o: o == Bl and Z < 5.2, W)
    v.box(-4.4, -14.4, 3.6, 4.4, -11.5, 5.4, (70, 20, 40))                     # mouth
    for k in range(9):                                                          # teeth
        x = -4 + k
        v.box(x, -14.6, 4.5 if k % 2 else 4.2, x + 0.5, -13.9, 5.4, WHITE)
    v.line((0, -1, 12), (0, 3, 18.5), lambda t: 2.6 - 2.0 * t, Bd)             # dorsal fin
    for sx in (-1, 1):
        v.line((sx * 5, -3, 5), (sx * 9.5, 0, 2.4), lambda t: 1.6 - 1.0 * t, Bd)   # side fins
        v.box(sx * 3.6 - 1.4, 4, 0, sx * 3.6 + 1.4, 7, 3.6, Bd)                     # stubby legs
    v.line((0, 14, 8), (0, 19, 14), lambda t: 1.8 - 1.0 * t, Bd)               # tail up
    v.line((0, 14, 7), (0, 18.5, 2.6), lambda t: 1.4 - 0.8 * t, Bd)            # tail down
    for k in range(4):                                                          # ice crystals on the back
        v.line((sx * 0, 4 + k * 2.5, 11.6 - k * 0.4), (0.0, 5 + k * 2.5, 13.8 - k * 0.5), 0.5, (190, 240, 255))
    eyes(v, 3.0, 8.2, w=2.0, h=2.0, angry=True)
    v.sym()
    return v


def magma_bull():
    v = Vox()
    K, L, Y, Hn = (44, 38, 46), (255, 96, 24), (255, 210, 60), (238, 232, 216)
    v.ell(0, 4, 9, 7.4, 10, 6.6, K)                                            # big chest/body
    v.ell(0, -1, 11.5, 7.6, 5.5, 6.0, K)                                        # hump
    for lx, ly in ((-4.4, -2), (4.4, -2), (-4.4, 10.5), (4.4, 10.5)):
        v.box(lx - 1.8, ly - 1.8, 0, lx + 1.8, ly + 1.8, 6.5, K)
        v.box(lx - 1.9, ly - 1.9, 0, lx + 1.9, ly + 1.9, 1.0, L)
    v.ell(0, -8, 9.5, 5.2, 4.6, 5.0, K)                                         # head
    v.box(-3, -13, 6, 3, -10.6, 9.4, (70, 60, 66))                              # snout
    v.box(-1.8, -13.5, 7.4, -0.8, -12.9, 8.4, L)                                # glowing nostrils
    v.box(0.8, -13.5, 7.4, 1.8, -12.9, 8.4, L)
    v.box(-0.5, -13.6, 6.2, 0.5, -12.8, 7.6, Y)                                 # nose ring
    for sx in (-1, 1):                                                           # big horns, glowing tips
        v.line((sx * 4.4, -8, 13), (sx * 8.6, -9, 14.6), lambda t: 1.6 - 0.4 * t, Hn)
        v.line((sx * 8.6, -9, 14.6), (sx * 9.6, -10.4, 18.2), lambda t: 1.0 - 0.6 * t, Hn)
        v.paint(lambda X, Y_, Z, o, sx=sx: o == Hn and Z > 16.8 and X * sx > 8.6, Y)
    # lava cracks: zigzag lines over the body
    for (a, b) in (((-7, 0, 10), (-6.6, 6, 6)), ((-6.6, 6, 6), (-7.2, 10, 9)), ((7, -2, 12), (7.2, 4, 8)),
                   ((7.2, 4, 8), (6.8, 9, 11)), ((-3, -2, 17.4), (2, 2, 17.2)), ((2, 2, 17.2), (-1, 7, 15.6))):
        v.line(a, b, 0.55, L)
    for sx in (-1, 1):
        for k in range(4):
            y0 = -3 + k * 3.6
            v.line((sx * 7.2, y0, 13 - k * 0.6), (sx * 7.6, y0 + 1.6, 9.5 - k * 0.4), 0.5, L)
            v.line((sx * 7.6, y0 + 1.6, 9.5 - k * 0.4), (sx * 7.0, y0 + 3.0, 6.5), 0.5, Y if k % 2 else L)
    v.paint(lambda X, Y_, Z, o: o == K and Z > 14.4 and int(X * 2 + Y_) % 7 == 0, (90, 40, 30))
    v.line((0, 14, 10), (0, 16, 5), 0.6, K)                                    # tail
    v.ell(0, 16, 4.6, 1, 1, 1.2, L)
    eyes(v, 2.4, 10.6, w=2.0, h=1.8, angry=True)
    v.paint(lambda X, Y_, Z, o: o == WHITE and Y_ < -9, Y)                      # glowing yellow eyes
    v.sym()
    return v


def storm_dragon():
    v = Vox()
    P, Pd, B, Hn, El = (156, 112, 255), (96, 66, 200), (214, 200, 255), (250, 240, 200), (120, 236, 255)
    v.ell(0, 4, 8, 6, 9, 5.6, P)                                               # body
    v.paint(lambda X, Y, Z, o: Z < 5.2 and Y < 10, B)                          # belly plates
    v.paint(lambda X, Y, Z, o: o == B and int(Z * 2) % 3 == 0, sh(B, 0.86))
    for lx, ly in ((-4, -1.5), (4, -1.5), (-4, 9.5), (4, 9.5)):
        v.box(lx - 1.6, ly - 1.6, 0, lx + 1.6, ly + 1.6, 5.5, P)
        for c in (-1, 0, 1):
            v.box(lx + c * 1.1 - 0.4, ly - 2.4, 0, lx + c * 1.1 + 0.4, ly - 1.4, 0.8, Hn)   # claws
    v.line((0, -2, 10), (0, -6, 14.5), 2.8, P)                                  # neck
    v.ell(0, -8, 15.5, 4.6, 5.6, 4.0, P)                                        # head
    v.box(-2.8, -14.4, 13, 2.8, -11, 15.6, P)                                   # snout
    v.box(-1.6, -14.8, 14.6, -0.6, -14.2, 15.4, INK)
    v.box(0.6, -14.8, 14.6, 1.6, -14.2, 15.4, INK)
    v.box(-2.4, -14.6, 13, 2.4, -13.4, 13.4, WHITE)                             # teeth row
    for sx in (-1, 1):
        v.line((sx * 2.4, -6.5, 18.5), (sx * 4.2, -3.5, 23), lambda t: 1.0 - 0.75 * t, Hn)   # horns
        # wings: bony arm with three fingers, membrane between them (flat, angled up and back)
        sh_ = (sx * 5.2, 3.0, 12.6)
        el = (sx * 10.5, 3.6, 17.5)
        tips = [(sx * 15.5, 5.0, 21.0), (sx * 16.0, 7.0, 15.5), (sx * 13.5, 8.5, 10.5)]
        prev = sh_
        for t in tips:
            v.tri(el, prev, t, El, 0.5)
            prev = t
        v.tri(el, prev, (sx * 6.0, 8.0, 11.0), El, 0.5)
        v.line(sh_, el, 0.75, Pd)
        for t in tips:
            v.line(el, t, lambda u: 0.6 - 0.3 * u, Pd)
    for k in range(8):                                                          # back spikes
        y = -3 + k * 2.4
        v.line((0, y, 13.2 - k * 0.45), (0, y + 1.0, 15.4 - k * 0.6), lambda t: 0.9 - 0.7 * t, Hn)
    v.line((0, 13, 7), (0, 18, 9), 1.4, P)                                      # tail
    v.line((0, 18, 9), (0, 21, 13), 1.0, P)
    v.line((0, 21, 13), (0, 22.6, 15.6), lambda t: 1.4 - 1.2 * t, El)          # lightning tip
    eyes(v, 2.0, 16.2, w=1.8, h=1.6, angry=True)
    v.paint(lambda X, Y, Z, o: o == WHITE and Z > 15.8 and Y < -10, El)          # electric eyes
    v.sym()
    return v


PETS = [('Spike Hog', spike_hog, 'COMMON'), ('Saber Cat', saber_cat, 'UNCOMMON'), ('Frost Shark', frost_shark, 'RARE'),
        ('Magma Bull', magma_bull, 'EPIC'), ('Storm Dragon', storm_dragon, 'LEGENDARY')]

# ================================================================ mesh
GOLD = [(200, 120, 0), (255, 176, 0), (255, 214, 40), (255, 244, 150)]
DIRS = [((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]), ((-1, 0, 0), [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)]),
        ((0, 1, 0), [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)]), ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
        ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]), ((0, 0, -1), [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)])]


def recolor(col, key, kind):
    if kind == 'gold' and col not in (INK,):
        l = (0.3 * col[0] + 0.59 * col[1] + 0.11 * col[2]) / 255
        return GOLD[min(3, int(l * 4.2))]
    if kind == 'rainbow' and col not in (INK, WHITE):
        h = ((key[1] * 0.6 + key[2]) / (34 * S)) % 1
        r, g, b = colorsys.hsv_to_rgb(h, 0.72, 1.0)
        return (int(r * 255), int(g * 255), int(b * 255))
    return col


def build_mesh(name, v, kind='normal', unit=0.07):
    bm = bmesh.new()
    cl = bm.loops.layers.color.new('Col')
    xs = [k[0] for k in v.g]
    ys = [k[1] for k in v.g]
    zs = [k[2] for k in v.g]
    ox, oy, oz = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2, min(zs)
    vc = {}

    def vert(p):
        if p not in vc:
            vc[p] = bm.verts.new(((p[0] - ox) * unit, (p[1] - oy) * unit, (p[2] - oz) * unit))
        return vc[p]

    for key, col in v.g.items():
        c = recolor(col, key, kind)
        hsh = int(hashlib.md5(str(key).encode()).hexdigest()[:4], 16) / 65535
        j = 0.93 + 0.09 * hsh
        for (dx, dy, dz), quad in DIRS:
            nb = (key[0] + dx, key[1] + dy, key[2] + dz)
            if nb in v.g:
                continue
            f = bm.faces.new([vert((key[0] + a, key[1] + b, key[2] + cc)) for a, b, cc in quad])
            light = 1.12 if dz == 1 else (0.95 if dz == 0 else 0.72)
            # soft ambient occlusion: darker where the voxel above is filled
            if dz == 0 and (key[0], key[1], key[2] + 1) in v.g and (key[0] + dx, key[1] + dy, key[2] + 1) in v.g:
                light *= 0.9
            cc_ = tuple(min(1.0, (x / 255) ** 2.2 * j * light) for x in c) + (1.0,)
            for lp in f.loops:
                lp[cl] = cc_
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    m = bpy.data.materials.new(name + 'M')
    m.use_nodes = True
    nt = m.node_tree
    a = nt.nodes.new('ShaderNodeVertexColor')
    a.layer_name = 'Col'
    b = nt.nodes['Principled BSDF']
    nt.links.new(a.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.6
    if kind == 'gold':
        b.inputs['Metallic'].default_value = 0.2
        b.inputs['Roughness'].default_value = 0.35
    me.materials.append(m)
    return o


# ================================================================ preview
def stage():
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
    sc.eevee.taa_render_samples = 48
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('W')
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.62, 0.8, 1.0, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.85
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
    sun.data.energy = 3.2
    sun.data.angle = math.radians(3)
    sun.rotation_euler = (math.radians(48), math.radians(6), math.radians(-38))
    sc.collection.objects.link(sun)
    bpy.ops.mesh.primitive_plane_add(size=400)
    g = bpy.context.object
    gm = bpy.data.materials.new('G')
    gm.use_nodes = True
    gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.36, 0.7, 0.24, 1)
    g.data.materials.append(gm)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    cam.data.type = 'ORTHO'
    sc.collection.objects.link(cam)
    sc.camera = cam
    return sc, cam


YAW = -32
RIGHT = (math.cos(math.radians(YAW)), math.sin(math.radians(YAW)))


def along(t):
    return (RIGHT[0] * t, RIGHT[1] * t, 0)


def render(path, cam, cx, scale, w, h, tz=1.0, pitch=70):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = w, h
    cam.data.ortho_scale = scale
    cam.rotation_euler = (math.radians(pitch), 0, math.radians(YAW))
    d = 60
    fwd = cam.matrix_world.to_3x3() @ __import__('mathutils').Vector((0, 0, -1))
    bpy.context.view_layer.update()
    fwd = cam.rotation_euler.to_matrix() @ __import__('mathutils').Vector((0, 0, -1))
    c = along(cx)
    cam.location = (c[0] - d * fwd.x, c[1] - d * fwd.y, tz - d * fwd.z)
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def clear():
    for o in list(bpy.data.objects):
        if o.type == 'MESH' and o.name != 'Plane':
            bpy.data.objects.remove(o, do_unlink=True)


if __name__ == '__main__' and 'preview' in args:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc, cam = stage()
    x = 0
    for name, fn, _ in PETS:
        o = build_mesh(name, fn())
        o.location = along(x)
        x += 4.2
    render(OUT / 'vox2_pets.png', cam, 8.4, 22, 2000, 700, tz=0.8)
    clear()
    x = 0
    for kind in ('normal', 'gold', 'rainbow'):
        o = build_mesh('D_' + kind, storm_dragon(), kind)
        o.location = along(x)
        x += 4.6
    render(OUT / 'vox2_variants.png', cam, 4.6, 14.5, 1800, 640, tz=0.9)
    clear()
    x = 0
    for s in (1.0, 1.35, 1.75, 2.4, 3.3):
        o = build_mesh('SZ', magma_bull())
        o.scale = (s, s, s)
        o.location = along(x + 1.7 * s)
        x += 3.4 * s + 0.4
    render(OUT / 'vox2_sizes.png', cam, x / 2, x * 0.92, 2000, 820, tz=1.6)
    print('done')
