r"""Voxel ("pixel") pets: every pet is a 3D grid of little cubes, built from simple shapes.
Only the outside faces become mesh; every cube gets a tiny brightness change -> the blocky pixel look.
  E:\tools\blender-4.2.3-windows-x64\blender.exe -b -P gen_voxel_pets.py -- preview
Grid units: x = right, y = back (pet looks towards -y), z = up. 1 voxel = 1 unit.
"""
import bpy, bmesh, math, sys, random, colorsys, pathlib, hashlib

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / 'out'
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []

INK = (22, 18, 30)
WHITE = (250, 250, 250)


class Vox:
    def __init__(self):
        self.g = {}

    def put(self, x, y, z, c):
        self.g[(x, y, z)] = c

    def ell(self, cx, cy, cz, rx, ry, rz, c, cut=None):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
                for z in range(int(cz - rz) - 1, int(cz + rz) + 2):
                    if ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 + ((z + .5 - cz) / rz) ** 2 <= 1:
                        if not cut or cut(x, y, z):
                            self.g[(x, y, z)] = c

    def box(self, x0, y0, z0, x1, y1, z1, c):
        for x in range(x0, x1):
            for y in range(y0, y1):
                for z in range(z0, z1):
                    self.g[(x, y, z)] = c

    def line(self, p0, p1, r, c):
        """thick line (horns, tails, legs at an angle)"""
        n = int(max(abs(p1[i] - p0[i]) for i in range(3)) * 2) + 1
        for k in range(n + 1):
            t = k / n
            p = [p0[i] + (p1[i] - p0[i]) * t for i in range(3)]
            rr = r(t) if callable(r) else r
            self.ell(p[0], p[1], p[2], rr, rr, rr, c)

    def paint(self, test, c):
        for k in list(self.g):
            if test(*k):
                self.g[k] = c

    def mirror_x(self, cx2):
        """copy the left half (x < cx2/2) to the right: cx2 = 2 * centre"""
        for (x, y, z), c in list(self.g.items()):
            self.g[(cx2 - 1 - x, y, z)] = c


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


# ---------------------------------------------------------------- the pets (zone 1 sample)
def eyes(v, x, y, z, angry=True, size=3, gap=2):
    """cartoon eyes on the front face (y): white block, 2x2 pupil towards the middle, slanted brow"""
    for sx in (-1, 1):
        x0 = x + gap if sx > 0 else x - gap - size
        v.box(x0, y, z, x0 + size, y + 1, z + size, WHITE)
        px = x0 if sx > 0 else x0 + size - 2
        v.box(px, y - 1, z, px + 2, y, z + 2, INK)
        v.box(px, y - 1, z + 1, px + 1, y, z + 2, WHITE) if sx > 0 else v.box(px + 1, y - 1, z + 1, px + 2, y, z + 2, WHITE)
        if angry:
            for k in range(size + 1):
                bx = x0 - 1 + k if sx > 0 else x0 + size - k
                v.put(bx, y - 1, z + size + (1 if k < 2 else 0), INK)


def moss_turtle():
    v = Vox()
    G, D, S = (96, 168, 72), (70, 130, 54), (150, 110, 70)
    v.ell(12, 14, 7, 9, 10, 6.5, G, cut=lambda x, y, z: z >= 5)               # shell
    v.paint(lambda x, y, z: z >= 5 and (x // 3 + y // 3 + z // 3) % 2 == 0, D)  # shell plates
    v.box(4, 5, 4, 20, 23, 6, S)                                            # rim
    for lx, ly in ((5, 7), (16, 7), (5, 18), (16, 18)):
        v.box(lx, ly, 0, lx + 3, ly + 3, 5, (120, 190, 90))
    v.ell(12, 2, 8, 5.5, 5, 5, (130, 200, 100))                               # head
    eyes(v, 12, -3, 8, angry=False)
    for k in range(6):                                                      # little plant on top
        v.put(12, 14, 13 + k, (90, 200, 70))
    v.ell(12, 14, 19.5, 2.5, 2.5, 1.5, (255, 120, 170))
    return v


def thunder_ram():
    v = Vox()
    W, F, H = (235, 236, 248), (120, 128, 170), (255, 214, 60)
    v.ell(12, 14, 9, 8, 11, 6.5, W)                                          # fluffy body
    v.paint(lambda x, y, z: (x + y * 2 + z * 3) % 7 == 0, shade(W, 0.9))
    for lx, ly in ((6, 8), (15, 8), (6, 18), (15, 18)):
        v.box(lx, ly, 0, lx + 3, ly + 3, 5, F)
    v.ell(12, 2, 12, 5.5, 5.5, 5.5, F)                                       # face
    eyes(v, 12, -4, 12)
    for sx in (-1, 1):                                                      # curled lightning horns
        pts = [(12 + sx * 4, 5, 15), (12 + sx * 8, 6, 17), (12 + sx * 10, 3, 14), (12 + sx * 9, 1, 10)]
        for a, b in zip(pts, pts[1:]):
            v.line(a, b, 1.2, H)
    v.line((12, 25, 10), (12, 29, 14), 1.0, H)                                # bolt tail
    v.line((12, 29, 14), (13, 30, 11), 1.0, H)
    return v


def ember_stag():
    v = Vox()
    B, L, E = (60, 40, 46), (255, 120, 30), (255, 220, 80)
    v.ell(12, 15, 10, 7, 11, 6, B)                                           # body
    v.paint(lambda x, y, z: z <= 9 and (x + y) % 4 == 0, L)                  # lava cracks underneath
    for lx, ly in ((7, 7), (15, 7), (7, 20), (15, 20)):
        v.box(lx, ly, 0, lx + 3, ly + 3, 7, B)
        v.box(lx, ly, 0, lx + 3, ly + 3, 1, L)
    v.line((12, 5, 12), (12, 2, 16), 3, B)                                   # neck
    v.ell(12, 1, 17, 5.5, 5, 5, B)                                           # head
    eyes(v, 12, -4, 16)
    v.paint(lambda x, y, z: z < 18 and y < 4 and (x + z) % 3 == 0 and v.g.get((x, y, z)) == B, L)
    for sx in (-1, 1):                                                      # flaming antlers
        v.line((12 + sx * 2, 1, 21), (12 + sx * 6, 3, 27), 0.9, L)
        v.line((12 + sx * 4, 2, 24), (12 + sx * 8, 0, 26), 0.8, E)
        v.line((12 + sx * 6, 3, 27), (12 + sx * 5, 5, 30), 0.8, E)
    v.paint(lambda x, y, z: z >= 25, E)
    v.line((12, 26, 13), (12, 30, 17), 1.4, L)                                # tail flame
    return v


def crystal_axo():
    v = Vox()
    P, C, G = (255, 150, 200), (120, 230, 255), (255, 90, 160)
    v.ell(12, 14, 5, 6, 11, 4, P)                                            # body
    v.ell(12, 3, 7, 7, 5.5, 5, P)                                            # big head
    eyes(v, 12, -3, 7, angry=False)
    v.box(10, -3, 4, 14, -2, 5, G)                                           # smile
    for sx in (-1, 1):                                                      # crystal gills
        for k, (dy, dz) in enumerate(((2, 8), (4, 10), (6, 8))):
            v.line((12 + sx * 6, dy, dz), (12 + sx * 11, dy + 1, dz + 4 - k), 0.8, C)
    for lx, ly in ((5, 8), (17, 8), (5, 19), (17, 19)):
        v.box(lx, ly, 0, lx + 3, ly + 3, 3, G)
    for k in range(4):                                                      # crystal spikes on the back
        v.line((12, 9 + k * 4, 8), (12, 10 + k * 4, 12 + (k % 2) * 2), 1.0, C)
    v.line((12, 25, 4), (12, 31, 6), lambda t: 2.2 * (1 - t) + 0.6, P)       # tail
    return v


def sun_griffin():
    v = Vox()
    Y, O, W2, K = (255, 200, 60), (240, 130, 30), (255, 245, 210), (90, 60, 40)
    v.ell(12, 15, 11, 6.5, 10, 6, Y)                                         # lion body
    for lx, ly in ((7, 9), (15, 9), (7, 20), (15, 20)):
        v.box(lx, ly, 0, lx + 3, ly + 3, 8, O)
        v.box(lx, ly - 1, 0, lx + 3, ly, 2, K)
    v.ell(12, 4, 18, 6, 6, 6, W2)                                            # eagle head
    v.ell(12, 7, 19, 7.5, 4, 7, O, cut=lambda x, y, z: y >= 6)               # feather crest
    eyes(v, 12, -3, 19)
    v.box(10, -4, 14, 14, -1, 17, (255, 170, 40))                            # beak
    v.box(11, -5, 14, 13, -4, 16, (255, 170, 40))
    for sx in (-1, 1):                                                      # wings: stepped feather panels
        for k in range(8):
            x0 = 12 + sx * (6 + k)
            top = 24 - abs(k - 2)
            for z in range(14, top):
                for y in range(11 + k // 2, 18):
                    v.put(int(x0), y, z, W2 if (z - 14) > (top - 14) * 0.45 else Y)
            v.put(int(x0), 18, top - 1, O)
    v.line((12, 25, 11), (12, 31, 15), 1.0, O)                                # tail
    v.ell(12, 32, 16, 1.8, 1.8, 1.8, W2)
    return v


PETS = [('Moss Turtle', moss_turtle), ('Thunder Ram', thunder_ram), ('Crystal Axolotl', crystal_axo),
        ('Ember Stag', ember_stag), ('Sun Griffin', sun_griffin)]

# ---------------------------------------------------------------- variants
GOLD = [(150, 85, 0), (230, 150, 0), (255, 200, 20), (255, 236, 120)]


def variant(col, key, kind, bounds):
    if kind == 'gold':
        l = (0.3 * col[0] + 0.59 * col[1] + 0.11 * col[2]) / 255
        i = min(3, int(l * 4))
        return GOLD[i] if col != INK else (60, 36, 8)
    if kind == 'rainbow':
        if col in (INK, WHITE):
            return col
        x, y, z = key
        h = ((x + y + z * 1.3) / 40) % 1
        r, g, b = colorsys.hsv_to_rgb(h, 0.75, 1.0)
        return (int(r * 255), int(g * 255), int(b * 255))
    return col


DIRS = [((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]), ((-1, 0, 0), [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)]),
        ((0, 1, 0), [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)]), ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
        ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]), ((0, 0, -1), [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)])]


def build_mesh(name, v, kind='normal', unit=0.12):
    """outside faces only, vertex colours with a per-cube jitter (pixel look)"""
    bm = bmesh.new()
    cl = bm.loops.layers.color.new('Col')
    xs = [k[0] for k in v.g]
    ys = [k[1] for k in v.g]
    zs = [k[2] for k in v.g]
    ox, oy = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2
    vcache = {}

    def vert(p):
        if p not in vcache:
            vcache[p] = bm.verts.new(((p[0] - ox) * unit, (p[1] - oy) * unit, (p[2] - min(zs)) * unit))
        return vcache[p]

    for key, col in v.g.items():
        c = variant(col, key, kind, None)
        h = int(hashlib.md5(str(key).encode()).hexdigest()[:4], 16) / 65535
        j = 0.9 + 0.14 * h
        for (dx, dy, dz), quad in DIRS:
            if (key[0] + dx, key[1] + dy, key[2] + dz) in v.g:
                continue
            f = bm.faces.new([vert((key[0] + a, key[1] + b, key[2] + cc)) for a, b, cc in quad])
            side = 1.0 if dz == 1 else (0.86 if dz == 0 else 0.7)       # baked light: tops bright, sides darker
            cc_ = tuple(min(1.0, (x / 255) ** 2.2 * j * side) for x in c) + (1.0,)
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
    b.inputs['Roughness'].default_value = 0.55
    if kind == 'gold':
        b.inputs['Metallic'].default_value = 0.65
        b.inputs['Roughness'].default_value = 0.3
    me.materials.append(m)
    return o


# ---------------------------------------------------------------- preview render
def stage():
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
    sc.eevee.taa_render_samples = 32
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('W')
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.55, 0.78, 1.0, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.9
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN'))
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(50), math.radians(8), math.radians(-35))
    sc.collection.objects.link(sun)
    bpy.ops.mesh.primitive_plane_add(size=300)
    g = bpy.context.object
    gm = bpy.data.materials.new('G')
    gm.use_nodes = True
    gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.25, 0.62, 0.18, 1)
    g.data.materials.append(gm)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam'))
    cam.data.type = 'ORTHO'
    sc.collection.objects.link(cam)
    sc.camera = cam
    return sc, cam


RIGHT = (math.cos(math.radians(-25)), math.sin(math.radians(-25)))
VIEW = (0.392, 0.840, -0.375)


def along(t):
    """a point t units along the camera's left-right line (rows stay straight on screen)"""
    return (RIGHT[0] * t, RIGHT[1] * t, 0)


def render(path, cam, cx, scale, w=1600, h=700, tz=1.2):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = w, h
    cam.data.ortho_scale = scale
    d = 40
    c = along(cx)
    cam.location = (c[0] - d * VIEW[0], c[1] - d * VIEW[1], tz - d * VIEW[2])
    cam.rotation_euler = (math.radians(68), 0, math.radians(-25))
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


if __name__ == '__main__' and 'preview' in args:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc, cam = stage()
    # row 1: the five pets
    x = 0
    for name, fn in PETS:
        o = build_mesh(name, fn())
        o.location = along(x)
        x += 6.0
    render(OUT / 'voxel_pets.png', cam, 12, 30, 1800, 640)
    # row 2: normal / gold / rainbow + sizes, on the legendary
    for o in list(bpy.data.objects):
        if o.type == 'MESH' and o.name != 'Plane':
            bpy.data.objects.remove(o, do_unlink=True)
    x = 0
    for kind in ('normal', 'gold', 'rainbow'):
        o = build_mesh('SG_' + kind, sun_griffin(), kind)
        o.location = along(x)
        x += 6.0
    render(OUT / 'voxel_variants.png', cam, 6, 18, 1600, 640)
    for o in list(bpy.data.objects):
        if o.type == 'MESH' and o.name != 'Plane':
            bpy.data.objects.remove(o, do_unlink=True)
    x = 0
    for s in (1.0, 1.35, 1.75, 2.4, 3.3):
        o = build_mesh('SZ', ember_stag())
        o.scale = (s, s, s)
        o.location = along(x + 2.6 * s)
        x += 5.2 * s + 0.6
    render(OUT / 'voxel_sizes.png', cam, x / 2, x * 0.95, 1800, 800, tz=3)
    print('done')
